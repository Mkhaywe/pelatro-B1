"""
Kafka integration for DWH events.
Consumes events from DWH (via Kafka) and triggers loyalty actions.
"""

from typing import Dict
from loyalty.integration.feature_store import FeatureStore
from loyalty.services.segmentation import SegmentationEngine
from loyalty.ml.inference import MLInferenceService
from loyalty.integration.kafka_handlers import HANDLERS
import logging

logger = logging.getLogger(__name__)


def handle_dwh_customer_updated(event: Dict):
    """Handle DWH customer update event"""
    customer_id = event.get('customer_id')
    
    if not customer_id:
        logger.warning("DWH customer update event missing customer_id")
        return
    
    # Invalidate feature cache
    FeatureStore.invalidate_cache(customer_id)
    
    # Recalculate segment memberships for dynamic segments
    from loyalty.models_khaywe import Segment
    segments = Segment.objects.filter(is_active=True, is_dynamic=True)
    
    for segment in segments:
        try:
            SegmentationEngine.update_segment_membership(segment, [customer_id])
        except Exception as e:
            logger.error(f"Error updating segment {segment.id} for customer {customer_id}: {e}")
    
    logger.info(f"Processed DWH customer update: {customer_id}")


def handle_dwh_transaction_event(event: Dict):
    """Handle DWH transaction event"""
    customer_id = event.get('customer_id')
    
    if not customer_id:
        logger.warning("DWH transaction event missing customer_id")
        return
    
    # Invalidate cache
    FeatureStore.invalidate_cache(customer_id)
    
    # Trigger ML predictions
    try:
        ml_service = MLInferenceService()
        nbo = ml_service.predict_nbo(customer_id)
        churn = ml_service.predict_churn(customer_id)
        
        # Store predictions in loyalty DB
        from loyalty.models import LoyaltyEvent
        LoyaltyEvent.objects.create(
            account=None,
            event_type='ml_prediction',
            description=f'NBO: {nbo.get("recommended_offer")}, Churn: {churn.get("churn_risk")}',
            metadata={
                'nbo': nbo,
                'churn': churn,
                'source': 'dwh_transaction_event'
            }
        )
        
        logger.info(f"Processed DWH transaction event: {customer_id}")
    except Exception as e:
        logger.error(f"Error processing DWH transaction event: {e}")


def handle_dwh_segment_recalculate(event: Dict):
    """Handle DWH segment recalculation request"""
    segment_id = event.get('segment_id')
    
    if not segment_id:
        logger.warning("DWH segment recalculate event missing segment_id")
        return
    
    try:
        from loyalty.models_khaywe import Segment
        segment = Segment.objects.get(id=segment_id)
        SegmentationEngine.update_segment_membership(segment)
        logger.info(f"Recalculated segment {segment_id} from DWH event")
    except Segment.DoesNotExist:
        logger.error(f"Segment {segment_id} not found")
    except Exception as e:
        logger.error(f"Error recalculating segment {segment_id}: {e}")


# Register DWH event handlers
DWH_HANDLERS = {
    'dwh.customer.updated': handle_dwh_customer_updated,
    'dwh.transaction.created': handle_dwh_transaction_event,
    'dwh.segment.recalculate': handle_dwh_segment_recalculate,
}

# Merge with existing handlers
HANDLERS.update(DWH_HANDLERS)

