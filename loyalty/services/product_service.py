"""
Product Sync Service - Syncs products from external systems
"""
import logging
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.db.models import Q
from loyalty.models import Product

# XivaClient import - will be implemented when Xiva API is configured
try:
    from loyalty.integration.external import XivaClient
except ImportError:
    XivaClient = None

logger = logging.getLogger(__name__)


class ProductSyncService:
    """Service to sync products from external systems"""
    
    def sync_from_external_system(self, config) -> Dict:
        """Sync products from a configured external system"""
        try:
            # For Xiva, use the working XivaClient (same as customer API)
            if config.system_type == 'xiva':
                return self._sync_from_xiva_using_client()
            
            # For other systems, use ExternalSystemManager
            from loyalty.services.external_system_manager import ExternalSystemManager
            
            manager = ExternalSystemManager(config)
            
            # Get products from external system
            result = manager.get_products()
            
            if not result.get('success'):
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to fetch products'),
                }
            
            products_data = result.get('data', {})
            
            # Handle TMF620 format
            if 'results' in products_data:
                products_list = products_data['results']
            elif isinstance(products_data, list):
                products_list = products_data
            else:
                products_list = [products_data]
            
            return self._process_products_list(products_list, config)
        except Exception as e:
            logger.exception(f"Error syncing products from {config.name}: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def _sync_from_xiva_using_client(self) -> Dict:
        """Sync products from Xiva using the working XivaClient (same as customer API)"""
        try:
            from loyalty.integration.xiva_client import get_xiva_client
            
            client = get_xiva_client()
            
            # Get product offerings using the same client that works for customers
            products_list = client.get_product_offerings()
            
            # Get config for system_type
            from loyalty.models_khaywe import ExternalSystemConfig
            config = ExternalSystemConfig.objects.filter(system_type='xiva', is_active=True).first()
            if not config:
                config = ExternalSystemConfig.objects.filter(system_type='xiva').first()
                if not config:
                    # Create a minimal config object for processing
                    class MinimalConfig:
                        system_type = 'xiva'
                    config = MinimalConfig()
            
            return self._process_products_list(products_list, config)
        except Exception as e:
            logger.error(f"Error syncing products from Xiva: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
            }
    
    def _process_products_list(self, products_list: List[Dict], config) -> Dict:
        """Process a list of products and save them to database"""
        if not products_list:
            return {
                'success': True,
                'message': 'No products to sync',
                'synced_count': 0,
                'created_count': 0,
                'updated_count': 0,
            }
        
        synced_count = 0
        created_count = 0
        updated_count = 0
        
        for product_data in products_list:
            # Map TMF620 ProductOffering to our Product model
            external_product_id = str(product_data.get('id', ''))
            if not external_product_id:
                continue
            
            # Extract product details from TMF620 format
            name = product_data.get('name', f"Product {external_product_id}")
            description = product_data.get('description', '')
            
            # Extract pricing
            pricing = product_data.get('productOfferingPrice', [])
            price = None
            currency = 'SAR'
            recurring = False
            billing_cycle = 'monthly'
            
            if pricing:
                first_price = pricing[0]
                price_obj = first_price.get('price', {})
                tax_amount = price_obj.get('taxIncludedAmount', {})
                price = tax_amount.get('value')
                currency = tax_amount.get('unit', 'SAR')
                price_type = first_price.get('priceType', '')
                recurring = price_type == 'recurring'
                billing_cycle = first_price.get('recurringChargePeriod', 'monthly')
            
            # Extract characteristics
            characteristics = product_data.get('characteristic', [])
            features = {}
            for char in characteristics:
                char_name = char.get('name', '')
                char_value = char.get('value', '')
                features[char_name] = char_value
            
            # Extract category
            categories = product_data.get('category', [])
            category = categories[0].get('name', '') if categories else ''
            
            # Map product type
            product_type = self._map_product_type_from_tmf(product_data, features)
            
            defaults = {
                'name': name,
                'description': description,
                'product_type': product_type,
                'category': category,
                'price': price,
                'currency': currency,
                'recurring': recurring,
                'billing_cycle': self._map_billing_cycle(billing_cycle),
                'features': features,
                'attributes': {
                    'lifecycle_status': product_data.get('lifecycleStatus', ''),
                    'is_bundle': product_data.get('isBundle', False),
                    'is_sellable': product_data.get('isSellable', True),
                    'valid_for': product_data.get('validFor', {}),
                },
                'is_active': product_data.get('lifecycleStatus') == 'Active',
                'is_available': product_data.get('isSellable', True),
                'last_synced': timezone.now(),
            }
            
            product, created = Product.objects.update_or_create(
                external_product_id=external_product_id,
                external_system=config.system_type,
                defaults=defaults
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
            synced_count += 1
        
        return {
            'success': True,
            'message': f"Successfully synced {synced_count} products",
            'synced_count': synced_count,
            'created_count': created_count,
            'updated_count': updated_count,
        }
    
    def sync_from_xiva(self) -> Dict:
        """Sync products from Xiva system (legacy method - use sync_from_external_system)"""
        # Try to find Xiva configuration
        try:
            from loyalty.models_khaywe import ExternalSystemConfig
            xiva_config = ExternalSystemConfig.objects.filter(
                system_type='xiva',
                is_active=True
            ).first()
            
            if xiva_config:
                return self.sync_from_external_system(xiva_config)
        except Exception as e:
            logger.exception(f"Error finding Xiva config: {e}")
        
        return {
            'success': False,
            'error': 'Xiva configuration not found. Please configure Xiva in External Systems.',
        }
    
    def _sync_from_xiva_legacy(self) -> Dict:
        """Legacy sync method (deprecated)"""
        if XivaClient is None:
            return {
                'success': False,
                'error': 'XivaClient not available. Xiva integration not configured.',
            }
        try:
            xiva_client = XivaClient()
            
            # Fetch products from Xiva API
            # Note: This is a placeholder - adjust based on actual Xiva API
            products_data = xiva_client.get_products()  # This method needs to be implemented in XivaClient
            
            if not products_data:
                return {
                    'success': False,
                    'error': 'No products returned from Xiva API',
                }
            
            synced_count = 0
            created_count = 0
            updated_count = 0
            
            for product_data in products_data:
                external_product_id = str(product_data.get('id') or product_data.get('product_id', ''))
                if not external_product_id:
                    continue
                
                # Map Xiva product data to our Product model
                defaults = {
                    'name': product_data.get('name', f"Product {external_product_id}"),
                    'description': product_data.get('description', ''),
                    'product_type': self._map_product_type(product_data.get('type', 'bundle')),
                    'category': product_data.get('category', ''),
                    'price': product_data.get('price'),
                    'currency': product_data.get('currency', 'USD'),
                    'recurring': product_data.get('recurring', False),
                    'billing_cycle': self._map_billing_cycle(product_data.get('billing_cycle', 'monthly')),
                    'features': product_data.get('features', {}),
                    'attributes': product_data.get('attributes', {}),
                    'is_active': product_data.get('is_active', True),
                    'is_available': product_data.get('is_available', True),
                    'last_synced': timezone.now(),
                }
                
                product, created = Product.objects.update_or_create(
                    external_product_id=external_product_id,
                    external_system='xiva',
                    defaults=defaults
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                synced_count += 1
            
            return {
                'success': True,
                'synced': synced_count,
                'created': created_count,
                'updated': updated_count,
            }
        except Exception as e:
            logger.exception(f"Error syncing products from Xiva: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def sync_from_crm(self) -> Dict:
        """Sync products from CRM system"""
        # Placeholder for CRM integration
        logger.warning("CRM product sync not yet implemented")
        return {
            'success': False,
            'error': 'CRM product sync not yet implemented',
        }
    
    def sync_from_billing(self) -> Dict:
        """Sync products from Billing/OCS system"""
        # Placeholder for Billing integration
        logger.warning("Billing product sync not yet implemented")
        return {
            'success': False,
            'error': 'Billing product sync not yet implemented',
        }
    
    def _map_product_type(self, external_type: str) -> str:
        """Map external product type to internal type"""
        type_mapping = {
            'voice': 'voice',
            'data': 'data',
            'sms': 'sms',
            'bundle': 'bundle',
            'device': 'device',
            'service': 'service',
            'addon': 'addon',
        }
        return type_mapping.get(external_type.lower(), 'bundle')
    
    def _map_billing_cycle(self, external_cycle: str) -> str:
        """Map external billing cycle to internal cycle"""
        cycle_mapping = {
            'daily': 'daily',
            'weekly': 'weekly',
            'monthly': 'monthly',
            'quarterly': 'quarterly',
            'yearly': 'yearly',
            'one_time': 'one_time',
            'onetime': 'one_time',
            'month': 'monthly',
            'week': 'weekly',
            'day': 'daily',
            'year': 'yearly',
        }
        return cycle_mapping.get(external_cycle.lower(), 'monthly')
    
    def _map_product_type_from_tmf(self, product_data: Dict, features: Dict) -> str:
        """Map TMF620 product data to internal product type"""
        # Check if bundle
        if product_data.get('isBundle', False):
            return 'bundle'
        
        # Check characteristics
        if 'data_allowance' in features or 'data_quota' in features:
            if 'voice_minutes' in features or 'voice_allowance' in features:
                return 'bundle'
            return 'data'
        
        if 'voice_minutes' in features or 'voice_allowance' in features:
            return 'voice'
        
        if 'sms_allowance' in features or 'sms_quota' in features:
            return 'sms'
        
        # Check category
        categories = product_data.get('category', [])
        if categories:
            category_name = categories[0].get('name', '').lower()
            if 'device' in category_name:
                return 'device'
            if 'addon' in category_name or 'add-on' in category_name:
                return 'addon'
            if 'service' in category_name:
                return 'service'
        
        # Default
        return 'bundle'


class ProductCatalogService:
    """Service to query and manage product catalog"""
    
    @staticmethod
    def get_product_by_external_id(external_product_id: str, external_system: str = 'xiva') -> Optional[Product]:
        """Get product by external ID"""
        try:
            return Product.objects.get(
                external_product_id=external_product_id,
                external_system=external_system
            )
        except Product.DoesNotExist:
            return None
    
    @staticmethod
    def get_available_products_for_campaign(customer_value: float = None) -> List[Product]:
        """Get available products for campaign targeting"""
        queryset = Product.objects.filter(is_active=True, is_available=True)
        
        if customer_value is not None:
            queryset = queryset.filter(
                Q(min_customer_value__isnull=True) | Q(min_customer_value__lte=customer_value),
                Q(max_customer_value__isnull=True) | Q(max_customer_value__gte=customer_value)
            )
        
        return list(queryset.order_by('name'))
    
    @staticmethod
    def get_products_by_type(product_type: str) -> List[Product]:
        """Get products by type"""
        return list(Product.objects.filter(
            product_type=product_type,
            is_active=True
        ).order_by('name'))
    
    @staticmethod
    def get_products_for_ml_recommendation(customer_features: Dict) -> List[Product]:
        """Get products suitable for ML recommendation based on customer features"""
        # This can be enhanced with ML-based filtering
        queryset = Product.objects.filter(is_active=True, is_available=True)
        
        # Filter by customer value if available
        customer_value = customer_features.get('lifetime_value') or customer_features.get('total_revenue')
        if customer_value:
            queryset = queryset.filter(
                Q(min_customer_value__isnull=True) | Q(min_customer_value__lte=customer_value),
                Q(max_customer_value__isnull=True) | Q(max_customer_value__gte=customer_value)
            )
        
        return list(queryset.order_by('name')[:10])  # Limit to top 10

