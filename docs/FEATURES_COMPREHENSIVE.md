# Comprehensive Features Documentation

This document covers all features and functionalities implemented in the loyalty platform that may not be fully documented elsewhere.

---

## Table of Contents

1. [Points Management](#points-management)
2. [Gamification](#gamification)
3. [Promotions](#promotions)
4. [Rewards Management](#rewards-management)
5. [Eligibility System](#eligibility-system)
6. [Tier Management](#tier-management)
7. [Points Expiry](#points-expiry)
8. [Earn Caps](#earn-caps)
9. [RBAC & Approval Workflows](#rbac--approval-workflows)
10. [TMF API](#tmf-api)
11. [Event Bus & Kafka](#event-bus--kafka)
12. [Admin Configuration](#admin-configuration)

---

## Points Management

### Overview

The **Points Service** (`loyalty/services/points_service.py`) handles all points-related operations with comprehensive validation, expiry, caps, and reconciliation.

### Components

#### 1. Points Calculation Service
- **Purpose**: Calculate points based on earn/burn rules and transaction context
- **Features**:
  - JSONLogic rule evaluation
  - Tier-based multipliers
  - Transaction amount-based calculations
  - Context-aware calculations (channel, product, etc.)

#### 2. Points Validation Service
- **Purpose**: Validate points transactions before execution
- **Validations**:
  - Account status (active/inactive)
  - Sufficient balance (for burns)
  - Transaction limits
  - Duplicate transaction prevention
  - Program eligibility

#### 3. Points Cap Service
- **Purpose**: Enforce earning caps (daily/monthly/program-level)
- **Features**:
  - Daily caps
  - Monthly caps
  - Program-level caps
  - Cap usage tracking
  - Cap reset scheduling

#### 4. Points Expiry Service
- **Purpose**: Handle points expiry based on rules
- **Features**:
  - FIFO/LIFO/Proportional expiry
  - Grace periods
  - Expiry event tracking
  - Automatic expiry processing

#### 5. Points Reconciliation Service
- **Purpose**: Reconcile account balances
- **Features**:
  - Balance verification
  - Transaction audit
  - Discrepancy detection
  - Reconciliation reports

### API Endpoints

```
POST /api/loyalty/v1/services/points/earn/
POST /api/loyalty/v1/services/points/burn/
POST /api/loyalty/v1/services/points/transfer/
GET  /api/loyalty/v1/services/points/reconcile/{account_id}/
```

### Usage Example

```python
from loyalty.services.points_service import PointsService

points_service = PointsService()

# Earn points
result = points_service.earn_points(
    account=account,
    transaction_amount=Decimal('100.00'),
    transaction_context={
        'description': 'Purchase',
        'channel': 'online',
        'product_category': 'electronics'
    },
    earn_rules=program.earn_rules
)

# Burn points
result = points_service.burn_points(
    account=account,
    points=500,
    transaction_context={
        'description': 'Reward redemption',
        'reward_id': reward.id
    }
)
```

---

## Gamification

### Overview

The **Gamification Service** (`loyalty/services/gamification_service.py`) handles missions, badges, leaderboards, and streaks.

### Components

#### 1. Mission Progress Service
- **Purpose**: Track and update mission progress
- **Mission Types**:
  - `points_earned` - Earn X points
  - `transactions_count` - Make X transactions
  - `tier_upgrade` - Reach a tier
  - `badge_earn` - Earn a badge
  - `custom` - Custom mission logic

#### 2. Badge Award Service
- **Purpose**: Award badges to customers
- **Features**:
  - Automatic badge awards
  - Manual badge awards
  - Badge progress tracking
  - Badge collections

#### 3. Leaderboard Service
- **Purpose**: Manage leaderboards
- **Features**:
  - Multiple leaderboard types (points, transactions, etc.)
  - Time-based leaderboards (daily, weekly, monthly)
  - Ranking calculations
  - Entry management

#### 4. Streak Service
- **Purpose**: Track customer streaks
- **Streak Types**:
  - Login streaks
  - Purchase streaks
  - Engagement streaks
  - Custom streaks

### Models

- **Mission**: Mission definition
- **MissionProgress**: Customer mission progress
- **Badge**: Badge definition
- **BadgeAward**: Badge awards to customers
- **Leaderboard**: Leaderboard definition
- **LeaderboardEntry**: Leaderboard entries
- **Streak**: Customer streak tracking

### API Endpoints

```
GET  /api/loyalty/v1/missions/
POST /api/loyalty/v1/missions/
GET  /api/loyalty/v1/missions/{id}/progress/
POST /api/loyalty/v1/missions/{id}/update-progress/

GET  /api/loyalty/v1/badges/
POST /api/loyalty/v1/badges/
POST /api/loyalty/v1/badges/{id}/award/

GET  /api/loyalty/v1/leaderboards/
POST /api/loyalty/v1/leaderboards/
GET  /api/loyalty/v1/leaderboards/{id}/entries/

GET  /api/loyalty/v1/streaks/
POST /api/loyalty/v1/streaks/
```

---

## Promotions

### Overview

The **Promotions Service** (`loyalty/services/promotions_service.py`) handles promotion application, eligibility, triggers, and performance tracking.

### Components

#### 1. Promotion Eligibility Service
- **Purpose**: Check if customers are eligible for promotions
- **Checks**:
  - Promotion status (active/inactive)
  - Date range validation
  - Customer eligibility criteria
  - Usage limits
  - Tier requirements

#### 2. Promotion Application Service
- **Purpose**: Apply promotions to transactions
- **Features**:
  - Automatic application
  - Manual application
  - Stacking rules
  - Exclusion rules
  - Performance tracking

#### 3. Promotion Performance Service
- **Purpose**: Track promotion performance
- **Metrics**:
  - Usage count
  - Redemption rate
  - Revenue impact
  - Customer acquisition

### Event Triggers

Promotions can be triggered by events:
- `customer_login`
- `customer_purchase`
- `tier_upgrade`
- `points_earned`
- Custom events

### Model

- **Promotion**: Promotion definition with event triggers

### API Endpoints

```
GET  /api/loyalty/v1/promotions/
POST /api/loyalty/v1/promotions/
GET  /api/loyalty/v1/promotions/{id}/eligibility/
POST /api/loyalty/v1/promotions/{id}/apply/
GET  /api/loyalty/v1/promotions/{id}/performance/
```

---

## Rewards Management

### Overview

The **Rewards Service** (`loyalty/services/rewards_service.py`) handles rewards inventory, availability, redemption, and fulfillment.

### Components

#### 1. Rewards Inventory Service
- **Purpose**: Manage rewards inventory
- **Features**:
  - Availability checking
  - Inventory tracking
  - Stock management
  - Inventory alerts

#### 2. Rewards Redemption Service
- **Purpose**: Handle reward redemptions
- **Features**:
  - Redemption validation
  - Points deduction
  - Fulfillment tracking
  - Redemption history

### Model

- **LoyaltyReward**: Reward catalog item
- **LoyaltyRedemption**: Redemption record

### API Endpoints

```
GET  /api/loyalty/v1/loyaltyRewards/
POST /api/loyalty/v1/loyaltyRewards/
GET  /api/loyalty/v1/loyaltyRewards/{id}/availability/
POST /api/loyalty/v1/loyaltyRedemptions/
GET  /api/loyalty/v1/loyaltyRedemptions/
```

---

## Eligibility System

### Overview

The **Eligibility Service** (`loyalty/services/eligibility_service.py`) provides a centralized eligibility checking system.

### Components

#### 1. Eligibility Evaluation Service
- **Purpose**: Evaluate customer eligibility
- **Features**:
  - Rule-based evaluation
  - JSONLogic support
  - Caching for performance
  - Override support

#### 2. Eligibility Override Service
- **Purpose**: Manage eligibility overrides
- **Features**:
  - Manual overrides
  - Temporary overrides
  - Override expiration
  - Audit trail

#### 3. Eligibility Cache Service
- **Purpose**: Cache eligibility results
- **Features**:
  - Redis caching
  - Cache invalidation
  - Performance optimization

### Models

- **LoyaltyEligibilityRule**: Eligibility rules
- **LoyaltyEligibilityOverride**: Eligibility overrides

### API Endpoints

```
GET  /api/loyalty/v1/services/eligibility/check/
POST /api/loyalty/v1/services/eligibility/override/
GET  /api/loyalty/v1/loyaltyEligibilityRules/
GET  /api/loyalty/v1/loyaltyEligibilityOverrides/
```

---

## Tier Management

### Overview

The **Tier Service** (`loyalty/services/tier_service.py`) handles tier calculations, upgrades, downgrades, and benefits.

### Components

#### 1. Tier Calculation Service
- **Purpose**: Calculate customer tier
- **Features**:
  - Points-based calculation
  - Transaction-based calculation
  - Time-based calculation
  - Custom calculation rules

#### 2. Tier Upgrade Service
- **Purpose**: Handle tier upgrades
- **Features**:
  - Automatic upgrades
  - Upgrade notifications
  - Upgrade benefits application
  - Upgrade history

#### 3. Tier Downgrade Service
- **Purpose**: Handle tier downgrades
- **Features**:
  - Automatic downgrades
  - Grace periods
  - Downgrade notifications
  - Benefit removal

#### 4. Tier Benefit Service
- **Purpose**: Manage tier benefits
- **Features**:
  - Benefit application
  - Benefit expiration
  - Benefit tracking

### API Endpoints

```
GET  /api/loyalty/v1/services/tier/calculate/
POST /api/loyalty/v1/services/tier/upgrade/
POST /api/loyalty/v1/services/tier/downgrade/
GET  /api/loyalty/v1/services/tier/benefits/
```

---

## Points Expiry

### Overview

Points can expire based on configurable rules. The system supports multiple expiry strategies.

### Expiry Types

1. **FIFO (First In First Out)**: Oldest points expire first
2. **LIFO (Last In First Out)**: Newest points expire first
3. **Proportional**: Points expire proportionally

### Configuration

Configure expiry rules in Program Builder:
- **Expiry Period**: Days until points expire
- **Expiry Type**: FIFO/LIFO/Proportional
- **Grace Period**: Days before expiry warning
- **Tier-Based**: Different expiry rules per tier

### Models

- **PointsExpiryRule**: Expiry rule definition
- **PointsExpiryEvent**: Expiry event tracking

### API Endpoints

```
GET  /api/loyalty/v1/pointsExpiryRules/
POST /api/loyalty/v1/pointsExpiryRules/
GET  /api/loyalty/v1/pointsExpiryEvents/
POST /api/loyalty/v1/services/points/expire/
```

### Usage

Expiry is automatically processed by the Points Service when:
- Points are earned
- Points are burned
- Account balance is queried
- Manual expiry processing is triggered

---

## Earn Caps

### Overview

Earn caps limit the amount of points customers can earn within a time period.

### Cap Types

1. **Daily Cap**: Maximum points per day
2. **Monthly Cap**: Maximum points per month
3. **Program Cap**: Maximum points per program period
4. **Transaction Cap**: Maximum points per transaction

### Configuration

Configure earn caps in Program Builder:
- **Cap Type**: Daily/Monthly/Program/Transaction
- **Cap Amount**: Maximum points
- **Cap Period**: Period definition
- **Reset Schedule**: When caps reset

### Models

- **EarnCap**: Cap definition
- **CapUsage**: Cap usage tracking

### API Endpoints

```
GET  /api/loyalty/v1/earnCaps/
POST /api/loyalty/v1/earnCaps/
GET  /api/loyalty/v1/capUsages/
```

### Usage

Caps are automatically enforced by the Points Service when points are earned.

---

## RBAC & Approval Workflows

### Overview

Role-Based Access Control (RBAC) and approval workflows provide enterprise-grade access control and governance.

### Components

#### 1. Roles & Permissions
- **Roles**: User roles (Admin, Manager, Operator, etc.)
- **Permissions**: Granular permissions (create_program, edit_campaign, etc.)
- **Role-Permission Mapping**: Assign permissions to roles
- **User-Role Mapping**: Assign roles to users

#### 2. Approval Workflows
- **Workflow Definition**: Define approval workflows
- **Approval Requests**: Create approval requests
- **Approval Decisions**: Approve/reject requests
- **Workflow States**: Track workflow progress

### Models

- **Role**: Role definition
- **Permission**: Permission definition
- **RolePermission**: Role-permission mapping
- **UserRole**: User-role mapping
- **ApprovalWorkflow**: Workflow definition
- **ApprovalRequest**: Approval request
- **ApprovalDecision**: Approval decision

### API Endpoints

```
GET  /api/loyalty/v1/roles/
POST /api/loyalty/v1/roles/
GET  /api/loyalty/v1/permissions/
POST /api/loyalty/v1/rolePermissions/
POST /api/loyalty/v1/userRoles/

GET  /api/loyalty/v1/approvalWorkflows/
POST /api/loyalty/v1/approvalWorkflows/
GET  /api/loyalty/v1/approvalRequests/
POST /api/loyalty/v1/approvalRequests/
POST /api/loyalty/v1/approvalDecisions/
```

---

## TMF API

### Overview

TM Forum (TMF) compliant API adapter layer for telecom industry standards.

### Endpoints

```
GET  /tmf-api/loyaltyManagement/v4/loyaltyAccount/{id}
GET  /tmf-api/loyaltyManagement/v4/loyaltyAccount
GET  /tmf-api/loyaltyManagement/v4/loyaltyProgram/{id}
GET  /tmf-api/loyaltyManagement/v4/loyaltyProgram
GET  /tmf-api/loyaltyManagement/v4/loyaltyTransaction/{id}
GET  /tmf-api/loyaltyManagement/v4/loyaltyTransaction
```

### TMF Resources

- **LoyaltyAccount**: Customer loyalty account (TMF format)
- **LoyaltyProgram**: Loyalty program (TMF format)
- **LoyaltyTransaction**: Points transaction (TMF format)

### Features

- TMF-compliant JSON structure
- Standard TMF metadata (`@type`, `@baseType`, `href`)
- TMF error responses
- TMF pagination

---

## Event Bus & Kafka

### Overview

Event-driven architecture using Kafka for real-time event processing.

### Components

#### 1. Event Publisher
- **Purpose**: Publish events to Kafka
- **Features**:
  - Event serialization
  - Topic routing
  - Error handling
  - Retry logic

#### 2. Event Subscriber
- **Purpose**: Subscribe to events from Kafka
- **Features**:
  - Event deserialization
  - Event handlers
  - Error handling
  - Dead letter queue

#### 3. Event Types

**Customer Events**:
- `customer.created`
- `customer.updated`
- `customer.login`
- `customer.purchase`
- `customer.tier_upgrade`

**Loyalty Events**:
- `points.earned`
- `points.burned`
- `points.expired`
- `reward.redeemed`
- `campaign.triggered`

**System Events**:
- `segment.recalculated`
- `journey.started`
- `journey.completed`
- `ml.prediction.completed`

### Configuration

```python
# settings.py
LOYALTY_KAFKA_ENABLED = True
LOYALTY_KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
LOYALTY_KAFKA_GROUP_ID = 'loyalty-service'
```

### Usage

```python
from loyalty.events.event_bus import EventPublisher

publisher = EventPublisher()
publisher.publish(
    event_type='customer.purchase',
    event_data={
        'customer_id': '...',
        'amount': 100.00,
        'product_id': '...'
    },
    topic='loyalty-events'
)
```

---

## Admin Configuration

### Overview

The Admin page provides comprehensive configuration management through the UI.

### Configuration Sections

#### 1. Data Sources
- **Xiva API**: Configure Xiva BSS connection
- **DWH**: Configure Data Warehouse connection
- **Test Connections**: Test data source connectivity

#### 2. ML & AI
- **ML Status**: View ML system status
- **Model Configuration**: Configure model paths
- **Feature Mapping**: Map DWH columns to ML features
- **Test Predictions**: Test ML predictions

#### 3. System Settings
- **Feature Store**: Configure data source priority and merge strategy
- **ML Feature Mapping**: Configure DWH column to ML feature mappings
- **DWH Features**: Configure DWH table/view and custom queries
- **Model Input Size**: Configure ML model input size

#### 4. RBAC Management
- **Roles**: Manage user roles
- **Permissions**: Manage permissions
- **Role-Permission Mapping**: Assign permissions to roles

#### 5. Audit Log
- **View Audit Logs**: View system audit logs
- **Filter Logs**: Filter by action, object type, date
- **Search Logs**: Search audit log entries

### API Endpoints

```
GET  /api/loyalty/v1/config/get_all/
GET  /api/loyalty/v1/config/xiva/
POST /api/loyalty/v1/config/xiva/
GET  /api/loyalty/v1/config/xiva/test/
GET  /api/loyalty/v1/config/dwh/
POST /api/loyalty/v1/config/dwh/
GET  /api/loyalty/v1/config/dwh/test/
GET  /api/loyalty/v1/config/ml/
POST /api/loyalty/v1/config/ml/
GET  /api/loyalty/v1/config/ml/status/
POST /api/loyalty/v1/config/ml/test/
POST /api/loyalty/v1/config/dwh/features/
```

### Feature Mapping Configuration

**ML Feature Mapping**:
- Map DWH columns to ML model features
- Example: `revenue` → `total_revenue`
- Configure via Admin → System Settings → ML Feature Mapping

**DWH Features Configuration**:
- Configure DWH table/view name
- Configure custom SQL query (optional)
- Configure via Admin → System Settings → DWH Features Configuration

---

## Summary

### Fully Documented & Implemented Features
- ✅ **Core Loyalty**: Programs, Tiers, Accounts, Transactions
- ✅ **Points Management**: Calculation, Validation, Caps, Expiry, Reconciliation
- ✅ **Promotions Service**: Eligibility, Application, Performance Tracking
- ✅ **Rewards Service**: Inventory, Redemption, Fulfillment
- ✅ **Eligibility System**: Rule Evaluation, Overrides, Caching
- ✅ **Tier Management**: Calculation, Upgrades, Downgrades, Benefits
- ✅ **Points Expiry**: FIFO/LIFO/Proportional Expiry Rules
- ✅ **Earn Caps**: Daily/Monthly/Program/Transaction Caps
- ✅ **Gamification**: Missions, Badges, Leaderboards, Streaks
- ✅ **Campaigns**: Triggering, Execution, Performance Tracking
- ✅ **Segments**: Dynamic Segmentation, JSONLogic Rules, Snapshots
- ✅ **Journeys**: Visual Builder, Node Types, Execution Engine
- ✅ **ML & DWH Integration**: Feature Store, Model Inference, Training
- ✅ **Analytics**: Program, Campaign, Segment, Transaction Analytics
- ✅ **RBAC & Approval Workflows**: Roles, Permissions, Workflows
- ✅ **TMF API**: TM Forum Compliant API Adapter
- ✅ **Event Bus & Kafka**: Event Publishing, Subscribing, Handlers
- ✅ **Admin Configuration**: Data Sources, ML Config, Feature Mapping
- ✅ **Field Selector**: DWH Field Selection for JSONLogic Rules

### Partially Documented Features
- ⚠️ **Partners**: Models exist but detailed documentation pending
- ⚠️ **A/B Testing**: Basic implementation documented, advanced features pending

### Implementation Status
All features listed above are **fully implemented** in the codebase:
- Service classes in `loyalty/services/`
- API endpoints in `loyalty/views*.py`
- Models in `loyalty/models*.py`
- Event handlers in `loyalty/events/` and `loyalty/integration/`
- TMF adapters in `loyalty/tmf_*.py`

---

**Last Updated**: 2026-01-02

