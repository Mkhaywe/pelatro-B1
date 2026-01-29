"""
Create default mission templates and badges for gamification system.
Run this script after migrations to populate initial data.
"""
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
django.setup()

from loyalty.models_khaywe import MissionTemplate, Badge
from loyalty.models import LoyaltyProgram
import logging

logger = logging.getLogger(__name__)


def create_default_mission_templates():
    """Create default mission templates (25-30 templates)"""
    
    # Get default program
    program = LoyaltyProgram.objects.filter(is_active=True).first()
    if not program:
        logger.warning("No active loyalty program found. Creating templates without program association.")
    
    templates_data = [
        # ========== ONBOARDING (5 templates) ==========
        {
            'template_name': 'First Call Mission',
            'category': 'onboarding',
            'description': 'Make your first call to activate your account',
            'metric': 'call_count',
            'threshold': {'value': 1, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 100, 'badge_type': 'activated'},
            'generation_rules': {'max_engagement_score': 20},
            'badge_type': 'activated',
            'badge_level': 'bronze',
            'priority': 10,
        },
        {
            'template_name': 'First Data Usage',
            'category': 'onboarding',
            'description': 'Use data for the first time',
            'metric': 'data_usage',
            'threshold': {'value': 100, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 150},
            'generation_rules': {'max_engagement_score': 20},
            'priority': 9,
        },
        {
            'template_name': 'App Installation',
            'category': 'onboarding',
            'description': 'Install and login to the mobile app',
            'metric': 'app_login',
            'threshold': {'value': 1, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 200, 'badge_type': 'activated'},
            'generation_rules': {'max_digital_score': 30},
            'badge_type': 'activated',
            'badge_level': 'bronze',
            'priority': 8,
        },
        {
            'template_name': 'Profile Completion',
            'category': 'onboarding',
            'description': 'Complete your profile information',
            'metric': 'custom',
            'threshold': {'value': 1, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 50},
            'priority': 7,
        },
        {
            'template_name': 'First Recharge',
            'category': 'onboarding',
            'description': 'Make your first recharge',
            'metric': 'recharge_amount',
            'threshold': {'value': 10, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 250},
            'generation_rules': {'max_revenue_score': 20},
            'priority': 6,
        },
        
        # ========== ENGAGEMENT (8 templates) ==========
        {
            'template_name': 'Daily Usage Streak',
            'category': 'engagement',
            'description': 'Use services daily for a streak',
            'metric': 'streak_days',
            'threshold': {'value': 3, 'operator': '>=', 'personalize': True},
            'period': 'weekly',
            'reward_config': {'points': 100},
            'generation_rules': {'min_engagement_score': 20, 'max_engagement_score': 70},
            'badge_type': 'power_user',
            'badge_level': 'bronze',
            'priority': 9,
        },
        {
            'template_name': 'Weekly Activity Goal',
            'category': 'engagement',
            'description': 'Stay active throughout the week',
            'metric': 'active_days',
            'threshold': {'value': 5, 'operator': '>=', 'personalize': True},
            'period': 'weekly',
            'reward_config': {'points': 150},
            'generation_rules': {'min_engagement_score': 30},
            'priority': 8,
        },
        {
            'template_name': 'Data Usage Goal',
            'category': 'engagement',
            'description': 'Use a certain amount of data',
            'metric': 'data_usage',
            'threshold': {'value': 2000, 'operator': '>=', 'personalize': True},
            'period': 'weekly',
            'reward_config': {'points': 200},
            'generation_rules': {'min_engagement_score': 25},
            'priority': 7,
        },
        {
            'template_name': 'Call Frequency',
            'category': 'engagement',
            'description': 'Make a certain number of calls',
            'metric': 'call_count',
            'threshold': {'value': 20, 'operator': '>=', 'personalize': True},
            'period': 'weekly',
            'reward_config': {'points': 120},
            'generation_rules': {'min_engagement_score': 20},
            'priority': 6,
        },
        {
            'template_name': 'App Feature Adoption',
            'category': 'engagement',
            'description': 'Use a new app feature',
            'metric': 'feature_use',
            'threshold': {'value': 3, 'operator': '>='},
            'period': 'weekly',
            'reward_config': {'points': 100, 'badge_type': 'app_champion'},
            'generation_rules': {'min_digital_score': 30, 'max_digital_score': 80},
            'badge_type': 'app_champion',
            'badge_level': 'silver',
            'priority': 5,
        },
        {
            'template_name': 'Content Consumption',
            'category': 'engagement',
            'description': 'View content in the app',
            'metric': 'content_view',
            'threshold': {'value': 10, 'operator': '>='},
            'period': 'weekly',
            'reward_config': {'points': 80},
            'generation_rules': {'min_digital_score': 25},
            'priority': 4,
        },
        {
            'template_name': 'Social Sharing',
            'category': 'engagement',
            'description': 'Share content or refer friends',
            'metric': 'custom',
            'threshold': {'value': 1, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 300, 'badge_type': 'referrer'},
            'badge_type': 'referrer',
            'badge_level': 'gold',
            'priority': 3,
        },
        {
            'template_name': 'Multi-Channel Usage',
            'category': 'engagement',
            'description': 'Use multiple channels (app, web, USSD)',
            'metric': 'custom',
            'threshold': {'value': 2, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 150},
            'generation_rules': {'min_digital_score': 40},
            'priority': 2,
        },
        
        # ========== REVENUE (6 templates) ==========
        {
            'template_name': 'Recharge Threshold',
            'category': 'revenue',
            'description': 'Recharge a certain amount',
            'metric': 'recharge_amount',
            'threshold': {'value': 50, 'operator': '>=', 'personalize': True},
            'period': 'monthly',
            'reward_config': {'points': 500, 'badge_type': 'big_spender'},
            'generation_rules': {'min_revenue_score': 20, 'max_revenue_score': 80},
            'badge_type': 'big_spender',
            'badge_level': 'bronze',
            'priority': 9,
        },
        {
            'template_name': 'Bundle Purchase',
            'category': 'revenue',
            'description': 'Purchase a data or voice bundle',
            'metric': 'bundle_purchase',
            'threshold': {'value': 1, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 300},
            'generation_rules': {'min_revenue_score': 15},
            'priority': 8,
        },
        {
            'template_name': 'Premium Upgrade',
            'category': 'revenue',
            'description': 'Upgrade to a premium plan',
            'metric': 'custom',
            'threshold': {'value': 1, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 1000, 'badge_type': 'premium'},
            'generation_rules': {'min_revenue_score': 60},
            'badge_type': 'premium',
            'badge_level': 'gold',
            'priority': 7,
        },
        {
            'template_name': 'Roaming Usage',
            'category': 'revenue',
            'description': 'Use services while roaming',
            'metric': 'data_usage',
            'threshold': {'value': 500, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 400},
            'priority': 6,
        },
        {
            'template_name': 'High Value Purchase',
            'category': 'revenue',
            'description': 'Make a high-value purchase',
            'metric': 'recharge_amount',
            'threshold': {'value': 100, 'operator': '>=', 'personalize': True},
            'period': 'monthly',
            'reward_config': {'points': 800, 'badge_type': 'big_spender'},
            'generation_rules': {'min_revenue_score': 50},
            'badge_type': 'big_spender',
            'badge_level': 'silver',
            'priority': 5,
        },
        {
            'template_name': 'Monthly ARPU Goal',
            'category': 'revenue',
            'description': 'Achieve a monthly ARPU target',
            'metric': 'arpu',
            'threshold': {'value': 30, 'operator': '>=', 'personalize': True},
            'period': 'monthly',
            'reward_config': {'points': 600},
            'generation_rules': {'min_revenue_score': 40},
            'priority': 4,
        },
        
        # ========== LOYALTY (5 templates) ==========
        {
            'template_name': '30 Days Active',
            'category': 'loyalty',
            'description': 'Stay active for 30 consecutive days',
            'metric': 'active_days',
            'threshold': {'value': 30, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 1000, 'badge_type': '30_days_active'},
            'badge_type': '30_days_active',
            'badge_level': 'silver',
            'priority': 9,
        },
        {
            'template_name': '90 Days Loyal',
            'category': 'loyalty',
            'description': 'Remain a loyal customer for 90 days',
            'metric': 'active_days',
            'threshold': {'value': 90, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 2000, 'badge_type': '90_days_loyal'},
            'badge_type': '90_days_loyal',
            'badge_level': 'gold',
            'priority': 8,
        },
        {
            'template_name': 'On-Time Payment',
            'category': 'loyalty',
            'description': 'Pay your bills on time',
            'metric': 'on_time_payment',
            'threshold': {'value': 3, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 500},
            'generation_rules': {'min_loyalty_score': 40},
            'priority': 7,
        },
        {
            'template_name': 'No Inactivity Period',
            'category': 'loyalty',
            'description': 'Stay active without long breaks',
            'metric': 'no_inactivity',
            'threshold': {'value': 60, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 800},
            'generation_rules': {'min_loyalty_score': 50},
            'priority': 6,
        },
        {
            'template_name': 'Anniversary Mission',
            'category': 'loyalty',
            'description': 'Celebrate your account anniversary',
            'metric': 'custom',
            'threshold': {'value': 365, 'operator': '>='},
            'period': 'yearly',
            'reward_config': {'points': 5000, 'badge_type': '90_days_loyal'},
            'badge_type': '90_days_loyal',
            'badge_level': 'platinum',
            'priority': 5,
        },
        
        # ========== BEHAVIORAL CORRECTION (5 templates) ==========
        {
            'template_name': 'Low Usage Recovery',
            'category': 'correction',
            'description': 'Get back to using services',
            'metric': 'data_usage',
            'threshold': {'value': 500, 'operator': '>=', 'personalize': True},
            'period': 'weekly',
            'reward_config': {'points': 200, 'offer_id': 'recovery_offer'},
            'generation_rules': {'min_engagement_score': 0, 'max_engagement_score': 30, 'min_risk_score': 50},
            'badge_type': 'comeback_hero',
            'badge_level': 'bronze',
            'priority': 10,
        },
        {
            'template_name': 'Churn Risk Intervention',
            'category': 'correction',
            'description': 'Stay active to prevent churn',
            'metric': 'active_days',
            'threshold': {'value': 7, 'operator': '>=', 'personalize': True},
            'period': 'weekly',
            'reward_config': {'points': 300, 'offer_id': 'retention_offer'},
            'generation_rules': {'min_risk_score': 70},
            'badge_type': 'comeback_hero',
            'badge_level': 'silver',
            'priority': 9,
        },
        {
            'template_name': 'QoE Compensation',
            'category': 'correction',
            'description': 'Compensation for service quality issues',
            'metric': 'custom',
            'threshold': {'value': 1, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 500, 'offer_id': 'compensation_offer'},
            'priority': 8,
        },
        {
            'template_name': 'Reactivation Mission',
            'category': 'correction',
            'description': 'Reactivate your account',
            'metric': 'custom',
            'threshold': {'value': 1, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 400, 'offer_id': 'reactivation_offer'},
            'generation_rules': {'min_risk_score': 80},
            'badge_type': 'comeback_hero',
            'badge_level': 'gold',
            'priority': 7,
        },
        {
            'template_name': 'Payment Recovery',
            'category': 'correction',
            'description': 'Clear outstanding payments',
            'metric': 'payment',
            'threshold': {'value': 1, 'operator': '>='},
            'period': 'monthly',
            'reward_config': {'points': 250},
            'generation_rules': {'min_risk_score': 60},
            'priority': 6,
        },
    ]
    
    print(f"Creating {len(templates_data)} mission templates...")
    created_count = 0
    updated_count = 0
    
    for template_data in templates_data:
        try:
            template, created = MissionTemplate.objects.update_or_create(
                template_name=template_data['template_name'],
                category=template_data['category'],
                defaults={
                    'description': template_data.get('description', ''),
                    'metric': template_data['metric'],
                    'threshold': template_data['threshold'],
                    'period': template_data['period'],
                    'reward_config': template_data.get('reward_config', {}),
                    'generation_rules': template_data.get('generation_rules', {}),
                    'eligibility_rules': template_data.get('eligibility_rules', {}),
                    'badge_type': template_data.get('badge_type', ''),
                    'badge_level': template_data.get('badge_level', ''),
                    'priority': template_data.get('priority', 0),
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                print(f"  ✓ Created: {template.template_name}")
            else:
                updated_count += 1
                print(f"  ↻ Updated: {template.template_name}")
        except Exception as e:
            logger.error(f"Error creating template {template_data.get('template_name')}: {e}")
            print(f"  ✗ Error: {template_data.get('template_name')} - {e}")
    
    print(f"\nMission templates: {created_count} created, {updated_count} updated")


def create_default_badges():
    """Create default badges (12 types × 4 levels = 48 badges)"""
    
    # Get default program
    program = LoyaltyProgram.objects.filter(is_active=True).first()
    
    badge_types = [
        # Lifecycle
        ('activated', 'Activated', 'Account activation badge'),
        ('30_days_active', '30 Days Active', 'Active for 30 days'),
        ('90_days_loyal', '90 Days Loyal', 'Loyal customer for 90 days'),
        
        # Engagement
        ('power_user', 'Power User', 'High engagement user'),
        ('app_champion', 'App Champion', 'Active app user'),
        
        # Revenue
        ('big_spender', 'Big Spender', 'High spending customer'),
        ('premium', 'Premium', 'Premium tier customer'),
        
        # Digital
        ('self_care_pro', 'Self-Care Pro', 'Active self-service user'),
        ('auto_renew', 'Auto-Renew', 'Auto-renewal enabled'),
        
        # Social
        ('referrer', 'Referrer', 'Referred other customers'),
        
        # Risk
        ('comeback_hero', 'Comeback Hero', 'Returned after inactivity'),
    ]
    
    levels = [
        ('bronze', 1, 0, 30),
        ('silver', 2, 31, 60),
        ('gold', 3, 61, 85),
        ('platinum', 4, 86, 100),
    ]
    
    print(f"Creating {len(badge_types) * len(levels)} badges...")
    created_count = 0
    updated_count = 0
    
    for badge_type, badge_name, description in badge_types:
        for level, level_name, unlock_order, min_score in levels:
            try:
                full_name = f"{badge_name} ({level_name.title()})"
                badge, created = Badge.objects.update_or_create(
                    badge_type=badge_type,
                    level=level,
                    defaults={
                        'name': full_name,
                        'description': f"{description} - {level_name.title()} level",
                        'program': program,
                        'requirements': {
                            'min_score': min_score,
                            'badge_type': badge_type,
                        },
                        'auto_award_rules': {
                            'min_score': min_score,
                        },
                        'rarity': 'common' if level == 'bronze' else ('rare' if level == 'silver' else ('epic' if level == 'gold' else 'legendary')),
                        'unlock_order': unlock_order,
                        'is_active': True,
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                logger.error(f"Error creating badge {badge_type} {level}: {e}")
                print(f"  ✗ Error: {badge_type} {level} - {e}")
    
    print(f"\nBadges: {created_count} created, {updated_count} updated")


if __name__ == '__main__':
    print("=" * 60)
    print("CREATING DEFAULT GAMIFICATION DATA")
    print("=" * 60)
    
    create_default_mission_templates()
    print()
    create_default_badges()
    
    print("\n" + "=" * 60)
    print("COMPLETE!")
    print("=" * 60)

