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

import httpx

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
        http2: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limiter = rate_limiter or RateLimiter()
        self.logger = logger or logging.getLogger(__name__)
        self.http2 = http2

        self.client = self._create_client()

    def _create_client(self) -> httpx.Client:
        """Create httpx client with HTTP/2 support and connection pooling"""
        limits = httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
            keepalive_expiry=30.0,
        )

        timeout = httpx.Timeout(
            timeout=self.timeout,
            connect=10.0,
            read=self.timeout,
            write=10.0,
            pool=5.0,
        )

        client = httpx.Client(
            http2=self.http2,
            limits=limits,
            timeout=timeout,
            follow_redirects=True,
        )

        self.logger.info(
            f"HTTP client created with HTTP/2={'enabled' if self.http2 else 'disabled'}, "
            f"timeout={self.timeout}s, max_retries={self.max_retries}"
        )

        return client

    def _get_full_url(self, endpoint: str) -> str:
        """Get full URL for endpoint"""
        return urljoin(self.base_url + "/", endpoint.lstrip("/"))

    def _prepare_headers(
        self, additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Prepare headers with authentication"""
        headers = self.auth.get_auth_headers()
        if additional_headers:
            headers.update(additional_headers)
        return headers

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response and errors"""
        # Handle specific status codes
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

        if response.status_code == 404:
            raise ResolvepayAPIException(
                404,
                "Resource not found",
                response_data={
                    "url": str(response.url),
                    "method": response.request.method,
                },
            )

        # Handle validation errors (400, 422)
        if response.status_code in [400, 422]:
            error_data = self._safe_json_decode(response)
            error_message = self._extract_error_message(error_data, response)

            error_type = (
                "Validation error"
                if response.status_code == 400
                else "Business validation error"
            )
            raise ResolvepayValidationException(
                f"{error_type}: {error_message}",
                details={
                    "status_code": response.status_code,
                    "response_data": error_data,
                },
            )

        # Handle other errors
        if not response.is_success:
            error_data = self._safe_json_decode(response)
            error_message = error_data.get("message") if error_data else response.text
            error_message = (
                error_message
                or f"API request failed with status {response.status_code}"
            )

            raise ResolvepayAPIException(
                response.status_code,
                error_message,
                response_data=error_data,
            )

        # Handle successful responses
        if response.status_code == 204:
            return {}

        return (
            self._safe_json_decode(response) or {"raw_response": response.text}
            if response.text
            else {}
        )

    def _safe_json_decode(self, response: httpx.Response) -> Dict[str, Any]:
        """Safely decode JSON response"""
        try:
            return response.json()
        except json.JSONDecodeError:
            return {}

    def _extract_error_message(
        self, error_data: Dict[str, Any], response: httpx.Response
    ) -> str:
        """Extract error message from response data"""
        if not error_data:
            return response.text or "Unknown error"

        # Handle structured error format
        if "error" in error_data:
            error_details = error_data["error"]
            message = error_details.get("message", "Unknown error")

            # Add validation details if present
            if "details" in error_details:
                details = error_details["details"]
                if isinstance(details, list) and details:
                    detail_messages = [
                        f"{d.get('path', 'field')}: {d.get('message', 'error')}"
                        for d in details
                    ]
                    message += f" - {', '.join(detail_messages)}"
            return message

        # Handle simple message format
        if "message" in error_data:
            return error_data["message"]

        return response.text or "Unknown error"

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
        return self._request(
            "POST", endpoint, data=data, params=params, headers=headers
        )

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
        """Make HTTP request with rate limiting, retries, and error handling

        Implements exponential backoff retry strategy for specific status codes:
        - 429: Rate limit exceeded
        - 500, 502, 503, 504: Server errors
        """
        self.rate_limiter.sync_wait_if_needed()

        url = self._get_full_url(endpoint)
        request_headers = self._prepare_headers(headers)

        request_kwargs = {
            "url": url,
            "headers": request_headers,
        }

        if params:
            request_kwargs["params"] = params

        if data:
            request_kwargs["json"] = data

        self.logger.debug(f"Making {method} request to {url}")
        start_time = time.time()

        # Retry logic with exponential backoff
        last_exception = None
        retry_status_codes = [429, 500, 502, 503, 504]

        for attempt in range(self.max_retries + 1):
            try:
                if method == "GET":
                    response = self.client.get(**request_kwargs)
                elif method == "POST":
                    response = self.client.post(**request_kwargs)
                elif method == "PUT":
                    response = self.client.put(**request_kwargs)
                elif method == "DELETE":
                    response = self.client.delete(**request_kwargs)
                else:
                    response = self.client.request(method, **request_kwargs)

                duration = time.time() - start_time

                # Log HTTP version used
                http_version = response.http_version
                self.logger.debug(
                    f"{method} {url} completed in {duration:.2f}s with status {response.status_code} "
                    f"(HTTP/{http_version})"
                )

                # Check if we need to retry based on status code
                if (
                    response.status_code in retry_status_codes
                    and attempt < self.max_retries
                ):
                    backoff_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    self.logger.warning(
                        f"Request failed with status {response.status_code}, "
                        f"retrying in {backoff_time}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(backoff_time)
                    continue

                return self._handle_response(response)

            except httpx.TimeoutException as e:
                last_exception = e
                if attempt < self.max_retries:
                    backoff_time = 2**attempt
                    self.logger.warning(
                        f"Request timeout, retrying in {backoff_time}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(backoff_time)
                    continue
                self.logger.error(
                    f"Request timeout after {self.timeout}s for {method} {url}"
                )
                raise ResolvepayAPIException(
                    408, f"Request timeout after {self.timeout} seconds"
                )

            except httpx.ConnectError as e:
                last_exception = e
                if attempt < self.max_retries:
                    backoff_time = 2**attempt
                    self.logger.warning(
                        f"Connection error, retrying in {backoff_time}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(backoff_time)
                    continue
                self.logger.error(f"Connection error for {method} {url}: {e}")
                raise ResolvepayAPIException(503, f"Connection error: {str(e)}")

            except httpx.HTTPStatusError as e:
                self.logger.error(f"HTTP status error for {method} {url}: {e}")
                raise ResolvepayAPIException(
                    e.response.status_code, f"HTTP status error: {str(e)}"
                )

            except httpx.RequestError as e:
                last_exception = e
                if attempt < self.max_retries:
                    backoff_time = 2**attempt
                    self.logger.warning(
                        f"Request error, retrying in {backoff_time}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(backoff_time)
                    continue
                self.logger.error(f"Request error for {method} {url}: {e}")
                raise ResolvepayAPIException(500, f"Request error: {str(e)}")

            except Exception as e:
                log = traceback.format_exc()
                self.logger.error(f"Unexpected error for {method} {url}: {e}\n{log}")
                raise ResolvepayAPIException(500, f"Unexpected error: {str(e)}")

        # If we exhausted all retries
        if last_exception:
            self.logger.error(
                f"Request failed after {self.max_retries} retries for {method} {url}"
            )
            raise ResolvepayAPIException(
                503,
                f"Request failed after {self.max_retries} retries: {str(last_exception)}",
            )

    def close(self) -> None:
        """Close the HTTP client and release connections"""
        if self.client:
            self.client.close()
            self.logger.debug("HTTP client closed")
