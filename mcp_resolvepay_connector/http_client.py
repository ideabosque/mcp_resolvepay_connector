#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

__author__ = "bibow"

import json
import logging
import time
import traceback
from typing import Any, Dict, Optional, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .auth import ResolvepayAuth
from .exceptions import (
    ResolvepayAPIException,
    ResolvepayAuthenticationException,
    ResolvepayRateLimitException,
    ResolvepayValidationException,
)
from .rate_limiter import RateLimiter


class ResolvepayHTTPClient:
    """HTTP client for ResolvePay API with error handling and retries"""

    def __init__(
        self,
        base_url: str,
        auth: ResolvepayAuth,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limiter: Optional[RateLimiter] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limiter = rate_limiter or RateLimiter()
        self.logger = logger or logging.getLogger(__name__)

        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy"""
        session = requests.Session()

        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"],
            backoff_factor=1,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_full_url(self, endpoint: str) -> str:
        """Get full URL for endpoint"""
        return urljoin(self.base_url + "/", endpoint.lstrip("/"))

    def _prepare_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare headers with authentication"""
        headers = self.auth.get_auth_headers()
        if additional_headers:
            headers.update(additional_headers)
        return headers

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors"""
        try:
            if response.status_code == 401:
                raise ResolvepayAuthenticationException(
                    "Authentication failed. Check merchant_id and api_key."
                )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise ResolvepayRateLimitException(
                    "Rate limit exceeded",
                    retry_after=int(retry_after) if retry_after else None,
                )

            if response.status_code == 400:
                error_data = {}
                try:
                    error_data = response.json()
                except json.JSONDecodeError:
                    pass

                raise ResolvepayValidationException(
                    f"Validation error: {response.text}",
                    details={"status_code": 400, "response_data": error_data},
                )

            if response.status_code == 404:
                raise ResolvepayAPIException(
                    404,
                    "Resource not found",
                    response_data={"url": response.url, "method": response.request.method},
                )

            if response.status_code == 422:
                error_data = {}
                error_message = "Unprocessable Entity"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_details = error_data["error"]
                        if "message" in error_details:
                            error_message = error_details["message"]
                        if "details" in error_details:
                            # Include detailed validation errors
                            details = error_details["details"]
                            if isinstance(details, list) and len(details) > 0:
                                detail_messages = [f"{d.get('path', 'field')}: {d.get('message', 'error')}" for d in details]
                                error_message += f" - {', '.join(detail_messages)}"
                    else:
                        error_message = response.text or error_message
                except json.JSONDecodeError:
                    error_message = response.text or error_message

                raise ResolvepayValidationException(
                    f"Business validation error: {error_message}",
                    details={"status_code": 422, "response_data": error_data},
                )

            if not response.ok:
                error_message = f"API request failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_message = error_data["message"]
                except json.JSONDecodeError:
                    error_message = response.text or error_message

                raise ResolvepayAPIException(
                    response.status_code,
                    error_message,
                    response_data=error_data if "error_data" in locals() else {},
                )

            if response.status_code == 204:
                return {}

            try:
                return response.json()
            except json.JSONDecodeError:
                if response.text:
                    return {"raw_response": response.text}
                return {}

        except ResolvepayAPIException:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error handling response: {e}")
            raise ResolvepayAPIException(
                response.status_code if hasattr(response, "status_code") else 500,
                f"Unexpected error: {str(e)}",
            )

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make GET request"""
        return self._request("GET", endpoint, params=params, headers=headers)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make POST request"""
        return self._request("POST", endpoint, data=data, params=params, headers=headers)

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make PUT request"""
        return self._request("PUT", endpoint, data=data, params=params, headers=headers)

    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make DELETE request"""
        return self._request("DELETE", endpoint, params=params, headers=headers)

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request with rate limiting and error handling"""
        self.rate_limiter.sync_wait_if_needed()

        url = self._get_full_url(endpoint)
        request_headers = self._prepare_headers(headers)

        request_kwargs = {
            "method": method,
            "url": url,
            "headers": request_headers,
            "timeout": self.timeout,
        }

        if params:
            request_kwargs["params"] = params

        if data:
            request_kwargs["json"] = data

        self.logger.debug(f"Making {method} request to {url}")
        start_time = time.time()

        try:
            response = self.session.request(**request_kwargs)
            duration = time.time() - start_time

            self.logger.debug(
                f"{method} {url} completed in {duration:.2f}s with status {response.status_code}"
            )

            return self._handle_response(response)

        except requests.exceptions.Timeout:
            self.logger.error(f"Request timeout after {self.timeout}s for {method} {url}")
            raise ResolvepayAPIException(408, f"Request timeout after {self.timeout} seconds")

        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error for {method} {url}: {e}")
            raise ResolvepayAPIException(503, f"Connection error: {str(e)}")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error for {method} {url}: {e}")
            raise ResolvepayAPIException(500, f"Request error: {str(e)}")

        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(f"Unexpected error for {method} {url}: {e}\n{log}")
            raise ResolvepayAPIException(500, f"Unexpected error: {str(e)}")

    def close(self) -> None:
        """Close the HTTP session"""
        if self.session:
            self.session.close()