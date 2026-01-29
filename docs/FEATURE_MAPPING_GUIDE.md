# Feature Mapping Guide: How to Configure DWH Columns for ML Models

## 🎯 Overview

The ML system uses **feature mapping** to connect your DWH column names to ML model input features. This guide explains:
- How feature mapping works
- Where to configure it
- How to change column mappings
- How it's used in training and inference

---

## 📍 Where Feature Mapping is Configured

### Primary Location: `loyalty_project/settings.py`

The feature mapping is defined in `settings.py`:

```python
# ML Feature Mapping - Maps DWH column names to ML model feature names
ML_FEATURE_MAPPING = {
    'revenue': 'total_revenue',                    # Model feature → DWH column
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

# Number of features expected by ML models
ML_MODEL_INPUT_SIZE = 10
```

### Alternative: Environment Variable

You can also set it via `.env` file:

```bash
# .env file
ML_FEATURE_MAPPING='{"revenue":"total_revenue","transaction_count":"transaction_count","days_since_last":"days_since_last_transaction","avg_transaction_value":"avg_transaction_value","lifetime_value":"lifetime_value"}'
ML_MODEL_INPUT_SIZE=5
```

---

## 🔄 How Feature Mapping Works

### The Flow

```
1. DWH Table/View
   ↓ (has columns: total_revenue, transaction_count, days_since_last_transaction, ...)
2. FeatureStore.get_customer_features(customer_id)
   ↓ (returns dict with DWH column names as keys)
3. ML_FEATURE_MAPPING
   ↓ (maps DWH columns to model features)
4. Feature Vector
   ↓ (array of numbers: [revenue, transaction_count, days_since_last, ...])
5. ML Model Input
   ↓ (model expects exactly ML_MODEL_INPUT_SIZE features)
6. Prediction
```

### Example

**DWH Table** (`customer_features_view`):
```sql
customer_id | total_revenue | transaction_count | days_since_last_transaction | lifetime_value
------------|---------------|-------------------|----------------------------|----------------
abc-123     | 5000.00      | 25                | 5                          | 10000.00
```

**Feature Mapping**:
```python
ML_FEATURE_MAPPING = {
    'revenue': 'total_revenue',                    # Maps DWH 'total_revenue' → model feature 'revenue'
    'transaction_count': 'transaction_count',      # Maps DWH 'transaction_count' → model feature 'transaction_count'
    'days_since_last': 'days_since_last_transaction',  # Maps DWH 'days_since_last_transaction' → model feature 'days_since_last'
    'lifetime_value': 'lifetime_value',
}
```

**Feature Vector** (what the model receives):
```python
[5000.00, 25, 5, 10000.00]  # [revenue, transaction_count, days_since_last, lifetime_value]
```

---

## 🔧 How to Change Feature Mappings

### Step 1: Check Your DWH Columns

First, check what columns exist in your DWH table:

```sql
-- PostgreSQL
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'customer_features_view';

-- Or just query one row
SELECT * FROM customer_features_view LIMIT 1;
```

### Step 2: Update `settings.py`

Edit `loyalty_project/settings.py`:

```python
# Example: Your DWH has different column names
ML_FEATURE_MAPPING = {
    'revenue': 'customer_revenue',                    # Changed from 'total_revenue'
    'transaction_count': 'txn_count',                # Changed from 'transaction_count'
    'days_since_last': 'last_txn_days',              # Changed from 'days_since_last_transaction'
    'avg_transaction_value': 'avg_txn_value',        # Changed from 'avg_transaction_value'
    'lifetime_value': 'ltv',                         # Changed from 'lifetime_value'
    # Add more mappings as needed
    'customer_age_days': 'account_age',
    'monthly_revenue': 'monthly_rev',
    'product_count': 'products',
    'service_count': 'services',
    'engagement_score': 'engagement',
}

# Update input size to match number of features
ML_MODEL_INPUT_SIZE = 10  # Must match number of features in ML_FEATURE_MAPPING
```

### Step 3: Update DWH Table Name (if needed)

If your table/view has a different name:

```python
# settings.py
DWH_CUSTOMER_FEATURES_TABLE = 'your_schema.your_customer_features_view'
```

### Step 4: Retrain Models

After changing feature mapping, **retrain your models**:

```bash
python train_models_from_dwh.py
```

**Important:** Models must be retrained after changing feature mapping because:
- Training uses the same mapping to extract features
- Model expects features in a specific order
- Changing mapping = changing feature order = model needs retraining

---

## 📊 How It's Used in Training

### Training Script: `train_models_from_dwh.py`

The training script uses `ML_FEATURE_MAPPING` to:

1. **Extract features from DWH**:
   ```python
   feature_mapping = getattr(settings, 'ML_FEATURE_MAPPING', {})
   feature_columns = list(feature_mapping.values())  # Gets DWH column names
   
   # Query: SELECT total_revenue, transaction_count, ... FROM customer_features_view
   ```

2. **Build feature vectors**:
   ```python
   X = df[feature_columns].fillna(0).values  # Uses DWH column names
   ```

3. **Train model** with these features in the order defined by `ML_FEATURE_MAPPING`

### Example Training Query

```python
# Based on ML_FEATURE_MAPPING, the script builds:
query = """
SELECT 
    total_revenue,              -- from 'revenue': 'total_revenue'
    transaction_count,          -- from 'transaction_count': 'transaction_count'
    days_since_last_transaction, -- from 'days_since_last': 'days_since_last_transaction'
    avg_transaction_value,      -- from 'avg_transaction_value': 'avg_transaction_value'
    lifetime_value,             -- from 'lifetime_value': 'lifetime_value'
    customer_id,
    converted_offer_id
FROM customer_features_view
WHERE converted_offer_id IS NOT NULL
LIMIT 10000
"""
```

---

## 🔍 How It's Used in Inference

### Inference Service: `loyalty/ml/inference.py`

The inference service uses `ML_FEATURE_MAPPING` to:

1. **Get features from DWH**:
   ```python
   features = FeatureStore.get_customer_features(customer_id)
   # Returns: {'total_revenue': 5000.00, 'transaction_count': 25, ...}
   ```

2. **Map to model features**:
   ```python
   feature_mapping = getattr(settings, 'ML_FEATURE_MAPPING', {})
   feature_vector = []
   for model_feature, dwh_column in feature_mapping.items():
       value = features.get(dwh_column, 0)  # Get value from DWH column
       feature_vector.append(float(value))   # Add to feature vector
   ```

3. **Pad/truncate to expected size**:
   ```python
   expected_size = getattr(settings, 'ML_MODEL_INPUT_SIZE', 10)
   if len(feature_vector) < expected_size:
       feature_vector.extend([0.0] * (expected_size - len(feature_vector)))
   ```

4. **Pass to model**:
   ```python
   interpreter.set_tensor(input_index, feature_vector)
   ```

---

## ⚠️ Common Issues and Solutions

### Issue 1: Column Mismatch Error

**Error:**
```
psycopg2.errors.UndefinedColumn: column "total_revenue" does not exist
```

**Solution:**
1. Check your DWH table columns
2. Update `ML_FEATURE_MAPPING` to use correct column names
3. Retrain models

### Issue 2: Feature Dimension Mismatch

**Error:**
```
Feature dimension mismatch: got 5, expected 10
```

**Solution:**
1. Update `ML_MODEL_INPUT_SIZE` to match number of features in `ML_FEATURE_MAPPING`
2. OR add more features to `ML_FEATURE_MAPPING` to reach 10
3. Retrain models

### Issue 3: Model Predictions Are Wrong

**Cause:**
- Feature mapping changed but models weren't retrained
- Feature order doesn't match training order

**Solution:**
1. Ensure `ML_FEATURE_MAPPING` matches what was used during training
2. Retrain models with current mapping

---

## 📝 Step-by-Step: Changing Column Mappings

### Scenario: Your DWH has different column names

**Current DWH columns:**
- `customer_revenue` (not `total_revenue`)
- `txn_count` (not `transaction_count`)
- `last_txn_days` (not `days_since_last_transaction`)

**Step 1:** Edit `loyalty_project/settings.py`:

```python
ML_FEATURE_MAPPING = {
    'revenue': 'customer_revenue',              # Changed
    'transaction_count': 'txn_count',           # Changed
    'days_since_last': 'last_txn_days',         # Changed
    'avg_transaction_value': 'avg_txn_value',   # Changed (if exists)
    'lifetime_value': 'ltv',                    # Changed (if exists)
}

# Keep ML_MODEL_INPUT_SIZE same if you have same number of features
ML_MODEL_INPUT_SIZE = 5
```

**Step 2:** Verify DWH table name:

```python
DWH_CUSTOMER_FEATURES_TABLE = 'your_schema.your_table_name'
```

**Step 3:** Test feature extraction:

```python
# In Django shell or test script
from loyalty.integration.feature_store import FeatureStore
features = FeatureStore.get_customer_features('test-customer-id')
print(features)  # Should show your DWH column names
```

**Step 4:** Retrain models:

```bash
python train_models_from_dwh.py
```

**Step 5:** Test predictions:

```python
from loyalty.ml.inference import MLInferenceService
ml = MLInferenceService()
result = ml.predict_churn('test-customer-id')
print(result)
```

---

## 🎯 Best Practices

1. **Keep mapping consistent**: Use same mapping for training and inference
2. **Document your columns**: Add comments in `settings.py` explaining what each feature means
3. **Test after changes**: Always test feature extraction after changing mapping
4. **Retrain models**: Always retrain after changing feature mapping
5. **Use meaningful names**: Model feature names should be descriptive (e.g., `revenue` not `f1`)

---

## 📋 Quick Reference

| Setting | Location | Purpose |
|---------|----------|---------|
| `ML_FEATURE_MAPPING` | `settings.py` | Maps DWH columns → model features |
| `ML_MODEL_INPUT_SIZE` | `settings.py` | Number of features model expects |
| `DWH_CUSTOMER_FEATURES_TABLE` | `settings.py` | DWH table/view name |
| `get_feature_columns()` | `train_models_from_dwh.py` | Gets DWH column names for training |
| `_extract_features()` | `loyalty/ml/inference.py` | Maps DWH → feature vector for inference |

---

## ✅ Summary

**To change feature mappings:**

1. ✅ Edit `ML_FEATURE_MAPPING` in `loyalty_project/settings.py`
2. ✅ Update `ML_MODEL_INPUT_SIZE` if number of features changed
3. ✅ Verify `DWH_CUSTOMER_FEATURES_TABLE` points to correct table
4. ✅ Retrain models: `python train_models_from_dwh.py`
5. ✅ Test predictions to verify it works

**The mapping connects:**
- **DWH columns** (what you have) → **Model features** (what model expects)

**Both training and inference use the same mapping**, so keep them consistent!

