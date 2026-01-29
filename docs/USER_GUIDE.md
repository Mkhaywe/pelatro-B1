# User Guide

## Overview

This guide explains how to use the Khaywe Loyalty Platform features.

## Table of Contents

1. [Loyalty Programs](#loyalty-programs)
2. [Campaigns](#campaigns)
3. [Segments](#segments)
4. [Journey Builder](#journey-builder)
5. [Analytics](#analytics)
6. [Admin & Configuration](#admin--configuration)

---

## Loyalty Programs

### Creating a Program

1. Navigate to **Programs** → **Create Program**
2. Fill in:
   - **Name**: Program name (e.g., "VIP Rewards")
   - **Description**: Program description
   - **Status**: Active/Inactive
   - **Start/End Dates**: Program validity period

### Tier Management

1. In Program Builder, go to **Tier Management** section
2. Click **+ Add Tier**
3. Configure:
   - **Tier Name**: e.g., "Gold"
   - **Min Points**: Minimum points required
   - **Benefits**: Tier-specific benefits
   - **Priority**: Tier order

### Earn Rules (JSONLogic)

Define how customers earn points:

```json
{
  "if": [
    {">": [{"var": "transaction_amount"}, 100]},
    {"*": [{"var": "transaction_amount"}, 0.1]},
    0
  ]
}
```

This rule: If transaction > $100, earn 10% points, else 0.

### Burn Rules (JSONLogic)

Define how customers redeem points:

```json
{
  "/": [{"var": "points_requested"}, 100]
}
```

This rule: 100 points = $1 discount.

---

## Campaigns

### Creating a Campaign

1. Go to **Campaigns** → **Create Campaign**
2. Select:
   - **Program**: Which loyalty program
   - **Segment**: Target customer segment
   - **Trigger**: Event, Schedule, or Threshold
3. Configure delivery channels
4. Set status to **Active**
5. Save campaign

### Campaign Triggers

**Event Trigger:**
- Triggers when specific event occurs
- Example: Customer makes purchase

**Schedule Trigger:**
- Triggers at specific time/date
- Example: Every Monday at 9 AM

**Threshold Trigger:**
- Triggers when condition is met
- Example: Segment size > 100 customers

### Campaign Performance

View campaign metrics:
1. Go to **Campaigns** → Select campaign → **View Metrics**
2. See:
   - Total sent
   - Delivered
   - Opened
   - Clicked
   - Converted
   - Conversion rate

---

## Segments

### Creating a Segment

1. Go to **Segments** → **Create Segment**
2. Enter name and description
3. Choose:
   - **Static**: Manual member management
   - **Dynamic**: Uses DWH/Xiva features, recalculates automatically
4. Use **Visual Rule Builder** to define JSONLogic rules
5. Click **Recalculate** to populate members

### Dynamic Segmentation

Segments use DWH/Xiva features in JSONLogic rules:

```json
{
  "and": [
    {">": [{"var": "total_revenue"}, 1000]},
    {"<": [{"var": "last_purchase_days_ago"}, 30]}
  ]
}
```

**Recalculate:**
- Click **Recalculate** button
- System fetches customer IDs from DWH/Xiva
- Evaluates rules for each customer
- Updates segment membership
- Shows added/removed/total counts

---

## Journey Builder

### Creating a Journey

1. Go to **Journeys** → **Create Journey**
2. Drag nodes onto canvas:
   - **Start** - Entry point
   - **Action** - Send message, award points, etc.
   - **Condition** - Branching logic
   - **Wait** - Delay before next step
   - **End** - Exit point
3. Connect nodes with edges
4. Configure node properties
5. Set entry segment (which customers enter)
6. Activate journey

### Journey Execution

- Journeys run automatically when customers enter entry segment
- Event-driven: Waits for customer actions
- Multi-step: Can have multiple conditions and actions

---

## Analytics

### Dashboard

View system overview:
- Total programs
- Total campaigns
- Total segments
- Total customers
- Active campaigns

### Program Analytics

View program performance:
- Points earned/burned
- Tier distribution
- Customer growth
- Redemption rate

### Campaign Analytics

View campaign performance:
- Send/delivery rates
- Open/click rates
- Conversion rates
- ROI

### Segment Analytics

View segment metrics:
- Member count
- Growth trends
- Last calculated
- Historical snapshots

---

## Partners & Coalitions

### Purpose

**Partners** = External businesses that participate in your loyalty program

### Use Cases

#### **Coalition Programs**
Multiple partners share one loyalty program:
- **Example:** Airline + Hotel + Car Rental = One points program
- Customers earn points from any partner
- Customers redeem points with any partner
- **Shared points** across all partners

#### **Merchant Partners**
Individual merchants with their own programs:
- **Example:** Coffee shop chain
- Customers earn points when purchasing at partner
- Partner pays you for points issued
- **Settlement** - Partner pays you monthly

#### **Affiliate Partners**
Referral or marketing partners:
- **Example:** Credit card company
- Customers earn points when signing up via partner
- Partner gets commission
- **Settlement** - You pay partner for referrals

### What You Can Do

1. **Manage Partners** - Add, configure, set settlement frequency
2. **Configure Partner Programs** - Set earn/burn rates per partner
3. **Manage Coalitions** - Group partners, enable shared points
4. **Track Settlements** - View history, calculate payments
5. **API Key Management** - Generate keys for partner integrations

### Real-World Example

**Telecom Loyalty Program:**
- **Coffee Shop** (Merchant) - Customers earn 1 point per $1, you get $0.01 per point
- **Hotel Chain** (Coalition) - Shared points, customers can use telecom points for hotels
- **Credit Card** (Affiliate) - 1000 points per signup, you pay $10 per signup

---

## Partners & Coalitions

### Purpose

**Partners** = External businesses that participate in your loyalty program

### Use Cases

#### **Coalition Programs**
Multiple partners share one loyalty program:
- **Example:** Airline + Hotel + Car Rental = One points program
- Customers earn points from any partner
- Customers redeem points with any partner
- **Shared points** across all partners

#### **Merchant Partners**
Individual merchants with their own programs:
- **Example:** Coffee shop chain
- Customers earn points when purchasing at partner
- Partner pays you for points issued
- **Settlement** - Partner pays you monthly

#### **Affiliate Partners**
Referral or marketing partners:
- **Example:** Credit card company
- Customers earn points when signing up via partner
- Partner gets commission
- **Settlement** - You pay partner for referrals

### What You Can Do

1. **Manage Partners** - Add, configure, set settlement frequency
2. **Configure Partner Programs** - Set earn/burn rates per partner
3. **Manage Coalitions** - Group partners, enable shared points
4. **Track Settlements** - View history, calculate payments
5. **API Key Management** - Generate keys for partner integrations

### Real-World Example

**Telecom Loyalty Program:**
- **Coffee Shop** (Merchant) - Customers earn 1 point per $1, you get $0.01 per point
- **Hotel Chain** (Coalition) - Shared points, customers can use telecom points for hotels
- **Credit Card** (Affiliate) - 1000 points per signup, you pay $10 per signup

---

## Admin & Configuration

### Data Source Configuration

Configure Xiva and DWH:
1. Go to **Admin** → **Data Sources**
2. Enter Xiva API credentials
3. Click **Test Connection**
4. Enter DWH connection details
5. Click **Test Connection**

### ML Configuration

Configure ML models:
1. Go to **Admin** → **ML & AI**
2. View ML system status
3. Configure model paths
4. Test predictions

### System Settings

Configure feature store:
1. Go to **Admin** → **System Settings**
2. Set data source (DWH, Xiva, or Auto)
3. Set merge strategy
4. Save settings

---

## Quick Reference

### Common Tasks

**Create Program with Tiers:**
1. Programs → Create Program
2. Add tiers in Tier Management
3. Configure earn/burn rules
4. Save

**Create Dynamic Segment:**
1. Segments → Create Segment
2. Set to Dynamic
3. Build rules with Visual Rule Builder
4. Click Recalculate

**Trigger Campaign:**
1. Campaigns → Select campaign
2. Click Trigger Now
3. Or run: `python trigger_campaigns.py`

**Train ML Models:**
1. Ensure DWH is populated
2. Run: `python train_models_from_dwh.py`
3. Models saved to `models/` directory

---

## Next Steps

- See [SETUP_GUIDE.md](SETUP_GUIDE.md) for installation
- See [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) for workflow
- See [API_REFERENCE.md](API_REFERENCE.md) for API details
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for help

