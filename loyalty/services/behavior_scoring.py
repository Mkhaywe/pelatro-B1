"""
Behavior Scoring Service
Calculates customer behavior scores (Engagement, Revenue, Loyalty, Risk, Digital)
from events and features.
"""
import logging
from typing import Dict, Optional, List, Tuple
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from decimal import Decimal

from loyalty.models_khaywe import CustomerEvent, CustomerBehaviorScore
from loyalty.integration.feature_store import FeatureStore
from loyalty.ml.inference import MLInferenceService

logger = logging.getLogger(__name__)


class BehaviorScoringService:
    """Service for calculating customer behavior scores"""
    
    def __init__(self):
        self.ml_service = MLInferenceService()
        self.scoring_version = "1.0"
    
    def calculate_all_scores(
        self,
        customer_id: str,
        force_recalculate: bool = False
    ) -> CustomerBehaviorScore:
        """
        Calculate all behavior scores for a customer.
        
        Args:
            customer_id: Customer UUID
            force_recalculate: Force recalculation even if recent scores exist
        
        Returns:
            CustomerBehaviorScore instance
        """
        # Get or create score record
        score_obj, created = CustomerBehaviorScore.objects.get_or_create(
            customer_id=customer_id,
            defaults={
                'engagement_score': 0,
                'revenue_score': 0,
                'loyalty_score': 0,
                'risk_score': 0,
                'digital_score': 0,
            }
        )
        
        # Check if recalculation is needed
        if not force_recalculate and not created:
            age = timezone.now() - score_obj.updated_at
            if age < timedelta(hours=1):  # Cache for 1 hour
                logger.debug(f"Using cached scores for customer {customer_id}")
                return score_obj
        
        # Get customer features
        features = FeatureStore.get_customer_features(customer_id)
        
        # Get recent events (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_events = CustomerEvent.objects.filter(
            customer_id=customer_id,
            timestamp__gte=thirty_days_ago,
            processed=True
        )
        
        # Calculate each score
        engagement_score, engagement_breakdown = self._calculate_engagement_score(
            customer_id, features, recent_events
        )
        
        revenue_score, revenue_breakdown = self._calculate_revenue_score(
            customer_id, features, recent_events
        )
        
        loyalty_score, loyalty_breakdown = self._calculate_loyalty_score(
            customer_id, features, recent_events
        )
        
        risk_score, risk_breakdown = self._calculate_risk_score(
            customer_id, features
        )
        
        digital_score, digital_breakdown = self._calculate_digital_score(
            customer_id, features, recent_events
        )
        
        # Update score record
        score_obj.engagement_score = engagement_score
        score_obj.revenue_score = revenue_score
        score_obj.loyalty_score = loyalty_score
        score_obj.risk_score = risk_score
        score_obj.digital_score = digital_score
        score_obj.score_breakdown = {
            'engagement': engagement_breakdown,
            'revenue': revenue_breakdown,
            'loyalty': loyalty_breakdown,
            'risk': risk_breakdown,
            'digital': digital_breakdown,
        }
        score_obj.calculation_version = self.scoring_version
        score_obj.save()
        
        logger.info(f"Calculated scores for customer {customer_id}: "
                   f"E:{engagement_score:.1f} R:{revenue_score:.1f} L:{loyalty_score:.1f} "
                   f"Risk:{risk_score:.1f} D:{digital_score:.1f}")
        
        return score_obj
    
    def _calculate_engagement_score(
        self,
        customer_id: str,
        features: Dict,
        events: List[CustomerEvent]
    ) -> Tuple[float, Dict]:
        """Calculate engagement score (0-100)"""
        score = 0.0
        breakdown = {}
        
        # Call activity (max 30 points)
        call_events = events.filter(event_type__in=['CALL_OUTGOING', 'CALL_INCOMING'])
        call_count = call_events.count()
        call_score = min(call_count / 50 * 30, 30)  # 50 calls = 30 points
        score += call_score
        breakdown['calls'] = {'count': call_count, 'score': call_score}
        
        # Data usage (max 30 points)
        data_events = events.filter(event_type='DATA_USAGE')
        total_data_mb = sum(
            float(e.value or 0) for e in data_events if e.value
        )
        data_score = min(total_data_mb / 5000 * 30, 30)  # 5GB = 30 points
        score += data_score
        breakdown['data_usage'] = {'mb': total_data_mb, 'score': data_score}
        
        # App activity (max 20 points)
        app_events = events.filter(event_type__in=['APP_LOGIN', 'APP_FEATURE_USE'])
        app_count = app_events.count()
        app_score = min(app_count / 20 * 20, 20)  # 20 app events = 20 points
        score += app_score
        breakdown['app_activity'] = {'count': app_count, 'score': app_score}
        
        # SMS activity (max 10 points)
        sms_events = events.filter(event_type__in=['SMS_SENT', 'SMS_RECEIVED'])
        sms_count = sms_events.count()
        sms_score = min(sms_count / 100 * 10, 10)  # 100 SMS = 10 points
        score += sms_score
        breakdown['sms_activity'] = {'count': sms_count, 'score': sms_score}
        
        # Recency bonus (max 10 points)
        if events.exists():
            last_event = events.order_by('-timestamp').first()
            days_since = (timezone.now() - last_event.timestamp).days
            recency_score = max(0, 10 - days_since * 2)  # -2 points per day
            score += recency_score
            breakdown['recency'] = {'days_since': days_since, 'score': recency_score}
        
        # Ensure score is between 0 and 100
        score = max(0, min(100, score))
        
        return score, breakdown
    
    def _calculate_revenue_score(
        self,
        customer_id: str,
        features: Dict,
        events: List[CustomerEvent]
    ) -> Tuple[float, Dict]:
        """Calculate revenue score (0-100)"""
        score = 0.0
        breakdown = {}
        
        # Total revenue (max 40 points)
        total_revenue = float(features.get('total_revenue', 0) or 0)
        revenue_score = min(total_revenue / 1000 * 40, 40)  # $1000 = 40 points
        score += revenue_score
        breakdown['total_revenue'] = {'value': total_revenue, 'score': revenue_score}
        
        # Recent recharges (max 30 points)
        recharge_events = events.filter(event_type='RECHARGE')
        recent_recharge = sum(
            float(e.value or 0) for e in recharge_events if e.value
        )
        recharge_score = min(recent_recharge / 200 * 30, 30)  # $200 = 30 points
        score += recharge_score
        breakdown['recent_recharge'] = {'value': recent_recharge, 'score': recharge_score}
        
        # ARPU (max 20 points)
        arpu = float(features.get('arpu', 0) or 0)
        arpu_score = min(arpu / 50 * 20, 20)  # $50 ARPU = 20 points
        score += arpu_score
        breakdown['arpu'] = {'value': arpu, 'score': arpu_score}
        
        # Lifetime value (max 10 points)
        ltv = float(features.get('lifetime_value', 0) or 0)
        ltv_score = min(ltv / 2000 * 10, 10)  # $2000 LTV = 10 points
        score += ltv_score
        breakdown['lifetime_value'] = {'value': ltv, 'score': ltv_score}
        
        # Ensure score is between 0 and 100
        score = max(0, min(100, score))
        
        return score, breakdown
    
    def _calculate_loyalty_score(
        self,
        customer_id: str,
        features: Dict,
        events: List[CustomerEvent]
    ) -> Tuple[float, Dict]:
        """Calculate loyalty score (0-100)"""
        score = 0.0
        breakdown = {}
        
        # Customer age (max 30 points)
        customer_age_days = features.get('customer_age_days', 0) or 0
        age_score = min(customer_age_days / 365 * 30, 30)  # 1 year = 30 points
        score += age_score
        breakdown['customer_age'] = {'days': customer_age_days, 'score': age_score}
        
        # Transaction count (max 25 points)
        transaction_count = features.get('transaction_count', 0) or 0
        tx_score = min(transaction_count / 50 * 25, 25)  # 50 transactions = 25 points
        score += tx_score
        breakdown['transaction_count'] = {'count': transaction_count, 'score': tx_score}
        
        # Consistency (max 25 points) - active days in last 30 days
        active_days = len(set(
            e.timestamp.date() for e in events
        ))
        consistency_score = min(active_days / 30 * 25, 25)  # 30 days = 25 points
        score += consistency_score
        breakdown['consistency'] = {'active_days': active_days, 'score': consistency_score}
        
        # On-time payments (max 20 points)
        payment_events = events.filter(event_type__in=['PAYMENT', 'BILL_PAID'])
        payment_count = payment_events.count()
        payment_score = min(payment_count / 10 * 20, 20)  # 10 payments = 20 points
        score += payment_score
        breakdown['payments'] = {'count': payment_count, 'score': payment_score}
        
        # Ensure score is between 0 and 100
        score = max(0, min(100, score))
        
        return score, breakdown
    
    def _calculate_risk_score(
        self,
        customer_id: str,
        features: Dict
    ) -> Tuple[float, Dict]:
        """Calculate risk score (0-100) - higher = more risk"""
        score = 0.0
        breakdown = {}
        
        # Get ML churn prediction
        try:
            churn_prediction = self.ml_service.predict_churn(customer_id)
            if churn_prediction and not churn_prediction.get('error'):
                churn_prob = float(churn_prediction.get('churn_probability', 0) or 0)
                ml_risk_score = churn_prob * 100  # Convert to 0-100
                score += ml_risk_score * 0.5  # ML contributes 50%
                breakdown['ml_churn_probability'] = {'value': churn_prob, 'score': ml_risk_score}
        except Exception as e:
            logger.warning(f"Could not get ML churn prediction: {e}")
        
        # Days since last transaction (max 30 points)
        days_since_last = features.get('days_since_last_transaction', 999) or 999
        inactivity_score = min(days_since_last / 90 * 30, 30)  # 90 days = 30 points
        score += inactivity_score
        breakdown['inactivity'] = {'days': days_since_last, 'score': inactivity_score}
        
        # Revenue decline (max 20 points)
        total_revenue = float(features.get('total_revenue', 0) or 0)
        if total_revenue > 0:
            # Low revenue = higher risk
            revenue_risk = max(0, 20 - (total_revenue / 100 * 2))  # $100 = 0 risk
            score += revenue_risk
            breakdown['revenue_risk'] = {'revenue': total_revenue, 'score': revenue_risk}
        
        # Ensure score is between 0 and 100
        score = max(0, min(100, score))
        
        return score, breakdown
    
    def _calculate_digital_score(
        self,
        customer_id: str,
        features: Dict,
        events: List[CustomerEvent]
    ) -> Tuple[float, Dict]:
        """Calculate digital score (0-100) - app/web usage"""
        score = 0.0
        breakdown = {}
        
        # App logins (max 40 points)
        app_logins = events.filter(event_type='APP_LOGIN').count()
        login_score = min(app_logins / 30 * 40, 40)  # 30 logins = 40 points
        score += login_score
        breakdown['app_logins'] = {'count': app_logins, 'score': login_score}
        
        # Feature usage (max 30 points)
        feature_uses = events.filter(event_type='APP_FEATURE_USE').count()
        feature_score = min(feature_uses / 20 * 30, 30)  # 20 uses = 30 points
        score += feature_score
        breakdown['feature_usage'] = {'count': feature_uses, 'score': feature_score}
        
        # Content views (max 20 points)
        content_views = events.filter(event_type='CONTENT_VIEW').count()
        content_score = min(content_views / 15 * 20, 20)  # 15 views = 20 points
        score += content_score
        breakdown['content_views'] = {'count': content_views, 'score': content_score}
        
        # Web logins (max 10 points)
        web_logins = events.filter(event_type='WEB_LOGIN').count()
        web_score = min(web_logins / 10 * 10, 10)  # 10 logins = 10 points
        score += web_score
        breakdown['web_logins'] = {'count': web_logins, 'score': web_score}
        
        # Ensure score is between 0 and 100
        score = max(0, min(100, score))
        
        return score, breakdown
    
    def get_scores(self, customer_id: str) -> Optional[CustomerBehaviorScore]:
        """Get current scores for a customer"""
        try:
            return CustomerBehaviorScore.objects.get(customer_id=customer_id)
        except CustomerBehaviorScore.DoesNotExist:
            # Calculate if doesn't exist
            return self.calculate_all_scores(customer_id)
    
    def batch_calculate_scores(self, customer_ids: List[str]) -> Dict[str, CustomerBehaviorScore]:
        """Calculate scores for multiple customers"""
        results = {}
        for customer_id in customer_ids:
            try:
                score = self.calculate_all_scores(customer_id)
                results[customer_id] = score
            except Exception as e:
                logger.error(f"Error calculating scores for {customer_id}: {e}")
        return results

