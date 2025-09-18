#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

__author__ = "bibow"

from typing import Any, Dict, Optional


class ResolvepayBaseException(Exception):
    """Base exception for all ResolvePay connector errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ResolvepayAPIException(ResolvepayBaseException):
    """Exception for ResolvePay API errors"""

    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(message, details)


class ResolvepayAuthenticationException(ResolvepayBaseException):
    """Exception for authentication errors"""

    pass


class ResolvepayValidationException(ResolvepayBaseException):
    """Exception for data validation errors"""

    pass


class ResolvepayRateLimitException(ResolvepayAPIException):
    """Exception for rate limit errors"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.retry_after = retry_after
        super().__init__(429, message, details)


class ResolvepayConfigurationException(ResolvepayBaseException):
    """Exception for configuration errors"""

    pass


class ResolvepayCustomerNotFoundException(ResolvepayAPIException):
    """Exception for when customer is not found"""

    def __init__(self, customer_id: str, details: Optional[Dict[str, Any]] = None):
        self.customer_id = customer_id
        message = f"Customer not found: {customer_id}"
        super().__init__(404, message, details)