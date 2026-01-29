#!/usr/bin/env python
"""
Quick test to verify .env file is being loaded correctly
"""
import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
    print("[OK] .env file loaded successfully")
except ImportError:
    print("[ERROR] python-dotenv not installed")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error loading .env: {e}")
    sys.exit(1)

# Check Xiva credentials
username = os.environ.get('XIVA_API_USERNAME', '')
password = os.environ.get('XIVA_API_PASSWORD', '')
base_url = os.environ.get('XIVA_API_BASE_URL', '')
auth_type = os.environ.get('XIVA_API_AUTH_TYPE', '')

print("\n[INFO] Environment Variables:")
print(f"  XIVA_API_USERNAME: {username if username else '[NOT SET]'}")
print(f"  XIVA_API_PASSWORD: {'[SET]' if password else '[NOT SET]'}")
print(f"  XIVA_API_BASE_URL: {base_url if base_url else '[NOT SET]'}")
print(f"  XIVA_API_AUTH_TYPE: {auth_type if auth_type else '[NOT SET]'}")

# Test Django settings loading
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
    import django
    django.setup()
    
    from django.conf import settings
    print("\n[INFO] Django Settings:")
    print(f"  settings.XIVA_API_USERNAME: {settings.XIVA_API_USERNAME if settings.XIVA_API_USERNAME else '[NOT SET]'}")
    print(f"  settings.XIVA_API_PASSWORD: {'[SET]' if settings.XIVA_API_PASSWORD else '[NOT SET]'}")
    print(f"  settings.XIVA_API_BASE_URL: {settings.XIVA_API_BASE_URL}")
    print(f"  settings.XIVA_API_AUTH_TYPE: {settings.XIVA_API_AUTH_TYPE}")
    
    # Test XivaClient initialization
    from loyalty.integration.xiva_client import XivaClient
    print("\n[TEST] Testing XivaClient initialization...")
    client = XivaClient()
    print("[OK] XivaClient initialized successfully")
    
    if hasattr(client, 'access_token') and client.access_token:
        print("[OK] Access token obtained (authenticated)")
    elif client.auth_type == 'JWT':
        print("[WARN] No access token yet (will authenticate on first request)")
    
except Exception as e:
    print(f"\n[ERROR] Error testing Django settings: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[OK] All checks passed! If server is running, restart it to load new .env values.")

