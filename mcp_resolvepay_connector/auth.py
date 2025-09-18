#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

__author__ = "bibow"

import base64
import logging
from typing import Dict, Optional

from .exceptions import ResolvepayAuthenticationException, ResolvepayConfigurationException


class ResolvepayAuth:
    """Authentication handler for ResolvePay API"""

    def __init__(self, merchant_id: str, api_key: str, logger: Optional[logging.Logger] = None):
        self.merchant_id = merchant_id
        self.api_key = api_key
        self.logger = logger or logging.getLogger(__name__)

        if not merchant_id:
            raise ResolvepayConfigurationException("merchant_id is required for authentication")
        if not api_key:
            raise ResolvepayConfigurationException("api_key is required for authentication")

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        try:
            auth_string = f"{self.merchant_id}:{self.api_key}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()

            return {
                "Authorization": f"Basic {encoded_auth}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        except Exception as e:
            self.logger.error(f"Failed to create authentication headers: {e}")
            raise ResolvepayAuthenticationException(f"Authentication header creation failed: {e}")

    def validate_credentials(self) -> bool:
        """Validate that credentials are properly formatted"""
        try:
            if not self.merchant_id or not isinstance(self.merchant_id, str):
                return False
            if not self.api_key or not isinstance(self.api_key, str):
                return False
            if len(self.merchant_id.strip()) == 0 or len(self.api_key.strip()) == 0:
                return False
            return True
        except Exception:
            return False

    def update_credentials(self, merchant_id: str, api_key: str) -> None:
        """Update authentication credentials"""
        if not merchant_id:
            raise ResolvepayConfigurationException("merchant_id cannot be empty")
        if not api_key:
            raise ResolvepayConfigurationException("api_key cannot be empty")

        self.merchant_id = merchant_id
        self.api_key = api_key
        self.logger.info("Authentication credentials updated successfully")