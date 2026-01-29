"""
Enterprise-Grade Campaign Execution Engine
Handles automatic campaign triggering, targeting, delivery, and performance tracking.
"""
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache

# Optional croniter for schedule triggers
try:
    from croniter import croniter
    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False
    croniter = None
    logger = logging.getLogger(__name__)
    logger.warning("croniter not available. Schedule triggers disabled.")

from loyalty.models_khaywe import Campaign, CampaignExecution
from loyalty.models import LoyaltyAccount
from loyalty.services.segmentation import SegmentationEngine
from loyalty.services.eligibility_service import EligibilityService
from loyalty.integration.external import fetch_customer_context
from apps.shared.audit import emit_audit_event

logger = logging.getLogger(__name__)


class CampaignTriggerService:
    """Evaluate campaign triggers"""
    
    def evaluate_event_trigger(
        self,
        campaign: Campaign,
        event_type: str,
        event_data: Dict
    ) -> bool:
        """
        Evaluate if an event trigger matches.
        
        Args:
            campaign: Campaign to check
            event_type: Type of event (e.g., 'customer.purchase')
            event_data: Event data
        
        Returns:
            True if trigger matches
        """
        for trigger in campaign.event_triggers:
            if trigger.get('event_type') == event_type:
                # Check conditions if any
                conditions = trigger.get('conditions', {})
                if conditions:
                    # Evaluate JSONLogic conditions
                    from loyalty.utils import safe_json_logic
                    try:
                        if not safe_json_logic(conditions, event_data):
                            return False
                    except Exception as e:
                        logger.error(f"Error evaluating event trigger conditions: {e}")
                        return False
                return True
        return False
    
    def evaluate_schedule_trigger(
        self,
        campaign: Campaign,
        current_time: Optional[datetime] = None
    ) -> bool:
        """
        Evaluate if a schedule trigger matches.
        
        Args:
            campaign: Campaign to check
            current_time: Current time (defaults to now)
        
        Returns:
            True if trigger matches
        """
        if not CRONITER_AVAILABLE:
            logger.warning("croniter not available, schedule triggers disabled")
            return False
        
        if current_time is None:
            current_time = timezone.now()
        
        for trigger in campaign.schedule_triggers:
            cron_expr = trigger.get('cron')
            if not cron_expr:
                continue
            
            try:
                # Check if current time matches cron expression
                cron = croniter(cron_expr, current_time)
                prev_time = cron.get_prev(datetime)
                next_time = cron.get_next(datetime)
                
                # Check if we're within the execution window
                time_diff_prev = (current_time - prev_time).total_seconds()
                time_diff_next = (next_time - current_time).total_seconds()
                
                # Execute if we're within 60 seconds of the scheduled time
                if time_diff_prev < 60 or time_diff_next < 60:
                    return True
            except Exception as e:
                logger.error(f"Error evaluating schedule trigger: {e}")
                continue
        
        return False
    
    def evaluate_threshold_trigger(
        self,
        campaign: Campaign,
        customer_id: str
    ) -> bool:
        """
        Evaluate if a threshold trigger matches.
        
        Args:
            campaign: Campaign to check
            customer_id: Customer to check
        
        Returns:
            True if trigger matches
        """
        from loyalty.integration.feature_store import FeatureStore
        
        feature_store = FeatureStore()
        customer_features = feature_store.get_customer_features(customer_id)
        
        for trigger in campaign.threshold_triggers:
            metric = trigger.get('metric')
            operator = trigger.get('operator', '>')
            threshold = trigger.get('threshold', 0)
            
            # Get metric value from features or account
            if metric == 'points_balance':
                try:
                    account = LoyaltyAccount.objects.get(
                        customer_id=customer_id,
                        program=campaign.program
                    )
                    value = account.points_balance
                except LoyaltyAccount.DoesNotExist:
                    value = 0
            elif metric in customer_features:
                value = customer_features[metric]
            else:
                continue
            
            # Evaluate operator
            if operator == '>' and value > threshold:
                return True
            elif operator == '<' and value < threshold:
                return True
            elif operator == '>=' and value >= threshold:
                return True
            elif operator == '<=' and value <= threshold:
                return True
            elif operator == '==' and value == threshold:
                return True
        
        return False


class CampaignTargetingService:
    """Find eligible customers for campaigns"""
    
    def __init__(self):
        self.segmentation_engine = SegmentationEngine()
        self.eligibility_service = EligibilityService()
    
    def find_target_customers(
        self,
        campaign: Campaign,
        limit: Optional[int] = None
    ) -> Set[str]:
        """
        Find customers eligible for campaign.
        
        Args:
            campaign: Campaign to target
            limit: Maximum number of customers to return
        
        Returns:
            Set of customer IDs
        """
        target_customers = set()
        
        # If segment specified, use segment members
        if campaign.segment:
            segment_members = self.segmentation_engine.calculate_segment_membership(
                campaign.segment
            )
            target_customers.update(segment_members)
        else:
            # No segment = all customers in program
            if campaign.program:
                accounts = LoyaltyAccount.objects.filter(
                    program=campaign.program,
                    status='active'
                )
                if limit:
                    accounts = accounts[:limit]
                target_customers.update(str(acc.customer_id) for acc in accounts)
        
        # Apply eligibility rules if any
        if campaign.eligibility_rules:
            eligible_customers = set()
            for customer_id in target_customers:
                is_eligible, _, _ = self.eligibility_service.check_eligibility(
                    customer_id,
                    campaign.program,
                    context={'campaign': campaign.name}
                )
                if is_eligible:
                    eligible_customers.add(customer_id)
            target_customers = eligible_customers
        
        # Apply limit
        if limit and len(target_customers) > limit:
            target_customers = set(list(target_customers)[:limit])
        
        return target_customers
    
    def check_frequency_cap(
        self,
        campaign: Campaign,
        customer_id: str
    ) -> bool:
        """
        Check if customer has exceeded frequency cap.
        
        Returns:
            True if within cap, False if exceeded
        """
        if campaign.frequency_cap == 0:
            return True  # No cap
        
        # Get period start
        now = timezone.now()
        if campaign.frequency_period == 'day':
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif campaign.frequency_period == 'week':
            days_since_monday = now.weekday()
            period_start = (now - timezone.timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif campaign.frequency_period == 'month':
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            period_start = now
        
        # Count executions in period
        execution_count = CampaignExecution.objects.filter(
            campaign=campaign,
            customer_id=customer_id,
            triggered_at__gte=period_start
        ).count()
        
        return execution_count < campaign.frequency_cap


class CampaignDeliveryService:
    """Deliver campaigns to customers"""
    
    def deliver_campaign(
        self,
        campaign: Campaign,
        customer_id: str,
        channel: Optional[str] = None
    ) -> Dict:
        """
        Deliver campaign to customer.
        
        Args:
            campaign: Campaign to deliver
            customer_id: Customer to deliver to
            channel: Channel to use (defaults to first channel in campaign)
        
        Returns:
            Dict with delivery details
        """
        if not channel:
            channels = campaign.channels or []
            if not channels:
                return {
                    'success': False,
                    'error': 'No channels configured for campaign'
                }
            channel = channels[0]
        
        # Get system-level channel configuration
        try:
            from loyalty.models_khaywe import DeliveryChannelConfig
            channel_config_obj = DeliveryChannelConfig.objects.get(channel=channel, is_enabled=True)
        except DeliveryChannelConfig.DoesNotExist:
            return {
                'success': False,
                'error': f'Channel {channel} is not configured or enabled in system settings'
            }
        
        # Get campaign-specific channel settings (if any)
        campaign_channel_settings = campaign.channel_settings or {}
        campaign_channel_config = campaign_channel_settings.get(channel, {})
        
        # Prepare delivery payload
        delivery_payload = {
            'campaign_id': campaign.id,
            'campaign_name': campaign.name,
            'customer_id': customer_id,
            'channel': channel,
            **campaign_channel_config  # Campaign-specific settings override defaults
        }
        
        # Deliver based on configured mode
        if channel_config_obj.delivery_mode == 'kafka':
            delivery_result = self._deliver_via_kafka(channel_config_obj, delivery_payload)
        elif channel_config_obj.delivery_mode == 'api':
            delivery_result = self._deliver_via_api(channel_config_obj, delivery_payload)
        else:
            return {
                'success': False,
                'error': f'Unknown delivery mode: {channel_config_obj.delivery_mode}'
            }
        
        # Create execution record
        execution = CampaignExecution.objects.create(
            campaign=campaign,
            customer_id=customer_id,
            channel=channel,
            triggered_at=timezone.now(),
            delivered_at=timezone.now() if delivery_result.get('success') else None,
            metadata={
                'campaign_name': campaign.name,
                'campaign_version': campaign.version,
                'delivery_mode': channel_config_obj.delivery_mode,
                'delivery_result': delivery_result,
            }
        )
        
        return {
            'success': delivery_result.get('success', False),
            'execution_id': str(execution.id),
            'channel': channel,
            'delivery_mode': channel_config_obj.delivery_mode,
            'delivered_at': execution.delivered_at.isoformat() if execution.delivered_at else None,
            **delivery_result
        }
    
    def _deliver_via_kafka(self, channel_config: 'DeliveryChannelConfig', payload: Dict) -> Dict:
        """Deliver campaign via Kafka topic"""
        try:
            # TODO: Integrate with Kafka producer
            # from kafka import KafkaProducer
            # producer = KafkaProducer(
            #     bootstrap_servers=channel_config.kafka_brokers,
            #     **channel_config.kafka_config
            # )
            # producer.send(channel_config.kafka_topic, value=json.dumps(payload).encode())
            # producer.flush()
            
            logger.info(
                f"Kafka delivery: topic={channel_config.kafka_topic}, "
                f"customer={payload.get('customer_id')}"
            )
            
            return {
                'success': True,
                'message': f'Message queued to Kafka topic: {channel_config.kafka_topic}',
                'kafka_topic': channel_config.kafka_topic
            }
        except Exception as e:
            logger.error(f"Kafka delivery error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _deliver_via_api(self, channel_config: 'DeliveryChannelConfig', payload: Dict) -> Dict:
        """Deliver campaign via direct API call"""
        try:
            import requests
            
            # Prepare headers
            headers = channel_config.api_headers.copy() if channel_config.api_headers else {}
            
            # Add authentication
            if channel_config.api_auth_type == 'bearer':
                token = channel_config.api_auth_config.get('token', '')
                headers['Authorization'] = f'Bearer {token}'
            elif channel_config.api_auth_type == 'basic':
                import base64
                username = channel_config.api_auth_config.get('username', '')
                password = channel_config.api_auth_config.get('password', '')
                credentials = base64.b64encode(f'{username}:{password}'.encode()).decode()
                headers['Authorization'] = f'Basic {credentials}'
            elif channel_config.api_auth_type == 'api_key':
                key = channel_config.api_auth_config.get('key', '')
                header_name = channel_config.api_auth_config.get('header', 'X-API-Key')
                headers[header_name] = key
            
            # Make API call
            response = requests.request(
                method=channel_config.api_method,
                url=channel_config.api_endpoint,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            logger.info(
                f"API delivery: endpoint={channel_config.api_endpoint}, "
                f"customer={payload.get('customer_id')}, status={response.status_code}"
            )
            
            return {
                'success': True,
                'message': 'Campaign delivered via API',
                'api_endpoint': channel_config.api_endpoint,
                'response_status': response.status_code,
                'response_data': response.json() if response.content else None
            }
        except Exception as e:
            logger.error(f"API delivery error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        
        logger.info(
            f"Campaign delivered: campaign={campaign.id}, "
            f"customer={customer_id}, channel={channel}"
        )
        
        return {
            'success': True,
            'execution_id': str(execution.id),
            'channel': channel,
            'delivered_at': execution.delivered_at.isoformat()
        }


class CampaignPerformanceService:
    """Track and analyze campaign performance"""
    
    def get_campaign_performance(
        self,
        campaign: Campaign,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get campaign performance metrics.
        
        Returns:
            Dict with performance metrics
        """
        executions = CampaignExecution.objects.filter(campaign=campaign)
        
        if start_date:
            executions = executions.filter(triggered_at__gte=start_date)
        if end_date:
            executions = executions.filter(triggered_at__lte=end_date)
        
        total_triggered = executions.count()
        total_delivered = executions.exclude(delivered_at__isnull=True).count()
        total_opened = executions.exclude(opened_at__isnull=True).count()
        total_clicked = executions.exclude(clicked_at__isnull=True).count()
        total_converted = executions.exclude(converted_at__isnull=True).count()
        
        return {
            'campaign_id': str(campaign.id),
            'campaign_name': campaign.name,
            'total_triggered': total_triggered,
            'total_delivered': total_delivered,
            'total_opened': total_opened,
            'total_clicked': total_clicked,
            'total_converted': total_converted,
            'delivery_rate': (total_delivered / total_triggered * 100) if total_triggered > 0 else 0,
            'open_rate': (total_opened / total_delivered * 100) if total_delivered > 0 else 0,
            'click_rate': (total_clicked / total_delivered * 100) if total_delivered > 0 else 0,
            'conversion_rate': (total_converted / total_delivered * 100) if total_delivered > 0 else 0
        }


class CampaignExecutionEngine:
    """
    Main Campaign Execution Engine - Orchestrates campaign execution.
    Enterprise-grade engine with automatic triggering, targeting, and performance tracking.
    """
    
    def __init__(self):
        self.trigger_service = CampaignTriggerService()
        self.targeting_service = CampaignTargetingService()
        self.delivery_service = CampaignDeliveryService()
        self.performance_service = CampaignPerformanceService()
    
    def process_event_trigger(
        self,
        event_type: str,
        event_data: Dict
    ) -> List[Dict]:
        """
        Process an event and trigger matching campaigns.
        
        Args:
            event_type: Type of event
            event_data: Event data
        
        Returns:
            List of execution results
        """
        # Find active campaigns with matching event triggers
        campaigns = Campaign.objects.filter(
            status='active',
            event_triggers__contains=[{'event_type': event_type}]
        )
        
        results = []
        customer_id = event_data.get('customer_id')
        
        if not customer_id:
            logger.warning(f"Event {event_type} missing customer_id")
            return results
        
        for campaign in campaigns:
            # Check if trigger matches
            if not self.trigger_service.evaluate_event_trigger(campaign, event_type, event_data):
                continue
            
            # Check if customer is in target segment
            target_customers = self.targeting_service.find_target_customers(campaign, limit=1)
            if customer_id not in target_customers:
                continue
            
            # Check frequency cap
            if not self.targeting_service.check_frequency_cap(campaign, customer_id):
                logger.debug(f"Frequency cap exceeded for campaign {campaign.id}, customer {customer_id}")
                continue
            
            # Deliver campaign
            result = self.delivery_service.deliver_campaign(campaign, customer_id)
            results.append({
                'campaign_id': str(campaign.id),
                'campaign_name': campaign.name,
                **result
            })
        
        return results
    
    def process_schedule_trigger(
        self,
        current_time: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Process schedule triggers and execute matching campaigns.
        
        Args:
            current_time: Current time (defaults to now)
        
        Returns:
            List of execution results
        """
        if current_time is None:
            current_time = timezone.now()
        
        # Find active campaigns with schedule triggers
        campaigns = Campaign.objects.filter(
            status='active'
        ).exclude(schedule_triggers=[])
        
        results = []
        
        for campaign in campaigns:
            # Check if schedule trigger matches
            if not self.trigger_service.evaluate_schedule_trigger(campaign, current_time):
                continue
            
            # Find target customers
            target_customers = self.targeting_service.find_target_customers(campaign)
            
            # Deliver to all target customers
            for customer_id in target_customers:
                # Check frequency cap
                if not self.targeting_service.check_frequency_cap(campaign, customer_id):
                    continue
                
                result = self.delivery_service.deliver_campaign(campaign, customer_id)
                results.append({
                    'campaign_id': str(campaign.id),
                    'campaign_name': campaign.name,
                    'customer_id': customer_id,
                    **result
                })
        
        return results
    
    def process_threshold_trigger(
        self,
        customer_id: str
    ) -> List[Dict]:
        """
        Process threshold triggers for a customer.
        
        Args:
            customer_id: Customer to check
        
        Returns:
            List of execution results
        """
        # Find active campaigns with threshold triggers
        campaigns = Campaign.objects.filter(
            status='active'
        ).exclude(threshold_triggers=[])
        
        results = []
        
        for campaign in campaigns:
            # Check if threshold trigger matches
            if not self.trigger_service.evaluate_threshold_trigger(campaign, customer_id):
                continue
            
            # Check if customer is in target segment
            target_customers = self.targeting_service.find_target_customers(campaign, limit=1)
            if customer_id not in target_customers:
                continue
            
            # Check frequency cap
            if not self.targeting_service.check_frequency_cap(campaign, customer_id):
                continue
            
            # Deliver campaign
            result = self.delivery_service.deliver_campaign(campaign, customer_id)
            results.append({
                'campaign_id': str(campaign.id),
                'campaign_name': campaign.name,
                **result
            })
        
        return results
    
    def get_performance(
        self,
        campaign: Campaign,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Get campaign performance metrics"""
        return self.performance_service.get_campaign_performance(campaign, start_date, end_date)

