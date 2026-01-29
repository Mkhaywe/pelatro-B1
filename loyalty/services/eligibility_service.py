"""
Enterprise-Grade Eligibility Service
Handles eligibility evaluation with caching, overrides, and rule optimization.
"""
import logging
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction

from loyalty.models import LoyaltyProgram, LoyaltyAccount, LoyaltyEligibilityRule, LoyaltyEligibilityOverride
from loyalty.utils import safe_json_logic
from loyalty.integration.feature_store import FeatureStore

logger = logging.getLogger(__name__)


class EligibilityEvaluationService:
    """Evaluate eligibility rules with optimization"""
    
    def __init__(self):
        self.feature_store = FeatureStore()
    
    def evaluate_eligibility_rules(
        self,
        customer_id: str,
        program: LoyaltyProgram,
        context: Optional[Dict] = None
    ) -> Tuple[bool, List[str], Dict]:
        """
        Evaluate all eligibility rules for a customer in a program.
        
        Returns:
            (is_eligible, errors, metadata) - Eligibility result, errors, and evaluation metadata
        """
        if context is None:
            context = {}
        
        # Get eligibility rules for program
        rules = LoyaltyEligibilityRule.objects.filter(
            program=program,
            is_active=True
        ).order_by('priority', 'id')
        
        if not rules.exists():
            # No rules = eligible by default
            return True, [], {'rules_evaluated': 0, 'default_eligible': True}
        
        errors = []
        metadata = {
            'rules_evaluated': 0,
            'rules_passed': 0,
            'rules_failed': 0,
            'evaluation_time_ms': 0
        }
        
        import time
        start_time = time.time()
        
        # Get customer features (cached)
        customer_features = self.feature_store.get_customer_features(customer_id)
        
        # Get account if exists
        try:
            account = LoyaltyAccount.objects.get(
                customer_id=customer_id,
                program=program
            )
            account_context = {
                'points_balance': account.points_balance,
                'tier': account.tier.name if account.tier else None,
                'status': account.status
            }
        except LoyaltyAccount.DoesNotExist:
            account_context = {}
        
        # Merge all context
        evaluation_context = {
            'customer_id': str(customer_id),
            'program': program.name,
            **customer_features,
            **account_context,
            **context
        }
        
        # Evaluate each rule
        for rule in rules:
            metadata['rules_evaluated'] += 1
            
            try:
                # Evaluate rule using JSONLogic
                rule_result = safe_json_logic(rule.rule, evaluation_context)
                
                if rule.rule_type == 'must_pass':
                    # Must pass rules - failure means ineligible
                    if not rule_result:
                        errors.append(f"Rule '{rule.name}' failed: {rule.description or 'No description'}")
                        metadata['rules_failed'] += 1
                        # Can short-circuit if must_pass rule fails
                        if rule.short_circuit:
                            break
                    else:
                        metadata['rules_passed'] += 1
                
                elif rule.rule_type == 'must_not_pass':
                    # Must not pass rules - passing means ineligible
                    if rule_result:
                        errors.append(f"Rule '{rule.name}' passed (should not pass): {rule.description or 'No description'}")
                        metadata['rules_failed'] += 1
                        if rule.short_circuit:
                            break
                    else:
                        metadata['rules_passed'] += 1
                
                elif rule.rule_type == 'bonus':
                    # Bonus rules - don't affect eligibility, just metadata
                    if rule_result:
                        metadata.setdefault('bonus_rules_passed', []).append(rule.name)
            
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id}: {e}")
                # On error, treat as failed for must_pass rules
                if rule.rule_type in ['must_pass', 'must_not_pass']:
                    errors.append(f"Rule '{rule.name}' evaluation error: {str(e)}")
                    metadata['rules_failed'] += 1
        
        elapsed_ms = (time.time() - start_time) * 1000
        metadata['evaluation_time_ms'] = round(elapsed_ms, 2)
        
        is_eligible = len(errors) == 0
        
        return is_eligible, errors, metadata


class EligibilityOverrideService:
    """Handle eligibility overrides"""
    
    def check_override(
        self,
        customer_id: str,
        program: LoyaltyProgram
    ) -> Optional[Dict]:
        """
        Check if there's an eligibility override for this customer.
        
        Returns:
            Override dict if exists, None otherwise
        """
        try:
            override = LoyaltyEligibilityOverride.objects.get(
                customer_id=customer_id,
                program=program,
                is_active=True
            )
            return {
                'is_eligible': override.is_eligible,
                'reason': override.reason,
                'expires_at': override.expires_at,
                'created_by': override.created_by
            }
        except LoyaltyEligibilityOverride.DoesNotExist:
            return None
    
    @transaction.atomic
    def create_override(
        self,
        customer_id: str,
        program: LoyaltyProgram,
        is_eligible: bool,
        reason: str,
        expires_at: Optional[timezone.datetime] = None,
        created_by: Optional[str] = None
    ) -> LoyaltyEligibilityOverride:
        """Create an eligibility override"""
        override = LoyaltyEligibilityOverride.objects.create(
            customer_id=customer_id,
            program=program,
            is_eligible=is_eligible,
            reason=reason,
            expires_at=expires_at,
            created_by=created_by or 'system',
            is_active=True
        )
        
        logger.info(
            f"Eligibility override created: customer={customer_id}, "
            f"program={program.id}, eligible={is_eligible}"
        )
        
        return override
    
    def expire_overrides(self):
        """Expire overrides that have passed their expiration date"""
        expired = LoyaltyEligibilityOverride.objects.filter(
            is_active=True,
            expires_at__lt=timezone.now()
        ).update(is_active=False)
        
        if expired > 0:
            logger.info(f"Expired {expired} eligibility overrides")


class EligibilityCacheService:
    """Cache eligibility evaluations for performance"""
    
    CACHE_PREFIX = 'eligibility'
    CACHE_TTL = 3600  # 1 hour
    
    def get_cached_eligibility(
        self,
        customer_id: str,
        program_id: int
    ) -> Optional[Dict]:
        """Get cached eligibility result"""
        cache_key = f"{self.CACHE_PREFIX}:{customer_id}:{program_id}"
        return cache.get(cache_key)
    
    def set_cached_eligibility(
        self,
        customer_id: str,
        program_id: int,
        result: Dict,
        ttl: Optional[int] = None
    ):
        """Cache eligibility result"""
        cache_key = f"{self.CACHE_PREFIX}:{customer_id}:{program_id}"
        cache.set(cache_key, result, ttl or self.CACHE_TTL)
    
    def invalidate_eligibility_cache(
        self,
        customer_id: Optional[str] = None,
        program_id: Optional[int] = None
    ):
        """Invalidate eligibility cache"""
        if customer_id and program_id:
            cache_key = f"{self.CACHE_PREFIX}:{customer_id}:{program_id}"
            cache.delete(cache_key)
        elif customer_id:
            # Invalidate all programs for this customer
            # This is a simplified version - in production, use cache tags or pattern matching
            logger.warning("Bulk cache invalidation by customer_id not fully implemented")
        elif program_id:
            # Invalidate all customers for this program
            logger.warning("Bulk cache invalidation by program_id not fully implemented")


class EligibilityService:
    """
    Main Eligibility Service - Orchestrates all eligibility operations.
    Enterprise-grade service with caching, overrides, and comprehensive evaluation.
    """
    
    def __init__(self):
        self.evaluation_service = EligibilityEvaluationService()
        self.override_service = EligibilityOverrideService()
        self.cache_service = EligibilityCacheService()
    
    def check_eligibility(
        self,
        customer_id: str,
        program: LoyaltyProgram,
        context: Optional[Dict] = None,
        use_cache: bool = True,
        use_override: bool = True
    ) -> Tuple[bool, List[str], Dict]:
        """
        Check customer eligibility for a program.
        
        Args:
            customer_id: Customer UUID
            program: LoyaltyProgram instance
            context: Additional context for evaluation
            use_cache: Whether to use cached results
            use_override: Whether to check for overrides
        
        Returns:
            (is_eligible, errors, metadata) - Eligibility result, errors, and metadata
        """
        # Check override first (overrides everything)
        if use_override:
            override = self.override_service.check_override(customer_id, program)
            if override:
                # Check if override is expired
                if override.get('expires_at') and override['expires_at'] < timezone.now():
                    # Override expired, continue with normal evaluation
                    pass
                else:
                    return (
                        override['is_eligible'],
                        [] if override['is_eligible'] else [override.get('reason', 'Eligibility override')],
                        {
                            'from_override': True,
                            'override_reason': override.get('reason'),
                            'override_created_by': override.get('created_by')
                        }
                    )
        
        # Check cache
        if use_cache:
            cached_result = self.cache_service.get_cached_eligibility(
                customer_id, program.id
            )
            if cached_result:
                return (
                    cached_result['is_eligible'],
                    cached_result.get('errors', []),
                    {**cached_result.get('metadata', {}), 'from_cache': True}
                )
        
        # Evaluate rules
        is_eligible, errors, metadata = self.evaluation_service.evaluate_eligibility_rules(
            customer_id, program, context
        )
        
        # Cache result
        if use_cache:
            self.cache_service.set_cached_eligibility(
                customer_id,
                program.id,
                {
                    'is_eligible': is_eligible,
                    'errors': errors,
                    'metadata': metadata
                }
            )
        
        return is_eligible, errors, metadata
    
    def create_override(
        self,
        customer_id: str,
        program: LoyaltyProgram,
        is_eligible: bool,
        reason: str,
        expires_at: Optional[timezone.datetime] = None,
        created_by: Optional[str] = None
    ) -> LoyaltyEligibilityOverride:
        """Create an eligibility override"""
        override = self.override_service.create_override(
            customer_id, program, is_eligible, reason, expires_at, created_by
        )
        
        # Invalidate cache
        self.cache_service.invalidate_eligibility_cache(customer_id, program.id)
        
        return override
    
    def expire_overrides(self):
        """Expire eligibility overrides"""
        self.override_service.expire_overrides()

