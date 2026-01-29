#!/usr/bin/env python
"""
Final pagination test - test the updated client with fetch_all
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
django.setup()

from loyalty.integration import get_xiva_client, XivaAPIError

def test_pagination_final():
    """Test pagination with updated client"""
    
    print("=" * 80)
    print("Testing Xiva Client Pagination")
    print("=" * 80)
    
    client = get_xiva_client()
    
    # Test 1: Default behavior (should get 50)
    print("\n[TEST 1] Default behavior (fetch_all=False)")
    print("-" * 80)
    try:
        customers = client.get_customer_list(ordering='-creationDate')
        print(f"  Returned: {len(customers)} customers")
        print(f"  [NOTE] Xiva API has a hard limit of 50 results per request")
    except XivaAPIError as e:
        print(f"  [ERROR] {e}")
    
    # Test 2: With fetch_all=True
    print("\n[TEST 2] With fetch_all=True (attempting to get all)")
    print("-" * 80)
    try:
        all_customers = client.get_customer_list(ordering='-creationDate', fetch_all=True)
        print(f"  Returned: {len(all_customers)} customers")
        
        if len(all_customers) > 50:
            print(f"  [SUCCESS] Got more than 50 customers!")
            print(f"  First customer: {all_customers[0].get('name', 'N/A')}")
            print(f"  Customer at index 50: {all_customers[50].get('name', 'N/A') if len(all_customers) > 50 else 'N/A'}")
        else:
            print(f"  [INFO] Only got {len(all_customers)} customers (may be all available, or pagination not supported)")
    except XivaAPIError as e:
        print(f"  [ERROR] {e}")
    
    # Test 3: With limit
    print("\n[TEST 3] With limit=100")
    print("-" * 80)
    try:
        limited = client.get_customer_list(ordering='-creationDate', fetch_all=True, limit=100)
        print(f"  Returned: {len(limited)} customers (limited to 100)")
    except XivaAPIError as e:
        print(f"  [ERROR] {e}")
    
    # Test 4: Billing accounts - check if each customer has one
    print("\n[TEST 4] Billing Accounts Check")
    print("-" * 80)
    try:
        customers = client.get_customer_list(ordering='-creationDate', limit=10)
        print(f"  Checking first 10 customers for billing accounts...")
        
        customers_with_accounts = 0
        customers_without_accounts = 0
        customers_with_multiple = 0
        
        for customer in customers:
            customer_id = customer.get('id')
            customer_name = customer.get('name', 'Unknown')
            
            try:
                accounts = client.get_billing_accounts(customer=customer_id)
                account_count = len(accounts) if isinstance(accounts, list) else 0
                
                if account_count == 0:
                    customers_without_accounts += 1
                    print(f"    {customer_name}: NO billing accounts")
                elif account_count == 1:
                    customers_with_accounts += 1
                    # print(f"    {customer_name}: 1 account (normal)")
                else:
                    customers_with_multiple += 1
                    print(f"    {customer_name}: {account_count} accounts (multiple)")
            except XivaAPIError as e:
                print(f"    {customer_name}: Error - {e}")
        
        print(f"\n  Summary:")
        print(f"    Customers with 1 account: {customers_with_accounts}")
        print(f"    Customers with 0 accounts: {customers_without_accounts}")
        print(f"    Customers with multiple accounts: {customers_with_multiple}")
        print(f"    [NOTE] Most customers should have 1 billing account")
        
    except XivaAPIError as e:
        print(f"  [ERROR] {e}")
    
    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)
    print("\n[SUMMARY]")
    print("  - Xiva API returns max 50 results per request")
    print("  - Pagination support may be limited")
    print("  - Use fetch_all=True to attempt fetching all results")
    print("  - Each customer typically has 1 billing account")

if __name__ == '__main__':
    test_pagination_final()

