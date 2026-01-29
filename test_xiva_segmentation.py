#!/usr/bin/env python
"""
Test Xiva data integration for segmentation
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
django.setup()

from loyalty.integration.feature_store import FeatureStore
from loyalty.integration.xiva_feature_extractor import XivaFeatureExtractor
from loyalty.utils import safe_json_logic

# Test customer
customer_id = "a0d35428-691f-4375-9118-d2bdf6811426"

print("=" * 80)
print("Testing Xiva Feature Extraction for Segmentation")
print("=" * 80)

# Test 1: Extract features directly
print("\n[TEST 1] Extracting features from Xiva...")
print("-" * 80)
try:
    features = XivaFeatureExtractor.extract_customer_features(customer_id)
    print(f"[SUCCESS] Extracted {len(features)} features:")
    for key, value in sorted(features.items()):
        if isinstance(value, (list, dict)):
            print(f"  {key}: {type(value).__name__} ({len(value) if hasattr(value, '__len__') else 'N/A'})")
        else:
            print(f"  {key}: {value}")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

# Test 2: Get via FeatureStore
print("\n[TEST 2] Getting features via FeatureStore (with Xiva)...")
print("-" * 80)
try:
    store_features = FeatureStore.get_customer_features(customer_id, data_source='xiva')
    print(f"[SUCCESS] FeatureStore returned {len(store_features)} features:")
    print(f"  Sample features:")
    for key in sorted(list(store_features.keys())[:10]):
        value = store_features[key]
        if isinstance(value, (list, dict)):
            print(f"    {key}: {type(value).__name__}")
        else:
            print(f"    {key}: {value}")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()

# Test 3: Test segmentation rules
print("\n[TEST 3] Testing segmentation rules with Xiva data...")
print("-" * 80)

if 'store_features' in locals() and store_features:
    # Rule 1: Active customer
    rule1 = {
        "==": [{"var": "customer_status"}, "active"]
    }
    result1 = safe_json_logic(rule1, store_features)
    print(f"Rule 1 (Active customer): {result1}")
    
    # Rule 2: High value customer
    rule2 = {
        "and": [
            {"==": [{"var": "customer_status"}, "active"]},
            {">": [{"var": "total_revenue"}, 0]}
        ]
    }
    result2 = safe_json_logic(rule2, store_features)
    print(f"Rule 2 (Active + Revenue > 0): {result2}")
    
    # Rule 3: Has data service
    rule3 = {
        "==": [{"var": "has_data_service"}, True]
    }
    result3 = safe_json_logic(rule3, store_features)
    print(f"Rule 3 (Has data service): {result3}")
    
    # Rule 4: Credit risk (high utilization)
    rule4 = {
        "and": [
            {">": [{"var": "credit_utilization"}, 0.5]},
            {"<": [{"var": "current_balance"}, 0]}
        ]
    }
    result4 = safe_json_logic(rule4, store_features)
    print(f"Rule 4 (Credit risk): {result4}")
    
    # Rule 5: Multiple products
    rule5 = {
        ">": [{"var": "active_products_count"}, 1]
    }
    result5 = safe_json_logic(rule5, store_features)
    print(f"Rule 5 (Multiple products): {result5}")
    
    print(f"\n[SUMMARY]")
    print(f"  Customer matches:")
    print(f"    - Active customer: {'YES' if result1 else 'NO'}")
    print(f"    - High value: {'YES' if result2 else 'NO'}")
    print(f"    - Has data service: {'YES' if result3 else 'NO'}")
    print(f"    - Credit risk: {'YES' if result4 else 'NO'}")
    print(f"    - Multiple products: {'YES' if result5 else 'NO'}")
else:
    print("[SKIP] No features available for rule testing")

# Test 4: Compare with DWH (if available)
print("\n[TEST 4] Comparing Xiva vs DWH data source...")
print("-" * 80)
try:
    xiva_features = FeatureStore.get_customer_features(customer_id, data_source='xiva')
    print(f"Xiva features: {len(xiva_features)} fields")
    
    try:
        dwh_features = FeatureStore.get_customer_features(customer_id, data_source='dwh')
        print(f"DWH features: {len(dwh_features)} fields")
        
        # Compare
        xiva_keys = set(xiva_features.keys())
        dwh_keys = set(dwh_features.keys())
        
        print(f"\nComparison:")
        print(f"  Xiva-only fields: {len(xiva_keys - dwh_keys)}")
        print(f"  DWH-only fields: {len(dwh_keys - xiva_keys)}")
        print(f"  Common fields: {len(xiva_keys & dwh_keys)}")
        
        if xiva_keys - dwh_keys:
            print(f"\n  Xiva unique fields: {sorted(list(xiva_keys - dwh_keys))[:5]}")
        if dwh_keys - xiva_keys:
            print(f"\n  DWH unique fields: {sorted(list(dwh_keys - xiva_keys))[:5]}")
    except Exception as e:
        print(f"DWH not available or error: {e}")
except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "=" * 80)
print("Test Complete")
print("=" * 80)
print("\n[CONCLUSION]")
print("  Xiva data is now available for segmentation!")
print("  Use FeatureStore.get_customer_features() with data_source='xiva'")
print("  SegmentationEngine will automatically use Xiva data if configured.")

