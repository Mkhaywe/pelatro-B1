# Loyalty Microservice - Khaywe

A comprehensive loyalty management microservice built with Django REST Framework, designed to replace Pelatro mViva with in-house development.

## Features

- ✅ **Core Loyalty**: Programs, Accounts, Transactions, Rewards, Redemptions
- ✅ **Campaign Management**: Full lifecycle, triggers, A/B testing
- ✅ **Segmentation**: Dynamic segments with DWH integration
- ✅ **Gamification**: Missions, Badges, Leaderboards, Streaks
- ✅ **Journey Builder**: Visual journey creation and execution
- ✅ **Partner Management**: Coalition programs, settlements
- ✅ **RBAC**: Role-based access control, approval workflows
- ✅ **ML Predictions**: NBO, Churn, RFM (on-premise/server-side)
- ✅ **TMF API**: TM Forum compliant API adapter layer

## Quick Start

### 1. Setup Virtual Environment

```powershell
# Create venv with Python 3.10
py -3.10 -m venv venv

# Activate venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup PostgreSQL Database

```powershell
# Run database setup script
.\setup_database.ps1

# Or manually:
psql -U postgres
CREATE DATABASE loyalty_db;
CREATE USER loyalty_user WITH PASSWORD 'loyalty_password';
GRANT ALL PRIVILEGES ON DATABASE loyalty_db TO loyalty_user;
\q
```

### 3. Configure Environment

Copy `.env.example` to `.env` and update values:

```powershell
cp .env.example .env
# Edit .env with your settings
```

Or set environment variables:

```powershell
$env:DB_NAME="loyalty_db"
$env:DB_USER="loyalty_user"
$env:DB_PASSWORD="loyalty_password"
$env:USE_POSTGRES="True"
```

### 4. Run Migrations

```powershell
python manage.py makemigrations loyalty
python manage.py migrate
```

### 5. Start Backend Server

```powershell
.\start_backend.ps1
```

Or manually:
```powershell
python manage.py runserver 8001
```

Backend runs at: `http://localhost:8001`

### 6. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

## Project Structure

```
.
├── loyalty/              # Main Django app
│   ├── models.py        # Core models
│   ├── models_khaywe.py # Extended models (Campaign, Segment, etc.)
│   ├── views.py         # Core ViewSets
│   ├── views_khaywe.py  # Extended ViewSets
│   ├── integration/     # DWH, Kafka integration
│   ├── services/        # Business logic
│   └── ml/              # ML inference
├── loyalty_project/     # Django project settings
├── frontend/            # Vue.js frontend
├── requirements.txt     # Python dependencies
└── .env.example         # Environment variables template
```

## API Endpoints

### Internal API (`/api/loyalty/v1/`)

- `/loyaltyPrograms/` - Programs
- `/loyaltyAccounts/` - Accounts
- `/campaigns/` - Campaigns
- `/segments/` - Segments
- `/missions/` - Missions
- `/badges/` - Badges
- `/journeys/` - Journeys
- `/experiments/` - A/B Tests
- `/partners/` - Partners
- `/roles/` - RBAC Roles
- `/dwh/ml/nbo/` - ML: Next Best Offer
- `/dwh/ml/churn/` - ML: Churn Prediction
- `/dwh/ml/rfm/` - ML: RFM Calculation

### TMF API (`/tmf-api/loyaltyManagement/v4/`)

- `/loyaltyAccount/` - TMF LoyaltyAccount
- `/loyaltyProgram/` - TMF LoyaltyProgram
- `/loyaltyTransaction/` - TMF LoyaltyTransaction

## Documentation

All documentation is now organized in the `docs/` directory:

- **[Setup Guide](docs/SETUP_GUIDE.md)** - Complete installation and setup
- **[Workflow Guide](docs/WORKFLOW_GUIDE.md)** - System workflow and setup sequence
- **[User Guide](docs/USER_GUIDE.md)** - How to use the platform
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[Architecture](docs/ARCHITECTURE.md)** - System architecture and design
- **[DWH Integration](docs/DWH_INTEGRATION.md)** - Data Warehouse setup
- **[ML Guide](docs/ML_GUIDE.md)** - Machine Learning training and usage
- **[XIVA Integration](docs/XIVA_INTEGRATION.md)** - Xiva BSS integration
- **[Frontend Guide](docs/FRONTEND_GUIDE.md)** - Frontend development
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

See [docs/README.md](docs/README.md) for complete documentation index.

## Requirements

- Python 3.10+
- PostgreSQL 12+
- Node.js 18+ (for frontend)
- Redis (optional, recommended)
- Kafka (optional, for events)

## License

Proprietary - Khaywe Internal Use
