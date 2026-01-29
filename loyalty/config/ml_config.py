"""
ML Configuration Defaults
This file contains default ML configuration that can be overridden via database/UI.
"""
from typing import Dict

# Default ML Feature Mapping
# Maps DWH column names to ML model feature names
# Format: {'model_feature_name': 'dwh_column_name', ...}
DEFAULT_ML_FEATURE_MAPPING: Dict[str, str] = {
    'revenue': 'total_revenue',
    'transaction_count': 'transaction_count',
    'days_since_last': 'days_since_last_transaction',
    'avg_transaction_value': 'avg_transaction_value',
    'lifetime_value': 'lifetime_value',
    'customer_age_days': 'customer_age_days',
    'monthly_revenue': 'monthly_revenue',
    'product_count': 'product_count',
    'service_count': 'service_count',
    'engagement_score': 'engagement_score',
}

# Default ML Model Input Size
# Number of features expected by ML models
# Should match the number of features in DEFAULT_ML_FEATURE_MAPPING
DEFAULT_ML_MODEL_INPUT_SIZE: int = len(DEFAULT_ML_FEATURE_MAPPING)

# Default ML Model Paths
DEFAULT_ML_MODEL_PATHS: Dict[str, str] = {
    'nbo': 'models/nbo.tflite',
    'churn': 'models/churn.tflite',
    'ltv': 'models/ltv.tflite',
    'propensity': 'models/propensity.tflite',
    'product': 'models/product.tflite',
    'campaign': 'models/campaign.tflite',
    'default_risk': 'models/default_risk.tflite',
    'upsell': 'models/upsell.tflite',
    'engagement': 'models/engagement.tflite',
}

# Default ML Configuration
DEFAULT_ML_CONFIG: Dict = {
    'feature_mapping': DEFAULT_ML_FEATURE_MAPPING,
    'model_input_size': DEFAULT_ML_MODEL_INPUT_SIZE,
    'model_paths': DEFAULT_ML_MODEL_PATHS,
    'mock_mode': False,
}

