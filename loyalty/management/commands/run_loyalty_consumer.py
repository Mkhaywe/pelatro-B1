"""
Management command to run the loyalty Kafka consumer.

Usage:
    python manage.py run_loyalty_consumer

Notes:
- Requires LOYALTY_KAFKA_ENABLED=True and proper bootstrap servers/topics.
- Uses the handlers defined in loyalty.integration.kafka_handlers.
"""

from django.core.management.base import BaseCommand
from loyalty.integration.kafka_handlers import consume_loop


class Command(BaseCommand):
    help = "Run loyalty Kafka consumer loop"

    def add_arguments(self, parser):
        parser.add_argument(
            "--max-messages",
            type=int,
            default=None,
            help="Max messages to process before exiting (for testing)",
        )
        parser.add_argument(
            "--timeout",
            type=float,
            default=1.0,
            help="Poll timeout seconds",
        )

    def handle(self, *args, **options):
        max_messages = options.get("max_messages")
        timeout = options.get("timeout") or 1.0
        self.stdout.write(self.style.SUCCESS("Starting loyalty Kafka consumer..."))
        consume_loop(timeout_s=timeout, max_messages=max_messages)
        self.stdout.write(self.style.SUCCESS("Loyalty Kafka consumer stopped."))



