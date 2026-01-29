#!/usr/bin/env python
"""
Detailed data inspection script for Xiva API responses

This script fetches data from Xiva API and displays the structure
and sample data to help understand what's available.
"""

import os
import sys
import django
import json
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
django.setup()

from loyalty.integration import get_xiva_client, XivaAPIError
from django.conf import settings

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_dict_structure(data, indent=0, max_depth=3, max_items=5):
    """Recursively print dictionary structure"""
    prefix = "  " * indent
    
    if isinstance(data, dict):
        if indent >= max_depth:
            print(f"{prefix}... (max depth reached)")
            return
        
        keys = list(data.keys())[:max_items]
        for key in keys:
            value = data[key]
            if isinstance(value, dict):
                print(f"{prefix}{key}: {{dict with {len(value)} keys}}")
                if indent < max_depth - 1:
                    print_dict_structure(value, indent + 1, max_depth, max_items)
            elif isinstance(value, list):
                print(f"{prefix}{key}: [list with {len(value)} items]")
                if value and indent < max_depth - 1:
                    print(f"{prefix}  Sample item:")
                    print_dict_structure(value[0], indent + 2, max_depth, max_items)
            else:
                print(f"{prefix}{key}: {type(value).__name__} = {str(value)[:100]}")
        
        if len(data.keys()) > max_items:
            print(f"{prefix}... ({len(data.keys()) - max_items} more keys)")
    
    elif isinstance(data, list):
        if data:
            print(f"{prefix}[list with {len(data)} items]")
            print(f"{prefix}Sample item:")
            print_dict_structure(data[0], indent + 1, max_depth, max_items)
        else:
            print(f"{prefix}[empty list]")
    else:
        print(f"{prefix}{type(data).__name__}: {str(data)[:200]}")

def inspect_xiva_data():
    """Inspect Xiva API data structures"""
    
    print_section("Xiva API Data Structure Inspection")
    
    try:
        client = get_xiva_client()
        
        # Get a customer ID
        print("\n[STEP 1] Getting customer list...")
        customers = client.get_customer_list(ordering='-creationDate')
        
        if not isinstance(customers, list) or len(customers) == 0:
            print("   [ERROR] No customers found")
            return
        
        customer_id = customers[0].get('id')
        customer_name = customers[0].get('name', 'Unknown')
        print(f"   [OK] Found customer: {customer_name} (ID: {customer_id})")
        
        # 1. Customer Details
        print_section("1. Customer Details Structure")
        try:
            customer = client.get_customer_details(customer_id)
            print_dict_structure(customer, max_depth=4, max_items=10)
        except XivaAPIError as e:
            print(f"   [ERROR] Error: {e}")
        
        # 2. Customer 360 Services
        print_section("2. Customer 360 Services Structure")
        try:
            services = client.get_customer_360_services(customer_id)
            print_dict_structure(services, max_depth=4, max_items=10)
        except XivaAPIError as e:
            print(f"   [ERROR] Error: {e}")
        
        # 3. Customer 360 Usage
        print_section("3. Customer 360 Usage Structure")
        try:
            usage = client.get_customer_360_usage(customer_id)
            print_dict_structure(usage, max_depth=4, max_items=10)
        except XivaAPIError as e:
            print(f"   [ERROR] Error: {e}")
        
        # 4. Customer 360 Overview
        print_section("4. Customer 360 Overview Structure")
        try:
            overview = client.get_customer_360_overview(customer_id)
            print_dict_structure(overview, max_depth=4, max_items=10)
        except XivaAPIError as e:
            print(f"   [ERROR] Error: {e}")
        
        # 5. Customer 360 Financial
        print_section("5. Customer 360 Financial Structure")
        try:
            financial = client.get_customer_360_financial(customer_id)
            print_dict_structure(financial, max_depth=4, max_items=10)
        except XivaAPIError as e:
            print(f"   [ERROR] Error: {e}")
        
        # 6. Product Instances
        print_section("6. Product Instances Structure")
        try:
            products = client.get_customer_product_instances(customer_id)
            if products:
                print(f"   Found {len(products)} product instances")
                print_dict_structure(products[0], max_depth=4, max_items=10)
            else:
                print("   No product instances found")
        except XivaAPIError as e:
            print(f"   [ERROR] Error: {e}")
        
        # 7. Billing Accounts
        print_section("7. Billing Accounts Structure")
        try:
            accounts = client.get_billing_accounts(customer=customer_id)
            if accounts:
                print(f"   Found {len(accounts)} billing accounts")
                print_dict_structure(accounts[0], max_depth=4, max_items=10)
            else:
                print("   No billing accounts found")
        except XivaAPIError as e:
            print(f"   [ERROR] Error: {e}")
        
        # 8. Rated Usage Records
        print_section("8. Rated Usage Records Structure")
        try:
            rated_usage = client.get_rated_usage_records(customer=customer_id)
            if rated_usage:
                print(f"   Found {len(rated_usage)} rated usage records")
                print_dict_structure(rated_usage[0], max_depth=4, max_items=10)
            else:
                print("   No rated usage records found")
        except XivaAPIError as e:
            print(f"   [ERROR] Error: {e}")
        
        # 9. Product Offerings
        print_section("9. Product Offerings Structure")
        try:
            offerings = client.get_product_offerings()
            if offerings:
                print(f"   Found {len(offerings)} product offerings")
                print_dict_structure(offerings[0], max_depth=4, max_items=10)
            else:
                print("   No product offerings found")
        except XivaAPIError as e:
            print(f"   [ERROR] Error: {e}")
        
        # 10. Full Context
        print_section("10. Full Customer Context Structure")
        try:
            context = client.get_customer_full_context(customer_id)
            print_dict_structure(context, max_depth=3, max_items=8)
        except XivaAPIError as e:
            print(f"   [ERROR] Error: {e}")
        
        print_section("Inspection Complete")
        print("\n[SUCCESS] All data structures inspected successfully!")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] Fatal Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    inspect_xiva_data()

