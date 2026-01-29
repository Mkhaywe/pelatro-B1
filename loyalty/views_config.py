"""
Configuration Management API
Allows frontend to configure data sources (Xiva, DWH), ML settings, and system configuration.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
import os
import logging
from pathlib import Path
from loyalty.models_khaywe import DeliveryChannelConfig

logger = logging.getLogger(__name__)


class ConfigurationViewSet(viewsets.ViewSet):
    """Configuration management endpoints"""
    permission_classes = [AllowAny]  # Allow unauthenticated access for development
    
    @action(detail=False, methods=['get'])
    def get_all(self, request):
        """Get all configuration (non-sensitive)"""
        return Response({
            'xiva': self._get_xiva_config(),
            'dwh': self._get_dwh_config(),
            'ml': self._get_ml_config(),
            'feature_store': self._get_feature_store_config(),
            'delivery_channels': self._get_delivery_channels_config(),
        })
    
    @action(detail=False, methods=['get'], url_path='xiva')
    def get_xiva_config(self, request):
        """Get Xiva configuration"""
        return Response(self._get_xiva_config())
    
    @action(detail=False, methods=['post'], url_path='xiva')
    def update_xiva_config(self, request):
        """Update Xiva configuration"""
        config = request.data
        
        # Update .env file
        env_path = Path(__file__).resolve().parent.parent.parent / '.env'
        
        try:
            # Read existing .env
            env_lines = []
            if env_path.exists():
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()
            
            # Update or add Xiva settings
            xiva_keys = {
                'XIVA_API_BASE_URL': config.get('base_url', ''),
                'XIVA_API_AUTH_TYPE': config.get('auth_type', 'JWT'),
                'XIVA_API_USERNAME': config.get('username', ''),
                'XIVA_API_PASSWORD': config.get('password', ''),
                'XIVA_API_AUTH_TOKEN': config.get('auth_token', ''),
                'XIVA_API_TIMEOUT': str(config.get('timeout', 30)),
            }
            
            # Update existing lines or add new ones
            updated_keys = set()
            new_lines = []
            
            for line in env_lines:
                line_stripped = line.strip()
                updated = False
                for key, value in xiva_keys.items():
                    if line_stripped.startswith(f'{key}='):
                        new_lines.append(f'{key}={value}\n')
                        updated_keys.add(key)
                        updated = True
                        break
                if not updated:
                    new_lines.append(line)
            
            # Add missing keys
            for key, value in xiva_keys.items():
                if key not in updated_keys:
                    new_lines.append(f'{key}={value}\n')
            
            # Write back
            with open(env_path, 'w') as f:
                f.writelines(new_lines)
            
            # Update os.environ for current process
            for key, value in xiva_keys.items():
                os.environ[key] = value
            
            # Reset Xiva client singleton
            try:
                from loyalty.integration.xiva_client import reset_xiva_client
                reset_xiva_client()
            except Exception as e:
                logger.warning(f"Could not reset Xiva client: {e}")
            
            return Response({
                'status': 'success',
                'message': 'Xiva configuration updated. Restart Django server to apply changes.'
            })
        except Exception as e:
            logger.error(f"Error updating Xiva config: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='dwh')
    def get_dwh_config(self, request):
        """Get DWH configuration"""
        return Response(self._get_dwh_config())
    
    @action(detail=False, methods=['post'], url_path='dwh')
    def update_dwh_config(self, request):
        """Update DWH configuration"""
        config = request.data
        env_path = Path(__file__).resolve().parent.parent.parent / '.env'
        
        try:
            env_lines = []
            if env_path.exists():
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()
            
            dwh_keys = {
                'DWH_TYPE': config.get('type', 'postgresql'),
                'DWH_POSTGRES_CONNECTION_STRING': config.get('postgres_connection_string', ''),
                'DWH_ORACLE_CONNECTION_STRING': config.get('oracle_connection_string', ''),
                'DWH_SNOWFLAKE_ACCOUNT': config.get('snowflake_account', ''),
                'DWH_USER': config.get('user', ''),
                'DWH_PASSWORD': config.get('password', ''),
                'DWH_CUSTOMER_FEATURES_QUERY': config.get('customer_features_query', ''),
                'DWH_CUSTOMER_FEATURES_TABLE': config.get('customer_features_table', 'customer_features_view'),
            }
            
            updated_keys = set()
            new_lines = []
            
            for line in env_lines:
                line_stripped = line.strip()
                updated = False
                for key, value in dwh_keys.items():
                    if line_stripped.startswith(f'{key}='):
                        new_lines.append(f'{key}={value}\n')
                        updated_keys.add(key)
                        updated = True
                        break
                if not updated:
                    new_lines.append(line)
            
            for key, value in dwh_keys.items():
                if key not in updated_keys:
                    new_lines.append(f'{key}={value}\n')
            
            with open(env_path, 'w') as f:
                f.writelines(new_lines)
            
            for key, value in dwh_keys.items():
                os.environ[key] = value
            
            return Response({
                'status': 'success',
                'message': 'DWH configuration updated. Restart Django server to apply changes.'
            })
        except Exception as e:
            logger.error(f"Error updating DWH config: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='ml')
    def get_ml_config(self, request):
        """Get ML configuration"""
        return Response(self._get_ml_config())
    
    @action(detail=False, methods=['get'], url_path='ml/status')
    def get_ml_status(self, request):
        """Get ML model status"""
        try:
            from loyalty.ml.inference import MLInferenceService, TENSORFLOW_AVAILABLE, NUMPY_AVAILABLE
            from django.conf import settings
            
            ml_service = MLInferenceService()
            
            # Check model files - get all model paths from ConfigurationService
            from loyalty.services.config_service import ConfigurationService
            
            all_models = ['nbo', 'churn', 'ltv', 'propensity', 'product', 'campaign', 'default_risk', 'upsell', 'engagement']
            model_status = {}
            
            for model_name in all_models:
                # Get path from ConfigurationService (database → config file → settings.py)
                path = ConfigurationService.get_ml_model_path(model_name)
                
                # Fallback to default paths if not configured
                if not path:
                    if model_name == 'nbo':
                        path = 'models/nbo.tflite'
                    elif model_name == 'churn':
                        path = 'models/churn.tflite'
                    elif model_name == 'ltv':
                        path = 'models/ltv.tflite'
                    elif model_name == 'propensity':
                        path = 'models/propensity.tflite'
                    elif model_name == 'product':
                        path = 'models/product.tflite'
                    elif model_name == 'campaign':
                        path = 'models/campaign.tflite'
                    elif model_name == 'default_risk':
                        path = 'models/default_risk.tflite'
                    elif model_name == 'upsell':
                        path = 'models/upsell.tflite'
                    elif model_name == 'engagement':
                        path = 'models/engagement.tflite'
                    else:
                        path = None
                
                if path:
                    model_file = Path(path)
                    model_status[model_name] = {
                        'path': path,
                        'exists': model_file.exists(),
                        'loaded': model_name in ml_service.models if hasattr(ml_service, 'models') else False,
                    }
                else:
                    model_status[model_name] = {
                        'path': 'N/A',
                        'exists': False,
                        'loaded': False,
                        'message': 'Model path not configured'
                    }
            
            return Response({
                'tensorflow_available': TENSORFLOW_AVAILABLE,
                'numpy_available': NUMPY_AVAILABLE,
                'mock_mode': getattr(settings, 'ML_MOCK_MODE', False),
                'models': model_status,
            })
        except Exception as e:
            logger.error(f"Error getting ML status: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='ml')
    def update_ml_config(self, request):
        """Update ML configuration (saves to database, can be changed via UI)"""
        config = request.data
        
        try:
            from loyalty.services.config_service import ConfigurationService
            
            # Get user info for audit trail
            updated_by = request.user.username if request.user.is_authenticated else 'api'
            
            # Prepare config dict
            ml_config = {}
            
            if 'feature_mapping' in config:
                ml_config['feature_mapping'] = config['feature_mapping']
            
            if 'model_input_size' in config:
                ml_config['model_input_size'] = int(config['model_input_size'])
            
            if 'mock_mode' in config:
                ml_config['mock_mode'] = bool(config['mock_mode'])
            
            # Model paths (store as dict)
            model_paths = {}
            if 'model_nbo_path' in config:
                model_paths['nbo'] = config['model_nbo_path']
            if 'model_churn_path' in config:
                model_paths['churn'] = config['model_churn_path']
            if 'model_ltv_path' in config:
                model_paths['ltv'] = config['model_ltv_path']
            if 'model_propensity_path' in config:
                model_paths['propensity'] = config['model_propensity_path']
            if 'model_product_path' in config:
                model_paths['product'] = config['model_product_path']
            if 'model_campaign_path' in config:
                model_paths['campaign'] = config['model_campaign_path']
            if 'model_default_path' in config:
                model_paths['default_risk'] = config['model_default_path']
            if 'model_upsell_path' in config:
                model_paths['upsell'] = config['model_upsell_path']
            if 'model_engagement_path' in config:
                model_paths['engagement'] = config['model_engagement_path']
            
            if model_paths:
                ml_config['model_paths'] = model_paths
            
            # Save to database
            if ml_config:
                success = ConfigurationService.set_ml_config(ml_config, updated_by=updated_by)
                if success:
                    return Response({
                        'status': 'success',
                        'message': 'ML configuration saved to database. Changes take effect immediately.',
                        'config': ConfigurationService.get_all_ml_config()
                    })
                else:
                    return Response({
                        'status': 'error',
                        'error': 'Failed to save configuration to database'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({
                    'status': 'error',
                    'error': 'No configuration provided'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error updating ML config: {e}")
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='dwh/features')
    def update_dwh_features_config(self, request):
        """Update DWH features configuration (table name, custom query)"""
        config = request.data
        
        env_path = Path(__file__).resolve().parent.parent.parent / '.env'
        
        try:
            # Read existing .env
            env_lines = []
            if env_path.exists():
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()
            
            # DWH features configuration
            dwh_config_updates = {}
            
            if 'customer_features_table' in config:
                dwh_config_updates['DWH_CUSTOMER_FEATURES_TABLE'] = str(config['customer_features_table'])
            if 'customer_features_query' in config:
                # Store query as-is (may contain newlines)
                dwh_config_updates['DWH_CUSTOMER_FEATURES_QUERY'] = str(config['customer_features_query'])
            
            # Update existing lines or add new ones
            updated_keys = set()
            new_lines = []
            
            for line in env_lines:
                line_stripped = line.strip()
                updated = False
                for key, value in dwh_config_updates.items():
                    if line_stripped.startswith(f'{key}='):
                        # Handle multi-line queries
                        if key == 'DWH_CUSTOMER_FEATURES_QUERY' and '\n' in value:
                            # Write query on multiple lines
                            new_lines.append(f'{key}="""\n')
                            new_lines.append(f'{value}\n')
                            new_lines.append('"""\n')
                        else:
                            new_lines.append(f'{key}={value}\n')
                        updated_keys.add(key)
                        updated = True
                        break
                if not updated:
                    new_lines.append(line)
            
            # Add missing keys
            for key, value in dwh_config_updates.items():
                if key not in updated_keys:
                    if key == 'DWH_CUSTOMER_FEATURES_QUERY' and '\n' in value:
                        new_lines.append(f'{key}="""\n')
                        new_lines.append(f'{value}\n')
                        new_lines.append('"""\n')
                    else:
                        new_lines.append(f'{key}={value}\n')
            
            # Write back
            with open(env_path, 'w') as f:
                f.writelines(new_lines)
            
            # Update settings for current process
            from django.conf import settings
            if 'customer_features_table' in config:
                settings.DWH_CUSTOMER_FEATURES_TABLE = config['customer_features_table']
            if 'customer_features_query' in config:
                settings.DWH_CUSTOMER_FEATURES_QUERY = config['customer_features_query']
            
            return Response({
                'status': 'success',
                'message': 'DWH features configuration updated. Restart Django server to apply changes.'
            })
        except Exception as e:
            logger.error(f"Error updating DWH features config: {e}")
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='ml/test')
    def test_ml_prediction(self, request):
        """Test ML prediction with a customer ID or batch of customer IDs"""
        customer_id = request.data.get('customer_id')
        customer_ids = request.data.get('customer_ids', [])  # Batch support
        prediction_type = request.data.get('type', 'churn')  # 'churn', 'nbo', 'rfm'
        
        # Support both single and batch
        if customer_ids and isinstance(customer_ids, list):
            # Batch prediction
            if not customer_ids:
                return Response({
                    'error': 'customer_ids list cannot be empty'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                from loyalty.ml.inference import MLInferenceService
                ml_service = MLInferenceService()
                
                results = []
                errors = []
                
                for cid in customer_ids:
                    try:
                        if prediction_type == 'churn':
                            result = ml_service.predict_churn(cid)
                        elif prediction_type == 'nbo':
                            result = ml_service.predict_nbo(cid)
                        elif prediction_type == 'rfm':
                            result = ml_service.calculate_rfm(cid)
                        elif prediction_type == 'ltv':
                            result = ml_service.predict_ltv(cid)
                        elif prediction_type == 'propensity':
                            result = ml_service.predict_propensity_to_buy(cid)
                        elif prediction_type == 'product':
                            result = ml_service.recommend_products(cid)
                        elif prediction_type == 'campaign':
                            result = ml_service.predict_campaign_response(cid, campaign_id="default")
                        elif prediction_type == 'default_risk':
                            result = ml_service.predict_payment_default_risk(cid)
                        elif prediction_type == 'upsell':
                            result = ml_service.predict_upsell_propensity(cid)
                        elif prediction_type == 'engagement':
                            result = ml_service.calculate_engagement_score(cid)
                        else:
                            errors.append({
                                'customer_id': cid,
                                'error': f'Invalid prediction type: {prediction_type}'
                            })
                            continue
                        
                        results.append({
                            'customer_id': cid,
                            'result': result,
                        })
                    except Exception as e:
                        errors.append({
                            'customer_id': cid,
                            'error': str(e)
                        })
                
                return Response({
                    'type': prediction_type,
                    'mode': 'batch',
                    'total': len(customer_ids),
                    'successful': len(results),
                    'failed': len(errors),
                    'results': results,
                    'errors': errors if errors else None,
                })
            except Exception as e:
                logger.error(f"Error testing batch ML prediction: {e}")
                return Response({
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Single prediction (backward compatible)
        elif customer_id:
            if not customer_id:
                return Response({
                    'error': 'customer_id required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                from loyalty.ml.inference import MLInferenceService
                ml_service = MLInferenceService()
                
                if prediction_type == 'churn':
                    result = ml_service.predict_churn(customer_id)
                elif prediction_type == 'nbo':
                    result = ml_service.predict_nbo(customer_id)
                elif prediction_type == 'rfm':
                    result = ml_service.calculate_rfm(customer_id)
                elif prediction_type == 'ltv':
                    result = ml_service.predict_ltv(customer_id)
                elif prediction_type == 'propensity':
                    result = ml_service.predict_propensity_to_buy(customer_id)
                elif prediction_type == 'product':
                    result = ml_service.recommend_products(customer_id)
                elif prediction_type == 'campaign':
                    result = ml_service.predict_campaign_response(customer_id, campaign_id="default")
                elif prediction_type == 'default_risk':
                    result = ml_service.predict_payment_default_risk(customer_id)
                elif prediction_type == 'upsell':
                    result = ml_service.predict_upsell_propensity(customer_id)
                elif prediction_type == 'engagement':
                    result = ml_service.calculate_engagement_score(customer_id)
                else:
                    return Response({
                        'error': f'Invalid prediction type: {prediction_type}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({
                    'customer_id': customer_id,
                    'type': prediction_type,
                    'mode': 'single',
                    'result': result,
                })
            except Exception as e:
                logger.error(f"Error testing ML prediction: {e}")
                return Response({
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                'error': 'Either customer_id or customer_ids required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='xiva/test')
    def test_xiva_connection(self, request):
        """Test Xiva API connection"""
        try:
            from loyalty.integration.xiva_client import get_xiva_client
            
            client = get_xiva_client()
            
            if not client.base_url:
                return Response({
                    'connected': False,
                    'error': 'Xiva API base URL not configured'
                })
            
            # Try to get customer list (simple test)
            try:
                customers = client.get_customer_list(limit=1)
                return Response({
                    'connected': True,
                    'base_url': client.base_url,
                    'auth_type': client.auth_type,
                    'has_token': client.access_token is not None,
                    'test_result': 'Successfully connected to Xiva API'
                })
            except Exception as e:
                return Response({
                    'connected': False,
                    'base_url': client.base_url,
                    'error': str(e)
                })
        except Exception as e:
            logger.error(f"Error testing Xiva connection: {e}")
            return Response({
                'connected': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='dwh/test')
    def test_dwh_connection(self, request):
        """Test DWH connection"""
        try:
            from loyalty.integration.dwh import get_dwh_connector
            
            try:
                connector = get_dwh_connector()
                
                # Check if connector is properly configured
                dwh_type = getattr(settings, 'DWH_TYPE', 'postgresql')
                
                # For PostgreSQL, check if connection string is set
                if dwh_type == 'postgresql':
                    conn_str = getattr(settings, 'DWH_POSTGRES_CONNECTION_STRING', '')
                    if not conn_str:
                        return Response({
                            'connected': False,
                            'dwh_type': dwh_type,
                            'error': 'DWH connection string not configured'
                        })
                
                # Try a simple query (this may fail if DWH is not accessible, but connector is initialized)
                try:
                    test_result = connector.get_customer_features('test-customer-id')
                    return Response({
                        'connected': True,
                        'dwh_type': dwh_type,
                        'test_result': 'DWH connector initialized successfully'
                    })
                except Exception as query_error:
                    # Connector initialized but query failed (DWH may not be accessible)
                    return Response({
                        'connected': False,
                        'dwh_type': dwh_type,
                        'error': f'DWH connector initialized but query failed: {str(query_error)}'
                    })
            except ImportError as import_error:
                return Response({
                    'connected': False,
                    'dwh_type': getattr(settings, 'DWH_TYPE', 'unknown'),
                    'error': f'DWH connector not available: {str(import_error)}'
                })
            except Exception as init_error:
                return Response({
                    'connected': False,
                    'dwh_type': getattr(settings, 'DWH_TYPE', 'unknown'),
                    'error': f'Failed to initialize DWH connector: {str(init_error)}'
                })
        except Exception as e:
            logger.error(f"Error testing DWH connection: {e}")
            return Response({
                'connected': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_xiva_config(self):
        """Get Xiva configuration (without passwords)"""
        return {
            'base_url': getattr(settings, 'XIVA_API_BASE_URL', ''),
            'auth_type': getattr(settings, 'XIVA_API_AUTH_TYPE', 'JWT'),
            'username': getattr(settings, 'XIVA_API_USERNAME', ''),
            'has_password': bool(getattr(settings, 'XIVA_API_PASSWORD', '')),
            'has_auth_token': bool(getattr(settings, 'XIVA_API_AUTH_TOKEN', '')),
            'timeout': getattr(settings, 'XIVA_API_TIMEOUT', 30),
        }
    
    def _get_dwh_config(self):
        """Get DWH configuration (without passwords)"""
        return {
            'type': getattr(settings, 'DWH_TYPE', 'postgresql'),
            'postgres_connection_string': getattr(settings, 'DWH_POSTGRES_CONNECTION_STRING', ''),
            'oracle_connection_string': getattr(settings, 'DWH_ORACLE_CONNECTION_STRING', ''),
            'snowflake_account': getattr(settings, 'DWH_SNOWFLAKE_ACCOUNT', ''),
            'user': getattr(settings, 'DWH_USER', ''),
            'has_password': bool(getattr(settings, 'DWH_PASSWORD', '')),
            'customer_features_query': getattr(settings, 'DWH_CUSTOMER_FEATURES_QUERY', ''),
            'customer_features_table': getattr(settings, 'DWH_CUSTOMER_FEATURES_TABLE', 'customer_features_view'),
        }
    
    def _get_ml_config(self):
        """Get ML configuration (from database → config file → settings.py)"""
        try:
            from loyalty.services.config_service import ConfigurationService
            config = ConfigurationService.get_all_ml_config()
            # Add model paths individually for backward compatibility and frontend
            all_models = ['nbo', 'churn', 'ltv', 'propensity', 'product', 'campaign', 'default_risk', 'upsell', 'engagement']
            for model_name in all_models:
                path = ConfigurationService.get_ml_model_path(model_name)
                if not path:
                    # Use default path
                    path = f'models/{model_name}.tflite'
                config_key = f'model_{model_name}_path' if model_name != 'default_risk' else 'model_default_path'
                config[config_key] = path
            return config
        except Exception as e:
            logger.warning(f"Could not load ML config from service: {e}, using settings.py")
            # Fallback to settings.py
            return {
                'mock_mode': getattr(settings, 'ML_MOCK_MODE', False),
                'model_nbo_path': getattr(settings, 'ML_MODEL_NBO_PATH', 'models/nbo.tflite'),
                'model_churn_path': getattr(settings, 'ML_MODEL_CHURN_PATH', 'models/churn.tflite'),
                'model_ltv_path': getattr(settings, 'ML_MODEL_LTV_PATH', 'models/ltv.tflite'),
                'model_propensity_path': getattr(settings, 'ML_MODEL_PROPENSITY_PATH', 'models/propensity.tflite'),
                'model_product_path': getattr(settings, 'ML_MODEL_PRODUCT_PATH', 'models/product.tflite'),
                'model_campaign_path': getattr(settings, 'ML_MODEL_CAMPAIGN_PATH', 'models/campaign.tflite'),
                'model_default_path': getattr(settings, 'ML_MODEL_DEFAULT_PATH', 'models/default_risk.tflite'),
                'model_upsell_path': getattr(settings, 'ML_MODEL_UPSELL_PATH', 'models/upsell.tflite'),
                'model_engagement_path': getattr(settings, 'ML_MODEL_ENGAGEMENT_PATH', 'models/engagement.tflite'),
                'model_input_size': getattr(settings, 'ML_MODEL_INPUT_SIZE', 10),
                'feature_mapping': getattr(settings, 'ML_FEATURE_MAPPING', {}),
            }
    
    def _get_feature_store_config(self):
        """Get Feature Store configuration"""
        return {
            'data_source': getattr(settings, 'FEATURE_STORE_DATA_SOURCE', 'auto'),
            'merge_strategy': getattr(settings, 'FEATURE_STORE_MERGE_STRATEGY', 'xiva_first'),
        }
    
    def _get_delivery_channels_config(self):
        """Get delivery channel configurations"""
        channels = DeliveryChannelConfig.objects.all()
        return {
            channel.channel: {
                'id': channel.id,
                'channel': channel.channel,
                'is_enabled': channel.is_enabled,
                'delivery_mode': channel.delivery_mode,
                'kafka_topic': channel.kafka_topic,
                'kafka_brokers': channel.kafka_brokers,
                'api_endpoint': channel.api_endpoint,
                'api_method': channel.api_method,
                'api_auth_type': channel.api_auth_type,
                'channel_settings': channel.channel_settings,
            }
            for channel in channels
        }
    
    @action(detail=False, methods=['get', 'post'], url_path='delivery-channels')
    def delivery_channels(self, request):
        """Get or update delivery channel configurations"""
        if request.method == 'GET':
            return Response(self._get_delivery_channels_config())
        
        # POST: Update channel configurations
        channels_data = request.data
        updated = []
        
        for channel_id, config in channels_data.items():
            try:
                channel = DeliveryChannelConfig.objects.get(channel=channel_id)
            except DeliveryChannelConfig.DoesNotExist:
                channel = DeliveryChannelConfig(channel=channel_id)
            
            channel.is_enabled = config.get('is_enabled', True)
            channel.delivery_mode = config.get('delivery_mode', 'api')
            channel.kafka_topic = config.get('kafka_topic', '')
            channel.kafka_brokers = config.get('kafka_brokers', [])
            channel.kafka_config = config.get('kafka_config', {})
            channel.api_endpoint = config.get('api_endpoint', '')
            channel.api_method = config.get('api_method', 'POST')
            channel.api_headers = config.get('api_headers', {})
            channel.api_auth_type = config.get('api_auth_type', '')
            channel.api_auth_config = config.get('api_auth_config', {})
            channel.channel_settings = config.get('channel_settings', {})
            channel.created_by = request.user.username if hasattr(request.user, 'username') else 'system'
            channel.save()
            updated.append(channel_id)
        
        return Response({
            'success': True,
            'updated_channels': updated,
            'message': f'Updated {len(updated)} channel configuration(s)'
        })

