"""
Setup DWH Database with Tables and Historical Data

This script:
1. Connects to PostgreSQL DWH
2. Creates required tables for ML/AI
3. Fetches customers from Xiva
4. Generates rich historical data
5. Populates DWH with training data

Requirements:
- psycopg2-binary
- pandas
- numpy

DWH Details:
- Host: localhost
- Database: DWH
- Password: root123
- User: postgres (default, adjust if needed)
"""

import os
import sys
from datetime import datetime, timedelta
import random
import json

# Check dependencies
try:
    import psycopg2
    from psycopg2.extras import execute_values
    import pandas as pd
    import numpy as np
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    print("Install with: pip install psycopg2-binary pandas numpy")
    sys.exit(1)

# Setup Django to access Xiva client
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loyalty_project.settings')
import django
django.setup()

from loyalty.integration.xiva_client import get_xiva_client, XivaAPIError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DWH Connection Details
# Update these if your PostgreSQL setup is different
DWH_CONFIG = {
    'host': 'localhost',
    'database': 'DWH',
    'user': 'postgres',  # Adjust if different
    'password': 'root123',
    'port': 5432
}

# Number of customers to process (adjust based on your needs)
NUM_CUSTOMERS = 200  # Increase for more training data

print("="*70)
print("DWH SETUP WITH HISTORICAL DATA")
print("="*70)
print()


# ============================================================================
# STEP 1: CONNECT TO DWH
# ============================================================================

def connect_dwh():
    """Connect to PostgreSQL DWH"""
    try:
        conn = psycopg2.connect(**DWH_CONFIG)
        print("[OK] Connected to DWH database")
        return conn
    except Exception as e:
        print(f"[ERROR] Error connecting to DWH: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running")
        print("  2. Database 'DWH' exists")
        print("  3. Credentials are correct")
        sys.exit(1)


# ============================================================================
# STEP 2: CREATE TABLES
# ============================================================================

def create_tables(conn):
    """Create all required tables for ML/AI"""
    print("\n[INFO] Creating DWH tables...")
    
    cursor = conn.cursor()
    
    # 1. Customer Features Table (main table for feature extraction)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_features_view (
            customer_id VARCHAR(255) PRIMARY KEY,
            total_revenue DECIMAL(15, 2) DEFAULT 0,
            transaction_count INTEGER DEFAULT 0,
            days_since_last_transaction INTEGER DEFAULT 0,
            avg_transaction_value DECIMAL(15, 2) DEFAULT 0,
            lifetime_value DECIMAL(15, 2) DEFAULT 0,
            churn_score DECIMAL(5, 4) DEFAULT 0,
            customer_status VARCHAR(50) DEFAULT 'active',
            active_products_count INTEGER DEFAULT 0,
            data_usage_mb DECIMAL(15, 2) DEFAULT 0,
            credit_utilization DECIMAL(5, 4) DEFAULT 0,
            account_age_days INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("   [OK] Created customer_features_view")
    
    # 2. Offer History Table (for NBO training)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_offer_history (
            id SERIAL PRIMARY KEY,
            customer_id VARCHAR(255) NOT NULL,
            offer_id INTEGER NOT NULL,
            offer_name VARCHAR(255),
            offer_type VARCHAR(50),
            sent_at TIMESTAMP NOT NULL,
            opened_at TIMESTAMP,
            clicked_at TIMESTAMP,
            converted_at TIMESTAMP,
            converted_offer_id INTEGER,
            points_earned DECIMAL(10, 2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customer_features_view(customer_id)
        );
    """)
    print("   [OK] Created customer_offer_history")
    
    # 3. Churn History Table (for Churn training)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_churn_history (
            id SERIAL PRIMARY KEY,
            customer_id VARCHAR(255) NOT NULL,
            snapshot_date DATE NOT NULL,
            total_revenue DECIMAL(15, 2) DEFAULT 0,
            transaction_count INTEGER DEFAULT 0,
            days_since_last_transaction INTEGER DEFAULT 0,
            avg_transaction_value DECIMAL(15, 2) DEFAULT 0,
            lifetime_value DECIMAL(15, 2) DEFAULT 0,
            churn_score DECIMAL(5, 4) DEFAULT 0,
            churned INTEGER DEFAULT 0,  -- 0 = not churned, 1 = churned
            churned_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customer_features_view(customer_id)
        );
    """)
    print("   [OK] Created customer_churn_history")
    
    # 4. Transaction History Table (for additional features)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_transaction_history (
            id SERIAL PRIMARY KEY,
            customer_id VARCHAR(255) NOT NULL,
            transaction_date DATE NOT NULL,
            transaction_type VARCHAR(50),
            transaction_amount DECIMAL(15, 2) DEFAULT 0,
            points_earned DECIMAL(10, 2) DEFAULT 0,
            points_redeemed DECIMAL(10, 2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customer_features_view(customer_id)
        );
    """)
    print("   [OK] Created customer_transaction_history")
    
    # Create indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_offer_history_customer 
        ON customer_offer_history(customer_id, sent_at);
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_churn_history_customer 
        ON customer_churn_history(customer_id, snapshot_date);
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transaction_history_customer 
        ON customer_transaction_history(customer_id, transaction_date);
    """)
    
    print("   [OK] Created indexes")
    
    conn.commit()
    cursor.close()
    print("\n[OK] All tables created successfully!")


# ============================================================================
# STEP 3: FETCH CUSTOMERS FROM XIVA
# ============================================================================

def fetch_xiva_customers(limit=500):
    """Fetch customers from Xiva API"""
    print(f"\n[INFO] Fetching customers from Xiva (limit: {limit})...")
    
    try:
        client = get_xiva_client()
        customers = client.get_customer_list(limit=limit)
        
        if not customers:
            print("[WARNING] No customers found in Xiva")
            print("   Using sample customer IDs for testing...")
            # Generate sample customer IDs
            return [f"customer_{i:06d}" for i in range(1, min(limit, 200) + 1)]
        
        customer_ids = [str(c.get('id', c.get('customer_id', ''))) for c in customers if c.get('id') or c.get('customer_id')]
        print(f"   [OK] Fetched {len(customer_ids)} customers from Xiva")
        return customer_ids[:limit]
        
    except XivaAPIError as e:
        print(f"[WARNING] Xiva API Error: {e}")
        print("   Using sample customer IDs for testing...")
        return [f"customer_{i:06d}" for i in range(1, min(limit, 200) + 1)]
    except Exception as e:
        print(f"[WARNING] Error fetching from Xiva: {e}")
        print("   Using sample customer IDs for testing...")
        return [f"customer_{i:06d}" for i in range(1, min(limit, 200) + 1)]


# ============================================================================
# STEP 4: GENERATE RICH HISTORICAL DATA
# ============================================================================

def generate_customer_features(customer_id, base_revenue=None):
    """Generate realistic customer features"""
    # Create customer segments for variety
    segment_type = random.choice(['high_value', 'medium_value', 'low_value', 'churn_risk', 'new'])
    
    if segment_type == 'high_value':
        total_revenue = base_revenue or random.uniform(5000, 20000)
        transaction_count = random.randint(50, 200)
        days_since_last = random.randint(1, 7)
        avg_transaction = total_revenue / max(transaction_count, 1)
        ltv = total_revenue * random.uniform(1.5, 3.0)
        churn_score = random.uniform(0.0, 0.2)  # Low churn risk
        status = 'active'
        products = random.randint(2, 5)
        data_usage = random.uniform(10000, 50000)
        credit_util = random.uniform(0.3, 0.6)
        account_age = random.randint(365, 2000)
        
    elif segment_type == 'medium_value':
        total_revenue = base_revenue or random.uniform(1000, 5000)
        transaction_count = random.randint(20, 50)
        days_since_last = random.randint(7, 30)
        avg_transaction = total_revenue / max(transaction_count, 1)
        ltv = total_revenue * random.uniform(1.2, 2.0)
        churn_score = random.uniform(0.2, 0.5)
        status = 'active'
        products = random.randint(1, 3)
        data_usage = random.uniform(5000, 15000)
        credit_util = random.uniform(0.4, 0.7)
        account_age = random.randint(180, 1000)
        
    elif segment_type == 'low_value':
        total_revenue = base_revenue or random.uniform(100, 1000)
        transaction_count = random.randint(5, 20)
        days_since_last = random.randint(30, 90)
        avg_transaction = total_revenue / max(transaction_count, 1)
        ltv = total_revenue * random.uniform(1.0, 1.5)
        churn_score = random.uniform(0.4, 0.7)
        status = random.choice(['active', 'inactive'])
        products = random.randint(1, 2)
        data_usage = random.uniform(1000, 5000)
        credit_util = random.uniform(0.5, 0.9)
        account_age = random.randint(30, 365)
        
    elif segment_type == 'churn_risk':
        total_revenue = base_revenue or random.uniform(500, 3000)
        transaction_count = random.randint(10, 30)
        days_since_last = random.randint(60, 180)
        avg_transaction = total_revenue / max(transaction_count, 1)
        ltv = total_revenue * random.uniform(0.8, 1.2)
        churn_score = random.uniform(0.7, 0.95)  # High churn risk
        status = random.choice(['active', 'inactive', 'suspended'])
        products = random.randint(1, 2)
        data_usage = random.uniform(500, 3000)
        credit_util = random.uniform(0.7, 1.0)
        account_age = random.randint(90, 730)
        
    else:  # new
        total_revenue = base_revenue or random.uniform(50, 500)
        transaction_count = random.randint(1, 10)
        days_since_last = random.randint(1, 30)
        avg_transaction = total_revenue / max(transaction_count, 1)
        ltv = total_revenue * random.uniform(1.0, 2.0)
        churn_score = random.uniform(0.3, 0.6)
        status = 'active'
        products = 1
        data_usage = random.uniform(100, 2000)
        credit_util = random.uniform(0.2, 0.5)
        account_age = random.randint(1, 90)
    
    return {
        'customer_id': customer_id,
        'total_revenue': round(total_revenue, 2),
        'transaction_count': transaction_count,
        'days_since_last_transaction': days_since_last,
        'avg_transaction_value': round(avg_transaction, 2),
        'lifetime_value': round(ltv, 2),
        'churn_score': round(churn_score, 4),
        'customer_status': status,
        'active_products_count': products,
        'data_usage_mb': round(data_usage, 2),
        'credit_utilization': round(credit_util, 4),
        'account_age_days': account_age,
        'last_updated': datetime.now()
    }


def generate_offer_history(customer_id, features, num_offers=50):
    """Generate offer history for NBO training"""
    offers = []
    offer_types = ['points_bonus', 'discount', 'free_data', 'upgrade', 'referral', 'birthday', 'anniversary', 'winback']
    offer_names = [
        'Double Points Weekend', '20% Off Next Purchase', 'Free 5GB Data',
        'Upgrade to Premium', 'Refer a Friend', 'Birthday Bonus',
        'Anniversary Reward', 'Come Back Offer'
    ]
    
    # Base conversion rate on customer value
    base_conversion_rate = 0.3 if features['total_revenue'] > 5000 else 0.15
    
    start_date = datetime.now() - timedelta(days=180)
    
    for i in range(num_offers):
        offer_id = random.randint(1, 8)
        sent_at = start_date + timedelta(days=random.randint(0, 180))
        
        # Conversion logic based on customer features
        will_convert = random.random() < base_conversion_rate
        
        opened_at = None
        clicked_at = None
        converted_at = None
        converted_offer_id = None
        points_earned = 0
        
        if will_convert:
            opened_at = sent_at + timedelta(hours=random.randint(1, 48))
            clicked_at = opened_at + timedelta(minutes=random.randint(5, 120))
            converted_at = clicked_at + timedelta(hours=random.randint(1, 72))
            converted_offer_id = offer_id
            points_earned = random.uniform(100, 1000) if offer_id <= 4 else random.uniform(50, 500)
        
        offers.append({
            'customer_id': customer_id,
            'offer_id': offer_id,
            'offer_name': offer_names[offer_id - 1],
            'offer_type': offer_types[offer_id - 1],
            'sent_at': sent_at,
            'opened_at': opened_at,
            'clicked_at': clicked_at,
            'converted_at': converted_at,
            'converted_offer_id': converted_offer_id,
            'points_earned': round(points_earned, 2)
        })
    
    return offers


def generate_churn_history(customer_id, features, num_snapshots=12):
    """Generate churn history for Churn training"""
    snapshots = []
    
    # Determine if customer will churn
    will_churn = features['churn_score'] > 0.7 or random.random() < 0.15
    churn_date = None
    if will_churn:
        churn_date = datetime.now() - timedelta(days=random.randint(1, 90))
    
    start_date = datetime.now() - timedelta(days=180)
    
    for i in range(num_snapshots):
        snapshot_date = start_date + timedelta(days=i * 15)
        
        # Features degrade if churning
        if will_churn and snapshot_date >= churn_date - timedelta(days=30):
            revenue_multiplier = 0.5
            txn_multiplier = 0.3
            days_since_last = random.randint(60, 180)
        else:
            revenue_multiplier = 1.0
            txn_multiplier = 1.0
            days_since_last = random.randint(1, 30)
        
        churned = 1 if (will_churn and snapshot_date >= churn_date) else 0
        
        snapshots.append({
            'customer_id': customer_id,
            'snapshot_date': snapshot_date.date(),
            'total_revenue': round(features['total_revenue'] * revenue_multiplier, 2),
            'transaction_count': int(features['transaction_count'] * txn_multiplier),
            'days_since_last_transaction': days_since_last,
            'avg_transaction_value': round(features['avg_transaction_value'] * revenue_multiplier, 2),
            'lifetime_value': round(features['lifetime_value'] * revenue_multiplier, 2),
            'churn_score': features['churn_score'] + (0.1 if will_churn else -0.05),
            'churned': churned,
            'churned_date': churn_date.date() if churn_date else None
        })
    
    return snapshots


def generate_transaction_history(customer_id, features, num_transactions=30):
    """Generate transaction history"""
    transactions = []
    transaction_types = ['purchase', 'recharge', 'subscription', 'redemption']
    
    start_date = datetime.now() - timedelta(days=180)
    
    for i in range(num_transactions):
        txn_date = start_date + timedelta(days=random.randint(0, 180))
        txn_type = random.choice(transaction_types)
        
        if txn_type == 'redemption':
            amount = random.uniform(10, 100)
            points_earned = 0
            points_redeemed = random.uniform(50, 500)
        else:
            amount = random.uniform(20, 500)
            points_earned = amount * random.uniform(0.01, 0.05)
            points_redeemed = 0
        
        transactions.append({
            'customer_id': customer_id,
            'transaction_date': txn_date.date(),
            'transaction_type': txn_type,
            'transaction_amount': round(amount, 2),
            'points_earned': round(points_earned, 2),
            'points_redeemed': round(points_redeemed, 2)
        })
    
    return transactions


# ============================================================================
# STEP 5: POPULATE DWH
# ============================================================================

def populate_dwh(conn, customer_ids):
    """Populate DWH with historical data"""
    print(f"\n[INFO] Populating DWH with data for {len(customer_ids)} customers...")
    
    cursor = conn.cursor()
    
    # Clear existing data
    print("   Clearing existing data...")
    cursor.execute("TRUNCATE TABLE customer_transaction_history CASCADE;")
    cursor.execute("TRUNCATE TABLE customer_offer_history CASCADE;")
    cursor.execute("TRUNCATE TABLE customer_churn_history CASCADE;")
    cursor.execute("TRUNCATE TABLE customer_features_view CASCADE;")
    conn.commit()
    print("   [OK] Cleared existing data")
    
    # Insert customer features
    print("   Generating customer features...")
    features_data = []
    for customer_id in customer_ids:
        features = generate_customer_features(customer_id)
        features_data.append(features)
    
    features_df = pd.DataFrame(features_data)
    print(f"   [OK] Generated features for {len(features_data)} customers")
    
    # Insert features
    print("   Inserting customer features...")
    for _, row in features_df.iterrows():
        cursor.execute("""
            INSERT INTO customer_features_view (
                customer_id, total_revenue, transaction_count, days_since_last_transaction,
                avg_transaction_value, lifetime_value, churn_score, customer_status,
                active_products_count, data_usage_mb, credit_utilization, account_age_days, last_updated
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO UPDATE SET
                total_revenue = EXCLUDED.total_revenue,
                transaction_count = EXCLUDED.transaction_count,
                days_since_last_transaction = EXCLUDED.days_since_last_transaction,
                avg_transaction_value = EXCLUDED.avg_transaction_value,
                lifetime_value = EXCLUDED.lifetime_value,
                churn_score = EXCLUDED.churn_score,
                customer_status = EXCLUDED.customer_status,
                active_products_count = EXCLUDED.active_products_count,
                data_usage_mb = EXCLUDED.data_usage_mb,
                credit_utilization = EXCLUDED.credit_utilization,
                account_age_days = EXCLUDED.account_age_days,
                last_updated = EXCLUDED.last_updated
        """, (
            row['customer_id'], row['total_revenue'], row['transaction_count'],
            row['days_since_last_transaction'], row['avg_transaction_value'],
            row['lifetime_value'], row['churn_score'], row['customer_status'],
            row['active_products_count'], row['data_usage_mb'],
            row['credit_utilization'], row['account_age_days'], row['last_updated']
        ))
    
    conn.commit()
    print(f"   [OK] Inserted {len(features_data)} customer features")
    
    # Insert offer history
    print("   Generating offer history...")
    offer_data = []
    for customer_id in customer_ids:
        features = features_df[features_df['customer_id'] == customer_id].iloc[0].to_dict()
        offers = generate_offer_history(customer_id, features, num_offers=random.randint(30, 80))
        offer_data.extend(offers)
    
    print(f"   [OK] Generated {len(offer_data)} offer records")
    
    if offer_data:
        print("   Inserting offer history...")
        offer_df = pd.DataFrame(offer_data)
        # Replace NaT with None for timestamp columns
        for col in ['opened_at', 'clicked_at', 'converted_at']:
            offer_df[col] = offer_df[col].replace({pd.NaT: None})
        
        execute_values(
            cursor,
            """
            INSERT INTO customer_offer_history (
                customer_id, offer_id, offer_name, offer_type, sent_at,
                opened_at, clicked_at, converted_at, converted_offer_id, points_earned
            ) VALUES %s
            """,
            [(row['customer_id'], row['offer_id'], row['offer_name'], row['offer_type'],
              row['sent_at'], 
              None if pd.isna(row['opened_at']) else row['opened_at'],
              None if pd.isna(row['clicked_at']) else row['clicked_at'],
              None if pd.isna(row['converted_at']) else row['converted_at'],
              None if pd.isna(row['converted_offer_id']) else int(row['converted_offer_id']),
              row['points_earned']) for _, row in offer_df.iterrows()],
            page_size=1000
        )
        conn.commit()
        print(f"   [OK] Inserted {len(offer_data)} offer records")
    
    # Insert churn history
    print("   Generating churn history...")
    churn_data = []
    for customer_id in customer_ids:
        features = features_df[features_df['customer_id'] == customer_id].iloc[0].to_dict()
        snapshots = generate_churn_history(customer_id, features, num_snapshots=12)
        churn_data.extend(snapshots)
    
    print(f"   [OK] Generated {len(churn_data)} churn snapshots")
    
    if churn_data:
        print("   Inserting churn history...")
        churn_df = pd.DataFrame(churn_data)
        execute_values(
            cursor,
            """
            INSERT INTO customer_churn_history (
                customer_id, snapshot_date, total_revenue, transaction_count,
                days_since_last_transaction, avg_transaction_value, lifetime_value,
                churn_score, churned, churned_date
            ) VALUES %s
            """,
            [(row['customer_id'], row['snapshot_date'], row['total_revenue'],
              row['transaction_count'], row['days_since_last_transaction'],
              row['avg_transaction_value'], row['lifetime_value'], row['churn_score'],
              row['churned'], 
              None if pd.isna(row['churned_date']) else row['churned_date']) 
             for _, row in churn_df.iterrows()],
            page_size=1000
        )
        conn.commit()
        print(f"   [OK] Inserted {len(churn_data)} churn snapshots")
    
    # Insert transaction history
    print("   Generating transaction history...")
    transaction_data = []
    for customer_id in customer_ids:
        features = features_df[features_df['customer_id'] == customer_id].iloc[0].to_dict()
        transactions = generate_transaction_history(customer_id, features, num_transactions=random.randint(20, 50))
        transaction_data.extend(transactions)
    
    print(f"   [OK] Generated {len(transaction_data)} transactions")
    
    if transaction_data:
        print("   Inserting transaction history...")
        txn_df = pd.DataFrame(transaction_data)
        execute_values(
            cursor,
            """
            INSERT INTO customer_transaction_history (
                customer_id, transaction_date, transaction_type,
                transaction_amount, points_earned, points_redeemed
            ) VALUES %s
            """,
            [(row['customer_id'], row['transaction_date'], row['transaction_type'],
              row['transaction_amount'], row['points_earned'], row['points_redeemed'])
             for _, row in txn_df.iterrows()],
            page_size=1000
        )
        conn.commit()
        print(f"   [OK] Inserted {len(transaction_data)} transactions")
    
    cursor.close()
    
    # Print summary
    print("\n" + "="*70)
    print("[OK] DWH POPULATION COMPLETE!")
    print("="*70)
    print(f"\n[INFO] Summary:")
    print(f"   - Customers: {len(customer_ids)}")
    print(f"   - Offer records: {len(offer_data)}")
    print(f"   - Churn snapshots: {len(churn_data)}")
    print(f"   - Transactions: {len(transaction_data)}")
    print(f"\n[INFO] Ready for ML training!")
    print("   Run: python train_models_from_dwh.py")
    print("="*70)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    print("Starting DWH setup...")
    print()
    
    # Step 1: Connect
    conn = connect_dwh()
    
    # Step 2: Create tables
    create_tables(conn)
    
    # Step 3: Fetch customers
    customer_ids = fetch_xiva_customers(limit=NUM_CUSTOMERS)
    
    # Step 4 & 5: Generate and populate data
    populate_dwh(conn, customer_ids)
    
    # Close connection
    conn.close()
    print("\n[OK] Done! DWH is ready for ML training.")

