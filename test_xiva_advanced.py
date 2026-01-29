#!/usr/bin/env python
"""
Advanced Xiva API Testing Suite

Tests performance, batch operations, edge cases, and data consistency.
This is a continuation of the basic integration tests.

Usage:
    python test_xiva_advanced.py
"""

import os
import sys
import django
import time
from datetime import datetime
from pathlib import Path

# Load .env file BEFORE Django setup
try:
    from dotenv import load_dotenv
    # Load .env from project root
    env_path = Path(__file__).resolve().parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[INFO] Loaded .env file from: {env_path}")
    else:
        print(f"[WARNING] .env file not found at: {env_path}")
except ImportError:
    print("[WARNING] python-dotenv not installed. Using environment variables only.")
    print("[TIP] Install with: pip install python-dotenv")

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
django.setup()

from loyalty.integration import get_xiva_client, XivaAPIError
from loyalty.integration.feature_store import FeatureStore
from loyalty.integration.xiva_feature_extractor import XivaFeatureExtractor
from django.conf import settings

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def measure_time(func, *args, **kwargs):
    """Measure execution time of a function"""
    start = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        return result, elapsed, None
    except Exception as e:
        elapsed = time.time() - start
        return None, elapsed, e

def test_advanced():
    """Run advanced Xiva API tests"""
    
    print_section("Advanced Xiva API Testing Suite")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    client = get_xiva_client()
    
    # Ensure authentication
    print("\n[SETUP] Checking authentication...")
    username = getattr(settings, 'XIVA_API_USERNAME', '')
    password = getattr(settings, 'XIVA_API_PASSWORD', '')
    base_url = getattr(settings, 'XIVA_API_BASE_URL', '')
    auth_type = getattr(settings, 'XIVA_API_AUTH_TYPE', '')
    
    # Debug output
    print(f"   Base URL: {base_url if base_url else 'NOT SET'}")
    print(f"   Auth Type: {auth_type if auth_type else 'NOT SET'}")
    print(f"   Username: {username if username else 'NOT SET'}")
    print(f"   Password: {'*' * len(password) if password else 'NOT SET'}")
    
    if not username or not password:
        print("\n   [ERROR] XIVA_API_USERNAME and XIVA_API_PASSWORD not configured")
        print("   [DEBUG] Checking environment variables directly...")
        env_username = os.environ.get('XIVA_API_USERNAME', '')
        env_password = os.environ.get('XIVA_API_PASSWORD', '')
        print(f"   [DEBUG] os.environ XIVA_API_USERNAME: {env_username if env_username else 'NOT SET'}")
        print(f"   [DEBUG] os.environ XIVA_API_PASSWORD: {'*' * len(env_password) if env_password else 'NOT SET'}")
        print("\n   [TIP] Solutions:")
        print("   1. Ensure .env file exists in project root")
        print("   2. Check .env file has: XIVA_API_USERNAME=karim@xiva.ca")
        print("   3. Check .env file has: XIVA_API_PASSWORD=Windows11")
        print("   4. Or set environment variables in PowerShell:")
        print("      $env:XIVA_API_USERNAME='karim@xiva.ca'")
        print("      $env:XIVA_API_PASSWORD='Windows11'")
        return
    
    # Explicitly login if not already authenticated
    if not client.access_token:
        print("   [INFO] Not authenticated, logging in...")
        try:
            client.login(username, password)
            print(f"   [OK] Login successful!")
            print(f"   Token expires at: {client.token_expires_at}")
        except XivaAPIError as e:
            print(f"   [ERROR] Login failed: {e}")
            return
        except Exception as e:
            print(f"   [ERROR] Unexpected error during login: {e}")
            return
    else:
        print(f"   [OK] Already authenticated (token expires at: {client.token_expires_at})")
    
    # Get a sample customer ID for testing
    print("\n[SETUP] Getting sample customer...")
    try:
        customers = client.get_customer_list(limit=5)
        if not customers or len(customers) == 0:
            print("   [ERROR] No customers available for testing")
            return
        test_customer_id = customers[0].get('id')
        test_customer_name = customers[0].get('name', 'Unknown')
        print(f"   [OK] Using customer: {test_customer_name} (ID: {test_customer_id})")
    except Exception as e:
        print(f"   [ERROR] Failed to get customer: {e}")
        return
    
    # ========================================================================
    # TEST SUITE 1: Performance Testing
    # ========================================================================
    print_section("TEST SUITE 1: Performance Testing")
    
    # Test 1.1: Single API call performance
    print("\n[TEST 1.1] Single API Call Performance")
    print("-" * 80)
    endpoints = [
        ("get_customer_details", lambda: client.get_customer_details(test_customer_id)),
        ("get_customer_360_services", lambda: client.get_customer_360_services(test_customer_id)),
        ("get_customer_360_financial", lambda: client.get_customer_360_financial(test_customer_id)),
        ("get_customer_360_usage", lambda: client.get_customer_360_usage(test_customer_id)),
        ("get_customer_full_context", lambda: client.get_customer_full_context(test_customer_id)),
    ]
    
    performance_results = {}
    for name, func in endpoints:
        result, elapsed, error = measure_time(func)
        if error:
            print(f"   {name}: ERROR - {error} ({elapsed:.2f}s)")
        else:
            print(f"   {name}: {elapsed:.2f}s")
            performance_results[name] = elapsed
    
    # Test 1.2: Batch customer list performance
    print("\n[TEST 1.2] Batch Customer List Performance")
    print("-" * 80)
    for limit in [10, 25, 50]:
        result, elapsed, error = measure_time(
            client.get_customer_list, 
            ordering='-creationDate',
            limit=limit
        )
        if error:
            print(f"   Limit {limit}: ERROR - {error} ({elapsed:.2f}s)")
        else:
            count = len(result) if result else 0
            print(f"   Limit {limit}: {count} customers in {elapsed:.2f}s ({elapsed/count*1000:.1f}ms per customer)")
    
    # Test 1.3: Feature extraction performance
    print("\n[TEST 1.3] Feature Extraction Performance")
    print("-" * 80)
    result, elapsed, error = measure_time(
        XivaFeatureExtractor.extract_customer_features,
        test_customer_id
    )
    if error:
        print(f"   Feature extraction: ERROR - {error} ({elapsed:.2f}s)")
    else:
        feature_count = len(result) if result else 0
        print(f"   Feature extraction: {feature_count} features in {elapsed:.2f}s")
        print(f"   Average: {elapsed/feature_count*1000:.1f}ms per feature")
    
    # ========================================================================
    # TEST SUITE 2: Batch Operations
    # ========================================================================
    print_section("TEST SUITE 2: Batch Operations")
    
    # Test 2.1: Multiple customers in sequence
    print("\n[TEST 2.1] Sequential Customer Data Retrieval")
    print("-" * 80)
    test_customers = customers[:5] if len(customers) >= 5 else customers
    print(f"   Testing with {len(test_customers)} customers...")
    
    success_count = 0
    total_time = 0
    for i, customer in enumerate(test_customers, 1):
        customer_id = customer.get('id')
        customer_name = customer.get('name', 'Unknown')
        result, elapsed, error = measure_time(
            client.get_customer_full_context,
            customer_id
        )
        total_time += elapsed
        if error:
            print(f"   {i}. {customer_name}: ERROR - {error}")
        else:
            success_count += 1
            print(f"   {i}. {customer_name}: OK ({elapsed:.2f}s)")
    
    print(f"\n   Summary: {success_count}/{len(test_customers)} successful")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average: {total_time/len(test_customers):.2f}s per customer")
    
    # Test 2.2: Feature extraction for multiple customers
    print("\n[TEST 2.2] Batch Feature Extraction")
    print("-" * 80)
    print(f"   Extracting features for {len(test_customers)} customers...")
    
    features_success = 0
    features_total_time = 0
    for i, customer in enumerate(test_customers, 1):
        customer_id = customer.get('id')
        customer_name = customer.get('name', 'Unknown')
        result, elapsed, error = measure_time(
            XivaFeatureExtractor.extract_customer_features,
            customer_id
        )
        features_total_time += elapsed
        if error:
            print(f"   {i}. {customer_name}: ERROR - {error}")
        else:
            features_success += 1
            feature_count = len(result) if result else 0
            print(f"   {i}. {customer_name}: {feature_count} features ({elapsed:.2f}s)")
    
    print(f"\n   Summary: {features_success}/{len(test_customers)} successful")
    print(f"   Total time: {features_total_time:.2f}s")
    print(f"   Average: {features_total_time/len(test_customers):.2f}s per customer")
    
    # ========================================================================
    # TEST SUITE 3: Edge Cases
    # ========================================================================
    print_section("TEST SUITE 3: Edge Cases & Error Handling")
    
    # Test 3.1: Invalid customer IDs
    print("\n[TEST 3.1] Invalid Customer ID Handling")
    print("-" * 80)
    invalid_ids = [
        "00000000-0000-0000-0000-000000000000",
        "invalid-id-format",
        "12345",
        "",
    ]
    
    for invalid_id in invalid_ids:
        try:
            result = client.get_customer_details(invalid_id)
            print(f"   '{invalid_id}': Unexpected success (returned data)")
        except XivaAPIError as e:
            print(f"   '{invalid_id}': Correctly rejected - {str(e)[:60]}")
        except Exception as e:
            print(f"   '{invalid_id}': Error - {type(e).__name__}")
    
    # Test 3.2: Search with various terms
    print("\n[TEST 3.2] Search Edge Cases")
    print("-" * 80)
    search_terms = [
        "a",  # Very short
        "nonexistentcustomer12345",  # Non-existent
        "",  # Empty
        "ahmad",  # Valid (should work)
    ]
    
    for term in search_terms:
        result, elapsed, error = measure_time(
            client.get_customer_list,
            search=term if term else None
        )
        if error:
            print(f"   Search '{term}': ERROR - {error}")
        else:
            count = len(result) if result else 0
            print(f"   Search '{term}': {count} results ({elapsed:.2f}s)")
    
    # Test 3.3: Empty result handling
    print("\n[TEST 3.3] Empty Result Handling")
    print("-" * 80)
    # Try to get usage for a customer that might not have usage
    result, elapsed, error = measure_time(
        client.get_customer_360_usage,
        test_customer_id,
        current_month_only=True
    )
    if error:
        print(f"   Usage (current month): ERROR - {error}")
    else:
        if isinstance(result, dict):
            by_date = result.get('by_date_and_type', {})
            usage_summary = result.get('usage_summary', {})
            print(f"   Usage (current month): OK")
            print(f"      Date breakdown: {len(by_date)} dates")
            print(f"      Has summary: {bool(usage_summary)}")
    
    # ========================================================================
    # TEST SUITE 4: Data Consistency
    # ========================================================================
    print_section("TEST SUITE 4: Data Consistency Checks")
    
    # Test 4.1: Cross-endpoint consistency
    print("\n[TEST 4.1] Cross-Endpoint Data Consistency")
    print("-" * 80)
    print(f"   Checking consistency for customer: {test_customer_id}")
    
    # Get data from different endpoints
    details = client.get_customer_details(test_customer_id)
    context = client.get_customer_full_context(test_customer_id)
    financial = client.get_customer_360_financial(test_customer_id)
    
    # Check customer ID consistency
    details_id = details.get('id') if details else None
    context_id = context.get('customer', {}).get('id') if context.get('customer') else None
    
    if details_id == context_id == test_customer_id:
        print(f"   [OK] Customer ID consistent across endpoints")
    else:
        print(f"   [WARNING] Customer ID mismatch:")
        print(f"      Details: {details_id}")
        print(f"      Context: {context_id}")
        print(f"      Expected: {test_customer_id}")
    
    # Check customer name consistency
    details_name = details.get('name') if details else None
    context_name = context.get('customer', {}).get('name') if context.get('customer') else None
    
    if details_name == context_name:
        print(f"   [OK] Customer name consistent: {details_name}")
    else:
        print(f"   [WARNING] Customer name mismatch:")
        print(f"      Details: {details_name}")
        print(f"      Context: {context_name}")
    
    # Check financial data consistency
    if financial:
        financial_customer_id = financial.get('customer_id')
        if financial_customer_id == test_customer_id:
            print(f"   [OK] Financial data customer ID matches")
        else:
            print(f"   [WARNING] Financial customer ID mismatch: {financial_customer_id}")
    
    # Test 4.2: Feature extraction consistency
    print("\n[TEST 4.2] Feature Extraction Consistency")
    print("-" * 80)
    
    # Extract features twice and compare
    features1 = XivaFeatureExtractor.extract_customer_features(test_customer_id)
    time.sleep(0.5)  # Small delay
    features2 = XivaFeatureExtractor.extract_customer_features(test_customer_id)
    
    if features1 == features2:
        print(f"   [OK] Features are consistent (identical on repeat extraction)")
    else:
        # Find differences
        keys1 = set(features1.keys()) if features1 else set()
        keys2 = set(features2.keys()) if features2 else set()
        
        if keys1 != keys2:
            print(f"   [WARNING] Feature keys differ:")
            print(f"      Only in first: {keys1 - keys2}")
            print(f"      Only in second: {keys2 - keys1}")
        else:
            # Same keys, check values
            differences = []
            for key in keys1:
                if features1.get(key) != features2.get(key):
                    differences.append(key)
            
            if differences:
                print(f"   [WARNING] {len(differences)} feature values differ: {differences[:5]}")
            else:
                print(f"   [OK] All feature values are consistent")
    
    # Test 4.3: FeatureStore consistency
    print("\n[TEST 4.3] FeatureStore Consistency")
    print("-" * 80)
    
    # Compare direct extraction vs FeatureStore
    direct_features = XivaFeatureExtractor.extract_customer_features(test_customer_id)
    store_features = FeatureStore.get_customer_features(test_customer_id, data_source='xiva')
    
    if direct_features and store_features:
        direct_keys = set(direct_features.keys())
        store_keys = set(store_features.keys())
        
        if direct_keys == store_keys:
            print(f"   [OK] FeatureStore returns same fields as direct extraction")
            print(f"      Field count: {len(direct_keys)}")
        else:
            print(f"   [WARNING] Field mismatch:")
            print(f"      Direct only: {direct_keys - store_keys}")
            print(f"      Store only: {store_keys - direct_keys}")
    else:
        print(f"   [WARNING] One or both extractions failed")
    
    # ========================================================================
    # TEST SUITE 5: Token Management
    # ========================================================================
    print_section("TEST SUITE 5: Token Management & Refresh")
    
    # Test 5.1: Token refresh behavior
    print("\n[TEST 5.1] Token Refresh Behavior")
    print("-" * 80)
    
    old_token = client.access_token
    print(f"   Current token: {old_token[:50]}...")
    print(f"   Token expires at: {client.token_expires_at}")
    
    # Force refresh
    try:
        new_token = client.refresh_access_token()
        if new_token != old_token:
            print(f"   [OK] Token refreshed successfully")
            print(f"   New token: {new_token[:50]}...")
        else:
            print(f"   [WARNING] Token refresh returned same token (may still be valid)")
    except Exception as e:
        print(f"   [ERROR] Token refresh failed: {e}")
    
    # Test 5.2: Multiple API calls with same token
    print("\n[TEST 5.2] Multiple API Calls (Token Reuse)")
    print("-" * 80)
    
    token_before = client.access_token
    print(f"   Making 5 API calls...")
    
    for i in range(5):
        try:
            result = client.get_customer_details(test_customer_id)
            print(f"   Call {i+1}: OK")
        except Exception as e:
            print(f"   Call {i+1}: ERROR - {e}")
    
    token_after = client.access_token
    if token_before == token_after:
        print(f"   [OK] Token unchanged after multiple calls (expected)")
    else:
        print(f"   [WARNING] Token changed (may have auto-refreshed)")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print_section("Test Summary")
    
    print("\n[PERFORMANCE SUMMARY]")
    if performance_results:
        avg_time = sum(performance_results.values()) / len(performance_results)
        max_time = max(performance_results.values())
        min_time = min(performance_results.values())
        print(f"   Average API call time: {avg_time:.2f}s")
        print(f"   Fastest: {min_time:.2f}s")
        print(f"   Slowest: {max_time:.2f}s")
    
    print("\n[RECOMMENDATIONS]")
    print("   1. Monitor API response times in production")
    print("   2. Consider caching for frequently accessed customer data")
    print("   3. Implement retry logic for transient errors")
    print("   4. Batch operations when processing multiple customers")
    print("   5. Use get_customer_full_context() for comprehensive data")
    
    print("\n" + "=" * 80)
    print("Advanced Testing Complete!")
    print(f"Test finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == '__main__':
    test_advanced()

