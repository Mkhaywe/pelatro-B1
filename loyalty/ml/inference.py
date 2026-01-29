"""
ML Inference Service that uses DWH features.
All inference happens on-premise (server-side) for privacy compliance.
No external ML API calls - models run on your infrastructure.
"""

from typing import Dict, List, Optional
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Optional ML dependencies
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy not available. ML inference disabled.")
    np = None

try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow not available. ML inference disabled.")
    tf = None

from loyalty.integration.feature_store import FeatureStore
from django.conf import settings

# Check if mock mode is enabled
# Default to False (matches settings.py default)
# Set ML_MOCK_MODE=True in environment or settings to enable mock mode
MOCK_ML_ENABLED = getattr(settings, 'ML_MOCK_MODE', False)

if MOCK_ML_ENABLED:
    from loyalty.ml.mock_inference import MockMLInferenceService


class MLInferenceService:
    """ML inference service with DWH feature extraction"""
    
    def __init__(self):
        self.models = {}
        if TENSORFLOW_AVAILABLE and NUMPY_AVAILABLE:
            self._load_models()
        else:
            logger.warning("ML Inference Service initialized but ML dependencies not available")
    
    def _load_models(self):
        """Load TFLite models"""
        from loyalty.services.config_service import ConfigurationService
        
        # Get model paths from ConfigurationService (database → config file → settings.py)
        model_paths = {
            'nbo': ConfigurationService.get_ml_model_path('nbo') or 'models/nbo.tflite',
            'churn': ConfigurationService.get_ml_model_path('churn') or 'models/churn.tflite',
            'ltv': ConfigurationService.get_ml_model_path('ltv') or 'models/ltv.tflite',
            'propensity': ConfigurationService.get_ml_model_path('propensity') or 'models/propensity.tflite',
            'product': ConfigurationService.get_ml_model_path('product') or 'models/product.tflite',
            'campaign': ConfigurationService.get_ml_model_path('campaign') or 'models/campaign.tflite',
            'default_risk': ConfigurationService.get_ml_model_path('default_risk') or 'models/default_risk.tflite',
            'upsell': ConfigurationService.get_ml_model_path('upsell') or 'models/upsell.tflite',
            'engagement': ConfigurationService.get_ml_model_path('engagement') or 'models/engagement.tflite',
            'rfm': None,  # RFM is calculated, not ML model
        }
        
        for name, path in model_paths.items():
            if path:
                try:
                    interpreter = tf.lite.Interpreter(model_path=path)
                    interpreter.allocate_tensors()
                    self.models[name] = interpreter
                    logger.info(f"Loaded ML model: {name}")
                except Exception as e:
                    logger.error(f"Error loading model {name}: {e}")
    
    def _extract_features(self, customer_id: str, return_raw_features: bool = False):
        """Extract features from DWH for ML model
        
        Args:
            customer_id: Customer ID
            return_raw_features: If True, return tuple (feature_array, raw_features_dict)
        
        Returns:
            If return_raw_features=False: numpy array of features
            If return_raw_features=True: tuple (numpy array, raw features dict)
        """
        if not NUMPY_AVAILABLE:
            logger.error("NumPy not available")
            return None
        
        from django.conf import settings
        
        features = FeatureStore.get_customer_features(customer_id)
        
        if not features:
            logger.warning(f"No features found for customer {customer_id}")
            # Return zeros with expected model input size
            try:
                from loyalty.services.config_service import ConfigurationService
                expected_size = ConfigurationService.get_ml_model_input_size()
            except Exception:
                expected_size = getattr(settings, 'ML_MODEL_INPUT_SIZE', 10)
            if return_raw_features:
                return (np.zeros((1, expected_size), dtype=np.float32), {})
            return np.zeros((1, expected_size), dtype=np.float32)
        
        # Get feature mapping from configuration service (database → config file → settings.py)
        try:
            from loyalty.services.config_service import ConfigurationService
            feature_mapping = ConfigurationService.get_ml_feature_mapping()
        except Exception as e:
            logger.warning(f"Could not load feature mapping from config service: {e}, using settings.py")
            # Fallback to settings.py for backward compatibility
            feature_mapping = getattr(settings, 'ML_FEATURE_MAPPING', {})
        
        if not feature_mapping:
            logger.warning("ML_FEATURE_MAPPING not configured. Using all DWH features as-is.")
            # Fallback: use all numeric features from DWH
            feature_vector = []
            for k, v in features.items():
                if k != 'customer_id' and isinstance(v, (int, float)):
                    feature_vector.append(float(v))
        else:
            # Map DWH columns to model features using configuration
            feature_vector = []
            for model_feature, dwh_column in feature_mapping.items():
                value = features.get(dwh_column, 0)
                try:
                    feature_vector.append(float(value))
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert {dwh_column} to float, using 0")
                    feature_vector.append(0.0)
        
        # Pad or truncate to expected size
        try:
            from loyalty.services.config_service import ConfigurationService
            expected_size = ConfigurationService.get_ml_model_input_size()
        except Exception:
            expected_size = getattr(settings, 'ML_MODEL_INPUT_SIZE', 10)
        
        # Always ensure we have exactly expected_size features
        if len(feature_vector) < expected_size:
            # Pad with zeros if we have fewer features
            feature_vector.extend([0.0] * (expected_size - len(feature_vector)))
            logger.debug(f"Padded feature vector from {len(feature_vector) - (expected_size - (len(feature_vector) - (expected_size - len(feature_vector))))} to {len(feature_vector)} features")
        elif len(feature_vector) > expected_size:
            # Truncate if we have more features
            feature_vector = feature_vector[:expected_size]
            logger.debug(f"Truncated feature vector from {len(feature_vector) + (len(feature_vector) - expected_size)} to {len(feature_vector)} features")
        
        # Final safety check - ensure we have exactly expected_size
        if len(feature_vector) != expected_size:
            logger.warning(f"Feature vector size mismatch: got {len(feature_vector)}, expected {expected_size}. Force padding/truncating.")
            if len(feature_vector) < expected_size:
                feature_vector.extend([0.0] * (expected_size - len(feature_vector)))
            else:
                feature_vector = feature_vector[:expected_size]
        
        # Log final feature vector size for debugging
        logger.debug(f"Final feature vector size: {len(feature_vector)}, expected: {expected_size}")
        
        if np:
            feature_array = np.array([feature_vector], dtype=np.float32)
            logger.debug(f"Feature array shape: {feature_array.shape}")
            if return_raw_features:
                return (feature_array, features)
            return feature_array
        return None
    
    def predict_nbo(self, customer_id: str) -> Dict:
        """Predict Next Best Offer"""
        # Use mock service if enabled
        if MOCK_ML_ENABLED:
            mock_service = MockMLInferenceService()
            return mock_service.predict_nbo(customer_id)
        
        if not TENSORFLOW_AVAILABLE or not NUMPY_AVAILABLE:
            return {'error': 'ML dependencies (TensorFlow/NumPy) not available. Please install required packages.'}
        if 'nbo' not in self.models:
            logger.error("NBO model not loaded")
            return {'error': 'NBO model not available. Please ensure model file exists and is properly configured.'}
        
        # Extract features from DWH (with raw features for explanation)
        result = self._extract_features(customer_id, return_raw_features=True)
        if result is None:
            return {'error': 'Unable to extract features from DWH. Please ensure DWH is configured and customer data is available.'}
        
        features, raw_features = result
        if features is None:
            return {'error': 'Unable to extract features from DWH. Please ensure DWH is configured and customer data is available.'}
        
        try:
            # Run inference
            interpreter = self.models['nbo']
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            
            # Validate and fix feature dimensions if needed
            expected_shape = input_details[0]['shape']
            # TensorFlow shape is like [1, 10], we need to check the feature dimension (index 1)
            expected_feature_count = expected_shape[1] if len(expected_shape) > 1 else expected_shape[0]
            actual_feature_count = features.shape[1] if len(features.shape) > 1 else features.shape[0]
            
            if actual_feature_count != expected_feature_count:
                # Try to fix by padding or truncating
                logger.warning(f"Feature dimension mismatch: got {actual_feature_count}, expected {expected_feature_count}. Attempting to fix...")
                if actual_feature_count < expected_feature_count:
                    # Pad with zeros
                    padding = np.zeros((features.shape[0], expected_feature_count - actual_feature_count), dtype=np.float32)
                    features = np.concatenate([features, padding], axis=1)
                    logger.info(f"Padded features from {actual_feature_count} to {expected_feature_count}")
                else:
                    # Truncate
                    features = features[:, :expected_feature_count]
                    logger.info(f"Truncated features from {actual_feature_count} to {expected_feature_count}")
            
            interpreter.set_tensor(input_details[0]['index'], features)
            interpreter.invoke()
            output = interpreter.get_tensor(output_details[0]['index'])
            
            # Map output to offers (assuming output is probability scores)
            offer_scores = output[0].tolist()
            recommended_offer = int(np.argmax(offer_scores))
            confidence = float(np.max(offer_scores))
            
            # Generate explanation
            explanation = self._generate_nbo_explanation(raw_features, recommended_offer, confidence, offer_scores)
            
            # Get offer details from catalog if available
            offer_details = None
            try:
                from loyalty.services.offer_service import OfferCatalogService
                offer_service = OfferCatalogService()
                offer = offer_service.get_offer_by_id(recommended_offer)
                if offer:
                    offer_details = {
                        'offer_id': offer.offer_id,
                        'name': offer.name,
                        'description': offer.description,
                        'category': offer.category,
                        'lifecycle_stage': offer.lifecycle_stage,
                        'target_value_segment': offer.target_value_segment,
                    }
            except Exception as e:
                logger.debug(f"Could not fetch offer details: {e}")
            
            # Format all offers with details
            offers_list = self._format_offers_with_details(offer_scores)
            
            return {
                'customer_id': customer_id,
                'offer_scores': offer_scores,
                'recommended_offer': recommended_offer,
                'confidence': confidence,
                'explanation': explanation,
                'offer_details': offer_details,
                'offers': offers_list,
                'top_offer': {
                    'offer_id': recommended_offer,
                    'offer_name': offer_details.get('name', f'Offer #{recommended_offer}') if offer_details else f'Offer #{recommended_offer}',
                    'category': offer_details.get('category', 'points') if offer_details else 'points',
                    'probability': confidence
                } if offer_details else None
            }
        except Exception as e:
            logger.error(f"Error running NBO prediction: {e}")
            return {'error': f'ML inference error: {str(e)}. Please check model configuration and DWH setup.'}
    
    def predict_churn(self, customer_id: str) -> Dict:
        """Predict churn probability"""
        # Use mock service if enabled
        if MOCK_ML_ENABLED:
            mock_service = MockMLInferenceService()
            return mock_service.predict_churn(customer_id)
        
        if not TENSORFLOW_AVAILABLE or not NUMPY_AVAILABLE:
            return {'error': 'ML dependencies (TensorFlow/NumPy) not available. Please install required packages.'}
        if 'churn' not in self.models:
            logger.error("Churn model not loaded")
            return {'error': 'Churn model not available. Please ensure model file exists and is properly configured.'}
        
        # Extract features from DWH (with raw features for explanation)
        result = self._extract_features(customer_id, return_raw_features=True)
        if result is None:
            return {'error': 'Unable to extract features from DWH. Please ensure DWH is configured and customer data is available.'}
        
        features, raw_features = result
        if features is None:
            return {'error': 'Unable to extract features from DWH. Please ensure DWH is configured and customer data is available.'}
        
        try:
            interpreter = self.models['churn']
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            
            # Validate and fix feature dimensions if needed
            expected_shape = input_details[0]['shape']
            # TensorFlow shape is like [1, 10], we need to check the feature dimension (index 1)
            expected_feature_count = expected_shape[1] if len(expected_shape) > 1 else expected_shape[0]
            actual_feature_count = features.shape[1] if len(features.shape) > 1 else features.shape[0]
            
            if actual_feature_count != expected_feature_count:
                # Try to fix by padding or truncating
                logger.warning(f"Feature dimension mismatch: got {actual_feature_count}, expected {expected_feature_count}. Attempting to fix...")
                if actual_feature_count < expected_feature_count:
                    # Pad with zeros
                    padding = np.zeros((features.shape[0], expected_feature_count - actual_feature_count), dtype=np.float32)
                    features = np.concatenate([features, padding], axis=1)
                    logger.info(f"Padded features from {actual_feature_count} to {expected_feature_count}")
                else:
                    # Truncate
                    features = features[:, :expected_feature_count]
                    logger.info(f"Truncated features from {actual_feature_count} to {expected_feature_count}")
            
            interpreter.set_tensor(input_details[0]['index'], features)
            interpreter.invoke()
            churn_probability = interpreter.get_tensor(output_details[0]['index'])[0][0]
            
            churn_risk = 'high' if churn_probability > 0.7 else 'medium' if churn_probability > 0.4 else 'low'
            
            # Generate explanation
            explanation = self._generate_churn_explanation(raw_features, churn_probability, churn_risk)
            
            return {
                'customer_id': customer_id,
                'churn_probability': float(churn_probability),
                'churn_risk': churn_risk,
                'explanation': explanation
            }
        except Exception as e:
            logger.error(f"Error running churn prediction: {e}")
            return {'error': f'ML inference error: {str(e)}. Please check model configuration and DWH setup.'}
    
    def _generate_churn_explanation(self, raw_features: Dict, churn_probability: float, churn_risk: str) -> str:
        """Generate human-readable explanation for churn prediction
        
        The explanation should match the prediction:
        - LOW risk: Highlight positive factors (why customer is stable)
        - HIGH risk: Highlight negative factors (why customer is at risk)
        - MEDIUM risk: Mix of both
        """
        reasons = []
        
        # Helper to safely convert to float (handles Decimal, None, etc.)
        def to_float(val, default=0.0):
            if val is None:
                return default
            try:
                return float(val)
            except (TypeError, ValueError):
                return default
        
        # Days since last recharge/payment
        days_since_payment = to_float(raw_features.get('days_since_last_payment', 0))
        days_since_last = to_float(raw_features.get('days_since_last_transaction', 0))
        
        # Usage patterns
        current_month_usage = to_float(raw_features.get('current_month_usage_spend', 0))
        total_usage = to_float(raw_features.get('total_usage_spend', 0))
        usage_records = to_float(raw_features.get('usage_records_count', 0))
        
        # Service status
        active_services = to_float(raw_features.get('active_services_count', 0))
        total_services = to_float(raw_features.get('total_services_count', 0))
        
        # Payment behavior
        outstanding = to_float(raw_features.get('outstanding_amount', 0))
        payment_ratio = to_float(raw_features.get('payment_ratio', 1.0), 1.0)
        
        # Revenue
        total_revenue = to_float(raw_features.get('total_revenue', 0))
        current_spend = to_float(raw_features.get('current_month_spend', 0))
        monthly_avg = (total_revenue / 12) if total_revenue > 0 else 0.0
        
        # Credit utilization
        credit_utilization = to_float(raw_features.get('credit_utilization', 0))
        
        # Calculate risk factors (negative indicators)
        risk_score = 0.0
        risk_factors = []
        positive_factors = []
        
        # Risk factor 1: No usage
        if usage_records == 0:
            risk_score += 0.3
            risk_factors.append(("No usage records found", 0.3))
        elif current_month_usage == 0 and total_usage > 0:
            risk_score += 0.25
            risk_factors.append(("No usage activity this month despite historical usage", 0.25))
        elif current_month_usage > 0:
            positive_factors.append(f"Active usage this month (${current_month_usage:.2f})")
        
        # Risk factor 2: Outstanding balance
        if outstanding > 0:
            if outstanding > 1000:
                risk_score += 0.25
                risk_factors.append((f"High outstanding balance (${outstanding:.2f})", 0.25))
            elif outstanding > 500:
                risk_score += 0.15
                risk_factors.append((f"Outstanding balance of ${outstanding:.2f}", 0.15))
            else:
                risk_factors.append((f"Outstanding balance of ${outstanding:.2f}", 0.1))
        else:
            positive_factors.append("No outstanding balance")
        
        # Risk factor 3: Payment behavior
        if payment_ratio < 0.3:
            risk_score += 0.2
            risk_factors.append(("Very low payment ratio - not paying bills regularly", 0.2))
        elif payment_ratio < 0.5:
            risk_score += 0.1
            risk_factors.append(("Low payment ratio - irregular bill payments", 0.1))
        elif payment_ratio >= 0.9:
            positive_factors.append("Excellent payment history")
        
        # Risk factor 4: Revenue decline
        if monthly_avg > 0 and current_spend < monthly_avg * 0.3:
            risk_score += 0.2
            risk_factors.append(("Significant decline in monthly spending", 0.2))
        elif monthly_avg > 0 and current_spend >= monthly_avg * 0.8:
            positive_factors.append(f"Stable spending (${current_spend:.2f} vs ${monthly_avg:.2f} avg)")
        
        # Risk factor 5: Credit utilization
        if credit_utilization > 0.9:
            risk_score += 0.15
            risk_factors.append((f"Credit limit nearly maxed out ({credit_utilization*100:.0f}% utilization)", 0.15))
        elif credit_utilization > 0.7:
            risk_score += 0.1
            risk_factors.append((f"High credit utilization ({credit_utilization*100:.0f}%)", 0.1))
        
        # Risk factor 6: Days since payment
        # Use the most recent activity (smallest number of days)
        most_recent_days = min(
            days_since_payment if days_since_payment > 0 else 999,
            days_since_last if days_since_last > 0 else 999
        )
        
        if most_recent_days > 60:
            risk_score += 0.2
            risk_factors.append((f"Last activity was {int(most_recent_days)} days ago", 0.2))
        elif most_recent_days > 30:
            risk_score += 0.1
            risk_factors.append((f"Last activity was {int(most_recent_days)} days ago", 0.1))
        elif most_recent_days <= 7:
            positive_factors.append(f"Recent activity ({int(most_recent_days)} days ago)")
        elif most_recent_days <= 14:
            positive_factors.append(f"Moderate recency ({int(most_recent_days)} days ago)")
        
        # Risk factor 7: Service status
        if active_services == 0 and total_services > 0:
            risk_score += 0.25
            risk_factors.append(("No active services (all suspended/cancelled)", 0.25))
        elif active_services < total_services * 0.5:
            risk_score += 0.1
            risk_factors.append((f"Only {active_services} of {total_services} services active", 0.1))
        elif active_services == total_services and total_services > 0:
            positive_factors.append(f"All {active_services} services active")
        
        # Sort risk factors by weight (highest first)
        risk_factors.sort(key=lambda x: x[1], reverse=True)
        
        # Build explanation based on actual prediction
        explanation = f"Churn risk: {churn_risk.upper()} ({churn_probability*100:.0f}%). "
        
        if churn_risk == 'low' or churn_probability < 0.3:
            # LOW RISK: Explain why customer is stable
            if positive_factors:
                explanation += "Customer appears stable. Key factors: " + "; ".join(positive_factors[:4])
            else:
                # If no positive factors but still low risk, explain based on risk factors that are NOT present
                if risk_factors:
                    # Explain that despite some risk factors, overall risk is low
                    top_risk = risk_factors[0][0] if risk_factors else "some risk indicators"
                    explanation += f"Overall risk is low despite {top_risk.lower()}. Customer shows stable engagement patterns."
                else:
                    explanation += "Customer shows stable engagement and payment patterns with no significant risk indicators."
        elif churn_risk == 'high' or churn_probability > 0.7:
            # HIGH RISK: Explain why customer is at risk
            if risk_factors:
                top_risks = [factor[0] for factor in risk_factors[:4]]  # Top 4 risk factors
                explanation += "Key risk indicators: " + "; ".join(top_risks)
            else:
                explanation += "High churn risk based on overall customer behavior patterns and engagement decline."
        else:
            # MEDIUM RISK: Mix of both
            if risk_factors and positive_factors:
                top_risk = risk_factors[0][0] if risk_factors else None
                top_positive = positive_factors[0] if positive_factors else None
                explanation += f"Mixed signals: {top_risk.lower() if top_risk else 'some risk factors'}, but {top_positive.lower() if top_positive else 'some positive indicators'}."
            elif risk_factors:
                top_risks = [factor[0] for factor in risk_factors[:3]]
                explanation += "Moderate risk indicators: " + "; ".join(top_risks)
            else:
                explanation += "Moderate churn risk based on customer behavior patterns."
        
        return explanation
    
    def _generate_nbo_explanation(self, raw_features: Dict, recommended_offer: int, confidence: float, offer_scores: List[float]) -> str:
        """Generate human-readable explanation for NBO prediction"""
        reasons = []
        
        # Check if all offers have same score (dummy/mock data indicator)
        if len(offer_scores) > 1:
            unique_scores = set([round(score, 2) for score in offer_scores])
            if len(unique_scores) == 1:
                reasons.append("⚠️ All offers have identical scores - model may be using default/mock predictions")
        
        # Helper to safely convert to float (handles Decimal, None, etc.)
        def to_float(val, default=0.0):
            if val is None:
                return default
            try:
                return float(val)
            except (TypeError, ValueError):
                return default
        
        # Customer spending patterns
        total_revenue = to_float(raw_features.get('total_revenue', 0))
        current_spend = to_float(raw_features.get('current_month_spend', 0))
        
        if total_revenue > 1000:
            reasons.append(f"High-value customer (${total_revenue:.2f} lifetime revenue)")
        elif total_revenue > 0:
            reasons.append(f"Customer with ${total_revenue:.2f} lifetime revenue")
        
        if current_spend > 0:
            reasons.append(f"Current month spending: ${current_spend:.2f}")
        
        # Usage patterns
        usage_spend = to_float(raw_features.get('current_month_usage_spend', 0))
        if usage_spend > 0:
            reasons.append(f"Active usage this month (${usage_spend:.2f})")
        
        # Service status
        active_products = to_float(raw_features.get('active_products_count', 0))
        if active_products > 0:
            reasons.append(f"{int(active_products)} active product(s)")
        
        # Payment behavior
        days_since_payment = to_float(raw_features.get('days_since_last_payment', 0))
        if days_since_payment > 0:
            reasons.append(f"Last payment {int(days_since_payment)} days ago")
        
        # Build explanation
        if confidence >= 0.9:
            conf_text = "very high"
        elif confidence >= 0.7:
            conf_text = "high"
        elif confidence >= 0.5:
            conf_text = "moderate"
        else:
            conf_text = "low"
        
        explanation = f"Recommended Offer #{recommended_offer} with {conf_text} confidence ({confidence*100:.0f}%). "
        
        if reasons:
            explanation += "Based on: " + "; ".join(reasons[:4])  # Limit to top 4 reasons
        else:
            explanation += "Based on customer behavior patterns and purchase history."
        
        # Add warning if confidence is suspiciously high (likely mock data)
        if confidence >= 0.99 and len(offer_scores) > 1:
            explanation += " ⚠️ Note: Very high confidence may indicate model is using default predictions."
        
        return explanation
    
    def _format_offers_with_details(self, offer_scores: List[float]) -> List[Dict]:
        """Format offer scores with details from catalog"""
        try:
            from loyalty.services.offer_service import OfferCatalogService
            offer_service = OfferCatalogService()
            
            offers = []
            for idx, score in enumerate(offer_scores):
                offer = offer_service.get_offer_by_id(idx)
                if offer:
                    offers.append({
                        'offer_id': offer.offer_id,
                        'offer_name': offer.name,
                        'category': offer.category,
                        'probability': score
                    })
                else:
                    offers.append({
                        'offer_id': idx,
                        'offer_name': f'Offer #{idx}',
                        'category': 'points',
                        'probability': score
                    })
            return offers
        except Exception as e:
            logger.debug(f"Could not format offers with details: {e}")
            return []
    
    def calculate_rfm(self, customer_id: str) -> Dict:
        """Calculate RFM segment (rule-based, not ML)
        
        Uses configurable RFM column mapping from settings.
        You must configure RFM_COLUMN_MAPPING to map your DWH columns.
        """
        # Use mock service if enabled
        if MOCK_ML_ENABLED:
            mock_service = MockMLInferenceService()
            return mock_service.calculate_rfm(customer_id)
        
        from django.conf import settings
        
        features = FeatureStore.get_customer_features(customer_id)
        
        if not features:
            return {
                'customer_id': customer_id,
                'error': 'No features available from DWH or Xiva. Please ensure DWH is configured and customer data exists.'
            }
        
        # Get RFM column mapping from settings
        # Format: {'recency': 'dwh_column_name', 'frequency': '...', 'monetary': '...'}
        rfm_mapping = getattr(settings, 'RFM_COLUMN_MAPPING', {
            'recency': 'days_since_last_transaction',
            'frequency': 'transaction_count',
            'monetary': 'total_revenue'
        })
        
        # Extract RFM values from DWH features
        recency = float(features.get(rfm_mapping.get('recency', 'days_since_last_transaction'), 999))
        frequency = float(features.get(rfm_mapping.get('frequency', 'transaction_count'), 0))
        monetary = float(features.get(rfm_mapping.get('monetary', 'total_revenue'), 0))
        
        # Get RFM thresholds from settings (configurable)
        rfm_thresholds = getattr(settings, 'RFM_THRESHOLDS', {
            'recency': [30, 60, 90, 180],
            'frequency': [2, 5, 10, 20],
            'monetary': [100, 200, 500, 1000]
        })
        
        # RFM scoring (1-5 scale) - configurable thresholds
        r_thresholds = rfm_thresholds.get('recency', [30, 60, 90, 180])
        r_score = (
            5 if recency <= r_thresholds[0] else
            4 if recency <= r_thresholds[1] else
            3 if recency <= r_thresholds[2] else
            2 if recency <= r_thresholds[3] else
            1
        )
        
        f_thresholds = rfm_thresholds.get('frequency', [2, 5, 10, 20])
        f_score = (
            5 if frequency >= f_thresholds[3] else
            4 if frequency >= f_thresholds[2] else
            3 if frequency >= f_thresholds[1] else
            2 if frequency >= f_thresholds[0] else
            1
        )
        
        m_thresholds = rfm_thresholds.get('monetary', [100, 200, 500, 1000])
        m_score = (
            5 if monetary >= m_thresholds[3] else
            4 if monetary >= m_thresholds[2] else
            3 if monetary >= m_thresholds[1] else
            2 if monetary >= m_thresholds[0] else
            1
        )
        
        # RFM Segment name mapping
        rfm_segment_code = f"{r_score}{f_score}{m_score}"
        segment_names = {
            '555': 'Champions', '554': 'Champions', '544': 'Loyal Customers', '545': 'Champions',
            '455': 'Potential Loyalists', '454': 'Potential Loyalists', '445': 'Potential Loyalists', '444': 'Loyal Customers',
            '355': 'At Risk', '354': 'At Risk', '345': 'At Risk', '344': 'Need Attention',
            '255': 'Cannot Lose Them', '254': 'At Risk', '245': 'At Risk', '244': 'At Risk',
            '155': 'Cannot Lose Them', '154': 'Hibernating', '145': 'About to Sleep', '144': 'Lost',
            '111': 'Lost', '112': 'Lost', '113': 'Lost', '114': 'Lost', '115': 'Lost',
            '211': 'Lost', '212': 'Lost', '213': 'Lost', '214': 'Lost', '215': 'Lost',
            '311': 'Lost', '312': 'Lost', '313': 'Lost', '314': 'Lost', '315': 'Lost',
            '411': 'Lost', '412': 'Lost', '413': 'Lost', '414': 'Lost', '415': 'Lost',
            '511': 'Lost', '512': 'Lost', '513': 'Lost', '514': 'Lost', '515': 'Lost',
        }
        
        segment_name = segment_names.get(rfm_segment_code, 'Regular')
        
        return {
            'customer_id': customer_id,
            'recency': recency,
            'frequency': frequency,
            'monetary': monetary,
            'r_score': r_score,
            'f_score': f_score,
            'm_score': m_score,
            'rfm_segment': rfm_segment_code,
            'segment': segment_name,
            'recency_score': r_score,
            'frequency_score': f_score,
            'monetary_score': m_score,
            'recency_days': recency,
            'frequency_count': frequency,
            'monetary_value': monetary,
        }
    
    def predict_ltv(self, customer_id: str) -> Dict:
        """Predict customer lifetime value"""
        if MOCK_ML_ENABLED:
            mock_service = MockMLInferenceService()
            return mock_service.predict_ltv(customer_id)
        
        if not TENSORFLOW_AVAILABLE or not NUMPY_AVAILABLE:
            return {'error': 'ML dependencies (TensorFlow/NumPy) not available.'}
        if 'ltv' not in self.models:
            logger.warning("LTV model not available - using calculated value")
            features = FeatureStore.get_customer_features(customer_id)
            lifetime_value = float(features.get('lifetime_value', 0) or 0)
            return {
                'customer_id': customer_id,
                'predicted_ltv': lifetime_value,
                'confidence': 0.5,
                'note': 'Using current lifetime value (LTV model not trained)'
            }
        
        # Extract features and run inference
        result = self._extract_features(customer_id, return_raw_features=True)
        if result is None:
            return {'error': 'Unable to extract features from DWH.'}
        
        features, raw_features = result
        if features is None:
            return {'error': 'Unable to extract features from DWH.'}
        
        try:
            interpreter = self.models['ltv']
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            
            # Validate dimensions
            expected_feature_count = input_details[0]['shape'][1] if len(input_details[0]['shape']) > 1 else input_details[0]['shape'][0]
            actual_feature_count = features.shape[1] if len(features.shape) > 1 else features.shape[0]
            
            if actual_feature_count != expected_feature_count:
                if actual_feature_count < expected_feature_count:
                    padding = np.zeros((features.shape[0], expected_feature_count - actual_feature_count), dtype=np.float32)
                    features = np.concatenate([features, padding], axis=1)
                else:
                    features = features[:, :expected_feature_count]
            
            interpreter.set_tensor(input_details[0]['index'], features)
            interpreter.invoke()
            predicted_ltv = interpreter.get_tensor(output_details[0]['index'])[0][0]
            
            return {
                'customer_id': customer_id,
                'predicted_ltv': float(predicted_ltv),
                'confidence': 0.8,
            }
        except Exception as e:
            logger.error(f"Error running LTV prediction: {e}")
            return {'error': f'ML inference error: {str(e)}'}
    
    def predict_propensity_to_buy(self, customer_id: str) -> Dict:
        """Predict likelihood customer will make a purchase"""
        if MOCK_ML_ENABLED:
            features = FeatureStore.get_customer_features(customer_id)
            days_since_last = features.get('days_since_last_transaction', 999)
            if days_since_last < 30:
                propensity = 0.8
            elif days_since_last < 60:
                propensity = 0.5
            else:
                propensity = 0.2
            return {
                'customer_id': customer_id,
                'propensity': propensity,
                'will_buy': propensity > 0.5
            }
        
        if 'propensity' not in self.models:
            return {'error': 'Propensity model not available. Train model first.'}
        
        result = self._extract_features(customer_id, return_raw_features=True)
        if result is None:
            return {'error': 'Unable to extract features from DWH.'}
        
        features, raw_features = result
        try:
            interpreter = self.models['propensity']
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            
            expected_feature_count = input_details[0]['shape'][1] if len(input_details[0]['shape']) > 1 else input_details[0]['shape'][0]
            actual_feature_count = features.shape[1] if len(features.shape) > 1 else features.shape[0]
            
            if actual_feature_count != expected_feature_count:
                if actual_feature_count < expected_feature_count:
                    padding = np.zeros((features.shape[0], expected_feature_count - actual_feature_count), dtype=np.float32)
                    features = np.concatenate([features, padding], axis=1)
                else:
                    features = features[:, :expected_feature_count]
            
            interpreter.set_tensor(input_details[0]['index'], features)
            interpreter.invoke()
            propensity = interpreter.get_tensor(output_details[0]['index'])[0][0]
            
            propensity_level = 'high' if propensity > 0.7 else 'medium' if propensity > 0.5 else 'low'
            return {
                'customer_id': customer_id,
                'propensity': float(propensity),
                'propensity_score': float(propensity),  # Alias for test compatibility
                'will_buy': propensity > 0.5,
                'propensity_level': propensity_level,
                'confidence': abs(propensity - 0.5) * 2
            }
        except Exception as e:
            logger.error(f"Error running propensity prediction: {e}")
            return {'error': f'ML inference error: {str(e)}'}
    
    def calculate_engagement_score(self, customer_id: str) -> Dict:
        """Calculate customer engagement score (0-100)"""
        features = FeatureStore.get_customer_features(customer_id)
        
        transaction_count = features.get('transaction_count', 0)
        days_since_last = features.get('days_since_last_transaction', 999)
        current_month_usage = features.get('current_month_usage_spend', 0)
        active_products = features.get('active_products_count', 0)
        
        score = 0
        
        if transaction_count > 20:
            score += 30
        elif transaction_count > 10:
            score += 20
        elif transaction_count > 5:
            score += 10
        
        if days_since_last < 7:
            score += 30
        elif days_since_last < 30:
            score += 20
        elif days_since_last < 60:
            score += 10
        
        if current_month_usage > 100:
            score += 20
        elif current_month_usage > 50:
            score += 10
        
        if active_products > 3:
            score += 20
        elif active_products > 1:
            score += 10
        
        if 'engagement' in self.models:
            try:
                result = self._extract_features(customer_id, return_raw_features=False)
                if result is not None:
                    interpreter = self.models['engagement']
                    input_details = interpreter.get_input_details()
                    output_details = interpreter.get_output_details()
                    
                    expected_feature_count = input_details[0]['shape'][1] if len(input_details[0]['shape']) > 1 else input_details[0]['shape'][0]
                    actual_feature_count = result.shape[1] if len(result.shape) > 1 else result.shape[0]
                    
                    if actual_feature_count != expected_feature_count:
                        if actual_feature_count < expected_feature_count:
                            padding = np.zeros((result.shape[0], expected_feature_count - actual_feature_count), dtype=np.float32)
                            result = np.concatenate([result, padding], axis=1)
                        else:
                            result = result[:, :expected_feature_count]
                    
                    interpreter.set_tensor(input_details[0]['index'], result)
                    interpreter.invoke()
                    ml_score = interpreter.get_tensor(output_details[0]['index'])[0][0]
                    score = float(ml_score) * 100
            except Exception as e:
                logger.warning(f"Could not use engagement model: {e}, using calculated score")
        
        return {
            'customer_id': customer_id,
            'engagement_score': min(100, max(0, score)),
            'level': 'high' if score >= 70 else 'medium' if score >= 40 else 'low'
        }
    
    def recommend_products(self, customer_id: str, top_n: int = 5) -> Dict:
        """Recommend specific products/services for customer"""
        if MOCK_ML_ENABLED:
            # Mock implementation - recommend based on customer profile
            features = FeatureStore.get_customer_features(customer_id)
            active_products = features.get('active_products_count', 0)
            
            # Mock product recommendations
            all_products = [
                {'product_id': 'P001', 'name': 'Premium Data Plan', 'category': 'data'},
                {'product_id': 'P002', 'name': 'Voice Bundle', 'category': 'voice'},
                {'product_id': 'P003', 'name': 'SMS Package', 'category': 'sms'},
                {'product_id': 'P004', 'name': 'International Roaming', 'category': 'roaming'},
                {'product_id': 'P005', 'name': 'Streaming Service', 'category': 'entertainment'},
            ]
            
            # Simple recommendation logic
            recommended = all_products[:top_n]
            for product in recommended:
                product['probability'] = 0.7 - (recommended.index(product) * 0.1)
            
            return {
                'customer_id': customer_id,
                'recommended_products': recommended,
                'reason': f'Based on customer profile with {active_products} active products'
            }
        
        if 'product' not in self.models:
            return {'error': 'Product recommendation model not available. Train model first.'}
        
        result = self._extract_features(customer_id, return_raw_features=True)
        if result is None:
            return {'error': 'Unable to extract features from DWH.'}
        
        features, raw_features = result
        try:
            interpreter = self.models['product']
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            
            expected_feature_count = input_details[0]['shape'][1] if len(input_details[0]['shape']) > 1 else input_details[0]['shape'][0]
            actual_feature_count = features.shape[1] if len(features.shape) > 1 else features.shape[0]
            
            if actual_feature_count != expected_feature_count:
                if actual_feature_count < expected_feature_count:
                    padding = np.zeros((features.shape[0], expected_feature_count - actual_feature_count), dtype=np.float32)
                    features = np.concatenate([features, padding], axis=1)
                else:
                    features = features[:, :expected_feature_count]
            
            interpreter.set_tensor(input_details[0]['index'], features)
            interpreter.invoke()
            product_scores = interpreter.get_tensor(output_details[0]['index'])[0]
            
            # Get top N products (assuming output is product probabilities)
            top_indices = np.argsort(product_scores)[-top_n:][::-1]
            
            recommended_products = []
            for idx in top_indices:
                recommended_products.append({
                    'product_id': f'P{idx:03d}',
                    'probability': float(product_scores[idx]),
                    'rank': len(recommended_products) + 1
                })
            
            return {
                'customer_id': customer_id,
                'recommended_products': recommended_products,
                'top_product': recommended_products[0] if recommended_products else None
            }
        except Exception as e:
            logger.error(f"Error running product recommendation: {e}")
            return {'error': f'ML inference error: {str(e)}'}
    
    def predict_campaign_response(self, customer_id: str, campaign_id: str = None) -> Dict:
        """Predict if customer will respond to a campaign"""
        if MOCK_ML_ENABLED:
            features = FeatureStore.get_customer_features(customer_id)
            days_since_last = features.get('days_since_last_transaction', 999)
            transaction_count = features.get('transaction_count', 0)
            
            # Mock logic: active customers more likely to respond
            if days_since_last < 30 and transaction_count > 5:
                response_probability = 0.8
            elif days_since_last < 60:
                response_probability = 0.5
            else:
                response_probability = 0.2
            
            return {
                'customer_id': customer_id,
                'campaign_id': campaign_id,
                'response_probability': response_probability,
                'will_respond': response_probability > 0.5,
                'confidence': abs(response_probability - 0.5) * 2
            }
        
        if 'campaign' not in self.models:
            return {'error': 'Campaign response model not available. Train model first.'}
        
        result = self._extract_features(customer_id, return_raw_features=True)
        if result is None:
            return {'error': 'Unable to extract features from DWH.'}
        
        features, raw_features = result
        try:
            interpreter = self.models['campaign']
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            
            expected_feature_count = input_details[0]['shape'][1] if len(input_details[0]['shape']) > 1 else input_details[0]['shape'][0]
            actual_feature_count = features.shape[1] if len(features.shape) > 1 else features.shape[0]
            
            if actual_feature_count != expected_feature_count:
                if actual_feature_count < expected_feature_count:
                    padding = np.zeros((features.shape[0], expected_feature_count - actual_feature_count), dtype=np.float32)
                    features = np.concatenate([features, padding], axis=1)
                else:
                    features = features[:, :expected_feature_count]
            
            interpreter.set_tensor(input_details[0]['index'], features)
            interpreter.invoke()
            response_probability = interpreter.get_tensor(output_details[0]['index'])[0][0]
            
            response_prediction = 'positive' if response_probability > 0.5 else 'negative'
            return {
                'customer_id': customer_id,
                'campaign_id': campaign_id,
                'response_probability': float(response_probability),
                'response_prediction': response_prediction,  # Alias for test compatibility
                'will_respond': response_probability > 0.5,
                'confidence': abs(response_probability - 0.5) * 2
            }
        except Exception as e:
            logger.error(f"Error running campaign response prediction: {e}")
            return {'error': f'ML inference error: {str(e)}'}
    
    def predict_payment_default_risk(self, customer_id: str) -> Dict:
        """Predict if customer will default on payments"""
        if MOCK_ML_ENABLED:
            features = FeatureStore.get_customer_features(customer_id)
            credit_utilization = features.get('credit_utilization', 0)
            days_since_last = features.get('days_since_last_transaction', 999)
            total_revenue = features.get('total_revenue', 0)
            
            # Mock logic: high credit utilization + inactivity = higher default risk
            default_risk = 0.1  # Base risk
            if credit_utilization > 0.9:
                default_risk += 0.4
            if days_since_last > 90:
                default_risk += 0.3
            if total_revenue < 100:
                default_risk += 0.2
            
            default_risk = min(1.0, default_risk)
            
            return {
                'customer_id': customer_id,
                'default_risk': default_risk,
                'risk_level': 'high' if default_risk > 0.7 else 'medium' if default_risk > 0.4 else 'low',
                'will_default': default_risk > 0.5
            }
        
        if 'default_risk' not in self.models:
            return {'error': 'Payment default risk model not available. Train model first.'}
        
        result = self._extract_features(customer_id, return_raw_features=True)
        if result is None:
            return {'error': 'Unable to extract features from DWH.'}
        
        features, raw_features = result
        try:
            interpreter = self.models['default_risk']
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            
            expected_feature_count = input_details[0]['shape'][1] if len(input_details[0]['shape']) > 1 else input_details[0]['shape'][0]
            actual_feature_count = features.shape[1] if len(features.shape) > 1 else features.shape[0]
            
            if actual_feature_count != expected_feature_count:
                if actual_feature_count < expected_feature_count:
                    padding = np.zeros((features.shape[0], expected_feature_count - actual_feature_count), dtype=np.float32)
                    features = np.concatenate([features, padding], axis=1)
                else:
                    features = features[:, :expected_feature_count]
            
            interpreter.set_tensor(input_details[0]['index'], features)
            interpreter.invoke()
            default_risk = interpreter.get_tensor(output_details[0]['index'])[0][0]
            
            risk_level = 'high' if default_risk > 0.7 else 'medium' if default_risk > 0.4 else 'low'
            return {
                'customer_id': customer_id,
                'default_risk': float(default_risk),
                'default_risk_score': float(default_risk),  # Alias for test compatibility
                'risk_level': risk_level,
                'will_default': default_risk > 0.5,
                'confidence': abs(default_risk - 0.5) * 2
            }
        except Exception as e:
            logger.error(f"Error running payment default risk prediction: {e}")
            return {'error': f'ML inference error: {str(e)}'}
    
    def predict_upsell_propensity(self, customer_id: str) -> Dict:
        """Predict likelihood to upgrade or buy additional products"""
        if MOCK_ML_ENABLED:
            features = FeatureStore.get_customer_features(customer_id)
            active_products = features.get('active_products_count', 0)
            total_revenue = features.get('total_revenue', 0)
            days_since_last = features.get('days_since_last_transaction', 999)
            
            # Mock logic: high-value customers with few products = high upsell potential
            upsell_propensity = 0.3  # Base
            if total_revenue > 1000 and active_products < 3:
                upsell_propensity = 0.8
            elif total_revenue > 500 and active_products < 2:
                upsell_propensity = 0.6
            elif days_since_last < 30:
                upsell_propensity = 0.4
            
            return {
                'customer_id': customer_id,
                'upsell_propensity': upsell_propensity,
                'will_upsell': upsell_propensity > 0.5,
                'recommended_action': 'high' if upsell_propensity > 0.7 else 'medium' if upsell_propensity > 0.5 else 'low'
            }
        
        if 'upsell' not in self.models:
            return {'error': 'Upsell propensity model not available. Train model first.'}
        
        result = self._extract_features(customer_id, return_raw_features=True)
        if result is None:
            return {'error': 'Unable to extract features from DWH.'}
        
        features, raw_features = result
        try:
            interpreter = self.models['upsell']
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            
            expected_feature_count = input_details[0]['shape'][1] if len(input_details[0]['shape']) > 1 else input_details[0]['shape'][0]
            actual_feature_count = features.shape[1] if len(features.shape) > 1 else features.shape[0]
            
            if actual_feature_count != expected_feature_count:
                if actual_feature_count < expected_feature_count:
                    padding = np.zeros((features.shape[0], expected_feature_count - actual_feature_count), dtype=np.float32)
                    features = np.concatenate([features, padding], axis=1)
                else:
                    features = features[:, :expected_feature_count]
            
            interpreter.set_tensor(input_details[0]['index'], features)
            interpreter.invoke()
            upsell_propensity = interpreter.get_tensor(output_details[0]['index'])[0][0]
            
            return {
                'customer_id': customer_id,
                'upsell_propensity': float(upsell_propensity),
                'will_upsell': upsell_propensity > 0.5,
                'recommended_action': 'high' if upsell_propensity > 0.7 else 'medium' if upsell_propensity > 0.5 else 'low',
                'confidence': abs(upsell_propensity - 0.5) * 2
            }
        except Exception as e:
            logger.error(f"Error running upsell propensity prediction: {e}")
            return {'error': f'ML inference error: {str(e)}'}

