"""
Kafka integration for the loyalty microservice.

Provides consumer handlers for inbound events and producer helpers
for emitting loyalty events. Designed to be generic so any BSS/CRM
can integrate by publishing to the agreed topics.
"""

import json
import logging
from typing import Any, Callable, Dict, Iterable, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from confluent_kafka import Consumer, Producer  # type: ignore
except ImportError:
    Consumer = None
    Producer = None


# ---------------------------------------------------------------------------
# Producer helpers
# ---------------------------------------------------------------------------

def _producer() -> Optional[Producer]:
    if not getattr(settings, "LOYALTY_KAFKA_ENABLED", False):
        return None
    if Producer is None:
        logger.warning("confluent-kafka not installed; Kafka producer disabled")
        return None
    return Producer({"bootstrap.servers": settings.LOYALTY_KAFKA_BOOTSTRAP_SERVERS})


def _emit(topic: str, payload: Dict[str, Any]) -> None:
    p = _producer()
    if not p:
        return
    p.produce(topic, json.dumps(payload).encode("utf-8"))
    p.flush(1)


def emit_points_earned(event: Dict[str, Any]) -> None:
    _emit(settings.LOYALTY_TOPIC_POINTS_EARNED, event)


def emit_points_redeemed(event: Dict[str, Any]) -> None:
    _emit(settings.LOYALTY_TOPIC_POINTS_REDEEMED, event)


def emit_promotion_applied(event: Dict[str, Any]) -> None:
    _emit(settings.LOYALTY_TOPIC_PROMOTION_APPLIED, event)


# ---------------------------------------------------------------------------
# Consumer handlers (inbound)
# ---------------------------------------------------------------------------

def handle_customer_created(event: Dict[str, Any]) -> None:
    """
    Example handler for customer.created events.
    Extend to preload/customer shadow models if desired.
    """
    logger.info("customer.created received: %s", event)


def handle_billing_invoice_created(event: Dict[str, Any]) -> None:
    """
    billing.invoice.created:
    {
        "customer_id": "...",
        "invoice_id": "...",
        "amount": 123.45,
        "due_date": "...",
        "status": "created"
    }
    """
    logger.info("billing.invoice.created received: %s", event)
    # TODO: apply earning rules or trigger promotions based on invoice events


def handle_payment_completed(event: Dict[str, Any]) -> None:
    """
    billing.payment.completed:
    {
        "customer_id": "...",
        "payment_id": "...",
        "amount": 123.45,
        "timestamp": "..."
    }
    """
    logger.info("billing.payment.completed received: %s", event)
    # TODO: award on-time payment bonus, trigger promotions


def handle_usage_threshold(event: Dict[str, Any]) -> None:
    """
    usage.threshold.exceeded:
    {
        "customer_id": "...",
        "usage_type": "data",
        "threshold": "80%",
        "timestamp": "..."
    }
    """
    logger.info("usage.threshold.exceeded received: %s", event)
    # TODO: trigger usage-based promotions


HANDLERS: Dict[str, Callable[[Dict[str, Any]], None]] = {
    getattr(settings, "LOYALTY_TOPIC_CUSTOMER_CREATED", "customer.created"): handle_customer_created,
    getattr(settings, "LOYALTY_TOPIC_BILLING_INVOICE_CREATED", "billing.invoice.created"): handle_billing_invoice_created,
    getattr(settings, "LOYALTY_TOPIC_PAYMENT_COMPLETED", "billing.payment.completed"): handle_payment_completed,
    getattr(settings, "LOYALTY_TOPIC_USAGE_THRESHOLD", "usage.threshold.exceeded"): handle_usage_threshold,
}

# Import DWH handlers (will merge into HANDLERS)
try:
    from loyalty.integration.kafka_dwh import DWH_HANDLERS
    HANDLERS.update(DWH_HANDLERS)
except ImportError:
    logger.warning("DWH Kafka handlers not available")


# ---------------------------------------------------------------------------
# Consumer loop
# ---------------------------------------------------------------------------

def consume_loop(timeout_s: float = 1.0, max_messages: Optional[int] = None) -> None:
    if not getattr(settings, "LOYALTY_KAFKA_ENABLED", False):
        logger.info("Kafka disabled via settings")
        return
    if Consumer is None:
        logger.warning("confluent-kafka not installed; cannot start consumer")
        return

    topics = list(HANDLERS.keys())
    c = Consumer(
        {
            "bootstrap.servers": settings.LOYALTY_KAFKA_BOOTSTRAP_SERVERS,
            "group.id": settings.LOYALTY_KAFKA_GROUP_ID,
            "auto.offset.reset": "earliest",
        }
    )
    c.subscribe(topics)
    logger.info("Kafka consumer subscribed to %s", topics)

    count = 0
    try:
        while True:
            msg = c.poll(timeout_s)
            if msg is None:
                continue
            if msg.error():
                logger.error("Kafka error: %s", msg.error())
                continue
            try:
                payload = json.loads(msg.value().decode("utf-8"))
                handler = HANDLERS.get(msg.topic())
                if handler:
                    handler(payload)
                else:
                    logger.debug("No handler for topic %s", msg.topic())
            except Exception as exc:  # pragma: no cover - log-only
                logger.exception("Failed to process message on %s: %s", msg.topic(), exc)

            count += 1
            if max_messages is not None and count >= max_messages:
                break
    finally:
        c.close()



