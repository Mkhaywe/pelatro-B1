#!/usr/bin/env python
"""
Test script for Xiva integration with JWT authentication

Usage:
    python test_xiva_integration.py

Or set environment variables:
    export XIVA_API_BASE_URL=https://www.xiva.ca/api
    export XIVA_API_USERNAME=karim@xiva.ca
    export XIVA_API_PASSWORD=Windows11
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
django.setup()

from loyalty.integration import get_xiva_client, XivaAPIError
from django.conf import settings

def test_xiva_integration():
    """Test Xiva API integration with JWT authentication"""
    
    print("=" * 70)
    print("Testing Xiva Integration with JWT Authentication")
    print("=" * 70)
    
    # Check configuration
    print("\n[CONFIG] Configuration Check:")
    print(f"   Base URL: {getattr(settings, 'XIVA_API_BASE_URL', 'Not set')}")
    print(f"   Auth Type: {getattr(settings, 'XIVA_API_AUTH_TYPE', 'Not set')}")
    print(f"   Username: {getattr(settings, 'XIVA_API_USERNAME', 'Not set')}")
    print(f"   Password: {'*' * len(getattr(settings, 'XIVA_API_PASSWORD', '')) if getattr(settings, 'XIVA_API_PASSWORD', '') else 'Not set'}")
    
    try:
        client = get_xiva_client()
        
        # Test 1: Login
        print("\n[TEST 1] JWT Login")
        print("-" * 70)
        try:
            username = getattr(settings, 'XIVA_API_USERNAME', '')
            password = getattr(settings, 'XIVA_API_PASSWORD', '')
            
            if not username or not password:
                print("   [WARNING] Username/password not configured in settings")
                print("   [TIP] Set XIVA_API_USERNAME and XIVA_API_PASSWORD in .env or settings.py")
                return
            
            access_token = client.login(username, password)
            print(f"   [OK] Login successful!")
            print(f"   Access Token: {access_token[:50]}...")
            print(f"   Token Expires: {client.token_expires_at}")
            
        except XivaAPIError as e:
            print(f"   [ERROR] Login failed: {e}")
            return
        except Exception as e:
            print(f"   [ERROR] Unexpected error: {e}")
            return
        
        # Test 2: Get Customer List
        print("\n[TEST 2] Get Customer List")
        print("-" * 70)
        try:
            customers = client.get_customer_list(ordering='-creationDate')
            print(f"   [OK] Retrieved {len(customers) if isinstance(customers, list) else 0} customers")
            
            if isinstance(customers, list) and len(customers) > 0:
                sample = customers[0]
                print(f"   Sample customer:")
                print(f"      ID: {sample.get('id', 'N/A')}")
                print(f"      Name: {sample.get('name', 'N/A')}")
                print(f"      Status: {sample.get('status', 'N/A')}")
            else:
                print("   [WARNING] No customers found (empty list or different response format)")
                if not isinstance(customers, list):
                    print(f"   Response type: {type(customers)}")
                    print(f"   Response: {str(customers)[:200]}")
        
        except XivaAPIError as e:
            print(f"   ❌ Failed: {e}")
        
        # Test 3: Get Customer Details (if we have a customer ID)
        if isinstance(customers, list) and len(customers) > 0:
            customer_id = customers[0].get('id')
            if customer_id:
                print(f"\n[TEST 3] Get Customer Details (ID: {customer_id})")
                print("-" * 70)
                try:
                    customer = client.get_customer_details(str(customer_id))
                    print(f"   [OK] Retrieved customer details")
                    print(f"      Name: {customer.get('name', 'N/A')}")
                    print(f"      Email: {customer.get('email', 'N/A')}")
                    print(f"      Status: {customer.get('status', 'N/A')}")
                except XivaAPIError as e:
                    print(f"   ❌ Failed: {e}")
        
        # Test 4: Get Customer 360 Services (if we have a customer ID)
        if isinstance(customers, list) and len(customers) > 0:
            customer_id = customers[0].get('id')
            if customer_id:
                print(f"\n[TEST 4] Get Customer 360 Services (ID: {customer_id})")
                print("-" * 70)
                try:
                    services = client.get_customer_360_services(str(customer_id))
                    print(f"   [OK] Retrieved customer 360 services")
                    if isinstance(services, dict):
                        products = services.get('products', [])
                        print(f"      Products: {len(products) if isinstance(products, list) else 0}")
                        usage = services.get('usage_summary', {})
                        if usage:
                            print(f"      Usage Summary: Available")
                except XivaAPIError as e:
                    print(f"   ❌ Failed: {e}")
        
        # Test 5: Token Refresh
        print("\n[TEST 5] Token Refresh")
        print("-" * 70)
        try:
            old_token = client.access_token
            new_token = client.refresh_access_token()
            if new_token != old_token:
                print(f"   [OK] Token refreshed successfully")
                print(f"   New Token: {new_token[:50]}...")
            else:
                print(f"   [WARNING] Token refresh returned same token (may be valid)")
        except XivaAPIError as e:
            print(f"   ❌ Token refresh failed: {e}")
        
        # Test 6: Get Customer Full Context (if we have a customer ID)
        customer_id = None
        if isinstance(customers, list) and len(customers) > 0:
            customer_id = customers[0].get('id')
            if customer_id:
                print(f"\n[TEST 6] Get Customer Full Context (ID: {customer_id})")
                print("-" * 70)
                try:
                    context = client.get_customer_full_context(str(customer_id))
                    print(f"   [OK] Retrieved full customer context")
                    print(f"      Timestamp: {context.get('timestamp', 'N/A')}")
                    print(f"      Has Customer: {bool(context.get('customer'))}")
                    print(f"      Has Services: {bool(context.get('services'))}")
                    print(f"      Billing Accounts: {len(context.get('billing_accounts', []))}")
                except XivaAPIError as e:
                    print(f"   ❌ Failed: {e}")
        
        # Test 7: Get Customer 360 Usage (if we have a customer ID)
        if customer_id:
            print(f"\n[TEST 7] Get Customer 360 Usage (ID: {customer_id})")
            print("-" * 70)
            try:
                usage = client.get_customer_360_usage(str(customer_id))
                print(f"   [OK] Retrieved customer 360 usage")
                if isinstance(usage, dict):
                    usage_summary = usage.get('usage_summary', {})
                    by_date = usage.get('by_date_and_type', {})
                    print(f"      Has Usage Summary: {bool(usage_summary)}")
                    print(f"      Has Date Breakdown: {bool(by_date)}")
                    if by_date:
                        print(f"      Date Range Keys: {len(by_date)} dates")
            except XivaAPIError as e:
                print(f"   ❌ Failed: {e}")
        
        # Test 8: Get Customer 360 Usage with Current Month Only
        if customer_id:
            print(f"\n[TEST 8] Get Customer 360 Usage (Current Month Only)")
            print("-" * 70)
            try:
                usage = client.get_customer_360_usage(
                    str(customer_id),
                    current_month_only=True
                )
                print(f"   [OK] Retrieved current month usage")
                if isinstance(usage, dict):
                    by_date = usage.get('by_date_and_type', {})
                    print(f"      Date Range Keys: {len(by_date)} dates")
            except XivaAPIError as e:
                print(f"   ❌ Failed: {e}")
        
        # Test 9: Get Customer Product Instances
        if customer_id:
            print(f"\n[TEST 9] Get Customer Product Instances (ID: {customer_id})")
            print("-" * 70)
            try:
                products = client.get_customer_product_instances(str(customer_id))
                print(f"   [OK] Retrieved {len(products) if isinstance(products, list) else 0} product instances")
                if isinstance(products, list) and len(products) > 0:
                    sample = products[0]
                    print(f"      Sample Product:")
                    print(f"         ID: {sample.get('id', 'N/A')}")
                    print(f"         Name: {sample.get('name', 'N/A')}")
                    print(f"         Status: {sample.get('status', 'N/A')}")
            except XivaAPIError as e:
                print(f"   ❌ Failed: {e}")
        
        # Test 10: Get Customer Billing Accounts
        if customer_id:
            print(f"\n[TEST 10] Get Customer Billing Accounts (ID: {customer_id})")
            print("-" * 70)
            try:
                accounts = client.get_billing_accounts(customer=str(customer_id))
                print(f"   [OK] Retrieved {len(accounts) if isinstance(accounts, list) else 0} billing accounts")
                if isinstance(accounts, list) and len(accounts) > 0:
                    sample = accounts[0]
                    print(f"      Sample Account:")
                    print(f"         ID: {sample.get('id', 'N/A')}")
                    print(f"         Name: {sample.get('name', 'N/A')}")
                    print(f"         Status: {sample.get('status', 'N/A')}")
            except XivaAPIError as e:
                print(f"   ❌ Failed: {e}")
        
        # Test 11: Search Customers
        print(f"\n[TEST 11] Search Customers (by name)")
        print("-" * 70)
        try:
            if isinstance(customers, list) and len(customers) > 0:
                # Try searching by first customer's name
                search_name = customers[0].get('name', '').split()[0] if customers[0].get('name') else None
                if search_name:
                    search_results = client.get_customer_list(search=search_name)
                    print(f"   [OK] Search for '{search_name}' returned {len(search_results) if isinstance(search_results, list) else 0} results")
                else:
                    print(f"   [SKIP] No name available for search test")
            else:
                print(f"   [SKIP] No customers available for search test")
        except XivaAPIError as e:
            print(f"   ❌ Failed: {e}")
        
        # Test 12: Get Product Offerings
        print(f"\n[TEST 12] Get Product Offerings")
        print("-" * 70)
        try:
            offerings = client.get_product_offerings()
            print(f"   [OK] Retrieved {len(offerings) if isinstance(offerings, list) else 0} product offerings")
            if isinstance(offerings, list) and len(offerings) > 0:
                sample = offerings[0]
                print(f"      Sample Offering:")
                print(f"         ID: {sample.get('id', 'N/A')}")
                print(f"         Name: {sample.get('name', 'N/A')}")
        except XivaAPIError as e:
            print(f"   ❌ Failed: {e}")
        
        # Test 13: Get Customer 360 Overview
        if customer_id:
            print(f"\n[TEST 13] Get Customer 360 Overview (ID: {customer_id})")
            print("-" * 70)
            try:
                overview = client.get_customer_360_overview(str(customer_id))
                print(f"   [OK] Retrieved customer 360 overview")
                if isinstance(overview, dict):
                    print(f"      Keys: {list(overview.keys())[:5]}...")
            except XivaAPIError as e:
                print(f"   ❌ Failed: {e}")
        
        # Test 14: Get Customer 360 Financial
        if customer_id:
            print(f"\n[TEST 14] Get Customer 360 Financial (ID: {customer_id})")
            print("-" * 70)
            try:
                financial = client.get_customer_360_financial(str(customer_id))
                print(f"   [OK] Retrieved customer 360 financial data")
                if isinstance(financial, dict):
                    print(f"      Keys: {list(financial.keys())[:5]}...")
            except XivaAPIError as e:
                print(f"   ❌ Failed: {e}")
        
        # Test 15: Error Handling - Invalid Customer ID
        print(f"\n[TEST 15] Error Handling - Invalid Customer ID")
        print("-" * 70)
        try:
            invalid_id = "00000000-0000-0000-0000-000000000000"
            customer = client.get_customer_details(invalid_id)
            print(f"   [WARNING] Invalid ID returned data (unexpected)")
        except XivaAPIError as e:
            print(f"   [OK] Correctly handled invalid customer ID: {str(e)[:100]}")
        except Exception as e:
            print(f"   [OK] Error caught: {type(e).__name__}")
        
        # Test 16: Get Rated Usage Records
        if customer_id:
            print(f"\n[TEST 16] Get Rated Usage Records (ID: {customer_id})")
            print("-" * 70)
            try:
                rated_usage = client.get_rated_usage_records(customer=str(customer_id))
                print(f"   [OK] Retrieved {len(rated_usage) if isinstance(rated_usage, list) else 0} rated usage records")
                if isinstance(rated_usage, list) and len(rated_usage) > 0:
                    sample = rated_usage[0]
                    print(f"      Sample Record Keys: {list(sample.keys())[:5]}...")
            except XivaAPIError as e:
                print(f"   ❌ Failed: {e}")
        
        print("\n" + "=" * 70)
        print("[SUCCESS] Comprehensive Testing Complete!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[FATAL ERROR] Fatal Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_xiva_integration()

