#!/usr/bin/env python
"""
Add more demo data: transactions, segment memberships, badge awards
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')

import django
django.setup()

from django.utils import timezone
from loyalty.models import LoyaltyProgram, LoyaltyAccount, LoyaltyTransaction, LoyaltyReward
from loyalty.models_khaywe import Segment, SegmentMember, Badge, BadgeAward, MissionProgress
from loyalty.integration.feature_store import FeatureStore
from loyalty.services.segmentation import SegmentationEngine

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def create_transactions():
    """Create sample transactions for accounts"""
    print_section("CREATING SAMPLE TRANSACTIONS")
    
    accounts = LoyaltyAccount.objects.all()[:5]
    transaction_types = ['earn', 'earn', 'earn', 'redeem', 'earn']  # Mix of earn/redeem
    amounts = [100, 250, 500, 200, 150]
    descriptions = [
        'Purchase reward points',
        'Referral bonus',
        'Monthly loyalty bonus',
        'Reward redemption',
        'Special promotion points'
    ]
    
    created = 0
    for i, account in enumerate(accounts):
        for j in range(3):  # 3 transactions per account
            tx = LoyaltyTransaction.objects.create(
                account=account,
                amount=amounts[(i+j) % len(amounts)],
                transaction_type=transaction_types[(i+j) % len(transaction_types)],
                description=descriptions[(i+j) % len(descriptions)]
            )
            created += 1
            print(f"  [OK] Created transaction: {tx.transaction_type} {tx.amount} points for account {account.id}")
    
    print(f"\n  Created {created} transactions")
    return created

def calculate_segment_memberships():
    """Calculate and create segment memberships"""
    print_section("CALCULATING SEGMENT MEMBERSHIPS")
    
    segments = Segment.objects.filter(is_active=True)
    accounts = LoyaltyAccount.objects.all()[:10]  # Use first 10 accounts
    
    total_members = 0
    for segment in segments:
        print(f"\n  Calculating: {segment.name}...")
        members_added = 0
        
        for account in accounts:
            customer_id = str(account.customer_id)
            
            # Evaluate segment rules
            try:
                matches = SegmentationEngine.evaluate_segment(segment, customer_id)
                
                if matches:
                    # Add to segment
                    member, created = SegmentMember.objects.get_or_create(
                        segment=segment,
                        customer_id=account.customer_id,
                        defaults={'is_active': True}
                    )
                    if created:
                        members_added += 1
                        total_members += 1
            except Exception as e:
                print(f"    [WARN] Could not evaluate customer {customer_id}: {e}")
                continue
        
        print(f"    [OK] Added {members_added} members to {segment.name}")
    
    print(f"\n  Total segment memberships created: {total_members}")
    return total_members

def create_badge_awards():
    """Award some badges to customers"""
    print_section("AWARDING BADGES")
    
    badges = Badge.objects.filter(is_active=True)[:3]  # First 3 badges
    accounts = LoyaltyAccount.objects.all()[:5]
    
    awarded = 0
    for i, account in enumerate(accounts):
        if i < len(badges):
            badge = badges[i]
            award, created = BadgeAward.objects.get_or_create(
                badge=badge,
                customer_id=account.customer_id,
                defaults={'awarded_reason': f'Demo badge award for {badge.name}'}
            )
            if created:
                awarded += 1
                print(f"  [OK] Awarded badge '{badge.name}' to customer {account.customer_id}")
    
    print(f"\n  Awarded {awarded} badges")
    return awarded

def create_mission_progress():
    """Create mission progress for customers"""
    print_section("CREATING MISSION PROGRESS")
    
    from loyalty.models_khaywe import Mission
    missions = Mission.objects.filter(is_active=True)[:2]
    accounts = LoyaltyAccount.objects.all()[:3]
    
    created = 0
    for mission in missions:
        for account in accounts:
            progress, created_progress = MissionProgress.objects.get_or_create(
                mission=mission,
                customer_id=account.customer_id,
                defaults={
                    'current_value': 0,
                    'target_value': mission.objective.get('points', 100) if isinstance(mission.objective, dict) else 100,
                    'progress_percentage': 0.0,
                    'is_completed': False
                }
            )
            if created_progress:
                created += 1
                print(f"  [OK] Created progress for {mission.name} - customer {account.customer_id}")
    
    print(f"\n  Created {created} mission progress records")
    return created

def main():
    print("\n" + "="*80)
    print("  ADDING MORE DEMO DATA")
    print("="*80)
    
    try:
        # Create transactions
        tx_count = create_transactions()
        
        # Calculate segment memberships
        members_count = calculate_segment_memberships()
        
        # Award badges
        badges_count = create_badge_awards()
        
        # Create mission progress
        missions_count = create_mission_progress()
        
        # Summary
        print_section("ADDITIONAL DATA SUMMARY")
        print(f"  [OK] Transactions: {tx_count}")
        print(f"  [OK] Segment Memberships: {members_count}")
        print(f"  [OK] Badge Awards: {badges_count}")
        print(f"  [OK] Mission Progress: {missions_count}")
        
        print("\n" + "="*80)
        print("  ADDITIONAL DEMO DATA COMPLETE!")
        print("="*80)
        print("\nThe demo is now fully populated with:")
        print("  - Customer transactions")
        print("  - Segment memberships (calculated from Xiva features)")
        print("  - Badge awards")
        print("  - Mission progress")
        print("\n")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to add demo data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

