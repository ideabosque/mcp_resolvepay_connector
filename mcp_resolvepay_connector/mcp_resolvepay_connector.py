#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

__author__ = "bibow"

import logging
import traceback
from functools import wraps
from typing import Any, Dict, List, Optional

from .auth import ResolvepayAuth
from .exceptions import (
    ResolvepayAPIException,
    ResolvepayConfigurationException,
    ResolvepayCustomerNotFoundException,
    ResolvepayValidationException,
)
from .http_client import ResolvepayHTTPClient
from .models import (
    CreditCheckRequest,
    CreditCheckResult,
    CustomerRequest,
    CustomerResponse,
    PaymentTerms,
    ResolvepayConfig,
)
from .rate_limiter import RateLimiter

MCP_CONFIGURATION = {
    "tools": [
        {
            "name": "create_customer",
            "description": "Create a new business customer in ResolvePay with complete business information including contact details and payment terms. This function validates all required fields and creates a customer record that can be used for credit checks and payment processing.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "business_name": {
                        "type": "string",
                        "description": "Legal business name of the customer",
                    },
                    "business_address": {
                        "type": "string",
                        "description": "Street address of the business location",
                    },
                    "business_city": {
                        "type": "string",
                        "description": "City where the business is located",
                    },
                    "business_state": {
                        "type": "string",
                        "description": "State/province code (e.g., NY, CA)",
                    },
                    "business_zip": {
                        "type": "string",
                        "description": "ZIP/postal code for the business",
                    },
                    "business_country": {
                        "type": "string",
                        "description": "2-letter ISO country code (e.g., US, CA)",
                    },
                    "business_ap_email": {
                        "type": "string",
                        "description": "Accounts payable email address for billing",
                    },
                    "email": {
                        "type": "string",
                        "description": "Primary business contact email address",
                    },
                    "business_ap_phone": {
                        "type": "string",
                        "description": "Phone number in ###-###-#### format (optional)",
                    },
                    "business_ap_phone_extension": {
                        "type": "string",
                        "description": "Phone extension if applicable (optional)",
                    },
                    "default_terms": {
                        "type": "string",
                        "enum": ["net7", "net10", "net15", "net30", "net45", "net60", "net90"],
                        "description": "Default payment terms for the customer (optional)",
                    },
                },
                "required": [
                    "business_name",
                    "business_address",
                    "business_city",
                    "business_state",
                    "business_zip",
                    "business_country",
                    "business_ap_email",
                    "email",
                ],
            },
            "annotations": None,
        },
        {
            "name": "get_customer",
            "description": "Retrieve detailed information for a specific customer by their unique ID. Returns complete customer profile including business details, contact information, credit status, and available credit amounts.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Unique identifier for the customer to retrieve",
                    }
                },
                "required": ["customer_id"],
            },
            "annotations": None,
        },
        {
            "name": "update_customer",
            "description": "Update existing customer information with new business details, contact information, or payment terms. Only provided fields will be updated, allowing for partial updates without affecting other customer data.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Unique identifier for the customer to update",
                    },
                    "business_name": {
                        "type": "string",
                        "description": "Updated legal business name (optional)",
                    },
                    "business_address": {
                        "type": "string",
                        "description": "Updated street address (optional)",
                    },
                    "business_city": {"type": "string", "description": "Updated city (optional)"},
                    "business_state": {
                        "type": "string",
                        "description": "Updated state/province code (optional)",
                    },
                    "business_zip": {
                        "type": "string",
                        "description": "Updated ZIP/postal code (optional)",
                    },
                    "business_country": {
                        "type": "string",
                        "description": "Updated 2-letter country code (optional)",
                    },
                    "business_ap_email": {
                        "type": "string",
                        "description": "Updated accounts payable email (optional)",
                    },
                    "email": {
                        "type": "string",
                        "description": "Updated primary contact email (optional)",
                    },
                    "business_ap_phone": {
                        "type": "string",
                        "description": "Updated phone number in ###-###-#### format (optional)",
                    },
                    "business_ap_phone_extension": {
                        "type": "string",
                        "description": "Updated phone extension (optional)",
                    },
                    "default_terms": {
                        "type": "string",
                        "enum": ["net7", "net10", "net15", "net30", "net45", "net60", "net90"],
                        "description": "Updated default payment terms (optional)",
                    },
                },
                "required": ["customer_id"],
            },
            "annotations": None,
        },
        {
            "name": "search_customers",
            "description": "Search for customers using various criteria including business name, email, or other business details. Supports filtering and pagination for handling large result sets efficiently.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "business_name": {
                        "type": "string",
                        "description": "Search by business name (partial matches supported)",
                    },
                    "email": {
                        "type": "string",
                        "description": "Search by primary contact email address",
                    },
                    "business_ap_email": {
                        "type": "string",
                        "description": "Search by accounts payable email address",
                    },
                    "business_city": {"type": "string", "description": "Search by business city"},
                    "business_state": {
                        "type": "string",
                        "description": "Search by business state/province",
                    },
                    "business_zip": {
                        "type": "string",
                        "description": "Search by business ZIP/postal code",
                    },
                    "business_country": {
                        "type": "string",
                        "description": "Search by business country code",
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number for pagination (default: 1)",
                        "minimum": 1,
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Number of results per page (default: 50)",
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
                "required": [],
            },
            "annotations": None,
        },
        {
            "name": "request_customer_credit_check",
            "description": "Initiate a credit check process for an existing customer to determine their creditworthiness and available credit limit. This process may take time to complete and should be followed up with status checks.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Unique identifier for the customer to check",
                    },
                    "amount_requested": {
                        "type": "number",
                        "description": "Amount of credit being requested for evaluation",
                    },
                    "has_purchase_history": {
                        "type": "boolean",
                        "description": "Whether the customer has previous purchase history with the merchant",
                    },
                },
                "required": ["customer_id", "amount_requested", "has_purchase_history"],
            },
            "annotations": None,
        },
        {
            "name": "get_credit_check_status",
            "description": "Retrieve the current status and results of a credit check for a customer. Returns credit approval status, approved amounts, and any available credit limits that have been established.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Unique identifier for the customer whose credit check status to retrieve",
                    }
                },
                "required": ["customer_id"],
            },
            "annotations": None,
        },
        {
            "name": "validate_customer_data",
            "description": "Validate customer data for format and completeness without creating or modifying any records. Useful for pre-validation before customer creation or to check data quality before API calls.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "business_name": {"type": "string", "description": "Business name to validate"},
                    "business_address": {
                        "type": "string",
                        "description": "Business address to validate",
                    },
                    "business_city": {"type": "string", "description": "Business city to validate"},
                    "business_state": {
                        "type": "string",
                        "description": "Business state/province to validate",
                    },
                    "business_zip": {
                        "type": "string",
                        "description": "Business ZIP/postal code to validate",
                    },
                    "business_country": {
                        "type": "string",
                        "description": "Business country code to validate",
                    },
                    "business_ap_email": {
                        "type": "string",
                        "description": "Accounts payable email to validate",
                    },
                    "email": {"type": "string", "description": "Primary contact email to validate"},
                    "business_ap_phone": {
                        "type": "string",
                        "description": "Phone number to validate (optional)",
                    },
                    "business_ap_phone_extension": {
                        "type": "string",
                        "description": "Phone extension to validate (optional)",
                    },
                    "default_terms": {
                        "type": "string",
                        "enum": ["net7", "net10", "net15", "net30", "net45", "net60", "net90"],
                        "description": "Payment terms to validate (optional)",
                    },
                },
                "required": [],
            },
            "annotations": None,
        },
    ],
    "resources": [],
    "prompts": [],
    "module_links": [
        {
            "type": "tool",
            "name": "create_customer",
            "module_name": "mcp_resolvepay_connector",
            "class_name": "MCPResolvepayConnector",
            "function_name": "create_customer",
            "return_type": "text",
        },
        {
            "type": "tool",
            "name": "get_customer",
            "module_name": "mcp_resolvepay_connector",
            "class_name": "MCPResolvepayConnector",
            "function_name": "get_customer",
            "return_type": "text",
        },
        {
            "type": "tool",
            "name": "update_customer",
            "module_name": "mcp_resolvepay_connector",
            "class_name": "MCPResolvepayConnector",
            "function_name": "update_customer",
            "return_type": "text",
        },
        {
            "type": "tool",
            "name": "search_customers",
            "module_name": "mcp_resolvepay_connector",
            "class_name": "MCPResolvepayConnector",
            "function_name": "search_customers",
            "return_type": "text",
        },
        {
            "type": "tool",
            "name": "request_customer_credit_check",
            "module_name": "mcp_resolvepay_connector",
            "class_name": "MCPResolvepayConnector",
            "function_name": "request_customer_credit_check",
            "return_type": "text",
        },
        {
            "type": "tool",
            "name": "get_credit_check_status",
            "module_name": "mcp_resolvepay_connector",
            "class_name": "MCPResolvepayConnector",
            "function_name": "get_credit_check_status",
            "return_type": "text",
        },
        {
            "type": "tool",
            "name": "validate_customer_data",
            "module_name": "mcp_resolvepay_connector",
            "class_name": "MCPResolvepayConnector",
            "function_name": "validate_customer_data",
            "return_type": "text",
        },
    ],
    "modules": [
        {
            "package_name": "mcp_resolvepay_connector",
            "module_name": "mcp_resolvepay_connector",
            "class_name": "MCPResolvepayConnector",
            "setting": {
                "merchant_id": "<merchant_id>",
                "api_key": "<api_key>",
                "base_url": "https://api.resolvepay.com/v5",
                "timeout": 30,
                "max_retries": 3,
                "rate_limit_calls_per_second": 10,
                "debug_mode": True,
            },
        }
    ],
}


def handle_resolvepay_errors(func):
    """Decorator to handle ResolvePay API errors consistently"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ResolvepayAPIException as e:
            logging.error(f"ResolvePay API error in {func.__name__}: {e}")
            raise Exception(f"ResolvePay API error: {e.message}")
        except ResolvepayValidationException as e:
            logging.error(f"Validation error in {func.__name__}: {e}")
            raise Exception(f"Validation error: {e.message}")
        except Exception as e:
            logging.error(f"Unexpected error in {func.__name__}: {e}")
            raise Exception(f"Unexpected error: {str(e)}")

    return wrapper


class MCPResolvepayConnector:
    """Main connector class for ResolvePay API integration"""

    def __init__(self, logger: logging.Logger, **settings: Dict[str, Any]):
        self.logger = logger
        self.settings = settings

        self.config = self._create_config(settings)
        self.auth = ResolvepayAuth(self.config.merchant_id, self.config.api_key, logger)
        self.rate_limiter = RateLimiter(self.config.rate_limit_calls_per_second)
        self.http_client = ResolvepayHTTPClient(
            base_url=self.config.base_url,
            auth=self.auth,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            rate_limiter=self.rate_limiter,
            logger=logger,
        )

        self.logger.info("MCPResolvepayConnector initialized successfully")

    def _create_config(self, settings: Dict[str, Any]) -> ResolvepayConfig:
        """Create configuration from settings"""
        try:
            return ResolvepayConfig(
                merchant_id=settings.get("merchant_id", ""),
                api_key=settings.get("api_key", ""),
                base_url=settings.get("base_url", "https://api.resolvepay.com/v5"),
                timeout=int(settings.get("timeout", 30)),
                max_retries=int(settings.get("max_retries", 3)),
                rate_limit_calls_per_second=int(settings.get("rate_limit_calls_per_second", 10)),
                debug_mode=settings.get("debug_mode", False),
            )
        except ValueError as e:
            raise ResolvepayConfigurationException(f"Configuration error: {e}")

    def _validate_customer_data(
        self, customer_data: Dict[str, Any], is_update: bool = False
    ) -> None:
        """Validate customer data before API call"""
        if not is_update:
            # For creation, all fields are required
            required_fields = [
                "business_name",
                "business_address",
                "business_city",
                "business_state",
                "business_zip",
                "business_country",
                "business_ap_email",
                "email",
            ]

            missing_fields = [field for field in required_fields if not customer_data.get(field)]
            if missing_fields:
                raise ResolvepayValidationException(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )

        # Validate business_country format only if it's provided
        business_country = customer_data.get("business_country")
        if business_country and len(business_country) != 2:
            raise ResolvepayValidationException(
                "business_country must be a 2-letter ISO 3166-1 country code"
            )

        for email_field in ["email", "business_ap_email"]:
            email = customer_data.get(email_field, "")
            if email and "@" not in email:
                raise ResolvepayValidationException(f"Invalid email format for {email_field}")

        # Validate business_ap_phone format if provided (ResolvePay requires ###-###-#### format)
        business_phone = customer_data.get("business_ap_phone")
        if business_phone:
            import re

            # Must be exactly ###-###-#### format (10 digits with dashes)
            if not re.match(r"^\d{3}-\d{3}-\d{4}$", business_phone):
                raise ResolvepayValidationException(
                    f"Invalid phone number format. Must be ###-###-#### (e.g., 212-555-0123), got: {business_phone}"
                )

            # ResolvePay may reject test/fake phone numbers like 555-xxx-xxxx
            # For real usage, use valid US area codes like 212, 415, 310, etc.
            if business_phone.startswith("555-"):
                self.logger.warning(
                    f"Phone number {business_phone} uses 555 area code which may be rejected by ResolvePay. "
                    f"Consider using a real area code like 212-555-0123 for production use."
                )

    # * MCP Function.
    @handle_resolvepay_errors
    def create_customer(self, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer in ResolvePay

        Args:
            business_name (str): Required. The legal business name of the customer
            business_address (str): Required. Street address of the business
            business_city (str): Required. City where the business is located
            business_state (str): Required. State/province code (e.g., "NY", "CA")
            business_zip (str): Required. ZIP/postal code for the business
            business_country (str): Required. 2-letter ISO 3166-1 country code (e.g., "US", "CA")
            business_ap_email (str): Required. Accounts payable email address for billing
            email (str): Required. Primary contact email address for the business
            business_ap_phone (str): Optional. Business phone number in ###-###-#### format
            business_ap_phone_extension (str): Optional. Phone extension number
            business_website (str): Optional. Business website URL
            business_ein (str): Optional. Employer Identification Number (EIN)
            business_duns (str): Optional. D-U-N-S Number for the business
            default_terms (str): Optional. Default payment terms (e.g., "net30", "net60")

        Returns:
            Dict containing:
                - success (bool): True if customer was created successfully
                - customer (dict): Customer object with assigned ID and details
                - message (str): Success message

        Raises:
            ResolvepayValidationException: If required fields are missing or invalid
            ResolvepayAPIException: If API request fails

        Example:
            result = connector.create_customer(
                business_name="Acme Corp",
                business_address="123 Main St",
                business_city="New York",
                business_state="NY",
                business_zip="10001",
                business_country="US",
                business_ap_email="ap@acme.com",
                email="contact@acme.com",
                business_ap_phone="212-555-0123"
            )
        """
        try:
            self.logger.info(f"Creating customer with arguments: {arguments}")

            customer_data = arguments.copy()
            self._validate_customer_data(customer_data)

            customer_request = CustomerRequest.from_dict(customer_data)
            request_data = customer_request.to_dict()

            response_data = self.http_client.post("customers", data=request_data)

            customer_response = CustomerResponse.from_dict(response_data)

            return {
                "success": True,
                "customer": customer_response.to_dict(),
                "message": "Customer created successfully",
            }

        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(f"Create customer failed: {e}\n{log}")
            return {
                "success": False,
                "customer": None,
                "error": str(e),
                "message": "Failed to create customer",
            }

    # * MCP Function.
    @handle_resolvepay_errors
    def get_customer(self, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve customer information by ID

        Args:
            customer_id (str): Required. The unique customer ID assigned by ResolvePay

        Returns:
            Dict containing:
                - success (bool): True if customer was found and retrieved
                - customer (dict): Complete customer object with all details
                - message (str): Success message

        Raises:
            ResolvepayValidationException: If customer_id is missing
            ResolvepayAPIException: If API request fails or customer not found

        Example:
            result = connector.get_customer(customer_id="cust_123456")
        """
        try:
            self.logger.info(f"Getting customer with arguments: {arguments}")

            customer_id = arguments.get("customer_id")
            if not customer_id:
                raise ResolvepayValidationException("customer_id is required")

            response_data = self.http_client.get(f"customers/{customer_id}")

            customer_response = CustomerResponse.from_dict(response_data)

            return {
                "success": True,
                "customer": customer_response.to_dict(),
                "message": "Customer retrieved successfully",
            }

        except ResolvepayAPIException as e:
            if e.status_code == 404:
                return {
                    "success": False,
                    "customer": None,
                    "error": f"Customer not found: {arguments.get('customer_id')}",
                    "message": "Customer not found",
                }
            raise

        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(f"Get customer failed: {e}\n{log}")
            return {
                "success": False,
                "customer": None,
                "error": str(e),
                "message": "Failed to retrieve customer",
            }

    # * MCP Function.
    @handle_resolvepay_errors
    def update_customer(self, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing customer information

        Args:
            customer_id (str): Required. The unique customer ID to update
            business_name (str): Optional. Updated legal business name
            business_address (str): Optional. Updated street address
            business_city (str): Optional. Updated city name
            business_state (str): Optional. Updated state/province code
            business_zip (str): Optional. Updated ZIP/postal code
            business_country (str): Optional. Updated 2-letter country code
            business_ap_email (str): Optional. Updated accounts payable email
            email (str): Optional. Updated primary contact email
            business_ap_phone (str): Optional. Updated phone number (###-###-####)
            business_ap_phone_extension (str): Optional. Updated phone extension
            business_website (str): Optional. Updated website URL
            business_ein (str): Optional. Updated EIN number
            business_duns (str): Optional. Updated D-U-N-S number
            default_terms (str): Optional. Updated payment terms

        Returns:
            Dict containing:
                - success (bool): True if customer was updated successfully
                - customer (dict): Updated customer object with new details
                - message (str): Success message

        Raises:
            ResolvepayValidationException: If customer_id is missing or validation fails
            ResolvepayAPIException: If API request fails or customer not found

        Note:
            Only provided fields will be updated. Omitted fields remain unchanged.

        Example:
            result = connector.update_customer(
                customer_id="cust_123456",
                business_name="Acme Corporation",
                email="newcontact@acme.com"
            )
        """
        try:
            self.logger.info(f"Updating customer with arguments: {arguments}")

            customer_id = arguments.get("customer_id")
            if not customer_id:
                raise ResolvepayValidationException("customer_id is required")

            update_data = arguments.copy()
            del update_data["customer_id"]

            if update_data:
                self._validate_customer_data(update_data, is_update=True)

            response_data = self.http_client.put(f"customers/{customer_id}", data=update_data)

            customer_response = CustomerResponse.from_dict(response_data)

            return {
                "success": True,
                "customer": customer_response.to_dict(),
                "message": "Customer updated successfully",
            }

        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(f"Update customer failed: {e}\n{log}")
            return {
                "success": False,
                "customer": None,
                "error": str(e),
                "message": "Failed to update customer",
            }

    # * MCP Function.
    @handle_resolvepay_errors
    def search_customers(self, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Search customers by various criteria

        Args:
            email (str): Optional. Search by customer email address (exact match)
            business_name (str): Optional. Search by business name (exact match)
            limit (int): Optional. Maximum number of results to return (25-100, default: 25)
            page (str): Optional. Page number for pagination (default: "1")
            offset (int): Optional. Alternative to page - number of records to skip

        Returns:
            Dict containing:
                - success (bool): True if search completed successfully
                - customers (list): List of customer objects matching criteria
                - total (int): Total number of customers found
                - page (int): Current page number
                - limit (int): Results per page limit
                - message (str): Success message

        Raises:
            ResolvepayAPIException: If API request fails

        Note:
            - Search uses exact match filtering (not partial/fuzzy matching)
            - Results are paginated with 25-100 customers per page
            - If no criteria provided, returns all customers with pagination
            - The limit will be adjusted to ResolvePay's required range (25-100)

        Example:
            # Search by email
            result = connector.search_customers(email="contact@acme.com")

            # Search by business name with pagination
            result = connector.search_customers(
                business_name="Acme Corp",
                limit=50,
                page="2"
            )

            # Get all customers (first page)
            result = connector.search_customers(limit=25)
        """
        try:
            self.logger.info(f"Searching customers with arguments: {arguments}")

            search_params = {}

            # ResolvePay API uses filter syntax for search parameters
            if arguments.get("email"):
                search_params["filter[email][eq]"] = arguments["email"]
            if arguments.get("business_name"):
                search_params["filter[business_name][eq]"] = arguments["business_name"]

            # API uses 'page' parameter, not 'offset'
            if arguments.get("page"):
                search_params["page"] = str(arguments["page"])
            elif arguments.get("offset"):
                # Convert offset to page if needed (assuming limit is known)
                limit = arguments.get("limit", 25)
                page = (arguments["offset"] // limit) + 1
                search_params["page"] = str(page)

            # Limit must be between 25-100, default 25
            if arguments.get("limit"):
                limit = max(25, min(100, arguments["limit"]))
                search_params["limit"] = limit

            response_data = self.http_client.get("customers", params=search_params)

            customers = []
            total_count = 0

            # API returns 'results' array with pagination metadata
            if "results" in response_data:
                customers = [
                    CustomerResponse.from_dict(customer).to_dict()
                    for customer in response_data["results"]
                ]
                total_count = response_data.get("count", len(customers))
            elif isinstance(response_data, list):
                # Fallback for direct array response
                customers = [
                    CustomerResponse.from_dict(customer).to_dict() for customer in response_data
                ]
                total_count = len(customers)

            return {
                "success": True,
                "customers": customers,
                "total": total_count,
                "page": response_data.get("page", 1),
                "limit": response_data.get("limit", 25),
                "message": "Customers retrieved successfully",
            }

        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(f"Search customers failed: {e}\n{log}")
            return {
                "success": False,
                "customers": [],
                "total": 0,
                "error": str(e),
                "message": "Failed to search customers",
            }

    # * MCP Function.
    @handle_resolvepay_errors
    def request_customer_credit_check(self, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Request credit check for existing customer

        Args:
            customer_id (str): Required. ID of the customer to check
            amount_requested (float): Required. Credit amount to request for approval
            has_purchase_history (bool): Optional. Whether customer has purchase history. Defaults to False

        Returns:
            Dict containing success status and credit check result

        Note:
            Customer must have a valid US phone number in format ###-###-#### for credit check to succeed.
            If customer phone is missing/invalid, update customer first:
            update_customer(customer_id="...", business_ap_phone="555-123-4567")
        """
        try:
            self.logger.info(f"Requesting credit check with arguments: {arguments}")

            customer_id = arguments.get("customer_id")
            if not customer_id:
                raise ResolvepayValidationException("customer_id is required")

            # Prepare request body for credit check
            request_data = {}

            # amount_requested is required by the API
            amount_requested = arguments.get("amount_requested")
            if not amount_requested:
                raise ResolvepayValidationException("amount_requested is required")

            request_data["amount_requested"] = amount_requested

            # has_purchase_history is required by the API
            has_purchase_history = arguments.get("has_purchase_history")
            if has_purchase_history is None:
                # Default to False if not provided
                has_purchase_history = False

            request_data["has_purchase_history"] = has_purchase_history

            response_data = self.http_client.post(
                f"customers/{customer_id}/credit-check", data=request_data
            )

            # Log response structure for debugging
            self.logger.info(f"Credit check API response: {response_data}")

            if "customer_id" not in response_data:
                response_data["customer_id"] = customer_id

            credit_result = CreditCheckResult.from_dict(response_data)

            return {
                "success": True,
                "credit_check": credit_result.to_dict(),
                "message": "Credit check requested successfully",
            }

        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(f"Credit check request failed: {e}\n{log}")
            return {
                "success": False,
                "credit_check": None,
                "error": str(e),
                "message": "Failed to request credit check",
            }

    # * MCP Function.
    @handle_resolvepay_errors
    def get_credit_check_status(self, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get credit check status and results from customer data

        Note: ResolvePay doesn't have a separate credit check endpoint for retrieval.
        Credit check status is available through the customer object fields:
        - credit_status, credit_check_requested_at, amount_approved, etc.
        """
        try:
            self.logger.info(f"Getting credit check status with arguments: {arguments}")

            customer_id = arguments.get("customer_id")
            if not customer_id:
                raise ResolvepayValidationException("customer_id is required")

            # Get customer data which contains credit check information
            response_data = self.http_client.get(f"customers/{customer_id}")

            # Extract credit check related fields from customer data
            credit_data = {
                "customer_id": customer_id,
                "status": response_data.get("credit_status"),
                "amount_approved": response_data.get("amount_approved"),
                "amount_available": response_data.get("amount_available"),
                "credit_limit": response_data.get("credit_limit"),
                "created_at": response_data.get("credit_check_requested_at"),
                "updated_at": response_data.get("updated_at"),
                "notes": None,  # Not available in customer object
            }

            credit_result = CreditCheckResult.from_dict(credit_data)

            return {
                "success": True,
                "credit_check": credit_result.to_dict(),
                "message": "Credit check status retrieved successfully",
            }

        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(f"Get credit check status failed: {e}\n{log}")
            return {
                "success": False,
                "credit_check": None,
                "error": str(e),
                "message": "Failed to get credit check status",
            }

    # * MCP Function.
    @handle_resolvepay_errors
    def validate_customer_data(self, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate customer data without creating a customer

        Validates customer data fields for format and completeness without making
        any API calls to ResolvePay. Useful for pre-validating data before creation.

        Args:
            business_name (str): Company or business name (required)
            business_address (str): Street address of the business (required)
            business_city (str): City where business is located (required)
            business_state (str): Two-letter state/province code (required)
            business_zip (str): ZIP or postal code (required)
            business_country (str): Two-letter country code, typically "US" (required)
            business_ap_email (str): Accounts payable email address (required)
            email (str): Primary business contact email address (required)
            business_ap_phone (str, optional): Phone number in ###-###-#### format
            business_ap_phone_extension (str, optional): Phone extension if applicable
            default_terms (str, optional): Payment terms (net7, net10, net15, net30, net45, net60, net90)

        Returns:
            Dict[str, Any]: Validation result with structure:
                {
                    "success": bool,
                    "valid": bool,
                    "errors": List[str] or None,
                    "message": str
                }

        Raises:
            ResolvepayValidationException: If required fields are missing or invalid

        Example:
            >>> result = connector.validate_customer_data(
            ...     business_name="Acme Corp",
            ...     business_address="123 Main St",
            ...     business_city="New York",
            ...     business_state="NY",
            ...     business_zip="10001",
            ...     business_country="US",
            ...     business_ap_email="ap@acme.com",
            ...     email="contact@acme.com"
            ... )
            >>> print(result["valid"])  # True if all data is valid
        """
        try:
            self.logger.info(f"Validating customer data with arguments: {arguments}")

            customer_data = arguments.copy()
            self._validate_customer_data(customer_data)

            return {
                "success": True,
                "valid": True,
                "message": "Customer data is valid",
            }

        except ResolvepayValidationException as e:
            return {
                "success": True,
                "valid": False,
                "error": str(e),
                "message": "Customer data validation failed",
            }
        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(f"Validate customer data failed: {e}\n{log}")
            return {
                "success": False,
                "valid": False,
                "error": str(e),
                "message": "Failed to validate customer data",
            }

    def close(self) -> None:
        """Close HTTP client and clean up resources"""
        if self.http_client:
            self.http_client.close()
        self.logger.info("MCPResolvepayConnector closed")
