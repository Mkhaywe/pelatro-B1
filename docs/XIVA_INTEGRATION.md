# Xiva Integration Guide

## Overview

Xiva BSS integration allows the loyalty platform to use Xiva customer data for segmentation, ML predictions, and campaign targeting - similar to how DWH is used.

## Architecture

### How Xiva Integrates

```
Xiva BSS API
    ↓ (REST API)
XivaClient
    ↓
FeatureStore (Redis Cache)
    ↓
SegmentationEngine / ML Models
    ↓
Campaigns / Recommendations
```

**Same pattern as DWH!** Xiva data flows through the same FeatureStore.

---

## Configuration

### Step 1: Set Xiva API Credentials

In `.env` file:

```env
XIVA_API_BASE_URL=https://www.xiva.ca/api
XIVA_API_USERNAME=your_username
XIVA_API_PASSWORD=your_password
```

### Step 2: Configure Feature Store

In `loyalty_project/settings.py`:

```python
# Use Xiva as data source
FEATURE_STORE_DATA_SOURCE = 'xiva'  # or 'dwh', 'auto'

# Or use both (auto mode)
FEATURE_STORE_DATA_SOURCE = 'auto'
FEATURE_STORE_MERGE_STRATEGY = 'xiva_first'  # Xiva takes precedence
```

---

## Data Source Options

### Option 1: Xiva Only

```python
FEATURE_STORE_DATA_SOURCE = 'xiva'
```

**Use when:** Xiva has all the data you need

**Pros:**
- Single source of truth
- Real-time data
- No DWH required

**Cons:**
- API rate limits
- No SQL queries
- Dependent on Xiva availability

### Option 2: Xiva + DWH (Auto Mode)

```python
FEATURE_STORE_DATA_SOURCE = 'auto'
FEATURE_STORE_MERGE_STRATEGY = 'xiva_first'
```

**Use when:** You want both real-time (Xiva) and historical (DWH) data

**Pros:**
- Best of both worlds
- Xiva for real-time, DWH for historical
- Fallback if one source fails

**Cons:**
- Need to merge data from two sources
- More complex configuration

### Option 3: DWH Only

```python
FEATURE_STORE_DATA_SOURCE = 'dwh'
```

**Use when:** You only have DWH, no Xiva integration

---

## Xiva Feature Extraction

The system automatically extracts features from Xiva API responses:

### Available Features

- `customer_id` - Customer UUID
- `customer_status` - Active/Inactive
- `total_revenue` - Total revenue (if available)
- `transaction_count` - Number of transactions
- `last_purchase_days_ago` - Days since last purchase
- `customer_tier` - Customer tier (if available)
- `city` - Customer city
- `age` - Customer age (if available)

### Custom Features

To add custom features, edit `loyalty/integration/xiva_feature_extractor.py`:

```python
def extract_customer_features(customer_id: str) -> Dict[str, Any]:
    # Fetch customer data from Xiva
    customer_data = client.get_customer(customer_id)
    
    # Extract features
    features = {
        'customer_id': customer_id,
        'custom_feature': customer_data.get('custom_field'),
        # Add your custom features here
    }
    
    return features
```

---

## Usage in Segmentation

Segments can use Xiva features in JSONLogic rules:

```json
{
  "and": [
    {"==": [{"var": "customer_status"}, "active"]},
    {">": [{"var": "transaction_count"}, 10]}
  ]
}
```

**Important:** Feature names in JSONLogic rules must match Xiva feature names!

---

## Troubleshooting

### Authentication Error

**Error:** `Not authenticated. Please configure XIVA_API_USERNAME and XIVA_API_PASSWORD`

**Solution:**
1. Verify credentials in `.env` file
2. Restart Django server
3. Check Xiva API URL is correct

### Rate Limiting

**Error:** `429 Too Many Requests`

**Solution:**
1. Enable Redis caching (reduces API calls)
2. Implement request throttling
3. Use DWH as primary source, Xiva as supplement

### Missing Features

**Error:** Feature not found in Xiva response

**Solution:**
1. Check Xiva API response structure
2. Update `xiva_feature_extractor.py` to extract feature
3. Verify feature name matches JSONLogic rules

---

## Best Practices

1. **Enable Caching** - Redis caching reduces Xiva API calls significantly
2. **Use Auto Mode** - Combine Xiva and DWH for best results
3. **Handle Errors** - Implement fallback to DWH if Xiva unavailable
4. **Monitor Rate Limits** - Track API usage to avoid limits
5. **Cache Aggressively** - Cache features for 1+ hours (customer data doesn't change frequently)

---

## Next Steps

- See [DWH_INTEGRATION.md](DWH_INTEGRATION.md) for DWH setup
- See [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) for system workflow
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues

