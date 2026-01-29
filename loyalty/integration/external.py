"""
REST adapters to external systems (e.g., customer/CRM context).

These helpers allow the loyalty microservice to fetch context without
direct database coupling to Xiva (or any other BSS). They are optional
and guarded by settings flags.
"""

from typing import Any, Dict, Optional

import requests
from django.conf import settings


class ExternalServiceError(Exception):
    """Raised when an external service call fails."""


def fetch_customer_context(customer_id: str) -> Dict[str, Any]:
    """
    Fetch customer context from an external API.

    Expects:
        settings.LOYALTY_CUSTOMER_API_BASE_URL (e.g., https://crm/api/customers)
        settings.LOYALTY_CUSTOMER_API_AUTH_TOKEN (Bearer token, optional)

    Returns a dict with at least an `id` field.
    """
    base = getattr(settings, "LOYALTY_CUSTOMER_API_BASE_URL", "")
    if not base:
        raise ExternalServiceError("LOYALTY_CUSTOMER_API_BASE_URL is not configured")

    url = f"{base.rstrip('/')}/{customer_id}"
    headers = {}
    token = getattr(settings, "LOYALTY_CUSTOMER_API_AUTH_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(url, headers=headers, timeout=5)
    if not resp.ok:
        raise ExternalServiceError(f"Customer API returned {resp.status_code}: {resp.text}")

    data = resp.json()
    if not data or "id" not in data:
        raise ExternalServiceError("Customer API response missing 'id'")
    return data


def extract_customer_id(customer_payload: Any) -> Optional[str]:
    """
    Normalize customer identifier from varied payloads (str, int, dict with id).
    """
    if customer_payload is None:
        return None
    if isinstance(customer_payload, (str, int)):
        return str(customer_payload)
    if isinstance(customer_payload, dict):
        cid = customer_payload.get("id") or customer_payload.get("customer_id")
        return str(cid) if cid else None
    return None



