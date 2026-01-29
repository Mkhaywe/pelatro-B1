# ML Predictions for Segments

## Overview

ML predictions are now available at **both customer and segment levels**:

- **Customer-level**: Predict churn/NBO/RFM for individual customers
- **Segment-level**: Predict churn/NBO/RFM for all customers in a segment with aggregated statistics

---

## What Does `create_ml_models.py` Do?

### Purpose

Creates **placeholder TensorFlow Lite models** for development and testing.

### What It Creates

1. **NBO Model** (`models/nbo.tflite`)
   - Input: 10 customer features
   - Output: 8 offer probabilities (softmax)
   - Architecture: 3-layer neural network (32 → 16 → 8 neurons)

2. **Churn Model** (`models/churn.tflite`)
   - Input: 10 customer features
   - Output: Churn probability (0-1, sigmoid)
   - Architecture: 3-layer neural network (32 → 16 → 1 neuron)

### Important Notes

⚠️ **These are placeholder models trained on RANDOM/DUMMY data!**

- They work but predictions are **not accurate**
- They're just to get the system running
- **Must be replaced** with real trained models for production

### How It Works

1. Creates simple neural networks using TensorFlow/Keras
2. Trains them on random dummy data (100 samples)
3. Converts to TensorFlow Lite format (optimized for inference)
4. Saves to `models/` directory

### For Production

Use `train_models_from_dwh.py` instead:
- Trains on your real DWH historical data
- Much more accurate predictions
- See `ML_TRAINING_STEP_BY_STEP.md` for details

---

## Segment-Level ML Predictions

### Why Segment-Level?

In loyalty systems, you often need to:
- **Analyze segment health**: What's the average churn risk for "High Value Customers"?
- **Target campaigns**: Which offers work best for "At Risk" segment?
- **Monitor trends**: How is churn risk changing for "VIP" segment?
- **Make decisions**: Should we create a retention campaign for segments with high churn?

### How Segments, Features, and ML Work Together

- **Feature source**: All ML and segmentation logic uses the **DWH customer features view** (by default `customer_features_view`).
  - Each row in that view becomes a Python dict like:
    - `{'customer_id': '...', 'total_revenue': 532.26, 'churn_score': 0.46, 'active_products_count': 3, 'customer_status': 'active', ...}`
  - These dictionaries are produced by the `FeatureStore` (`loyalty/integration/feature_store.py`) and cached in Redis.
- **Segment rules (JSONLogic)**:
  - In the frontend, the **Visual Rule Builder** (`VisualRuleBuilder.vue`) lets you define conditions using:
    - Built-in logical fields (Financial, Activity, Profile, Risk & Engagement)
    - Actual DWH columns (from `/api/loyalty/v1/dwh/columns/`, shown under “DWH Columns”)
  - The builder generates JSONLogic rules like:
    ```json
    {
      "and": [
        { ">":  [ { "var": "active_products_count" }, 2 ] },
        { "==": [ { "var": "customer_status" }, "active" ] },
        { ">":  [ { "var": "total_revenue" }, 200 ] }
      ]
    }
    ```
  - These rules are stored on the `Segment` model and evaluated in the backend.
- **JSONLogic evaluation (backend)**:
  - The backend uses `safe_json_logic` in `loyalty/utils.py`, which:
    - Implements a **small, robust JSONLogic evaluator** for:
      - `and`, `or`, `!`
      - `>`, `<`, `>=`, `<=`, `==`, `!=`
      - `in`
      - `{ "var": "field_name" }` references
    - Works directly on the DWH feature dict for each customer.
    - Treats empty rules as “always true”.
    - Avoids older `json_logic` library issues (e.g. `'dict_keys' object is not subscriptable`).
- **ML on a segment**:
  - Segment rules decide **which customers belong to the segment** (based on DWH features).
  - ML (`MLInferenceService`) runs **per customer** (churn, NBO, RFM) using the same features.
  - Segment-level ML endpoints aggregate those per-customer predictions for all segment members.

In short: **DWH features → JSONLogic rules decide segment membership → ML runs on those members and is aggregated at segment level.**

### API Endpoints

#### 1. Run ML Predictions for Segment

**Endpoint:** `POST /api/loyalty/v1/segments/{segment_id}/ml/predict/`

**Request:**
```json
{
  "type": "churn"  // or "nbo" or "rfm"
}
```

**Response:**
```json
{
  "segment_id": 1,
  "segment_name": "High Value Customers",
  "type": "churn",
  "mode": "segment",
  "total_customers": 1250,
  "processed": 1000,
  "successful": 998,
  "failed": 2,
  "warning": "Limited to first 1000 customers (segment has 1250 total)",
  "aggregated_stats": {
    "churn": {
      "high": 150,
      "medium": 300,
      "low": 548,
      "avg_probability": 0.42
    }
  },
  "results": [...],  // First 100 results
  "errors": [...],   // First 10 errors
  "has_more_results": true
}
```

#### 2. Get Aggregated ML Statistics

**Endpoint:** `GET /api/loyalty/v1/segments/{segment_id}/ml/stats/`

**Response:**
```json
{
  "segment_id": 1,
  "segment_name": "High Value Customers",
  "member_count": 1250,
  "sampled_count": 1000,
  "stats": {
    "churn": {
      "high": 150,
      "medium": 300,
      "low": 550,
      "count": 1000,
      "avg_probability": 0.42,
      "high_percentage": 15.0,
      "medium_percentage": 30.0,
      "low_percentage": 55.0
    },
    "nbo": {
      "top_offers": [
        ["offer_3", 250],
        ["offer_1", 200],
        ["offer_5", 180]
      ],
      "distribution": {
        "offer_1": 200,
        "offer_3": 250,
        "offer_5": 180
      }
    },
    "rfm": {
      "distribution": {
        "Champions": 300,
        "Loyal Customers": 250,
        "At Risk": 150
      },
      "top_segments": [
        ["Champions", 300],
        ["Loyal Customers", 250]
      ]
    }
  }
}
```

---

## Use Cases

### 1. Segment Health Dashboard

```javascript
// Get churn stats for all segments
const segments = await segmentsApi.getAll()
for (const segment of segments) {
  const stats = await segmentsApi.getMLStats(segment.id)
  console.log(`${segment.name}: ${stats.stats.churn.high_percentage}% high churn risk`)
}
```

### 2. Campaign Targeting

```javascript
// Find segments with high churn risk
const highChurnSegments = []
for (const segment of segments) {
  const stats = await segmentsApi.getMLStats(segment.id)
  if (stats.stats.churn.high_percentage > 20) {
    highChurnSegments.push(segment)
  }
}
// Create retention campaigns for these segments
```

### 3. Offer Optimization

```javascript
// See which offers work best for a segment
const stats = await segmentsApi.getMLStats(segmentId)
const topOffer = stats.stats.nbo.top_offers[0][0]
// Use this offer in campaigns targeting this segment
```

---

## Frontend Integration

### Segment Detail Page

Add ML prediction tabs to segment detail page:

```vue
<template>
  <div>
    <h2>{{ segment.name }}</h2>
    
    <!-- ML Predictions Tab -->
    <tabs>
      <tab name="Overview">...</tab>
      <tab name="ML Predictions">
        <MLSegmentStats :segment-id="segment.id" />
      </tab>
    </tabs>
  </div>
</template>
```

### ML Segment Stats Component

```vue
<script setup>
import { ref, onMounted } from 'vue'
import { segmentsApi } from '@/api/services/segments'

const props = defineProps(['segmentId'])
const stats = ref(null)
const loading = ref(false)

const loadStats = async () => {
  loading.value = true
  try {
    const response = await segmentsApi.getMLStats(props.segmentId)
    stats.value = response.data
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
</script>

<template>
  <div>
    <h3>Churn Risk Distribution</h3>
    <div>
      High Risk: {{ stats?.stats.churn.high_percentage }}%
      Medium Risk: {{ stats?.stats.churn.medium_percentage }}%
      Low Risk: {{ stats?.stats.churn.low_percentage }}%
    </div>
    
    <h3>Top Recommended Offers</h3>
    <ul>
      <li v-for="[offer, count] in stats?.stats.nbo.top_offers" :key="offer">
        {{ offer }}: {{ count }} customers
      </li>
    </ul>
  </div>
</template>
```

---

## Performance Considerations

### Batch Limits

- **Segment prediction**: Limited to 1000 customers per request
- **Stats endpoint**: Samples first 1000 customers for performance
- **Results preview**: Returns first 100 individual results

### Caching

Consider caching segment ML stats:
- Recalculate periodically (e.g., daily)
- Cache results for 1 hour
- Invalidate on segment recalculation

### Async Processing

For large segments (>1000 customers):
- Use async task queue (Celery)
- Process in batches
- Store results in database
- Poll for completion

---

## Comparison: Customer vs Segment Predictions

| Feature | Customer-Level | Segment-Level |
|---------|---------------|---------------|
| **Use Case** | Individual customer insights | Segment analysis & targeting |
| **Input** | Single customer ID | Segment ID |
| **Output** | Single prediction | Aggregated statistics |
| **Performance** | Fast (<100ms) | Slower (depends on segment size) |
| **Best For** | Customer 360 view | Campaign planning, monitoring |

---

## Example Workflow

### 1. Monitor Segment Health

```bash
# Get churn stats for "VIP Customers" segment
curl -X GET /api/loyalty/v1/segments/5/ml/stats/
```

### 2. Identify At-Risk Segments

```bash
# Run churn predictions for all segments
for segment_id in 1 2 3 4 5; do
  curl -X POST /api/loyalty/v1/segments/$segment_id/ml/predict/ \
    -d '{"type": "churn"}'
done
```

### 3. Create Targeted Campaigns

```bash
# Find best offer for "At Risk" segment
curl -X POST /api/loyalty/v1/segments/3/ml/predict/ \
  -d '{"type": "nbo"}'
```

---

## Related Documentation

- **`ML_BATCH_PREDICTION.md`** - Batch predictions for multiple customers
- **`ML_TRAINING_STEP_BY_STEP.md`** - How to train real models
- **`DWH_SETUP_GUIDE.md`** - DWH setup for ML features
- **`API_REFERENCE.md`** - Complete API documentation

---

**Last Updated**: 2026-01-02

