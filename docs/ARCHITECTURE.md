# System Architecture

## Overview

The Khaywe Loyalty Platform is an enterprise-grade loyalty management system built with Django REST Framework backend and Vue.js frontend, designed to replace Pelatro mViva with in-house development.

## Architecture Principles

1. **Event-Driven Architecture** - Everything is event-driven, not polling
2. **Microservices-Ready** - Clean boundaries, async communication
3. **Scalable & Performant** - Handle millions of customers, real-time
4. **Resilient** - Circuit breakers, retries, graceful degradation
5. **Observable** - Comprehensive logging, metrics, tracing
6. **Testable** - Unit tests, integration tests, contract tests
7. **Maintainable** - Clean code, SOLID principles, design patterns

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Warehouse (DWH)                     │
│  PostgreSQL / Oracle / Snowflake                            │
│  - Customer analytics views                                 │
│  - Transaction history                                      │
│  - Feature tables                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ SQL (Read-only)
                     │
┌────────────────────▼────────────────────────────────────────┐
│           Loyalty Microservice (Django)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  DWH Integration Layer                                │  │
│  │  - Multi-backend connector (Oracle/PG/Snowflake)     │  │
│  │  - Connection pooling                                 │  │
│  │  - Query execution                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Feature Store                                        │  │
│  │  - Redis caching (1hr TTL)                           │  │
│  │  - Batch feature extraction                          │  │
│  │  - Cache invalidation                                │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Segmentation Engine                                 │  │
│  │  - Query DWH for customer attributes                 │  │
│  │  - JSONLogic rule evaluation                         │  │
│  │  - Segment membership calculation                    │  │
│  │  - Dynamic segment updates                           │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ML Inference Service                                 │  │
│  │  - Feature extraction from DWH                       │  │
│  │  - TFLite models (on-premise)                       │  │
│  │  - NBO, Churn, RFM predictions                       │  │
│  │  - Privacy-compliant (no external APIs)              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Core Loyalty Models                                  │  │
│  │  - Programs, Accounts, Transactions                   │  │
│  │  - Campaigns, Segments, Gamification                 │  │
│  │  - Journeys, Experiments, Partners                   │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ REST API / Kafka
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Vue Frontend (Console)                        │
│  - Program Builder                                          │
│  - Campaign Management                                      │
│  - Segment Builder                                          │
│  - Customer 360                                             │
│  - Analytics Dashboards                                     │
│  - Gamification                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Feature Status

### ✅ Fully Implemented

#### Core Loyalty
- ✅ Programs CRUD with tiers
- ✅ Accounts management
- ✅ Transactions (earn/burn)
- ✅ Rewards catalog
- ✅ Redemptions
- ✅ Points expiry rules
- ✅ Earn caps

#### Campaign Management
- ✅ Campaign CRUD
- ✅ Campaign targeting (segments)
- ✅ Campaign triggers (event/schedule/threshold)
- ✅ Campaign delivery
- ✅ Campaign execution tracking
- ✅ Campaign performance analytics

#### Segmentation
- ✅ Segment CRUD
- ✅ Segment rules (JSONLogic)
- ✅ Segment membership tracking
- ✅ Dynamic segment recalculation
- ✅ Segment snapshots

#### ML & DWH
- ✅ DWH integration (PostgreSQL/Oracle/Snowflake)
- ✅ Feature Store with Redis caching
- ✅ ML inference (NBO, Churn, RFM)
- ✅ ML model training from DWH
- ✅ Feature mapping and extraction

#### Gamification
- ✅ Missions model
- ✅ Badges model
- ✅ Leaderboards model
- ✅ Streaks model

#### Journeys
- ✅ Journey CRUD
- ✅ Journey nodes (START, CONDITION, ACTION, WAIT, END)
- ✅ Journey edges (routing)
- ✅ Journey execution
- ✅ Journey state machine

#### A/B Testing
- ✅ Experiments model
- ✅ Experiment assignments
- ✅ Holdout groups

#### Partners
- ✅ Partners model
- ✅ Partner programs
- ✅ Partner settlements
- ✅ Coalitions

#### RBAC
- ✅ Roles model
- ✅ Permissions model
- ✅ User-role mapping
- ✅ Approval workflows
- ✅ Approval requests/decisions

### ⚠️ Needs Service Layer

These models exist but need business logic services:

- **Rewards Service** - Inventory, availability, redemption
- **Promotions Service** - Application, eligibility, triggers
- **Gamification Service** - Mission progress, badge awards, leaderboards, streaks
- **A/B Testing Service** - Experiment execution, assignment, analysis
- **Partners Service** - Integration, settlements, coalitions
- **Analytics Service** - Calculations, reports, cohorts
- **Customer 360 Service** - Profile aggregation, history

---

## "God Mode" Features

**God Mode** = Predictive + Automated + Data-Driven Loyalty Management

### Core Components

#### 1. ML Predictions ✅
- Predicts best offers for each customer (NBO)
- Predicts churn probability
- Calculates customer value (RFM)

#### 2. Dynamic Segmentation ✅
- Evaluates segments using DWH features
- Recalculates automatically on DWH updates
- Uses JSONLogic for flexible rules

#### 3. DWH Integration ✅
- Queries DWH for customer features
- Caches features in Redis
- Provides data for ML and segmentation

#### 4. Automated Campaigns ✅
- Triggers campaigns based on events
- Uses ML predictions for targeting
- Personalizes offers per customer

### God Mode Workflows

#### Automated Retention Campaign
```
1. DWH publishes customer update event → Kafka
2. Kafka consumer receives event
3. Feature Store invalidates cache
4. ML predicts churn → High risk detected
5. Segmentation Engine adds customer to "High Churn Risk" segment
6. Campaign triggers automatically
7. ML predicts NBO → Best retention offer selected
8. Offer sent to customer
```

#### Personalized Campaign
```
1. Campaign created targeting "VIP Customers" segment
2. Campaign triggers for segment members
3. For each customer:
   a. ML predicts NBO → Best offer selected
   b. Personalized message generated
   c. Sent via preferred channel
4. Performance tracked in real-time
```

---

## Enterprise Architecture Components

### 1. Event-Driven Architecture

**Event Bus System:**
- EventPublisher - Publish events to Kafka/RabbitMQ
- EventSubscriber - Subscribe to events
- Event Handlers - Process events asynchronously
- Event Store - Store events for replay/audit

**Event Types:**
- `CustomerEvent` - Customer actions (purchase, login, etc.)
- `PointsEvent` - Points earned/burned
- `CampaignEvent` - Campaign triggered/completed
- `SegmentEvent` - Segment membership changed
- `JourneyEvent` - Journey step completed

### 2. Execution Engines

**Campaign Execution Engine:**
- CampaignTriggerService - Evaluate triggers
- CampaignTargetingService - Find eligible customers
- CampaignDeliveryService - Send campaigns
- CampaignPerformanceService - Track metrics

**Journey Execution Engine:**
- JourneyStateMachine - Manage journey state
- JourneyTriggerService - Evaluate triggers
- JourneyActionService - Execute actions
- JourneyRoutingService - Route to next node

**Segment Recalculation Engine:**
- SegmentEvaluationService - Evaluate rules
- SegmentUpdateService - Update memberships
- SegmentSnapshotService - Create snapshots

### 3. Business Logic Services

**Points Service:**
- PointsCalculationService - Calculate points
- PointsValidationService - Validate transactions
- PointsExpiryService - Handle expiry
- PointsCapService - Enforce caps

**Eligibility Service:**
- EligibilityEvaluationService - Evaluate rules
- EligibilityOverrideService - Handle overrides
- EligibilityCacheService - Cache evaluations

**Tier Service:**
- TierCalculationService - Calculate tier
- TierUpgradeService - Handle upgrades
- TierDowngradeService - Handle downgrades

### 4. Background Task Processing

**Celery Tasks:**
- RecalculateSegmentTask - Async segment recalculation
- ProcessCampaignTask - Async campaign processing
- ExecuteJourneyTask - Async journey execution
- ExpirePointsTask - Async points expiry

### 5. Caching Layer

**Redis Caching:**
- CustomerFeaturesCache - Cache DWH features
- SegmentMembershipCache - Cache segment memberships
- EligibilityCache - Cache eligibility results
- MLPredictionsCache - Cache ML predictions

### 6. Resilience Patterns

**Circuit Breaker:**
- DWHCircuitBreaker - Protect DWH calls
- MLCircuitBreaker - Protect ML calls
- ExternalAPICircuitBreaker - Protect external APIs

**Retry Logic:**
- ExponentialBackoffRetry - Retry with backoff
- CircuitBreakerRetry - Retry with circuit breaker

### 7. Observability

**Logging:**
- Structured logging (JSON)
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Request/response logging

**Metrics:**
- Prometheus metrics
- Custom business metrics
- Performance metrics

**Tracing:**
- OpenTelemetry integration
- Distributed tracing
- Request tracing

---

## Technology Stack

### Backend
- **Django 5.2** - Web framework
- **Django REST Framework** - API framework
- **PostgreSQL** - Primary database
- **Redis** - Caching and feature store
- **Kafka** (optional) - Event streaming
- **TensorFlow Lite** - ML inference
- **SQLAlchemy** - DWH connectors

### Frontend
- **Vue 3** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Vue Router** - Routing
- **Pinia** - State management
- **Axios** - HTTP client
- **ECharts** - Charts and visualizations
- **Vue Flow** - Journey builder

---

## Data Flow Examples

### Customer Segmentation

```
User creates segment in UI
    ↓
Segmentation Engine queries DWH for customer attributes
    ↓
Feature Store caches results in Redis
    ↓
JSONLogic rules evaluated against DWH features
    ↓
SegmentMember table updated in loyalty DB
    ↓
Campaigns triggered for matching customers
```

### ML Prediction (NBO)

```
Campaign triggers NBO prediction
    ↓
Feature Store gets customer features (from cache or DWH)
    ↓
ML Inference Service loads TFLite model
    ↓
Features normalized and fed to model
    ↓
Model predicts best offer
    ↓
Campaign uses prediction to personalize offer
```

---

## Next Steps

- See [SETUP_GUIDE.md](SETUP_GUIDE.md) for installation
- See [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) for workflow
- See [ML_GUIDE.md](ML_GUIDE.md) for ML details
- See [DWH_INTEGRATION.md](DWH_INTEGRATION.md) for DWH setup

