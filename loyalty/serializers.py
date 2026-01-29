from rest_framework import serializers
from .models import LoyaltyProgram, LoyaltyTier, LoyaltyAccount, LoyaltyTransaction, LoyaltyReward, LoyaltyRedemption, LoyaltyRule, LoyaltyEvent, Promotion, Recommendation, AuditLog, LoyaltyEligibilityRule, LoyaltyEligibilityOverride

class LoyaltyProgramSerializer(serializers.ModelSerializer):
    tiers = serializers.SerializerMethodField()
    
    class Meta:
        model = LoyaltyProgram
        fields = '__all__'
    
    def get_tiers(self, obj):
        """Return nested tiers"""
        from .models import LoyaltyTier
        tiers = LoyaltyTier.objects.filter(program=obj).order_by('priority', 'min_points')
        return LoyaltyTierSerializer(tiers, many=True).data

class LoyaltyTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyTier
        fields = '__all__'

class LoyaltyAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyAccount
        fields = '__all__'

class LoyaltyTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyTransaction
        fields = '__all__'
    
    def create(self, validated_data):
        """Create transaction and update account balance"""
        transaction = super().create(validated_data)
        self._update_account_balance(transaction)
        return transaction
    
    def update(self, instance, validated_data):
        """Update transaction and recalculate account balance"""
        old_amount = instance.amount
        old_type = instance.transaction_type
        
        transaction = super().update(instance, validated_data)
        
        # Reverse the old transaction effect
        self._reverse_transaction_effect(transaction.account, old_amount, old_type)
        
        # Apply the new transaction effect
        self._update_account_balance(transaction)
        
        return transaction
    
    def _update_account_balance(self, transaction):
        """Update the account's points balance based on transaction"""
        account = transaction.account
        amount = transaction.amount
        transaction_type = transaction.transaction_type
        
        if transaction_type in ['earn', 'adjust']:
            # For earn and adjust transactions, add the amount to balance
            account.points_balance += amount
        elif transaction_type == 'redeem':
            # For redeem transactions, subtract the amount from balance
            account.points_balance -= amount
        
        # Ensure balance doesn't go negative
        if account.points_balance < 0:
            account.points_balance = 0
        
        account.save(update_fields=['points_balance'])
    
    def _reverse_transaction_effect(self, account, old_amount, old_type):
        """Reverse the effect of a previous transaction"""
        if old_type in ['earn', 'adjust']:
            # Reverse earn/adjust by subtracting
            account.points_balance -= old_amount
        elif old_type == 'redeem':
            # Reverse redeem by adding back
            account.points_balance += old_amount
        
        # Ensure balance doesn't go negative
        if account.points_balance < 0:
            account.points_balance = 0

class LoyaltyRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyReward
        fields = '__all__'

class LoyaltyRedemptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyRedemption
        fields = '__all__'
    
    def create(self, validated_data):
        """Create redemption with proper validation and point deduction"""
        # Auto-calculate points_used if not provided
        if 'points_used' not in validated_data or validated_data['points_used'] == 0:
            reward = validated_data.get('reward')
            if reward:
                validated_data['points_used'] = getattr(reward, 'points_required', 0) or getattr(reward, 'cost', 0) or 0
        
        # Validate account has sufficient points
        account = validated_data.get('account')
        points_used = validated_data.get('points_used', 0)
        
        if account and points_used > 0:
            if account.points_balance < points_used:
                raise serializers.ValidationError({
                    'detail': f'Insufficient points. Account has {account.points_balance}, but {points_used} required.'
                })
        
        # Create the redemption (model save will handle point deduction)
        return super().create(validated_data)

class LoyaltyRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyRule
        fields = '__all__'

class LoyaltyEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyEvent
        fields = '__all__'

class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = '__all__'

class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = '__all__'

class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'
        ref_name = 'Loyalty_AuditLog'

class LoyaltyEligibilityRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyEligibilityRule
        fields = '__all__'

class LoyaltyEligibilityOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyEligibilityOverride
        fields = '__all__' 