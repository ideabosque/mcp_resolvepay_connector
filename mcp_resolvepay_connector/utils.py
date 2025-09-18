#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

__author__ = "bibow"

import re
from typing import Any, Dict, List, Optional


def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_country_code(country_code: str) -> bool:
    """Validate 2-letter ISO country code"""
    if not country_code:
        return False
    return len(country_code) == 2 and country_code.isalpha()


def validate_phone_number(phone: str) -> bool:
    """Basic phone number validation"""
    if not phone:
        return True
    # Remove all non-digits to count actual digits
    digits_only = re.sub(r'[^\d]', '', phone)
    return len(digits_only) >= 10


def normalize_business_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize business data for consistency"""
    normalized = data.copy()

    if 'business_name' in normalized:
        normalized['business_name'] = normalized['business_name'].strip()

    if 'business_address' in normalized:
        normalized['business_address'] = normalized['business_address'].strip()

    if 'business_city' in normalized:
        normalized['business_city'] = normalized['business_city'].strip()

    if 'business_state' in normalized:
        normalized['business_state'] = normalized['business_state'].strip().upper()

    if 'business_country' in normalized:
        normalized['business_country'] = normalized['business_country'].strip().upper()

    if 'business_zip' in normalized:
        normalized['business_zip'] = normalized['business_zip'].strip()

    for email_field in ['email', 'business_ap_email']:
        if email_field in normalized:
            normalized[email_field] = normalized[email_field].strip().lower()

    return normalized


def extract_numeric_id(id_value: Any) -> Optional[str]:
    """Extract numeric ID from various formats"""
    if not id_value:
        return None

    if isinstance(id_value, (int, float)):
        return str(int(id_value))

    if isinstance(id_value, str):
        match = re.search(r'\d+', id_value)
        if match:
            return match.group()

    return None


def format_currency(amount: Optional[float]) -> str:
    """Format currency amount for display"""
    if amount is None:
        return "N/A"
    return f"${amount:,.2f}"


def sanitize_response_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize response data by removing sensitive information"""
    sensitive_fields = ['api_key', 'password', 'secret', 'token']
    sanitized = {}

    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_response_data(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_response_data(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


def build_search_filters(criteria: Dict[str, Any]) -> Dict[str, Any]:
    """Build search filters from criteria"""
    filters = {}

    if criteria.get('email'):
        filters['email'] = criteria['email'].strip().lower()

    if criteria.get('business_name'):
        filters['business_name'] = criteria['business_name'].strip()

    if criteria.get('business_state'):
        filters['business_state'] = criteria['business_state'].strip().upper()

    if criteria.get('business_country'):
        filters['business_country'] = criteria['business_country'].strip().upper()

    if criteria.get('credit_status'):
        filters['credit_status'] = criteria['credit_status']

    return filters


def paginate_results(
    results: List[Any],
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> Dict[str, Any]:
    """Paginate results with metadata"""
    total = len(results)

    if offset:
        results = results[offset:]

    if limit:
        results = results[:limit]

    return {
        'items': results,
        'total': total,
        'limit': limit,
        'offset': offset or 0,
        'has_more': total > (offset or 0) + len(results)
    }