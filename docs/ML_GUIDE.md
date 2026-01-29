# Machine Learning Guide

## Overview

The loyalty platform includes ML models for:
- **NBO (Next Best Offer)** - Predicts best offer for each customer
- **Churn Prediction** - Predicts churn probability
- **RFM Calculation** - Calculates customer value segments

All ML runs **on-premise** (no external APIs) for privacy compliance.

---

## Quick Start

### Step 1: Install Dependencies

```bash
pip install tensorflow numpy pandas scikit-learn
```

### Step 2: Configure DWH

See [DWH_INTEGRATION.md](DWH_INTEGRATION.md) for DWH setup.

### Step 3: Train Models

```bash
python train_models_from_dwh.py
```

Models will be saved to `models/` directory:
- `models/nbo.tflite` - Next Best Offer model
- `models/churn.tflite` - Churn prediction model

---

## What is Model Training?

**Training** = Teaching the model by showing it historical examples:
- **Input**: Customer features (revenue, transactions, etc.)
- **Output**: What happened (which offer converted, did they churn?)

The model learns patterns and can predict for new customers!

---

## Training Process

### Prerequisites

1. **DWH populated** with historical data
2. **Feature mapping configured** in `settings.py`
3. **Training data available** (1000+ samples recommended)

### Step-by-Step

#### 1. Prepare DWH Data

Your DWH needs tables with historical data including features and labels:

**For NBO Model:**
- `customer_offer_history` table with:
  - Customer features (revenue, transactions, etc.)
  - `converted_offer_id` column (which offer converted, 1-8)

**Example DWH Table Structure:**
```sql
CREATE TABLE customer_offer_history AS
SELECT 
    customer_id,
    total_revenue,
    transaction_count,
    days_since_last_transaction,
    avg_transaction_value,
    lifetime_value,
    converted_offer_id,  -- Which offer converted (1-8)
    created_at
FROM your_customer_table
WHERE converted_offer_id IS NOT NULL;
```

**For Churn Model:**
- `customer_churn_history` table with:
  - Customer features (revenue, transactions, etc.)
  - `churned` column (0 = no, 1 = yes)

**Example DWH Table Structure:**
```sql
CREATE TABLE customer_churn_history AS
SELECT 
    customer_id,
    total_revenue,
    transaction_count,
    days_since_last_transaction,
    avg_transaction_value,
    lifetime_value,
    churned,  -- 0 = not churned, 1 = churned
    snapshot_date
FROM your_customer_table
WHERE churned IS NOT NULL;
```

#### 2. Configure Feature Mapping

In `loyalty_project/settings.py`:

```python
ML_FEATURE_MAPPING = {
    'revenue': 'total_revenue',
    'transaction_count': 'transaction_count',
    'days_since_last': 'last_purchase_days_ago',
    'avg_transaction_value': 'avg_transaction_value',
    'lifetime_value': 'lifetime_value',
}

ML_MODEL_INPUT_SIZE = 5  # Number of features
```

**Optional: Custom Training Queries**

If your DWH schema is different, you can create custom queries in `settings.py`:

```python
# Custom query for NBO training
DWH_NBO_TRAINING_QUERY = """
    SELECT 
        customer_id,
        total_revenue,
        transaction_count,
        days_since_last_transaction,
        avg_transaction_value,
        lifetime_value,
        converted_offer_id
    FROM your_schema.customer_offer_history
    WHERE converted_offer_id IS NOT NULL
    AND created_at >= :start_date
    LIMIT 10000
"""

# Custom query for Churn training
DWH_CHURN_TRAINING_QUERY = """
    SELECT 
        customer_id,
        total_revenue,
        transaction_count,
        days_since_last_transaction,
        avg_transaction_value,
        lifetime_value,
        churned
    FROM your_schema.customer_churn_history
    WHERE churned IS NOT NULL
    AND snapshot_date >= :start_date
    LIMIT 10000
"""
```

#### 3. Run Training

```bash
python train_models_from_dwh.py
```

**What happens:**
1. Connects to DWH
2. Extracts training data
3. Preprocesses features (normalization)
4. Trains TensorFlow/Keras models
5. Converts to TensorFlow Lite
6. Saves to `models/` directory
7. Saves `StandardScaler` for inference preprocessing

#### 4. Verify Models

Check that models exist:
```bash
ls models/
# Should show:
# - nbo.tflite
# - churn.tflite
# - scaler.pkl (for preprocessing)
```

---

## Using ML Predictions

### NBO (Next Best Offer)

```python
from loyalty.ml.inference import MLInferenceService

ml_service = MLInferenceService()
nbo = ml_service.predict_nbo(customer_id='123e4567-e89b-12d3-a456-426614174000')

# Returns:
# {
#     'customer_id': '...',
#     'recommended_offer': 3,
#     'confidence': 0.85,
#     'all_offers': [
#         {'offer_id': 1, 'score': 0.2},
#         {'offer_id': 2, 'score': 0.3},
#         {'offer_id': 3, 'score': 0.85},  # Best offer
#         ...
#     ]
# }
```

### Churn Prediction

```python
churn = ml_service.predict_churn(customer_id='...')

# Returns:
# {
#     'customer_id': '...',
#     'churn_probability': 0.75,
#     'churn_risk': 'high',  # 'low', 'medium', 'high'
#     'recommendations': ['Send retention offer', 'Contact customer']
# }
```

### RFM Calculation

```python
rfm = ml_service.calculate_rfm(customer_id='...')

# Returns:
# {
#     'customer_id': '...',
#     'recency': 5,  # 1-5 scale
#     'frequency': 4,  # 1-5 scale
#     'monetary': 5,  # 1-5 scale
#     'segment': 'Champions'  # RFM segment name
# }
```

---

## Features & Segmentation (How ML Sees the Data)

### Where Features Come From

- Backend reads customer features from the **DWH** via `FeatureStore`:
  - Default table/view: `customer_features_view` (configurable via `DWH_CUSTOMER_FEATURES_TABLE`).
  - Each row becomes a Python dict, for example:
    ```python
    {
        "customer_id": "...",
        "total_revenue": 532.26,
        "transaction_count": 44,
        "days_since_last_transaction": 24,
        "avg_transaction_value": 33.41,
        "lifetime_value": 2348.01,
        "churn_score": 0.4864,
        "customer_status": "active",
        "active_products_count": 3,
        ...
    }
    ```
- These dicts are used by:
  - **MLInferenceService** (for churn/NBO/RFM).
  - **SegmentationEngine** (for JSONLogic segment rules).

### Where Features Are Defined in the Frontend

- The **Visual Rule Builder** (`VisualRuleBuilder.vue`) exposes feature fields to the user:
  - **Logical groups** (hard-coded):
    - Financial: `total_revenue`, `lifetime_value`, `avg_transaction_value`, `points_balance`
    - Activity: `transaction_count`, `last_purchase_days_ago`, `last_login_days_ago`
    - Profile: `customer_tier`, `segment`, `city`, `region`, `country`, `age`, `gender`
    - Risk & Engagement: `churn_score`, `campaign_engagement_rate`, `email_verified`, `phone_verified`
  - **Dynamic DWH columns**:
    - Fetched from `/api/loyalty/v1/dwh/columns/`
    - Shown under “DWH Columns” group
    - This means any column in `customer_features_view` can be used directly in segment rules.
- The **Segment Builder** (`SegmentBuilder.vue`) passes the DWH column list (`dwhColumns`) into the rule builder and also shows a **DWH column selector** panel for quick insertion into rules.

### JSONLogic Evaluation for Segments

- Segment rules are stored as JSONLogic on the `Segment` model and evaluated in the backend using `safe_json_logic` (`loyalty/utils.py`):
  - Supported operators:
    - `and`, `or`, `!`
    - `>`, `<`, `>=`, `<=`, `==`, `!=`
    - `in`
    - `{ "var": "field_name" }` to reference DWH feature keys.
  - Empty or `null` rule → interpreted as “always true”.
  - Evaluates directly against the DWH feature dict for each customer.
- This custom evaluator:
  - Avoids known issues in some `json_logic` versions (e.g. `'dict_keys' object is not subscriptable`).
  - Is used by `SegmentationEngine` to decide **segment membership** before ML runs.

For **segment-level ML endpoints and examples**, see `ML_SEGMENT_PREDICTIONS.md`.

---

## API Endpoints

### NBO Prediction

```
POST /api/loyalty/v1/dwh/ml/nbo/
{
    "customer_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Churn Prediction

```
POST /api/loyalty/v1/dwh/ml/churn/
{
    "customer_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### RFM Calculation

```
POST /api/loyalty/v1/dwh/ml/rfm/
{
    "customer_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

---

## Mock Mode

For testing without trained models:

```python
# settings.py
ML_MOCK_MODE = True
```

Mock mode returns realistic sample predictions without requiring model files.

---

## Model Retraining

### When to Retrain

- **Monthly** - Regular retraining with new data
- **After major changes** - Business rules changed
- **Performance degradation** - Model accuracy drops
- **New features** - DWH schema changed

### Retraining Process

1. Update DWH with new historical data
2. Run training script: `python train_models_from_dwh.py`
3. Models are automatically reloaded (or restart server)

---

## Troubleshooting

### Model Not Found

**Error:** `FileNotFoundError: models/nbo.tflite`

**Solution:**
1. Run training: `python train_models_from_dwh.py`
2. Verify models exist in `models/` directory
3. Check file permissions

### Feature Mismatch

**Error:** `ValueError: Feature count mismatch`

**Solution:**
1. Verify `ML_MODEL_INPUT_SIZE` matches model input size
2. Check `ML_FEATURE_MAPPING` matches DWH columns
3. Ensure all features are present in DWH

### Low Accuracy

**Problem:** Model predictions are inaccurate

**Solution:**
1. Check training data quality
2. Ensure sufficient training samples (1000+)
3. Verify feature mapping is correct
4. Retrain with more data

---

## Advanced Configuration

### Custom Model Architecture

Edit `train_models_from_dwh.py` to customize:
- Model architecture (layers, neurons)
- Training parameters (epochs, batch size)
- Loss functions
- Optimizers

### Feature Engineering

Add custom features in DWH:
1. Create computed columns in DWH views
2. Update `ML_FEATURE_MAPPING`
3. Retrain models

---

## Best Practices

1. **Regular Retraining** - Monthly retraining keeps models accurate
2. **Feature Validation** - Verify features exist before training
3. **Model Versioning** - Keep backups of previous models
4. **Performance Monitoring** - Track prediction accuracy over time
5. **A/B Testing** - Test new models before full deployment

---

## "God Mode" Features

**God Mode** = Predictive + Automated + Data-Driven Loyalty Management

### Complete Setup Checklist

1. ✅ **DWH Setup** - Customer data source
2. ✅ **Redis Setup** - Feature caching
3. ✅ **ML Models** - Trained and deployed
4. ✅ **Segmentation** - Dynamic segments with JSONLogic
5. ✅ **Kafka** (optional) - Event-driven automation

### God Mode Workflows

#### Automated Retention Campaign
```
1. DWH publishes customer update event → Kafka
2. Kafka consumer receives event
3. Feature Store invalidates cache
4. ML predicts churn → High risk detected
5. Segmentation Engine adds customer to "High Churn Risk" segment
6. Campaign triggers automatically
7. ML predicts NBO → Best retention offer selected
8. Offer sent to customer
```

#### Personalized Campaign
```
1. Campaign created targeting "VIP Customers" segment
2. Campaign triggers for segment members
3. For each customer:
   a. ML predicts NBO → Best offer selected
   b. Personalized message generated
   c. Sent via preferred channel
4. Performance tracked in real-time
```

---

## Next Steps

- See [DWH_INTEGRATION.md](DWH_INTEGRATION.md) for DWH setup
- See [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) for system workflow
- See [API_REFERENCE.md](API_REFERENCE.md) for API details
- See [ARCHITECTURE.md](ARCHITECTURE.md) for system architecture

