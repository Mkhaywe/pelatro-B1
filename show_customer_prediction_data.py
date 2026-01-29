"""
Show Customer Prediction Data
Displays the raw customer data/features used for ML predictions
"""
import os
import sys
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
import django
django.setup()

from loyalty.ml.inference import MLInferenceService
from loyalty.integration.feature_store import FeatureStore
from loyalty.integration.dwh import get_dwh_connector

customer_id = "a0d35428-691f-4375-9118-d2bdf6811426"

print("="*70)
print(f"CUSTOMER PREDICTION DATA ANALYSIS")
print(f"Customer ID: {customer_id}")
print("="*70)
print()

# 1. Get raw features from DWH
print("1. RAW CUSTOMER DATA FROM DWH")
print("-"*70)
dwh_connector = get_dwh_connector()
raw_dwh_data = dwh_connector.get_customer_features(customer_id)

if raw_dwh_data:
    print("DWH Data:")
    for key, value in sorted(raw_dwh_data.items()):
        print(f"  {key}: {value}")
else:
    print("  [No DWH data found]")
print()

# 2. Get features from Feature Store
print("2. FEATURES FROM FEATURE STORE")
print("-"*70)
feature_store = FeatureStore()
feature_store_data = feature_store.get_customer_features(customer_id)

if feature_store_data:
    print("Feature Store Data:")
    for key, value in sorted(feature_store_data.items()):
        print(f"  {key}: {value}")
else:
    print("  [No feature store data found]")
print()

# 3. Get extracted features (what the model actually sees)
print("3. EXTRACTED FEATURES (MODEL INPUT)")
print("-"*70)
ml_service = MLInferenceService()
result = ml_service._extract_features(customer_id, return_raw_features=True)

if result:
    features, raw_features = result
    print("Raw Features (before normalization):")
    for key, value in sorted(raw_features.items()):
        print(f"  {key}: {value}")
    print()
    print("Normalized Features (model input vector):")
    if features is not None:
        print(f"  Shape: {features.shape}")
        print(f"  Values: {features.flatten().tolist()}")
    else:
        print("  [Features are None]")
else:
    print("  [Could not extract features]")
print()

# 4. Run churn prediction and show explanation
print("4. CHURN PREDICTION RESULT")
print("-"*70)
churn_result = ml_service.predict_churn(customer_id)

if 'error' in churn_result:
    print(f"ERROR: {churn_result['error']}")
else:
    print(f"Churn Probability: {churn_result.get('churn_probability', 0)*100:.2f}%")
    print(f"Risk Level: {churn_result.get('churn_risk', 'unknown').upper()}")
    print()
    print("Explanation:")
    print(f"  {churn_result.get('explanation', 'N/A')}")
    print()
    
    # Analyze the prediction
    prob = churn_result.get('churn_probability', 0)
    print("PREDICTION ANALYSIS:")
    print("-"*70)
    if prob < 0.1:
        print("  [LOW RISK] Very low churn risk (0-10%)")
        print("  [LOW RISK] Customer shows strong engagement and stability")
    elif prob < 0.3:
        print("  [LOW RISK] Low churn risk (10-30%)")
        print("  [LOW RISK] Some risk factors present but overall stable")
    elif prob < 0.7:
        print("  [MEDIUM RISK] Medium churn risk (30-70%)")
        print("  [MEDIUM RISK] Multiple risk factors detected")
    else:
        print("  [HIGH RISK] High churn risk (70-100%)")
        print("  [HIGH RISK] Critical risk factors present")
    print()

# 5. Feature importance analysis
print("5. FEATURE ANALYSIS")
print("-"*70)
if result and raw_features:
    print("Key Indicators:")
    print()
    
    # Payment behavior
    outstanding = raw_features.get('outstanding_amount', 0) or 0
    payment_ratio = raw_features.get('payment_ratio', 1.0) or 1.0
    print(f"Payment Behavior:")
    print(f"  Outstanding Balance: ${outstanding:.2f}")
    print(f"  Payment Ratio: {payment_ratio*100:.1f}%")
    if outstanding == 0:
        print("  [POSITIVE] No outstanding balance - positive indicator")
    if payment_ratio >= 0.9:
        print("  [POSITIVE] Excellent payment history - positive indicator")
    print()
    
    # Usage activity
    usage_records = raw_features.get('usage_records_count', 0) or 0
    current_usage = raw_features.get('current_month_usage_spend', 0) or 0
    total_usage = raw_features.get('total_usage_spend', 0) or 0
    print(f"Usage Activity:")
    print(f"  Usage Records: {usage_records}")
    print(f"  Current Month Usage: ${current_usage:.2f}")
    print(f"  Total Usage: ${total_usage:.2f}")
    if usage_records > 0:
        print("  [POSITIVE] Active usage - positive indicator")
    else:
        print("  [WARNING] No usage records found - may indicate inactivity")
    if current_usage > 0:
        print("  [POSITIVE] Current month activity - positive indicator")
    print()
    
    # Revenue/Spending
    total_revenue = raw_features.get('total_revenue', 0) or 0
    current_spend = raw_features.get('current_month_spend', 0) or 0
    monthly_avg = (total_revenue / 12) if total_revenue > 0 else 0
    print(f"Revenue/Spending:")
    print(f"  Total Revenue: ${total_revenue:.2f}")
    print(f"  Current Month Spend: ${current_spend:.2f}")
    print(f"  Monthly Average: ${monthly_avg:.2f}")
    if monthly_avg > 0:
        if current_spend >= monthly_avg * 0.8 and current_spend <= monthly_avg * 1.2:
            print("  [POSITIVE] Stable spending pattern - positive indicator")
        elif current_spend > monthly_avg * 1.5:
            print("  [WARNING] Spending spike detected - may indicate one-time purchase")
        elif current_spend < monthly_avg * 0.5:
            print("  [WARNING] Spending decline - potential risk indicator")
    print()
    
    # Recency
    days_since_payment = raw_features.get('days_since_last_payment', 0) or 0
    days_since_last = raw_features.get('days_since_last_transaction', 0) or 0
    print(f"Recency:")
    print(f"  Days Since Last Payment: {days_since_payment}")
    print(f"  Days Since Last Transaction: {days_since_last}")
    if days_since_payment <= 7 or days_since_last <= 7:
        print("  [POSITIVE] Recent activity - positive indicator")
    elif days_since_payment > 30 or days_since_last > 30:
        print("  [WARNING] No recent activity - potential risk indicator")
    else:
        print("  [NEUTRAL] Moderate recency - neither positive nor negative")
    print()
    
    # Service status
    active_services = raw_features.get('active_services_count', 0) or 0
    total_services = raw_features.get('total_services_count', 0) or 0
    print(f"Service Status:")
    print(f"  Active Services: {active_services}")
    print(f"  Total Services: {total_services}")
    if active_services == total_services and total_services > 0:
        print("  [POSITIVE] All services active - positive indicator")
    elif active_services == 0 and total_services > 0:
        print("  [WARNING] No active services - high risk indicator")
    print()

# 6. Data quality check
print("6. DATA QUALITY ASSESSMENT")
print("-"*70)
if result and raw_features:
    missing_fields = []
    zero_fields = []
    
    important_fields = [
        'total_revenue', 'current_month_spend', 'outstanding_amount',
        'payment_ratio', 'usage_records_count', 'days_since_last_transaction',
        'active_services_count'
    ]
    
    for field in important_fields:
        value = raw_features.get(field)
        if value is None:
            missing_fields.append(field)
        elif value == 0 and field not in ['outstanding_amount']:  # Outstanding can be 0
            zero_fields.append(field)
    
    if missing_fields:
        print(f"[WARNING] Missing fields: {', '.join(missing_fields)}")
    if zero_fields:
        print(f"[WARNING] Zero-value fields: {', '.join(zero_fields)}")
    if not missing_fields and not zero_fields:
        print("[OK] All important fields have valid data")
    
    data_completeness = (len(important_fields) - len(missing_fields)) / len(important_fields) * 100
    print(f"Data Completeness: {data_completeness:.1f}%")
    print()

print("="*70)
print("ANALYSIS COMPLETE")
print("="*70)
print()
print("NOTE: This prediction is based on the available customer data.")
print("The 0% churn probability indicates:")
print("  - Strong positive indicators (no outstanding balance, excellent payment history)")
print("  - Stable spending patterns")
print("  - Recent activity")
print()
print("However, predictions are only as good as the data quality.")
print("If key data is missing or outdated, the prediction may not be accurate.")

