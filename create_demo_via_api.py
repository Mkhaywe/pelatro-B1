#!/usr/bin/env python
"""
Create demo data via API endpoints (works around database issues)
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api"

def get_auth_token():
    """Get authentication token"""
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login/",
            json={'username': 'admin', 'password': 'admin'},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get('token')
        else:
            print(f"[WARN] Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[WARN] Could not login: {e}")
        return None

def create_program(token):
    """Create loyalty program"""
    headers = {'Authorization': f'Token {token}'}
    data = {
        'name': 'Pelatro Premium Rewards',
        'description': 'Main loyalty program with points, tiers, and rewards',
        'start_date': (datetime.now() - timedelta(days=365)).isoformat(),
        'end_date': (datetime.now() + timedelta(days=365)).isoformat(),
        'is_active': True
    }
    
    response = requests.post(
        f"{BASE_URL}/loyalty/v1/loyaltyPrograms/",
        json=data,
        headers=headers,
        timeout=10
    )
    
    if response.status_code in [200, 201]:
        program = response.json()
        print(f"  [OK] Created program: {program.get('name')} (ID: {program.get('id')})")
        return program
    else:
        print(f"  [ERROR] Failed to create program: {response.status_code} - {response.text}")
        return None

def create_segments(token, program_id):
    """Create segments"""
    headers = {'Authorization': f'Token {token}'}
    
    segments_data = [
        {
            'name': 'High Value Customers',
            'description': 'Customers with high revenue and active status',
            'program': program_id,
            'rules': [{
                "and": [
                    {">": [{"var": "total_revenue"}, 500]},
                    {"==": [{"var": "customer_status"}, "active"]},
                    {">": [{"var": "active_products_count"}, 0]}
                ]
            }],
            'is_dynamic': True,
            'is_active': True
        },
        {
            'name': 'Data Power Users',
            'description': 'Customers who use significant data',
            'program': program_id,
            'rules': [{
                "and": [
                    {">": [{"var": "data_usage_mb"}, 1000]},
                    {"==": [{"var": "has_data_service"}, True]},
                    {"==": [{"var": "customer_status"}, "active"]}
                ]
            }],
            'is_dynamic': True,
            'is_active': True
        },
        {
            'name': 'At-Risk Customers',
            'description': 'Customers with low usage or high credit utilization',
            'program': program_id,
            'rules': [{
                "or": [
                    {"<": [{"var": "data_usage_mb"}, 100]},
                    {">": [{"var": "credit_utilization"}, 0.8]},
                    {"<": [{"var": "current_month_spend"}, 0]}
                ]
            }],
            'is_dynamic': True,
            'is_active': True
        }
    ]
    
    segments = []
    for seg_data in segments_data:
        response = requests.post(
            f"{BASE_URL}/loyalty/v1/segments/",
            json=seg_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            segment = response.json()
            segments.append(segment)
            print(f"  [OK] Created segment: {segment.get('name')} (ID: {segment.get('id')})")
        else:
            print(f"  [ERROR] Failed to create segment {seg_data['name']}: {response.status_code} - {response.text[:200]}")
    
    return segments

def create_campaigns(token, program_id, segments):
    """Create campaigns"""
    headers = {'Authorization': f'Token {token}'}
    now = datetime.now()
    
    campaigns_data = [
        {
            'name': 'Welcome Bonus for New Customers',
            'description': 'Special welcome offer for new customers',
            'program': program_id,
            'segment': segments[2].get('id') if len(segments) > 2 else None,
            'status': 'active',
            'start_date': (now - timedelta(days=7)).isoformat(),
            'end_date': (now + timedelta(days=30)).isoformat(),
            'channels': ['email', 'sms'],
            'reward_type': 'points',
            'reward_value': 500
        },
        {
            'name': 'Data Boost Campaign',
            'description': 'Extra data bonus for power users',
            'program': program_id,
            'segment': segments[1].get('id') if len(segments) > 1 else None,
            'status': 'active',
            'start_date': (now - timedelta(days=3)).isoformat(),
            'end_date': (now + timedelta(days=60)).isoformat(),
            'channels': ['email', 'push'],
            'reward_type': 'points',
            'reward_value': 1000
        },
        {
            'name': 'VIP Rewards Program',
            'description': 'Exclusive rewards for high-value customers',
            'program': program_id,
            'segment': segments[0].get('id') if len(segments) > 0 else None,
            'status': 'active',
            'start_date': (now - timedelta(days=14)).isoformat(),
            'end_date': (now + timedelta(days=90)).isoformat(),
            'channels': ['email'],
            'reward_type': 'points',
            'reward_value': 2000
        }
    ]
    
    campaigns = []
    for camp_data in campaigns_data:
        response = requests.post(
            f"{BASE_URL}/loyalty/v1/campaigns/",
            json=camp_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            campaign = response.json()
            campaigns.append(campaign)
            print(f"  [OK] Created campaign: {campaign.get('name')} (ID: {campaign.get('id')})")
        else:
            print(f"  [ERROR] Failed to create campaign {camp_data['name']}: {response.status_code} - {response.text[:200]}")
    
    return campaigns

def create_rewards(token, program_id):
    """Create rewards"""
    headers = {'Authorization': f'Token {token}'}
    
    rewards_data = [
        {'name': 'Free 1GB Data', 'description': 'Get 1GB of free data', 'points_required': 500},
        {'name': 'Free 5GB Data', 'description': 'Get 5GB of free data', 'points_required': 2000},
        {'name': '10% Discount Voucher', 'description': '10% off your next bill', 'points_required': 1000},
        {'name': '20% Discount Voucher', 'description': '20% off your next bill', 'points_required': 2500},
        {'name': 'Free Month Service', 'description': 'One month free service', 'points_required': 5000},
    ]
    
    rewards = []
    for reward_data in rewards_data:
        reward_data['program'] = program_id
        reward_data['is_active'] = True
        
        response = requests.post(
            f"{BASE_URL}/loyalty/v1/loyaltyRewards/",
            json=reward_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            reward = response.json()
            rewards.append(reward)
            print(f"  [OK] Created reward: {reward.get('name')} ({reward.get('points_required')} points)")
        else:
            print(f"  [ERROR] Failed to create reward {reward_data['name']}: {response.status_code} - {response.text[:200]}")
    
    return rewards

def main():
    print("\n" + "="*80)
    print("  CREATING DEMO DATA VIA API")
    print("="*80)
    
    # Get auth token
    print("\n[1] Authenticating...")
    token = get_auth_token()
    if not token:
        print("[ERROR] Could not authenticate. Make sure Django server is running and credentials are correct.")
        return
    
    print("  [OK] Authenticated")
    
    # Create program
    print("\n[2] Creating loyalty program...")
    program = create_program(token)
    if not program:
        print("[ERROR] Could not create program")
        return
    
    program_id = program.get('id')
    
    # Create segments
    print("\n[3] Creating segments...")
    segments = create_segments(token, program_id)
    print(f"  Created {len(segments)} segments")
    
    # Create campaigns
    print("\n[4] Creating campaigns...")
    campaigns = create_campaigns(token, program_id, segments)
    print(f"  Created {len(campaigns)} campaigns")
    
    # Create rewards
    print("\n[5] Creating rewards...")
    rewards = create_rewards(token, program_id)
    print(f"  Created {len(rewards)} rewards")
    
    # Summary
    print("\n" + "="*80)
    print("  DEMO DATA CREATION COMPLETE!")
    print("="*80)
    print(f"\n  ✅ Program: {program.get('name')}")
    print(f"  ✅ Segments: {len(segments)}")
    print(f"  ✅ Campaigns: {len(campaigns)}")
    print(f"  ✅ Rewards: {len(rewards)}")
    print("\nYou can now view these in the frontend!")
    print()

if __name__ == '__main__':
    main()

