"""
API endpoints for DWH integration.
"""

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework import status
from loyalty.integration.feature_store import FeatureStore
from loyalty.ml.inference import MLInferenceService
from loyalty.services.segmentation import SegmentationEngine
import logging

logger = logging.getLogger(__name__)


class DWHIntegrationViewSet(ViewSet):
    """DWH integration endpoints"""
    
    @action(detail=False, methods=['get'], url_path='features/(?P<customer_id>[^/.]+)')
    def get_customer_features(self, request, customer_id=None):
        """Get customer features from DWH"""
        try:
            features = FeatureStore.get_customer_features(customer_id)
            return Response(features)
        except Exception as e:
            logger.error(f"Error fetching features: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='features/batch')
    def batch_get_features(self, request):
        """Batch get features for multiple customers"""
        customer_ids = request.data.get('customer_ids', [])
        if not customer_ids:
            return Response({'error': 'customer_ids required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            features = FeatureStore.batch_get_features(customer_ids)
            return Response(features)
        except Exception as e:
            logger.error(f"Error batch fetching features: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='cache/invalidate')
    def invalidate_cache(self, request):
        """Invalidate feature cache for customer(s)"""
        customer_id = request.data.get('customer_id')
        customer_ids = request.data.get('customer_ids', [])
        
        if customer_id:
            customer_ids.append(customer_id)
        
        if not customer_ids:
            return Response({'error': 'customer_id or customer_ids required'}, status=status.HTTP_400_BAD_REQUEST)
        
        for cid in customer_ids:
            FeatureStore.invalidate_cache(cid)
        
        return Response({'status': 'success', 'invalidated': len(customer_ids)})
    
    @action(detail=False, methods=['post'], url_path='ml/nbo')
    def predict_nbo(self, request):
        """Predict Next Best Offer"""
        customer_id = request.data.get('customer_id')
        if not customer_id:
            return Response({'error': 'customer_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            ml_service = MLInferenceService()
            result = ml_service.predict_nbo(customer_id)
            return Response(result)
        except Exception as e:
            logger.error(f"Error predicting NBO: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='ml/churn')
    def predict_churn(self, request):
        """Predict churn"""
        customer_id = request.data.get('customer_id')
        if not customer_id:
            return Response({'error': 'customer_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            ml_service = MLInferenceService()
            result = ml_service.predict_churn(customer_id)
            return Response(result)
        except Exception as e:
            logger.error(f"Error predicting churn: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='ml/rfm')
    def calculate_rfm(self, request):
        """Calculate RFM segment"""
        customer_id = request.data.get('customer_id')
        if not customer_id:
            return Response({'error': 'customer_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            ml_service = MLInferenceService()
            result = ml_service.calculate_rfm(customer_id)
            return Response(result)
        except Exception as e:
            logger.error(f"Error calculating RFM: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='segments/(?P<segment_id>[^/.]+)/calculate')
    def calculate_segment(self, request, segment_id=None):
        """Recalculate segment membership"""
        from loyalty.models_khaywe import Segment
        
        try:
            segment = Segment.objects.get(id=segment_id)
            customer_ids = request.data.get('customer_ids')  # Optional: specific customers
            
            result = SegmentationEngine.update_segment_membership(segment, customer_ids)
            return Response({
                'status': 'success',
                'segment_id': segment_id,
                'added': result['added'],
                'removed': result['removed'],
                'total': result['total']
            })
        except Segment.DoesNotExist:
            return Response({'error': 'Segment not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error calculating segment: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='columns')
    def list_columns(self, request):
        """
        List available columns/fields from data sources (Xiva, DWH, or both)
        
        Query Parameters:
        - source: 'dwh', 'xiva', or 'auto' (default: 'auto')
        - customer_id: Optional sample customer ID for discovery
        """
        from django.conf import settings
        
        # Get data source from query param
        data_source = request.query_params.get('source', 'auto')
        sample_customer_id = request.query_params.get('customer_id', None)
        
        try:
            # Option 1: Get from settings (explicit configuration)
            columns_config = getattr(settings, 'DWH_COLUMNS_CONFIG', None)
            if columns_config:
                # Filter by data source if specified
                if data_source != 'auto':
                    filtered = [c for c in columns_config if c.get('data_source', 'dwh') == data_source or c.get('data_source') is None]
                    if filtered:
                        return Response(filtered)
                return Response(columns_config)
            
            # Option 2: Auto-discover from data source(s)
            discovered_columns = []
            
            # Try to get sample customer ID
            if not sample_customer_id:
                # Try to get a real customer ID from Xiva or DWH
                try:
                    if data_source in ('auto', 'xiva'):
                        from loyalty.integration.xiva_client import get_xiva_client
                        client = get_xiva_client()
                        customers = client.get_customer_list(limit=1)
                        if customers and len(customers) > 0:
                            sample_customer_id = customers[0].get('id')
                except:
                    pass
            
            # Discover from Xiva
            if data_source in ('auto', 'xiva') and sample_customer_id:
                try:
                    xiva_features = FeatureStore.get_customer_features(
                        sample_customer_id, 
                        data_source='xiva',
                        use_cache=False  # Don't use cache for discovery
                    )
                    if xiva_features:
                        for key, value in xiva_features.items():
                            if key == 'customer_id':
                                continue
                            discovered_columns.append({
                                'name': key,
                                'type': self._infer_type(value),
                                'description': f'Xiva field: {key}',
                                'data_source': 'xiva',
                                'category': self._categorize_field(key)
                            })
                except Exception as e:
                    logger.debug(f"Could not discover from Xiva: {e}")
            
            # Discover from DWH
            if data_source in ('auto', 'dwh') and sample_customer_id:
                try:
                    dwh_features = FeatureStore.get_customer_features(
                        sample_customer_id,
                        data_source='dwh',
                        use_cache=False  # Don't use cache for discovery
                    )
                    if dwh_features:
                        for key, value in dwh_features.items():
                            if key == 'customer_id':
                                continue
                            # Only add if not already added from Xiva
                            if not any(c['name'] == key for c in discovered_columns):
                                discovered_columns.append({
                                    'name': key,
                                    'type': self._infer_type(value),
                                    'description': f'DWH column: {key}',
                                    'data_source': 'dwh',
                                    'category': self._categorize_field(key)
                                })
                except Exception as e:
                    logger.debug(f"Could not discover from DWH: {e}")
            
            if discovered_columns:
                return Response(discovered_columns)
            
            # Option 3: Return default/common columns
            default_columns = [
                {'name': 'total_revenue', 'type': 'number', 'description': 'Total customer revenue', 'category': 'financial'},
                {'name': 'transaction_count', 'type': 'number', 'description': 'Number of transactions', 'category': 'transaction'},
                {'name': 'last_purchase_days_ago', 'type': 'number', 'description': 'Days since last purchase', 'category': 'transaction'},
                {'name': 'avg_transaction_value', 'type': 'number', 'description': 'Average transaction value', 'category': 'transaction'},
                {'name': 'lifetime_value', 'type': 'number', 'description': 'Customer lifetime value', 'category': 'financial'},
                {'name': 'churn_score', 'type': 'number', 'description': 'Churn risk score (0-1)', 'category': 'ml'},
                {'name': 'customer_tier', 'type': 'string', 'description': 'Current loyalty tier', 'category': 'loyalty'},
                {'name': 'points_balance', 'type': 'number', 'description': 'Current points balance', 'category': 'loyalty'},
                {'name': 'customer_status', 'type': 'string', 'description': 'Customer status', 'category': 'profile'},
                {'name': 'city', 'type': 'string', 'description': 'Customer city', 'category': 'demographic'},
                {'name': 'region', 'type': 'string', 'description': 'Customer region', 'category': 'demographic'},
                {'name': 'country', 'type': 'string', 'description': 'Customer country', 'category': 'demographic'},
                {'name': 'age', 'type': 'number', 'description': 'Customer age', 'category': 'demographic'},
                {'name': 'gender', 'type': 'string', 'description': 'Customer gender', 'category': 'demographic'},
                {'name': 'segment', 'type': 'string', 'description': 'Current segment', 'category': 'segmentation'},
                {'name': 'registration_date', 'type': 'date', 'description': 'Customer registration date', 'category': 'profile'},
                {'name': 'last_login_days_ago', 'type': 'number', 'description': 'Days since last login', 'category': 'engagement'},
                {'name': 'email_verified', 'type': 'boolean', 'description': 'Email verification status', 'category': 'profile'},
                {'name': 'phone_verified', 'type': 'boolean', 'description': 'Phone verification status', 'category': 'profile'},
                {'name': 'preferred_channel', 'type': 'string', 'description': 'Preferred communication channel', 'category': 'engagement'},
                {'name': 'campaign_engagement_rate', 'type': 'number', 'description': 'Campaign engagement rate', 'category': 'engagement'},
            ]
            return Response(default_columns)
        except Exception as e:
            logger.error(f"Error listing columns: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _infer_type(self, value):
        """Infer field type from Python value"""
        if value is None:
            return 'string'
        python_type = type(value).__name__
        type_map = {
            'int': 'number',
            'float': 'number',
            'str': 'string',
            'bool': 'boolean',
            'datetime': 'datetime',
            'date': 'date',
            'list': 'array',
            'dict': 'object',
        }
        return type_map.get(python_type, 'string')
    
    def _categorize_field(self, field_name):
        """Categorize field by name patterns"""
        name_lower = field_name.lower()
        
        if any(word in name_lower for word in ['revenue', 'spend', 'payment', 'balance', 'credit', 'outstanding']):
            return 'financial'
        elif any(word in name_lower for word in ['transaction', 'purchase', 'order']):
            return 'transaction'
        elif any(word in name_lower for word in ['points', 'tier', 'loyalty', 'reward']):
            return 'loyalty'
        elif any(word in name_lower for word in ['age', 'gender', 'city', 'region', 'country', 'nationality']):
            return 'demographic'
        elif any(word in name_lower for word in ['status', 'type', 'name', 'email', 'phone']):
            return 'profile'
        elif any(word in name_lower for word in ['usage', 'service', 'product']):
            return 'service'
        elif any(word in name_lower for word in ['churn', 'nbo', 'rfm', 'score']):
            return 'ml'
        elif any(word in name_lower for word in ['segment', 'campaign', 'engagement']):
            return 'segmentation'
        else:
            return 'other'
    
    @action(detail=False, methods=['get'], url_path='event-types')
    def list_event_types(self, request):
        """List available event types for triggers"""
        # Comprehensive list of event types
        event_types = [
            # Customer Events
            {'value': 'customer.created', 'label': 'Customer Created', 'category': 'customer'},
            {'value': 'customer.updated', 'label': 'Customer Updated', 'category': 'customer'},
            {'value': 'customer.login', 'label': 'Customer Login', 'category': 'customer'},
            {'value': 'customer.logout', 'label': 'Customer Logout', 'category': 'customer'},
            {'value': 'customer.profile_updated', 'label': 'Profile Updated', 'category': 'customer'},
            
            # Transaction Events
            {'value': 'transaction.purchase', 'label': 'Purchase Made', 'category': 'transaction'},
            {'value': 'transaction.refund', 'label': 'Refund Processed', 'category': 'transaction'},
            {'value': 'transaction.cancelled', 'label': 'Transaction Cancelled', 'category': 'transaction'},
            
            # Loyalty Events
            {'value': 'loyalty.account_created', 'label': 'Loyalty Account Created', 'category': 'loyalty'},
            {'value': 'loyalty.points_earned', 'label': 'Points Earned', 'category': 'loyalty'},
            {'value': 'loyalty.points_redeemed', 'label': 'Points Redeemed', 'category': 'loyalty'},
            {'value': 'loyalty.points_expired', 'label': 'Points Expired', 'category': 'loyalty'},
            {'value': 'loyalty.tier_upgraded', 'label': 'Tier Upgraded', 'category': 'loyalty'},
            {'value': 'loyalty.tier_downgraded', 'label': 'Tier Downgraded', 'category': 'loyalty'},
            {'value': 'loyalty.reward_redeemed', 'label': 'Reward Redeemed', 'category': 'loyalty'},
            
            # Campaign Events
            {'value': 'campaign.triggered', 'label': 'Campaign Triggered', 'category': 'campaign'},
            {'value': 'campaign.delivered', 'label': 'Campaign Delivered', 'category': 'campaign'},
            {'value': 'campaign.opened', 'label': 'Campaign Opened', 'category': 'campaign'},
            {'value': 'campaign.clicked', 'label': 'Campaign Clicked', 'category': 'campaign'},
            {'value': 'campaign.converted', 'label': 'Campaign Converted', 'category': 'campaign'},
            {'value': 'campaign.bounced', 'label': 'Campaign Bounced', 'category': 'campaign'},
            
            # Promotion Events
            {'value': 'promotion.applied', 'label': 'Promotion Applied', 'category': 'promotion'},
            {'value': 'promotion.eligible', 'label': 'Promotion Eligible', 'category': 'promotion'},
            {'value': 'promotion.expired', 'label': 'Promotion Expired', 'category': 'promotion'},
            
            # Journey Events
            {'value': 'journey.started', 'label': 'Journey Started', 'category': 'journey'},
            {'value': 'journey.completed', 'label': 'Journey Completed', 'category': 'journey'},
            {'value': 'journey.abandoned', 'label': 'Journey Abandoned', 'category': 'journey'},
            {'value': 'journey.node_reached', 'label': 'Journey Node Reached', 'category': 'journey'},
            
            # Gamification Events
            {'value': 'gamification.mission_completed', 'label': 'Mission Completed', 'category': 'gamification'},
            {'value': 'gamification.badge_earned', 'label': 'Badge Earned', 'category': 'gamification'},
            {'value': 'gamification.leaderboard_updated', 'label': 'Leaderboard Updated', 'category': 'gamification'},
            {'value': 'gamification.streak_achieved', 'label': 'Streak Achieved', 'category': 'gamification'},
            
            # Segment Events
            {'value': 'segment.joined', 'label': 'Segment Joined', 'category': 'segment'},
            {'value': 'segment.left', 'label': 'Segment Left', 'category': 'segment'},
            
            # Custom Events (user-defined)
            {'value': 'custom', 'label': 'Custom Event', 'category': 'custom'},
        ]
        return Response(event_types)

