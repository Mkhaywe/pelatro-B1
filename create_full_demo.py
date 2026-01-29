#!/usr/bin/env python
"""
Comprehensive Demo Data Creation Script
Creates a full demo environment with programs, segments, campaigns, rewards, and gamification
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4
import json

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')

import django
django.setup()

# Suppress JSONField warnings for SQLite
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='django.db.models.fields.json')

from django.utils import timezone
from loyalty.models import (
    LoyaltyProgram, LoyaltyTier, LoyaltyAccount, LoyaltyTransaction,
    LoyaltyReward, LoyaltyRedemption
)
from loyalty.models_khaywe import (
    Campaign, Segment, SegmentMember,
    Mission, Badge, BadgeAward, Leaderboard, LeaderboardEntry,
    Journey, JourneyNode, JourneyEdge
)
from loyalty.integration.xiva_client import get_xiva_client

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_step(num, text):
    print(f"\n[{num}] {text}")

def create_loyalty_program():
    """Create a main loyalty program with tiers"""
    print_section("CREATING LOYALTY PROGRAM")
    
    # Create program
    program, created = LoyaltyProgram.objects.get_or_create(
        name="Pelatro Premium Rewards",
        defaults={
            'description': 'Main loyalty program with points, tiers, and rewards',
            'start_date': timezone.now() - timedelta(days=365),
            'end_date': timezone.now() + timedelta(days=365),
            'is_active': True
        }
    )
    
    if created:
        print(f"[OK] Created program: {program.name}")
    else:
        print(f"[OK] Using existing program: {program.name}")
    
    # Create tiers
    tiers_data = [
        {'name': 'Bronze', 'min_points': 0, 'description': 'Entry level tier', 'priority': 1},
        {'name': 'Silver', 'min_points': 1000, 'description': 'Mid-tier with better benefits', 'priority': 2},
        {'name': 'Gold', 'min_points': 5000, 'description': 'Premium tier with exclusive benefits', 'priority': 3},
        {'name': 'Platinum', 'min_points': 15000, 'description': 'Elite tier with VIP benefits', 'priority': 4},
    ]
    
    tiers = []
    for tier_data in tiers_data:
        tier, created = LoyaltyTier.objects.get_or_create(
            program=program,
            name=tier_data['name'],
            defaults={
                'min_points': tier_data['min_points'],
                'description': tier_data['description'],
                'priority': tier_data['priority'],
                'benefits': f"Benefits for {tier_data['name']} tier members"
            }
        )
        tiers.append(tier)
        if created:
            print(f"  [OK] Created tier: {tier.name} (min {tier.min_points} points)")
        else:
            print(f"  [OK] Using existing tier: {tier.name}")
    
    return program, tiers

def create_segments(program):
    """Create segments using Xiva features"""
    print_section("CREATING SEGMENTS WITH XIVA FEATURES")
    
    segments_data = [
        {
            'name': 'High Value Customers',
            'description': 'Customers with high revenue and active status',
            'rules': [{
                "and": [
                    {">": [{"var": "total_revenue"}, 500]},
                    {"==": [{"var": "customer_status"}, "active"]},
                    {">": [{"var": "active_products_count"}, 0]}
                ]
            }]
        },
        {
            'name': 'Data Power Users',
            'description': 'Customers who use significant data',
            'rules': [{
                "and": [
                    {">": [{"var": "data_usage_mb"}, 1000]},
                    {"==": [{"var": "has_data_service"}, True]},
                    {"==": [{"var": "customer_status"}, "active"]}
                ]
            }]
        },
        {
            'name': 'At-Risk Customers',
            'description': 'Customers with low usage or high credit utilization',
            'rules': [{
                "or": [
                    {"<": [{"var": "data_usage_mb"}, 100]},
                    {">": [{"var": "credit_utilization"}, 0.8]},
                    {"<": [{"var": "current_month_spend"}, 0]}
                ]
            }]
        },
        {
            'name': 'New Customers',
            'description': 'Recently acquired customers',
            'rules': [{
                "and": [
                    {"<": [{"var": "customer_age_days"}, 90]},
                    {"==": [{"var": "customer_status"}, "active"]}
                ]
            }]
        },
        {
            'name': 'Premium Service Users',
            'description': 'Customers with premium products',
            'rules': [{
                "and": [
                    {">": [{"var": "active_products_count"}, 2]},
                    {"==": [{"var": "customer_status"}, "active"]},
                    {">": [{"var": "total_revenue"}, 200]}
                ]
            }]
        }
    ]
    
    segments = []
    for seg_data in segments_data:
        segment, created = Segment.objects.get_or_create(
            name=seg_data['name'],
            defaults={
                'description': seg_data['description'],
                'program': program,
                'rules': seg_data['rules'],
                'is_dynamic': True,
                'is_active': True
            }
        )
        
        if not created:
            # Update existing segment
            segment.description = seg_data['description']
            segment.rules = seg_data['rules']
            segment.program = program
            segment.save()
        
        segments.append(segment)
        if created:
            print(f"  [OK] Created segment: {segment.name}")
            print(f"      Rules: {len(segment.rules)} rule(s)")
        else:
            print(f"  [OK] Updated segment: {segment.name}")
    
    return segments

def create_campaigns(program, segments):
    """Create campaigns targeting different segments"""
    print_section("CREATING CAMPAIGNS")
    
    now = timezone.now()
    
    campaigns_data = [
        {
            'name': 'Welcome Bonus for New Customers',
            'description': 'Special welcome offer for new customers',
            'segment': segments[3] if len(segments) > 3 else None,  # New Customers
            'status': 'active',
            'start_date': now - timedelta(days=7),
            'end_date': now + timedelta(days=30),
            'channels': ['email', 'sms'],
            'eligibility_rules': {},
            'event_triggers': [],
            'schedule_triggers': [],
            'threshold_triggers': []
        },
        {
            'name': 'Data Boost Campaign',
            'description': 'Extra data bonus for power users',
            'segment': segments[1] if len(segments) > 1 else None,  # Data Power Users
            'status': 'active',
            'start_date': now - timedelta(days=3),
            'end_date': now + timedelta(days=60),
            'channels': ['email', 'push'],
            'eligibility_rules': {},
            'event_triggers': [],
            'schedule_triggers': [],
            'threshold_triggers': []
        },
        {
            'name': 'Retention Campaign - At-Risk',
            'description': 'Win-back campaign for at-risk customers',
            'segment': segments[2] if len(segments) > 2 else None,  # At-Risk
            'status': 'active',
            'start_date': now,
            'end_date': now + timedelta(days=45),
            'channels': ['email', 'sms', 'push'],
            'eligibility_rules': {},
            'event_triggers': [],
            'schedule_triggers': [],
            'threshold_triggers': []
        },
        {
            'name': 'VIP Rewards Program',
            'description': 'Exclusive rewards for high-value customers',
            'segment': segments[0] if len(segments) > 0 else None,  # High Value
            'status': 'active',
            'start_date': now - timedelta(days=14),
            'end_date': now + timedelta(days=90),
            'channels': ['email'],
            'eligibility_rules': {},
            'event_triggers': [],
            'schedule_triggers': [],
            'threshold_triggers': []
        }
    ]
    
    campaigns = []
    for camp_data in campaigns_data:
        campaign, created = Campaign.objects.get_or_create(
            name=camp_data['name'],
            defaults={
                'description': camp_data['description'],
                'program': program,
                'segment': camp_data['segment'],
                'status': camp_data['status'],
                'start_date': camp_data['start_date'],
                'end_date': camp_data['end_date'],
                'channels': camp_data['channels'],
                'eligibility_rules': camp_data.get('eligibility_rules', {}),
                'event_triggers': camp_data.get('event_triggers', []),
                'schedule_triggers': camp_data.get('schedule_triggers', []),
                'threshold_triggers': camp_data.get('threshold_triggers', [])
            }
        )
        
        if not created:
            # Update existing campaign
            campaign.status = camp_data['status']
            campaign.segment = camp_data['segment']
            campaign.start_date = camp_data['start_date']
            campaign.end_date = camp_data['end_date']
            campaign.save()
        
        campaigns.append(campaign)
        if created:
            print(f"  [OK] Created campaign: {campaign.name}")
            print(f"      Status: {campaign.status}, Segment: {campaign.segment.name if campaign.segment else 'None'}")
        else:
            print(f"  [OK] Updated campaign: {campaign.name}")
    
    return campaigns

def create_rewards(program):
    """Create reward catalog"""
    print_section("CREATING REWARDS CATALOG")
    
    rewards_data = [
        {'name': 'Free 1GB Data', 'description': 'Get 1GB of free data', 'points_required': 500},
        {'name': 'Free 5GB Data', 'description': 'Get 5GB of free data', 'points_required': 2000},
        {'name': '10% Discount Voucher', 'description': '10% off your next bill', 'points_required': 1000},
        {'name': '20% Discount Voucher', 'description': '20% off your next bill', 'points_required': 2500},
        {'name': 'Free Month Service', 'description': 'One month free service', 'points_required': 5000},
        {'name': 'Premium Upgrade', 'description': 'Upgrade to premium plan', 'points_required': 7500},
        {'name': 'VIP Support Access', 'description': 'Access to VIP customer support', 'points_required': 3000},
        {'name': 'Early Access to Features', 'description': 'Early access to new features', 'points_required': 1500},
    ]
    
    rewards = []
    for reward_data in rewards_data:
        reward, created = LoyaltyReward.objects.get_or_create(
            program=program,
            name=reward_data['name'],
            defaults={
                'description': reward_data['description'],
                'points_required': reward_data['points_required'],
                'is_active': True
            }
        )
        
        if not created:
            reward.points_required = reward_data['points_required']
            reward.is_active = True
            reward.save()
        
        rewards.append(reward)
        if created:
            print(f"  [OK] Created reward: {reward.name} ({reward.points_required} points)")
        else:
            print(f"  [OK] Updated reward: {reward.name}")
    
    return rewards

def create_gamification(program):
    """Create gamification elements"""
    print_section("CREATING GAMIFICATION ELEMENTS")
    
    now = timezone.now()
    
    # Create badges
    badges_data = [
        {'name': 'First Steps', 'description': 'Earned your first 100 points', 'rarity': 'common'},
        {'name': 'Data Master', 'description': 'Used 10GB of data in a month', 'rarity': 'rare'},
        {'name': 'Loyal Customer', 'description': 'Active for 6 months', 'rarity': 'rare'},
        {'name': 'High Roller', 'description': 'Earned 10,000 points', 'rarity': 'epic'},
        {'name': 'VIP Member', 'description': 'Reached Platinum tier', 'rarity': 'legendary'},
    ]
    
    badges = []
    for badge_data in badges_data:
        badge, created = Badge.objects.get_or_create(
            program=program,
            name=badge_data['name'],
            defaults={
                'description': badge_data['description'],
                'rarity': badge_data['rarity'],
                'is_active': True,
                'requirements': {'points': 0}  # Simplified
            }
        )
        badges.append(badge)
        if created:
            print(f"  [OK] Created badge: {badge.name} ({badge.rarity})")
        else:
            print(f"  [OK] Using existing badge: {badge.name}")
    
    # Create missions
    missions_data = [
        {
            'name': 'Weekly Points Challenge',
            'description': 'Earn 500 points this week',
            'mission_type': 'points_earn',
            'objective': {'points': 500, 'period': 'week'},
            'reward_points': 100,
            'start_date': now,
            'end_date': now + timedelta(days=7)
        },
        {
            'name': 'Data Usage Goal',
            'description': 'Use 5GB of data this month',
            'mission_type': 'custom',
            'objective': {'data_usage_mb': 5000, 'period': 'month'},
            'reward_points': 250,
            'start_date': now,
            'end_date': now + timedelta(days=30)
        },
        {
            'name': 'Transaction Streak',
            'description': 'Make 5 transactions this month',
            'mission_type': 'transaction_count',
            'objective': {'count': 5, 'period': 'month'},
            'reward_points': 200,
            'start_date': now,
            'end_date': now + timedelta(days=30)
        }
    ]
    
    missions = []
    for mission_data in missions_data:
        mission, created = Mission.objects.get_or_create(
            program=program,
            name=mission_data['name'],
            defaults={
                'description': mission_data['description'],
                'mission_type': mission_data['mission_type'],
                'objective': mission_data['objective'],
                'reward_points': mission_data['reward_points'],
                'start_date': mission_data['start_date'],
                'end_date': mission_data['end_date'],
                'is_active': True
            }
        )
        missions.append(mission)
        if created:
            print(f"  [OK] Created mission: {mission.name}")
        else:
            print(f"  [OK] Using existing mission: {mission.name}")
    
    # Create leaderboard
    leaderboard, created = Leaderboard.objects.get_or_create(
        program=program,
        name='Top Points Earners',
        defaults={
            'description': 'Monthly leaderboard for points earned',
            'ranking_criteria': 'points_earned',
            'period': 'monthly',
            'top_n': 100,
            'is_active': True
        }
    )
    
    if created:
        print(f"  [OK] Created leaderboard: {leaderboard.name}")
    else:
        print(f"  [OK] Using existing leaderboard: {leaderboard.name}")
    
    return badges, missions, leaderboard

def create_journey(program):
    """Create a customer journey"""
    print_section("CREATING CUSTOMER JOURNEY")
    
    try:
        journey, created = Journey.objects.get_or_create(
            program=program,
            name='New Customer Onboarding',
            defaults={
                'description': 'Journey for onboarding new customers',
                'is_active': True
            }
        )
        
        if created:
            print(f"  [OK] Created journey: {journey.name}")
            print(f"  [INFO] Journey created. Add nodes via frontend for full configuration.")
        else:
            print(f"  [OK] Using existing journey: {journey.name}")
        
        return journey
    except Exception as e:
        print(f"  [WARN] Could not create journey: {e}")
        return None

def get_sample_customers():
    """Get some real customers from Xiva to use in demo"""
    print_section("FETCHING SAMPLE CUSTOMERS FROM XIVA")
    
    try:
        client = get_xiva_client()
        customers = client.get_customer_list(limit=10)
        
        if customers and len(customers) > 0:
            print(f"  [OK] Retrieved {len(customers)} customers from Xiva")
            for i, customer in enumerate(customers[:5], 1):
                name = customer.get('firstName', '') + ' ' + customer.get('lastName', '')
                customer_id = customer.get('id', 'N/A')
                print(f"      {i}. {name} (ID: {customer_id[:8]}...)")
            return customers
        else:
            print(f"  [WARN] No customers found in Xiva")
            return []
    except Exception as e:
        print(f"  [WARN] Could not fetch customers from Xiva: {e}")
        return []

def create_sample_accounts(program, tiers, customers):
    """Create sample loyalty accounts for demo"""
    print_section("CREATING SAMPLE LOYALTY ACCOUNTS")
    
    if not customers:
        print("  [SKIP] No customers available to create accounts")
        return []
    
    accounts = []
    points_distribution = [0, 500, 1500, 3500, 8000, 12000]  # Various point levels
    
    for i, customer in enumerate(customers[:5]):  # Use first 5 customers
        customer_id = customer.get('id')
        if not customer_id:
            continue
        
        # Determine tier based on points
        points = points_distribution[i % len(points_distribution)]
        tier = None
        for t in sorted(tiers, key=lambda x: x.min_points, reverse=True):
            if points >= t.min_points:
                tier = t
                break
        
        account, created = LoyaltyAccount.objects.get_or_create(
            customer_id=customer_id,
            program=program,
            defaults={
                'tier': tier,
                'points_balance': points,
                'status': 'active'
            }
        )
        
        if not created:
            account.tier = tier
            account.points_balance = points
            account.save()
        
        accounts.append(account)
        name = customer.get('firstName', '') + ' ' + customer.get('lastName', '')
        tier_name = tier.name if tier else 'None'
        print(f"  [OK] Account for {name}: {points} points, {tier_name} tier")
    
    return accounts

def main():
    """Main demo creation function"""
    print("\n" + "="*80)
    print("  COMPREHENSIVE DEMO DATA CREATION")
    print("  Creating programs, segments, campaigns, rewards, and gamification")
    print("="*80)
    
    try:
        # 1. Create loyalty program
        program, tiers = create_loyalty_program()
        
        # 2. Create segments
        segments = create_segments(program)
        
        # 3. Create campaigns
        campaigns = create_campaigns(program, segments)
        
        # 4. Create rewards
        rewards = create_rewards(program)
        
        # 5. Create gamification
        badges, missions, leaderboard = create_gamification(program)
        
        # 6. Create journey
        journey = create_journey(program)
        
        # 7. Get sample customers
        customers = get_sample_customers()
        
        # 8. Create sample accounts
        accounts = create_sample_accounts(program, tiers, customers)
        
        # Summary
        print_section("DEMO CREATION SUMMARY")
        print(f"  [OK] Loyalty Program: {program.name}")
        print(f"  [OK] Tiers: {len(tiers)}")
        print(f"  [OK] Segments: {len(segments)}")
        print(f"  [OK] Campaigns: {len(campaigns)}")
        print(f"  [OK] Rewards: {len(rewards)}")
        print(f"  [OK] Badges: {len(badges)}")
        print(f"  [OK] Missions: {len(missions)}")
        print(f"  [OK] Leaderboard: {leaderboard.name if leaderboard else 'N/A'}")
        print(f"  [OK] Journey: {journey.name if journey else 'N/A'}")
        print(f"  [OK] Sample Accounts: {len(accounts)}")
        
        print("\n" + "="*80)
        print("  DEMO DATA CREATION COMPLETE!")
        print("="*80)
        print("\nYou can now:")
        print("  1. View the program in the frontend")
        print("  2. See segments with Xiva features")
        print("  3. View active campaigns")
        print("  4. Browse the rewards catalog")
        print("  5. Check gamification elements")
        print("  6. See customer accounts with points and tiers")
        print("\n")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to create demo data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

