#!/usr/bin/env python
"""
Simple Feature Extraction Demo - No Database Required

This shows:
1. Connecting to Xiva
2. Extracting features from real customer data
3. Displaying all features organized by category

Run: python demo_features_only.py
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
django.setup()

from loyalty.integration.feature_store import FeatureStore
from loyalty.integration.xiva_client import get_xiva_client, XivaAPIError

def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_section(title):
    print(f"\n{title}")
    print("-" * 80)

def main():
    print_header("FEATURE EXTRACTION DEMO - XIVA DATA")
    
    # Step 1: Get customer from Xiva
    print_section("Step 1: Getting customer from Xiva...")
    try:
        client = get_xiva_client()
        customers = client.get_customer_list(limit=3)
        
        if not customers:
            print("[ERROR] No customers found in Xiva")
            print("\n[FIX] Check Xiva connection and credentials")
            return
        
        customer = customers[0]
        customer_id = customer.get('id')
        customer_name = customer.get('name', 'Unknown')
        
        print(f"[OK] Found customer: {customer_name}")
        print(f"     Customer ID: {customer_id}")
        
    except XivaAPIError as e:
        print(f"[ERROR] Xiva connection failed: {e}")
        print("\n[FIX] Check credentials in .env:")
        print("     XIVA_API_USERNAME=karim@xiva.ca")
        print("     XIVA_API_PASSWORD=Windows11")
        return
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 2: Extract features
    print_section("Step 2: Extracting features from Xiva...")
    try:
        features = FeatureStore.get_customer_features(customer_id, data_source='xiva')
        
        if not features or len(features) < 2:
            print("[ERROR] No features extracted")
            return
        
        print(f"[OK] Successfully extracted {len(features)} features!")
        
        # Organize features by category
        financial = {}
        service = {}
        usage = {}
        profile = {}
        other = {}
        
        for key, value in features.items():
            key_lower = key.lower()
            if any(x in key_lower for x in ['revenue', 'balance', 'credit', 'payment', 'spend']):
                financial[key] = value
            elif any(x in key_lower for x in ['product', 'service', 'has_']):
                service[key] = value
            elif any(x in key_lower for x in ['usage', 'data', 'voice', 'sms']):
                usage[key] = value
            elif any(x in key_lower for x in ['status', 'type', 'name', 'email', 'phone', 'age', 'gender', 'nationality']):
                profile[key] = value
            else:
                other[key] = value
        
        # Display features by category
        print_section("Financial Features:")
        if financial:
            for key, value in sorted(financial.items()):
                print(f"  {key:35} = {value}")
        else:
            print("  (none)")
        
        print_section("Service/Product Features:")
        if service:
            for key, value in sorted(service.items()):
                if isinstance(value, list):
                    print(f"  {key:35} = {value}")
                else:
                    print(f"  {key:35} = {value}")
        else:
            print("  (none)")
        
        print_section("Usage Features:")
        if usage:
            for key, value in sorted(usage.items()):
                print(f"  {key:35} = {value}")
        else:
            print("  (none)")
        
        print_section("Profile/Demographic Features:")
        if profile:
            for key, value in sorted(profile.items()):
                if key != 'customer_id':
                    print(f"  {key:35} = {value}")
        else:
            print("  (none)")
        
        if other:
            print_section("Other Features:")
            for key, value in sorted(other.items()):
                print(f"  {key:35} = {value}")
        
        # Summary
        print_section("Summary:")
        print(f"  Total Features: {len(features)}")
        print(f"  Financial: {len(financial)}")
        print(f"  Service/Product: {len(service)}")
        print(f"  Usage: {len(usage)}")
        print(f"  Profile: {len(profile)}")
        print(f"  Other: {len(other)}")
        
        # Show how to use in segmentation
        print_section("How to Use These Features:")
        print("""
  These features can be used in segmentation rules:
  
  Example Segment Rules:
  
  1. High Value Customers:
     {
       "and": [
         {">": [{"var": "total_revenue"}, 100]},
         {"==": [{"var": "customer_status"}, "active"]}
       ]
     }
  
  2. Data-Heavy Users:
     {
       "and": [
         {">": [{"var": "data_usage_mb"}, 5000]},
         {"==": [{"var": "has_data_service"}, true]}
       ]
     }
  
  3. High Credit Utilization:
     {
       "and": [
         {">": [{"var": "credit_utilization"}, 0.8]},
         {"==": [{"var": "customer_status"}, "active"]}
       ]
     }
  
  In Frontend:
  1. Go to Segments -> Create Segment
  2. In right sidebar, select "Xiva Only"
  3. Click "Refresh" to see these fields
  4. Click "Insert" on any field to use in rule
  5. Build your segment rule
  6. Save and recalculate
        """)
        
    except Exception as e:
        print(f"[ERROR] Feature extraction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Demo interrupted by user]")
    except Exception as e:
        print(f"\n\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()

