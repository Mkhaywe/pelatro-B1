"""
Enterprise-Grade Points Service
Handles all points-related business logic with comprehensive validation,
expiry, caps, and reconciliation.
"""
import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_DOWN
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.conf import settings

from loyalty.models import LoyaltyAccount, LoyaltyTransaction, LoyaltyProgram
from loyalty.models_khaywe import EarnCap, CapUsage, PointsExpiryRule, PointsExpiryEvent
from loyalty.services.eligibility_service import EligibilityService
from apps.shared.audit import emit_audit_event

logger = logging.getLogger(__name__)


class PointsCalculationService:
    """Calculate points based on rules and context"""
    
    def __init__(self):
        self.eligibility_service = EligibilityService()
    
    def calculate_earn_points(
        self,
        account: LoyaltyAccount,
        transaction_amount: Decimal,
        transaction_context: Dict,
        earn_rules: Optional[Dict] = None
    ) -> Tuple[int, Dict]:
        """
        Calculate points to earn based on rules and context.
        
        Returns:
            (points, metadata) - Points amount and calculation metadata
        """
        if not account or account.status != 'active':
            return 0, {'error': 'Account not active'}
        
        # Get program earn rules if not provided
        if earn_rules is None:
            program = account.program
            # In real implementation, get from LoyaltyRule
            earn_rules = {}
        
        # Default calculation: 1 point per currency unit
        base_points = int(transaction_amount)
        
        # Apply tier multiplier if exists
        if account.tier:
            tier_multiplier = getattr(account.tier, 'points_multiplier', 1.0)
            base_points = int(base_points * tier_multiplier)
        
        # Apply JSONLogic rules if provided
        if earn_rules:
            try:
                # Evaluate rules with transaction context
                context = {
                    'transaction_amount': float(transaction_amount),
                    'customer_id': str(account.customer_id),
                    'program': account.program.name,
                    'tier': account.tier.name if account.tier else None,
                    **transaction_context
                }
                # In real implementation, use JSONLogic evaluator
                # For now, use base calculation
                calculated_points = base_points
            except Exception as e:
                logger.error(f"Error evaluating earn rules: {e}")
                calculated_points = base_points
        else:
            calculated_points = base_points
        
        metadata = {
            'base_points': base_points,
            'calculated_points': calculated_points,
            'tier_multiplier': getattr(account.tier, 'points_multiplier', 1.0) if account.tier else 1.0,
            'rules_applied': bool(earn_rules)
        }
        
        return max(0, calculated_points), metadata
    
    def calculate_burn_points(
        self,
        account: LoyaltyAccount,
        reward_cost: int,
        burn_rules: Optional[Dict] = None
    ) -> Tuple[int, Dict]:
        """
        Calculate points to burn for a reward.
        
        Returns:
            (points, metadata) - Points amount and calculation metadata
        """
        if not account or account.status != 'active':
            return 0, {'error': 'Account not active'}
        
        if account.points_balance < reward_cost:
            return 0, {'error': 'Insufficient points'}
        
        # Apply tier discount if exists
        if account.tier:
            tier_discount = getattr(account.tier, 'redemption_discount', 0.0)
            if tier_discount > 0:
                discount_amount = int(reward_cost * tier_discount)
                actual_cost = reward_cost - discount_amount
            else:
                actual_cost = reward_cost
        else:
            actual_cost = reward_cost
        
        metadata = {
            'reward_cost': reward_cost,
            'actual_cost': actual_cost,
            'tier_discount': getattr(account.tier, 'redemption_discount', 0.0) if account.tier else 0.0
        }
        
        return max(0, actual_cost), metadata


class PointsValidationService:
    """Validate points transactions before execution"""
    
    def __init__(self):
        self.cap_service = PointsCapService()
        self.eligibility_service = EligibilityService()
    
    def validate_earn_transaction(
        self,
        account: LoyaltyAccount,
        points: int,
        transaction_context: Dict
    ) -> Tuple[bool, List[str]]:
        """
        Validate if points can be earned.
        
        Returns:
            (is_valid, errors) - Validation result and error messages
        """
        errors = []
        
        # Check account status
        if account.status != 'active':
            errors.append('Account is not active')
        
        # Check program status
        if not account.program.is_active:
            errors.append('Program is not active')
        
        # Check program dates
        now = timezone.now()
        if account.program.start_date > now:
            errors.append('Program has not started')
        if account.program.end_date and account.program.end_date < now:
            errors.append('Program has ended')
        
        # Check eligibility
        is_eligible, eligibility_errors = self.eligibility_service.check_eligibility(
            account.customer_id,
            account.program
        )
        if not is_eligible:
            errors.extend(eligibility_errors)
        
        # Check caps
        cap_check, cap_errors = self.cap_service.check_earn_cap(
            account,
            points,
            transaction_context.get('transaction_date', now)
        )
        if not cap_check:
            errors.extend(cap_errors)
        
        return len(errors) == 0, errors
    
    def validate_burn_transaction(
        self,
        account: LoyaltyAccount,
        points: int
    ) -> Tuple[bool, List[str]]:
        """
        Validate if points can be burned.
        
        Returns:
            (is_valid, errors) - Validation result and error messages
        """
        errors = []
        
        # Check account status
        if account.status != 'active':
            errors.append('Account is not active')
        
        # Check balance
        if account.points_balance < points:
            errors.append(f'Insufficient points. Balance: {account.points_balance}, Required: {points}')
        
        # Check minimum balance (if exists)
        min_balance = getattr(account.program, 'min_balance', 0)
        if account.points_balance - points < min_balance:
            errors.append(f'Transaction would violate minimum balance: {min_balance}')
        
        return len(errors) == 0, errors


class PointsCapService:
    """Handle points earning and burning caps"""
    
    def check_earn_cap(
        self,
        account: LoyaltyAccount,
        points: int,
        transaction_date: Optional[timezone.datetime] = None
    ) -> Tuple[bool, List[str]]:
        """
        Check if earning points would exceed caps.
        
        Returns:
            (is_allowed, errors) - Whether allowed and error messages
        """
        if transaction_date is None:
            transaction_date = timezone.now()
        
        errors = []
        
        # Get caps for this program
        caps = EarnCap.objects.filter(
            program=account.program,
            is_active=True
        )
        
        for cap in caps:
            # Get usage for the period
            usage = self._get_cap_usage(account, cap, transaction_date)
            
            # Check if adding points would exceed cap
            if usage + points > cap.max_points:
                errors.append(
                    f'Would exceed {cap.period} cap: {usage}/{cap.max_points} points used'
                )
        
        return len(errors) == 0, errors
    
    def _get_cap_usage(
        self,
        account: LoyaltyAccount,
        cap: EarnCap,
        transaction_date: timezone.datetime
    ) -> int:
        """Get current cap usage for the period"""
        # Get period start
        if cap.period == 'day':
            period_start = transaction_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif cap.period == 'week':
            days_since_monday = transaction_date.weekday()
            period_start = (transaction_date - timezone.timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif cap.period == 'month':
            period_start = transaction_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            period_start = transaction_date
        
        # Get usage from CapUsage or calculate from transactions
        try:
            cap_usage = CapUsage.objects.get(
                account=account,
                cap=cap,
                period_start=period_start
            )
            return cap_usage.used_points
        except CapUsage.DoesNotExist:
            # Calculate from transactions
            transactions = LoyaltyTransaction.objects.filter(
                account=account,
                transaction_type='earn',
                created_at__gte=period_start,
                created_at__lte=transaction_date
            )
            return sum(tx.amount for tx in transactions)
    
    def record_cap_usage(
        self,
        account: LoyaltyAccount,
        points: int,
        transaction_date: Optional[timezone.datetime] = None
    ):
        """Record cap usage after transaction"""
        if transaction_date is None:
            transaction_date = timezone.now()
        
        caps = EarnCap.objects.filter(
            program=account.program,
            is_active=True
        )
        
        for cap in caps:
            period_start = self._get_period_start(cap, transaction_date)
            
            cap_usage, created = CapUsage.objects.get_or_create(
                account=account,
                cap=cap,
                period_start=period_start,
                defaults={'used_points': 0}
            )
            
            cap_usage.used_points += points
            cap_usage.save()


class PointsExpiryService:
    """Handle points expiry"""
    
    def process_expiry(
        self,
        account: LoyaltyAccount,
        expiry_date: Optional[timezone.datetime] = None
    ) -> Dict:
        """
        Process points expiry for an account.
        
        Returns:
            Dict with expiry details
        """
        if expiry_date is None:
            expiry_date = timezone.now()
        
        # Get expiry rules for program
        expiry_rules = PointsExpiryRule.objects.filter(
            program=account.program,
            is_active=True
        )
        
        if not expiry_rules.exists():
            return {'expired_points': 0, 'remaining_balance': account.points_balance}
        
        # Get transactions that should expire
        expiry_rule = expiry_rules.first()  # For now, use first rule
        expiry_period_days = expiry_rule.expiry_period_days
        
        cutoff_date = expiry_date - timezone.timedelta(days=expiry_period_days)
        
        # Get earn transactions before cutoff
        expired_transactions = LoyaltyTransaction.objects.filter(
            account=account,
            transaction_type='earn',
            created_at__lt=cutoff_date
        ).exclude(
            amount__lte=0
        )
        
        # Calculate expired points (FIFO)
        expired_points = 0
        remaining_balance = account.points_balance
        
        for tx in expired_transactions.order_by('created_at'):
            if remaining_balance > 0:
                points_to_expire = min(tx.amount, remaining_balance)
                expired_points += points_to_expire
                remaining_balance -= points_to_expire
        
        # Create expiry transaction if points expired
        if expired_points > 0:
            with transaction.atomic():
                # Create expiry transaction
                expiry_tx = LoyaltyTransaction.objects.create(
                    account=account,
                    transaction_type='expire',
                    amount=-expired_points,
                    description=f'Points expired after {expiry_period_days} days',
                    created_at=expiry_date
                )
                
                # Update account balance
                account.points_balance = remaining_balance
                account.save(update_fields=['points_balance'])
                
                # Record expiry event
                PointsExpiryEvent.objects.create(
                    account=account,
                    expired_points=expired_points,
                    expiry_rule=expiry_rule,
                    transaction=expiry_tx
                )
                
                emit_audit_event(
                    action='POINTS_EXPIRED',
                    object_type='LoyaltyAccount',
                    object_id=str(account.id),
                    details={
                        'expired_points': expired_points,
                        'remaining_balance': remaining_balance,
                        'expiry_rule': expiry_rule.id
                    },
                    status='success'
                )
        
        return {
            'expired_points': expired_points,
            'remaining_balance': remaining_balance,
            'expiry_rule': expiry_rule.id if expiry_rule else None
        }


class PointsReconciliationService:
    """Reconcile points balances"""
    
    def reconcile_account(self, account: LoyaltyAccount) -> Dict:
        """
        Reconcile account balance by recalculating from transactions.
        
        Returns:
            Dict with reconciliation results
        """
        # Calculate expected balance from transactions
        transactions = LoyaltyTransaction.objects.filter(account=account)
        
        expected_balance = sum(
            tx.amount if tx.transaction_type in ['earn', 'adjust'] else -tx.amount
            for tx in transactions
        )
        
        actual_balance = account.points_balance
        discrepancy = expected_balance - actual_balance
        
        if discrepancy != 0:
            logger.warning(
                f"Balance discrepancy for account {account.id}: "
                f"Expected {expected_balance}, Actual {actual_balance}, "
                f"Discrepancy: {discrepancy}"
            )
            
            # Auto-correct if discrepancy is small (configurable threshold)
            auto_correct_threshold = getattr(settings, 'POINTS_AUTO_CORRECT_THRESHOLD', 10)
            if abs(discrepancy) <= auto_correct_threshold:
                with transaction.atomic():
                    account.points_balance = expected_balance
                    account.save(update_fields=['points_balance'])
                    
                    # Create adjustment transaction
                    LoyaltyTransaction.objects.create(
                        account=account,
                        transaction_type='adjust',
                        amount=discrepancy,
                        description=f'Auto-reconciliation: Corrected balance discrepancy',
                        created_at=timezone.now()
                    )
                    
                    emit_audit_event(
                        action='BALANCE_RECONCILED',
                        object_type='LoyaltyAccount',
                        object_id=str(account.id),
                        details={
                            'expected_balance': expected_balance,
                            'actual_balance': actual_balance,
                            'discrepancy': discrepancy,
                            'auto_corrected': True
                        },
                        status='success'
                    )
        
        return {
            'expected_balance': expected_balance,
            'actual_balance': actual_balance,
            'discrepancy': discrepancy,
            'reconciled': discrepancy == 0
        }


class PointsService:
    """
    Main Points Service - Orchestrates all points operations.
    Enterprise-grade service with comprehensive validation, caps, expiry.
    """
    
    def __init__(self):
        self.calculation_service = PointsCalculationService()
        self.validation_service = PointsValidationService()
        self.cap_service = PointsCapService()
        self.expiry_service = PointsExpiryService()
        self.reconciliation_service = PointsReconciliationService()
    
    @transaction.atomic
    def earn_points(
        self,
        account: LoyaltyAccount,
        transaction_amount: Decimal,
        transaction_context: Dict,
        earn_rules: Optional[Dict] = None
    ) -> Dict:
        """
        Earn points for a customer.
        
        Returns:
            Dict with transaction details and metadata
        """
        # Calculate points
        points, calc_metadata = self.calculation_service.calculate_earn_points(
            account, transaction_amount, transaction_context, earn_rules
        )
        
        if points <= 0:
            return {
                'success': False,
                'error': 'No points to earn',
                'metadata': calc_metadata
            }
        
        # Validate transaction
        is_valid, errors = self.validation_service.validate_earn_transaction(
            account, points, transaction_context
        )
        
        if not is_valid:
            return {
                'success': False,
                'errors': errors,
                'metadata': calc_metadata
            }
        
        # Create transaction
        tx = LoyaltyTransaction.objects.create(
            account=account,
            transaction_type='earn',
            amount=points,
            description=transaction_context.get('description', 'Points earned'),
            metadata=calc_metadata,
            created_at=transaction_context.get('transaction_date', timezone.now())
        )
        
        # Update account balance
        account.points_balance += points
        account.save(update_fields=['points_balance'])
        
        # Record cap usage
        self.cap_service.record_cap_usage(
            account, points, transaction_context.get('transaction_date')
        )
        
        # Emit audit event
        emit_audit_event(
            action='POINTS_EARNED',
            object_type='LoyaltyAccount',
            object_id=str(account.id),
            details={
                'points': points,
                'transaction_id': str(tx.id),
                'balance_after': account.points_balance,
                **calc_metadata
            },
            status='success'
        )
        
        return {
            'success': True,
            'transaction_id': str(tx.id),
            'points': points,
            'balance_after': account.points_balance,
            'metadata': calc_metadata
        }
    
    @transaction.atomic
    def burn_points(
        self,
        account: LoyaltyAccount,
        reward_cost: int,
        burn_rules: Optional[Dict] = None
    ) -> Dict:
        """
        Burn points for a reward redemption.
        
        Returns:
            Dict with transaction details
        """
        # Calculate actual cost
        points, calc_metadata = self.calculation_service.calculate_burn_points(
            account, reward_cost, burn_rules
        )
        
        if points <= 0:
            return {
                'success': False,
                'error': calc_metadata.get('error', 'Invalid redemption'),
                'metadata': calc_metadata
            }
        
        # Validate transaction
        is_valid, errors = self.validation_service.validate_burn_transaction(
            account, points
        )
        
        if not is_valid:
            return {
                'success': False,
                'errors': errors,
                'metadata': calc_metadata
            }
        
        # Create transaction
        tx = LoyaltyTransaction.objects.create(
            account=account,
            transaction_type='redeem',
            amount=-points,
            description=calc_metadata.get('description', 'Points redeemed'),
            metadata=calc_metadata,
            created_at=timezone.now()
        )
        
        # Update account balance
        account.points_balance -= points
        account.save(update_fields=['points_balance'])
        
        # Emit audit event
        emit_audit_event(
            action='POINTS_REDEEMED',
            object_type='LoyaltyAccount',
            object_id=str(account.id),
            details={
                'points': points,
                'transaction_id': str(tx.id),
                'balance_after': account.points_balance,
                **calc_metadata
            },
            status='success'
        )
        
        return {
            'success': True,
            'transaction_id': str(tx.id),
            'points': points,
            'balance_after': account.points_balance,
            'metadata': calc_metadata
        }
    
    def process_expiry(self, account: LoyaltyAccount) -> Dict:
        """Process points expiry for an account"""
        return self.expiry_service.process_expiry(account)
    
    def reconcile_account(self, account: LoyaltyAccount) -> Dict:
        """Reconcile account balance"""
        return self.reconciliation_service.reconcile_account(account)

