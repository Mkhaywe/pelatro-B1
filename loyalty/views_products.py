from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.db.models import Q
import logging

from loyalty.models import Product
from loyalty.serializers_products import ProductSerializer
from loyalty.services.product_service import ProductSyncService

logger = logging.getLogger(__name__)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product catalog management"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access for development
    
    def get_queryset(self):
        """Filter products based on query parameters"""
        queryset = Product.objects.all()
        
        # Filter by product type
        product_type = self.request.query_params.get('product_type', None)
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        # Filter by external system
        external_system = self.request.query_params.get('external_system', None)
        if external_system:
            queryset = queryset.filter(external_system=external_system)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        # Filter by available status
        is_available = self.request.query_params.get('is_available', None)
        if is_available is not None:
            is_available = is_available.lower() == 'true'
            queryset = queryset.filter(is_available=is_available)
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__icontains=category)
        
        # Search by name or description
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(external_product_id__icontains=search)
            )
        
        return queryset.order_by('name')
    
    @action(detail=False, methods=['post'], url_path='sync')
    def sync_products(self, request):
        """Sync products from external system using ExternalSystemConfig"""
        external_system_id = request.data.get('external_system_id')
        external_system = request.data.get('external_system', 'xiva')  # Fallback for legacy
        
        try:
            from loyalty.services.external_system_manager import ExternalSystemManager
            from loyalty.models_khaywe import ExternalSystemConfig
            
            # If external_system_id is provided, use ExternalSystemConfig
            if external_system_id:
                try:
                    config = ExternalSystemConfig.objects.get(id=external_system_id)
                    sync_service = ProductSyncService()
                    result = sync_service.sync_from_external_system(config)
                except ExternalSystemConfig.DoesNotExist:
                    return Response(
                        {'error': f'External system config with ID {external_system_id} not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # Legacy: try to find config by system_type
                try:
                    config = ExternalSystemConfig.objects.filter(system_type=external_system, is_active=True).first()
                    if config:
                        sync_service = ProductSyncService()
                        result = sync_service.sync_from_external_system(config)
                    else:
                        return Response(
                            {'error': f'No active external system config found for {external_system}. Please configure it in Admin > External Systems Config.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except Exception:
                    # Fallback to old method if ExternalSystemConfig doesn't exist
                    sync_service = ProductSyncService()
                    if external_system == 'xiva':
                        result = sync_service.sync_from_xiva()
                    elif external_system == 'crm':
                        result = sync_service.sync_from_crm()
                    elif external_system == 'billing':
                        result = sync_service.sync_from_billing()
                    else:
                        return Response(
                            {'error': f'Unknown external system: {external_system}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            
            if result.get('success'):
                return Response({
                    'success': True,
                    'message': result.get('message', f"Successfully synced {result.get('synced_count', 0)} products"),
                    'created': result.get('created_count', 0),
                    'updated': result.get('updated_count', 0),
                    'synced_count': result.get('synced_count', 0),
                })
            else:
                return Response(
                    {'error': result.get('error', 'Sync failed')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.exception(f"Error syncing products: {e}")
            return Response(
                {'error': f'Failed to sync products: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='available')
    def available_products(self, request):
        """Get available products for campaigns (filtered by active and available)"""
        queryset = self.get_queryset().filter(is_active=True, is_available=True)
        
        # Additional filtering for campaign targeting
        customer_value = request.query_params.get('customer_value', None)
        if customer_value:
            try:
                customer_value = float(customer_value)
                queryset = queryset.filter(
                    Q(min_customer_value__isnull=True) | Q(min_customer_value__lte=customer_value),
                    Q(max_customer_value__isnull=True) | Q(max_customer_value__gte=customer_value)
                )
            except ValueError:
                pass
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='stats')
    def product_stats(self, request):
        """Get product catalog statistics"""
        total = Product.objects.count()
        active = Product.objects.filter(is_active=True).count()
        available = Product.objects.filter(is_active=True, is_available=True).count()
        
        by_type = {}
        for product_type, _ in Product.PRODUCT_TYPES:
            by_type[product_type] = Product.objects.filter(
                product_type=product_type,
                is_active=True
            ).count()
        
        by_system = {}
        for system, _ in Product._meta.get_field('external_system').choices:
            by_system[system] = Product.objects.filter(
                external_system=system
            ).count()
        
        return Response({
            'total': total,
            'active': active,
            'available': available,
            'by_type': by_type,
            'by_system': by_system,
        })

