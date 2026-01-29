import logging
from typing import Any, Dict, Optional

from django.apps import apps as django_apps

logger = logging.getLogger(__name__)


def emit_audit_event(
    action: str,
    object_type: str,
    object_id: str,
    details: Dict[str, Any],
    status: str = "success",
    actor_id: Optional[str] = None,
) -> None:
    """
    Minimal local replacement for the monolith's common.audit_bus.emit_audit_event.

    Writes to the local AuditLog model only. Can later be extended to emit
    Kafka events or forward to a central audit service.
    """
    try:
        AuditLog = django_apps.get_model("loyalty", "AuditLog")
        AuditLog.objects.create(
            action=action,
            object_type=object_type,
            object_id=object_id,
            changes=str(details),
        )
    except Exception as exc:  # pragma: no cover - best-effort logging only
        logger.warning("Failed to emit audit event %s %s: %s", object_type, object_id, exc)



