#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

__author__ = "bibow"

from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum


class PaymentTerms(str, Enum):
    """Available payment terms for customers"""

    NET7 = "net7"
    NET10 = "net10"
    NET15 = "net15"
    NET30 = "net30"
    NET45 = "net45"
    NET60 = "net60"
    NET90 = "net90"


class CreditCheckStatus(str, Enum):
    """Credit check status values"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    APPROVED = "approved"
    DENIED = "denied"


@dataclass
class ResolvepayConfig:
    """Configuration for ResolvePay connector"""

    merchant_id: str
    api_key: str
    base_url: str = "https://api.resolvepay.com/v5"
    timeout: int = 30
    max_retries: int = 3
    rate_limit_calls_per_second: int = 10
    debug_mode: bool = False
    http2_enabled: bool = True

    def __post_init__(self):
        if not self.merchant_id:
            raise ValueError("merchant_id is required")
        if not self.api_key:
            raise ValueError("api_key is required")


@dataclass
class CustomerRequest:
    """Data model for creating a customer"""

    business_name: str
    business_address: str
    business_city: str
    business_state: str
    business_zip: str
    business_country: str
    business_ap_email: str
    email: str
    business_ap_phone: Optional[str] = None
    business_ap_phone_extension: Optional[str] = None
    default_terms: Optional[PaymentTerms] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request"""
        data = {
            "business_name": self.business_name,
            "business_address": self.business_address,
            "business_city": self.business_city,
            "business_state": self.business_state,
            "business_zip": self.business_zip,
            "business_country": self.business_country,
            "business_ap_email": self.business_ap_email,
            "email": self.email,
        }

        if self.business_ap_phone:
            data["business_ap_phone"] = self.business_ap_phone
        if self.business_ap_phone_extension:
            data["business_ap_phone_extension"] = self.business_ap_phone_extension
        if self.default_terms:
            data["default_terms"] = self.default_terms.value

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CustomerRequest":
        """Create from dictionary"""
        return cls(
            business_name=data["business_name"],
            business_address=data["business_address"],
            business_city=data["business_city"],
            business_state=data["business_state"],
            business_zip=data["business_zip"],
            business_country=data["business_country"],
            business_ap_email=data["business_ap_email"],
            email=data["email"],
            business_ap_phone=data.get("business_ap_phone"),
            business_ap_phone_extension=data.get("business_ap_phone_extension"),
            default_terms=PaymentTerms(data["default_terms"])
            if data.get("default_terms")
            else None,
        )


@dataclass
class CustomerResponse:
    """Data model for customer response"""

    id: str
    business_name: str
    business_address: str
    business_city: str
    business_state: str
    business_zip: str
    business_country: str
    business_ap_email: str
    email: str
    created_at: str
    updated_at: str
    amount_approved: Optional[float] = None
    amount_available: Optional[float] = None
    business_ap_phone: Optional[str] = None
    business_ap_phone_extension: Optional[str] = None
    default_terms: Optional[str] = None
    credit_status: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CustomerResponse":
        """Create from API response dictionary"""
        return cls(
            id=data["id"],
            business_name=data["business_name"],
            business_address=data["business_address"],
            business_city=data["business_city"],
            business_state=data["business_state"],
            business_zip=data["business_zip"],
            business_country=data["business_country"],
            business_ap_email=data["business_ap_email"],
            email=data["email"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            amount_approved=data.get("amount_approved"),
            amount_available=data.get("amount_available"),
            business_ap_phone=data.get("business_ap_phone"),
            business_ap_phone_extension=data.get("business_ap_phone_extension"),
            default_terms=data.get("default_terms"),
            credit_status=data.get("credit_status"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "business_name": self.business_name,
            "business_address": self.business_address,
            "business_city": self.business_city,
            "business_state": self.business_state,
            "business_zip": self.business_zip,
            "business_country": self.business_country,
            "business_ap_email": self.business_ap_email,
            "email": self.email,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "amount_approved": self.amount_approved,
            "amount_available": self.amount_available,
            "business_ap_phone": self.business_ap_phone,
            "business_ap_phone_extension": self.business_ap_phone_extension,
            "default_terms": self.default_terms,
            "credit_status": self.credit_status,
        }


@dataclass
class CreditCheckRequest:
    """Data model for credit check request"""

    customer_id: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request"""
        return {"customer_id": self.customer_id}


@dataclass
class CreditCheckResult:
    """Data model for credit check result"""

    customer_id: str
    status: CreditCheckStatus
    amount_approved: Optional[float] = None
    amount_available: Optional[float] = None
    credit_limit: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CreditCheckResult":
        """Create from API response dictionary"""
        # Handle missing status field gracefully
        status_value = data.get("status")
        if status_value:
            status = CreditCheckStatus(status_value)
        else:
            # Default to PENDING if no status provided
            status = CreditCheckStatus.PENDING

        return cls(
            customer_id=data.get("customer_id", ""),
            status=status,
            amount_approved=data.get("amount_approved"),
            amount_available=data.get("amount_available"),
            credit_limit=data.get("credit_limit"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            notes=data.get("notes"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "customer_id": self.customer_id,
            "status": self.status.value,
            "amount_approved": self.amount_approved,
            "amount_available": self.amount_available,
            "credit_limit": self.credit_limit,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "notes": self.notes,
        }
