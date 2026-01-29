"""
Webhook endpoints for receiving customer events from external systems.
No Kafka required - uses simple HTTP POST endpoints.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging

from loyalty.models_khaywe import CustomerEvent, DataSourceConfig
from loyalty.services.event_normalizer import EventNormalizerService
from loyalty.services.behavior_scoring import BehaviorScoringService

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class CustomerEventWebhookView(View):
    """
    Webhook endpoint for receiving customer events from external systems.
    
    POST /api/loyalty/v1/webhooks/customer-events/
    
    Request body:
    {
        "source": "cdr" | "billing" | "crm" | "app" | "network" | "custom",
        "source_name": "CDR System",  // Optional: name of the data source config
        "event": {
            "customer_id": "uuid-or-msisdn",
            "event_type": "data_usage" | "recharge" | "app_login" | etc.,
            "timestamp": "2024-01-01T12:00:00Z",
            "value": 100.5,  // Optional: numeric value
            "metadata": {}  // Optional: additional event data
        }
    }
    
    Response:
    {
        "status": "success",
        "event_id": "uuid",
        "customer_id": "uuid",
        "event_type": "data_usage"
    }
    """
    
    def post(self, request):
        try:
            # Parse request body
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
            
            source_type = data.get('source', 'custom')
            source_name = data.get('source_name')
            raw_event = data.get('event', {})
            
            if not raw_event:
                return Response({
                    'error': 'Missing "event" in request body'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get or create data source config
            source_config = None
            if source_name:
                try:
                    source_config = DataSourceConfig.objects.get(name=source_name, is_active=True)
                except DataSourceConfig.DoesNotExist:
                    logger.warning(f"Data source config '{source_name}' not found, using default mapping")
            
            # Normalize event
            normalizer = EventNormalizerService()
            
            if source_config:
                # Use configured mapping
                normalized_event = normalizer.normalize_event(raw_event, source_config.name)
            else:
                # Use default mapping (direct field mapping)
                try:
                    from django.utils import timezone
                    from decimal import Decimal
                    
                    customer_id = raw_event.get('customer_id')
                    event_type = raw_event.get('event_type', 'custom')
                    timestamp_str = raw_event.get('timestamp')
                    value = raw_event.get('value')
                    
                    if not customer_id or not timestamp_str:
                        return Response({
                            'error': 'Missing required fields: customer_id, timestamp'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Parse timestamp
                    try:
                        from dateutil import parser
                        timestamp = parser.parse(timestamp_str)
                    except:
                        timestamp = timezone.now()
                    
                    # Create event
                    normalized_event = CustomerEvent.objects.create(
                        customer_id=customer_id,
                        event_type=event_type,
                        value=Decimal(str(value)) if value is not None else None,
                        metadata=raw_event.get('metadata', {}),
                        timestamp=timestamp,
                        source=source_config
                    )
                except Exception as e:
                    logger.error(f"Error creating customer event: {e}")
                    return Response({
                        'error': f'Failed to create event: {str(e)}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            if not normalized_event:
                return Response({
                    'error': 'Failed to normalize event'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Trigger behavior scoring update (async in production)
            try:
                scoring_service = BehaviorScoringService()
                scoring_service.calculate_all_scores_for_customer(str(normalized_event.customer_id))
            except Exception as e:
                logger.warning(f"Error calculating behavior scores: {e}")
                # Don't fail the webhook if scoring fails
            
            return Response({
                'status': 'success',
                'event_id': str(normalized_event.id),
                'customer_id': str(normalized_event.customer_id),
                'event_type': normalized_event.event_type,
                'timestamp': normalized_event.timestamp.isoformat(),
            }, status=status.HTTP_201_CREATED)
            
        except json.JSONDecodeError:
            return Response({
                'error': 'Invalid JSON in request body'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return Response({
                'error': f'Internal server error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        """Return webhook documentation"""
        return Response({
            'endpoint': '/api/loyalty/v1/webhooks/customer-events/',
            'method': 'POST',
            'description': 'Receive customer events from external systems',
            'request_format': {
                'source': 'cdr | billing | crm | app | network | custom',
                'source_name': 'Optional: name of data source config',
                'event': {
                    'customer_id': 'Required: customer UUID or MSISDN',
                    'event_type': 'Required: event type (data_usage, recharge, app_login, etc.)',
                    'timestamp': 'Required: ISO 8601 timestamp',
                    'value': 'Optional: numeric value',
                    'metadata': 'Optional: additional event data'
                }
            },
            'response_format': {
                'status': 'success',
                'event_id': 'UUID of created event',
                'customer_id': 'Customer ID',
                'event_type': 'Event type',
                'timestamp': 'ISO 8601 timestamp'
            }
        })


class WebhookViewSet(viewsets.ViewSet):
    """Webhook management endpoints"""
    
    @action(detail=False, methods=['get'], url_path='info')
    def webhook_info(self, request):
        """Get webhook endpoint information"""
        base_url = request.build_absolute_uri('/').rstrip('/')
        webhook_url = f"{base_url}/api/loyalty/v1/webhooks/customer-events/"
        
        return Response({
            'webhook_url': webhook_url,
            'method': 'POST',
            'description': 'Send customer events to this endpoint for gamification',
            'authentication': 'None required (can be added via middleware)',
            'example_request': {
                'source': 'cdr',
                'source_name': 'CDR System',
                'event': {
                    'customer_id': '123e4567-e89b-12d3-a456-426614174000',
                    'event_type': 'data_usage',
                    'timestamp': '2024-01-01T12:00:00Z',
                    'value': 100.5,
                    'metadata': {
                        'data_mb': 100.5,
                        'network_type': '4G'
                    }
                }
            },
            'supported_event_types': [
                'data_usage',
                'recharge',
                'app_login',
                'call_outgoing',
                'bundle_purchase',
                'kyc_update',
                'feature_usage',
                'qoe_issue',
                'custom'
            ]
        })

