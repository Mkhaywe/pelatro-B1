# ML Configuration Migration Guide

## ✅ What Changed

ML configuration has been moved from `settings.py` to a **database-backed system** with a separate config file for defaults.

### New Structure:

1. **`loyalty/config/ml_config.py`** - Default ML configuration (version controlled)
2. **`SystemConfiguration` model** - Database storage for dynamic configuration
3. **`ConfigurationService`** - Service layer with fallback logic
4. **UI can now save** - Changes persist in database

---

## 🚀 Migration Steps

### Step 1: Create Database Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

This creates the `SystemConfiguration` table.

### Step 2: Verify Configuration

The system will automatically:
- Use database config if available
- Fall back to `loyalty/config/ml_config.py` if not in database
- Fall back to `settings.py` for backward compatibility

**No breaking changes!** Existing `settings.py` config still works.

### Step 3: (Optional) Migrate Existing Config to Database

If you have existing config in `settings.py`, you can migrate it:

```python
# In Django shell: python manage.py shell
from loyalty.services.config_service import ConfigurationService
from django.conf import settings

# Migrate feature mapping
if hasattr(settings, 'ML_FEATURE_MAPPING'):
    ConfigurationService.set_ml_feature_mapping(
        settings.ML_FEATURE_MAPPING,
        updated_by='migration'
    )

# Migrate model input size
if hasattr(settings, 'ML_MODEL_INPUT_SIZE'):
    ConfigurationService.set_ml_model_input_size(
        settings.ML_MODEL_INPUT_SIZE,
        updated_by='migration'
    )
```

---

## 📁 File Structure

```
loyalty/
├── config/
│   ├── __init__.py
│   └── ml_config.py          # Default ML configuration
├── services/
│   └── config_service.py     # Configuration service (database + fallback)
├── models_khaywe.py          # SystemConfiguration model
└── views_config.py           # API endpoints (now saves to database)
```

---

## 🔄 How It Works

### Configuration Priority (Highest to Lowest):

1. **Database** (`SystemConfiguration` table) - Can be changed via UI
2. **Config File** (`loyalty/config/ml_config.py`) - Version controlled defaults
3. **Settings.py** - Backward compatibility fallback

### Example Flow:

```python
# 1. UI saves configuration
POST /api/config/ml
{
  "feature_mapping": {
    "revenue": "total_revenue",
    "transaction_count": "txn_count"
  }
}

# 2. Saved to database
SystemConfiguration.objects.create(
    category='ml',
    key='feature_mapping',
    value={'revenue': 'total_revenue', ...}
)

# 3. Inference service reads it
feature_mapping = ConfigurationService.get_ml_feature_mapping()
# Returns database value if exists, else config file, else settings.py
```

---

## ✅ Benefits

- ✅ **UI can save** - No code deployment needed
- ✅ **Dynamic** - Changes take effect immediately
- ✅ **Version controlled** - Defaults in Git
- ✅ **Backward compatible** - Still works with `settings.py`
- ✅ **Audit trail** - Tracks who changed what
- ✅ **Multi-environment** - Different configs per environment

---

## 🧪 Testing

1. **Test UI Save:**
   - Go to Admin → System Settings → ML Feature Mapping
   - Change a mapping
   - Click "Save ML Configuration"
   - Verify it's saved in database

2. **Test Fallback:**
   - Delete config from database
   - Verify system uses config file defaults
   - Verify predictions still work

3. **Test API:**
   ```bash
   # Get config
   GET /api/config/ml
   
   # Save config
   POST /api/config/ml
   {
     "feature_mapping": {"revenue": "total_revenue"},
     "model_input_size": 10
   }
   ```

---

## 📝 Notes

- **No restart needed** - Database changes take effect immediately
- **settings.py still works** - For backward compatibility
- **Config file is defaults** - Can be overridden via database/UI
- **Training script updated** - Uses configuration service

---

## 🔧 Troubleshooting

**Issue:** Configuration not saving
- Check database migration ran: `python manage.py migrate`
- Check `SystemConfiguration` table exists
- Check API response for errors

**Issue:** Changes not taking effect
- Clear any caches
- Restart Django server (if using settings.py fallback)
- Check database config is active: `is_active=True`

**Issue:** Want to reset to defaults
- Delete from database: `SystemConfiguration.objects.filter(category='ml').delete()`
- System will use config file defaults

