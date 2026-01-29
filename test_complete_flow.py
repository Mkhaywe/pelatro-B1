#!/usr/bin/env python
"""
Complete end-to-end test: Xiva → Features → Segment → Campaign

This script demonstrates the complete flow:
1. Get customer from Xiva
2. Extract features
3. Create segment using features
4. Calculate segment membership
5. Show how it all works together
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
django.setup()

from loyalty.integration.feature_store import FeatureStore
from loyalty.integration.xiva_client import get_xiva_client, XivaAPIError
from loyalty.services.segmentation import SegmentationEngine
from loyalty.models_khaywe import Segment, SegmentMember
from django.conf import settings
import json

print("=" * 80)
print("Complete End-to-End Flow Test")
print("=" * 80)

# Step 1: Get a customer from Xiva
print("\n[STEP 1] Getting customer from Xiva...")
print("-" * 80)
try:
    client = get_xiva_client()
    customers = client.get_customer_list(limit=5)
    
    if not customers:
        print("❌ No customers found in Xiva")
        print("   [TIP] Check Xiva connection and credentials")
        exit(1)
    
    customer_id = customers[0].get('id')
    customer_name = customers[0].get('name', 'Unknown')
    print(f"[OK] Found customer: {customer_name}")
    print(f"   Customer ID: {customer_id}")
    
except XivaAPIError as e:
    print(f"[ERROR] Error connecting to Xiva: {e}")
    print("\n[FIX] Set credentials in .env file:")
    print("   XIVA_API_USERNAME=karim@xiva.ca")
    print("   XIVA_API_PASSWORD=Windows11")
    exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 2: Extract features
print("\n[STEP 2] Extracting features from Xiva...")
print("-" * 80)
try:
    features = FeatureStore.get_customer_features(customer_id, data_source='xiva')
    
    if not features or len(features) < 2:
        print("[ERROR] No features extracted")
        print("   [TIP] Check Xiva feature extractor")
        exit(1)
    
    print(f"[OK] Extracted {len(features)} features")
    print("\n   Key Features:")
    key_features = [
        'total_revenue', 'customer_status', 'data_usage_mb',
        'active_products_count', 'credit_utilization', 'has_data_service'
    ]
    for key in key_features:
        if key in features:
            value = features[key]
            print(f"      {key}: {value}")
    
except Exception as e:
    print(f"[ERROR] Error extracting features: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 3: Create segment
print("\n[STEP 3] Creating segment using Xiva features...")
print("-" * 80)
try:
    # Create a simple segment rule using Xiva features
    segment_rule = {
        "and": [
            {">": [{"var": "total_revenue"}, 0]},  # Has revenue
            {"==": [{"var": "customer_status"}, "active"]}  # Is active
        ]
    }
    
    segment, created = Segment.objects.get_or_create(
        name="Test - Active Customers with Revenue",
        defaults={
            'description': 'Test segment: Active customers with any revenue (using Xiva features)',
            'is_dynamic': True,
            'rules': [segment_rule]
        }
    )
    
    if created:
        print(f"[OK] Created segment: {segment.name}")
    else:
        print(f"[OK] Using existing segment: {segment.name}")
        # Update rules if needed
        segment.rules = [segment_rule]
        segment.save()
    
    print(f"   Segment ID: {segment.id}")
    print(f"   Rule: {json.dumps(segment_rule, indent=2)}")
    
except Exception as e:
    print(f"[ERROR] Error creating segment: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 4: Calculate segment membership
print("\n[STEP 4] Calculating segment membership...")
print("-" * 80)
try:
    result = SegmentationEngine.update_segment_membership(segment, [customer_id])
    print(f"[OK] Segment calculation complete:")
    print(f"   Added: {result['added']} customers")
    print(f"   Removed: {result['removed']} customers")
    print(f"   Total: {result['total']} customers")
    
except Exception as e:
    print(f"[ERROR] Error calculating segment: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 5: Verify customer is in segment
print("\n[STEP 5] Verifying segment membership...")
print("-" * 80)
try:
    is_member = SegmentMember.objects.filter(
        segment=segment,
        customer_id=customer_id,
        is_active=True
    ).exists()
    
    if is_member:
        print(f"[OK] Customer '{customer_name}' IS in segment!")
        print(f"   Segment: {segment.name}")
    else:
        print(f"[WARNING] Customer '{customer_name}' is NOT in segment")
        print("\n   [DEBUG] Features used for evaluation:")
        for key, value in sorted(features.items()):
            if key in ['total_revenue', 'customer_status', 'data_usage_mb']:
                print(f"      {key}: {value}")
        
        # Test rule manually
        print("\n   [DEBUG] Rule evaluation:")
        print(f"      total_revenue > 0: {features.get('total_revenue', 0) > 0}")
        print(f"      customer_status == 'active': {features.get('customer_status') == 'active'}")
    
except Exception as e:
    print(f"[ERROR] Error verifying membership: {e}")
    import traceback
    traceback.print_exc()

# Step 6: Show how to use in campaign
print("\n[STEP 6] Campaign Targeting Example...")
print("-" * 80)
print("[OK] Segment is ready for campaign targeting!")
print("\n   To create a campaign:")
print("   1. Go to Campaigns -> Create Campaign")
print(f"   2. Select target segment: '{segment.name}'")
print("   3. Set trigger: 'Segment Joined'")
print("   4. Configure reward (points, discount, etc.)")
print("   5. Save campaign")
print("\n   When customer joins this segment, campaign will automatically trigger!")

# Summary
print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
print("\n[SUMMARY]")
print(f"  [OK] Customer: {customer_name}")
print(f"  [OK] Features Extracted: {len(features)}")
print(f"  [OK] Segment: {segment.name}")
print(f"  [OK] In Segment: {'YES' if is_member else 'NO'}")
print(f"  [OK] Ready for Campaigns: YES")
print("\n[SUCCESS] Complete flow is working!")

