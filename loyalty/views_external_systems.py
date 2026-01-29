from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
import logging
import requests

from loyalty.models_khaywe import ExternalSystemConfig
from loyalty.serializers_external_systems import ExternalSystemConfigSerializer
from loyalty.services.external_system_manager import ExternalSystemManager

logger = logging.getLogger(__name__)


class ExternalSystemConfigViewSet(viewsets.ModelViewSet):
    """ViewSet for managing external system configurations"""
    queryset = ExternalSystemConfig.objects.all()
    serializer_class = ExternalSystemConfigSerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access for development
    
    def get_queryset(self):
        """Filter configurations based on query parameters"""
        queryset = ExternalSystemConfig.objects.all()
        
        # Filter by system type
        system_type = self.request.query_params.get('system_type', None)
        if system_type:
            queryset = queryset.filter(system_type=system_type)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        # Filter by production
        is_production = self.request.query_params.get('is_production', None)
        if is_production is not None:
            is_production = is_production.lower() == 'true'
            queryset = queryset.filter(is_production=is_production)
        
        return queryset.order_by('system_type', 'name')
    
    @action(detail=True, methods=['post'], url_path='test')
    def test_connection(self, request, pk=None):
        """Test connection to external system"""
        config = self.get_object()
        
        try:
            manager = ExternalSystemManager(config)
            result = manager.test_connection()
            
            if result['success']:
                # Update last_tested_at
                config.last_tested_at = timezone.now()
                config.save(update_fields=['last_tested_at'])
                
                return Response({
                    'success': True,
                    'message': 'Connection test successful',
                    'details': result.get('details', {}),
                })
            else:
                return Response(
                    {
                        'success': False,
                        'error': result.get('error', 'Connection test failed'),
                        'details': result.get('details', {}),
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.exception(f"Error testing connection for {config.name}: {e}")
            return Response(
                {'error': f'Failed to test connection: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='sync-products')
    def sync_products(self, request, pk=None):
        """Sync products from this external system"""
        config = self.get_object()
        
        if config.system_type not in ['xiva', 'crm', 'billing']:
            return Response(
                {'error': f'Product sync not supported for system type: {config.system_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from loyalty.services.product_service import ProductSyncService
            sync_service = ProductSyncService()
            
            # Use the configured external system
            if config.system_type == 'xiva':
                result = sync_service.sync_from_external_system(config)
            elif config.system_type == 'crm':
                result = sync_service.sync_from_external_system(config)
            elif config.system_type == 'billing':
                result = sync_service.sync_from_external_system(config)
            else:
                result = {'success': False, 'error': 'Unsupported system type'}
            
            if result.get('success'):
                # Update last_sync_at
                config.last_sync_at = timezone.now()
                config.save(update_fields=['last_sync_at'])
                
                return Response({
                    'success': True,
                    'message': f"Successfully synced {result.get('synced', 0)} products",
                    'created': result.get('created', 0),
                    'updated': result.get('updated', 0),
                })
            else:
                return Response(
                    {'error': result.get('error', 'Sync failed')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.exception(f"Error syncing products from {config.name}: {e}")
            return Response(
                {'error': f'Failed to sync products: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

