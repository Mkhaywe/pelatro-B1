from django.db import models
from django.utils import timezone
from decimal import Decimal
from uuid import uuid4

# Note: Segment, SegmentMember, Campaign, and other Khaywe models are in models_khaywe.py
# Import them from there: from loyalty.models_khaywe import Segment, SegmentMember


# ============================================================================
# CORE LOYALTY MODELS
# ============================================================================

class LoyaltyProgram(models.Model):
    """Loyalty program definition"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class LoyaltyTier(models.Model):
    """Tier levels within a loyalty program"""
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name='tiers')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    min_points = models.PositiveIntegerField(default=0)
    benefits = models.TextField(blank=True)
    priority = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['priority', 'min_points']
    
    def __str__(self):
        return f"{self.program.name} - {self.name}"


class LoyaltyAccount(models.Model):
    """Customer loyalty account"""
    customer_id = models.UUIDField(db_index=True, unique=True)
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name='accounts')
    tier = models.ForeignKey(LoyaltyTier, on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts')
    points_balance = models.PositiveIntegerField(default=0)
    lifetime_points_earned = models.PositiveIntegerField(default=0)
    lifetime_points_redeemed = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['customer_id', 'program']]
        indexes = [
            models.Index(fields=['customer_id']),
            models.Index(fields=['program', 'tier']),
        ]
    
    def __str__(self):
        return f"Account: {self.customer_id} ({self.program.name})"


class LoyaltyTransaction(models.Model):
    """Points transaction (earn/redeem/adjust)"""
    TRANSACTION_TYPES = [
        ('earn', 'Earn'),
        ('redeem', 'Redeem'),
        ('adjust', 'Adjust'),
    ]
    
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='transactions')
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type}: {self.amount} points"


class LoyaltyReward(models.Model):
    """Rewards available for redemption"""
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name='rewards')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    points_required = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.points_required} points)"


class LoyaltyRedemption(models.Model):
    """Reward redemption record"""
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='redemptions')
    reward = models.ForeignKey(LoyaltyReward, on_delete=models.CASCADE, related_name='redemptions')
    points_used = models.PositiveIntegerField(default=0, help_text="Points used for this redemption. Auto-calculated from reward if 0.")
    status = models.CharField(max_length=50, default='pending')
    notes = models.TextField(blank=True, null=True, help_text="Additional notes for this redemption")
    redemption_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Redemption: {self.reward.name} by {self.account.customer_id}"


class LoyaltyRule(models.Model):
    """Business rules for loyalty program"""
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name='rules')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=100, help_text="earn, redeem, tier, etc.")
    logic = models.JSONField(help_text="JSONLogic expression")
    value = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.rule_type}: {self.name}"


class LoyaltyEvent(models.Model):
    """Event log for loyalty activities"""
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='events', null=True, blank=True)
    event_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    points_delta = models.IntegerField(default=0)
    metadata = models.JSONField(blank=True, null=True, help_text="Additional event metadata")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.created_at}"


class Promotion(models.Model):
    """Promotional campaigns"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    eligibility_criteria = models.TextField(blank=True, help_text="Describe eligibility or use JSON")
    event_triggers = models.JSONField(blank=True, default=list, help_text="List of event triggers that activate this promotion. Format: [{'type': 'customer_login', 'conditions': {...}}, ...]")
    trigger_frequency = models.CharField(
        max_length=20,
        choices=[
            ('once', 'Once per customer'),
            ('daily', 'Once per day'),
            ('weekly', 'Once per week'),
            ('unlimited', 'Unlimited'),
        ],
        default='unlimited',
        help_text="How often this promotion can be triggered per customer"
    )
    reward = models.ForeignKey(LoyaltyReward, on_delete=models.SET_NULL, null=True, blank=True, related_name='promotions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def matches_event(self, event_type, event_data=None):
        """Check if promotion matches an event"""
        for trigger in self.event_triggers:
            if trigger.get('type') == event_type:
                conditions = trigger.get('conditions', {})
                if conditions and event_data:
                    # Evaluate JSONLogic conditions
                    try:
                        from loyalty.utils import safe_json_logic
                        return safe_json_logic(conditions, event_data)
                    except:
                        return False
                return True
        return False
    
    def __str__(self):
        return self.name


class Recommendation(models.Model):
    """Customer recommendations"""
    customer_id = models.UUIDField(db_index=True)
    recommended_offering = models.CharField(max_length=255)
    reason = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Recommendation for {self.customer_id}: {self.recommended_offering}"


class AuditLog(models.Model):
    """Audit trail for system changes"""
    actor_id = models.CharField(max_length=100, blank=True, null=True)
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    changes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['object_type', 'object_id']),
            models.Index(fields=['actor_id', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action} {self.object_type} {self.object_id}"


class LoyaltyEligibilityRule(models.Model):
    """Eligibility rules for loyalty program"""
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name='eligibility_rules')
    name = models.CharField(max_length=255)
    logic = models.JSONField(help_text="JSONLogic expression for eligibility")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.program.name} - {self.name}"


class LoyaltyEligibilityOverride(models.Model):
    """Manual eligibility overrides for specific customers"""
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE)
    customer_id = models.UUIDField(unique=True)
    force_eligible = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Override for {self.customer_id}: {self.force_eligible}"


# ============================================================================
# OFFER CATALOG (for ML predictions)
# ============================================================================

class Offer(models.Model):
    """Offer catalog for ML predictions and campaign management"""
    offer_id = models.IntegerField(unique=True, help_text="Numeric ID used by ML models (0-7 for NBO)")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('points', 'Points'),
            ('discount', 'Discount'),
            ('shipping', 'Free Shipping'),
            ('access', 'VIP Access'),
            ('special', 'Special Event'),
            ('referral', 'Referral'),
            ('sale', 'Sale'),
            ('tier', 'Tier Upgrade'),
            ('retention', 'Retention'),
            ('acquisition', 'Acquisition'),
        ],
        default='points'
    )
    is_active = models.BooleanField(default=True)
    
    # CLM (Customer Lifecycle Management) fields
    lifecycle_stage = models.CharField(
        max_length=50,
        choices=[
            ('acquisition', 'Acquisition'),
            ('onboarding', 'Onboarding'),
            ('growth', 'Growth'),
            ('retention', 'Retention'),
            ('win_back', 'Win-back'),
            ('churn', 'Churn Risk'),
        ],
        blank=True,
        null=True,
        help_text="Target lifecycle stage for this offer"
    )
    
    # CVM (Customer Value Management) fields
    target_value_segment = models.CharField(
        max_length=50,
        choices=[
            ('high_value', 'High Value'),
            ('medium_value', 'Medium Value'),
            ('low_value', 'Low Value'),
            ('all', 'All Segments'),
        ],
        default='all'
    )
    min_customer_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_customer_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # External system sync
    external_offer_id = models.CharField(max_length=255, blank=True, help_text="ID in external system (Xiva, CRM, etc.)")
    external_system = models.CharField(
        max_length=50,
        choices=[
            ('xiva', 'Xiva'),
            ('crm', 'CRM'),
            ('manual', 'Manual'),
        ],
        default='manual'
    )
    last_synced = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['offer_id']
        indexes = [
            models.Index(fields=['offer_id', 'is_active']),
            models.Index(fields=['lifecycle_stage', 'is_active']),
            models.Index(fields=['target_value_segment', 'is_active']),
        ]
    
    def __str__(self):
        return f"Offer #{self.offer_id}: {self.name}"


# ============================================================================
# CLM/CVM MODELS (from migration 0006)
# ============================================================================

class CustomerLifecycleStage(models.Model):
    """Customer lifecycle stage tracking"""
    STAGE_CHOICES = [
        ('acquisition', 'Acquisition'),
        ('onboarding', 'Onboarding'),
        ('growth', 'Growth'),
        ('retention', 'Retention'),
        ('win_back', 'Win-back'),
        ('churn_risk', 'Churn Risk'),
        ('churned', 'Churned'),
    ]
    
    customer_id = models.UUIDField(db_index=True)
    stage = models.CharField(max_length=50, choices=STAGE_CHOICES)
    entered_at = models.DateTimeField(auto_now_add=True)
    exited_at = models.DateTimeField(null=True, blank=True)
    duration_days = models.IntegerField(null=True, blank=True)
    transition_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-entered_at']
        indexes = [
            models.Index(fields=['customer_id', '-entered_at']),
            models.Index(fields=['stage', 'entered_at']),
        ]
    
    def __str__(self):
        return f"{self.customer_id} - {self.stage}"


class CustomerValueSegment(models.Model):
    """Customer value segmentation"""
    SEGMENT_CHOICES = [
        ('high_value', 'High Value'),
        ('medium_value', 'Medium Value'),
        ('low_value', 'Low Value'),
    ]
    
    customer_id = models.UUIDField(db_index=True, unique=True)
    segment = models.CharField(max_length=50, choices=SEGMENT_CHOICES)
    lifetime_value = models.DecimalField(max_digits=10, decimal_places=2)
    predicted_ltv = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    value_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="0-100 score")
    rfm_segment = models.CharField(max_length=50, blank=True)
    calculated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-value_score']
        indexes = [
            models.Index(fields=['segment', '-value_score']),
            models.Index(fields=['customer_id']),
        ]
    
    def __str__(self):
        return f"{self.customer_id} - {self.segment}"


# ============================================================================
# PRODUCT CATALOG (for campaigns and offerings)
# ============================================================================

class Product(models.Model):
    """Product/Plan catalog from external systems (Xiva, CRM, Billing, etc.)"""
    PRODUCT_TYPES = [
        ('voice', 'Voice Plan'),
        ('data', 'Data Plan'),
        ('sms', 'SMS Plan'),
        ('bundle', 'Bundle Plan'),
        ('device', 'Device'),
        ('service', 'Service'),
        ('addon', 'Add-on'),
    ]
    
    # External system reference
    external_product_id = models.CharField(max_length=255, help_text="Product ID in external system")
    external_system = models.CharField(
        max_length=50,
        choices=[
            ('xiva', 'Xiva'),
            ('crm', 'CRM'),
            ('billing', 'Billing/OCS'),
            ('manual', 'Manual'),
        ],
        default='manual'
    )
    
    # Product details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    product_type = models.CharField(max_length=50, choices=PRODUCT_TYPES, default='bundle')
    category = models.CharField(max_length=100, blank=True, help_text="Product category (e.g., 'Postpaid', 'Prepaid')")
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    recurring = models.BooleanField(default=False, help_text="Is this a recurring subscription?")
    billing_cycle = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
            ('one_time', 'One-time'),
        ],
        default='monthly'
    )
    
    # Features/Attributes
    features = models.JSONField(default=dict, blank=True, help_text="Product features (data allowance, minutes, etc.)")
    attributes = models.JSONField(default=dict, blank=True, help_text="Additional attributes (brand, model, etc.)")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True, help_text="Available for purchase")
    
    # Targeting (for campaigns)
    target_segments = models.JSONField(default=list, blank=True, help_text="Target customer segments")
    min_customer_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_customer_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Sync metadata
    last_synced = models.DateTimeField(null=True, blank=True)
    sync_frequency = models.CharField(
        max_length=20,
        choices=[
            ('realtime', 'Real-time'),
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('manual', 'Manual'),
        ],
        default='daily'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['external_product_id', 'external_system']),
            models.Index(fields=['product_type', 'is_active']),
            models.Index(fields=['is_active', 'is_available']),
        ]
        unique_together = [['external_product_id', 'external_system']]
    
    def __str__(self):
        return f"{self.name} ({self.external_system})"
