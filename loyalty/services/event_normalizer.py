"""
Event Normalization Service
Normalizes events from different data sources into a unified CustomerEvent structure.
"""
import logging
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from loyalty.models_khaywe import CustomerEvent, DataSourceConfig

logger = logging.getLogger(__name__)


class EventNormalizerService:
    """Service for normalizing events from different data sources"""
    
    def __init__(self):
        self.source_configs = {}
        self._load_source_configs()
    
    def _load_source_configs(self):
        """Load active data source configurations"""
        configs = DataSourceConfig.objects.filter(is_active=True)
        for config in configs:
            self.source_configs[config.source_type] = config
        logger.info(f"Loaded {len(self.source_configs)} active data source configurations")
    
    def normalize_event(
        self,
        source_type: str,
        raw_event: Dict[str, Any],
        customer_id: Optional[str] = None
    ) -> Optional[CustomerEvent]:
        """
        Normalize an event from a data source into CustomerEvent.
        
        Args:
            source_type: Type of data source (cdr, billing, app, crm, network)
            raw_event: Raw event data from the source
            customer_id: Customer ID (if not in raw_event)
        
        Returns:
            CustomerEvent instance or None if normalization fails
        """
        try:
            # Get source configuration
            config = self.source_configs.get(source_type)
            if not config:
                logger.warning(f"No configuration found for source type: {source_type}")
                return None
            
            # Apply event mapping
            mapped_event = self._apply_event_mapping(config.event_mapping, raw_event)
            
            # Extract customer ID
            if not customer_id:
                customer_id = mapped_event.get('customer_id') or raw_event.get('customer_id') or raw_event.get('user_id')
            
            if not customer_id:
                logger.warning(f"Could not extract customer_id from event: {raw_event}")
                return None
            
            # Extract event type
            event_type = mapped_event.get('event_type') or self._infer_event_type(source_type, raw_event)
            
            # Extract value
            value = self._extract_value(mapped_event, raw_event)
            
            # Extract timestamp
            timestamp = self._extract_timestamp(mapped_event, raw_event)
            
            # Extract metadata
            metadata = self._extract_metadata(mapped_event, raw_event)
            
            # Create normalized event
            normalized_event = CustomerEvent.objects.create(
                customer_id=customer_id,
                event_type=event_type,
                value=value,
                timestamp=timestamp,
                source=source_type,
                source_event_id=str(raw_event.get('id') or raw_event.get('event_id', '')),
                metadata=metadata,
                processed=False
            )
            
            logger.debug(f"Normalized event: {customer_id} - {event_type} - {timestamp}")
            return normalized_event
            
        except Exception as e:
            logger.error(f"Error normalizing event from {source_type}: {e}", exc_info=True)
            return None
    
    def _apply_event_mapping(self, mapping: Dict, raw_event: Dict) -> Dict:
        """Apply event mapping configuration to raw event"""
        if not mapping:
            return raw_event
        
        mapped = {}
        for target_field, source_path in mapping.items():
            value = self._get_nested_value(raw_event, source_path)
            if value is not None:
                mapped[target_field] = value
        
        # Merge with original event (mapped values take precedence)
        return {**raw_event, **mapped}
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get nested value from dict using dot notation (e.g., 'user.id')"""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
            if value is None:
                return None
        return value
    
    def _infer_event_type(self, source_type: str, raw_event: Dict) -> str:
        """Infer event type from source and raw event"""
        # CDR events
        if source_type == 'cdr':
            if raw_event.get('call_type') == 'outgoing':
                return 'CALL_OUTGOING'
            elif raw_event.get('call_type') == 'incoming':
                return 'CALL_INCOMING'
            elif raw_event.get('data_usage'):
                return 'DATA_USAGE'
            elif raw_event.get('sms_type') == 'sent':
                return 'SMS_SENT'
            elif raw_event.get('sms_type') == 'received':
                return 'SMS_RECEIVED'
        
        # Billing events
        elif source_type == 'billing':
            if raw_event.get('transaction_type') == 'recharge':
                return 'RECHARGE'
            elif raw_event.get('transaction_type') == 'top_up':
                return 'TOP_UP'
            elif raw_event.get('bundle_purchase'):
                return 'BUNDLE_PURCHASE'
            elif raw_event.get('payment'):
                return 'PAYMENT'
        
        # App events
        elif source_type == 'app':
            if raw_event.get('action') == 'login':
                return 'APP_LOGIN'
            elif raw_event.get('action') == 'feature_use':
                return 'APP_FEATURE_USE'
            elif raw_event.get('action') == 'content_view':
                return 'CONTENT_VIEW'
        
        # CRM events
        elif source_type == 'crm':
            if raw_event.get('event') == 'activation':
                return 'ACTIVATION'
            elif raw_event.get('event') == 'status_change':
                return 'STATUS_CHANGE'
            elif raw_event.get('event') == 'profile_update':
                return 'PROFILE_UPDATE'
        
        # Network events
        elif source_type == 'network':
            if raw_event.get('qoe_issue'):
                return 'QOE_ISSUE'
            else:
                return 'NETWORK_EVENT'
        
        return 'CUSTOM'
    
    def _extract_value(self, mapped_event: Dict, raw_event: Dict) -> Optional[Decimal]:
        """Extract numeric value from event"""
        # Try mapped value first
        value = mapped_event.get('value')
        if value is not None:
            try:
                return Decimal(str(value))
            except (ValueError, TypeError):
                pass
        
        # Try common field names
        for field in ['amount', 'value', 'usage', 'data_usage', 'duration', 'count']:
            if field in raw_event:
                try:
                    return Decimal(str(raw_event[field]))
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_timestamp(self, mapped_event: Dict, raw_event: Dict) -> timezone.datetime:
        """Extract timestamp from event"""
        # Try mapped timestamp
        timestamp = mapped_event.get('timestamp')
        if timestamp:
            if isinstance(timestamp, str):
                try:
                    return timezone.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
        
        # Try common field names
        for field in ['timestamp', 'event_time', 'created_at', 'date', 'time']:
            if field in raw_event:
                value = raw_event[field]
                if isinstance(value, str):
                    try:
                        return timezone.datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        continue
                elif isinstance(value, timezone.datetime):
                    return value
        
        # Default to now
        return timezone.now()
    
    def _extract_metadata(self, mapped_event: Dict, raw_event: Dict) -> Dict:
        """Extract metadata from event"""
        metadata = {}
        
        # Common metadata fields
        metadata_fields = [
            'duration', 'destination', 'product', 'bundle', 'channel',
            'device', 'location', 'quality', 'error', 'status', 'description'
        ]
        
        for field in metadata_fields:
            if field in raw_event:
                metadata[field] = raw_event[field]
        
        # Add any additional fields from mapped event
        if 'metadata' in mapped_event:
            metadata.update(mapped_event['metadata'])
        
        return metadata
    
    def normalize_batch(
        self,
        source_type: str,
        raw_events: List[Dict[str, Any]]
    ) -> List[CustomerEvent]:
        """Normalize a batch of events"""
        normalized = []
        for raw_event in raw_events:
            event = self.normalize_event(source_type, raw_event)
            if event:
                normalized.append(event)
        return normalized
    
    def mark_processed(self, event: CustomerEvent):
        """Mark an event as processed"""
        event.processed = True
        event.processed_at = timezone.now()
        event.save(update_fields=['processed', 'processed_at'])
    
    def mark_batch_processed(self, events: List[CustomerEvent]):
        """Mark a batch of events as processed"""
        with transaction.atomic():
            for event in events:
                self.mark_processed(event)

