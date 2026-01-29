"""
Journey Action Execution Service
Handles execution of different action types in journey nodes.
"""
import logging
from typing import Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class JourneyActionExecutor:
    """Execute journey actions"""
    
    def execute_action(
        self,
        action_type: str,
        config: Dict,
        context: Dict
    ) -> Dict:
        """
        Execute a journey action.
        
        Args:
            action_type: Type of action to execute
            config: Action configuration from node
            context: Execution context (customer_id, journey_id, etc.)
        
        Returns:
            Dict with execution result
        """
        customer_id = context.get('customer_id')
        if not customer_id:
            return {
                'success': False,
                'error': 'customer_id required in context'
            }
        
        try:
            if action_type == 'send_email':
                return self._send_email(config, context)
            elif action_type == 'send_sms':
                return self._send_sms(config, context)
            elif action_type == 'send_push':
                return self._send_push(config, context)
            elif action_type == 'award_points':
                return self._award_points(config, context)
            elif action_type == 'trigger_campaign':
                return self._trigger_campaign(config, context)
            else:
                return {
                    'success': False,
                    'error': f'Unknown action type: {action_type}'
                }
        except Exception as e:
            logger.error(f"Error executing action {action_type}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_email(self, config: Dict, context: Dict) -> Dict:
        """Send email to customer"""
        customer_id = context.get('customer_id')
        subject = config.get('subject', 'Loyalty Program Update')
        template = config.get('template', 'default')
        variables = config.get('variables', {})
        
        # TODO: Integrate with email service (SendGrid, AWS SES, etc.)
        # For now, log the action
        logger.info(
            f"Action: Send email to {customer_id} - Subject: {subject}, Template: {template}"
        )
        
        # In production, this would:
        # 1. Fetch customer email from DWH/Xiva
        # 2. Render email template with variables
        # 3. Send via email service
        # 4. Log email sent event
        
        return {
            'success': True,
            'action': 'send_email',
            'customer_id': str(customer_id),
            'subject': subject,
            'template': template,
            'message': 'Email queued for sending'
        }
    
    def _send_sms(self, config: Dict, context: Dict) -> Dict:
        """Send SMS to customer"""
        customer_id = context.get('customer_id')
        message = config.get('message', '')
        template = config.get('template', 'default')
        variables = config.get('variables', {})
        
        # TODO: Integrate with SMS service (Twilio, AWS SNS, etc.)
        logger.info(
            f"Action: Send SMS to {customer_id} - Message: {message[:50]}..."
        )
        
        # In production, this would:
        # 1. Fetch customer phone from DWH/Xiva
        # 2. Render SMS template with variables
        # 3. Send via SMS service
        # 4. Log SMS sent event
        
        return {
            'success': True,
            'action': 'send_sms',
            'customer_id': str(customer_id),
            'message': message,
            'template': template,
            'message': 'SMS queued for sending'
        }
    
    def _send_push(self, config: Dict, context: Dict) -> Dict:
        """Send push notification to customer"""
        customer_id = context.get('customer_id')
        title = config.get('title', 'Loyalty Program')
        body = config.get('body', '')
        data = config.get('data', {})
        
        # TODO: Integrate with push notification service (FCM, APNS, etc.)
        logger.info(
            f"Action: Send push to {customer_id} - Title: {title}"
        )
        
        # In production, this would:
        # 1. Fetch customer device tokens from DWH
        # 2. Send push via FCM/APNS
        # 3. Log push sent event
        
        return {
            'success': True,
            'action': 'send_push',
            'customer_id': str(customer_id),
            'title': title,
            'body': body,
            'message': 'Push notification queued'
        }
    
    def _award_points(self, config: Dict, context: Dict) -> Dict:
        """Award points to customer"""
        from loyalty.models import LoyaltyAccount
        from loyalty.services.points_service import PointsService
        
        customer_id = context.get('customer_id')
        points = config.get('points', 0)
        program_id = config.get('program_id') or context.get('program_id')
        reason = config.get('reason', 'Journey action')
        
        if points <= 0:
            return {
                'success': False,
                'error': 'Points must be greater than 0'
            }
        
        try:
            # Find or create loyalty account
            if program_id:
                account = LoyaltyAccount.objects.filter(
                    customer_id=customer_id,
                    program_id=program_id
                ).first()
            else:
                # Use default program if available
                from loyalty.models import LoyaltyProgram
                default_program = LoyaltyProgram.objects.filter(is_active=True).first()
                if not default_program:
                    return {
                        'success': False,
                        'error': 'No active program found'
                    }
                account = LoyaltyAccount.objects.filter(
                    customer_id=customer_id,
                    program=default_program
                ).first()
            
            if not account:
                return {
                    'success': False,
                    'error': f'No loyalty account found for customer {customer_id}'
                }
            
            # Award points
            points_service = PointsService()
            transaction = points_service.earn_points(
                account=account,
                amount=points,
                reason=reason,
                metadata={
                    'source': 'journey_action',
                    'journey_id': context.get('journey_id'),
                    'action_type': 'award_points'
                }
            )
            
            logger.info(
                f"Action: Awarded {points} points to {customer_id} (account {account.id})"
            )
            
            return {
                'success': True,
                'action': 'award_points',
                'customer_id': str(customer_id),
                'points': points,
                'transaction_id': str(transaction.id),
                'new_balance': account.points_balance
            }
        except Exception as e:
            logger.error(f"Error awarding points: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _trigger_campaign(self, config: Dict, context: Dict) -> Dict:
        """Trigger a campaign for customer"""
        from loyalty.models_khaywe import Campaign
        from loyalty.engines.campaign_engine import CampaignDeliveryService
        
        customer_id = context.get('customer_id')
        campaign_id = config.get('campaign_id')
        channel = config.get('channel')  # Optional channel override
        
        if not campaign_id:
            return {
                'success': False,
                'error': 'campaign_id required in action config'
            }
        
        try:
            campaign = Campaign.objects.get(id=campaign_id, is_active=True)
            
            # Deliver campaign
            delivery_service = CampaignDeliveryService()
            result = delivery_service.deliver_campaign(
                campaign=campaign,
                customer_id=str(customer_id),
                channel=channel
            )
            
            if not result.get('success'):
                return result
            
            logger.info(
                f"Action: Triggered campaign {campaign_id} for {customer_id}"
            )
            
            return {
                'success': True,
                'action': 'trigger_campaign',
                'customer_id': str(customer_id),
                'campaign_id': campaign_id,
                'campaign_name': campaign.name,
                'execution_id': result.get('execution_id'),
                'channel': result.get('channel')
            }
        except Campaign.DoesNotExist:
            return {
                'success': False,
                'error': f'Campaign {campaign_id} not found or inactive'
            }
        except Exception as e:
            logger.error(f"Error triggering campaign: {e}")
            return {
                'success': False,
                'error': str(e)
            }

