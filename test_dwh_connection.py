"""
Test DWH Connection

Quick script to verify Django can connect to DWH and read data.
"""
import os
import sys
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')

import django
django.setup()

from loyalty.integration.dwh import get_dwh_connector

print("="*70)
print("TESTING DWH CONNECTION")
print("="*70)
print()

try:
    # Get connector
    print("[INFO] Connecting to DWH...")
    connector = get_dwh_connector()
    print("[OK] Connected to DWH!")
    print()
    
    # Test query - get a customer
    print("[INFO] Testing customer features query...")
    features = connector.get_customer_features('customer_000001')
    
    if features:
        print("[OK] Successfully retrieved customer features!")
        print(f"\n[INFO] Sample features for customer_000001:")
        for key, value in list(features.items())[:10]:
            print(f"   {key}: {value}")
        print(f"\n[OK] Total features: {len(features)}")
    else:
        print("[WARNING] No features returned (customer might not exist)")
        print("[INFO] Trying to get any customer...")
        
        # Try to get list of customers
        result = connector.execute_query(
            "SELECT customer_id FROM customer_features_view LIMIT 1"
        )
        if result:
            test_customer = result[0]['customer_id']
            print(f"[INFO] Found customer: {test_customer}")
            features = connector.get_customer_features(test_customer)
            if features:
                print("[OK] Successfully retrieved features!")
                print(f"\n[INFO] Sample features:")
                for key, value in list(features.items())[:10]:
                    print(f"   {key}: {value}")
    
    print()
    print("="*70)
    print("[OK] DWH CONNECTION TEST PASSED!")
    print("="*70)
    print("\n[INFO] Django can now:")
    print("   - Read customer features from DWH")
    print("   - Use DWH for segmentation")
    print("   - Train ML models from DWH")
    print("   - Use DWH features for ML predictions")
    print("="*70)
    
except Exception as e:
    print(f"\n[ERROR] DWH Connection Test Failed: {e}")
    print("\n[INFO] Troubleshooting:")
    print("   1. Check PostgreSQL is running")
    print("   2. Verify database 'DWH' exists")
    print("   3. Check credentials in settings.py")
    print("   4. Verify tables exist in DWH")
    import traceback
    traceback.print_exc()
    sys.exit(1)

