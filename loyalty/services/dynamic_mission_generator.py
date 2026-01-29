"""
Dynamic Mission Generator Service
Generates personalized missions from templates based on behavior scores and segments.
"""
import logging
from typing import Dict, List, Optional
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from decimal import Decimal

from loyalty.models_khaywe import (
    Mission, MissionTemplate, MissionProgress,
    CustomerBehaviorScore, Segment, SegmentMember
)
from loyalty.services.behavior_scoring import BehaviorScoringService
from loyalty.services.gamification_service import GamificationService
from loyalty.models import LoyaltyProgram
from loyalty.utils import safe_json_logic

logger = logging.getLogger(__name__)


class DynamicMissionGeneratorService:
    """Service for dynamically generating missions from templates"""
    
    def __init__(self):
        self.scoring_service = BehaviorScoringService()
        self.gamification_service = GamificationService()
    
    def generate_missions_for_customer(
        self,
        customer_id: str,
        max_missions: int = 5,
        force_regenerate: bool = False
    ) -> List[Mission]:
        """
        Generate personalized missions for a customer based on their scores.
        
        Args:
            customer_id: Customer UUID
            max_missions: Maximum number of missions to generate
            force_regenerate: Force regeneration even if missions exist
        
        Returns:
            List of generated Mission instances
        """
        # Get customer scores
        scores = self.scoring_service.get_scores(customer_id)
        if not scores:
            logger.warning(f"Could not get scores for customer {customer_id}")
            return []
        
        # Get customer features for context
        from loyalty.integration.feature_store import FeatureStore
        features = FeatureStore.get_customer_features(customer_id)
        
        # Get active templates
        templates = MissionTemplate.objects.filter(is_active=True).order_by('-priority')
        
        # Get existing active missions for this customer
        existing_missions = Mission.objects.filter(
            generated_for=customer_id,
            is_active=True,
            end_date__gte=timezone.now()
        )
        
        if not force_regenerate and existing_missions.count() >= max_missions:
            logger.debug(f"Customer {customer_id} already has {existing_missions.count()} active missions")
            return list(existing_missions)
        
        # Evaluate templates and generate missions
        generated_missions = []
        
        for template in templates:
            if len(generated_missions) >= max_missions:
                break
            
            # Check if customer is eligible
            if not self._is_eligible(template, customer_id, scores, features):
                continue
            
            # Check generation rules
            if not self._should_generate(template, scores, features):
                continue
            
            # Check if similar mission already exists
            if self._similar_mission_exists(template, customer_id, existing_missions):
                continue
            
            # Generate mission from template
            mission = self._generate_mission_from_template(
                template, customer_id, scores, features
            )
            
            if mission:
                generated_missions.append(mission)
        
        logger.info(f"Generated {len(generated_missions)} missions for customer {customer_id}")
        return generated_missions
    
    def generate_missions_for_segment(
        self,
        segment_id: int,
        max_missions_per_customer: int = 5
    ) -> Dict[str, List[Mission]]:
        """
        Generate missions for all customers in a segment.
        
        Returns:
            Dict mapping customer_id to list of generated missions
        """
        try:
            segment = Segment.objects.get(pk=segment_id)
            members = SegmentMember.objects.filter(segment=segment).values_list('customer_id', flat=True)
            
            results = {}
            for customer_id in members:
                try:
                    missions = self.generate_missions_for_customer(
                        str(customer_id),
                        max_missions=max_missions_per_customer
                    )
                    results[str(customer_id)] = missions
                except Exception as e:
                    logger.error(f"Error generating missions for customer {customer_id}: {e}")
            
            return results
        except Segment.DoesNotExist:
            logger.error(f"Segment {segment_id} not found")
            return {}
    
    def _is_eligible(
        self,
        template: MissionTemplate,
        customer_id: str,
        scores: CustomerBehaviorScore,
        features: Dict
    ) -> bool:
        """Check if customer is eligible for this template"""
        if not template.eligibility_rules:
            return True
        
        # Evaluate JSONLogic rules
        try:
            from loyalty.utils import safe_json_logic
            context = {
                'customer_id': customer_id,
                'engagement_score': scores.engagement_score,
                'revenue_score': scores.revenue_score,
                'loyalty_score': scores.loyalty_score,
                'risk_score': scores.risk_score,
                'digital_score': scores.digital_score,
                **features
            }
            return safe_json_logic(template.eligibility_rules, context)
        except Exception as e:
            logger.error(f"Error evaluating eligibility rules: {e}")
            return False
    
    def _should_generate(
        self,
        template: MissionTemplate,
        scores: CustomerBehaviorScore,
        features: Dict
    ) -> bool:
        """Check if mission should be generated based on generation rules"""
        if not template.generation_rules:
            return True
        
        rules = template.generation_rules
        
        # Check score thresholds
        if 'min_engagement_score' in rules:
            if scores.engagement_score < rules['min_engagement_score']:
                return False
        
        if 'max_engagement_score' in rules:
            if scores.engagement_score > rules['max_engagement_score']:
                return False
        
        if 'min_revenue_score' in rules:
            if scores.revenue_score < rules['min_revenue_score']:
                return False
        
        if 'max_revenue_score' in rules:
            if scores.revenue_score > rules['max_revenue_score']:
                return False
        
        if 'min_risk_score' in rules:
            if scores.risk_score < rules['min_risk_score']:
                return False
        
        if 'max_risk_score' in rules:
            if scores.risk_score > rules['max_risk_score']:
                return False
        
        # Check feature thresholds
        if 'min_total_revenue' in rules:
            total_revenue = float(features.get('total_revenue', 0) or 0)
            if total_revenue < rules['min_total_revenue']:
                return False
        
        if 'max_days_since_last' in rules:
            days_since = features.get('days_since_last_transaction', 999) or 999
            if days_since > rules['max_days_since_last']:
                return False
        
        return True
    
    def _similar_mission_exists(
        self,
        template: MissionTemplate,
        customer_id: str,
        existing_missions: List[Mission]
    ) -> bool:
        """Check if a similar mission already exists"""
        for mission in existing_missions:
            if mission.template == template:
                return True
            if mission.category == template.category and mission.metric == template.metric:
                return True
        return False
    
    def _generate_mission_from_template(
        self,
        template: MissionTemplate,
        customer_id: str,
        scores: CustomerBehaviorScore,
        features: Dict
    ) -> Optional[Mission]:
        """Generate a mission instance from a template"""
        try:
            # Get default program (or first available)
            program = LoyaltyProgram.objects.filter(is_active=True).first()
            if not program:
                logger.error("No active loyalty program found")
                return None
            
            # Calculate threshold based on customer's current state
            threshold = self._calculate_threshold(template, customer_id, scores, features)
            
            # Calculate mission period
            start_date, end_date = self._calculate_period(template)
            
            # Generate mission name
            name = self._generate_mission_name(template, threshold)
            
            # Generate description
            description = self._generate_mission_description(template, threshold, scores)
            
            # Create mission
            mission = Mission.objects.create(
                name=name,
                description=description,
                program=program,
                template=template,
                is_dynamic=True,
                generated_for=customer_id,
                mission_type=self._map_category_to_mission_type(template.category),
                category=template.category,
                metric=template.metric,
                target_value=threshold,
                objective={
                    'metric': template.metric,
                    'threshold': float(threshold),
                    'period': template.period,
                },
                reward_config=template.reward_config,
                reward_points=template.reward_config.get('points', 0),
                start_date=start_date,
                end_date=end_date,
                is_active=True,
                eligibility_rules=template.eligibility_rules,
            )
            
            logger.info(f"Generated mission '{name}' for customer {customer_id} from template '{template.template_name}'")
            return mission
            
        except Exception as e:
            logger.error(f"Error generating mission from template {template.id}: {e}", exc_info=True)
            return None
    
    def _calculate_threshold(
        self,
        template: MissionTemplate,
        customer_id: str,
        scores: CustomerBehaviorScore,
        features: Dict
    ) -> Decimal:
        """Calculate personalized threshold for mission"""
        threshold_config = template.threshold
        
        # If threshold is a fixed value
        if 'value' in threshold_config:
            base_value = Decimal(str(threshold_config['value']))
        else:
            # Use default based on metric
            base_value = self._get_default_threshold(template.metric)
        
        # Apply personalization based on scores
        if 'personalize' in threshold_config and threshold_config['personalize']:
            # Adjust based on customer's current level
            if template.category == 'engagement':
                # Lower threshold for low engagement customers
                multiplier = 0.7 if scores.engagement_score < 30 else 1.0
            elif template.category == 'revenue':
                # Adjust based on revenue score
                multiplier = 0.8 if scores.revenue_score < 40 else 1.2
            elif template.category == 'correction':
                # Lower threshold for correction missions
                multiplier = 0.6
            else:
                multiplier = 1.0
            
            base_value = base_value * Decimal(str(multiplier))
        
        return base_value
    
    def _get_default_threshold(self, metric: str) -> Decimal:
        """Get default threshold for a metric"""
        defaults = {
            'data_usage': Decimal('1000'),  # MB
            'recharge_amount': Decimal('20'),  # $
            'call_count': Decimal('10'),
            'app_login': Decimal('5'),
            'active_days': Decimal('7'),
            'streak_days': Decimal('3'),
        }
        return defaults.get(metric, Decimal('10'))
    
    def _calculate_period(self, template: MissionTemplate) -> tuple[timezone.datetime, timezone.datetime]:
        """Calculate start and end dates for mission"""
        now = timezone.now()
        
        if template.period == 'daily':
            start_date = now
            end_date = now + timedelta(days=1)
        elif template.period == 'weekly':
            start_date = now
            end_date = now + timedelta(days=7)
        elif template.period == 'monthly':
            start_date = now
            end_date = now + timedelta(days=30)
        else:
            # Custom period
            start_date = now
            end_date = now + timedelta(days=7)  # Default to 7 days
        
        return start_date, end_date
    
    def _generate_mission_name(self, template: MissionTemplate, threshold: Decimal) -> str:
        """Generate mission name from template and threshold"""
        metric_names = {
            'data_usage': 'Use {threshold}MB Data',
            'recharge_amount': 'Recharge ${threshold}',
            'call_count': 'Make {threshold} Calls',
            'app_login': 'Login {threshold} Times',
            'active_days': 'Stay Active for {threshold} Days',
            'streak_days': 'Maintain {threshold} Day Streak',
        }
        
        name_template = metric_names.get(template.metric, '{threshold} {metric}')
        return name_template.format(threshold=threshold, metric=template.metric)
    
    def _generate_mission_description(
        self,
        template: MissionTemplate,
        threshold: Decimal,
        scores: CustomerBehaviorScore
    ) -> str:
        """Generate mission description"""
        if template.description:
            return template.description
        
        category_descriptions = {
            'onboarding': f"Complete this mission to get started and earn rewards!",
            'engagement': f"Increase your activity to unlock better rewards.",
            'revenue': f"Boost your spending to access premium benefits.",
            'loyalty': f"Stay active to maintain your loyalty status.",
            'correction': f"Get back on track and earn bonus rewards!",
        }
        
        return category_descriptions.get(template.category, "Complete this mission to earn rewards!")
    
    def _map_category_to_mission_type(self, category: str) -> str:
        """Map template category to mission type"""
        mapping = {
            'onboarding': 'engagement',
            'engagement': 'engagement',
            'revenue': 'revenue',
            'loyalty': 'loyalty',
            'correction': 'correction',
        }
        return mapping.get(category, 'custom')

