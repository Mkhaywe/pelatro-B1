"""
Enterprise-Grade Rewards Service
Handles rewards inventory, availability, redemption, and fulfillment.
"""
import logging
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache

from loyalty.models import LoyaltyReward, LoyaltyRedemption, LoyaltyAccount
from loyalty.services.points_service import PointsService
from apps.shared.audit import emit_audit_event

logger = logging.getLogger(__name__)


class RewardsInventoryService:
    """Manage rewards inventory"""
    
    def check_availability(
        self,
        reward: LoyaltyReward,
        quantity: int = 1
    ) -> Tuple[bool, str]:
        """
        Check if reward is available.
        
        Returns:
            (is_available, reason) - Availability status and reason
        """
        if not reward.is_active:
            return False, 'Reward is not active'
        
        # Check dates
        now = timezone.now()
        if reward.start_date and reward.start_date > now:
            return False, 'Reward has not started'
        if reward.end_date and reward.end_date < now:
            return False, 'Reward has ended'
        
        # Check inventory (if inventory fields exist)
        if hasattr(reward, 'inventory_type') and reward.inventory_type == 'limited':
            available_qty = getattr(reward, 'available_quantity', None)
            if available_qty is not None and available_qty < quantity:
                return False, f'Insufficient inventory. Available: {available_qty}, Requested: {quantity}'
        
        return True, 'Available'
    
    @transaction.atomic
    def reserve_inventory(
        self,
        reward: LoyaltyReward,
        quantity: int = 1
    ) -> bool:
        """Reserve inventory for a reward"""
        if hasattr(reward, 'inventory_type') and reward.inventory_type == 'limited':
            available_qty = getattr(reward, 'available_quantity', None)
            if available_qty is not None and available_qty < quantity:
                return False
            reward.available_quantity = available_qty - quantity
            reward.save(update_fields=['available_quantity'])
        return True
    
    @transaction.atomic
    def release_inventory(
        self,
        reward: LoyaltyReward,
        quantity: int = 1
    ):
        """Release reserved inventory"""
        if hasattr(reward, 'inventory_type') and reward.inventory_type == 'limited':
            available_qty = getattr(reward, 'available_quantity', 0)
            reward.available_quantity = available_qty + quantity
            reward.save(update_fields=['available_quantity'])


class RewardsRedemptionService:
    """Handle reward redemptions"""
    
    def __init__(self):
        self.inventory_service = RewardsInventoryService()
        self.points_service = PointsService()
    
    @transaction.atomic
    def redeem_reward(
        self,
        account: LoyaltyAccount,
        reward: LoyaltyReward,
        quantity: int = 1,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Redeem a reward for a customer.
        
        Returns:
            Dict with redemption details
        """
        # Check availability
        is_available, reason = self.inventory_service.check_availability(reward, quantity)
        if not is_available:
            return {
                'success': False,
                'error': reason
            }
        
        # Calculate total cost (use points_required or points_cost)
        points_cost = getattr(reward, 'points_cost', None) or getattr(reward, 'points_required', 0)
        total_cost = points_cost * quantity
        
        # Check account balance
        if account.points_balance < total_cost:
            return {
                'success': False,
                'error': f'Insufficient points. Balance: {account.points_balance}, Required: {total_cost}'
            }
        
        # Reserve inventory
        if not self.inventory_service.reserve_inventory(reward, quantity):
            return {
                'success': False,
                'error': 'Failed to reserve inventory'
            }
        
        try:
            # Burn points
            burn_result = self.points_service.burn_points(account, total_cost)
            if not burn_result['success']:
                # Release inventory on failure
                self.inventory_service.release_inventory(reward, quantity)
                return {
                    'success': False,
                    'error': 'Failed to process points: ' + str(burn_result.get('errors', []))
                }
            
            # Create redemption
            redemption = LoyaltyRedemption.objects.create(
                account=account,
                reward=reward,
                quantity=quantity,
                points_cost=total_cost,
                status='pending',
                metadata=metadata or {}
            )
            
            # Emit audit event
            emit_audit_event(
                action='REWARD_REDEEMED',
                object_type='LoyaltyRedemption',
                object_id=str(redemption.id),
                details={
                    'reward_id': str(reward.id),
                    'reward_name': reward.name,
                    'quantity': quantity,
                    'points_cost': total_cost,
                    'account_id': str(account.id),
                    'customer_id': str(account.customer_id)
                },
                status='success'
            )
            
            return {
                'success': True,
                'redemption_id': str(redemption.id),
                'points_cost': total_cost,
                'balance_after': burn_result['balance_after'],
                'redemption': {
                    'id': str(redemption.id),
                    'status': redemption.status,
                    'created_at': redemption.created_at.isoformat()
                }
            }
        
        except Exception as e:
            # Release inventory on error
            self.inventory_service.release_inventory(reward, quantity)
            logger.error(f"Error redeeming reward: {e}")
            return {
                'success': False,
                'error': f'Redemption failed: {str(e)}'
            }
    
    @transaction.atomic
    def fulfill_redemption(
        self,
        redemption: LoyaltyRedemption,
        fulfillment_data: Optional[Dict] = None
    ) -> Dict:
        """
        Fulfill a redemption (mark as completed).
        
        Returns:
            Dict with fulfillment details
        """
        if redemption.status == 'fulfilled':
            return {
                'success': False,
                'error': 'Redemption already fulfilled'
            }
        
        redemption.status = 'fulfilled'
        redemption.fulfilled_at = timezone.now()
        if fulfillment_data:
            redemption.metadata.update(fulfillment_data)
        redemption.save(update_fields=['status', 'fulfilled_at', 'metadata'])
        
        emit_audit_event(
            action='REDEMPTION_FULFILLED',
            object_type='LoyaltyRedemption',
            object_id=str(redemption.id),
            details={
                'redemption_id': str(redemption.id),
                'fulfilled_at': redemption.fulfilled_at.isoformat()
            },
            status='success'
        )
        
        return {
            'success': True,
            'redemption_id': str(redemption.id),
            'fulfilled_at': redemption.fulfilled_at.isoformat()
        }
    
    @transaction.atomic
    def cancel_redemption(
        self,
        redemption: LoyaltyRedemption,
        reason: str
    ) -> Dict:
        """
        Cancel a redemption and refund points.
        
        Returns:
            Dict with cancellation details
        """
        if redemption.status in ['fulfilled', 'cancelled']:
            return {
                'success': False,
                'error': f'Cannot cancel redemption in status: {redemption.status}'
            }
        
        # Refund points
        refund_result = self.points_service.earn_points(
            redemption.account,
            redemption.points_cost,
            {
                'description': f'Refund for cancelled redemption {redemption.id}',
                'transaction_date': timezone.now()
            }
        )
        
        if not refund_result['success']:
            return {
                'success': False,
                'error': 'Failed to refund points'
            }
        
        # Release inventory
        self.inventory_service.release_inventory(redemption.reward, redemption.quantity)
        
        # Cancel redemption
        redemption.status = 'cancelled'
        redemption.metadata['cancellation_reason'] = reason
        redemption.cancelled_at = timezone.now()
        redemption.save(update_fields=['status', 'metadata', 'cancelled_at'])
        
        emit_audit_event(
            action='REDEMPTION_CANCELLED',
            object_type='LoyaltyRedemption',
            object_id=str(redemption.id),
            details={
                'redemption_id': str(redemption.id),
                'reason': reason,
                'points_refunded': redemption.points_cost
            },
            status='success'
        )
        
        return {
            'success': True,
            'redemption_id': str(redemption.id),
            'points_refunded': redemption.points_cost,
            'balance_after': refund_result['balance_after']
        }


class RewardsService:
    """
    Main Rewards Service - Orchestrates all rewards operations.
    Enterprise-grade service with inventory management, redemption, and fulfillment.
    """
    
    def __init__(self):
        self.inventory_service = RewardsInventoryService()
        self.redemption_service = RewardsRedemptionService()
    
    def check_availability(self, reward: LoyaltyReward, quantity: int = 1) -> Tuple[bool, str]:
        """Check reward availability"""
        return self.inventory_service.check_availability(reward, quantity)
    
    def redeem_reward(
        self,
        account: LoyaltyAccount,
        reward: LoyaltyReward,
        quantity: int = 1,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Redeem a reward"""
        return self.redemption_service.redeem_reward(account, reward, quantity, metadata)
    
    def fulfill_redemption(
        self,
        redemption: LoyaltyRedemption,
        fulfillment_data: Optional[Dict] = None
    ) -> Dict:
        """Fulfill a redemption"""
        return self.redemption_service.fulfill_redemption(redemption, fulfillment_data)
    
    def cancel_redemption(
        self,
        redemption: LoyaltyRedemption,
        reason: str
    ) -> Dict:
        """Cancel a redemption"""
        return self.redemption_service.cancel_redemption(redemption, reason)

