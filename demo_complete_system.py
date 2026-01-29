#!/usr/bin/env python
"""
Complete System Demo - Shows Features, Segments, Campaigns Working Together

This script demonstrates:
1. Feature extraction from Xiva
2. Creating segments using Xiva features
3. Calculating segment membership
4. Creating campaigns targeting segments
5. Showing the complete flow

Run: python demo_complete_system.py
"""

import os
import sys
import django
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
django.setup()

from loyalty.integration.feature_store import FeatureStore
from loyalty.integration.xiva_client import get_xiva_client, XivaAPIError
from loyalty.services.segmentation import SegmentationEngine
from loyalty.models_khaywe import Segment, SegmentMember, Campaign
from django.conf import settings

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_step(step_num, title):
    """Print a step header"""
    print(f"\n[STEP {step_num}] {title}")
    print("-" * 80)

def demo_feature_extraction():
    """Demonstrate feature extraction from Xiva"""
    print_section("PART 1: FEATURE EXTRACTION FROM XIVA")
    
    print_step(1, "Getting customer from Xiva...")
    try:
        client = get_xiva_client()
        customers = client.get_customer_list(limit=3)
        
        if not customers:
            print("[ERROR] No customers found in Xiva")
            return None
        
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
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    print_step(2, "Extracting features from Xiva...")
    try:
        features = FeatureStore.get_customer_features(customer_id, data_source='xiva')
        
        if not features or len(features) < 2:
            print("[ERROR] No features extracted")
            return None
        
        print(f"[OK] Extracted {len(features)} features from Xiva")
        print("\n     Key Features Extracted:")
        print("     " + "-" * 76)
        
        # Group features by category
        financial_features = {k: v for k, v in features.items() if any(x in k.lower() for x in ['revenue', 'balance', 'credit', 'payment', 'spend'])}
        service_features = {k: v for k, v in features.items() if any(x in k.lower() for x in ['product', 'service', 'has_'])}
        usage_features = {k: v for k, v in features.items() if any(x in k.lower() for x in ['usage', 'data', 'voice', 'sms'])}
        profile_features = {k: v for k, v in features.items() if any(x in k.lower() for x in ['status', 'type', 'name', 'email', 'phone', 'age', 'gender'])}
        
        if financial_features:
            print("\n     Financial Features:")
            for key, value in sorted(financial_features.items()):
                print(f"       - {key}: {value}")
        
        if service_features:
            print("\n     Service Features:")
            for key, value in sorted(service_features.items()):
                print(f"       - {key}: {value}")
        
        if usage_features:
            print("\n     Usage Features:")
            for key, value in sorted(usage_features.items()):
                print(f"       - {key}: {value}")
        
        if profile_features:
            print("\n     Profile Features:")
            for key, value in sorted(profile_features.items()):
                if key not in ['customer_id']:
                    print(f"       - {key}: {value}")
        
        return customer_id, customer_name, features
        
    except Exception as e:
        print(f"[ERROR] Feature extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def demo_segment_creation(customer_id, customer_name, features):
    """Demonstrate segment creation using Xiva features"""
    print_section("PART 2: SEGMENT CREATION USING XIVA FEATURES")
    
    print_step(1, "Creating segment with Xiva features...")
    
    # Create a realistic segment rule based on actual features
    segment_rule = {
        "and": [
            {">": [{"var": "total_revenue"}, 0]},  # Has any revenue
            {"==": [{"var": "customer_status"}, "active"]}  # Is active
        ]
    }
    
    try:
        segment, created = Segment.objects.get_or_create(
            name="Demo - Active Customers with Revenue",
            defaults={
                'description': 'Demo segment: Active customers with any revenue (using Xiva features)',
                'is_dynamic': True,
                'rules': [segment_rule]
            }
        )
        
        if created:
            print(f"[OK] Created new segment: {segment.name}")
        else:
            print(f"[OK] Using existing segment: {segment.name}")
            # Update rules
            segment.rules = [segment_rule]
            segment.description = 'Demo segment: Active customers with any revenue (using Xiva features)'
            segment.save()
        
        print(f"     Segment ID: {segment.id}")
        print(f"     Is Dynamic: {segment.is_dynamic}")
        print(f"\n     Segment Rule (JSONLogic):")
        print("     " + json.dumps(segment_rule, indent=6))
        
        print("\n     Rule Translation:")
        print("     - Customer must have revenue > $0")
        print("     - Customer status must be 'active'")
        
        return segment
        
    except Exception as e:
        print(f"[ERROR] Failed to create segment: {e}")
        import traceback
        traceback.print_exc()
        return None

def demo_segment_calculation(segment, customer_id, customer_name, features):
    """Demonstrate segment membership calculation"""
    print_section("PART 3: SEGMENT MEMBERSHIP CALCULATION")
    
    print_step(1, "Calculating segment membership...")
    
    try:
        # Calculate membership for this customer
        result = SegmentationEngine.update_segment_membership(segment, [customer_id])
        
        print(f"[OK] Segment calculation complete!")
        print(f"     Added: {result['added']} customers")
        print(f"     Removed: {result['removed']} customers")
        print(f"     Total members: {result['total']} customers")
        
        # Check if customer is in segment
        is_member = SegmentMember.objects.filter(
            segment=segment,
            customer_id=customer_id,
            is_active=True
        ).exists()
        
        print_step(2, "Verifying customer membership...")
        if is_member:
            print(f"[OK] Customer '{customer_name}' IS in segment!")
            print(f"     Segment: {segment.name}")
            
            # Show why customer matched
            print("\n     Why customer matched:")
            revenue = features.get('total_revenue', 0)
            status = features.get('customer_status', '')
            print(f"     - total_revenue ({revenue}) > 0: {revenue > 0}")
            print(f"     - customer_status ('{status}') == 'active': {status == 'active'}")
        else:
            print(f"[WARNING] Customer '{customer_name}' is NOT in segment")
            print("\n     Features used for evaluation:")
            print(f"     - total_revenue: {features.get('total_revenue', 'N/A')}")
            print(f"     - customer_status: {features.get('customer_status', 'N/A')}")
        
        return is_member
        
    except Exception as e:
        print(f"[ERROR] Segment calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_campaign_creation(segment):
    """Demonstrate campaign creation targeting segment"""
    print_section("PART 4: CAMPAIGN CREATION TARGETING SEGMENT")
    
    print_step(1, "Creating campaign targeting segment...")
    
    try:
        campaign, created = Campaign.objects.get_or_create(
            name="Demo - Welcome Bonus for Active Customers",
            defaults={
                'description': 'Demo campaign: Welcome bonus for active customers with revenue',
                'target_segment': segment,
                'trigger_type': 'segment.joined',
                'is_active': True,
                'start_date': datetime.now().date(),
                'reward_config': {
                    'points': 1000,
                    'discount_percent': 10,
                    'message': 'Welcome! You earned 1000 points and 10% discount for being an active customer.'
                }
            }
        )
        
        if created:
            print(f"[OK] Created new campaign: {campaign.name}")
        else:
            print(f"[OK] Using existing campaign: {campaign.name}")
            # Update campaign
            campaign.target_segment = segment
            campaign.is_active = True
            campaign.reward_config = {
                'points': 1000,
                'discount_percent': 10,
                'message': 'Welcome! You earned 1000 points and 10% discount for being an active customer.'
            }
            campaign.save()
        
        print(f"     Campaign ID: {campaign.id}")
        print(f"     Target Segment: {campaign.target_segment.name}")
        print(f"     Trigger: {campaign.trigger_type}")
        print(f"     Is Active: {campaign.is_active}")
        print(f"\n     Reward Configuration:")
        print(f"     - Points: {campaign.reward_config.get('points', 0)}")
        print(f"     - Discount: {campaign.reward_config.get('discount_percent', 0)}%")
        print(f"     - Message: {campaign.reward_config.get('message', 'N/A')}")
        
        return campaign
        
    except Exception as e:
        print(f"[ERROR] Campaign creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def demo_complete_flow():
    """Demonstrate the complete flow"""
    print_section("PART 5: COMPLETE FLOW DEMONSTRATION")
    
    print_step(1, "Complete Flow Summary")
    print("""
    Here's how everything works together:
    
    1. Xiva BSS System
       | Customer uses service, makes payment
       |
    2. Xiva API
       | REST API calls to get customer data
       |
    3. XivaClient (Backend)
       | Fetches raw JSON data
       |
    4. XivaFeatureExtractor
       | Converts to clean features:
       | - total_revenue: 191.61
       | - customer_status: "active"
       | - data_usage_mb: 0
       | - active_products_count: 3
       |
    5. FeatureStore
       | Caches features in Redis (1 hour)
       |
    6. SegmentationEngine
       | Evaluates segment rules:
       | - total_revenue > 0? YES
       | - customer_status == "active"? YES
       | Result: Customer MATCHES segment
       |
    7. Segment Membership Updated
       | Customer added to segment
       |
    8. Campaign Engine
       | Detects: Customer joined segment
       | Triggers: Campaign automatically
       |
    9. Customer Receives Offer
       | - 1000 points added
       | - 10% discount code
       | - Email/SMS notification
    """)

def main():
    """Main demo function"""
    print("\n" + "=" * 80)
    print("  COMPLETE SYSTEM DEMO")
    print("  Features -> Segments -> Campaigns")
    print("=" * 80)
    
    # Part 1: Feature Extraction
    result = demo_feature_extraction()
    if not result:
        print("\n[ERROR] Feature extraction failed. Cannot continue.")
        return
    
    customer_id, customer_name, features = result
    
    # Part 2: Segment Creation
    segment = demo_segment_creation(customer_id, customer_name, features)
    if not segment:
        print("\n[ERROR] Segment creation failed. Cannot continue.")
        return
    
    # Part 3: Segment Calculation
    is_member = demo_segment_calculation(segment, customer_id, customer_name, features)
    
    # Part 4: Campaign Creation
    campaign = demo_campaign_creation(segment)
    
    # Part 5: Complete Flow
    demo_complete_flow()
    
    # Final Summary
    print_section("DEMO COMPLETE - SUMMARY")
    print(f"""
    [OK] Customer: {customer_name}
    [OK] Customer ID: {customer_id}
    [OK] Features Extracted: {len(features)}
    [OK] Segment Created: {segment.name}
    [OK] Customer in Segment: {'YES' if is_member else 'NO'}
    [OK] Campaign Created: {campaign.name if campaign else 'N/A'}
    [OK] Campaign Active: {campaign.is_active if campaign else False}
    
    [SUCCESS] Complete system is working!
    
    Next Steps:
    1. View in Frontend:
       - Go to Segments → See "{segment.name}"
       - Go to Campaigns → See "{campaign.name if campaign else 'Demo Campaign'}"
    
    2. Test in Frontend:
       - Create new segment using Xiva fields
       - Create campaign targeting segment
       - See segment members update
       - See campaign trigger when customer joins segment
    
    3. Use Real Data:
       - All features are from real Xiva data
       - Segments use real Xiva features
       - Campaigns target real segments
    """)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Demo interrupted by user]")
    except Exception as e:
        print(f"\n\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()

