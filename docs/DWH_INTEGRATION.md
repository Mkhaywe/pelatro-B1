# DWH Integration Guide

## What is DWH?

**DWH = Data Warehouse** - A separate PostgreSQL database that stores historical customer data.

### Architecture

```
Django Loyalty Project (SQLite/PostgreSQL)
    ↓
    Connects to DWH (PostgreSQL) via settings.py
    ↓
    Reads customer features from DWH
    ↓
    Uses for: Segmentation, ML Training, ML Predictions
```

**They are two separate databases!**

---

## DWH Setup

### Step 1: Create DWH Database

```sql
CREATE DATABASE DWH;
```

### Step 2: Run Setup Script

```bash
python setup_dwh_with_data.py
```

**What it does:**
1. Connects to PostgreSQL DWH database
2. Creates 4 tables:
   - `customer_features_view` - Current customer features
   - `customer_offer_history` - Historical offer conversions (for NBO training)
   - `customer_churn_history` - Historical churn snapshots (for Churn training)
   - `customer_transaction_history` - Transaction history
3. Fetches customers from Xiva API (or generates sample)
4. Populates with rich historical data

**Result:**
- ✅ Customer features table
- ✅ 2,800+ offer records
- ✅ 600 churn snapshots
- ✅ 1,700+ transactions

---

## DWH Tables Structure

### 1. `customer_features_view`

Current customer features for segmentation and ML:

```sql
CREATE TABLE customer_features_view (
    customer_id UUID PRIMARY KEY,
    total_revenue DECIMAL(12,2),
    transaction_count INTEGER,
    last_purchase_days_ago INTEGER,
    avg_transaction_value DECIMAL(10,2),
    lifetime_value DECIMAL(12,2),
    churn_score DECIMAL(5,4),
    customer_tier VARCHAR(50),
    city VARCHAR(100),
    age INTEGER,
    -- Add your custom columns here
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2. `customer_offer_history`

Historical offer conversions for NBO training:

```sql
CREATE TABLE customer_offer_history (
    id SERIAL PRIMARY KEY,
    customer_id UUID NOT NULL,
    offer_id INTEGER NOT NULL,
    converted BOOLEAN DEFAULT FALSE,
    converted_offer_id INTEGER,
    -- Customer features at time of offer
    total_revenue DECIMAL(12,2),
    transaction_count INTEGER,
    -- ... other features
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3. `customer_churn_history`

Historical churn snapshots for Churn training:

```sql
CREATE TABLE customer_churn_history (
    id SERIAL PRIMARY KEY,
    customer_id UUID NOT NULL,
    churned BOOLEAN DEFAULT FALSE,
    churn_date DATE,
    -- Customer features at snapshot time
    total_revenue DECIMAL(12,2),
    transaction_count INTEGER,
    -- ... other features
    snapshot_date DATE DEFAULT CURRENT_DATE
);
```

### 4. `customer_transaction_history`

Transaction history:

```sql
CREATE TABLE customer_transaction_history (
    id SERIAL PRIMARY KEY,
    customer_id UUID NOT NULL,
    transaction_date TIMESTAMP,
    transaction_amount DECIMAL(10,2),
    transaction_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Configuration

### Django Settings

In `loyalty_project/settings.py`:

```python
# DWH Configuration
DWH_TYPE = 'postgresql'  # or 'oracle', 'snowflake'
DWH_POSTGRES_CONNECTION_STRING = 'postgresql://user:password@localhost:5432/DWH'
DWH_CUSTOMER_FEATURES_TABLE = 'public.customer_features_view'

# Feature Store Configuration
FEATURE_STORE_DATA_SOURCE = 'auto'  # 'dwh', 'xiva', or 'auto'
FEATURE_STORE_MERGE_STRATEGY = 'xiva_first'  # 'xiva_first', 'dwh_first', or 'merge'

# Redis Caching (optional but recommended)
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_FEATURE_STORE_DB = 1
```

---

## How Django Connects to DWH

### Connection Flow

```
Django Request
    ↓
FeatureStore.get_customer_features(customer_id)
    ↓
Check Redis Cache (if enabled)
    ↓ (cache miss)
DWHConnector.get_customer_features(customer_id)
    ↓
Execute SQL Query
    ↓
Return Features
    ↓
Cache in Redis (if enabled)
    ↓
Return to Django
```

### Usage in Code

```python
from loyalty.integration.feature_store import FeatureStore

# Get customer features
features = FeatureStore.get_customer_features(
    customer_id='123e4567-e89b-12d3-a456-426614174000',
    use_cache=True,
    data_source='dwh'  # or 'xiva', 'auto'
)

# Features dict contains:
# {
#     'customer_id': '...',
#     'total_revenue': 5000.00,
#     'transaction_count': 25,
#     'last_purchase_days_ago': 5,
#     ...
# }
```

---

## Feature Mapping

### ML Feature Mapping

Map your DWH columns to ML model input features:

```python
# settings.py
ML_FEATURE_MAPPING = {
    'revenue': 'total_revenue',
    'transaction_count': 'transaction_count',
    'days_since_last': 'last_purchase_days_ago',
    'avg_transaction_value': 'avg_transaction_value',
    'lifetime_value': 'lifetime_value',
}

ML_MODEL_INPUT_SIZE = 5  # Number of features
```

### Segmentation Feature Mapping

Segments use DWH column names directly in JSONLogic rules:

```json
{
  "and": [
    {">": [{"var": "total_revenue"}, 1000]},
    {"<": [{"var": "last_purchase_days_ago"}, 30]}
  ]
}
```

**Important:** Column names in JSONLogic rules must match DWH column names!

---

## Custom DWH Schema

### Option 1: Custom SQL Query

```python
# settings.py
DWH_CUSTOMER_FEATURES_QUERY = """
    SELECT 
        customer_id,
        your_revenue_column,
        your_transaction_count_column,
        your_last_transaction_date_column,
        -- Add your actual DWH columns here
    FROM your_actual_table_or_view
    WHERE customer_id = :customer_id
"""
```

### Option 2: Table/View Name

```python
# settings.py
DWH_CUSTOMER_FEATURES_TABLE = "your_schema.your_customer_features_view"
```

The connector will execute: `SELECT * FROM {table_name} WHERE customer_id = :customer_id`

---

## Data Source Selection

### Auto Mode (Recommended)

```python
FEATURE_STORE_DATA_SOURCE = 'auto'
FEATURE_STORE_MERGE_STRATEGY = 'xiva_first'
```

**Behavior:**
- Tries Xiva first (real-time data)
- Falls back to DWH (historical data)
- Merges both if available (Xiva takes precedence)

### DWH Only

```python
FEATURE_STORE_DATA_SOURCE = 'dwh'
```

**Use when:** You only have DWH, no Xiva integration

### Xiva Only

```python
FEATURE_STORE_DATA_SOURCE = 'xiva'
```

**Use when:** You only have Xiva, no DWH

---

## Troubleshooting

### Connection Issues

**Error:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
1. Verify PostgreSQL is running
2. Check connection string in settings
3. Verify database exists
4. Check firewall/network access

### Missing Columns

**Error:** `column "column_name" does not exist`

**Solution:**
1. Verify column names match DWH schema
2. Update `ML_FEATURE_MAPPING` if needed
3. Update JSONLogic rules to use correct column names

### Empty Results

**Error:** No features returned

**Solution:**
1. Verify customer_id exists in DWH
2. Check SQL query syntax
3. Verify table/view exists
4. Check permissions

---

## Best Practices

1. **Use Views** - Create views in DWH for easier querying
2. **Index customer_id** - Ensure customer_id is indexed for performance
3. **Enable Redis Caching** - Reduces DWH load significantly
4. **Regular Updates** - Keep DWH data fresh (daily/hourly sync)
5. **Column Naming** - Use consistent naming across DWH and Django

---

## Next Steps

- See [ML_GUIDE.md](ML_GUIDE.md) for ML training using DWH data
- See [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) for system workflow
- See [XIVA_INTEGRATION.md](XIVA_INTEGRATION.md) for Xiva integration

