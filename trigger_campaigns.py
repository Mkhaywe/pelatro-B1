"""
Trigger Campaigns and Create Executions

This script:
1. Finds all active campaigns
2. Evaluates triggers
3. Finds target customers from segments
4. Creates CampaignExecution records
5. Simulates campaign delivery

Run this after creating campaigns to generate execution data.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')

import django
django.setup()

from django.utils import timezone
from loyalty.models_khaywe import Campaign, CampaignExecution, Segment, SegmentMember
from loyalty.engines.campaign_engine import CampaignExecutionEngine
from loyalty.models import LoyaltyAccount
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("="*70)
print("TRIGGER CAMPAIGNS AND CREATE EXECUTIONS")
print("="*70)
print()


def trigger_all_campaigns():
    """Trigger all active campaigns and create executions"""
    print("[INFO] Finding active campaigns...")
    
    active_campaigns = Campaign.objects.filter(status='active')
    
    if not active_campaigns.exists():
        print("[WARNING] No active campaigns found!")
        print("   Create campaigns first via Campaign Builder")
        return
    
    print(f"[OK] Found {active_campaigns.count()} active campaigns")
    print()
    
    engine = CampaignExecutionEngine()
    total_executions = 0
    
    for campaign in active_campaigns:
        print(f"[INFO] Processing campaign: {campaign.name}")
        
        # Get target customers from segment
        target_customers = []
        
        if campaign.segment:
            # Get segment members
            members = SegmentMember.objects.filter(
                segment=campaign.segment,
                is_active=True
            )
            target_customers = [str(m.customer_id) for m in members]
            print(f"   Segment: {campaign.segment.name} ({len(target_customers)} members)")
        else:
            # No segment - get all loyalty account customers
            accounts = LoyaltyAccount.objects.filter(
                program=campaign.program,
                status='active'
            )
            target_customers = [str(acc.customer_id) for acc in accounts]
            print(f"   No segment - using all program customers ({len(target_customers)} customers)")
        
        if not target_customers:
            print(f"   [WARNING] No target customers found for campaign {campaign.name}")
            continue
        
        # Limit to first 50 customers for demo
        target_customers = target_customers[:50]
        
        # Create executions for each customer
        executions_created = 0
        
        for customer_id in target_customers:
            try:
                # Check if execution already exists (avoid duplicates)
                existing = CampaignExecution.objects.filter(
                    campaign=campaign,
                    customer_id=customer_id,
                    triggered_at__gte=timezone.now() - timedelta(days=1)
                ).exists()
                
                if existing:
                    continue
                
                # Create execution
                execution = CampaignExecution.objects.create(
                    campaign=campaign,
                    customer_id=customer_id,
                    channel=campaign.channels[0] if campaign.channels else 'email',
                    triggered_at=timezone.now(),
                    delivered_at=timezone.now(),
                    metadata={
                        'campaign_name': campaign.name,
                        'campaign_version': campaign.version,
                        'triggered_by': 'manual_script'
                    }
                )
                
                # Simulate some interactions (for demo)
                import random
                if random.random() < 0.6:  # 60% open rate
                    execution.opened_at = timezone.now() + timedelta(minutes=random.randint(5, 120))
                    execution.save()
                    
                    if random.random() < 0.4:  # 40% click rate (of opens)
                        execution.clicked_at = execution.opened_at + timedelta(minutes=random.randint(1, 30))
                        execution.save()
                        
                        if random.random() < 0.3:  # 30% conversion rate (of clicks)
                            execution.converted_at = execution.clicked_at + timedelta(hours=random.randint(1, 24))
                            execution.save()
                
                executions_created += 1
                total_executions += 1
                
            except Exception as e:
                logger.error(f"Error creating execution for customer {customer_id}: {e}")
                continue
        
        print(f"   [OK] Created {executions_created} executions for {campaign.name}")
        print()
    
    print("="*70)
    print(f"[OK] CAMPAIGN TRIGGERING COMPLETE!")
    print("="*70)
    print(f"\n[INFO] Summary:")
    print(f"   - Campaigns processed: {active_campaigns.count()}")
    print(f"   - Total executions created: {total_executions}")
    print(f"\n[INFO] View executions in:")
    print(f"   - Campaigns → Select campaign → View Metrics")
    print(f"   - Analytics → Campaign Performance")
    print("="*70)


if __name__ == '__main__':
    trigger_all_campaigns()

