# System Workflow Guide

## Overview

This guide explains the complete system workflow and the recommended order of operations for setting up and using the loyalty platform.

## System Flow Diagram

```
1. Xiva Customers (Source Data)
   ↓
2. DWH Setup (Historical Data for ML)
   ↓
3. Segments (Dynamic segments need DWH/Xiva)
   ↓
4. Programs with Tiers (Foundation)
   ↓
5. Campaigns (Target segments)
   ↓
6. Campaign Executions (Created when triggered)
   ↓
7. ML Training (Uses DWH data)
```

## Recommended Setup Order

### 1. Fetch Xiva Customers ✅

**What it does:**
- Connects to Xiva API
- Fetches customer list
- Used for creating loyalty accounts

**When to run:**
- First time setup
- When you need fresh customer data

**Script:** Integrated in `create_full_demo.py`

---

### 2. Setup DWH with Historical Data ✅

**What it does:**
- Creates PostgreSQL tables in DWH database
- Populates with historical customer data
- Generates offer history, churn snapshots, transactions

**When to run:**
- Before ML training
- When you need training data

**Script:** `python setup_dwh_with_data.py`

**Result:**
- ✅ Customer features table
- ✅ Offer history (for NBO training)
- ✅ Churn history (for Churn training)
- ✅ Transaction history

---

### 3. Create Segments

**When to create:**
- **Anytime**, but:
  - **Static segments**: Created manually, members added manually
  - **Dynamic segments**: Need DWH/Xiva data to calculate members

**How to create:**
1. Go to **Segments** → **Create Segment**
2. Enter name, description
3. Choose:
   - **Static**: Manual member management
   - **Dynamic**: Uses DWH/Xiva features, recalculates automatically
4. Use **Visual Rule Builder** to define JSONLogic rules
5. Click **Recalculate** to populate members

**Best Practice:**
- Create segments **after DWH setup** if using dynamic segments
- Segments use DWH features for rule evaluation

---

### 4. Create Programs with Tiers

**When to create:**
- **Anytime** - Programs are independent
- Usually created first as foundation

**How to create:**
1. Go to **Programs** → **Create Program**
2. Fill in program details
3. In **Tier Management** section:
   - Click **+ Add Tier**
   - Configure: Name, Min Points, Benefits
   - Add multiple tiers (Bronze, Silver, Gold, Platinum)
4. Configure **Earn Rules** and **Burn Rules** (JSONLogic)
5. Configure **Points Expiry Rules**
6. Configure **Earn Caps**
7. Save program

**Note:** Tiers are saved with the program. If you don't see tiers:
- Check ProgramBuilder is loading tiers correctly
- Verify tiers were saved to database

---

### 5. Create Campaigns

**When to create:**
- After segments exist (campaigns target segments)
- After programs exist (campaigns belong to programs)

**How to create:**
1. Go to **Campaigns** → **Create Campaign**
2. Select program and segment
3. Configure triggers (event, schedule, or threshold)
4. Set status to **Active**
5. Save campaign

**Note:** Campaigns are **not executed automatically**. They need to be triggered.

---

### 6. Trigger Campaigns (Create Executions)

**When to trigger:**
- After campaigns are created and active
- When you want to see campaign executions

**How to trigger:**

**Option A: Via Script**
```bash
python trigger_campaigns.py
```

**Option B: Via Admin Interface**
- Go to **Campaigns** → Select campaign → **Trigger Now**

**Option C: Automatic (Event-based)**
- Campaigns trigger automatically when events occur
- Example: Customer makes purchase → Event trigger → Campaign executes

**What happens:**
- CampaignEngine finds active campaigns
- Evaluates triggers
- Finds target customers (from segments)
- Creates CampaignExecution records
- Delivers campaigns

**Result:**
- CampaignExecution records created
- Performance metrics tracked
- Campaign metrics visible in dashboard

---

### 7. Train ML Models

**When to train:**
- After DWH is populated
- When you have enough historical data (1000+ samples recommended)

**How to train:**
```bash
python train_models_from_dwh.py
```

**What it does:**
- Connects to DWH
- Extracts training data
- Trains NBO and Churn models
- Saves to `models/` directory

**Result:**
- `models/nbo.tflite` - Next Best Offer model
- `models/churn.tflite` - Churn prediction model

See [ML_GUIDE.md](ML_GUIDE.md) for detailed ML training instructions.

---

## Journey Builder

### When to Use Journeys

**Journeys** = Multi-step customer experiences with branching logic

**Use Cases:**
- **Customer Onboarding** - Welcome → Tutorial → First purchase → Reward
- **Tier Progression** - Check tier → Send upgrade offer → Wait → Check if upgraded
- **Win-Back Campaigns** - Detect inactivity → Send offer → Wait → Check response
- **Complex Flows** - Multiple conditions, waits, and actions

### How It Works

1. **Create Journey** in Journey Builder (drag nodes, connect them)
2. **Set Entry Segment** (which customers enter this journey)
3. **Activate Journey**
4. **Automatic Execution** - When customer enters segment → Journey starts automatically
5. **Event-Driven** - Journey waits for customer actions (e.g., purchase)

### Example Flow

```
New Customer Onboarding:
Start → Send Welcome Email → Wait 1 day → 
Condition: Made first purchase?
  ├─ YES → Award 100 points → End
  └─ NO → Send offer → Wait 3 days → End
```

**This runs automatically for all new customers!**

---

## Partners Page

### Purpose: Coalition Programs & Cross-Program Rewards

**Partners** = External businesses that participate in your loyalty program

### Use Cases

#### Coalition Programs
Multiple partners share one loyalty program:
- **Example:** Airline + Hotel + Car Rental = One points program
- Customers earn points from any partner
- Customers redeem points with any partner
- **Shared points** across all partners

#### Merchant Partners
Individual merchants with their own programs:
- Each merchant has their own program
- Customers can earn/redeem with multiple merchants
- **Separate points** per merchant

### How to Use

1. Go to **Partners** → **Add Partner**
2. Configure partner details
3. Create **Partner Programs** (link partner to loyalty program)
4. Configure **Earn/Burn Rates** (how points convert)
5. Set up **Settlements** (financial reconciliation)

---

## Dynamic Segmentation

### How Recalculate Works

1. **Click "Recalculate"** on a segment
2. System fetches customer IDs from DWH (or Xiva)
3. For each customer:
   - Fetches features from DWH/Xiva
   - Evaluates JSONLogic rules
   - Adds/removes from segment based on rules
4. Creates **SegmentSnapshot** (historical record)
5. Updates **member_count** and **last_calculated_at**

### When to Recalculate

- **After DWH data updates** - New features available
- **After rule changes** - Rules modified
- **Scheduled** - Automatic recalculation (via cron/Kafka)
- **On-demand** - Manual trigger via UI

---

## Summary

**Complete Setup Sequence:**

1. ✅ **Setup DWH** → `python setup_dwh_with_data.py`
2. ✅ **Create Programs with Tiers** → Via Program Builder or `create_full_demo.py`
3. ✅ **Create Segments** → Via Segment Builder (use DWH features)
4. ✅ **Create Campaigns** → Via Campaign Builder (target segments)
5. ✅ **Trigger Campaigns** → `python trigger_campaigns.py`
6. ✅ **Train ML Models** → `python train_models_from_dwh.py`

For detailed guides, see:
- [DWH_INTEGRATION.md](DWH_INTEGRATION.md) - DWH setup details
- [ML_GUIDE.md](ML_GUIDE.md) - ML training details
- [USER_GUIDE.md](USER_GUIDE.md) - Using the platform

