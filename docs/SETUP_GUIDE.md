# Setup Guide - Complete Installation Instructions

## Prerequisites

- **Python 3.10+**
- **PostgreSQL 12+** (for production) or SQLite (for development)
- **Node.js 18+** (for frontend)
- **Redis** (optional, recommended for caching)
- **Kafka** (optional, for event streaming)

## Step 1: Clone and Setup Virtual Environment

```powershell
# Create venv with Python 3.10
py -3.10 -m venv venv

# Activate venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Database Setup

### Option A: PostgreSQL (Recommended for Production)

```powershell
# Create database
psql -U postgres
CREATE DATABASE loyalty_db;
CREATE USER loyalty_user WITH PASSWORD 'loyalty_password';
GRANT ALL PRIVILEGES ON DATABASE loyalty_db TO loyalty_user;
\q
```

### Option B: SQLite (Development)

No setup needed - SQLite database will be created automatically.

## Step 3: Configure Environment

Create `.env` file in project root:

```env
# Database
USE_POSTGRES=True
DB_NAME=loyalty_db
DB_USER=loyalty_user
DB_PASSWORD=loyalty_password
DB_HOST=localhost
DB_PORT=5432

# Xiva API (for customer data)
XIVA_API_BASE_URL=https://your-xiva-instance.com/api
XIVA_API_USERNAME=your_username
XIVA_API_PASSWORD=your_password

# DWH Configuration (for ML and segmentation)
DWH_TYPE=postgresql
DWH_POSTGRES_CONNECTION_STRING=postgresql://user:password@localhost:5432/DWH
DWH_CUSTOMER_FEATURES_TABLE=public.customer_features_view

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_FEATURE_STORE_DB=1

# ML Configuration
ML_MOCK_MODE=False
ML_MODEL_NBO_PATH=models/nbo.tflite
ML_MODEL_CHURN_PATH=models/churn.tflite
ML_MODEL_INPUT_SIZE=10
```

## Step 4: Run Migrations

```powershell
python manage.py makemigrations loyalty
python manage.py migrate
```

## Step 5: Create Superuser

```powershell
python manage.py createsuperuser
# Or use: python create_user.py
```

## Step 6: Setup DWH (Optional but Recommended)

For ML and advanced segmentation:

```powershell
python setup_dwh_with_data.py
```

This creates DWH tables and populates with sample data.

## Step 7: Start Backend Server

```powershell
.\start_backend.ps1
# Or manually:
python manage.py runserver 8000
```

Backend runs at: `http://localhost:8000`

## Step 8: Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

## Step 9: Create Demo Data (Optional)

```powershell
python create_full_demo.py
```

This creates sample programs, segments, campaigns, and customer accounts.

## Verification

1. **Backend**: Visit `http://localhost:8000/api/loyalty/v1/dashboard/stats/`
2. **Frontend**: Visit `http://localhost:5173` and login
3. **Admin**: Visit `http://localhost:8000/admin/`

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues.

## Next Steps

- Read [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) for system workflow
- Read [USER_GUIDE.md](USER_GUIDE.md) for using the platform
- Read [DWH_INTEGRATION.md](DWH_INTEGRATION.md) for DWH setup
- Read [ML_GUIDE.md](ML_GUIDE.md) for ML training

