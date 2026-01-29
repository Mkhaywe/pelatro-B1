# Configuration Architecture: Best Practices

## 🤔 Is `settings.py` the Right Place?

### Current Approach: `settings.py`

**Pros:**
- ✅ Simple and straightforward
- ✅ Easy to access via Django settings
- ✅ Works well for static configuration
- ✅ Version controlled (in Git)

**Cons:**
- ❌ Requires code deployment to change
- ❌ Not dynamic (can't change without restart)
- ❌ Mixes configuration with code
- ❌ UI changes don't persist (SystemSettings component can't save)
- ❌ Not ideal for multi-environment setups

---

## 🎯 Better Approaches

### Option 1: Database Configuration (Recommended) ⭐

Store configuration in the database, similar to `DeliveryChannelConfig`:

**Pros:**
- ✅ Can be changed via UI without code deployment
- ✅ Dynamic (changes take effect immediately)
- ✅ Can have different configs per environment
- ✅ Audit trail (who changed what, when)
- ✅ Can be versioned/historied

**Cons:**
- ❌ Requires database migration
- ❌ Slightly more complex to implement

**Implementation:**
```python
# loyalty/models_khaywe.py
class MLConfiguration(models.Model):
    """ML configuration stored in database"""
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField()
    description = models.TextField(blank=True)
    updated_by = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ml_configuration'
    
    @classmethod
    def get_feature_mapping(cls):
        """Get feature mapping from database"""
        try:
            config = cls.objects.get(key='feature_mapping')
            return config.value
        except cls.DoesNotExist:
            # Fallback to settings.py
            from django.conf import settings
            return getattr(settings, 'ML_FEATURE_MAPPING', {})
    
    @classmethod
    def set_feature_mapping(cls, mapping, updated_by='system'):
        """Save feature mapping to database"""
        config, created = cls.objects.update_or_create(
            key='feature_mapping',
            defaults={
                'value': mapping,
                'description': 'ML feature mapping: DWH columns → model features',
                'updated_by': updated_by,
            }
        )
        return config
```

**Usage:**
```python
# In inference.py
from loyalty.models_khaywe import MLConfiguration

feature_mapping = MLConfiguration.get_feature_mapping()
# Falls back to settings.py if not in database
```

---

### Option 2: Hybrid Approach (Settings + Database Override)

Use `settings.py` for defaults, database for overrides:

**Pros:**
- ✅ Best of both worlds
- ✅ Defaults in code (version controlled)
- ✅ Can override via UI
- ✅ Works even if database is down (uses defaults)

**Implementation:**
```python
# loyalty/ml/inference.py
def get_feature_mapping():
    """Get feature mapping with database override"""
    from django.conf import settings
    
    # Try database first
    try:
        from loyalty.models_khaywe import MLConfiguration
        db_mapping = MLConfiguration.get_feature_mapping()
        if db_mapping:
            return db_mapping
    except:
        pass  # Database not available, use settings
    
    # Fallback to settings.py
    return getattr(settings, 'ML_FEATURE_MAPPING', {})
```

---

### Option 3: Environment Variables + Config File

Use `.env` file or separate config file:

**Pros:**
- ✅ Separates config from code
- ✅ Easy to change per environment
- ✅ No database dependency

**Cons:**
- ❌ Still requires file deployment
- ❌ Not as dynamic as database

**Implementation:**
```bash
# .env file
ML_FEATURE_MAPPING='{"revenue":"total_revenue","transaction_count":"transaction_count"}'
```

---

### Option 4: External Config Service

Use a dedicated configuration service (e.g., Consul, etcd):

**Pros:**
- ✅ Centralized configuration
- ✅ Real-time updates
- ✅ Multi-service support

**Cons:**
- ❌ Additional infrastructure
- ❌ More complex setup

---

## 🏆 Recommended Solution: Hybrid Approach

**Best Practice:**
1. **Defaults in `settings.py`** - Version controlled, always available
2. **Overrides in Database** - Can be changed via UI
3. **Environment Variables** - For sensitive/secrets

### Implementation Plan

#### Step 1: Create Database Model

```python
# loyalty/models_khaywe.py
class SystemConfiguration(models.Model):
    """System-wide configuration stored in database"""
    category = models.CharField(max_length=50)  # 'ml', 'dwh', 'feature_store'
    key = models.CharField(max_length=100)
    value = models.JSONField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    updated_by = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['category', 'key']]
        indexes = [
            models.Index(fields=['category', 'key']),
        ]
    
    @classmethod
    def get_config(cls, category, key, default=None):
        """Get configuration value"""
        try:
            config = cls.objects.get(category=category, key=key, is_active=True)
            return config.value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_config(cls, category, key, value, description='', updated_by='system'):
        """Set configuration value"""
        config, created = cls.objects.update_or_create(
            category=category,
            key=key,
            defaults={
                'value': value,
                'description': description,
                'is_active': True,
                'updated_by': updated_by,
            }
        )
        return config
```

#### Step 2: Create Configuration Service

```python
# loyalty/services/config_service.py
class ConfigurationService:
    """Service to get configuration with fallback to settings.py"""
    
    @staticmethod
    def get_ml_feature_mapping():
        """Get ML feature mapping (database → settings.py → default)"""
        # Try database first
        try:
            from loyalty.models_khaywe import SystemConfiguration
            db_mapping = SystemConfiguration.get_config('ml', 'feature_mapping')
            if db_mapping:
                return db_mapping
        except Exception as e:
            logger.debug(f"Could not load from database: {e}")
        
        # Fallback to settings.py
        from django.conf import settings
        return getattr(settings, 'ML_FEATURE_MAPPING', {})
    
    @staticmethod
    def set_ml_feature_mapping(mapping, updated_by='system'):
        """Save ML feature mapping to database"""
        from loyalty.models_khaywe import SystemConfiguration
        return SystemConfiguration.set_config(
            category='ml',
            key='feature_mapping',
            value=mapping,
            description='ML feature mapping: DWH columns → model features',
            updated_by=updated_by
        )
```

#### Step 3: Update Inference Service

```python
# loyalty/ml/inference.py
from loyalty.services.config_service import ConfigurationService

def _extract_features(self, customer_id: str, ...):
    # Use configuration service instead of direct settings access
    feature_mapping = ConfigurationService.get_ml_feature_mapping()
    # ... rest of code
```

#### Step 4: Update API to Save

```python
# loyalty/views_config.py
@action(detail=False, methods=['post'], url_path='ml')
def update_ml_config(self, request):
    """Update ML configuration"""
    from loyalty.services.config_service import ConfigurationService
    
    feature_mapping = request.data.get('feature_mapping')
    if feature_mapping:
        ConfigurationService.set_ml_feature_mapping(
            feature_mapping,
            updated_by=request.user.username if request.user.is_authenticated else 'api'
        )
    
    return Response({'success': True})
```

---

## 📊 Comparison Table

| Approach | Dynamic | UI Editable | Version Control | Complexity | Best For |
|----------|---------|------------|-----------------|------------|----------|
| `settings.py` | ❌ | ❌ | ✅ | Low | Static config |
| Database | ✅ | ✅ | ⚠️ | Medium | Dynamic config |
| Hybrid | ✅ | ✅ | ✅ | Medium | **Production** ⭐ |
| Env Vars | ⚠️ | ❌ | ✅ | Low | Secrets |
| Config Service | ✅ | ✅ | ⚠️ | High | Microservices |

---

## ✅ Recommendation

**Use Hybrid Approach for Production:**

1. **Keep defaults in `settings.py`** - For version control and fallback
2. **Store overrides in database** - For UI-driven changes
3. **Use environment variables** - For secrets and environment-specific values

This gives you:
- ✅ Version controlled defaults
- ✅ Dynamic UI configuration
- ✅ Fallback if database unavailable
- ✅ Audit trail
- ✅ Multi-environment support

---

## 🚀 Migration Path

**Current State:**
- Configuration in `settings.py` ✅
- UI can read but not save ❌

**Step 1:** Add database model (non-breaking)
**Step 2:** Add configuration service (non-breaking, falls back to settings)
**Step 3:** Update inference to use service (non-breaking)
**Step 4:** Update API to save to database
**Step 5:** UI can now save changes ✅

**No breaking changes** - everything falls back to `settings.py` if database not available!

