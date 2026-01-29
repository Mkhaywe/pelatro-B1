"""
Create Offer Catalog
Initializes the offer catalog with default offers for ML predictions
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
import django
django.setup()

from loyalty.models import Offer
from loyalty.services.offer_service import OfferSyncService

print("="*70)
print("CREATING OFFER CATALOG")
print("="*70)
print()

# Default offers for NBO model (0-7)
default_offers = [
    {
        'offer_id': 0,
        'name': 'Double Points Weekend',
        'description': 'Earn double points on all purchases this weekend',
        'category': 'points',
        'lifecycle_stage': 'retention',
        'target_value_segment': 'all',
    },
    {
        'offer_id': 1,
        'name': 'Free Shipping',
        'description': 'Free shipping on your next order',
        'category': 'shipping',
        'lifecycle_stage': 'growth',
        'target_value_segment': 'medium_value',
    },
    {
        'offer_id': 2,
        'name': '10% Discount',
        'description': '10% off your next purchase',
        'category': 'discount',
        'lifecycle_stage': 'retention',
        'target_value_segment': 'all',
    },
    {
        'offer_id': 3,
        'name': 'Exclusive VIP Access',
        'description': 'Access to exclusive VIP events and offers',
        'category': 'access',
        'lifecycle_stage': 'growth',
        'target_value_segment': 'high_value',
    },
    {
        'offer_id': 4,
        'name': 'Birthday Bonus',
        'description': 'Special birthday bonus points',
        'category': 'special',
        'lifecycle_stage': 'retention',
        'target_value_segment': 'all',
    },
    {
        'offer_id': 5,
        'name': 'Referral Reward',
        'description': 'Reward for referring friends',
        'category': 'referral',
        'lifecycle_stage': 'growth',
        'target_value_segment': 'all',
    },
    {
        'offer_id': 6,
        'name': 'Flash Sale',
        'description': 'Limited time flash sale offer',
        'category': 'sale',
        'lifecycle_stage': 'win_back',
        'target_value_segment': 'low_value',
    },
    {
        'offer_id': 7,
        'name': 'Loyalty Tier Upgrade',
        'description': 'Upgrade to next loyalty tier',
        'category': 'tier',
        'lifecycle_stage': 'growth',
        'target_value_segment': 'high_value',
    },
]

print("Creating default offers...")
print()

created_count = 0
updated_count = 0

for offer_data in default_offers:
    offer, created = Offer.objects.update_or_create(
        offer_id=offer_data['offer_id'],
        defaults={
            'name': offer_data['name'],
            'description': offer_data['description'],
            'category': offer_data['category'],
            'lifecycle_stage': offer_data['lifecycle_stage'],
            'target_value_segment': offer_data['target_value_segment'],
            'is_active': True,
            'external_system': 'manual',
        }
    )
    
    if created:
        print(f"✅ Created: Offer #{offer.offer_id} - {offer.name}")
        created_count += 1
    else:
        print(f"🔄 Updated: Offer #{offer.offer_id} - {offer.name}")
        updated_count += 1

print()
print("="*70)
print(f"✅ COMPLETE!")
print("="*70)
print(f"Created: {created_count}")
print(f"Updated: {updated_count}")
print()
print("Next steps:")
print("1. Offers are now linked to ML predictions")
print("2. NBO predictions will return offer details")
print("3. You can sync offers from external systems using OfferSyncService")
print("4. Update offers via Admin UI or API")
print("="*70)

