#!/usr/bin/env python
"""
Detailed pagination test - check if page 2 has different results
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
django.setup()

from loyalty.integration import get_xiva_client, XivaAPIError
import requests

def test_detailed_pagination():
    """Test pagination in detail"""
    
    print("=" * 80)
    print("Detailed Pagination Test")
    print("=" * 80)
    
    client = get_xiva_client()
    headers = client._get_headers()
    base_url = f"{client.base_url}/customerManagement/v4/customer/"
    
    # Get page 1
    print("\n[PAGE 1] Getting first page...")
    params1 = {'ordering': '-creationDate'}
    response1 = requests.get(base_url, headers=headers, params=params1, timeout=client.timeout)
    data1 = response1.json()
    
    if isinstance(data1, list):
        print(f"  Returned: {len(data1)} customers")
        if len(data1) > 0:
            print(f"  First customer: {data1[0].get('name', 'N/A')} (ID: {data1[0].get('id', 'N/A')[:20]}...)")
            print(f"  Last customer: {data1[-1].get('name', 'N/A')} (ID: {data1[-1].get('id', 'N/A')[:20]}...)")
    
    # Get page 2
    print("\n[PAGE 2] Getting second page...")
    params2 = {'ordering': '-creationDate', 'page': '2'}
    response2 = requests.get(base_url, headers=headers, params=params2, timeout=client.timeout)
    data2 = response2.json()
    
    if isinstance(data2, list):
        print(f"  Returned: {len(data2)} customers")
        if len(data2) > 0:
            print(f"  First customer: {data2[0].get('name', 'N/A')} (ID: {data2[0].get('id', 'N/A')[:20]}...)")
            print(f"  Last customer: {data2[-1].get('name', 'N/A')} (ID: {data2[-1].get('id', 'N/A')[:20]}...)")
    
    # Check if results are different
    if isinstance(data1, list) and isinstance(data2, list) and len(data1) > 0 and len(data2) > 0:
        id1 = data1[0].get('id')
        id2 = data2[0].get('id')
        if id1 != id2:
            print(f"\n[SUCCESS] Page 2 has different results! Pagination works.")
        else:
            print(f"\n[WARNING] Page 2 has same first result as page 1. Pagination may not be working.")
    
    # Try different page sizes
    print("\n[TEST] Trying different page sizes...")
    for size in [100, 200, 500]:
        params = {'ordering': '-creationDate', 'page_size': str(size)}
        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=client.timeout)
            if response.ok:
                data = response.json()
                if isinstance(data, list):
                    print(f"  page_size={size}: Returned {len(data)} customers")
                    if len(data) > 50:
                        print(f"    [SUCCESS] Got more than 50 results!")
        except Exception as e:
            print(f"  page_size={size}: Error - {str(e)[:50]}")
    
    # Try limit parameter
    print("\n[TEST] Trying limit parameter...")
    for limit in [100, 200]:
        params = {'ordering': '-creationDate', 'limit': str(limit)}
        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=client.timeout)
            if response.ok:
                data = response.json()
                if isinstance(data, list):
                    print(f"  limit={limit}: Returned {len(data)} customers")
        except Exception as e:
            print(f"  limit={limit}: Error - {str(e)[:50]}")
    
    # Check billing accounts pagination
    print("\n[BILLING ACCOUNTS] Testing billing accounts...")
    if isinstance(data1, list) and len(data1) > 0:
        customer_id = data1[0].get('id')
        customer_name = data1[0].get('name', 'Unknown')
        
        accounts_url = f"{client.base_url}/customerManagement/v4/customerAccount/"
        accounts_params = {'customer': customer_id}
        
        accounts_response = requests.get(accounts_url, headers=headers, params=accounts_params, timeout=client.timeout)
        if accounts_response.ok:
            accounts_data = accounts_response.json()
            
            if isinstance(accounts_data, list):
                print(f"  Customer: {customer_name}")
                print(f"  Billing accounts: {len(accounts_data)}")
                for i, account in enumerate(accounts_data, 1):
                    print(f"    Account {i}: {account.get('name', 'N/A')} (Status: {account.get('status', 'N/A')})")
            elif isinstance(accounts_data, dict):
                if 'results' in accounts_data:
                    print(f"  Customer: {customer_name}")
                    print(f"  Billing accounts (results): {len(accounts_data['results'])}")
                    if 'count' in accounts_data:
                        print(f"  Total count: {accounts_data['count']}")
                    for i, account in enumerate(accounts_data['results'], 1):
                        print(f"    Account {i}: {account.get('name', 'N/A')} (Status: {account.get('status', 'N/A')})")
    
    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)

if __name__ == '__main__':
    test_detailed_pagination()

