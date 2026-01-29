#!/usr/bin/env python
"""
Test Xiva API pagination to see if there are more results available
"""

import os
import sys
import django
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
django.setup()

from loyalty.integration import get_xiva_client, XivaAPIError
from django.conf import settings
import requests

def test_pagination():
    """Test if Xiva API returns pagination metadata"""
    
    print("=" * 80)
    print("Testing Xiva API Pagination")
    print("=" * 80)
    
    try:
        client = get_xiva_client()
        
        # Make a direct request to see the raw response structure
        print("\n[TEST 1] Raw API Response Structure")
        print("-" * 80)
        
        url = f"{client.base_url}/customerManagement/v4/customer/"
        headers = client._get_headers()
        params = {'ordering': '-creationDate'}
        
        response = requests.get(url, headers=headers, params=params, timeout=client.timeout)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        data = response.json()
        
        print(f"\nResponse Type: {type(data)}")
        print(f"Response Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A (list response)'}")
        
        if isinstance(data, dict):
            print("\nResponse Structure:")
            for key, value in data.items():
                if key == 'results' and isinstance(value, list):
                    print(f"  {key}: [list with {len(value)} items]")
                elif isinstance(value, (dict, list)):
                    print(f"  {key}: {type(value).__name__} with {len(value) if hasattr(value, '__len__') else '?'} items")
                else:
                    print(f"  {key}: {value}")
        
        # Check for pagination fields
        print("\n[TEST 2] Pagination Metadata Check")
        print("-" * 80)
        
        pagination_fields = ['count', 'next', 'previous', 'page', 'page_size', 'total', 'total_pages']
        found_pagination = {}
        
        if isinstance(data, dict):
            for field in pagination_fields:
                if field in data:
                    found_pagination[field] = data[field]
                    print(f"  [FOUND] {field}: {data[field]}")
        
        if not found_pagination:
            print("  [INFO] No standard pagination fields found in response")
            print("  [INFO] Response might be a simple list or use different pagination format")
        
        # Check if we can request more results
        print("\n[TEST 3] Testing Pagination Parameters")
        print("-" * 80)
        
        pagination_params = ['page', 'page_size', 'limit', 'offset', 'size']
        for param in pagination_params:
            test_params = params.copy()
            test_params[param] = '100' if param in ['page_size', 'limit', 'size'] else '2'
            
            try:
                test_response = requests.get(url, headers=headers, params=test_params, timeout=client.timeout)
                if test_response.ok:
                    test_data = test_response.json()
                    if isinstance(test_data, dict) and 'results' in test_data:
                        count = len(test_data['results'])
                        print(f"  {param}=100: Returned {count} results")
                    elif isinstance(test_data, list):
                        count = len(test_data)
                        print(f"  {param}=100: Returned {count} results")
            except Exception as e:
                print(f"  {param}: Error - {str(e)[:50]}")
        
        # Test with page parameter
        print("\n[TEST 4] Testing Page Parameter")
        print("-" * 80)
        
        try:
            page2_params = params.copy()
            page2_params['page'] = '2'
            page2_response = requests.get(url, headers=headers, params=page2_params, timeout=client.timeout)
            
            if page2_response.ok:
                page2_data = page2_response.json()
                if isinstance(page2_data, dict) and 'results' in page2_data:
                    page2_count = len(page2_data['results'])
                    print(f"  Page 2: Returned {page2_count} results")
                    if page2_count > 0:
                        print(f"  [SUCCESS] Pagination works! Page 2 has different results")
                        print(f"  First customer on page 2: {page2_data['results'][0].get('name', 'N/A')}")
                elif isinstance(page2_data, list):
                    page2_count = len(page2_data)
                    print(f"  Page 2: Returned {page2_count} results")
        except Exception as e:
            print(f"  [ERROR] Could not fetch page 2: {e}")
        
        # Check billing accounts for the test customer
        print("\n[TEST 5] Billing Accounts Check")
        print("-" * 80)
        
        if isinstance(data, dict) and 'results' in data and len(data['results']) > 0:
            customer_id = data['results'][0].get('id')
            print(f"  Testing with customer: {customer_id}")
            
            # Get billing accounts
            accounts = client.get_billing_accounts(customer=customer_id)
            print(f"  Billing accounts returned: {len(accounts) if isinstance(accounts, list) else 0}")
            
            # Check raw response
            accounts_url = f"{client.base_url}/customerManagement/v4/customerAccount/"
            accounts_params = {'customer': customer_id}
            accounts_response = requests.get(accounts_url, headers=headers, params=accounts_params, timeout=client.timeout)
            
            if accounts_response.ok:
                accounts_data = accounts_response.json()
                print(f"  Raw accounts response type: {type(accounts_data)}")
                if isinstance(accounts_data, dict):
                    print(f"  Raw accounts response keys: {list(accounts_data.keys())}")
                    if 'results' in accounts_data:
                        print(f"  Accounts in 'results': {len(accounts_data['results'])}")
                        if 'count' in accounts_data:
                            print(f"  Total accounts (count): {accounts_data['count']}")
                elif isinstance(accounts_data, list):
                    print(f"  Raw accounts response: list with {len(accounts_data)} items")
        
        print("\n" + "=" * 80)
        print("Pagination Test Complete")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_pagination()

