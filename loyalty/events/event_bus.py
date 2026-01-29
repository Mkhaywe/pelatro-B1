"""
Enterprise-Grade Event Bus
Publishes and subscribes to events for event-driven architecture.
"""
import logging
import json
from typing import Dict, List, Optional, Callable, Any
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Try to import Kafka
try:
    from confluent_kafka import Producer, Consumer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    Producer = None
    Consumer = None


class EventPublisher:
    """Publish events to event bus"""
    
    def __init__(self):
        self.kafka_enabled = getattr(settings, 'LOYALTY_KAFKA_ENABLED', False)
        self.producer = None
        
        if self.kafka_enabled and KAFKA_AVAILABLE:
            try:
                self.producer = Producer({
                    'bootstrap.servers': settings.LOYALTY_KAFKA_BOOTSTRAP_SERVERS
                })
            except Exception as e:
                logger.error(f"Failed to create Kafka producer: {e}")
                self.producer = None
    
    def publish(
        self,
        event_type: str,
        event_data: Dict,
        topic: Optional[str] = None
    ) -> bool:
        """
        Publish an event.
        
        Args:
            event_type: Type of event (e.g., 'customer.purchase')
            event_data: Event data
            topic: Kafka topic (defaults to event_type)
        
        Returns:
            True if published successfully
        """
        if not topic:
            topic = event_type
        
        event = {
            'event_type': event_type,
            'timestamp': timezone.now().isoformat(),
            'data': event_data
        }
        
        # Publish to Kafka if enabled
        if self.kafka_enabled and self.producer:
            try:
                self.producer.produce(
                    topic,
                    json.dumps(event).encode('utf-8')
                )
                self.producer.flush(1)
                logger.debug(f"Event published: {event_type} to {topic}")
                return True
            except Exception as e:
                logger.error(f"Failed to publish event to Kafka: {e}")
                return False
        
        # Fallback: log event (for development/testing)
        logger.info(f"Event (not published): {event_type} - {json.dumps(event_data)}")
        return True
    
    def publish_customer_event(
        self,
        customer_id: str,
        event_type: str,
        event_data: Dict
    ):
        """Publish a customer-related event"""
        event_data['customer_id'] = customer_id
        return self.publish(event_type, event_data)
    
    def publish_points_event(
        self,
        customer_id: str,
        points: int,
        transaction_type: str,
        metadata: Dict
    ):
        """Publish a points-related event"""
        return self.publish(
            f'points.{transaction_type}',
            {
                'customer_id': customer_id,
                'points': points,
                **metadata
            }
        )
    
    def publish_campaign_event(
        self,
        campaign_id: str,
        customer_id: str,
        event_type: str,
        metadata: Dict
    ):
        """Publish a campaign-related event"""
        return self.publish(
            f'campaign.{event_type}',
            {
                'campaign_id': campaign_id,
                'customer_id': customer_id,
                **metadata
            }
        )


class EventSubscriber:
    """Subscribe to events from event bus"""
    
    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = {}
        self.kafka_enabled = getattr(settings, 'LOYALTY_KAFKA_ENABLED', False)
        self.consumer = None
        
        if self.kafka_enabled and KAFKA_AVAILABLE:
            try:
                self.consumer = Consumer({
                    'bootstrap.servers': settings.LOYALTY_KAFKA_BOOTSTRAP_SERVERS,
                    'group.id': getattr(settings, 'LOYALTY_KAFKA_GROUP_ID', 'loyalty-service'),
                    'auto.offset.reset': 'earliest'
                })
            except Exception as e:
                logger.error(f"Failed to create Kafka consumer: {e}")
                self.consumer = None
    
    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Dict], None]
    ):
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Handler function
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.info(f"Subscribed to event: {event_type}")
    
    def handle_event(
        self,
        event_type: str,
        event_data: Dict
    ):
        """Handle an event by calling registered handlers"""
        handlers = self.handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                handler(event_data)
            except Exception as e:
                logger.error(f"Error handling event {event_type}: {e}", exc_info=True)
    
    def start_consuming(
        self,
        topics: List[str],
        timeout: float = 1.0
    ):
        """
        Start consuming events from Kafka.
        
        Args:
            topics: List of topics to consume
            timeout: Poll timeout in seconds
        """
        if not self.kafka_enabled or not self.consumer:
            logger.warning("Kafka not enabled or consumer not available")
            return
        
        self.consumer.subscribe(topics)
        logger.info(f"Started consuming from topics: {topics}")
        
        try:
            while True:
                msg = self.consumer.poll(timeout)
                if msg is None:
                    continue
                if msg.error():
                    logger.error(f"Kafka error: {msg.error()}")
                    continue
                
                try:
                    event = json.loads(msg.value().decode('utf-8'))
                    event_type = event.get('event_type')
                    event_data = event.get('data', {})
                    
                    self.handle_event(event_type, event_data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
        except KeyboardInterrupt:
            logger.info("Stopping event consumer")
        finally:
            self.consumer.close()


class EventStore:
    """Store events for replay and audit"""
    
    def store_event(
        self,
        event_type: str,
        event_data: Dict,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Store an event.
        
        Returns:
            Event ID
        """
        # In real implementation, store in database or event store
        # For now, just log
        logger.debug(f"Event stored: {event_type}")
        return f"event_{timezone.now().timestamp()}"


# Global instances
_event_publisher = None
_event_subscriber = None


def get_event_publisher() -> EventPublisher:
    """Get global event publisher instance"""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = EventPublisher()
    return _event_publisher


def get_event_subscriber() -> EventSubscriber:
    """Get global event subscriber instance"""
    global _event_subscriber
    if _event_subscriber is None:
        _event_subscriber = EventSubscriber()
    return _event_subscriber

