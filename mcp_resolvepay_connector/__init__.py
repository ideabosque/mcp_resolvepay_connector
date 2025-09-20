#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

__author__ = "bibow"
__version__ = "0.1.0"

# Authentication
from .auth import ResolvepayAuth

# Exceptions
from .exceptions import (
    ResolvepayAPIException,
    ResolvepayAuthenticationException,
    ResolvepayBaseException,
    ResolvepayConfigurationException,
    ResolvepayCustomerNotFoundException,
    ResolvepayRateLimitException,
    ResolvepayValidationException,
)

# HTTP Client
from .http_client import ResolvepayHTTPClient

# Core connector
from .mcp_resolvepay_connector import (
    MCP_CONFIGURATION,
    MCPResolvepayConnector,
    handle_resolvepay_errors,
)

# Models
from .models import (
    CreditCheckRequest,
    CreditCheckResult,
    CreditCheckStatus,
    CustomerRequest,
    CustomerResponse,
    PaymentTerms,
    ResolvepayConfig,
)

# Rate Limiter
from .rate_limiter import RateLimiter

__all__ = [
    # Core
    "MCPResolvepayConnector",
    "MCP_CONFIGURATION",
    "handle_resolvepay_errors",
    # Auth
    "ResolvepayAuth",
    # HTTP Client
    "ResolvepayHTTPClient",
    # Models
    "PaymentTerms",
    "CreditCheckStatus",
    "ResolvepayConfig",
    "CustomerRequest",
    "CustomerResponse",
    "CreditCheckRequest",
    "CreditCheckResult",
    # Exceptions
    "ResolvepayBaseException",
    "ResolvepayAPIException",
    "ResolvepayAuthenticationException",
    "ResolvepayValidationException",
    "ResolvepayRateLimitException",
    "ResolvepayConfigurationException",
    "ResolvepayCustomerNotFoundException",
    # Rate Limiter
    "RateLimiter",
]
