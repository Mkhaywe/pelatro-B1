"""
Customer Lifecycle Management (CLM) Service
Tracks and manages customers through lifecycle stages
"""
from typing import Dict, List, Optional
from django.utils import timezone
from django.db.models import Q
from loyalty.models import CustomerLifecycleStage
from loyalty.ml.inference import MLInferenceService
from loyalty.integration.feature_store import FeatureStore
import logging

logger = logging.getLogger(__name__)


class CLMService:
    """Customer Lifecycle Management Service"""
    
    def __init__(self):
        self.ml_service = MLInferenceService()
    
    def get_customer_stage(self, customer_id: str) -> Optional[str]:
        """
        Get current lifecycle stage for customer
        
        Returns:
            Current stage name or None
        """
        latest_stage = CustomerLifecycleStage.objects.filter(
            customer_id=customer_id
        ).order_by('-entered_at').first()
        
        if latest_stage and not latest_stage.exited_at:
            return latest_stage.stage
        
        return None
    
    def calculate_customer_stage(self, customer_id: str) -> str:
        """
        Calculate customer lifecycle stage using ML predictions and business rules
        
        Returns:
            Stage name
        """
        # Get customer features
        features = FeatureStore.get_customer_features(customer_id)
        
        # Get ML predictions
        churn_result = self.ml_service.predict_churn(customer_id)
        churn_prob = churn_result.get('churn_probability', 0) if 'error' not in churn_result else 0
        
        # Get customer metrics
        days_since_last = features.get('days_since_last_transaction', 999)
        transaction_count = features.get('transaction_count', 0)
        total_revenue = features.get('total_revenue', 0)
        account_age_days = features.get('account_age_days', 0)
        
        # Business rules for stage determination
        if account_age_days < 30:
            if transaction_count == 0:
                return 'acquisition'
            else:
                return 'onboarding'
        elif churn_prob >= 0.7:
            return 'churn_risk'
        elif days_since_last > 90:
            return 'win_back'
        elif total_revenue > 1000 and transaction_count > 10:
            return 'growth'
        elif transaction_count > 0:
            return 'retention'
        else:
            return 'acquisition'
    
    def transition_customer_stage(self, customer_id: str, new_stage: str, reason: str = '') -> CustomerLifecycleStage:
        """
        Transition customer to new lifecycle stage
        
        Args:
            customer_id: Customer ID
            new_stage: New stage name
            reason: Reason for transition
        
        Returns:
            New CustomerLifecycleStage instance
        """
        # Exit current stage
        current_stage = CustomerLifecycleStage.objects.filter(
            customer_id=customer_id,
            exited_at__isnull=True
        ).first()
        
        if current_stage:
            current_stage.exited_at = timezone.now()
            if current_stage.entered_at:
                duration = (timezone.now() - current_stage.entered_at).days
                current_stage.duration_days = duration
            current_stage.save()
        
        # Enter new stage
        new_lifecycle_stage = CustomerLifecycleStage.objects.create(
            customer_id=customer_id,
            stage=new_stage,
            transition_reason=reason
        )
        
        return new_lifecycle_stage
    
    def auto_update_customer_stage(self, customer_id: str) -> Optional[CustomerLifecycleStage]:
        """
        Automatically update customer stage based on current metrics
        
        Returns:
            New CustomerLifecycleStage if transitioned, None if no change
        """
        current_stage = self.get_customer_stage(customer_id)
        calculated_stage = self.calculate_customer_stage(customer_id)
        
        if current_stage != calculated_stage:
            return self.transition_customer_stage(
                customer_id,
                calculated_stage,
                reason=f'Auto-updated from {current_stage} to {calculated_stage}'
            )
        
        return None
    
    def get_stage_statistics(self, stage: Optional[str] = None) -> Dict:
        """
        Get statistics for lifecycle stages
        
        Args:
            stage: Optional stage name to filter
        
        Returns:
            Dict with stage statistics
        """
        queryset = CustomerLifecycleStage.objects.filter(exited_at__isnull=True)
        
        if stage:
            queryset = queryset.filter(stage=stage)
        
        stats = {}
        for lifecycle_stage in queryset.values('stage').distinct():
            stage_name = lifecycle_stage['stage']
            count = queryset.filter(stage=stage_name).count()
            stats[stage_name] = count
        
        return stats
    
    def recommend_actions(self, customer_id: str) -> List[Dict]:
        """
        Recommend actions based on customer lifecycle stage
        
        Returns:
            List of recommended actions (offers, campaigns, etc.)
        """
        stage = self.get_customer_stage(customer_id) or self.calculate_customer_stage(customer_id)
        
        recommendations = []
        
        if stage == 'churn_risk':
            recommendations.append({
                'type': 'offer',
                'priority': 'high',
                'action': 'Send retention offer',
                'description': 'Customer is at high risk of churning'
            })
            recommendations.append({
                'type': 'campaign',
                'priority': 'high',
                'action': 'Trigger win-back campaign',
                'description': 'Immediate intervention needed'
            })
        elif stage == 'win_back':
            recommendations.append({
                'type': 'offer',
                'priority': 'medium',
                'action': 'Send re-engagement offer',
                'description': 'Customer has been inactive'
            })
        elif stage == 'growth':
            recommendations.append({
                'type': 'offer',
                'priority': 'low',
                'action': 'Send upsell offer',
                'description': 'Customer is growing, opportunity for upsell'
            })
        elif stage == 'onboarding':
            recommendations.append({
                'type': 'campaign',
                'priority': 'medium',
                'action': 'Send welcome series',
                'description': 'New customer onboarding'
            })
        
        return recommendations

