# Gamification System: Quick Start Guide

## 🚀 Getting Started

### Step 1: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 2: Create Default Data
```bash
python create_default_gamification_data.py
```

This creates:
- 29 Mission Templates
- 48 Badges (12 types × 4 levels)

### Step 3: Configure Data Sources

Configure your data sources (CDR, Billing, CRM, App, Network) via API or UI:

```python
POST /api/loyalty/v1/data-sources/
{
  "source_type": "cdr",
  "source_name": "CDR System",
  "connection_config": {
    "api_endpoint": "https://cdr.example.com/api",
    "api_key": "your-key"
  },
  "event_mapping": {
    "event_type": "call_type",
    "value": "duration",
    "timestamp": "call_time"
  },
  "sync_frequency": "hourly"
}
```

### Step 4: Normalize Events

Send events from your data sources:

```python
POST /api/loyalty/v1/customer-events/normalize/
{
  "source_type": "cdr",
  "event": {
    "customer_id": "uuid-here",
    "call_type": "outgoing",
    "duration": 120,
    "call_time": "2026-01-22T10:00:00Z"
  }
}
```

### Step 5: Calculate Behavior Scores

```python
POST /api/loyalty/v1/behavior-scores/{customer_id}/recalculate/
```

This calculates:
- Engagement Score (0-100)
- Revenue Score (0-100)
- Loyalty Score (0-100)
- Risk Score (0-100)
- Digital Score (0-100)

### Step 6: Generate Personalized Missions

```python
POST /api/loyalty/v1/missions/generate-for-customer/
{
  "customer_id": "uuid-here",
  "max_missions": 5,
  "force_regenerate": false
}
```

This generates up to 5 personalized missions based on:
- Customer's behavior scores
- Mission template eligibility rules
- Generation rules

### Step 7: Track Mission Progress

Events automatically update mission progress. You can also manually update:

```python
POST /api/loyalty/v1/missionProgress/
{
  "mission": 1,
  "customer_id": "uuid-here",
  "current_value": 50,
  "target_value": 100
}
```

### Step 8: Award Badges

Badges are automatically awarded when criteria are met. You can also manually check:

```python
POST /api/loyalty/v1/badges/check-and-award/
{
  "badge_id": 1,
  "customer_id": "uuid-here"
}
```

---

## 📊 Example Workflow

### 1. Customer Makes a Call
- CDR system sends event → Normalized to `CustomerEvent`
- Event updates engagement score
- Mission progress updated (if applicable)
- Badge eligibility checked

### 2. Customer Recharges
- Billing system sends event → Normalized to `CustomerEvent`
- Event updates revenue score
- Mission progress updated
- Badge eligibility checked

### 3. System Generates Missions
- Behavior scores calculated
- Mission templates evaluated
- Personalized missions generated
- Customer sees missions in app

### 4. Customer Completes Mission
- Mission progress reaches target
- Points awarded
- Badge awarded (if applicable)
- Campaign triggered (if configured)

---

## 🎯 Key Concepts

### Mission Templates
- Reusable mission definitions
- 5 categories: Onboarding, Engagement, Revenue, Loyalty, Correction
- Parameterized thresholds
- Generation rules based on scores

### Dynamic Mission Generation
- Generates missions per customer
- Based on behavior scores
- Personalized thresholds
- Max 5 active missions per customer

### Behavior Scores
- Calculated from events and features
- Updated in real-time
- Used for mission generation
- Used for campaign targeting

### Badge Levels
- 4 levels: Bronze, Silver, Gold, Platinum
- Progressive unlocking
- Auto-award based on scores
- Manual award available

---

## 🔧 Configuration

### Data Source Configuration
Each data source needs:
- Connection config (API endpoint, DB connection, etc.)
- Event mapping (maps source fields to normalized structure)
- Sync frequency (real-time, hourly, daily, weekly)

### Mission Template Configuration
Each template needs:
- Category (onboarding, engagement, revenue, loyalty, correction)
- Metric (data_usage, recharge_amount, etc.)
- Threshold (fixed or parameterized)
- Period (daily, weekly, monthly)
- Reward config (points, badges, offers)
- Generation rules (score thresholds)

### Badge Configuration
Each badge needs:
- Badge type (activated, power_user, etc.)
- Level (bronze, silver, gold, platinum)
- Requirements (score thresholds, mission completion)
- Auto-award rules (JSONLogic)

---

## 📈 Monitoring

### Check Behavior Scores
```python
GET /api/loyalty/v1/behavior-scores/{customer_id}/
```

### Check Mission Progress
```python
GET /api/loyalty/v1/missions/{mission_id}/progress/?customer_id={customer_id}
```

### Check Badge Awards
```python
GET /api/loyalty/v1/badgeAwards/?customer_id={customer_id}
```

---

## 🎉 Success!

Your gamification system is now:
- ✅ Normalizing events from all sources
- ✅ Calculating behavior scores
- ✅ Generating personalized missions
- ✅ Awarding badges with levels
- ✅ Integrated with ML and campaigns

**The system is now a behavior control layer driving growth!** 🚀

