"""
Feature Store for ML models.
Caches DWH features in Redis to reduce DWH load.
"""

from typing import Dict, List, Optional
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    import redis
    redis_available = True
except ImportError:
    redis_available = False
    logger.warning("Redis not available. Feature caching disabled.")

from loyalty.integration.dwh import get_dwh_connector

# Try to import Xiva feature extractor (optional)
try:
    from loyalty.integration.xiva_feature_extractor import XivaFeatureExtractor
    xiva_available = True
except ImportError:
    xiva_available = False
    logger.debug("Xiva feature extractor not available")

if redis_available:
    redis_client = redis.Redis(
        host=getattr(settings, 'REDIS_HOST', 'localhost'),
        port=getattr(settings, 'REDIS_PORT', 6379),
        db=getattr(settings, 'REDIS_FEATURE_STORE_DB', 1),
        decode_responses=True
    )
else:
    redis_client = None


class FeatureStore:
    """Feature store with Redis caching - supports DWH and Xiva"""
    
    CACHE_TTL = 3600  # 1 hour
    
    @staticmethod
    def get_customer_features(customer_id: str, use_cache: bool = True, 
                              data_source: str = None) -> Dict:
        """
        Get customer features from DWH or Xiva (with caching)
        
        Args:
            customer_id: Customer ID
            use_cache: Use Redis cache
            data_source: 'dwh', 'xiva', or None/'auto' (try both, Xiva first if available)
        """
        cache_key = f"features:{customer_id}"
        
        # Try cache first
        if use_cache and redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit for customer {customer_id}")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        # Determine data source
        if data_source is None:
            data_source = getattr(settings, 'FEATURE_STORE_DATA_SOURCE', 'auto')
        
        merge_strategy = getattr(settings, 'FEATURE_STORE_MERGE_STRATEGY', 'xiva_first')
        features = {}
        
        # Fetch from Xiva if requested or auto
        if data_source in ('auto', 'xiva') and xiva_available:
            try:
                xiva_features = XivaFeatureExtractor.extract_customer_features(customer_id)
                if xiva_features and len(xiva_features) > 1:  # More than just customer_id
                    features.update(xiva_features)
                    logger.debug(f"Got features from Xiva for customer {customer_id}")
            except Exception as e:
                logger.warning(f"Error fetching from Xiva: {e}")
        
        # Fetch from DWH if requested or auto
        if data_source in ('auto', 'dwh'):
            try:
                import uuid
                # Ensure customer_id is a string (handle UUID objects)
                customer_id_str = str(customer_id) if not isinstance(customer_id, str) else customer_id
                connector = get_dwh_connector()
                dwh_features = connector.get_customer_features(customer_id_str)
                
                if dwh_features:
                    if merge_strategy == 'xiva_first' and features:
                        # Xiva values override DWH, but fill gaps from DWH
                        merged = dwh_features.copy()
                        merged.update(features)  # Xiva takes precedence
                        features = merged
                    elif merge_strategy == 'dwh_first':
                        # DWH values override Xiva
                        features.update(dwh_features)
                    elif merge_strategy == 'merge':
                        # Merge both (Xiva first, then DWH)
                        merged = features.copy()
                        merged.update(dwh_features)
                        features = merged
                    else:
                        # No existing features, use DWH
                        features = dwh_features
                    
                    logger.debug(f"Got features from DWH for customer {customer_id}")
            except Exception as e:
                logger.warning(f"Error fetching from DWH: {e}")
        
        # Cache result
        if use_cache and redis_client and features:
            try:
                # Convert Decimal, datetime, UUID, and other types to JSON-serializable types
                def convert_for_json(obj):
                    from decimal import Decimal
                    from datetime import datetime, date
                    import uuid
                    if isinstance(obj, Decimal):
                        return float(obj)
                    elif isinstance(obj, (datetime, date)):
                        # Convert datetime/date to ISO format string
                        return obj.isoformat()
                    elif isinstance(obj, uuid.UUID):
                        # Convert UUID to string
                        return str(obj)
                    elif isinstance(obj, dict):
                        return {k: convert_for_json(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_for_json(item) for item in obj]
                    return obj
                
                features_serializable = convert_for_json(features)
                redis_client.setex(
                    cache_key,
                    FeatureStore.CACHE_TTL,
                    json.dumps(features_serializable)
                )
                logger.debug(f"Cached features for customer {customer_id}")
            except Exception as e:
                logger.warning(f"Redis cache write error: {e}")
        
        return features
    
    @staticmethod
    def invalidate_cache(customer_id: str):
        """Invalidate cached features for customer"""
        if not redis_client:
            return
        
        cache_key = f"features:{customer_id}"
        try:
            redis_client.delete(cache_key)
            logger.debug(f"Invalidated cache for customer {customer_id}")
        except Exception as e:
            logger.warning(f"Redis cache invalidation error: {e}")
    
    @staticmethod
    def batch_get_features(customer_ids: List[str]) -> Dict[str, Dict]:
        """Batch fetch features for multiple customers"""
        results = {}
        missing_ids = []
        
        # Try cache first
        if redis_client:
            for customer_id in customer_ids:
                cache_key = f"features:{customer_id}"
                try:
                    cached = redis_client.get(cache_key)
                    if cached:
                        results[customer_id] = json.loads(cached)
                    else:
                        missing_ids.append(customer_id)
                except Exception as e:
                    logger.warning(f"Redis cache read error: {e}")
                    missing_ids.append(customer_id)
        else:
            missing_ids = customer_ids
        
        # Fetch missing from data source
        if missing_ids:
            data_source = getattr(settings, 'FEATURE_STORE_DATA_SOURCE', 'auto')
            
            # Try Xiva first if available
            if data_source in ('auto', 'xiva') and xiva_available:
                for customer_id in missing_ids:
                    try:
                        features = XivaFeatureExtractor.extract_customer_features(customer_id)
                        if features and len(features) > 1:
                            results[customer_id] = features
                            
                            # Cache
                            if redis_client:
                                try:
                                    cache_key = f"features:{customer_id}"
                                    redis_client.setex(
                                        cache_key,
                                        FeatureStore.CACHE_TTL,
                                        json.dumps(features)
                                    )
                                except Exception as e:
                                    logger.warning(f"Redis cache write error: {e}")
                    except Exception as e:
                        logger.warning(f"Error fetching from Xiva for {customer_id}: {e}")
            
            # Try DWH for remaining missing
            if data_source in ('auto', 'dwh'):
                still_missing = [cid for cid in missing_ids if cid not in results]
                if still_missing:
                    try:
                        import uuid
                        connector = get_dwh_connector()
                        for customer_id in still_missing:
                            # Ensure customer_id is a string (handle UUID objects)
                            customer_id_str = str(customer_id) if not isinstance(customer_id, str) else customer_id
                            features = connector.get_customer_features(customer_id_str)
                            if features:
                                results[customer_id] = features
                                
                                # Cache
                                if redis_client:
                                    try:
                                        cache_key = f"features:{customer_id}"
                                        redis_client.setex(
                                            cache_key,
                                            FeatureStore.CACHE_TTL,
                                            json.dumps(features)
                                        )
                                    except Exception as e:
                                        logger.warning(f"Redis cache write error: {e}")
                    except Exception as e:
                        logger.error(f"Error batch fetching features from DWH: {e}")
        
        return results

