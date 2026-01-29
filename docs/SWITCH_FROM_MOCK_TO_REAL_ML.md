# Switching from Mock ML to Real ML - Complete Guide

## 🔍 **FOUND THE ISSUE!**

**The Problem:**
- ✅ TensorFlow **IS installed** in your venv (2.20.0)
- ✅ Model files exist (`models/nbo.tflite`, `models/churn.tflite`)
- ❌ **ML_MOCK_MODE environment variable is set to `True`** - This forces mock mode!

**The Solution:**
Set `ML_MOCK_MODE=False` when starting the Django server.

---

## ✅ Quick Fix

### Option 1: Update Start Scripts (Recommended)

The start scripts have been updated to set `ML_MOCK_MODE=False` automatically.

Just restart your server:
```powershell
.\start_backend.ps1
# or
.\start_all.ps1
```

### Option 2: Set Environment Variable Manually

Before starting Django:
```powershell
$env:ML_MOCK_MODE="False"
python manage.py runserver 8001
```

### Option 3: Unset Environment Variable

If `ML_MOCK_MODE` is set globally, unset it:
```powershell
Remove-Item Env:\ML_MOCK_MODE
# or
$env:ML_MOCK_MODE=''
```

---

## 📋 Requirements to Switch from Mock to Real ML

### 1. **Install Python ML Libraries** ✅ DONE

TensorFlow is already installed in your venv:
- TensorFlow 2.20.0 ✅
- NumPy 2.2.6 ✅
- Pandas 2.3.3 ✅
- scikit-learn 1.7.2 ✅

### 2. **Ensure Model Files Exist** ✅ DONE

- `models/nbo.tflite` ✅
- `models/churn.tflite` ✅

### 3. **Disable Mock Mode** ⚠️ **THIS IS THE ISSUE**

Set `ML_MOCK_MODE=False` in environment or start scripts.

### 4. **Configure DWH (Data Warehouse)**

The ML service needs customer features from your DWH. Configure in `settings.py`:

```python
# DWH Configuration
DWH_TYPE = 'postgresql'  # or 'oracle', 'snowflake'
DWH_HOST = 'localhost'
DWH_PORT = 5432
DWH_NAME = 'your_dwh_db'
DWH_USER = 'your_user'
DWH_PASSWORD = 'your_password'

# Feature mapping (maps DWH columns to model features)
ML_FEATURE_MAPPING = {
    'feature_0': 'total_revenue',
    'feature_1': 'transaction_count',
    'feature_2': 'days_since_last_transaction',
    # ... map all 10 features
}
```

---

## 🎯 How the System Decides: Mock vs Real ML

The system checks in this order:

1. **Is Mock Mode Enabled?** (`ML_MOCK_MODE = True`)
   - ✅ YES → Use Mock Service (dummy predictions) ⚠️ **THIS WAS YOUR ISSUE**
   - ❌ NO → Continue to step 2

2. **Is TensorFlow Installed?**
   - ❌ NO → **Automatically falls back to Mock Service**
   - ✅ YES → Continue to step 3

3. **Are Model Files Present?**
   - ❌ NO → Return error: "Model not available"
   - ✅ YES → Continue to step 4

4. **Can Features Be Extracted from DWH?**
   - ❌ NO → Return error: "Unable to extract features"
   - ✅ YES → **Use Real ML Service** ✅

---

## 🚀 Step-by-Step: Switch to Real ML

### Step 1: Disable Mock Mode ✅

The start scripts now set `ML_MOCK_MODE=False` automatically.

### Step 2: Restart Django Server

```powershell
# Stop current server (Ctrl+C)
# Restart with updated script
.\start_backend.ps1
```

### Step 3: Verify Real ML is Active

Run the diagnostic script:
```powershell
python check_ml_status.py
```

You should see:
```
*** REAL ML MODE SHOULD BE ACTIVE ***
   TensorFlow: OK
   NumPy: OK
   Mock Mode: Disabled
```

### Step 4: Test Real ML

1. Go to **Admin → ML & AI → Test ML Predictions**
2. Enter a customer ID
3. Run prediction
4. Check if it uses real ML (should show actual feature-based predictions with detailed explanations)

---

## 🎓 How to Train Models

### Option 1: Create Placeholder Models (Quick Start)

For development/testing:

```bash
python create_ml_models.py
```

**What this does:**
- Creates simple models trained on random data
- Models work but predictions are not accurate
- Good for testing the system

### Option 2: Train Real Models from DWH (Production)

For production with real data:

```bash
python train_models_from_dwh.py
```

**Prerequisites:**
1. DWH must be configured and connected
2. DWH must have historical data:
   - `customer_offer_history` table (for NBO training)
   - `customer_churn_history` table (for Churn training)
3. At least 1000+ samples recommended

**What this does:**
1. Connects to DWH
2. Extracts historical customer data
3. Prepares training data (features + labels)
4. Trains TensorFlow/Keras models
5. Converts to TFLite format
6. Saves to `models/` directory

---

## 🔧 Troubleshooting

### Problem: "Mock mode still enabled"

**Solution:**
```powershell
# Check current value
$env:ML_MOCK_MODE

# Set to False
$env:ML_MOCK_MODE="False"

# Or unset it
Remove-Item Env:\ML_MOCK_MODE
```

### Problem: "TensorFlow not available"

**Solution:**
Make sure Django server is using venv Python:
```powershell
# Activate venv first
.\venv\Scripts\Activate.ps1

# Then start server
python manage.py runserver 8001
```

### Problem: "Model not available"

**Solution:**
```bash
# Create placeholder models
python create_ml_models.py
```

### Problem: "Unable to extract features from DWH"

**Solutions:**
1. Check DWH connection settings in `settings.py`
2. Verify DWH is running and accessible
3. Check if customer data exists in DWH
4. Verify `ML_FEATURE_MAPPING` is configured correctly

---

## 📊 Infrastructure Requirements

### Minimum Requirements:
- **Python 3.10+** (for TensorFlow 2.15+)
- **TensorFlow 2.15+** (or 2.10+ minimum) ✅ **You have 2.20.0**
- **NumPy 1.24+** ✅ **You have 2.2.6**
- **DWH Connection** (PostgreSQL, Oracle, or Snowflake)
- **Model Files** (`models/*.tflite`) ✅ **You have them**

### Optional (Recommended):
- **Redis** (for feature caching - improves performance)
- **Pandas & scikit-learn** (for model training) ✅ **You have them**

### No Special Infrastructure Needed:
- ✅ No GPU required (CPU inference works fine)
- ✅ No external ML APIs needed (all on-premise)
- ✅ No cloud services required

---

## ✅ Checklist: Switch to Real ML

- [x] Install TensorFlow: `pip install tensorflow numpy pandas scikit-learn` ✅ **DONE**
- [x] Verify installation: TensorFlow 2.20.0 ✅ **DONE**
- [x] Check model files exist: `models/nbo.tflite` and `models/churn.tflite` ✅ **DONE**
- [ ] **Set `ML_MOCK_MODE=False` in environment or start scripts** ⚠️ **DO THIS**
- [ ] Restart Django server
- [ ] Test ML predictions in Admin UI
- [ ] (Optional) Train models with real data: `python train_models_from_dwh.py`

---

## 🎯 Summary

**Why Mock Was Being Used:**
- ❌ **ML_MOCK_MODE environment variable was set to `True`** ← **THIS WAS THE ISSUE**
- TensorFlow IS installed ✅
- Models exist ✅

**To Switch to Real ML:**
1. ✅ TensorFlow installed (already done)
2. ✅ Model files exist (already done)
3. ⚠️ **Set `ML_MOCK_MODE=False`** (start scripts updated)
4. Restart server

**The start scripts (`start_backend.ps1` and `start_all.ps1`) have been updated to automatically set `ML_MOCK_MODE=False`.**

Just restart your server and real ML will be used!
