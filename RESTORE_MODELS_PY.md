# How to Restore models.py

## ⚠️ **CRITICAL: models.py was overwritten**

The `loyalty/models.py` file was accidentally overwritten and needs to be restored.

## 🔧 **Solution**

### **Option 1: Restore from Backup**
If you have a backup, restore it and add the `Product` model.

### **Option 2: Recreate from Migrations**
The migrations show what models should exist. Recreate `models.py` with:

1. **Core Models** (from migration 0001):
   - LoyaltyProgram
   - LoyaltyTier
   - LoyaltyAccount
   - LoyaltyTransaction
   - LoyaltyReward
   - LoyaltyRedemption
   - LoyaltyRule
   - LoyaltyEvent
   - Promotion
   - Recommendation
   - AuditLog
   - LoyaltyEligibilityRule
   - LoyaltyEligibilityOverride

2. **Additional Models** (from migration 0006):
   - Offer
   - CustomerLifecycleStage
   - CustomerValueSegment

3. **New Model to Add**:
   - Product (for product catalog)

### **Option 3: Use Django's inspectdb**
If you have a working database:
```bash
python manage.py inspectdb > loyalty/models_restored.py
```

Then manually add the Product model.

---

## ✅ **What's Already Fixed**

1. **ML Model Return Keys** ✅
   - `propensity_score` added
   - `response_prediction` added
   - `default_risk_score` added

2. **Product Model Definition** ✅
   - Model structure created (needs to be added to restored models.py)

---

## 🎯 **Next Steps After Restoring models.py**

1. Add Product model to restored file
2. Run: `python manage.py makemigrations`
3. Run: `python manage.py migrate`
4. Create Product service, API, and Frontend (see COMPLETE_FIX_SUMMARY.md)

