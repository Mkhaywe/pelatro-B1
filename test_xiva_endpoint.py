#!/usr/bin/env python
"""Test Xiva endpoint with authentication"""
import os
import sys
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# First, try to login
print("Step 1: Logging in...")
try:
    login_response = requests.post(
        'http://localhost:8000/api/auth/login/',
        json={'username': 'admin', 'password': 'admin'},
        timeout=5
    )
    print(f"  Login status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        token = login_response.json().get('token')
        print(f"  Token obtained: {token[:20]}..." if token else "  No token in response")
        
        # Now test Xiva endpoint
        print("\nStep 2: Testing Xiva customers endpoint...")
        xiva_response = requests.get(
            'http://localhost:8000/api/external/xiva/customers/',
            headers={'Authorization': f'Token {token}'},
            timeout=10
        )
        print(f"  Status: {xiva_response.status_code}")
        print(f"  Response: {xiva_response.text[:500]}")
        
        if xiva_response.status_code == 503:
            print("\n[ERROR] 503 Service Unavailable")
            print("This means Xiva authentication failed in the Django view.")
            print("The error message should be in the response above.")
    else:
        print(f"  Login failed: {login_response.text}")
        
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

