"""
API Views for Enhanced Gamification System
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q
from django.utils import timezone
import logging

from loyalty.models_khaywe import (
    Mission, MissionTemplate, MissionProgress,
    Badge, BadgeAward,
    CustomerEvent, CustomerBehaviorScore, DataSourceConfig
)
from loyalty.serializers_khaywe import (
    DataSourceConfigSerializer, CustomerEventSerializer,
    CustomerBehaviorScoreSerializer, MissionTemplateSerializer
)
from loyalty.services.event_normalizer import EventNormalizerService
from loyalty.services.behavior_scoring import BehaviorScoringService
from loyalty.services.dynamic_mission_generator import DynamicMissionGeneratorService
from loyalty.services.gamification_service import GamificationService

logger = logging.getLogger(__name__)


class DataSourceConfigViewSet(viewsets.ModelViewSet):
    """API for managing data source configurations"""
    serializer_class = DataSourceConfigSerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access for development
    
    def get_queryset(self):
        """Handle case where table doesn't exist yet"""
        try:
            return DataSourceConfig.objects.all()
        except Exception:
            # Table doesn't exist, return empty queryset
            return DataSourceConfig.objects.none()
    
    @action(detail=True, methods=['post'], url_path='sync')
    def sync_events(self, request, pk=None):
        """Sync events from a data source"""
        config = self.get_object()
        normalizer = EventNormalizerService()
        
        # TODO: Implement actual sync logic based on source type
        # This would fetch events from the source and normalize them
        
        return Response({
            'status': 'success',
            'message': f'Sync initiated for {config.source_name}',
            'source_type': config.source_type
        })
    
    def get_queryset(self):
        """Filter by is_active if requested"""
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class CustomerEventViewSet(viewsets.ReadOnlyModelViewSet):
    """API for viewing customer events"""
    queryset = CustomerEvent.objects.all()
    serializer_class = CustomerEventSerializer
    filterset_fields = ['customer_id', 'event_type', 'source', 'processed']
    
    @action(detail=False, methods=['post'], url_path='normalize')
    def normalize_event(self, request):
        """Normalize an event from a data source"""
        source_type = request.data.get('source_type')
        raw_event = request.data.get('event')
        
        if not source_type or not raw_event:
            return Response({
                'error': 'source_type and event are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        normalizer = EventNormalizerService()
        normalized = normalizer.normalize_event(source_type, raw_event)
        
        if normalized:
            return Response({
                'status': 'success',
                'event_id': str(normalized.id),
                'customer_id': str(normalized.customer_id),
                'event_type': normalized.event_type,
            })
        else:
            return Response({
                'error': 'Failed to normalize event'
            }, status=status.HTTP_400_BAD_REQUEST)


class CustomerBehaviorScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """API for customer behavior scores"""
    queryset = CustomerBehaviorScore.objects.all()
    serializer_class = CustomerBehaviorScoreSerializer
    lookup_field = 'customer_id'
    
    @action(detail=True, methods=['post'], url_path='recalculate')
    def recalculate_scores(self, request, customer_id=None):
        """Recalculate behavior scores for a customer"""
        scoring_service = BehaviorScoringService()
        score = scoring_service.calculate_all_scores(
            customer_id,
            force_recalculate=True
        )
        
        return Response({
            'customer_id': str(score.customer_id),
            'engagement_score': score.engagement_score,
            'revenue_score': score.revenue_score,
            'loyalty_score': score.loyalty_score,
            'risk_score': score.risk_score,
            'digital_score': score.digital_score,
            'score_breakdown': score.score_breakdown,
            'updated_at': score.updated_at.isoformat(),
        })
    
    @action(detail=False, methods=['post'], url_path='batch-calculate')
    def batch_calculate_scores(self, request):
        """Calculate scores for multiple customers"""
        customer_ids = request.data.get('customer_ids', [])
        if not customer_ids:
            return Response({
                'error': 'customer_ids is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        scoring_service = BehaviorScoringService()
        results = scoring_service.batch_calculate_scores(customer_ids)
        
        return Response({
            'processed': len(results),
            'results': {
                str(cid): {
                    'engagement_score': score.engagement_score,
                    'revenue_score': score.revenue_score,
                    'loyalty_score': score.loyalty_score,
                    'risk_score': score.risk_score,
                    'digital_score': score.digital_score,
                }
                for cid, score in results.items()
            }
        })


class MissionTemplateViewSet(viewsets.ModelViewSet):
    """API for mission templates"""
    queryset = MissionTemplate.objects.all()
    serializer_class = MissionTemplateSerializer
    filterset_fields = ['category', 'metric', 'is_active']
    
    @action(detail=True, methods=['post'], url_path='generate-for-customer')
    def generate_for_customer(self, request, pk=None):
        """Generate a mission from template for a specific customer"""
        template = self.get_object()
        customer_id = request.data.get('customer_id')
        
        if not customer_id:
            return Response({
                'error': 'customer_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        generator = DynamicMissionGeneratorService()
        mission = generator._generate_mission_from_template(
            template,
            customer_id,
            generator.scoring_service.get_scores(customer_id),
            {}  # Features would be loaded in the method
        )
        
        if mission:
            return Response({
                'status': 'success',
                'mission_id': mission.id,
                'mission_name': mission.name,
            })
        else:
            return Response({
                'error': 'Failed to generate mission'
            }, status=status.HTTP_400_BAD_REQUEST)


class MissionViewSet(viewsets.ModelViewSet):
    """API for missions (enhanced)"""
    queryset = Mission.objects.all()
    serializer_class = None  # TODO: Create serializer
    filterset_fields = ['category', 'is_active', 'is_dynamic', 'generated_for']
    
    @action(detail=False, methods=['post'], url_path='generate-for-customer')
    def generate_for_customer(self, request):
        """Generate personalized missions for a customer"""
        customer_id = request.data.get('customer_id')
        max_missions = request.data.get('max_missions', 5)
        force_regenerate = request.data.get('force_regenerate', False)
        
        if not customer_id:
            return Response({
                'error': 'customer_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        generator = DynamicMissionGeneratorService()
        missions = generator.generate_missions_for_customer(
            customer_id,
            max_missions=max_missions,
            force_regenerate=force_regenerate
        )
        
        return Response({
            'customer_id': customer_id,
            'generated': len(missions),
            'missions': [
                {
                    'id': mission.id,
                    'name': mission.name,
                    'category': mission.category,
                    'target_value': float(mission.target_value) if mission.target_value else None,
                    'metric': mission.metric,
                }
                for mission in missions
            ]
        })
    
    @action(detail=False, methods=['post'], url_path='generate-for-segment')
    def generate_for_segment(self, request):
        """Generate missions for all customers in a segment"""
        segment_id = request.data.get('segment_id')
        max_missions_per_customer = request.data.get('max_missions_per_customer', 5)
        
        if not segment_id:
            return Response({
                'error': 'segment_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        generator = DynamicMissionGeneratorService()
        results = generator.generate_missions_for_segment(
            segment_id,
            max_missions_per_customer=max_missions_per_customer
        )
        
        total_missions = sum(len(missions) for missions in results.values())
        
        return Response({
            'segment_id': segment_id,
            'customers_processed': len(results),
            'total_missions_generated': total_missions,
            'results': {
                customer_id: {
                    'missions_count': len(missions),
                    'missions': [
                        {
                            'id': m.id,
                            'name': m.name,
                            'category': m.category,
                        }
                        for m in missions
                    ]
                }
                for customer_id, missions in results.items()
            }
        })


class BadgeViewSet(viewsets.ModelViewSet):
    """API for badges (enhanced)"""
    queryset = Badge.objects.all()
    serializer_class = None  # TODO: Create serializer
    filterset_fields = ['badge_type', 'level', 'is_active']
    
    @action(detail=False, methods=['post'], url_path='check-and-award')
    def check_and_award(self, request):
        """Check badge criteria and award if met"""
        badge_id = request.data.get('badge_id')
        customer_id = request.data.get('customer_id')
        
        if not badge_id or not customer_id:
            return Response({
                'error': 'badge_id and customer_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            badge = Badge.objects.get(pk=badge_id)
            gamification_service = GamificationService()
            
            # Get customer scores for context
            scoring_service = BehaviorScoringService()
            scores = scoring_service.get_scores(customer_id)
            
            from loyalty.integration.feature_store import FeatureStore
            features = FeatureStore.get_customer_features(customer_id)
            
            context = {
                'customer_id': customer_id,
                'engagement_score': scores.engagement_score if scores else 0,
                'revenue_score': scores.revenue_score if scores else 0,
                'loyalty_score': scores.loyalty_score if scores else 0,
                'risk_score': scores.risk_score if scores else 0,
                'digital_score': scores.digital_score if scores else 0,
                **features
            }
            
            result = gamification_service.check_and_award_badge(badge, customer_id, context)
            
            return Response(result)
        except Badge.DoesNotExist:
            return Response({
                'error': 'Badge not found'
            }, status=status.HTTP_404_NOT_FOUND)

