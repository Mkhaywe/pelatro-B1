"""
Test All ML Models
Validates all 9 ML models work correctly and produce valid outputs
"""
import os
import sys
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
import django
django.setup()

from loyalty.ml.inference import MLInferenceService
from loyalty.integration.feature_store import FeatureStore

print("="*70)
print("TESTING ALL ML MODELS")
print("="*70)
print()

# Get a test customer ID
feature_store = FeatureStore()
test_customer_id = "a0d35428-612c-5483-46e7-48c6bdd6ab59"  # From your error log

print(f"Testing with customer: {test_customer_id}")
print()

ml_service = MLInferenceService()

models_to_test = [
    ('churn', 'Churn Prediction'),
    ('nbo', 'Next Best Offer'),
    ('rfm', 'RFM Analysis'),
    ('ltv', 'Lifetime Value'),
    ('propensity', 'Propensity to Buy'),
    ('product', 'Product Recommendation'),
    ('campaign', 'Campaign Response'),
    ('default_risk', 'Payment Default Risk'),
    ('upsell', 'Upsell Propensity'),
    ('engagement', 'Engagement Score'),
]

results = {}
errors = []

for model_key, model_name in models_to_test:
    print(f"\n{'='*70}")
    print(f"Testing: {model_name} ({model_key})")
    print(f"{'='*70}")
    
    try:
        if model_key == 'churn':
            result = ml_service.predict_churn(test_customer_id)
        elif model_key == 'nbo':
            result = ml_service.predict_nbo(test_customer_id)
        elif model_key == 'rfm':
            result = ml_service.calculate_rfm(test_customer_id)
        elif model_key == 'ltv':
            result = ml_service.predict_ltv(test_customer_id)
        elif model_key == 'propensity':
            result = ml_service.predict_propensity_to_buy(test_customer_id)
        elif model_key == 'product':
            result = ml_service.recommend_products(test_customer_id)
        elif model_key == 'campaign':
            result = ml_service.predict_campaign_response(test_customer_id, campaign_id="test")
        elif model_key == 'default_risk':
            result = ml_service.predict_payment_default_risk(test_customer_id)
        elif model_key == 'upsell':
            result = ml_service.predict_upsell_propensity(test_customer_id)
        elif model_key == 'engagement':
            result = ml_service.calculate_engagement_score(test_customer_id)
        else:
            result = {'error': f'Unknown model: {model_key}'}
        
        if 'error' in result:
            print(f"[ERROR] {result['error']}")
            errors.append((model_name, result['error']))
        else:
            print(f"[SUCCESS]")
            print(f"Result keys: {list(result.keys())}")
            
            # Validate output structure
            if model_key == 'churn':
                assert 'churn_probability' in result, "Missing churn_probability"
                assert 'churn_risk' in result, "Missing churn_risk"
                assert 'explanation' in result, "Missing explanation"
                print(f"  Churn Probability: {result.get('churn_probability', 0)*100:.2f}%")
                print(f"  Risk Level: {result.get('churn_risk', 'unknown')}")
                print(f"  Explanation: {result.get('explanation', '')[:100]}...")
            elif model_key == 'nbo':
                assert 'recommended_offer' in result, "Missing recommended_offer"
                assert 'confidence' in result, "Missing confidence"
                print(f"  Recommended Offer: {result.get('recommended_offer', 'N/A')}")
                print(f"  Confidence: {result.get('confidence', 0)*100:.2f}%")
                if 'offer_details' in result:
                    print(f"  Offer Details: {result.get('offer_details', {}).get('name', 'N/A')}")
            elif model_key == 'rfm':
                assert 'segment' in result, "Missing segment"
                print(f"  RFM Segment: {result.get('segment', 'N/A')}")
                print(f"  R: {result.get('recency', 'N/A')}, F: {result.get('frequency', 'N/A')}, M: {result.get('monetary', 'N/A')}")
            elif model_key == 'ltv':
                assert 'predicted_ltv' in result, "Missing predicted_ltv"
                print(f"  Predicted LTV: ${result.get('predicted_ltv', 0):.2f}")
            elif model_key == 'propensity':
                assert 'propensity_score' in result, "Missing propensity_score"
                print(f"  Propensity Score: {result.get('propensity_score', 0)*100:.2f}%")
                print(f"  Propensity Level: {result.get('propensity_level', 'unknown')}")
            elif model_key == 'product':
                assert 'recommended_products' in result, "Missing recommended_products"
                print(f"  Recommended Products: {len(result.get('recommended_products', []))}")
            elif model_key == 'campaign':
                assert 'response_prediction' in result, "Missing response_prediction"
                print(f"  Response Prediction: {result.get('response_prediction', 'unknown')}")
                print(f"  Response Probability: {result.get('response_probability', 0)*100:.2f}%")
            elif model_key == 'default_risk':
                assert 'default_risk_score' in result, "Missing default_risk_score"
                print(f"  Default Risk Score: {result.get('default_risk_score', 0)*100:.2f}%")
                print(f"  Risk Level: {result.get('risk_level', 'unknown')}")
            elif model_key == 'upsell':
                assert 'upsell_propensity' in result, "Missing upsell_propensity"
                print(f"  Upsell Propensity: {result.get('upsell_propensity', 0)*100:.2f}%")
                print(f"  Propensity Level: {result.get('propensity_level', 'unknown')}")
            elif model_key == 'engagement':
                assert 'engagement_score' in result, "Missing engagement_score"
                print(f"  Engagement Score: {result.get('engagement_score', 0):.2f}/100")
            
            results[model_key] = result
            
    except Exception as e:
        print(f"[EXCEPTION] {str(e)}")
        import traceback
        traceback.print_exc()
        errors.append((model_name, str(e)))

print()
print("="*70)
print("SUMMARY")
print("="*70)
print(f"[SUCCESS] Successful: {len(results)}/{len(models_to_test)}")
print(f"[ERROR] Errors: {len(errors)}/{len(models_to_test)}")

if errors:
    print("\nErrors:")
    for model_name, error in errors:
        print(f"  - {model_name}: {error}")

print()
print("="*70)
print("VALIDATION COMPLETE")
print("="*70)

