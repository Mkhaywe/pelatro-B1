"""
Create Training Data Tables from Existing DWH Data

This script creates training data tables/views from your existing DWH data
when you don't have historical labels (converted_offer_id, churned).

It uses heuristics to create labels from existing data.
"""
import os
import sys
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
import django
django.setup()

from django.conf import settings
from loyalty.integration.dwh import get_dwh_connector

print("="*70)
print("CREATE TRAINING DATA FROM DWH")
print("="*70)
print()

connector = get_dwh_connector()
table = getattr(settings, 'DWH_CUSTOMER_FEATURES_TABLE', 'customer_features_view')

print(f"📊 Checking DWH table: {table}")
print()

# Get available columns
try:
    test_query = f"SELECT * FROM {table} LIMIT 1"
    test_results = connector.execute_query(test_query, {})
    if test_results:
        available_columns = set(test_results[0].keys())
        print(f"✅ Available columns: {sorted(available_columns)}")
        print()
    else:
        print("❌ No data found in table!")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error checking table: {e}")
    sys.exit(1)

# Check if churn_score exists
has_churn_score = 'churn_score' in available_columns
has_customer_status = 'customer_status' in available_columns

print("="*70)
print("CREATING CHURN TRAINING DATA")
print("="*70)
print()

# Create churn training data
if has_churn_score:
    print("✅ Found 'churn_score' column - using it to create churn labels")
    print()
    print("Creating view: customer_churn_history")
    print()
    
    # Create view using churn_score
    # Threshold: churn_score > 0.7 = churned (1), else not churned (0)
    create_churn_view_sql = f"""
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
        CASE 
            WHEN churn_score >= 0.7 THEN 1  -- High churn score = churned
            WHEN churn_score >= 0.4 THEN 1  -- Medium churn score = churned
            ELSE 0  -- Low churn score = not churned
        END as churned,
        CURRENT_DATE as snapshot_date,
        last_updated as created_at
    FROM {table}
    WHERE churn_score IS NOT NULL;
    """
    
    print("SQL to create churn training view:")
    print("-" * 70)
    print(create_churn_view_sql)
    print("-" * 70)
    print()
    
    try:
        connector.execute_query(create_churn_view_sql, {})
        print("✅ Churn training view created successfully!")
        
        # Check how many samples
        count_query = "SELECT COUNT(*) as count FROM customer_churn_history"
        count_result = connector.execute_query(count_query, {})
        if count_result:
            print(f"✅ Training samples: {count_result[0]['count']}")
    except Exception as e:
        print(f"⚠️  Could not create view automatically: {e}")
        print("   Please run the SQL manually in your database")
        
elif has_customer_status:
    print("✅ Found 'customer_status' column - using it to create churn labels")
    print()
    print("Creating view: customer_churn_history")
    print()
    
    # Create view using customer_status
    # 'inactive', 'suspended', 'cancelled' = churned (1)
    create_churn_view_sql = f"""
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
        CASE 
            WHEN customer_status IN ('inactive', 'suspended', 'cancelled', 'churned') THEN 1
            ELSE 0
        END as churned,
        CURRENT_DATE as snapshot_date,
        last_updated as created_at
    FROM {table}
    WHERE customer_status IS NOT NULL;
    """
    
    print("SQL to create churn training view:")
    print("-" * 70)
    print(create_churn_view_sql)
    print("-" * 70)
    print()
    
    try:
        connector.execute_query(create_churn_view_sql, {})
        print("✅ Churn training view created successfully!")
        
        count_query = "SELECT COUNT(*) as count FROM customer_churn_history"
        count_result = connector.execute_query(count_query, {})
        if count_result:
            print(f"✅ Training samples: {count_result[0]['count']}")
    except Exception as e:
        print(f"⚠️  Could not create view automatically: {e}")
        print("   Please run the SQL manually in your database")
else:
    print("⚠️  No 'churn_score' or 'customer_status' column found")
    print("   Cannot automatically create churn labels")
    print()
    print("   Options:")
    print("   1. Add a 'churn_score' column to your DWH")
    print("   2. Use customer_status to identify churned customers")
    print("   3. Manually create churn labels based on business rules")

print()
print("="*70)
print("CREATING NBO TRAINING DATA")
print("="*70)
print()

# For NBO, we need offer conversion data
# Since we don't have it, we'll create a synthetic training set
# based on customer features (this is less accurate but better than nothing)

print("⚠️  No 'converted_offer_id' column found")
print("   Creating synthetic NBO training data based on customer features")
print()
print("   This will assign offers based on customer characteristics:")
print("   - High revenue customers → Premium offers (3, 4)")
print("   - Medium revenue → Standard offers (0, 1, 2)")
print("   - Low revenue / Inactive → Retention offers (5, 6, 7)")
print()

create_nbo_view_sql = f"""
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
    CASE 
        -- High value customers get premium offers
        WHEN lifetime_value > 1000 AND days_since_last_transaction < 30 THEN 
            CASE (customer_id::text)::int % 2
                WHEN 0 THEN 3
                ELSE 4
            END
        -- Medium value customers get standard offers
        WHEN lifetime_value > 200 AND days_since_last_transaction < 60 THEN
            CASE (customer_id::text)::int % 3
                WHEN 0 THEN 0
                WHEN 1 THEN 1
                ELSE 2
            END
        -- Low value / inactive get retention offers
        ELSE
            CASE (customer_id::text)::int % 3
                WHEN 0 THEN 5
                WHEN 1 THEN 6
                ELSE 7
            END
    END as converted_offer_id,
    last_updated as created_at
FROM {table}
WHERE lifetime_value IS NOT NULL;
"""

print("SQL to create NBO training view:")
print("-" * 70)
print(create_nbo_view_sql)
print("-" * 70)
print()

try:
    connector.execute_query(create_nbo_view_sql, {})
    print("✅ NBO training view created successfully!")
    
    count_query = "SELECT COUNT(*) as count FROM customer_offer_history"
    count_result = connector.execute_query(count_query, {})
    if count_result:
        print(f"✅ Training samples: {count_result[0]['count']}")
except Exception as e:
    print(f"⚠️  Could not create view automatically: {e}")
    print("   Note: The SQL uses customer_id modulo which may not work with UUIDs")
    print("   Please adjust the SQL for your customer_id format")
    print()
    print("   Alternative: Create a simpler version:")
    print(f"   CREATE VIEW customer_offer_history AS")
    print(f"   SELECT customer_id, features...,")
    print(f"          CASE WHEN lifetime_value > 1000 THEN 3")
    print(f"               WHEN lifetime_value > 200 THEN 1")
    print(f"               ELSE 7 END as converted_offer_id")
    print(f"   FROM {table};")

print()
print("="*70)
print("✅ COMPLETE!")
print("="*70)
print()
print("Next steps:")
print("1. Verify the views were created:")
print("   SELECT COUNT(*) FROM customer_churn_history;")
print("   SELECT COUNT(*) FROM customer_offer_history;")
print()
print("2. Update settings.py to use the new views:")
print("   DWH_CUSTOMER_FEATURES_TABLE = 'customer_churn_history'  # For churn training")
print("   # Or use custom queries:")
print("   DWH_CHURN_TRAINING_QUERY = 'SELECT * FROM customer_churn_history'")
print("   DWH_NBO_TRAINING_QUERY = 'SELECT * FROM customer_offer_history'")
print()
print("3. Run training:")
print("   python train_models_from_dwh.py")
print()
print("⚠️  NOTE: These are synthetic labels based on heuristics.")
print("   For best results, use real historical conversion data when available.")
print("="*70)

