# Troubleshooting Guide

## Common Issues and Solutions

### Authentication Issues

#### Xiva API Authentication Error

**Error:** `Not authenticated. Please configure XIVA_API_USERNAME and XIVA_API_PASSWORD`

**Solution:**
1. Verify credentials in `.env` file:
   ```env
   XIVA_API_USERNAME=your_username
   XIVA_API_PASSWORD=your_password
   ```
2. Restart Django server (singleton needs refresh)
3. Check Xiva API URL is correct
4. Run: `python manage.py reset_xiva_client`

---

### Database Issues

#### Migration Errors

**Error:** `django.db.migrations.exceptions.InconsistentMigrationHistory`

**Solution:**
```bash
python manage.py migrate --fake-initial
```

#### Field Clash Errors

**Error:** `Reverse accessor 'LoyaltyProgram.earn_caps' clashes`

**Solution:**
- Already fixed: `EarnCap.program` uses `related_name='earn_cap_instances'`
- Run migrations: `python manage.py migrate`

---

### Redis Cache Issues

#### Decimal Serialization Error

**Error:** `Object of type Decimal is not JSON serializable`

**Solution:**
- Already fixed: `convert_for_json()` handles Decimal and datetime
- Restart server if still seeing errors

#### Datetime Serialization Error

**Error:** `Object of type datetime is not JSON serializable`

**Solution:**
- Already fixed: `convert_for_json()` converts datetime to ISO strings
- Restart server if still seeing errors

---

### Frontend Issues

#### Visual Rule Builder Resets

**Problem:** Rules reset when selecting dropdowns

**Solution:**
- Already fixed: Added `isInternalUpdate` flag to prevent circular updates
- Clear browser cache and reload

#### Program Tiers Not Saving

**Problem:** Tiers created but not visible after refresh

**Solution:**
- Already fixed: `LoyaltyProgramViewSet` handles nested tiers
- Verify tiers are included in save payload
- Check browser console for errors

#### Date Format Warnings

**Error:** `The specified value "2025-01-02T16:17:18.002464Z" does not conform`

**Solution:**
- Already fixed: Date formatting converts ISO to `YYYY-MM-DDTHH:mm`
- Clear browser cache

---

### ML Issues

#### Model Not Found

**Error:** `FileNotFoundError: models/nbo.tflite`

**Solution:**
1. Train models: `python train_models_from_dwh.py`
2. Verify models exist: `ls models/`
3. Check `ML_MODEL_NBO_PATH` in settings

#### Feature Mismatch

**Error:** `ValueError: Feature count mismatch`

**Solution:**
1. Verify `ML_MODEL_INPUT_SIZE` matches model
2. Check `ML_FEATURE_MAPPING` matches DWH columns
3. Ensure all features exist in DWH

---

### DWH Connection Issues

#### Connection Failed

**Error:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
1. Verify PostgreSQL is running
2. Check connection string in settings
3. Verify database exists
4. Check firewall/network access

#### Missing Columns

**Error:** `column "column_name" does not exist`

**Solution:**
1. Verify column names match DWH schema
2. Update `ML_FEATURE_MAPPING` if needed
3. Update JSONLogic rules to use correct names

---

### Segmentation Issues

#### Segment Recalculate Fails

**Error:** `Error evaluating JSONLogic rule`

**Solution:**
1. Verify JSONLogic syntax is correct
2. Check feature names match DWH/Xiva columns
3. Verify DWH/Xiva connection is working
4. Check browser console for detailed errors

#### Empty Segments

**Problem:** Segment has 0 members after recalculate

**Solution:**
1. Verify rules are correct (test with sample customer)
2. Check DWH/Xiva has data for customers
3. Verify feature names match
4. Check segment is set to "Dynamic" not "Static"

---

### Campaign Issues

#### Campaigns Not Triggering

**Problem:** Campaigns exist but no executions

**Solution:**
1. Verify campaign status is "Active"
2. Check triggers are configured correctly
3. Run: `python trigger_campaigns.py`
4. Verify target segment has members

#### Campaign Performance Shows Zero

**Problem:** Campaign metrics show 0

**Solution:**
1. Verify campaigns were triggered
2. Check `CampaignExecution` records exist
3. Verify delivery channels are configured
4. Check campaign is active

---

### Journey Builder Issues

#### Can't Drag Nodes

**Error:** `TypeError: instance.on is not a function`

**Solution:**
- Already fixed: Removed invalid event handler
- Clear browser cache
- Verify Vue Flow is installed: `npm install @vue-flow/core`

#### Node Types Missing

**Error:** `Node type is missing`

**Solution:**
- Already fixed: Custom node types registered
- Clear browser cache
- Reload page

---

## Getting Help

### Check Logs

**Django Server Logs:**
- Check console output for errors
- Look for stack traces

**Browser Console:**
- Open DevTools (F12)
- Check Console tab for errors
- Check Network tab for failed requests

### Debug Mode

Enable debug logging:

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

### Common Commands

```bash
# Reset Xiva client
python manage.py reset_xiva_client

# Check migrations
python manage.py showmigrations

# Create superuser
python manage.py createsuperuser

# Test DWH connection
python test_dwh_connection.py
```

---

## Still Having Issues?

1. Check [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) for setup order
2. Verify all prerequisites are installed
3. Check environment variables are set correctly
4. Review recent changes in git history
5. Check Django and browser console logs

---

## Next Steps

- See [SETUP_GUIDE.md](SETUP_GUIDE.md) for installation
- See [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) for workflow
- See [API_REFERENCE.md](API_REFERENCE.md) for API details

