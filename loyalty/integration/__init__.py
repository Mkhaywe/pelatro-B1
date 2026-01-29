"""
Integration helpers for external systems (Kafka, REST adapters).

These are designed to keep the loyalty microservice decoupled from any
specific BSS/CRM implementation (including Xiva). External systems can
connect via events (Kafka) and REST APIs.
"""

from .xiva_client import XivaClient, XivaAPIError, get_xiva_client
from .external import ExternalServiceError, fetch_customer_context

__all__ = [
    'XivaClient',
    'XivaAPIError',
    'get_xiva_client',
    'ExternalServiceError',
    'fetch_customer_context',
]

