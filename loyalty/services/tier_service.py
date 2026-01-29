"""
Enterprise-Grade Tier Service
Handles tier calculation, upgrades, downgrades, and benefits.
"""
import logging
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache

from loyalty.models import LoyaltyAccount, LoyaltyTier, LoyaltyProgram, LoyaltyTransaction
from apps.shared.audit import emit_audit_event

logger = logging.getLogger(__name__)


class TierCalculationService:
    """Calculate customer tier based on points and rules"""
    
    def calculate_tier(
        self,
        account: LoyaltyAccount,
        points_balance: Optional[int] = None
    ) -> Tuple[Optional[LoyaltyTier], Dict]:
        """
        Calculate appropriate tier for account based on points balance.
        
        Returns:
            (tier, metadata) - Calculated tier and calculation metadata
        """
        if points_balance is None:
            points_balance = account.points_balance
        
        # Get all tiers for program, ordered by min_points descending
        tiers = LoyaltyTier.objects.filter(
            program=account.program,
            min_points__lte=points_balance
        ).order_by('-min_points', '-priority')
        
        if not tiers.exists():
            return None, {'reason': 'No tier matches current points balance'}
        
        # Get highest tier that matches
        calculated_tier = tiers.first()
        
        metadata = {
            'points_balance': points_balance,
            'calculated_tier': calculated_tier.name if calculated_tier else None,
            'tier_min_points': calculated_tier.min_points if calculated_tier else None,
            'tiers_considered': tiers.count()
        }
        
        return calculated_tier, metadata


class TierUpgradeService:
    """Handle tier upgrades"""
    
    def __init__(self):
        self.calculation_service = TierCalculationService()
    
    def check_upgrade(
        self,
        account: LoyaltyAccount
    ) -> Tuple[bool, Optional[LoyaltyTier], Dict]:
        """
        Check if account is eligible for tier upgrade.
        
        Returns:
            (can_upgrade, new_tier, metadata) - Upgrade eligibility and new tier
        """
        # Calculate what tier should be
        calculated_tier, calc_metadata = self.calculation_service.calculate_tier(account)
        
        if not calculated_tier:
            return False, None, {**calc_metadata, 'reason': 'No tier calculated'}
        
        # Check if upgrade needed
        current_tier = account.tier
        if current_tier is None:
            # No current tier = upgrade needed
            return True, calculated_tier, {**calc_metadata, 'reason': 'No current tier'}
        
        # Compare tiers by priority (higher priority = better tier)
        if calculated_tier.priority > current_tier.priority:
            return True, calculated_tier, {
                **calc_metadata,
                'current_tier': current_tier.name,
                'new_tier': calculated_tier.name,
                'reason': 'Higher tier available'
            }
        
        return False, None, {
            **calc_metadata,
            'current_tier': current_tier.name,
            'reason': 'Already at appropriate tier'
        }
    
    @transaction.atomic
    def upgrade_tier(
        self,
        account: LoyaltyAccount,
        new_tier: Optional[LoyaltyTier] = None,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Upgrade account to new tier.
        
        Returns:
            Dict with upgrade details
        """
        if new_tier is None:
            can_upgrade, new_tier, metadata = self.check_upgrade(account)
            if not can_upgrade:
                return {
                    'success': False,
                    'error': 'Account not eligible for upgrade',
                    'metadata': metadata
                }
        
        old_tier = account.tier
        
        # Update account tier
        account.tier = new_tier
        account.save(update_fields=['tier'])
        
        # Emit audit event
        emit_audit_event(
            action='TIER_UPGRADED',
            object_type='LoyaltyAccount',
            object_id=str(account.id),
            details={
                'old_tier': old_tier.name if old_tier else None,
                'new_tier': new_tier.name,
                'points_balance': account.points_balance,
                'reason': reason or 'Automatic upgrade'
            },
            status='success'
        )
        
        logger.info(
            f"Tier upgraded: account={account.id}, "
            f"old_tier={old_tier.name if old_tier else None}, "
            f"new_tier={new_tier.name}"
        )
        
        return {
            'success': True,
            'old_tier': old_tier.name if old_tier else None,
            'new_tier': new_tier.name,
            'points_balance': account.points_balance
        }


class TierDowngradeService:
    """Handle tier downgrades"""
    
    def __init__(self):
        self.calculation_service = TierCalculationService()
    
    def check_downgrade(
        self,
        account: LoyaltyAccount
    ) -> Tuple[bool, Optional[LoyaltyTier], Dict]:
        """
        Check if account should be downgraded.
        
        Returns:
            (should_downgrade, new_tier, metadata) - Downgrade eligibility and new tier
        """
        if not account.tier:
            return False, None, {'reason': 'No current tier to downgrade'}
        
        # Calculate what tier should be
        calculated_tier, calc_metadata = self.calculation_service.calculate_tier(account)
        
        if not calculated_tier:
            # No tier matches = should be downgraded to None
            return True, None, {**calc_metadata, 'reason': 'No tier matches points balance'}
        
        # Check if downgrade needed
        if calculated_tier.priority < account.tier.priority:
            return True, calculated_tier, {
                **calc_metadata,
                'current_tier': account.tier.name,
                'new_tier': calculated_tier.name,
                'reason': 'Points balance below current tier threshold'
            }
        
        return False, None, {
            **calc_metadata,
            'current_tier': account.tier.name,
            'reason': 'Tier still appropriate'
        }
    
    @transaction.atomic
    def downgrade_tier(
        self,
        account: LoyaltyAccount,
        new_tier: Optional[LoyaltyTier] = None,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Downgrade account to new tier.
        
        Returns:
            Dict with downgrade details
        """
        if new_tier is None:
            should_downgrade, new_tier, metadata = self.check_downgrade(account)
            if not should_downgrade:
                return {
                    'success': False,
                    'error': 'Account should not be downgraded',
                    'metadata': metadata
                }
        
        old_tier = account.tier
        
        # Update account tier
        account.tier = new_tier
        account.save(update_fields=['tier'])
        
        # Emit audit event
        emit_audit_event(
            action='TIER_DOWNGRADED',
            object_type='LoyaltyAccount',
            object_id=str(account.id),
            details={
                'old_tier': old_tier.name if old_tier else None,
                'new_tier': new_tier.name if new_tier else None,
                'points_balance': account.points_balance,
                'reason': reason or 'Automatic downgrade'
            },
            status='success'
        )
        
        logger.info(
            f"Tier downgraded: account={account.id}, "
            f"old_tier={old_tier.name if old_tier else None}, "
            f"new_tier={new_tier.name if new_tier else None}"
        )
        
        return {
            'success': True,
            'old_tier': old_tier.name if old_tier else None,
            'new_tier': new_tier.name if new_tier else None,
            'points_balance': account.points_balance
        }


class TierBenefitService:
    """Apply tier benefits"""
    
    def get_tier_benefits(self, tier: LoyaltyTier) -> Dict:
        """Get benefits for a tier"""
        return {
            'name': tier.name,
            'description': tier.description,
            'benefits': tier.benefits,
            'min_points': tier.min_points,
            'priority': tier.priority,
            # Add more benefit details as needed
            'points_multiplier': getattr(tier, 'points_multiplier', 1.0),
            'redemption_discount': getattr(tier, 'redemption_discount', 0.0)
        }
    
    def apply_tier_benefits(
        self,
        account: LoyaltyAccount,
        benefit_type: str,
        context: Dict
    ) -> Dict:
        """
        Apply tier benefits for a specific action.
        
        Args:
            account: LoyaltyAccount
            benefit_type: Type of benefit ('earn_multiplier', 'redemption_discount', etc.)
            context: Context for benefit application
        
        Returns:
            Dict with applied benefits
        """
        if not account.tier:
            return {'benefits_applied': False, 'reason': 'No tier assigned'}
        
        benefits = self.get_tier_benefits(account.tier)
        
        if benefit_type == 'earn_multiplier':
            multiplier = benefits.get('points_multiplier', 1.0)
            base_points = context.get('base_points', 0)
            adjusted_points = int(base_points * multiplier)
            return {
                'benefits_applied': True,
                'multiplier': multiplier,
                'base_points': base_points,
                'adjusted_points': adjusted_points,
                'bonus_points': adjusted_points - base_points
            }
        
        elif benefit_type == 'redemption_discount':
            discount = benefits.get('redemption_discount', 0.0)
            original_cost = context.get('reward_cost', 0)
            discounted_cost = int(original_cost * (1 - discount))
            return {
                'benefits_applied': True,
                'discount': discount,
                'original_cost': original_cost,
                'discounted_cost': discounted_cost,
                'savings': original_cost - discounted_cost
            }
        
        return {'benefits_applied': False, 'reason': f'Unknown benefit type: {benefit_type}'}


class TierService:
    """
    Main Tier Service - Orchestrates all tier operations.
    Enterprise-grade service with automatic upgrades/downgrades and benefits.
    """
    
    def __init__(self):
        self.calculation_service = TierCalculationService()
        self.upgrade_service = TierUpgradeService()
        self.downgrade_service = TierDowngradeService()
        self.benefit_service = TierBenefitService()
    
    def calculate_and_update_tier(
        self,
        account: LoyaltyAccount,
        auto_upgrade: bool = True,
        auto_downgrade: bool = False
    ) -> Dict:
        """
        Calculate and update tier for account.
        
        Args:
            account: LoyaltyAccount to update
            auto_upgrade: Whether to automatically upgrade if eligible
            auto_downgrade: Whether to automatically downgrade if needed
        
        Returns:
            Dict with tier update details
        """
        # Check for upgrade
        if auto_upgrade:
            can_upgrade, new_tier, metadata = self.upgrade_service.check_upgrade(account)
            if can_upgrade:
                return self.upgrade_service.upgrade_tier(account, new_tier)
        
        # Check for downgrade
        if auto_downgrade:
            should_downgrade, new_tier, metadata = self.downgrade_service.check_downgrade(account)
            if should_downgrade:
                return self.downgrade_service.downgrade_tier(account, new_tier)
        
        # No change needed
        calculated_tier, calc_metadata = self.calculation_service.calculate_tier(account)
        return {
            'success': True,
            'tier_unchanged': True,
            'current_tier': account.tier.name if account.tier else None,
            'calculated_tier': calculated_tier.name if calculated_tier else None,
            'metadata': calc_metadata
        }
    
    def get_tier_benefits(self, account: LoyaltyAccount) -> Dict:
        """Get tier benefits for account"""
        if not account.tier:
            return {'benefits': None, 'reason': 'No tier assigned'}
        
        return self.benefit_service.get_tier_benefits(account.tier)
    
    def apply_benefits(
        self,
        account: LoyaltyAccount,
        benefit_type: str,
        context: Dict
    ) -> Dict:
        """Apply tier benefits"""
        return self.benefit_service.apply_tier_benefits(account, benefit_type, context)

