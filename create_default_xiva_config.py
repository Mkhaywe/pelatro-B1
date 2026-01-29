#!/usr/bin/env python
"""
Create default Xiva external system configuration for product catalog sync.
Run this script after migrations to set up Xiva integration.
"""
import os
import sys
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')

import django
django.setup()

from loyalty.models_khaywe import ExternalSystemConfig
import logging

logger = logging.getLogger(__name__)


def create_default_xiva_config():
    """Create default Xiva external system configuration"""
    
    print("\n" + "="*80)
    print("CREATING DEFAULT XIVA EXTERNAL SYSTEM CONFIGURATION")
    print("="*80)
    
    # Check if Xiva config already exists
    existing = ExternalSystemConfig.objects.filter(
        system_type='xiva',
        name__icontains='Xiva'
    ).first()
    
    if existing:
        print(f"\n[INFO] Xiva configuration already exists: {existing.name}")
        print(f"       ID: {existing.id}")
        print(f"       Base URL: {existing.base_url}")
        print(f"       Active: {existing.is_active}")
        print("[UPDATE] Updating existing configuration with correct settings...")
        config = existing
    else:
        config = ExternalSystemConfig()
    
    # Set Xiva configuration - Use same settings as working XivaClient
    from django.conf import settings
    
    config.name = "Xiva Production"
    config.system_type = 'xiva'
    
    # Use the same base URL as XivaClient (from environment or settings)
    config.base_url = (os.environ.get('XIVA_API_BASE_URL', '') or getattr(settings, 'XIVA_API_BASE_URL', 'https://www.xiva.ca/api')).rstrip('/')
    config.api_version = "v5"
    
    # Authentication - JWT (same as XivaClient)
    config.auth_type = 'jwt'
    config.auth_endpoint = "/auth/jwt/create/"  # Same as XivaClient uses
    config.refresh_endpoint = "/auth/jwt/refresh/"  # JWT refresh endpoint
    
    # Credentials - Use same environment variables as XivaClient
    print("\n[CONFIG] Authentication Credentials:")
    print("         Using same credentials as XivaClient (XIVA_API_USERNAME / XIVA_API_PASSWORD)")
    config.client_id = os.environ.get('XIVA_API_USERNAME', '') or getattr(settings, 'XIVA_API_USERNAME', '')
    config.client_secret = os.environ.get('XIVA_API_PASSWORD', '') or getattr(settings, 'XIVA_API_PASSWORD', '')
    
    # Endpoints - TMF620 Product Catalog Management
    # Note: The endpoint path should NOT include the base URL, just the path
    config.endpoints = {
        'products': 'productCatalogManagement/v5/productOffering/',
        'categories': 'productCatalogManagement/v5/category/',
        'product_specifications': 'productCatalogManagement/v5/productSpecification/',
    }
    
    # Custom headers (if needed)
    config.custom_headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    
    # Request configuration
    config.timeout = 30
    config.max_retries = 3
    config.retry_backoff = 'exponential'
    
    # Rate limiting
    config.rate_limit_per_minute = 300
    config.rate_limit_per_hour = 10000
    
    # Connection pool
    config.max_connections = 20
    config.max_connections_per_host = 10
    
    # Token management
    config.token_refresh_buffer = 300  # Refresh 5 minutes before expiry
    config.token_cache_enabled = True
    
    # SSL/TLS
    config.verify_ssl = True
    
    # Status
    config.is_active = True
    config.is_production = True
    
    # Description
    config.description = """Xiva Production API Configuration
TMF620 Product Catalog Management API
- Product Offerings: productCatalogManagement/v5/productOffering/
- Authentication: JWT (Bearer Token) - Same as customer API
- Base URL: Uses XIVA_API_BASE_URL environment variable
- Credentials: Uses XIVA_API_USERNAME and XIVA_API_PASSWORD (same as customer API)

This configuration uses the same authentication as the working Xiva customer API."""
    
    config.save()
    
    print(f"\n[SUCCESS] Xiva configuration {'updated' if existing else 'created'}!")
    print(f"         ID: {config.id}")
    print(f"         Name: {config.name}")
    print(f"         Base URL: {config.base_url}")
    print(f"         Products Endpoint: {config.endpoints.get('products', 'N/A')}")
    print(f"         Auth Type: {config.auth_type}")
    print(f"         Active: {config.is_active}")
    
    if not config.client_id or not config.client_secret:
        print("\n[WARNING] Username and/or Password are not set!")
        print("          Please set them via environment variables:")
        print("          - XIVA_API_USERNAME (same as used by customer API)")
        print("          - XIVA_API_PASSWORD (same as used by customer API)")
        print("          Or update via Admin > External Systems Config UI")
    else:
        print(f"\n[INFO] Credentials loaded from environment variables")
        print(f"       Username: {config.client_id[:3]}*** (hidden)")
    
    print("\n" + "="*80)
    return config


if __name__ == '__main__':
    try:
        create_default_xiva_config()
        print("\n[COMPLETE] Default Xiva configuration is ready!")
        print("          You can now sync products from Xiva via:")
        print("          Admin > Product Catalog > Sync from External System")
    except Exception as e:
        logger.exception(f"Error creating Xiva configuration: {e}")
        print(f"\n[ERROR] Failed to create Xiva configuration: {e}")
        sys.exit(1)

