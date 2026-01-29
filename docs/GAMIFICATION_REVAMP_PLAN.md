# Gamification System Revamp Plan

## 🎯 Current State Assessment

### ✅ What We Have:
- Basic Mission, Badge, Leaderboard, Streak models
- Basic CRUD operations
- Simple progress tracking
- Frontend UI for management

### ❌ What's Missing (Critical):
1. **Event Normalization** - No unified event system
2. **Behavior Scoring** - No Engagement/Revenue/Loyalty/Risk/Digital scores
3. **Mission Templates** - Static missions, no template system
4. **Dynamic Generation** - Can't generate missions per user/segment
5. **Data Source Configuration** - No configurable data sources (CDR, Billing, etc.)
6. **Campaign Integration** - Not connected to campaign engine
7. **ML Integration** - Not using ML scores for mission generation

---

## 🏗️ Architecture: Behavior Control Layer

```
NETWORK DATA (CDR, Billing, App, CRM)
        ↓
[Event Normalization Layer]
        ↓
[Behavior Scoring Engine]
        ↓
[Gamification Engine] ← Mission Templates + Dynamic Generation
        ↓
[Loyalty Engine] (Tiers, Points)
        ↓
[Campaign Engine] (Offers, Promos)
        ↓
CUSTOMER (App/SMS/Push)
```

---

## 📋 Implementation Plan

### Phase 1: Event Normalization System ✅

**Create:**
- `CustomerEvent` model - Unified event structure
- `EventSource` model - Configurable data sources
- `EventNormalizer` service - Normalizes events from different sources

**Events:**
```python
Event {
  customer_id
  event_type      # 'DATA_USAGE', 'RECHARGE', 'APP_LOGIN', 'CALL', etc.
  value           # Numeric value (MB, $, count, etc.)
  timestamp
  source          # 'cdr', 'billing', 'app', 'crm', 'network'
  metadata        # Additional context
}
```

### Phase 2: Behavior Scoring Engine ✅

**Create:**
- `CustomerBehaviorScore` model - Stores all scores
- `BehaviorScoringService` - Calculates scores from events
- Score types:
  - Engagement Score (0-100)
  - Revenue Score (0-100)
  - Loyalty Score (0-100)
  - Risk Score (0-100) - Churn probability
  - Digital Score (0-100) - App usage

**Formula:**
```python
Engagement Score = 
  (calls_weight * call_activity) +
  (data_weight * data_activity) +
  (app_weight * app_activity)
```

### Phase 3: Mission Template System ✅

**Create:**
- `MissionTemplate` model - Reusable mission templates
- 5 Categories:
  1. Onboarding (Lifecycle)
  2. Engagement
  3. Revenue (ARPU)
  4. Loyalty
  5. Behavioral Correction

**Template Structure:**
```python
MissionTemplate {
  category
  template_name
  metric              # 'data_usage', 'recharge', 'app_login', etc.
  threshold           # Parameterized
  period              # 'daily', 'weekly', 'monthly'
  reward_config       # Points, badges, offers
  eligibility_rules   # JSONLogic
  generation_rules    # When to generate (score-based)
}
```

### Phase 4: Dynamic Mission Generation ✅

**Create:**
- `DynamicMissionGenerator` service
- Generates missions per user based on:
  - Behavior scores
  - Segment
  - ML predictions
  - Current behavior patterns

**Logic:**
```python
IF RiskScore > 80 AND EngagementScore < 30:
    generate_retention_mission()
    
IF RevenueScore > 90 AND DigitalScore > 70:
    generate_premium_upsell_mission()
```

### Phase 5: Badge System with Levels ✅

**Create:**
- Badge types (10-15 core types)
- Badge levels (Bronze/Silver/Gold/Platinum)
- Auto-award based on scores/missions

**Badge Types:**
1. Lifecycle: Activated, 30 Days Active, 90 Days Loyal
2. Engagement: Power User, App Champion
3. Revenue: Big Spender, Premium
4. Digital: Self-Care Pro, Auto-Renew
5. Social: Referrer
6. Risk: Comeback Hero

### Phase 6: Data Source Configuration ✅

**Create:**
- `DataSourceConfig` model - Configurable data sources
- Support for:
  - CDR (Call Detail Records)
  - Billing/OCS
  - CRM/Subscriber DB
  - App/Web/USSD
  - Network/QoE

**Configuration:**
```python
DataSourceConfig {
  source_type        # 'cdr', 'billing', 'crm', 'app', 'network'
  source_name
  connection_config  # API endpoint, DB connection, etc.
  event_mapping      # Maps source events → normalized events
  sync_frequency     # Real-time, hourly, daily
  is_active
}
```

### Phase 7: Campaign Integration ✅

**Connect:**
- Missions trigger campaigns
- Scores feed campaign targeting
- Rewards are campaign offers

---

## 🎯 Mission Template Categories

### 1. Onboarding Missions (Lifecycle)
**Goal:** Activate behavior fast

**Templates:**
- First Call Mission
- First Data Usage Mission
- App Installation Mission
- Auto-Renew Setup Mission

**Badges:** "Activated", "Digital Starter"

### 2. Engagement Missions
**Goal:** Increase usage frequency

**Templates:**
- Daily Usage Streak
- Weekly Activity Goal
- Feature Adoption Mission

**Badges:** "Active User", "Power User"

### 3. Revenue Missions (ARPU)
**Goal:** Make more money

**Templates:**
- Recharge Threshold Mission
- Bundle Purchase Mission
- Upsell Mission
- Roaming Usage Mission

**Badges:** "Big Spender", "Premium"

### 4. Loyalty Missions
**Goal:** Prevent churn

**Templates:**
- Active Days Mission
- On-Time Payment Mission
- No Inactivity Mission

**Badges:** "1 Month Loyal", "VIP"

### 5. Behavioral Correction Missions
**Goal:** Fix bad behavior

**Templates:**
- Low Usage Recovery Mission
- Churn Risk Intervention Mission
- QoE Compensation Mission

**Badges:** "Comeback Hero"

---

## 📊 Score-Based Mission Generation

**Example Logic:**

```python
# Low engagement → Engagement mission
IF EngagementScore < 30:
    generate_mission(
        template='daily_usage_streak',
        threshold=user_segment.avg_usage * 0.8,
        reward='bonus_data'
    )

# High churn risk → Retention mission
IF RiskScore > 70:
    generate_mission(
        template='active_days',
        threshold=7,
        reward='retention_offer'
    )

# High value + low products → Upsell mission
IF RevenueScore > 80 AND active_products < 3:
    generate_mission(
        template='product_adoption',
        threshold=1,
        reward='premium_offer'
    )
```

---

## 🔧 Implementation Steps

1. ✅ Create Event models and normalization
2. ✅ Create Behavior Scoring models and service
3. ✅ Create Mission Template system
4. ✅ Create Dynamic Mission Generator
5. ✅ Enhance Badge system with levels
6. ✅ Create Data Source Configuration
7. ✅ Integrate with Campaign engine
8. ✅ Update UI for new features

---

## 📈 Expected Outcome

**Before:**
- Static missions
- Manual setup
- No personalization
- No behavior scoring
- Limited data sources

**After:**
- Dynamic mission generation
- Score-based personalization
- Configurable data sources
- Template-based system (20-30 templates → unlimited missions)
- Integrated with ML and campaigns
- Real-time behavior tracking

---

## 🎯 Success Metrics

- Mission completion rate
- Engagement score improvement
- ARPU increase
- Churn reduction
- Badge award rate
- Campaign conversion from missions

