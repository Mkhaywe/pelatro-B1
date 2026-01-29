"""
Kafka Consumer Service for Gamification Events

This service consumes customer events from Kafka topics and processes them
for gamification (missions, badges, leaderboards, behavior scoring).

Usage:
    # Start consumer as a management command:
    python manage.py run_kafka_consumer

    # Or run as a service:
    from loyalty.integration.kafka_consumer_service import KafkaConsumerService
    service = KafkaConsumerService()
    service.start()
"""
import json
import logging
import signal
import sys
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Try to import Kafka libraries
try:
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("kafka-python not installed. Install with: pip install kafka-python")
    KafkaConsumer = None


class KafkaConsumerService:
    """
    Kafka consumer service for processing customer events.
    
    Consumes events from Kafka topics and processes them through:
    1. Event normalization
    2. Behavior scoring
    3. Gamification updates (missions, badges, leaderboards)
    """
    
    def __init__(self):
        if not KAFKA_AVAILABLE:
            raise ImportError("kafka-python library not installed. Install with: pip install kafka-python")
        
        self.consumer = None
        self.running = False
        self.topics = getattr(settings, 'KAFKA_CUSTOMER_EVENTS_TOPICS', ['customer-events'])
        self.bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', ['localhost:9092'])
        self.consumer_group = getattr(settings, 'KAFKA_CONSUMER_GROUP', 'loyalty-gamification-consumer')
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down consumer...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Start consuming events from Kafka"""
        if self.running:
            logger.warning("Consumer is already running")
            return
        
        try:
            logger.info(f"Starting Kafka consumer for topics: {self.topics}")
            logger.info(f"Bootstrap servers: {self.bootstrap_servers}")
            logger.info(f"Consumer group: {self.consumer_group}")
            
            # Create consumer
            self.consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',  # Start from latest if no offset
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                consumer_timeout_ms=1000,  # Timeout for polling
            )
            
            self.running = True
            logger.info("Kafka consumer started successfully")
            
            # Consume messages
            self._consume_loop()
            
        except Exception as e:
            logger.error(f"Error starting Kafka consumer: {e}", exc_info=True)
            raise
        finally:
            self.stop()
    
    def _consume_loop(self):
        """Main consumption loop"""
        processed_count = 0
        error_count = 0
        
        while self.running:
            try:
                # Poll for messages (non-blocking with timeout)
                message_pack = self.consumer.poll(timeout_ms=1000)
                
                if not message_pack:
                    continue
                
                # Process each message
                for topic_partition, messages in message_pack.items():
                    for message in messages:
                        try:
                            self._process_message(message)
                            processed_count += 1
                            
                            if processed_count % 100 == 0:
                                logger.info(f"Processed {processed_count} events")
                                
                        except Exception as e:
                            error_count += 1
                            logger.error(
                                f"Error processing message from {topic_partition}: {e}",
                                exc_info=True
                            )
                            
                            # TODO: Send to dead letter queue or retry topic
                            
            except KafkaError as e:
                logger.error(f"Kafka error: {e}", exc_info=True)
                error_count += 1
                # Continue processing other messages
                
            except Exception as e:
                logger.error(f"Unexpected error in consume loop: {e}", exc_info=True)
                error_count += 1
                # Continue processing
        
        logger.info(f"Consumer stopped. Processed: {processed_count}, Errors: {error_count}")
    
    def _process_message(self, message):
        """
        Process a single Kafka message.
        
        Args:
            message: Kafka message object with value, key, topic, partition, offset
        """
        try:
            event_data = message.value
            topic = message.topic
            partition = message.partition
            offset = message.offset
            
            logger.debug(f"Processing event from {topic}[{partition}]:{offset}")
            
            # Extract source information
            source = event_data.get('source', 'unknown')
            source_name = event_data.get('source_name')
            
            # Get or use default data source config
            from loyalty.models_khaywe import DataSourceConfig
            source_config = None
            if source_name:
                try:
                    source_config = DataSourceConfig.objects.get(
                        name=source_name,
                        is_active=True
                    )
                except DataSourceConfig.DoesNotExist:
                    logger.warning(f"Data source config '{source_name}' not found")
            
            # Normalize event
            from loyalty.services.event_normalizer import EventNormalizerService
            normalizer = EventNormalizerService()
            
            if source_config:
                normalized_event = normalizer.normalize_event(event_data, source_config.name)
            else:
                # Use default normalization (direct mapping)
                normalized_event = self._normalize_event_default(event_data)
            
            if not normalized_event:
                logger.warning(f"Failed to normalize event: {event_data}")
                return
            
            # Update behavior scores
            from loyalty.services.behavior_scoring import BehaviorScoringService
            scoring_service = BehaviorScoringService()
            
            try:
                scoring_service.calculate_all_scores_for_customer(
                    str(normalized_event.customer_id)
                )
            except Exception as e:
                logger.warning(f"Error calculating behavior scores: {e}")
                # Don't fail the event processing if scoring fails
            
            # Trigger gamification updates
            # (This would trigger mission progress, badge checks, leaderboard updates)
            # TODO: Implement gamification trigger service
            
            logger.debug(f"Successfully processed event {normalized_event.id}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            raise
    
    def _normalize_event_default(self, event_data: Dict[str, Any]):
        """
        Default event normalization when no DataSourceConfig is found.
        Assumes event_data already has normalized fields.
        """
        from loyalty.models_khaywe import CustomerEvent
        from decimal import Decimal
        
        customer_id = event_data.get('customer_id')
        event_type = event_data.get('event_type', 'custom')
        timestamp_str = event_data.get('timestamp')
        value = event_data.get('value')
        metadata = event_data.get('metadata', {})
        
        if not customer_id or not timestamp_str:
            logger.warning(f"Missing required fields in event: {event_data}")
            return None
        
        # Parse timestamp
        try:
            from dateutil import parser
            timestamp = parser.parse(timestamp_str)
        except:
            timestamp = timezone.now()
        
        # Create event
        try:
            normalized_event = CustomerEvent.objects.create(
                customer_id=customer_id,
                event_type=event_type,
                value=Decimal(str(value)) if value is not None else None,
                metadata=metadata,
                timestamp=timestamp,
                source=None  # No source config
            )
            return normalized_event
        except Exception as e:
            logger.error(f"Error creating CustomerEvent: {e}")
            return None
    
    def stop(self):
        """Stop the consumer gracefully"""
        if not self.running:
            return
        
        logger.info("Stopping Kafka consumer...")
        self.running = False
        
        if self.consumer:
            try:
                self.consumer.close()
                logger.info("Kafka consumer closed")
            except Exception as e:
                logger.error(f"Error closing consumer: {e}")


def start_consumer():
    """Convenience function to start the consumer"""
    service = KafkaConsumerService()
    service.start()


if __name__ == '__main__':
    # Can be run directly for testing
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
    django.setup()
    
    start_consumer()

