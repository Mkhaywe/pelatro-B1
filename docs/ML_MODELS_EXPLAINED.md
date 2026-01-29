# ML Models in the Loyalty System - Explained

## 🤔 Why Only Two Models?

The system currently has **2 ML models** plus **1 calculated metric**:

### Current Models:

1. **Churn Prediction Model** (`models/churn.tflite`)
   - **Purpose**: Predicts probability that a customer will churn (leave)
   - **Input**: 10 customer features (revenue, transactions, usage, etc.)
   - **Output**: Churn probability (0-1)
   - **Use Case**: Identify at-risk customers for retention campaigns

2. **Next Best Offer (NBO) Model** (`models/nbo.tflite`)
   - **Purpose**: Predicts which offer is most likely to convert for each customer
   - **Input**: 10 customer features
   - **Output**: 8 offer probabilities (one for each offer type)
   - **Use Case**: Personalize offers to maximize conversion

3. **RFM Analysis** (Calculated, not ML)
   - **Purpose**: Segments customers by Recency, Frequency, Monetary value
   - **Method**: Rule-based calculation (not machine learning)
   - **Use Case**: Customer segmentation and value analysis

---

## 🎯 Why Not More Models?

### Design Philosophy

The system is designed to be **modular and extensible**. You can add more models as needed!

### Common Models You Could Add:

1. **Lifetime Value (LTV) Prediction**
   - Predicts total future value of a customer
   - Useful for: Prioritizing high-value customers, budget allocation

2. **Propensity to Buy**
   - Predicts likelihood customer will make a purchase
   - Useful for: Timing campaigns, product recommendations

3. **Product Recommendation**
   - Recommends specific products/services
   - Useful for: Cross-selling, upselling

4. **Campaign Response Prediction**
   - Predicts if customer will respond to a campaign
   - Useful for: Campaign targeting, ROI optimization

5. **Payment Default Risk**
   - Predicts if customer will default on payments
   - Useful for: Credit risk management

6. **Upsell/Cross-sell Propensity**
   - Predicts likelihood to upgrade or buy additional products
   - Useful for: Revenue optimization

7. **Engagement Score**
   - Predicts customer engagement level
   - Useful for: Segment prioritization

---

## 🚀 How to Add More Models

### Step 1: Create Model File

Add model path to `loyalty/ml/inference.py`:

```python
def _load_models(self):
    model_paths = {
        'nbo': getattr(settings, 'ML_MODEL_NBO_PATH', 'models/nbo.tflite'),
        'churn': getattr(settings, 'ML_MODEL_CHURN_PATH', 'models/churn.tflite'),
        'ltv': getattr(settings, 'ML_MODEL_LTV_PATH', 'models/ltv.tflite'),  # NEW
        'propensity': getattr(settings, 'ML_MODEL_PROPENSITY_PATH', 'models/propensity.tflite'),  # NEW
        'rfm': None,  # RFM is calculated, not ML model
    }
```

### Step 2: Add Prediction Method

Add method to `MLInferenceService`:

```python
def predict_ltv(self, customer_id: str) -> Dict:
    """Predict customer lifetime value"""
    if MOCK_ML_ENABLED:
        mock_service = MockMLInferenceService()
        return mock_service.predict_ltv(customer_id)
    
    if 'ltv' not in self.models:
        return {'error': 'LTV model not available'}
    
    features = self._extract_features(customer_id)
    # ... run inference ...
    return {
        'customer_id': customer_id,
        'predicted_ltv': ltv_value,
        'confidence': confidence
    }
```

### Step 3: Add Training Script

Create training script or extend `train_models_from_dwh.py`:

```python
def train_ltv_model(X, y):
    """Train LTV prediction model"""
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(64, activation='relu', input_shape=(10,)),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(1, activation='linear')  # Regression
    ])
    # ... training code ...
```

### Step 4: Add API Endpoint

Add endpoint in `loyalty/views_khaywe.py` or create new view:

```python
@action(detail=True, methods=['post'], url_path='predict/ltv')
def predict_ltv(self, request, pk=None):
    """Predict LTV for customer"""
    customer = self.get_object()
    ml_service = MLInferenceService()
    result = ml_service.predict_ltv(customer.id)
    return Response(result)
```

### Step 5: Add Frontend UI

Add UI component in `frontend/src/views/Admin/components/MLConfiguration.vue` or create new component.

---

## 📊 Why Start with Just 2 Models?

### 1. **Focus on Core Use Cases**
- **Churn**: Most critical - losing customers is expensive
- **NBO**: Direct revenue impact - better offers = more conversions

### 2. **Proven Value**
- These are the most commonly used models in loyalty systems
- High ROI and clear business impact

### 3. **Foundation First**
- Get the infrastructure working (DWH, feature extraction, model serving)
- Then add more models as needed

### 4. **Flexibility**
- System is designed to easily add more models
- No need to rebuild everything

---

## 🎓 Model Types Explained

### Classification Models (Churn, NBO)
- **Purpose**: Predict categories/classes
- **Churn**: Binary (will churn / won't churn)
- **NBO**: Multi-class (which of 8 offers)

### Regression Models (LTV, Revenue)
- **Purpose**: Predict numeric values
- **LTV**: Predict dollar amount
- **Revenue**: Predict future revenue

### Ranking Models (Recommendations)
- **Purpose**: Rank items by relevance
- **Product Recommendations**: Rank products by interest
- **Content Recommendations**: Rank content by engagement

---

## ✅ Summary

**Current Models:**
- ✅ Churn Prediction (ML)
- ✅ Next Best Offer (ML)
- ✅ RFM Analysis (Calculated)

**Why Only 2 ML Models:**
- Focus on core, high-impact use cases
- Foundation for adding more models later
- System is extensible - easy to add more

**How to Add More:**
1. Create model file
2. Add prediction method
3. Add training script
4. Add API endpoint
5. Add frontend UI

**The system is designed to grow with your needs!** Start with churn and NBO, then add more models as you identify new use cases.

