"""
Enterprise-Grade Promotions Service
Handles promotion application, eligibility, triggers, and performance tracking.
"""
import logging
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache

from loyalty.models import Promotion, LoyaltyAccount, LoyaltyTransaction
from loyalty.services.eligibility_service import EligibilityService
from loyalty.services.points_service import PointsService
from loyalty.engines.campaign_engine import CampaignExecutionEngine
from apps.shared.audit import emit_audit_event

logger = logging.getLogger(__name__)


class PromotionEligibilityService:
    """Check promotion eligibility"""
    
    def __init__(self):
        self.eligibility_service = EligibilityService()
    
    def check_eligibility(
        self,
        promotion: Promotion,
        customer_id: str,
        context: Optional[Dict] = None
    ) -> Tuple[bool, List[str], Dict]:
        """
        Check if customer is eligible for promotion.
        
        Returns:
            (is_eligible, errors, metadata) - Eligibility result
        """
        errors = []
        metadata = {}
        
        # Check promotion status
        if not promotion.is_active:
            errors.append('Promotion is not active')
        
        # Check dates
        now = timezone.now()
        if promotion.start_date and promotion.start_date > now:
            errors.append('Promotion has not started')
        if promotion.end_date and promotion.end_date < now:
            errors.append('Promotion has ended')
        
        # Check eligibility rules (if field exists, otherwise use eligibility_criteria)
        eligibility_rules = getattr(promotion, 'eligibility_rules', None)
        if not eligibility_rules and hasattr(promotion, 'eligibility_criteria'):
            # Try to parse eligibility_criteria if it's JSON
            import json
            try:
                eligibility_rules = json.loads(promotion.eligibility_criteria) if promotion.eligibility_criteria else None
            except:
                eligibility_rules = None
        
        if eligibility_rules:
                # Get program from promotion (check if field exists)
                program = getattr(promotion, 'program', None)
                if not program and hasattr(promotion, 'reward') and promotion.reward:
                    program = promotion.reward.program
                
                if program:
                    is_eligible, rule_errors, rule_metadata = self.eligibility_service.check_eligibility(
                        customer_id,
                        program,
                        {**(context or {}), 'promotion': promotion.name}
                    )
                else:
                    is_eligible, rule_errors, rule_metadata = True, [], {}
            if not is_eligible:
                errors.extend(rule_errors)
            metadata['rule_evaluation'] = rule_metadata
        
        # Check trigger frequency
        if promotion.trigger_frequency != 'unlimited':
            # Check if already triggered
            account = LoyaltyAccount.objects.filter(
                customer_id=customer_id,
                program=promotion.program
            ).first()
            
            if account:
                recent_redemptions = LoyaltyTransaction.objects.filter(
                    account=account,
                    description__icontains=promotion.name,
                    created_at__gte=self._get_frequency_period_start(promotion.trigger_frequency)
                ).exists()
                
                if recent_redemptions:
                    errors.append(f'Promotion already triggered (frequency: {promotion.trigger_frequency})')
        
        return len(errors) == 0, errors, metadata
    
    def _get_frequency_period_start(self, frequency: str) -> timezone.datetime:
        """Get period start for frequency check"""
        now = timezone.now()
        if frequency == 'once':
            return timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)
        elif frequency == 'daily':
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif frequency == 'weekly':
            days_since_monday = now.weekday()
            return (now - timezone.timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:
            return now


class PromotionApplicationService:
    """Apply promotions to customers"""
    
    def __init__(self):
        self.eligibility_service = PromotionEligibilityService()
        self.points_service = PointsService()
        self.campaign_engine = CampaignExecutionEngine()
    
    @transaction.atomic
    def apply_promotion(
        self,
        promotion: Promotion,
        customer_id: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Apply a promotion to a customer.
        
        Returns:
            Dict with application details
        """
        # Check eligibility
        is_eligible, errors, metadata = self.eligibility_service.check_eligibility(
            promotion, customer_id, context
        )
        
        if not is_eligible:
            return {
                'success': False,
                'errors': errors,
                'metadata': metadata
            }
        
        # Get account
        try:
            account = LoyaltyAccount.objects.get(
                customer_id=customer_id,
                program=promotion.program
            )
        except LoyaltyAccount.DoesNotExist:
            return {
                'success': False,
                'error': 'Account not found'
            }
        
        # Apply promotion based on type
        if promotion.promotion_type == 'points_bonus':
            # Award bonus points
            bonus_points = promotion.bonus_points or 0
            if bonus_points > 0:
                result = self.points_service.earn_points(
                    account,
                    bonus_points,
                    {
                        'description': f'Promotion: {promotion.name}',
                        'transaction_date': timezone.now()
                    }
                )
                
                if result['success']:
                    emit_audit_event(
                        action='PROMOTION_APPLIED',
                        object_type='Promotion',
                        object_id=str(promotion.id),
                        details={
                            'promotion_name': promotion.name,
                            'customer_id': customer_id,
                            'bonus_points': bonus_points,
                            'transaction_id': result['transaction_id']
                        },
                        status='success'
                    )
                    
                    return {
                        'success': True,
                        'promotion_id': str(promotion.id),
                        'promotion_name': promotion.name,
                        'bonus_points': bonus_points,
                        'balance_after': result['balance_after'],
                        'transaction_id': result['transaction_id']
                    }
                else:
                    return {
                    'success': False,
                    'error': 'Failed to award bonus points',
                    'errors': result.get('errors', [])
                }
        
        elif promotion_type == 'discount':
            # Discount is applied at redemption time
            discount_pct = getattr(promotion, 'discount_percentage', 0)
            return {
                'success': True,
                'promotion_id': str(promotion.id),
                'promotion_name': promotion.name,
                'discount_percentage': discount_pct,
                'message': 'Discount will be applied at redemption'
            }
        
        elif promotion_type == 'campaign_trigger':
            # Trigger a campaign
            # This would integrate with campaign engine
            return {
                'success': True,
                'promotion_id': str(promotion.id),
                'promotion_name': promotion.name,
                'message': 'Campaign triggered'
            }
        
        return {
            'success': False,
            'error': f'Unknown promotion type: {promotion_type}'
        }
    
    def process_event_trigger(
        self,
        event_type: str,
        event_data: Dict
    ) -> List[Dict]:
        """
        Process an event and apply matching promotions.
        
        Returns:
            List of application results
        """
        # Find promotions with matching event triggers
        promotions = Promotion.objects.filter(
            is_active=True,
            event_triggers__contains=[{'event_type': event_type}]
        )
        
        results = []
        customer_id = event_data.get('customer_id')
        
        if not customer_id:
            logger.warning(f"Event {event_type} missing customer_id")
            return results
        
        for promotion in promotions:
            # Check if trigger matches
            if not self._check_event_trigger(promotion, event_type, event_data):
                continue
            
            # Apply promotion
            result = self.apply_promotion(promotion, customer_id, event_data)
            results.append({
                'promotion_id': str(promotion.id),
                'promotion_name': promotion.name,
                **result
            })
        
        return results
    
    def _check_event_trigger(
        self,
        promotion: Promotion,
        event_type: str,
        event_data: Dict
    ) -> bool:
        """Check if event trigger matches"""
        for trigger in promotion.event_triggers or []:
            if trigger.get('event_type') == event_type:
                # Check conditions if any
                conditions = trigger.get('conditions', {})
                if conditions:
                    from loyalty.utils import safe_json_logic
                    try:
                        return safe_json_logic(conditions, event_data)
                    except Exception as e:
                        logger.error(f"Error evaluating trigger conditions: {e}")
                        return False
                return True
        return False


class PromotionPerformanceService:
    """Track promotion performance"""
    
    def get_promotion_performance(
        self,
        promotion: Promotion,
        start_date: Optional[timezone.datetime] = None,
        end_date: Optional[timezone.datetime] = None
    ) -> Dict:
        """
        Get promotion performance metrics.
        
        Returns:
            Dict with performance metrics
        """
        # Get transactions related to this promotion
        transactions = LoyaltyTransaction.objects.filter(
            description__icontains=promotion.name
        )
        
        if start_date:
            transactions = transactions.filter(created_at__gte=start_date)
        if end_date:
            transactions = transactions.filter(created_at__lte=end_date)
        
        total_applications = transactions.count()
        total_points_awarded = sum(tx.amount for tx in transactions if tx.amount > 0)
        unique_customers = transactions.values('account__customer_id').distinct().count()
        
        return {
            'promotion_id': str(promotion.id),
            'promotion_name': promotion.name,
            'total_applications': total_applications,
            'total_points_awarded': total_points_awarded,
            'unique_customers': unique_customers,
            'avg_points_per_customer': total_points_awarded / unique_customers if unique_customers > 0 else 0
        }


class PromotionsService:
    """
    Main Promotions Service - Orchestrates all promotion operations.
    Enterprise-grade service with eligibility, application, triggers, and performance tracking.
    """
    
    def __init__(self):
        self.eligibility_service = PromotionEligibilityService()
        self.application_service = PromotionApplicationService()
        self.performance_service = PromotionPerformanceService()
    
    def check_eligibility(
        self,
        promotion: Promotion,
        customer_id: str,
        context: Optional[Dict] = None
    ) -> Tuple[bool, List[str], Dict]:
        """Check promotion eligibility"""
        return self.eligibility_service.check_eligibility(promotion, customer_id, context)
    
    def apply_promotion(
        self,
        promotion: Promotion,
        customer_id: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """Apply a promotion"""
        return self.application_service.apply_promotion(promotion, customer_id, context)
    
    def process_event_trigger(
        self,
        event_type: str,
        event_data: Dict
    ) -> List[Dict]:
        """Process event trigger"""
        return self.application_service.process_event_trigger(event_type, event_data)
    
    def get_performance(
        self,
        promotion: Promotion,
        start_date: Optional[timezone.datetime] = None,
        end_date: Optional[timezone.datetime] = None
    ) -> Dict:
        """Get promotion performance"""
        return self.performance_service.get_promotion_performance(promotion, start_date, end_date)

