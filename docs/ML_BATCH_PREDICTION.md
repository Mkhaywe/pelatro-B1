# ML Batch Prediction & Model Files Guide

## Overview

This document explains:
1. Why model files are missing and how to create them
2. How to use batch prediction for multiple customers

---

## 🔍 Missing Model Files

### Why Are Model Files Missing?

The ML models (`models/nbo.tflite` and `models/churn.tflite`) are **not automatically created**. You need to generate them using one of these methods:

### What Does `create_ml_models.py` Do?

**`create_ml_models.py`** creates **placeholder TensorFlow Lite models** trained on **random/dummy data**:

1. **Creates NBO Model** (`models/nbo.tflite`)
   - Simple 3-layer neural network (32 → 16 → 8 neurons)
   - Input: 10 features, Output: 8 offer probabilities
   - Trained on 100 random samples

2. **Creates Churn Model** (`models/churn.tflite`)
   - Simple 3-layer neural network (32 → 16 → 1 neuron)
   - Input: 10 features, Output: churn probability (0-1)
   - Trained on 100 random samples

⚠️ **Important**: These are **placeholder models** - they work but predictions are **not accurate**. They're just to get the system running. For production, use `train_models_from_dwh.py` to train on your real data.

See `ML_SEGMENT_PREDICTIONS.md` for more details.

### Option 1: Create Placeholder Models (Quick Start)

For development and testing, create simple placeholder models:

```bash
python create_ml_models.py
```

**What this does:**
- Creates `models/nbo.tflite` - Next Best Offer prediction model
- Creates `models/churn.tflite` - Churn prediction model
- These are simple models that work but need to be replaced with trained models for production

**Requirements:**
- TensorFlow >= 2.10.0
- NumPy

**Install dependencies:**
```bash
pip install tensorflow numpy
```

### Option 2: Train Real Models from DWH Data (Production)

For production, train models using your DWH historical data:

```bash
python train_models_from_dwh.py
```

**What this does:**
- Connects to your DWH database
- Extracts historical customer data
- Trains TensorFlow/Keras models
- Converts to TensorFlow Lite format
- Saves to `models/` directory
- Also saves `StandardScaler` for preprocessing

**Requirements:**
- DWH database set up with historical data
- TensorFlow >= 2.10.0
- NumPy
- Pandas
- Scikit-learn

**See:** `ML_TRAINING_STEP_BY_STEP.md` for detailed training instructions.

### Mock Mode

If model files are missing, the system automatically uses **Mock Mode**:
- Predictions return realistic mock data
- Useful for testing without actual models
- Clearly indicated in the UI

**To disable mock mode:**
Set `ML_MOCK_MODE = False` in `loyalty_project/settings.py` (requires model files).

---

## 📊 Batch Prediction

### What Is Batch Prediction?

Batch prediction allows you to run ML predictions for **multiple customers at once** instead of one at a time.

### Benefits

1. **Efficiency**: Process 100 customers in one request instead of 100 separate requests
2. **Performance**: Faster than sequential single predictions
3. **Convenience**: Test multiple customers simultaneously

### How to Use

#### In the Admin UI

1. Go to **Admin → ML & AI** tab
2. Scroll to **"Test ML Predictions"** section
3. Toggle to **"Batch (Multiple Customers)"** mode
4. Enter customer IDs, one per line:
   ```
   customer-uuid-1
   customer-uuid-2
   customer-uuid-3
   ```
5. Select prediction type (Churn, NBO, or RFM)
6. Click **"Run Batch Prediction"**

#### API Usage

**Single Customer (backward compatible):**
```http
POST /api/loyalty/v1/config/ml/test/
Content-Type: application/json

{
  "customer_id": "customer-uuid-1",
  "type": "churn"
}
```

**Batch (Multiple Customers):**
```http
POST /api/loyalty/v1/config/ml/test/
Content-Type: application/json

{
  "customer_ids": [
    "customer-uuid-1",
    "customer-uuid-2",
    "customer-uuid-3"
  ],
  "type": "churn"
}
```

### Batch Response Format

```json
{
  "type": "churn",
  "mode": "batch",
  "total": 3,
  "successful": 2,
  "failed": 1,
  "results": [
    {
      "customer_id": "customer-uuid-1",
      "result": {
        "customer_id": "customer-uuid-1",
        "churn_probability": 0.65,
        "churn_risk": "medium"
      }
    },
    {
      "customer_id": "customer-uuid-2",
      "result": {
        "customer_id": "customer-uuid-2",
        "churn_probability": 0.85,
        "churn_risk": "high"
      }
    }
  ],
  "errors": [
    {
      "customer_id": "customer-uuid-3",
      "error": "Customer not found in DWH"
    }
  ]
}
```

### Limits

- **Maximum batch size**: 100 customers per request
- **Timeout**: 60 seconds (adjustable in Django settings)

### Error Handling

Batch predictions handle errors gracefully:
- **Partial success**: Some customers succeed, others fail
- **Error details**: Each failed customer includes error message
- **No interruption**: One failure doesn't stop the batch

---

## 🎯 Quick Start Checklist

### Step 1: Create Model Files

```bash
# Quick placeholder models
python create_ml_models.py

# OR train real models from DWH
python train_models_from_dwh.py
```

### Step 2: Verify Models

1. Check Admin UI → ML & AI → Model Status
2. Both models should show "File Exists" and "Loaded"

### Step 3: Test Predictions

**Single Customer:**
- Use "Single Customer" mode
- Enter one customer ID
- Run prediction

**Batch:**
- Use "Batch (Multiple Customers)" mode
- Enter multiple customer IDs (one per line)
- Run batch prediction

---

## 🔧 Troubleshooting

### Model Files Still Missing After Running Script

1. **Check script output**: Look for errors
2. **Verify TensorFlow**: `python -c "import tensorflow; print(tensorflow.__version__)"`
3. **Check directory**: Ensure `models/` directory exists
4. **Permissions**: Ensure write permissions to `models/` directory

### Batch Prediction Fails

1. **Check customer IDs**: Ensure they exist in DWH/Xiva
2. **Check batch size**: Maximum 100 customers
3. **Check logs**: Django server logs show detailed errors
4. **Verify DWH connection**: Ensure DWH is configured correctly

### Mock Mode Still Active

1. **Check model files exist**: `ls models/*.tflite`
2. **Check settings**: `ML_MOCK_MODE` in `settings.py`
3. **Restart Django**: Restart server after creating models

---

## 📚 Related Documentation

- **`ML_SEGMENT_PREDICTIONS.md`** - ML predictions for entire segments (recommended!)
- **`ML_TRAINING_STEP_BY_STEP.md`** - Detailed ML training guide
- **`DWH_SETUP_GUIDE.md`** - DWH setup for training data
- **`SCRIPTS_REFERENCE.md`** - All Python scripts reference
- **`API_REFERENCE.md`** - API endpoints documentation

---

## 💡 Segment-Level Predictions (Recommended)

**You're right!** ML predictions should be available at the **segment level**, not just individual customers.

### Why Segment-Level?

- **Analyze segment health**: Average churn risk for "High Value Customers"
- **Target campaigns**: Which offers work best for "At Risk" segment?
- **Monitor trends**: How is churn risk changing for segments?
- **Make decisions**: Create retention campaigns for high-churn segments

### New Endpoints Added

1. **`POST /api/loyalty/v1/segments/{id}/ml/predict/`** - Run ML predictions for all customers in segment
2. **`GET /api/loyalty/v1/segments/{id}/ml/stats/`** - Get aggregated ML statistics for segment

See **`ML_SEGMENT_PREDICTIONS.md`** for complete documentation and examples!

---

## 💡 Best Practices

1. **Development**: Use placeholder models (`create_ml_models.py`)
2. **Production**: Train real models from DWH data (`train_models_from_dwh.py`)
3. **Testing**: Use batch prediction for testing multiple scenarios
4. **Monitoring**: Check model status regularly in Admin UI
5. **Retraining**: Retrain models periodically as new data becomes available

---

**Last Updated**: 2026-01-02

