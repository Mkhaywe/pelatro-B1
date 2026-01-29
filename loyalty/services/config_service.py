"""
Configuration Service
Manages system configuration with database storage and fallback to defaults.
"""
from typing import Dict, Any, Optional
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Import default configurations
try:
    from loyalty.config.ml_config import (
        DEFAULT_ML_FEATURE_MAPPING,
        DEFAULT_ML_MODEL_INPUT_SIZE,
        DEFAULT_ML_MODEL_PATHS,
        DEFAULT_ML_CONFIG,
    )
except ImportError:
    # Fallback if config file doesn't exist
    DEFAULT_ML_FEATURE_MAPPING = {}
    DEFAULT_ML_MODEL_INPUT_SIZE = 10
    DEFAULT_ML_MODEL_PATHS = {}
    DEFAULT_ML_CONFIG = {}


class ConfigurationService:
    """Service to get/set configuration with database + defaults fallback"""
    
    @staticmethod
    def get_ml_feature_mapping() -> Dict[str, str]:
        """Get ML feature mapping (database → config file → settings.py → default)
        
        Returns:
            Dict mapping model feature names to DWH column names
        """
        # Try database first
        try:
            from loyalty.models_khaywe import SystemConfiguration
            db_mapping = SystemConfiguration.get_config('ml', 'feature_mapping')
            if db_mapping:
                logger.debug("Using ML feature mapping from database")
                return db_mapping
        except Exception as e:
            logger.debug(f"Could not load from database: {e}")
        
        # Fallback to config file
        if DEFAULT_ML_FEATURE_MAPPING:
            logger.debug("Using ML feature mapping from config file")
            return DEFAULT_ML_FEATURE_MAPPING.copy()
        
        # Fallback to settings.py (for backward compatibility)
        settings_mapping = getattr(settings, 'ML_FEATURE_MAPPING', {})
        if settings_mapping:
            logger.debug("Using ML feature mapping from settings.py")
            return settings_mapping
        
        # Final fallback
        logger.warning("No ML feature mapping found, using empty dict")
        return {}
    
    @staticmethod
    def set_ml_feature_mapping(mapping: Dict[str, str], updated_by: str = 'system') -> bool:
        """Save ML feature mapping to database
        
        Args:
            mapping: Feature mapping dict
            updated_by: User/system making the change
        
        Returns:
            True if successful
        """
        try:
            from loyalty.models_khaywe import SystemConfiguration
            SystemConfiguration.set_config(
                category='ml',
                key='feature_mapping',
                value=mapping,
                description='ML feature mapping: DWH columns → model features',
                updated_by=updated_by
            )
            logger.info(f"ML feature mapping updated by {updated_by}")
            return True
        except Exception as e:
            logger.error(f"Error saving ML feature mapping: {e}")
            return False
    
    @staticmethod
    def get_ml_model_input_size() -> int:
        """Get ML model input size (database → config file → settings.py → default)"""
        try:
            from loyalty.models_khaywe import SystemConfiguration
            db_size = SystemConfiguration.get_config('ml', 'model_input_size')
            if db_size is not None:
                return int(db_size)
        except Exception:
            pass
        
        # Fallback to config file
        if DEFAULT_ML_MODEL_INPUT_SIZE:
            return DEFAULT_ML_MODEL_INPUT_SIZE
        
        # Fallback to settings.py
        return int(getattr(settings, 'ML_MODEL_INPUT_SIZE', 10))
    
    @staticmethod
    def set_ml_model_input_size(size: int, updated_by: str = 'system') -> bool:
        """Save ML model input size to database"""
        try:
            from loyalty.models_khaywe import SystemConfiguration
            SystemConfiguration.set_config(
                category='ml',
                key='model_input_size',
                value=size,
                description='Number of features expected by ML models',
                updated_by=updated_by
            )
            return True
        except Exception as e:
            logger.error(f"Error saving ML model input size: {e}")
            return False
    
    @staticmethod
    def get_ml_model_path(model_name: str) -> Optional[str]:
        """Get ML model path (database → config file → settings.py → default)"""
        try:
            from loyalty.models_khaywe import SystemConfiguration
            db_paths = SystemConfiguration.get_config('ml', 'model_paths')
            if db_paths and model_name in db_paths:
                return db_paths[model_name]
        except Exception:
            pass
        
        # Fallback to config file
        if DEFAULT_ML_MODEL_PATHS and model_name in DEFAULT_ML_MODEL_PATHS:
            return DEFAULT_ML_MODEL_PATHS[model_name]
        
        # Fallback to settings.py
        setting_key = f'ML_MODEL_{model_name.upper()}_PATH'
        return getattr(settings, setting_key, None)
    
    @staticmethod
    def get_all_ml_config() -> Dict[str, Any]:
        """Get all ML configuration (database → config file → settings.py → defaults)"""
        try:
            from loyalty.models_khaywe import SystemConfiguration
            db_configs = SystemConfiguration.get_all_category_configs('ml')
            if db_configs:
                # Merge with defaults for missing keys
                config = DEFAULT_ML_CONFIG.copy()
                config.update(db_configs)
                return config
        except Exception:
            pass
        
        # Fallback to config file
        config = DEFAULT_ML_CONFIG.copy()
        
        # Merge with settings.py for backward compatibility
        config['feature_mapping'] = getattr(settings, 'ML_FEATURE_MAPPING', config['feature_mapping'])
        config['model_input_size'] = int(getattr(settings, 'ML_MODEL_INPUT_SIZE', config['model_input_size']))
        config['mock_mode'] = getattr(settings, 'ML_MOCK_MODE', config.get('mock_mode', False))
        
        return config
    
    @staticmethod
    def set_ml_config(config: Dict[str, Any], updated_by: str = 'system') -> bool:
        """Save all ML configuration to database
        
        Args:
            config: Dict with keys: feature_mapping, model_input_size, model_paths, mock_mode
            updated_by: User/system making the change
        """
        try:
            from loyalty.models_khaywe import SystemConfiguration
            
            if 'feature_mapping' in config:
                ConfigurationService.set_ml_feature_mapping(config['feature_mapping'], updated_by)
            
            if 'model_input_size' in config:
                ConfigurationService.set_ml_model_input_size(config['model_input_size'], updated_by)
            
            if 'model_paths' in config:
                SystemConfiguration.set_config(
                    category='ml',
                    key='model_paths',
                    value=config['model_paths'],
                    description='ML model file paths',
                    updated_by=updated_by
                )
            
            if 'mock_mode' in config:
                SystemConfiguration.set_config(
                    category='ml',
                    key='mock_mode',
                    value=config['mock_mode'],
                    description='ML mock mode flag',
                    updated_by=updated_by
                )
            
            logger.info(f"ML configuration updated by {updated_by}")
            return True
        except Exception as e:
            logger.error(f"Error saving ML configuration: {e}")
            return False

