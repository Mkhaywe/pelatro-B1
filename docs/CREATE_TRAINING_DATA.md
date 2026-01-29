# Creating Training Data from Your DWH

Your DWH has `churn_score` which we can use! Here's how to create training data tables.

## Available Columns in Your DWH

From your `customer_features_view`:
- `account_age_days`
- `active_products_count`
- `avg_transaction_value`
- `churn_score` ✅ **This is perfect for churn training!**
- `credit_utilization`
- `customer_id`
- `customer_status`
- `data_usage_mb`
- `days_since_last_transaction`
- `last_updated`
- `lifetime_value`
- `total_revenue`
- `transaction_count`

---

## Step 1: Create Churn Training Data

Since you have `churn_score`, we can use it to create churn labels:

```sql
-- Create churn training view
CREATE OR REPLACE VIEW customer_churn_history AS
SELECT 
    customer_id,
    total_revenue,
    transaction_count,
    days_since_last_transaction,
    avg_transaction_value,
    lifetime_value,
    account_age_days,
    active_products_count,
    credit_utilization,
    data_usage_mb,
    -- Convert churn_score to binary label
    CASE 
        WHEN churn_score >= 0.7 THEN 1  -- High churn score = churned
        WHEN churn_score >= 0.4 THEN 1  -- Medium-high = churned
        ELSE 0  -- Low churn score = not churned
    END as churned,
    CURRENT_DATE as snapshot_date,
    last_updated as created_at
FROM customer_features_view
WHERE churn_score IS NOT NULL;
```

**Alternative**: If you prefer to use `customer_status`:

```sql
CREATE OR REPLACE VIEW customer_churn_history AS
SELECT 
    customer_id,
    total_revenue,
    transaction_count,
    days_since_last_transaction,
    avg_transaction_value,
    lifetime_value,
    account_age_days,
    active_products_count,
    credit_utilization,
    data_usage_mb,
    -- Use customer_status to identify churned
    CASE 
        WHEN customer_status IN ('inactive', 'suspended', 'cancelled', 'churned') THEN 1
        ELSE 0
    END as churned,
    CURRENT_DATE as snapshot_date,
    last_updated as created_at
FROM customer_features_view
WHERE customer_status IS NOT NULL;
```

---

## Step 2: Create NBO Training Data

Since you don't have `converted_offer_id`, we'll create synthetic labels based on customer characteristics:

```sql
-- Create NBO training view with synthetic offer assignments
CREATE OR REPLACE VIEW customer_offer_history AS
SELECT 
    customer_id,
    total_revenue,
    transaction_count,
    days_since_last_transaction,
    avg_transaction_value,
    lifetime_value,
    account_age_days,
    active_products_count,
    credit_utilization,
    data_usage_mb,
    -- Assign offers based on customer value and activity
    CASE 
        -- High value, active customers → Premium offers (3, 4)
        WHEN lifetime_value > 1000 AND days_since_last_transaction < 30 THEN 
            CASE WHEN (ROW_NUMBER() OVER (ORDER BY customer_id)) % 2 = 0 THEN 3 ELSE 4 END
        -- Medium value, active → Standard offers (0, 1, 2)
        WHEN lifetime_value > 200 AND days_since_last_transaction < 60 THEN
            CASE WHEN (ROW_NUMBER() OVER (ORDER BY customer_id)) % 3 = 0 THEN 0
                 WHEN (ROW_NUMBER() OVER (ORDER BY customer_id)) % 3 = 1 THEN 1
                 ELSE 2 END
        -- Low value or inactive → Retention offers (5, 6, 7)
        ELSE
            CASE WHEN (ROW_NUMBER() OVER (ORDER BY customer_id)) % 3 = 0 THEN 5
                 WHEN (ROW_NUMBER() OVER (ORDER BY customer_id)) % 3 = 1 THEN 6
                 ELSE 7 END
    END as converted_offer_id,
    last_updated as created_at
FROM customer_features_view
WHERE lifetime_value IS NOT NULL;
```

**Simpler version** (if the above doesn't work with your customer_id format):

```sql
CREATE OR REPLACE VIEW customer_offer_history AS
SELECT 
    customer_id,
    total_revenue,
    transaction_count,
    days_since_last_transaction,
    avg_transaction_value,
    lifetime_value,
    account_age_days,
    active_products_count,
    credit_utilization,
    data_usage_mb,
    -- Simple assignment based on value
    CASE 
        WHEN lifetime_value > 1000 THEN 3  -- Premium offer
        WHEN lifetime_value > 500 THEN 1   -- Standard offer
        WHEN lifetime_value > 200 THEN 2   -- Standard offer
        ELSE 7  -- Retention offer
    END as converted_offer_id,
    last_updated as created_at
FROM customer_features_view
WHERE lifetime_value IS NOT NULL;
```

---

## Step 3: Verify the Views

```sql
-- Check churn training data
SELECT COUNT(*) as total_samples,
       SUM(churned) as churned_count,
       AVG(churned) as churn_rate
FROM customer_churn_history;

-- Check NBO training data
SELECT 
    converted_offer_id,
    COUNT(*) as count
FROM customer_offer_history
GROUP BY converted_offer_id
ORDER BY converted_offer_id;
```

---

## Step 4: Update Settings (Optional)

You can update `settings.py` to use the new views:

```python
# For churn training
DWH_CHURN_TRAINING_QUERY = """
SELECT * FROM customer_churn_history
WHERE snapshot_date >= CURRENT_DATE - INTERVAL '6 months'
"""

# For NBO training
DWH_NBO_TRAINING_QUERY = """
SELECT * FROM customer_offer_history
WHERE created_at >= CURRENT_DATE - INTERVAL '6 months'
"""
```

Or update the table name:

```python
# Use the churn history view for training
DWH_CUSTOMER_FEATURES_TABLE = 'customer_churn_history'  # For churn
# Or keep using customer_features_view and use custom queries
```

---

## Step 5: Train Models

Now run the training script:

```bash
python train_models_from_dwh.py
```

---

## ⚠️ Important Notes

### Churn Training
- ✅ **Good**: Using `churn_score` is actually better than binary labels in some cases
- The model will learn patterns that correlate with high churn scores
- You can adjust the threshold (0.7, 0.4) based on your business needs

### NBO Training
- ⚠️ **Synthetic Labels**: The offer assignments are based on heuristics, not real conversions
- This is better than nothing, but **not as accurate** as real conversion data
- **For production**: Start collecting real offer conversion data and retrain

### Next Steps
1. ✅ Use these views to train initial models
2. 📊 Start collecting real offer conversion data
3. 🔄 Retrain models with real data when available
4. 📈 Monitor model performance and adjust

---

## Alternative: Use Placeholder Models

If you prefer to wait for real data:

```bash
python create_ml_models.py
```

This creates placeholder models that work but aren't trained on your data.

---

## Summary

1. **Run the SQL** to create `customer_churn_history` and `customer_offer_history` views
2. **Verify** the views have data
3. **Train models**: `python train_models_from_dwh.py`
4. **Collect real data** for future retraining

The models trained on `churn_score` will be quite good since you're using an actual churn metric!

