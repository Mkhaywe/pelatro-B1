# Python Scripts Reference

## Overview

This document lists all Python scripts in the project, organized by category and purpose.

---

## 🚀 Setup & Initialization Scripts

### Database & Demo Data
- **`setup_dwh_with_data.py`** (26 KB)
  - Sets up DWH database with tables and historical data
  - Creates customer features, offer history, churn history, transaction history
  - Populates with sample data from Xiva or generates dummy data

- **`setup_postgres_and_demo.py`** (9.6 KB)
  - Sets up PostgreSQL database and creates demo data
  - Alternative setup script

- **`create_full_demo.py`** (21.7 KB)
  - Creates comprehensive demo data
  - Creates programs, segments, campaigns, rewards, gamification, customer accounts
  - Fetches customers from Xiva API

- **`create_demo_via_api.py`** (9.5 KB)
  - Creates demo data via API calls
  - Alternative demo data creation method

- **`add_more_demo_data.py`** (6.8 KB)
  - Adds additional demo data to existing database

- **`demo_complete_system.py`** (14.2 KB)
  - Demonstrates complete system functionality

- **`demo_features_only.py`** (6.3 KB)
  - Creates demo data for features only

- **`create_user.py`** (1.2 KB)
  - Creates Django superuser non-interactively
  - Usage: `python create_user.py`

---

## 🤖 Machine Learning Scripts

### ML Model Creation & Training
- **`create_ml_models.py`** (4.4 KB)
  - Creates placeholder TensorFlow Lite models
  - Generates simple NBO and Churn models
  - Saves to `models/` directory

- **`train_models_from_dwh.py`** (14.7 KB)
  - Trains ML models using DWH data
  - Connects to DWH, extracts historical data
  - Trains TensorFlow/Keras models
  - Converts to TFLite and saves to `models/` directory
  - Saves StandardScaler for preprocessing

---

## 🧪 Testing Scripts

### DWH Testing
- **`test_dwh_connection.py`** (2.6 KB)
  - Tests DWH connection from Django environment
  - Verifies Django can connect to configured DWH
  - Retrieves customer features

### Xiva Testing
- **`test_xiva_quick.py`** (1.3 KB)
  - Quick Xiva API test

- **`test_xiva_endpoint.py`** (1.6 KB)
  - Tests specific Xiva endpoint

- **`test_xiva_integration.py`** (14.6 KB)
  - Comprehensive Xiva integration test

- **`test_xiva_advanced.py`** (19.4 KB)
  - Advanced Xiva API testing

- **`test_xiva_data_inspection.py`** (7.4 KB)
  - Inspects Xiva data structure

- **`test_xiva_pagination.py`** (7.0 KB)
  - Tests Xiva pagination

- **`test_xiva_pagination_detailed.py`** (5.4 KB)
  - Detailed pagination testing

- **`test_xiva_pagination_final.py`** (4.4 KB)
  - Final pagination test

- **`test_xiva_offset.py`** (834 bytes)
  - Tests Xiva offset parameter

- **`test_xiva_segmentation.py`** (5.3 KB)
  - Tests Xiva segmentation integration

### System Testing
- **`test_complete_flow.py`** (6.5 KB)
  - Tests complete system flow

- **`test_env_loading.py`** (2.5 KB)
  - Tests environment variable loading

---

## ⚙️ Operational Scripts

### Campaign Management
- **`trigger_campaigns.py`** (5.7 KB)
  - Triggers campaigns and creates campaign executions
  - Demonstrates how campaigns are executed
  - Creates CampaignExecution records

---

## 📁 Django Application Files

### Core Application
- **`manage.py`** (695 bytes)
  - Django management script

### Models
- **`loyalty/models.py`** (14.6 KB)
  - Core loyalty models (Programs, Accounts, Transactions, etc.)

- **`loyalty/models_khaywe.py`** (30.1 KB)
  - Extended models (Campaigns, Segments, Journeys, etc.)

### Views & APIs
- **`loyalty/views.py`** (84.9 KB)
  - Core ViewSets for loyalty models

- **`loyalty/views_khaywe.py`** (22.4 KB)
  - Extended ViewSets (Campaigns, Segments, etc.)

- **`loyalty/views_auth.py`** (5.0 KB)
  - Authentication views

- **`loyalty/views_config.py`** (16.2 KB)
  - Configuration management views

- **`loyalty/views_dashboard.py`** (3.0 KB)
  - Dashboard views

- **`loyalty/views_dwh.py`** (19.0 KB)
  - DWH integration views

- **`loyalty/views_external.py`** (10.5 KB)
  - External API views (Xiva)

- **`loyalty/views_services.py`** (13.1 KB)
  - Service layer views

### Serializers
- **`loyalty/serializers.py`** (5.6 KB)
  - Core serializers

- **`loyalty/serializers_khaywe.py`** (7.4 KB)
  - Extended serializers

- **`loyalty/tmf_serializers.py`** (4.7 KB)
  - TMF API serializers

### URLs
- **`loyalty/urls.py`** (7.3 KB)
  - Main URL configuration

- **`loyalty/urls_auth.py`** (369 bytes)
  - Authentication URLs

- **`loyalty/urls_external.py`** (1.3 KB)
  - External API URLs

- **`loyalty/tmf_urls.py`** (2.9 KB)
  - TMF API URLs

### Services
- **`loyalty/services/points_service.py`** (22.7 KB)
  - Points calculation and management service

- **`loyalty/services/eligibility_service.py`** (12.7 KB)
  - Eligibility checking service

- **`loyalty/services/tier_service.py`** (13.4 KB)
  - Tier calculation and management service

- **`loyalty/services/segmentation.py`** (5.9 KB)
  - Segmentation engine

- **`loyalty/services/rewards_service.py`** (11.4 KB)
  - Rewards management service

- **`loyalty/services/promotions_service.py`** (13.9 KB)
  - Promotions service

- **`loyalty/services/gamification_service.py`** (12.7 KB)
  - Gamification service

### Engines
- **`loyalty/engines/campaign_engine.py`** (18.8 KB)
  - Campaign execution engine

- **`loyalty/engines/journey_engine.py`** (17.7 KB)
  - Journey execution engine

- **`loyalty/engines/segment_engine.py`** (10.1 KB)
  - Segment recalculation engine

### Integration
- **`loyalty/integration/xiva_client.py`** (37.8 KB)
  - Xiva API client

- **`loyalty/integration/xiva_feature_extractor.py`** (9.2 KB)
  - Xiva feature extraction

- **`loyalty/integration/dwh.py`** (8.2 KB)
  - DWH connectors (PostgreSQL, Oracle, Snowflake)

- **`loyalty/integration/feature_store.py`** (9.7 KB)
  - Feature store with Redis caching

- **`loyalty/integration/kafka_dwh.py`** (3.5 KB)
  - Kafka DWH integration

- **`loyalty/integration/kafka_handlers.py`** (5.7 KB)
  - Kafka event handlers

- **`loyalty/integration/external.py`** (2.0 KB)
  - External integration utilities

### ML
- **`loyalty/ml/inference.py`** (10.5 KB)
  - ML inference service (NBO, Churn, RFM)

- **`loyalty/ml/mock_inference.py`** (10.2 KB)
  - Mock ML inference for testing

### Utilities
- **`loyalty/utils.py`** (1.4 KB)
  - Utility functions (JSONLogic, Decimal conversion)

- **`loyalty/admin.py`** (743 bytes)
  - Django admin configuration

### Management Commands
- **`loyalty/management/commands/reset_xiva_client.py`** (1.6 KB)
  - Resets Xiva client singleton

- **`loyalty/management/commands/recalculate_loyalty_balances.py`** (3.0 KB)
  - Recalculates loyalty account balances

- **`loyalty/management/commands/fix_loyalty_balances.py`** (5.2 KB)
  - Fixes loyalty account balances

- **`loyalty/management/commands/run_loyalty_consumer.py`** (1.2 KB)
  - Runs Kafka consumer for loyalty events

### Project Configuration
- **`loyalty_project/settings.py`** (7.8 KB)
  - Django project settings

- **`loyalty_project/urls.py`** (1.4 KB)
  - Main project URLs

- **`loyalty_project/wsgi.py`** (244 bytes)
  - WSGI configuration

- **`loyalty_project/asgi.py`** (244 bytes)
  - ASGI configuration

---

## 📊 Script Categories Summary

### Setup & Demo (8 scripts)
- Database setup
- Demo data creation
- User creation

### ML & Training (2 scripts)
- Model creation
- Model training

### Testing (13 scripts)
- DWH testing
- Xiva API testing
- System flow testing

### Operational (1 script)
- Campaign triggering

### Django Application (60+ files)
- Models, Views, Serializers
- Services, Engines
- Integration, ML
- Management commands

---

## 🎯 Most Important Scripts

### For Setup
1. **`setup_dwh_with_data.py`** - Sets up DWH with training data
2. **`create_full_demo.py`** - Creates demo data
3. **`create_user.py`** - Creates admin user

### For ML
1. **`train_models_from_dwh.py`** - Trains ML models
2. **`create_ml_models.py`** - Creates placeholder models

### For Operations
1. **`trigger_campaigns.py`** - Triggers campaigns

### For Testing
1. **`test_dwh_connection.py`** - Tests DWH connection
2. **`test_xiva_integration.py`** - Tests Xiva integration

---

## 📝 Usage Examples

### Setup DWH
```bash
python setup_dwh_with_data.py
```

### Create Demo Data
```bash
python create_full_demo.py
```

### Train ML Models
```bash
python train_models_from_dwh.py
```

### Trigger Campaigns
```bash
python trigger_campaigns.py
```

### Test DWH Connection
```bash
python test_dwh_connection.py
```

### Create Admin User
```bash
python create_user.py
```

---

## 🔍 Finding Scripts

### By Purpose
- **Setup**: `setup_*.py`, `create_*.py`
- **ML**: `*ml*.py`, `train_*.py`
- **Testing**: `test_*.py`
- **Operations**: `trigger_*.py`

### By Location
- **Root**: Setup, demo, testing scripts
- **loyalty/**: Django application code
- **loyalty/services/**: Business logic services
- **loyalty/engines/**: Execution engines
- **loyalty/integration/**: External integrations
- **loyalty/ml/**: ML inference
- **loyalty/management/commands/**: Django management commands

---

**Total Scripts**: 80+ Python files  
**Total Size**: ~500 KB (excluding venv and node_modules)

