#!/usr/bin/env python
"""Quick test of Xiva connection"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
import django
django.setup()

from loyalty.integration.xiva_client import XivaClient, XivaAPIError

print("Testing Xiva connection...")
try:
    client = XivaClient()
    print(f"[OK] XivaClient initialized")
    print(f"  Base URL: {client.base_url}")
    print(f"  Auth Type: {client.auth_type}")
    
    if hasattr(client, 'access_token') and client.access_token:
        print(f"  Access Token: Present")
    else:
        print(f"  Access Token: Not yet obtained")
    
    # Try to get customers
    print("\nAttempting to fetch customers...")
    customers = client.get_customer_list(limit=1)
    print(f"[OK] Successfully retrieved {len(customers) if isinstance(customers, list) else 0} customer(s)")
    
except XivaAPIError as e:
    print(f"[ERROR] Xiva API Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[OK] All tests passed!")

