"""
Django management command to run the Kafka consumer service.

Usage:
    python manage.py run_kafka_consumer
"""
from django.core.management.base import BaseCommand
from loyalty.integration.kafka_consumer_service import KafkaConsumerService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run Kafka consumer for processing customer events'

    def add_arguments(self, parser):
        parser.add_argument(
            '--topics',
            nargs='+',
            help='Kafka topics to consume from (default: customer-events)',
            default=['customer-events']
        )
        parser.add_argument(
            '--bootstrap-servers',
            nargs='+',
            help='Kafka bootstrap servers (default: localhost:9092)',
            default=['localhost:9092']
        )
        parser.add_argument(
            '--consumer-group',
            type=str,
            help='Consumer group ID (default: loyalty-gamification-consumer)',
            default='loyalty-gamification-consumer'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Kafka consumer...'))
        
        try:
            # Override settings if provided
            if options['topics']:
                from django.conf import settings
                settings.KAFKA_CUSTOMER_EVENTS_TOPICS = options['topics']
            
            if options['bootstrap_servers']:
                from django.conf import settings
                settings.KAFKA_BOOTSTRAP_SERVERS = options['bootstrap_servers']
            
            if options['consumer_group']:
                from django.conf import settings
                settings.KAFKA_CONSUMER_GROUP = options['consumer_group']
            
            # Start consumer
            service = KafkaConsumerService()
            service.start()
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nShutting down consumer...'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            raise

