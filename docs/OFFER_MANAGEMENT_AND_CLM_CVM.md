# Offer Management, CLM, and CVM Integration

## 🔍 Current Issue: Missing Offer Catalog

**The Problem:**
- NBO model predicts offer IDs (0-7) but there's **no offer catalog**
- No way to fetch offer details (name, description, category, etc.)
- Offers are hardcoded in mock service only

**The Solution:**
We need to create an **Offer Management System** that:
1. Stores offer catalog in local database
2. Can sync from external system (Xiva, etc.)
3. Links ML predictions to actual offers
4. Supports CLM (Customer Lifecycle Management) and CVM (Customer Value Management)

---

## 📋 Solution Architecture

### 1. Offer Catalog Model

Create an `Offer` model to store offer details:

```python
class Offer(models.Model):
    """Offer catalog for ML predictions"""
    offer_id = models.IntegerField(unique=True)  # 0-7 for NBO model
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50)  # 'points', 'discount', 'access', etc.
    is_active = models.BooleanField(default=True)
    
    # CLM/CVM fields
    lifecycle_stage = models.CharField(max_length=50)  # 'acquisition', 'retention', 'win_back', 'growth'
    target_segment = models.CharField(max_length=50)  # 'high_value', 'at_risk', 'new', etc.
    min_customer_value = models.DecimalField(null=True, blank=True)
    max_customer_value = models.DecimalField(null=True, blank=True)
    
    # External system sync
    external_offer_id = models.CharField(max_length=255, blank=True)
    external_system = models.CharField(max_length=50, blank=True)  # 'xiva', 'crm', etc.
    last_synced = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 2. Offer Sync Service

Create service to sync offers from external systems:

```python
class OfferSyncService:
    """Sync offers from external systems (Xiva, CRM, etc.)"""
    
    def sync_from_xiva(self):
        """Fetch offers from Xiva API and store locally"""
        # Call Xiva API to get offers
        # Map to Offer model
        # Store in database
        pass
    
    def sync_from_crm(self):
        """Fetch offers from CRM system"""
        pass
```

### 3. Enhanced NBO Prediction

Update ML inference to return offer details:

```python
def predict_nbo(self, customer_id: str) -> Dict:
    # ... existing prediction code ...
    
    # Fetch offer details from catalog
    from loyalty.models import Offer
    try:
        offer = Offer.objects.get(offer_id=recommended_offer, is_active=True)
        offer_details = {
            'offer_id': offer.offer_id,
            'name': offer.name,
            'description': offer.description,
            'category': offer.category,
            'lifecycle_stage': offer.lifecycle_stage,
        }
    except Offer.DoesNotExist:
        offer_details = {
            'offer_id': recommended_offer,
            'name': f'Offer #{recommended_offer}',
            'description': 'Offer details not available',
        }
    
    return {
        'customer_id': customer_id,
        'recommended_offer': recommended_offer,
        'offer_details': offer_details,
        'offer_scores': offer_scores,
        'confidence': confidence,
        'explanation': explanation
    }
```

---

## 🎯 CLM (Customer Lifecycle Management)

### What is CLM?

**Customer Lifecycle Management** tracks and manages customers through their lifecycle stages:
- **Acquisition**: New customers
- **Onboarding**: First-time users
- **Growth**: Increasing engagement
- **Retention**: Maintaining loyalty
- **Win-back**: Re-engaging inactive customers
- **Churn**: At-risk customers

### Implementation

```python
class CustomerLifecycleStage(models.Model):
    """Customer lifecycle stages"""
    customer_id = models.UUIDField()
    stage = models.CharField(max_length=50)  # 'acquisition', 'onboarding', etc.
    entered_at = models.DateTimeField(auto_now_add=True)
    exited_at = models.DateTimeField(null=True, blank=True)
    duration_days = models.IntegerField(null=True)
    
class CLMService:
    """Customer Lifecycle Management Service"""
    
    def get_customer_stage(self, customer_id: str) -> str:
        """Get current lifecycle stage"""
        # Use ML predictions + business rules
        churn_prob = ml_service.predict_churn(customer_id)
        if churn_prob > 0.7:
            return 'churn_risk'
        # ... more logic ...
    
    def recommend_actions(self, customer_id: str) -> List[Dict]:
        """Recommend actions based on lifecycle stage"""
        stage = self.get_customer_stage(customer_id)
        # Return recommended offers, campaigns, etc.
```

---

## 💰 CVM (Customer Value Management)

### What is CVM?

**Customer Value Management** focuses on maximizing customer lifetime value through:
- **Value Segmentation**: High/Medium/Low value customers
- **Value-Based Targeting**: Different strategies for different value tiers
- **Value Optimization**: Increase customer value over time

### Implementation

```python
class CustomerValueSegment(models.Model):
    """Customer value segments"""
    customer_id = models.UUIDField()
    segment = models.CharField(max_length=50)  # 'high_value', 'medium_value', 'low_value'
    lifetime_value = models.DecimalField()
    predicted_ltv = models.DecimalField(null=True)  # From LTV model
    value_score = models.DecimalField()  # 0-100
    calculated_at = models.DateTimeField(auto_now_add=True)

class CVMService:
    """Customer Value Management Service"""
    
    def calculate_customer_value(self, customer_id: str) -> Dict:
        """Calculate customer value using RFM + LTV prediction"""
        # Get RFM scores
        rfm = ml_service.calculate_rfm(customer_id)
        
        # Get LTV prediction
        ltv = ml_service.predict_ltv(customer_id)  # New model
        
        # Calculate value score
        value_score = (rfm['m_score'] * 0.4 + ltv['predicted_ltv'] * 0.6)
        
        return {
            'customer_id': customer_id,
            'rfm_segment': rfm['segment'],
            'predicted_ltv': ltv['predicted_ltv'],
            'value_score': value_score,
            'value_segment': self._get_value_segment(value_score)
        }
    
    def get_value_based_offers(self, customer_id: str) -> List[Dict]:
        """Get offers based on customer value"""
        value = self.calculate_customer_value(customer_id)
        # Return offers matching value segment
```

---

## 🤖 Adding Additional ML Models

### Models to Add:

1. **Lifetime Value (LTV) Prediction**
2. **Propensity to Buy**
3. **Product Recommendation**
4. **Campaign Response Prediction**
5. **Payment Default Risk**
6. **Upsell/Cross-sell Propensity**
7. **Engagement Score**

### Implementation Steps:

#### Step 1: Create Model Files

Add to `loyalty/ml/inference.py`:

```python
def _load_models(self):
    model_paths = {
        'nbo': getattr(settings, 'ML_MODEL_NBO_PATH', 'models/nbo.tflite'),
        'churn': getattr(settings, 'ML_MODEL_CHURN_PATH', 'models/churn.tflite'),
        'ltv': getattr(settings, 'ML_MODEL_LTV_PATH', 'models/ltv.tflite'),  # NEW
        'propensity': getattr(settings, 'ML_MODEL_PROPENSITY_PATH', 'models/propensity.tflite'),  # NEW
        'product_recommendation': getattr(settings, 'ML_MODEL_PRODUCT_PATH', 'models/product.tflite'),  # NEW
        'campaign_response': getattr(settings, 'ML_MODEL_CAMPAIGN_PATH', 'models/campaign.tflite'),  # NEW
        'default_risk': getattr(settings, 'ML_MODEL_DEFAULT_PATH', 'models/default.tflite'),  # NEW
        'upsell': getattr(settings, 'ML_MODEL_UPSELL_PATH', 'models/upsell.tflite'),  # NEW
        'engagement': getattr(settings, 'ML_MODEL_ENGAGEMENT_PATH', 'models/engagement.tflite'),  # NEW
        'rfm': None,  # RFM is calculated, not ML model
    }
```

#### Step 2: Add Prediction Methods

```python
def predict_ltv(self, customer_id: str) -> Dict:
    """Predict customer lifetime value"""
    # Similar to predict_churn but outputs LTV amount
    
def predict_propensity_to_buy(self, customer_id: str) -> Dict:
    """Predict likelihood to make a purchase"""
    # Binary classification: will buy / won't buy
    
def recommend_products(self, customer_id: str) -> Dict:
    """Recommend products/services"""
    # Multi-class: product IDs with probabilities
    
def predict_campaign_response(self, customer_id: str, campaign_id: str) -> Dict:
    """Predict if customer will respond to campaign"""
    # Binary: will respond / won't respond
    
def predict_payment_default(self, customer_id: str) -> Dict:
    """Predict payment default risk"""
    # Binary: will default / won't default
    
def predict_upsell_propensity(self, customer_id: str) -> Dict:
    """Predict likelihood to upgrade/buy more"""
    # Binary or multi-class
    
def calculate_engagement_score(self, customer_id: str) -> Dict:
    """Calculate customer engagement score"""
    # Regression: engagement score 0-100
```

#### Step 3: Create Training Scripts

Extend `train_models_from_dwh.py` or create separate scripts for each model.

---

## 🚀 Implementation Plan

### Phase 1: Offer Management (Priority 1)

1. ✅ Create `Offer` model
2. ✅ Create migration
3. ✅ Create Offer sync service
4. ✅ Update NBO prediction to return offer details
5. ✅ Create API endpoints for offer management
6. ✅ Create frontend UI for offer catalog

### Phase 2: CLM Integration (Priority 2)

1. ✅ Create `CustomerLifecycleStage` model
2. ✅ Create `CLMService`
3. ✅ Integrate with ML predictions
4. ✅ Create lifecycle dashboard
5. ✅ Add lifecycle-based campaign targeting

### Phase 3: CVM Integration (Priority 2)

1. ✅ Create `CustomerValueSegment` model
2. ✅ Create `CVMService`
3. ✅ Integrate LTV prediction
4. ✅ Create value-based segmentation
5. ✅ Add value-based offer recommendations

### Phase 4: Additional ML Models (Priority 3)

1. ✅ Add LTV prediction model
2. ✅ Add Propensity to Buy model
3. ✅ Add Product Recommendation model
4. ✅ Add Campaign Response model
5. ✅ Add Payment Default Risk model
6. ✅ Add Upsell/Cross-sell model
7. ✅ Add Engagement Score model

---

## 📊 Data Flow

```
External System (Xiva/CRM)
    ↓
Offer Sync Service
    ↓
Local Offer Catalog (Database)
    ↓
ML NBO Prediction
    ↓
Offer Details + Prediction
    ↓
Frontend Display
```

---

## 🔧 Configuration

### Settings for Offer Management

```python
# Offer Management
OFFER_SYNC_ENABLED = os.environ.get('OFFER_SYNC_ENABLED', 'False') == 'True'
OFFER_SYNC_SOURCE = os.environ.get('OFFER_SYNC_SOURCE', 'xiva')  # 'xiva', 'crm', 'manual'
OFFER_SYNC_INTERVAL = int(os.environ.get('OFFER_SYNC_INTERVAL', '3600'))  # seconds

# CLM Configuration
CLM_ENABLED = os.environ.get('CLM_ENABLED', 'True') == 'True'
CLM_STAGES = ['acquisition', 'onboarding', 'growth', 'retention', 'win_back', 'churn']

# CVM Configuration
CVM_ENABLED = os.environ.get('CVM_ENABLED', 'True') == 'True'
CVM_VALUE_SEGMENTS = ['high_value', 'medium_value', 'low_value']
```

---

## ✅ Next Steps

1. **Create Offer model and migration**
2. **Create Offer sync service**
3. **Update NBO prediction to use offer catalog**
4. **Add CLM and CVM models/services**
5. **Create training scripts for new ML models**
6. **Add frontend UI for offer management**

Would you like me to implement these now?

