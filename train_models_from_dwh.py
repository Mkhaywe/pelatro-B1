"""
Train ML Models from DWH Data

This script:
1. Connects to your DWH
2. Extracts historical customer data
3. Prepares training data (features + labels)
4. Trains all ML models (NBO, Churn, LTV, Propensity, Product, Campaign, Default Risk, Upsell, Engagement)
5. Saves models to models/ directory

Requirements:
- tensorflow >= 2.10.0
- numpy
- pandas
- scikit-learn
- DWH connector configured in settings

Install: pip install tensorflow numpy pandas scikit-learn
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Check dependencies
try:
    import tensorflow as tf
    import numpy as np
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install with: pip install tensorflow numpy pandas scikit-learn")
    sys.exit(1)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
import django
django.setup()

from django.conf import settings
from loyalty.integration.dwh import get_dwh_connector
from loyalty.integration.xiva_feature_extractor import XivaFeatureExtractor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create models directory
models_dir = Path('models')
models_dir.mkdir(exist_ok=True)

print("="*70)
print("ML MODEL TRAINING FROM DWH")
print("="*70)
print()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_feature_columns():
    """Get feature columns from settings or use defaults"""
    feature_mapping = getattr(settings, 'ML_FEATURE_MAPPING', {})
    if not feature_mapping:
        return [
            'total_revenue',
            'transaction_count',
            'days_since_last_transaction',
            'avg_transaction_value',
            'lifetime_value',
        ]
    return list(feature_mapping.values())

def check_table_columns(connector, table):
    """Check which columns exist in the table"""
    try:
        test_query = f"SELECT * FROM {table} LIMIT 1"
        test_results = connector.execute_query(test_query, {})
        if test_results:
            return set(test_results[0].keys())
    except Exception as e:
        logger.warning(f"Could not check table schema: {e}")
    return set()


# ============================================================================
# STEP 1: EXTRACT TRAINING DATA FROM DWH
# ============================================================================

def extract_training_data_nbo():
    """
    Extract training data for NBO (Next Best Offer) model.
    
    Returns:
        X: Feature matrix (n_samples, n_features)
        y: Labels - one-hot encoded offer conversions (n_samples, n_offers)
    """
    print("📊 Step 1: Extracting NBO training data from DWH...")
    
    connector = get_dwh_connector()
    feature_columns = get_feature_columns()
    table = getattr(settings, 'DWH_CUSTOMER_FEATURES_TABLE', 'customer_features_view')
    
    # Check available columns
    available_columns = check_table_columns(connector, table)
    if available_columns:
        print(f"   Available columns in {table}: {len(available_columns)} columns")
        valid_feature_columns = [col for col in feature_columns if col in available_columns]
        missing_columns = [col for col in feature_columns if col not in available_columns]
        if missing_columns:
            print(f"   ⚠️  Missing columns (will be skipped): {missing_columns}")
        if not valid_feature_columns:
            print("   ❌ ERROR: None of the configured feature columns exist!")
            return None, None
        feature_columns = valid_feature_columns
        print(f"   Using {len(feature_columns)} valid feature columns")
    
    # Check if converted_offer_id exists
    query = getattr(settings, 'DWH_NBO_TRAINING_QUERY', None)
    if not query:
        if available_columns and 'converted_offer_id' not in available_columns:
            print("   ❌ ERROR: 'converted_offer_id' column not found!")
            print("   Create customer_offer_history view (see docs/CREATE_TRAINING_DATA.md)")
            return None, None
        
        columns_str = ', '.join(feature_columns + ['customer_id', 'converted_offer_id'])
        date_filter = ""
        date_params = {}
        if 'created_at' in available_columns:
            date_filter = "AND created_at >= :start_date"
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            date_params = {'start_date': start_date}
        
        query = f"""
        SELECT {columns_str}
        FROM {table}
        WHERE converted_offer_id IS NOT NULL
        {date_filter}
        LIMIT 10000
        """
    
    results = connector.execute_query(query, date_params if 'date_params' in locals() else {})
    
    if not results:
        print("❌ No training data found!")
        return None, None
    
    df = pd.DataFrame(results)
    print(f"   ✅ Loaded {len(df)} training samples")
    
    # Prepare features
    X = df[feature_columns].fillna(0).values.astype(np.float32)
    
    # Prepare labels - one-hot encode offer conversions (0-7)
    offer_ids = df['converted_offer_id'].fillna(-1).astype(int)
    valid_offers = offer_ids[offer_ids >= 0]
    if len(valid_offers) == 0:
        print("   ❌ ERROR: No valid offer IDs found")
        return None, None
    
    n_offers = max(8, valid_offers.max() + 1)
    y = np.zeros((len(df), n_offers), dtype=np.float32)
    for i, offer_id in enumerate(offer_ids):
        if 0 <= offer_id < n_offers:
            y[i, offer_id] = 1.0
    
    print(f"   ✅ Features shape: {X.shape}, Labels shape: {y.shape} ({n_offers} offers)")
    return X, y


def extract_training_data_churn():
    """Extract training data for Churn prediction model"""
    print("\n📊 Step 1: Extracting Churn training data from DWH...")
    
    connector = get_dwh_connector()
    feature_columns = get_feature_columns()
    table = getattr(settings, 'DWH_CUSTOMER_FEATURES_TABLE', 'customer_features_view')
    
    available_columns = check_table_columns(connector, table)
    if available_columns:
        valid_feature_columns = [col for col in feature_columns if col in available_columns]
        if not valid_feature_columns:
            print("   ❌ ERROR: None of the configured feature columns exist!")
            return None, None
        feature_columns = valid_feature_columns
        print(f"   Using {len(feature_columns)} valid feature columns")
    
    query = getattr(settings, 'DWH_CHURN_TRAINING_QUERY', None)
    if not query:
        if available_columns and 'churned' not in available_columns:
            print("   ❌ ERROR: 'churned' column not found!")
            print("   Create customer_churn_history view (see docs/CREATE_TRAINING_DATA.md)")
            return None, None
        
        columns_str = ', '.join(feature_columns + ['customer_id', 'churned'])
        date_filter = ""
        date_params = {}
        if 'snapshot_date' in available_columns:
            date_filter = "AND snapshot_date >= :start_date"
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            date_params = {'start_date': start_date}
        
        query = f"""
        SELECT {columns_str}
        FROM {table}
        WHERE churned IS NOT NULL
        {date_filter}
        LIMIT 10000
        """
    
    results = connector.execute_query(query, date_params if 'date_params' in locals() else {})
    
    if not results:
        print("❌ No training data found!")
        return None, None
    
    df = pd.DataFrame(results)
    print(f"   ✅ Loaded {len(df)} training samples")
    
    X = df[feature_columns].fillna(0).values.astype(np.float32)
    y = df['churned'].fillna(0).astype(int).values.astype(np.float32)
    
    print(f"   ✅ Features shape: {X.shape}, Labels shape: {y.shape}")
    print(f"   ✅ Churn rate: {y.mean():.2%}")
    return X, y


def extract_training_data_ltv():
    """Extract training data for LTV prediction model"""
    print("\n📊 Step 1: Extracting LTV training data from DWH...")
    print("   ⚠️  LTV training requires 'future_ltv' or 'actual_ltv' column")
    print("   Using lifetime_value as target (regression model)")
    
    connector = get_dwh_connector()
    feature_columns = get_feature_columns()
    table = getattr(settings, 'DWH_CUSTOMER_FEATURES_TABLE', 'customer_features_view')
    
    available_columns = check_table_columns(connector, table)
    if available_columns:
        valid_feature_columns = [col for col in feature_columns if col in available_columns]
        if not valid_feature_columns:
            return None, None
        feature_columns = valid_feature_columns
    
    # Use lifetime_value as target (regression)
    if 'lifetime_value' not in available_columns:
        print("   ⚠️  'lifetime_value' column not found, skipping LTV training")
        return None, None
    
    query = f"""
    SELECT {', '.join(feature_columns + ['customer_id', 'lifetime_value'])}
    FROM {table}
    WHERE lifetime_value IS NOT NULL AND lifetime_value > 0
    LIMIT 10000
    """
    
    results = connector.execute_query(query, {})
    if not results:
        return None, None
    
    df = pd.DataFrame(results)
    print(f"   ✅ Loaded {len(df)} training samples")
    
    X = df[feature_columns].fillna(0).values.astype(np.float32)
    y = df['lifetime_value'].fillna(0).values.astype(np.float32)
    
    print(f"   ✅ Features shape: {X.shape}, Labels shape: {y.shape}")
    return X, y


def extract_training_data_propensity():
    """Extract training data for Propensity to Buy model"""
    print("\n📊 Step 1: Extracting Propensity training data from DWH...")
    print("   ⚠️  Propensity training requires purchase history")
    print("   Using 'made_purchase' flag or transaction_count > 0 as target")
    
    connector = get_dwh_connector()
    feature_columns = get_feature_columns()
    table = getattr(settings, 'DWH_CUSTOMER_FEATURES_TABLE', 'customer_features_view')
    
    available_columns = check_table_columns(connector, table)
    if available_columns:
        valid_feature_columns = [col for col in feature_columns if col in available_columns]
        if not valid_feature_columns:
            return None, None
        feature_columns = valid_feature_columns
    
    # Use transaction_count > 0 as proxy for purchase propensity
    query = f"""
    SELECT {', '.join(feature_columns + ['customer_id', 'transaction_count'])}
    FROM {table}
    LIMIT 10000
    """
    
    results = connector.execute_query(query, {})
    if not results:
        return None, None
    
    df = pd.DataFrame(results)
    print(f"   ✅ Loaded {len(df)} training samples")
    
    X = df[feature_columns].fillna(0).values.astype(np.float32)
    y = (df['transaction_count'] > 0).astype(int).values.astype(np.float32)
    
    print(f"   ✅ Features shape: {X.shape}, Labels shape: {y.shape}")
    print(f"   ✅ Purchase rate: {y.mean():.2%}")
    return X, y


def extract_training_data_product():
    """Extract training data for Product Recommendation model"""
    print("\n📊 Step 1: Extracting Product Recommendation training data...")
    print("   ⚠️  Product training requires 'purchased_product_id' column")
    print("   Skipping (requires product purchase history)")
    return None, None


def extract_training_data_campaign():
    """Extract training data for Campaign Response model"""
    print("\n📊 Step 1: Extracting Campaign Response training data...")
    print("   ⚠️  Campaign training requires campaign response history")
    print("   Skipping (requires campaign_response table)")
    return None, None


def extract_training_data_default_risk():
    """Extract training data for Payment Default Risk model"""
    print("\n📊 Step 1: Extracting Payment Default Risk training data...")
    print("   ⚠️  Default risk training requires payment history")
    print("   Using credit_utilization > 0.9 as proxy")
    
    connector = get_dwh_connector()
    feature_columns = get_feature_columns()
    table = getattr(settings, 'DWH_CUSTOMER_FEATURES_TABLE', 'customer_features_view')
    
    available_columns = check_table_columns(connector, table)
    if available_columns:
        valid_feature_columns = [col for col in feature_columns if col in available_columns]
        if not valid_feature_columns:
            return None, None
        feature_columns = valid_feature_columns
    
    if 'credit_utilization' not in available_columns:
        print("   ⚠️  'credit_utilization' column not found, skipping")
        return None, None
    
    query = f"""
    SELECT {', '.join(feature_columns + ['customer_id', 'credit_utilization'])}
    FROM {table}
    WHERE credit_utilization IS NOT NULL
    LIMIT 10000
    """
    
    results = connector.execute_query(query, {})
    if not results:
        return None, None
    
    df = pd.DataFrame(results)
    print(f"   ✅ Loaded {len(df)} training samples")
    
    X = df[feature_columns].fillna(0).values.astype(np.float32)
    y = (df['credit_utilization'] > 0.9).astype(int).values.astype(np.float32)
    
    print(f"   ✅ Features shape: {X.shape}, Labels shape: {y.shape}")
    print(f"   ✅ Default risk rate: {y.mean():.2%}")
    return X, y


def extract_training_data_upsell():
    """Extract training data for Upsell Propensity model"""
    print("\n📊 Step 1: Extracting Upsell Propensity training data...")
    print("   ⚠️  Upsell training requires upgrade history")
    print("   Using active_products_count increase as proxy")
    
    connector = get_dwh_connector()
    feature_columns = get_feature_columns()
    table = getattr(settings, 'DWH_CUSTOMER_FEATURES_TABLE', 'customer_features_view')
    
    available_columns = check_table_columns(connector, table)
    if available_columns:
        valid_feature_columns = [col for col in feature_columns if col in available_columns]
        if not valid_feature_columns:
            return None, None
        feature_columns = valid_feature_columns
    
    if 'active_products_count' not in available_columns:
        print("   ⚠️  'active_products_count' column not found, skipping")
        return None, None
    
    query = f"""
    SELECT {', '.join(feature_columns + ['customer_id', 'active_products_count', 'lifetime_value'])}
    FROM {table}
    WHERE active_products_count IS NOT NULL
    LIMIT 10000
    """
    
    results = connector.execute_query(query, {})
    if not results:
        return None, None
    
    df = pd.DataFrame(results)
    print(f"   ✅ Loaded {len(df)} training samples")
    
    X = df[feature_columns].fillna(0).values.astype(np.float32)
    # High-value customers with few products = high upsell potential
    y = ((df['lifetime_value'] > 500) & (df['active_products_count'] < 3)).astype(int).values.astype(np.float32)
    
    print(f"   ✅ Features shape: {X.shape}, Labels shape: {y.shape}")
    print(f"   ✅ Upsell potential rate: {y.mean():.2%}")
    return X, y


def extract_training_data_engagement():
    """Extract training data for Engagement Score model"""
    print("\n📊 Step 1: Extracting Engagement Score training data...")
    print("   Calculating engagement score from features (regression)")
    
    connector = get_dwh_connector()
    feature_columns = get_feature_columns()
    table = getattr(settings, 'DWH_CUSTOMER_FEATURES_TABLE', 'customer_features_view')
    
    available_columns = check_table_columns(connector, table)
    if available_columns:
        valid_feature_columns = [col for col in feature_columns if col in available_columns]
        if not valid_feature_columns:
            return None, None
        feature_columns = valid_feature_columns
        print(f"   Using {len(feature_columns)} valid feature columns")
    
    # Build list of columns needed for engagement calculation
    engagement_cols = ['customer_id']
    optional_cols = {
        'transaction_count': 0,
        'days_since_last_transaction': 999,
        'current_month_usage_spend': 0,
        'current_month_spend': 0,  # Alternative name
        'active_products_count': 0,
        'product_count': 0,  # Alternative name
    }
    
    # Only include columns that exist
    for col, default_value in optional_cols.items():
        if col in available_columns:
            engagement_cols.append(col)
    
    # Remove duplicates
    engagement_cols = list(dict.fromkeys(engagement_cols))  # Preserves order
    
    # Build query with only existing columns
    all_cols = feature_columns + engagement_cols
    all_cols = list(dict.fromkeys(all_cols))  # Remove duplicates
    columns_str = ', '.join(all_cols)
    
    query = f"""
    SELECT {columns_str}
    FROM {table}
    LIMIT 10000
    """
    
    try:
        results = connector.execute_query(query, {})
    except Exception as e:
        print(f"   ❌ Error querying DWH: {e}")
        return None, None
    
    if not results:
        return None, None
    
    df = pd.DataFrame(results)
    print(f"   ✅ Loaded {len(df)} training samples")
    
    X = df[feature_columns].fillna(0).values.astype(np.float32)
    
    # Calculate engagement score (0-100) from available features
    score = np.zeros(len(df))
    
    # Transaction frequency (0-30 points)
    if 'transaction_count' in df.columns:
        score += np.clip(df['transaction_count'].fillna(0) / 20 * 30, 0, 30)
    
    # Recency (0-30 points)
    if 'days_since_last_transaction' in df.columns:
        days_since = df['days_since_last_transaction'].fillna(999)
        score += np.clip((30 - days_since) / 30 * 30, 0, 30)
    
    # Usage activity (0-20 points)
    usage_col = None
    if 'current_month_usage_spend' in df.columns:
        usage_col = 'current_month_usage_spend'
    elif 'current_month_spend' in df.columns:
        usage_col = 'current_month_spend'
    
    if usage_col:
        score += np.clip(df[usage_col].fillna(0) / 100 * 20, 0, 20)
    
    # Product engagement (0-20 points)
    product_col = None
    if 'active_products_count' in df.columns:
        product_col = 'active_products_count'
    elif 'product_count' in df.columns:
        product_col = 'product_count'
    
    if product_col:
        score += np.clip(df[product_col].fillna(0) / 3 * 20, 0, 20)
    
    y = np.clip(score, 0, 100).astype(np.float32)
    
    print(f"   ✅ Features shape: {X.shape}, Labels shape: {y.shape}")
    if len(y) > 0:
        print(f"   ✅ Engagement score range: {y.min():.1f} - {y.max():.1f}")
    return X, y


# ============================================================================
# STEP 2: TRAIN MODELS
# ============================================================================

def train_model_common(X, y, model_name, model_type='binary', output_size=1):
    """Common training function for all models"""
    if X is None or y is None:
        return None
    
    print(f"\n🤖 Training {model_name} Model...")
    
    # Split data
    if model_type == 'binary':
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Build model
    n_features = X_train.shape[1]
    
    if model_type == 'regression':
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(n_features,)),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(output_size, activation='linear')
        ])
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    elif model_type == 'multiclass':
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(n_features,)),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(output_size, activation='softmax')
        ])
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    else:  # binary
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(n_features,)),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        churn_rate = y_train.mean() if len(y_train.shape) == 1 else y_train[:, 0].mean()
        class_weight = {0: 1.0, 1: 2.0} if churn_rate < 0.3 else {0: 1.0, 1: 1.0}
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy', 'precision', 'recall'])
    
    # Train
    print("   Training model...")
    fit_kwargs = {
        'epochs': 50,
        'batch_size': 32,
        'validation_data': (X_test_scaled, y_test),
        'verbose': 1
    }
    if model_type == 'binary':
        fit_kwargs['class_weight'] = class_weight
    
    history = model.fit(X_train_scaled, y_train, **fit_kwargs)
    
    # Evaluate
    print("\n   Evaluating model...")
    metrics = model.evaluate(X_test_scaled, y_test, verbose=0)
    print(f"   ✅ Test Metrics: {dict(zip(model.metrics_names, metrics))}")
    
    # Convert to TFLite
    print("   Converting to TFLite...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()
    
    # Save model
    model_path = models_dir / f'{model_name}.tflite'
    with open(model_path, 'wb') as f:
        f.write(tflite_model)
    print(f"   ✅ Model saved to {model_path}")
    
    # Save scaler
    import pickle
    scaler_path = models_dir / f'{model_name}_scaler.pkl'
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"   ✅ Scaler saved to {scaler_path}")
    
    return model


def train_nbo_model(X, y):
    """Train Next Best Offer prediction model"""
    return train_model_common(X, y, 'nbo', 'multiclass', output_size=y.shape[1] if len(y.shape) > 1 else 8)


def train_churn_model(X, y):
    """Train Churn prediction model"""
    return train_model_common(X, y, 'churn', 'binary')


def train_ltv_model(X, y):
    """Train Lifetime Value prediction model"""
    return train_model_common(X, y, 'ltv', 'regression')


def train_propensity_model(X, y):
    """Train Propensity to Buy model"""
    return train_model_common(X, y, 'propensity', 'binary')


def train_product_model(X, y):
    """Train Product Recommendation model"""
    if X is None or y is None:
        return None
    return train_model_common(X, y, 'product', 'multiclass', output_size=y.shape[1] if len(y.shape) > 1 else 10)


def train_campaign_model(X, y):
    """Train Campaign Response model"""
    return train_model_common(X, y, 'campaign', 'binary')


def train_default_risk_model(X, y):
    """Train Payment Default Risk model"""
    return train_model_common(X, y, 'default_risk', 'binary')


def train_upsell_model(X, y):
    """Train Upsell Propensity model"""
    return train_model_common(X, y, 'upsell', 'binary')


def train_engagement_model(X, y):
    """Train Engagement Score model"""
    return train_model_common(X, y, 'engagement', 'regression')


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    print("Starting ML Model Training from DWH...")
    print()
    
    # Check DWH configuration
    dwh_type = getattr(settings, 'DWH_TYPE', None)
    if not dwh_type:
        print("❌ ERROR: DWH_TYPE not configured in settings.py")
        sys.exit(1)
    
    print(f"✅ DWH Type: {dwh_type}")
    print()
    
    # Train all models
    models_to_train = [
        ('NBO', extract_training_data_nbo, train_nbo_model),
        ('Churn', extract_training_data_churn, train_churn_model),
        ('LTV', extract_training_data_ltv, train_ltv_model),
        ('Propensity', extract_training_data_propensity, train_propensity_model),
        ('Product', extract_training_data_product, train_product_model),
        ('Campaign', extract_training_data_campaign, train_campaign_model),
        ('Default Risk', extract_training_data_default_risk, train_default_risk_model),
        ('Upsell', extract_training_data_upsell, train_upsell_model),
        ('Engagement', extract_training_data_engagement, train_engagement_model),
    ]
    
    trained_count = 0
    skipped_count = 0
    
    for model_name, extract_func, train_func in models_to_train:
        print("\n" + "="*70)
        print(f"TRAINING {model_name.upper()} MODEL")
        print("="*70)
        
        try:
            X, y = extract_func()
            if X is not None and y is not None and len(X) > 0 and len(y) > 0:
                try:
                    train_func(X, y)
                    trained_count += 1
                except Exception as e:
                    print(f"   ❌ Error training {model_name} model: {e}")
                    logger.exception(f"Training error for {model_name}")
                    skipped_count += 1
            else:
                print(f"⚠️  Skipping {model_name} model training (no data or not configured)")
                skipped_count += 1
        except Exception as e:
            error_msg = str(e)
            if "UndefinedColumn" in error_msg or "does not exist" in error_msg:
                print(f"   ⚠️  Skipping {model_name} model (required columns not found in DWH)")
                col_name = error_msg.split("column ")[1].split(" ")[0].strip('"') if "column " in error_msg else "unknown"
                print(f"      Missing column: {col_name}")
            else:
                print(f"   ❌ Error extracting data for {model_name} model: {e}")
                logger.exception(f"Data extraction error for {model_name}")
            skipped_count += 1
    
    print("\n" + "="*70)
    print("✅ TRAINING COMPLETE!")
    print("="*70)
    print(f"\nTrained: {trained_count} models")
    print(f"Skipped: {skipped_count} models")
    print("\nNext steps:")
    print("1. Models are saved in models/ directory")
    print("2. Test models using Admin → ML & AI → Test ML Predictions")
    print("3. Models will be used automatically for predictions")
    print("\nTo retrain with new data, run this script again.")
    print("="*70)
