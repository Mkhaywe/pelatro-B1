"""
ViewSets for Khaywe models.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from django.db import models

logger = logging.getLogger(__name__)

from loyalty.models_khaywe import (
    Campaign, CampaignExecution,
    Segment, SegmentMember, SegmentSnapshot,
    Mission, MissionProgress, Badge, BadgeAward, Leaderboard, LeaderboardEntry, Streak,
    Journey, JourneyNode, JourneyEdge, JourneyExecution,
    Experiment, ExperimentAssignment, HoldoutGroup,
    Partner, PartnerProgram, PartnerSettlement, Coalition,
    Role, Permission, RolePermission, UserRole,
    ApprovalWorkflow, ApprovalRequest, ApprovalDecision,
    PointsExpiryRule, PointsExpiryEvent,
    EarnCap, CapUsage,
)
from loyalty.serializers_khaywe import (
    CampaignSerializer, CampaignExecutionSerializer,
    SegmentSerializer, SegmentMemberSerializer, SegmentSnapshotSerializer,
    MissionSerializer, MissionProgressSerializer, BadgeSerializer, BadgeAwardSerializer,
    LeaderboardSerializer, LeaderboardEntrySerializer, StreakSerializer,
    JourneySerializer, JourneyNodeSerializer, JourneyEdgeSerializer, JourneyExecutionSerializer,
    ExperimentSerializer, ExperimentAssignmentSerializer, HoldoutGroupSerializer,
    PartnerSerializer, PartnerProgramSerializer, PartnerSettlementSerializer, CoalitionSerializer,
    RoleSerializer, PermissionSerializer, RolePermissionSerializer, UserRoleSerializer,
    ApprovalWorkflowSerializer, ApprovalRequestSerializer, ApprovalDecisionSerializer,
    PointsExpiryRuleSerializer, PointsExpiryEventSerializer,
    EarnCapSerializer, CapUsageSerializer,
)
from loyalty.services.segmentation import SegmentationEngine


# ============================================================================
# CAMPAIGN MANAGEMENT
# ============================================================================

class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    filterset_fields = ['status', 'program', 'is_active']
    
    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request, pk=None):
        """Activate campaign"""
        campaign = self.get_object()
        campaign.status = 'active'
        campaign.save()
        return Response({'status': 'activated'})
    
    @action(detail=True, methods=['post'], url_path='pause')
    def pause(self, request, pk=None):
        """Pause campaign"""
        campaign = self.get_object()
        campaign.status = 'paused'
        campaign.save()
        return Response({'status': 'paused'})
    
        @action(detail=True, methods=['get'], url_path='performance')
        def performance(self, request, pk=None):
            """Get campaign performance metrics"""
            campaign = self.get_object()
            
            # Check if CampaignExecution is a managed model or a placeholder
            try:
                # Try to check if it's a placeholder model
                if hasattr(CampaignExecution._meta, 'managed') and CampaignExecution._meta.managed == False:
                    return Response({
                        'total_sent': 0,
                        'delivered': 0,
                        'opened': 0,
                        'clicked': 0,
                        'converted': 0,
                        'message': 'CampaignExecution model not fully migrated, returning placeholder performance.'
                    })
                
                # Try to filter - if it fails, the model is a placeholder
                try:
                    executions = CampaignExecution.objects.filter(campaign=campaign)
                except Exception as e:
                    logger.warning(f"CampaignExecution model doesn't have 'campaign' field (likely placeholder): {e}")
                    return Response({
                        'total_sent': 0,
                        'delivered': 0,
                        'opened': 0,
                        'clicked': 0,
                        'converted': 0,
                        'message': 'CampaignExecution model not fully migrated, returning placeholder performance.'
                    })
            except AttributeError:
                # Model might not have _meta or managed attribute
                try:
                    executions = CampaignExecution.objects.filter(campaign=campaign)
                except Exception as e:
                    logger.warning(f"CampaignExecution model doesn't have 'campaign' field: {e}")
                    return Response({
                        'total_sent': 0,
                        'delivered': 0,
                        'opened': 0,
                        'clicked': 0,
                        'converted': 0,
                        'message': 'CampaignExecution model not fully migrated, returning placeholder performance.'
                    })
            
            return Response({
                'total_sent': executions.count(),
                'delivered': executions.exclude(delivered_at__isnull=True).count(),
                'opened': executions.exclude(opened_at__isnull=True).count(),
                'clicked': executions.exclude(clicked_at__isnull=True).count(),
                'converted': executions.exclude(converted_at__isnull=True).count(),
            })
    
    @action(detail=False, methods=['get'], url_path='available-offers')
    def available_offers(self, request):
        """Get available offers from product catalog for campaign selection"""
        from loyalty.services.offer_service import OfferCatalogService
        from loyalty.models import Offer
        
        offer_service = OfferCatalogService()
        
        # Get all active offers
        offers = Offer.objects.filter(is_active=True).order_by('offer_id')
        
        offers_data = []
        for offer in offers:
            offers_data.append({
                'offer_id': offer.offer_id,
                'name': offer.name,
                'description': offer.description,
                'category': offer.category,
                'lifecycle_stage': offer.lifecycle_stage,
                'target_value_segment': offer.target_value_segment,
            })
        
        return Response({
            'offers': offers_data,
            'total': len(offers_data)
        })
    
    @action(detail=True, methods=['get'], url_path='offer-details')
    def offer_details(self, request, pk=None):
        """Get offer details for this campaign"""
        campaign = self.get_object()
        
        if not campaign.offer_id:
            return Response({
                'error': 'Campaign does not have an offer assigned'
            }, status=status.HTTP_404_NOT_FOUND)
        
        from loyalty.services.offer_service import OfferCatalogService
        offer_service = OfferCatalogService()
        offer = offer_service.get_offer_by_id(campaign.offer_id)
        
        if not offer:
            return Response({
                'error': f'Offer ID {campaign.offer_id} not found in catalog'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'offer_id': offer.offer_id,
            'name': offer.name,
            'description': offer.description,
            'category': offer.category,
            'lifecycle_stage': offer.lifecycle_stage,
            'target_value_segment': offer.target_value_segment,
            'offer_config': campaign.offer_config,
        })


class CampaignExecutionViewSet(viewsets.ModelViewSet):
    queryset = CampaignExecution.objects.all()
    serializer_class = CampaignExecutionSerializer
    filterset_fields = ['campaign', 'customer_id', 'channel']


# ============================================================================
# SEGMENTATION
# ============================================================================

class SegmentViewSet(viewsets.ModelViewSet):
    queryset = Segment.objects.all().order_by('-id')
    serializer_class = SegmentSerializer
    filterset_fields = ['program', 'is_active', 'is_dynamic', 'is_rfm']
    permission_classes = [AllowAny]  # Allow unauthenticated access for development
    
    def get_queryset(self):
        """Annotate queryset with member counts"""
        from django.db.models import Count
        try:
            # Try to use the related_name 'members' if it exists
            return Segment.objects.annotate(
                active_member_count=Count('members', filter=models.Q(members__is_active=True))
            )
        except Exception:
            # If annotation fails (e.g., placeholder model), return queryset without annotation
            return Segment.objects.all()
    
    @action(detail=True, methods=['post'], url_path='calculate')
    def calculate(self, request, pk=None):
        """Recalculate segment membership"""
        segment = self.get_object()
        customer_ids = request.data.get('customer_ids')  # Optional
        
        result = SegmentationEngine.update_segment_membership(segment, customer_ids)
        return Response(result)
    
    @action(detail=True, methods=['get'], url_path='members')
    def members(self, request, pk=None):
        """Get segment members"""
        segment = self.get_object()
        
        # Handle SegmentMember as a placeholder model - query database directly
        if SegmentMember._meta.managed == False:
            try:
                from django.db import connection
                import logging
                logger = logging.getLogger(__name__)
                
                # Try loyalty_segmentmember first (PostgreSQL convention), then segmentmember
                table_name = None
                if hasattr(SegmentMember._meta, 'db_table') and SegmentMember._meta.db_table:
                    table_name = SegmentMember._meta.db_table
                
                # Check if table exists first - try both table names
                with connection.cursor() as cursor:
                    table_names_to_try = ['loyalty_segmentmember', 'segmentmember']
                    if table_name:
                        table_names_to_try.insert(0, table_name)
                    
                    table_exists = False
                    for candidate_table in table_names_to_try:
                        if connection.vendor == 'sqlite':
                            cursor.execute(
                                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                                [candidate_table]
                            )
                            if cursor.fetchone():
                                table_name = candidate_table
                                table_exists = True
                                break
                        else:
                            # PostgreSQL check
                            cursor.execute(
                                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
                                [candidate_table]
                            )
                            if cursor.fetchone()[0]:
                                table_name = candidate_table
                                table_exists = True
                                break
                    
                    if not table_exists:
                        logger.warning(f"Table loyalty_segmentmember or segmentmember does not exist, returning empty members list")
                        return Response([])
                
                with connection.cursor() as cursor:
                    # Try to get column names first to handle different schemas
                    col_indices = {}
                    if connection.vendor == 'sqlite':
                        try:
                            cursor.execute(f'PRAGMA table_info({table_name})')
                            columns_info = cursor.fetchall()
                            column_names = [col[1] for col in columns_info] if columns_info else []
                            
                            if not column_names:
                                # Table might not exist or be empty
                                logger.warning(f"Table {table_name} has no columns or doesn't exist")
                                return Response([])
                            
                            # Build SELECT query based on available columns
                            select_cols = []
                            idx = 0
                            
                            if 'id' in column_names:
                                select_cols.append('id')
                                col_indices['id'] = idx
                                idx += 1
                            if 'customer_id' in column_names:
                                select_cols.append('customer_id')
                                col_indices['customer_id'] = idx
                                idx += 1
                            if 'segment_id' in column_names:
                                select_cols.append('segment_id')
                                col_indices['segment_id'] = idx
                                idx += 1
                            if 'is_active' in column_names:
                                select_cols.append('is_active')
                                col_indices['is_active'] = idx
                                idx += 1
                            if 'joined_at' in column_names:
                                select_cols.append('joined_at')
                                col_indices['joined_at'] = idx
                                idx += 1
                            if 'created_at' in column_names:
                                select_cols.append('created_at')
                                col_indices['created_at'] = idx
                                idx += 1
                            if 'updated_at' in column_names:
                                select_cols.append('updated_at')
                                col_indices['updated_at'] = idx
                                idx += 1
                            
                            if not select_cols:
                                return Response([])
                            
                            select_str = ', '.join(select_cols)
                            
                            # Build WHERE clause - check if segment_id column exists
                            if 'segment_id' in column_names:
                                where_clause = 'segment_id = ?'
                            elif 'segment' in column_names:
                                where_clause = 'segment = ?'
                            else:
                                # No segment column, return empty
                                return Response([])
                            
                            # Add is_active filter if column exists
                            if 'is_active' in column_names:
                                where_clause += ' AND is_active = 1'
                            
                            cursor.execute(
                                f'SELECT {select_str} FROM "{table_name}" WHERE {where_clause}',
                                [segment.id]
                            )
                        except Exception as table_error:
                            logger.exception(f"Error querying table {table_name}: {table_error}")
                            return Response([])
                    else:
                        # PostgreSQL - dynamically detect columns
                        try:
                            cursor.execute(f"""
                                SELECT column_name 
                                FROM information_schema.columns 
                                WHERE table_name = '{table_name}'
                                ORDER BY ordinal_position
                            """)
                            columns_info = cursor.fetchall()
                            column_names = [col[0] for col in columns_info] if columns_info else []
                            
                            if not column_names:
                                logger.warning(f"Table {table_name} has no columns or doesn't exist")
                                return Response([])
                            
                            # Build SELECT query based on available columns
                            select_cols = []
                            col_indices = {}
                            idx = 0
                            
                            if 'id' in column_names:
                                select_cols.append('id')
                                col_indices['id'] = idx
                                idx += 1
                            if 'customer_id' in column_names:
                                select_cols.append('customer_id')
                                col_indices['customer_id'] = idx
                                idx += 1
                            # Check for segment_id or segment
                            if 'segment_id' in column_names:
                                select_cols.append('segment_id')
                                col_indices['segment_id'] = idx
                                idx += 1
                            elif 'segment' in column_names:
                                select_cols.append('segment')
                                col_indices['segment'] = idx
                                idx += 1
                            if 'is_active' in column_names:
                                select_cols.append('is_active')
                                col_indices['is_active'] = idx
                                idx += 1
                            if 'joined_at' in column_names:
                                select_cols.append('joined_at')
                                col_indices['joined_at'] = idx
                                idx += 1
                            if 'left_at' in column_names:
                                select_cols.append('left_at')
                                col_indices['left_at'] = idx
                                idx += 1
                            # Only include created_at/updated_at if they exist
                            if 'created_at' in column_names:
                                select_cols.append('created_at')
                                col_indices['created_at'] = idx
                                idx += 1
                            if 'updated_at' in column_names:
                                select_cols.append('updated_at')
                                col_indices['updated_at'] = idx
                                idx += 1
                            
                            if not select_cols:
                                return Response([])
                            
                            select_str = ', '.join(select_cols)
                            
                            # Build WHERE clause - check if segment_id or segment column exists
                            if 'segment_id' in column_names:
                                where_clause = 'segment_id = %s'
                            elif 'segment' in column_names:
                                where_clause = 'segment = %s'
                            else:
                                # No segment column, return empty
                                return Response([])
                            
                            # Add is_active filter if column exists
                            if 'is_active' in column_names:
                                where_clause += ' AND is_active = true'
                            
                            cursor.execute(
                                f'SELECT {select_str} FROM "{table_name}" WHERE {where_clause}',
                                [segment.id]
                            )
                        except Exception as table_error:
                            logger.exception(f"Error querying table {table_name}: {table_error}")
                            return Response([])
                    
                    rows = cursor.fetchall()
                    members = []
                    for row in rows:
                        if not row:
                            continue
                            
                        member_dict = {
                            'segment': segment.id,
                        }
                        
                        # Map columns based on what we selected (works for both SQLite and PostgreSQL)
                        if col_indices:
                            if 'id' in col_indices and col_indices['id'] < len(row):
                                member_dict['id'] = row[col_indices['id']]
                            if 'customer_id' in col_indices and col_indices['customer_id'] < len(row):
                                member_dict['customer_id'] = str(row[col_indices['customer_id']])
                            if 'is_active' in col_indices and col_indices['is_active'] < len(row):
                                member_dict['is_active'] = bool(row[col_indices['is_active']])
                            if 'joined_at' in col_indices and col_indices['joined_at'] < len(row) and row[col_indices['joined_at']]:
                                dt = row[col_indices['joined_at']]
                                member_dict['joined_at'] = dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)
                            if 'left_at' in col_indices and col_indices['left_at'] < len(row) and row[col_indices['left_at']]:
                                dt = row[col_indices['left_at']]
                                member_dict['left_at'] = dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)
                            # Only include created_at/updated_at if they exist
                            if 'created_at' in col_indices and col_indices['created_at'] < len(row) and row[col_indices['created_at']]:
                                dt = row[col_indices['created_at']]
                                member_dict['created_at'] = dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)
                            if 'updated_at' in col_indices and col_indices['updated_at'] < len(row) and row[col_indices['updated_at']]:
                                dt = row[col_indices['updated_at']]
                                member_dict['updated_at'] = dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)
                        else:
                            # Fallback: assume standard order if col_indices not available
                            if len(row) > 0:
                                member_dict['id'] = row[0]
                            if len(row) > 1:
                                member_dict['customer_id'] = str(row[1])
                            if len(row) > 3:
                                member_dict['is_active'] = bool(row[3])
                            if len(row) > 4 and row[4]:
                                dt = row[4]
                                member_dict['joined_at'] = dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)
                        
                        members.append(member_dict)
                    
                    return Response(members)
            except Exception as e:
                logger.exception(f"Error getting segment members from database: {e}")
                # Return empty list instead of error to prevent frontend issues
                return Response([])
        
        try:
            members = SegmentMember.objects.filter(segment=segment, is_active=True)
            serializer = SegmentMemberSerializer(members, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error getting segment members: {e}")
            return Response({
                'error': str(e),
                'members': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='metrics')
    def metrics(self, request, pk=None):
        """Get segment metrics"""
        from django.db.models import Count, Max
        from django.utils import timezone
        
        segment = self.get_object()
        
        # Handle SegmentMember as a placeholder model
        if SegmentMember._meta.managed == False:
            return Response({
                'total_members': 0,
                'inactive_members': 0,
                'last_calculated': None,
                'snapshots': [],
                'segment_id': segment.id,
                'segment_name': getattr(segment, 'name', 'Unknown'),
                'is_dynamic': getattr(segment, 'is_dynamic', False),
                'is_rfm': getattr(segment, 'is_rfm', False),
                'message': 'SegmentMember model not fully migrated, returning placeholder metrics.'
            })
        
        try:
            members = SegmentMember.objects.filter(segment=segment)
            
            # Get snapshots for trend
            snapshots = []
            if SegmentSnapshot._meta.managed != False:
                snapshots = SegmentSnapshot.objects.filter(segment=segment).order_by('-snapshot_date')[:10]
            
            return Response({
                'total_members': members.filter(is_active=True).count(),
                'inactive_members': members.filter(is_active=False).count(),
                'last_calculated': segment.last_calculated_at.isoformat() if hasattr(segment, 'last_calculated_at') and segment.last_calculated_at else None,
                'snapshots': [
                    {
                        'date': s.snapshot_date.isoformat(),
                        'member_count': s.member_count
                    }
                    for s in snapshots
                ],
                'segment_id': segment.id,
                'segment_name': getattr(segment, 'name', 'Unknown'),
                'is_dynamic': getattr(segment, 'is_dynamic', False),
                'is_rfm': getattr(segment, 'is_rfm', False),
            })
        except Exception as e:
            logger.error(f"Error getting segment metrics: {e}")
            return Response({
                'error': str(e),
                'total_members': 0,
                'inactive_members': 0,
                'last_calculated': None,
                'snapshots': [],
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    @action(detail=True, methods=['post'], url_path='ml/predict')
    def predict_ml(self, request, pk=None):
        """Run ML predictions for all customers in segment"""
        segment = self.get_object()
        prediction_type = request.data.get('type', 'churn')  # 'churn', 'nbo', 'rfm', 'ltv', 'propensity', 'product', 'campaign', 'default_risk', 'upsell', 'engagement'
        
        # Get all active segment members using raw SQL (SegmentMember is placeholder)
        customer_ids = []
        try:
            from django.db import connection
            table_name = 'loyalty_segmentmember'
            with connection.cursor() as cursor:
                if connection.vendor == 'sqlite':
                    cursor.execute(
                        f'SELECT customer_id FROM "{table_name}" WHERE segment_id = ? AND is_active = 1',
                        [segment.id]
                    )
                else:
                    cursor.execute(
                        f'SELECT customer_id FROM "{table_name}" WHERE segment_id = %s AND is_active = true',
                        [segment.id]
                    )
                customer_ids = [str(row[0]) for row in cursor.fetchall()]
        except Exception as e:
            logger.warning(f"Error getting segment members via raw SQL: {e}")
            # Fallback to ORM
            try:
                members = SegmentMember.objects.filter(segment=segment, is_active=True).values_list('customer_id', flat=True)
                customer_ids = list(members)
            except Exception:
                pass
        
        if not customer_ids:
            return Response({
                'error': 'Segment has no active members'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Limit batch size
        max_batch = 1000
        if len(customer_ids) > max_batch:
            customer_ids = customer_ids[:max_batch]
            warning = f'Limited to first {max_batch} customers (segment has {len(members)} total)'
        else:
            warning = None
        
        try:
            from loyalty.ml.inference import MLInferenceService
            try:
                ml_service = MLInferenceService()
            except Exception as e:
                logger.error(f"Error initializing ML service: {e}", exc_info=True)
                return Response({
                    'error': f'Failed to initialize ML service: {str(e)}. Please check ML configuration and dependencies.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            results = []
            errors = []
            aggregated_stats = {
                'churn': {'high': 0, 'medium': 0, 'low': 0, 'avg_probability': 0.0},
                'nbo': {},
                'rfm': {},
                'ltv': {'total_ltv': 0.0, 'count': 0},
                'propensity': {'high': 0, 'medium': 0, 'low': 0},
                'campaign': {'positive': 0, 'negative': 0},
                'default_risk': {'high': 0, 'medium': 0, 'low': 0},
                'upsell': {'high': 0, 'medium': 0, 'low': 0},
                'engagement': {'total_score': 0.0, 'count': 0},
            }
            
            for cid in customer_ids:
                try:
                    if prediction_type == 'churn':
                        result = ml_service.predict_churn(cid)
                        # Check if result has an error
                        if 'error' in result:
                            errors.append({
                                'customer_id': cid,
                                'error': result['error']
                            })
                        else:
                            results.append({
                                'customer_id': cid,
                                'result': result
                            })
                            # Aggregate churn stats
                            risk = result.get('churn_risk', 'low')
                            aggregated_stats['churn'][risk] = aggregated_stats['churn'].get(risk, 0) + 1
                            aggregated_stats['churn']['avg_probability'] += result.get('churn_probability', 0)
                    elif prediction_type == 'nbo':
                        result = ml_service.predict_nbo(cid)
                        # Check if result has an error
                        if 'error' in result:
                            errors.append({
                                'customer_id': cid,
                                'error': result['error']
                            })
                        else:
                            results.append({
                                'customer_id': cid,
                                'result': result
                            })
                            # Aggregate NBO stats
                            offer_id = result.get('recommended_offer')
                            if offer_id is not None:
                                aggregated_stats['nbo'][str(offer_id)] = aggregated_stats['nbo'].get(str(offer_id), 0) + 1
                    elif prediction_type == 'rfm':
                        result = ml_service.calculate_rfm(cid)
                        # Check if result has an error
                        if 'error' in result:
                            errors.append({
                                'customer_id': cid,
                                'error': result['error']
                            })
                        else:
                            results.append({
                                'customer_id': cid,
                                'result': result
                            })
                            # Aggregate RFM stats
                            segment_name = result.get('segment', 'Unknown')
                            aggregated_stats['rfm'][segment_name] = aggregated_stats['rfm'].get(segment_name, 0) + 1
                    elif prediction_type == 'ltv':
                        result = ml_service.predict_ltv(cid)
                        if 'error' in result:
                            errors.append({
                                'customer_id': cid,
                                'error': result['error']
                            })
                        else:
                            results.append({
                                'customer_id': cid,
                                'result': result
                            })
                            # Aggregate LTV stats
                            if 'ltv' not in aggregated_stats:
                                aggregated_stats['ltv'] = {'total_ltv': 0.0, 'count': 0}
                            aggregated_stats['ltv']['total_ltv'] += result.get('predicted_ltv', 0)
                            aggregated_stats['ltv']['count'] += 1
                    elif prediction_type == 'propensity':
                        result = ml_service.predict_propensity_to_buy(cid)
                        if 'error' in result:
                            errors.append({
                                'customer_id': cid,
                                'error': result['error']
                            })
                        else:
                            results.append({
                                'customer_id': cid,
                                'result': result
                            })
                            # Aggregate propensity stats
                            if 'propensity' not in aggregated_stats:
                                aggregated_stats['propensity'] = {'high': 0, 'medium': 0, 'low': 0}
                            propensity_level = result.get('propensity_level', 'low')
                            if propensity_level in aggregated_stats['propensity']:
                                aggregated_stats['propensity'][propensity_level] += 1
                    elif prediction_type == 'product':
                        result = ml_service.recommend_products(cid)
                        if 'error' in result:
                            errors.append({
                                'customer_id': cid,
                                'error': result['error']
                            })
                        else:
                            results.append({
                                'customer_id': cid,
                                'result': result
                            })
                    elif prediction_type == 'campaign':
                        result = ml_service.predict_campaign_response(cid, campaign_id="default")
                        if 'error' in result:
                            errors.append({
                                'customer_id': cid,
                                'error': result['error']
                            })
                        else:
                            results.append({
                                'customer_id': cid,
                                'result': result
                            })
                            # Aggregate campaign stats
                            if 'campaign' not in aggregated_stats:
                                aggregated_stats['campaign'] = {'positive': 0, 'negative': 0}
                            response = result.get('response_prediction', 'negative')
                            if response in aggregated_stats['campaign']:
                                aggregated_stats['campaign'][response] += 1
                    elif prediction_type == 'default_risk':
                        result = ml_service.predict_payment_default_risk(cid)
                        if 'error' in result:
                            errors.append({
                                'customer_id': cid,
                                'error': result['error']
                            })
                        else:
                            results.append({
                                'customer_id': cid,
                                'result': result
                            })
                            # Aggregate default risk stats
                            if 'default_risk' not in aggregated_stats:
                                aggregated_stats['default_risk'] = {'high': 0, 'medium': 0, 'low': 0}
                            risk_level = result.get('risk_level', 'low')
                            if risk_level in aggregated_stats['default_risk']:
                                aggregated_stats['default_risk'][risk_level] += 1
                    elif prediction_type == 'upsell':
                        result = ml_service.predict_upsell_propensity(cid)
                        if 'error' in result:
                            errors.append({
                                'customer_id': cid,
                                'error': result['error']
                            })
                        else:
                            results.append({
                                'customer_id': cid,
                                'result': result
                            })
                            # Aggregate upsell stats
                            if 'upsell' not in aggregated_stats:
                                aggregated_stats['upsell'] = {'high': 0, 'medium': 0, 'low': 0}
                            propensity_level = result.get('propensity_level', 'low')
                            if propensity_level in aggregated_stats['upsell']:
                                aggregated_stats['upsell'][propensity_level] += 1
                    elif prediction_type == 'engagement':
                        result = ml_service.calculate_engagement_score(cid)
                        if 'error' in result:
                            errors.append({
                                'customer_id': cid,
                                'error': result['error']
                            })
                        else:
                            results.append({
                                'customer_id': cid,
                                'result': result
                            })
                            # Aggregate engagement stats
                            if 'engagement' not in aggregated_stats:
                                aggregated_stats['engagement'] = {'total_score': 0.0, 'count': 0}
                            aggregated_stats['engagement']['total_score'] += result.get('engagement_score', 0)
                            aggregated_stats['engagement']['count'] += 1
                    else:
                        errors.append({
                            'customer_id': cid,
                            'error': f'Invalid prediction type: {prediction_type}'
                        })
                        continue
                except Exception as e:
                    logger.error(f"Error processing customer {cid}: {e}", exc_info=True)
                    errors.append({
                        'customer_id': cid,
                        'error': str(e)
                    })
            
            # Calculate averages
            if prediction_type == 'churn' and len(results) > 0:
                aggregated_stats['churn']['avg_probability'] /= len(results)
            elif prediction_type == 'ltv' and 'ltv' in aggregated_stats and aggregated_stats['ltv']['count'] > 0:
                aggregated_stats['ltv']['avg_ltv'] = aggregated_stats['ltv']['total_ltv'] / aggregated_stats['ltv']['count']
                del aggregated_stats['ltv']['total_ltv']
                del aggregated_stats['ltv']['count']
            elif prediction_type == 'engagement' and 'engagement' in aggregated_stats and aggregated_stats['engagement']['count'] > 0:
                aggregated_stats['engagement']['avg_score'] = aggregated_stats['engagement']['total_score'] / aggregated_stats['engagement']['count']
                del aggregated_stats['engagement']['total_score']
                del aggregated_stats['engagement']['count']
            
            return Response({
                'segment_id': segment.id,
                'segment_name': getattr(segment, 'name', f'Segment {segment.id}'),
                'type': prediction_type,
                'mode': 'segment',
                'total_customers': len(customer_ids),
                'processed': len(customer_ids),
                'successful': len(results),
                'failed': len(errors),
                'warning': warning,
                'aggregated_stats': aggregated_stats,
                'results': results[:100],  # Return first 100 for preview
                'errors': errors[:10] if errors else None,  # Return first 10 errors
                'has_more_results': len(results) > 100,
            })
        except Exception as e:
            logger.error(f"Error running segment ML prediction: {e}", exc_info=True)
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Full traceback: {error_trace}")
            return Response({
                'error': str(e),
                'detail': 'An error occurred while running ML predictions. Check backend logs for details.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='ml/stats')
    def ml_stats(self, request, pk=None):
        """Get aggregated ML statistics for segment"""
        segment = self.get_object()
        
        # Get all active segment members using raw SQL (SegmentMember is placeholder)
        customer_ids = []
        total_members = 0
        try:
            from django.db import connection
            table_name = 'loyalty_segmentmember'
            with connection.cursor() as cursor:
                if connection.vendor == 'sqlite':
                    cursor.execute(
                        f'SELECT customer_id FROM "{table_name}" WHERE segment_id = ? AND is_active = 1',
                        [segment.id]
                    )
                else:
                    cursor.execute(
                        f'SELECT customer_id FROM "{table_name}" WHERE segment_id = %s AND is_active = true',
                        [segment.id]
                    )
                all_members = [str(row[0]) for row in cursor.fetchall()]
                total_members = len(all_members)
                customer_ids = all_members[:1000]  # Limit to 1000 for performance
        except Exception as e:
            logger.warning(f"Error getting segment members via raw SQL for ml_stats: {e}")
            # Fallback to ORM
            try:
                members = SegmentMember.objects.filter(segment=segment, is_active=True).values_list('customer_id', flat=True)
                total_members = members.count()
                customer_ids = list(members[:1000])
            except Exception:
                pass
        
        if not customer_ids:
            return Response({
                'segment_id': segment.id,
                'segment_name': getattr(segment, 'name', f'Segment {segment.id}'),
                'member_count': 0,
                'stats': {}
            })
        
        try:
            from loyalty.ml.inference import MLInferenceService
            ml_service = MLInferenceService()
            
            # Calculate stats for each prediction type
            churn_stats = {'high': 0, 'medium': 0, 'low': 0, 'total_probability': 0.0, 'count': 0}
            nbo_counts = {}
            rfm_counts = {}
            
            for cid in customer_ids:
                try:
                    # Churn
                    churn_result = ml_service.predict_churn(cid)
                    risk = churn_result.get('churn_risk', 'low')
                    churn_stats[risk] = churn_stats.get(risk, 0) + 1
                    churn_stats['total_probability'] += churn_result.get('churn_probability', 0)
                    churn_stats['count'] += 1
                    
                    # NBO
                    nbo_result = ml_service.predict_nbo(cid)
                    offer_id = str(nbo_result.get('recommended_offer', 'unknown'))
                    nbo_counts[offer_id] = nbo_counts.get(offer_id, 0) + 1
                    
                    # RFM
                    rfm_result = ml_service.calculate_rfm(cid)
                    segment_name = rfm_result.get('segment', 'Unknown')
                    rfm_counts[segment_name] = rfm_counts.get(segment_name, 0) + 1
                except Exception as e:
                    logger.warning(f"Error calculating ML stats for customer {cid}: {e}")
                    continue
            
            # Calculate averages
            if churn_stats['count'] > 0:
                churn_stats['avg_probability'] = churn_stats['total_probability'] / churn_stats['count']
                churn_stats['high_percentage'] = (churn_stats['high'] / churn_stats['count']) * 100
                churn_stats['medium_percentage'] = (churn_stats['medium'] / churn_stats['count']) * 100
                churn_stats['low_percentage'] = (churn_stats['low'] / churn_stats['count']) * 100
            del churn_stats['total_probability']
            
            return Response({
                'segment_id': segment.id,
                'segment_name': getattr(segment, 'name', f'Segment {segment.id}'),
                'member_count': total_members,
                'sampled_count': len(customer_ids),
                'stats': {
                    'churn': churn_stats,
                    'nbo': {
                        'top_offers': sorted(nbo_counts.items(), key=lambda x: x[1], reverse=True)[:10],
                        'distribution': nbo_counts
                    },
                    'rfm': {
                        'distribution': rfm_counts,
                        'top_segments': sorted(rfm_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    }
                }
            })
        except Exception as e:
            logger.error(f"Error getting segment ML stats: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        from django.db.models import Count, Max
        from django.utils import timezone
        
        segment = self.get_object()
        members = SegmentMember.objects.filter(segment=segment)
        
        # Get snapshots for trend
        snapshots = SegmentSnapshot.objects.filter(segment=segment).order_by('-snapshot_date')[:10]
        
        return Response({
            'total_members': members.filter(is_active=True).count(),
            'inactive_members': members.filter(is_active=False).count(),
            'last_calculated': segment.last_calculated_at.isoformat() if segment.last_calculated_at else None,
            'snapshots': [
                {
                    'date': s.snapshot_date.isoformat(),
                    'member_count': s.member_count
                }
                for s in snapshots
            ]
        })


class SegmentMemberViewSet(viewsets.ModelViewSet):
    queryset = SegmentMember.objects.all().order_by('-id')
    serializer_class = SegmentMemberSerializer
    filterset_fields = ['segment', 'customer_id', 'is_active']


class SegmentSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SegmentSnapshot.objects.all().order_by('-id')
    serializer_class = SegmentSnapshotSerializer
    filterset_fields = ['segment']
    
    def list(self, request, *args, **kwargs):
        """Override list to use raw SQL for placeholder models"""
        from django.db import connection
        
        segment_id = request.query_params.get('segment')
        
        try:
            with connection.cursor() as cursor:
                if segment_id:
                    if connection.vendor == 'sqlite':
                        cursor.execute("""
                            SELECT id, segment_id, snapshot_date, member_count 
                            FROM loyalty_segmentsnapshot 
                            WHERE segment_id = ? 
                            ORDER BY snapshot_date DESC
                        """, [segment_id])
                    else:
                        cursor.execute("""
                            SELECT id, segment_id, snapshot_date, member_count 
                            FROM loyalty_segmentsnapshot 
                            WHERE segment_id = %s 
                            ORDER BY snapshot_date DESC
                        """, [segment_id])
                else:
                    cursor.execute("""
                        SELECT id, segment_id, snapshot_date, member_count 
                        FROM loyalty_segmentsnapshot 
                        ORDER BY snapshot_date DESC
                    """)
                
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    snap_date = row[2]
                    # Handle date formatting
                    if hasattr(snap_date, 'isoformat'):
                        snap_date_str = snap_date.isoformat()
                    else:
                        snap_date_str = str(snap_date) if snap_date else None
                    
                    results.append({
                        'id': row[0],
                        'segment': row[1],
                        'snapshot_date': snap_date_str,
                        'member_count': row[3] or 0,
                        'created_at': snap_date_str,  # Use snapshot_date as created_at
                    })
                
                return Response({
                    'count': len(results),
                    'next': None,
                    'previous': None,
                    'results': results
                })
        except Exception as e:
            logger.warning(f"Error fetching snapshots with raw SQL: {e}")
            # Fall back to standard behavior
            return super().list(request, *args, **kwargs)


# ============================================================================
# GAMIFICATION
# ============================================================================

class MissionViewSet(viewsets.ModelViewSet):
    queryset = Mission.objects.all()
    serializer_class = MissionSerializer
    filterset_fields = ['program', 'mission_type', 'is_active', 'category', 'is_dynamic', 'generated_for']
    
    @action(detail=True, methods=['get'], url_path='progress')
    def progress(self, request, pk=None):
        """Get mission progress for customers"""
        mission = self.get_object()
        customer_id = request.query_params.get('customer_id')
        
        if customer_id:
            progress = MissionProgress.objects.filter(mission=mission, customer_id=customer_id).first()
            if progress:
                return Response(MissionProgressSerializer(progress).data)
            return Response({'error': 'No progress found'}, status=404)
        
        # Return all progress
        progress_list = MissionProgress.objects.filter(mission=mission)
        return Response(MissionProgressSerializer(progress_list, many=True).data)
    
    @action(detail=False, methods=['post'], url_path='generate-for-customer')
    def generate_for_customer(self, request):
        """Generate personalized missions for a customer"""
        from loyalty.services.dynamic_mission_generator import DynamicMissionGeneratorService
        
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
        from loyalty.services.dynamic_mission_generator import DynamicMissionGeneratorService
        
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


class MissionProgressViewSet(viewsets.ModelViewSet):
    queryset = MissionProgress.objects.all()
    serializer_class = MissionProgressSerializer
    filterset_fields = ['mission', 'customer_id', 'is_completed']


class BadgeViewSet(viewsets.ModelViewSet):
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    filterset_fields = ['program', 'rarity', 'is_active']


class BadgeAwardViewSet(viewsets.ModelViewSet):
    queryset = BadgeAward.objects.all()
    serializer_class = BadgeAwardSerializer
    filterset_fields = ['badge', 'customer_id']


class LeaderboardViewSet(viewsets.ModelViewSet):
    queryset = Leaderboard.objects.all()
    serializer_class = LeaderboardSerializer
    filterset_fields = ['program', 'is_active']
    
    @action(detail=True, methods=['get'], url_path='entries')
    def entries(self, request, pk=None):
        """Get leaderboard entries"""
        leaderboard = self.get_object()
        entries = LeaderboardEntry.objects.filter(leaderboard=leaderboard).order_by('rank')[:leaderboard.top_n]
        return Response(LeaderboardEntrySerializer(entries, many=True).data)


class LeaderboardEntryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LeaderboardEntry.objects.all()
    serializer_class = LeaderboardEntrySerializer
    filterset_fields = ['leaderboard', 'customer_id']


class StreakViewSet(viewsets.ModelViewSet):
    queryset = Streak.objects.all()
    serializer_class = StreakSerializer
    filterset_fields = ['customer_id', 'program', 'streak_type']


# ============================================================================
# JOURNEY BUILDER
# ============================================================================

class JourneyViewSet(viewsets.ModelViewSet):
    queryset = Journey.objects.all()
    serializer_class = JourneySerializer
    filterset_fields = ['program', 'is_active']
    
    def perform_create(self, serializer):
        """Create journey and save nodes/edges from structure"""
        journey = serializer.save()
        self._save_nodes_and_edges(journey, self.request.data)
    
    def perform_update(self, serializer):
        """Update journey and save nodes/edges from structure"""
        journey = serializer.save()
        self._save_nodes_and_edges(journey, self.request.data)
    
    def _save_nodes_and_edges(self, journey, data):
        """Save nodes and edges from structure field"""
        from loyalty.models_khaywe import JourneyNode, JourneyEdge
        import json
        
        # Get structure from request data
        structure = data.get('structure')
        if isinstance(structure, str):
            try:
                structure = json.loads(structure)
            except:
                structure = {}
        elif not structure:
            structure = {}
        
        # Save structure field to journey
        journey.structure = structure
        journey.save(update_fields=['structure'])
        
        nodes_data = structure.get('nodes', [])
        edges_data = structure.get('edges', [])
        
        # Delete existing nodes and edges
        JourneyNode.objects.filter(journey=journey).delete()
        JourneyEdge.objects.filter(journey=journey).delete()
        
        # Create nodes
        node_map = {}  # Map frontend node IDs to database node IDs
        for idx, node_data in enumerate(nodes_data):
            node_id = node_data.get('id', f'node-{idx}')
            node_type = node_data.get('type', 'default')
            position = node_data.get('position', {})
            data_obj = node_data.get('data', {})
            
            # Extract config from data
            config = {
                'label': data_obj.get('label', ''),
                'actionType': data_obj.get('actionType'),
                'condition': data_obj.get('condition'),
                'duration': data_obj.get('duration'),
                'durationUnit': data_obj.get('durationUnit'),
            }
            # Remove None values
            config = {k: v for k, v in config.items() if v is not None}
            
            # Map node_type to valid choices
            valid_types = ['start', 'condition', 'action', 'wait', 'end']
            if node_type not in valid_types:
                node_type = 'action' if node_type == 'default' else 'start'
            
            node = JourneyNode.objects.create(
                journey=journey,
                node_type=node_type,
                name=data_obj.get('label', node_type.title()),
                config=config,
                position_x=position.get('x', 0),
                position_y=position.get('y', 0),
                order=idx
            )
            node_map[node_id] = node.id
        
        # Create edges
        for edge_data in edges_data:
            source_id = edge_data.get('source')
            target_id = edge_data.get('target')
            
            # Get database node IDs from map
            from_node_id = node_map.get(source_id)
            to_node_id = node_map.get(target_id)
            
            if from_node_id and to_node_id:
                try:
                    from_node = JourneyNode.objects.get(id=from_node_id)
                    to_node = JourneyNode.objects.get(id=to_node_id)
                    
                    condition = edge_data.get('condition') or edge_data.get('label')
                    if isinstance(condition, str):
                        try:
                            condition = json.loads(condition) if condition else {}
                        except:
                            condition = {}
                    
                    JourneyEdge.objects.create(
                        journey=journey,
                        from_node=from_node,
                        to_node=to_node,
                        condition=condition
                    )
                except JourneyNode.DoesNotExist:
                    pass
    
    @action(detail=True, methods=['get'], url_path='executions')
    def executions(self, request, pk=None):
        """Get journey executions"""
        journey = self.get_object()
        executions = JourneyExecution.objects.filter(journey=journey)
        return Response(JourneyExecutionSerializer(executions, many=True).data)
    
    @action(detail=True, methods=['post'], url_path='preview')
    def preview(self, request, pk=None):
        """Preview journey execution for a test customer"""
        journey = self.get_object()
        customer_id = request.data.get('customer_id', 'test-customer-123')
        
        # Parse structure - try structure field first, then fallback to nodes/edges
        structure = journey.structure
        if isinstance(structure, str):
            import json
            try:
                structure = json.loads(structure)
            except:
                structure = {}
        elif not structure:
            structure = {}
        
        # If structure is empty, try to build from nodes/edges
        if not structure.get('nodes') and journey.nodes.exists():
            nodes_list = []
            edges_list = []
            for node in journey.nodes.all():
                node_data = {
                    'id': str(node.id),
                    'type': node.node_type,
                    'position': {'x': node.position_x, 'y': node.position_y},
                    'data': {
                        'label': node.name,
                        **(node.config or {})
                    }
                }
                nodes_list.append(node_data)
            
            for edge in journey.edges.all():
                edge_data = {
                    'source': str(edge.from_node.id),
                    'target': str(edge.to_node.id),
                    'condition': edge.condition or {}
                }
                edges_list.append(edge_data)
            
            structure = {'nodes': nodes_list, 'edges': edges_list}
        
        nodes = structure.get('nodes', [])
        edges = structure.get('edges', [])
        
        # Simulate execution path
        execution_path = []
        current_node = None
        
        # Find start node
        for node in nodes:
            if node.get('type') == 'start':
                current_node = node
                execution_path.append({
                    'node_id': node.get('id'),
                    'node_type': node.get('type'),
                    'node_name': node.get('data', {}).get('label', 'Start'),
                    'status': 'completed'
                })
                break
        
        # Simulate flow through nodes
        max_steps = 10
        step = 0
        while current_node and step < max_steps:
            step += 1
            node_type = current_node.get('type')
            
            if node_type == 'end':
                execution_path.append({
                    'node_id': current_node.get('id'),
                    'node_type': 'end',
                    'node_name': current_node.get('data', {}).get('label', 'End'),
                    'status': 'completed'
                })
                break
            
            # Find next node via edges
            next_node = None
            current_node_id = current_node.get('id')
            
            for edge in edges:
                # Match by 'source' (frontend format) or 'from_node' (backend format)
                edge_source = edge.get('source') or edge.get('from_node')
                edge_target = edge.get('target') or edge.get('to_node')
                
                # Convert to string for comparison
                if str(edge_source) == str(current_node_id):
                    # Check condition (simplified - always pass for preview)
                    target_id = edge_target
                    for node in nodes:
                        node_id = node.get('id')
                        if str(node_id) == str(target_id):
                            next_node = node
                            execution_path.append({
                                'node_id': str(node_id),
                                'node_type': node.get('type'),
                                'node_name': node.get('data', {}).get('label', 'Node'),
                                'status': 'completed' if node.get('type') != 'wait' else 'waiting'
                            })
                            break
                    if next_node:
                        break
            
            if not next_node:
                break
            
            current_node = next_node
        
        return Response({
            'journey_id': str(journey.id),
            'journey_name': journey.name,
            'test_customer_id': customer_id,
            'preview': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'execution_path': execution_path,
                'steps_completed': len(execution_path),
                'estimated_duration_minutes': len([n for n in execution_path if n.get('node_type') == 'wait']) * 5
            }
        })


class JourneyNodeViewSet(viewsets.ModelViewSet):
    queryset = JourneyNode.objects.all()
    serializer_class = JourneyNodeSerializer
    filterset_fields = ['journey', 'node_type']


class JourneyEdgeViewSet(viewsets.ModelViewSet):
    queryset = JourneyEdge.objects.all()
    serializer_class = JourneyEdgeSerializer
    filterset_fields = ['journey']


class JourneyExecutionViewSet(viewsets.ModelViewSet):
    queryset = JourneyExecution.objects.all()
    serializer_class = JourneyExecutionSerializer
    filterset_fields = ['journey', 'customer_id', 'status']


# ============================================================================
# A/B TESTING
# ============================================================================

class ExperimentViewSet(viewsets.ModelViewSet):
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer
    filterset_fields = ['status']
    
    @action(detail=True, methods=['get'], url_path='results')
    def results(self, request, pk=None):
        """Get experiment results"""
        experiment = self.get_object()
        assignments = ExperimentAssignment.objects.filter(experiment=experiment)
        
        # Parse variants if string
        variants = experiment.variants
        if isinstance(variants, str):
            import json
            try:
                variants = json.loads(variants)
            except:
                variants = []
        
        variant_counts = {}
        for variant in variants:
            variant_name = variant.get('name') if isinstance(variant, dict) else str(variant)
            variant_counts[variant_name] = assignments.filter(variant=variant_name).count()
        
        # Calculate conversions
        variant_conversions = {}
        for variant_name in variant_counts.keys():
            variant_conversions[variant_name] = assignments.filter(
                variant=variant_name,
                converted=True
            ).count()
        
        return Response({
            'total_assignments': assignments.count(),
            'variant_counts': variant_counts,
            'variant_conversions': variant_conversions,
            'total_conversions': sum(variant_conversions.values())
        })
    
    @action(detail=True, methods=['post'], url_path='start')
    def start(self, request, pk=None):
        """Start an experiment"""
        experiment = self.get_object()
        
        if experiment.status == 'running':
            return Response({'error': 'Experiment is already running'}, status=400)
        
        if experiment.status == 'completed':
            return Response({'error': 'Cannot start a completed experiment'}, status=400)
        
        experiment.status = 'running'
        experiment.save()
        
        return Response({
            'status': 'started',
            'experiment_id': str(experiment.id),
            'message': 'Experiment started successfully'
        })
    
    @action(detail=True, methods=['post'], url_path='stop')
    def stop(self, request, pk=None):
        """Stop an experiment"""
        experiment = self.get_object()
        
        if experiment.status != 'running':
            return Response({'error': 'Experiment is not running'}, status=400)
        
        experiment.status = 'completed'
        experiment.save()
        
        return Response({
            'status': 'stopped',
            'experiment_id': str(experiment.id),
            'message': 'Experiment stopped successfully'
        })


class ExperimentAssignmentViewSet(viewsets.ModelViewSet):
    queryset = ExperimentAssignment.objects.all()
    serializer_class = ExperimentAssignmentSerializer
    filterset_fields = ['experiment', 'customer_id', 'variant']


class HoldoutGroupViewSet(viewsets.ModelViewSet):
    queryset = HoldoutGroup.objects.all()
    serializer_class = HoldoutGroupSerializer
    filterset_fields = ['experiment']


# ============================================================================
# PARTNER/COALITION
# ============================================================================

class PartnerViewSet(viewsets.ModelViewSet):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
    filterset_fields = ['partner_type', 'is_active']
    
    @action(detail=True, methods=['get'], url_path='programs')
    def get_programs(self, request, pk=None):
        """Get partner programs"""
        partner = self.get_object()
        programs = PartnerProgram.objects.filter(partner=partner)
        serializer = PartnerProgramSerializer(programs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='coalitions')
    def get_coalitions(self, request, pk=None):
        """Get partner coalitions"""
        partner = self.get_object()
        coalitions = partner.coalitions.all()
        serializer = CoalitionSerializer(coalitions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='settlements')
    def get_settlements(self, request, pk=None):
        """Get partner settlements"""
        partner = self.get_object()
        settlements = PartnerSettlement.objects.filter(partner=partner).order_by('-period_start')
        serializer = PartnerSettlementSerializer(settlements, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='generate-api-key')
    def generate_api_key(self, request, pk=None):
        """Generate API key for partner"""
        import secrets
        partner = self.get_object()
        api_key = secrets.token_urlsafe(32)
        partner.api_key = api_key
        partner.save()
        return Response({'api_key': api_key})


class PartnerProgramViewSet(viewsets.ModelViewSet):
    queryset = PartnerProgram.objects.all()
    serializer_class = PartnerProgramSerializer
    filterset_fields = ['partner', 'program', 'is_active']


class PartnerSettlementViewSet(viewsets.ModelViewSet):
    queryset = PartnerSettlement.objects.all()
    serializer_class = PartnerSettlementSerializer
    filterset_fields = ['partner', 'program', 'status']


class CoalitionViewSet(viewsets.ModelViewSet):
    queryset = Coalition.objects.all()
    serializer_class = CoalitionSerializer
    filterset_fields = ['is_active']


# ============================================================================
# RBAC
# ============================================================================

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    filterset_fields = ['role_type', 'is_active']


class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    filterset_fields = ['resource', 'action']


class RolePermissionViewSet(viewsets.ModelViewSet):
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    filterset_fields = ['role', 'permission']


class UserRoleViewSet(viewsets.ModelViewSet):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    filterset_fields = ['user_id', 'role']


class ApprovalWorkflowViewSet(viewsets.ModelViewSet):
    queryset = ApprovalWorkflow.objects.all()
    serializer_class = ApprovalWorkflowSerializer
    filterset_fields = ['resource_type', 'is_active']


class ApprovalRequestViewSet(viewsets.ModelViewSet):
    queryset = ApprovalRequest.objects.all()
    serializer_class = ApprovalRequestSerializer
    filterset_fields = ['workflow', 'resource_type', 'status']


class ApprovalDecisionViewSet(viewsets.ModelViewSet):
    queryset = ApprovalDecision.objects.all()
    serializer_class = ApprovalDecisionSerializer
    filterset_fields = ['request', 'decision']


# ============================================================================
# POINTS EXPIRY & CAPS
# ============================================================================

class PointsExpiryRuleViewSet(viewsets.ModelViewSet):
    queryset = PointsExpiryRule.objects.all()
    serializer_class = PointsExpiryRuleSerializer
    filterset_fields = ['program', 'is_active']


class PointsExpiryEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PointsExpiryEvent.objects.all()
    serializer_class = PointsExpiryEventSerializer
    filterset_fields = ['account', 'rule']


class EarnCapViewSet(viewsets.ModelViewSet):
    queryset = EarnCap.objects.all()
    serializer_class = EarnCapSerializer
    filterset_fields = ['program', 'cap_type', 'is_active']


class CapUsageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CapUsage.objects.all()
    serializer_class = CapUsageSerializer
    filterset_fields = ['cap', 'customer_id']

