"""
TMF (TM Forum) serializers.
Maps internal models to TMF-compliant JSON structure.
"""

from rest_framework import serializers
from loyalty.models import LoyaltyAccount, LoyaltyProgram, LoyaltyTransaction, LoyaltyReward, LoyaltyTier


class RelatedPartySerializer(serializers.Serializer):
    """TMF RelatedParty structure"""
    id = serializers.CharField()
    href = serializers.CharField(required=False)
    role = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    
    def to_representation(self, instance):
        """Add @referredType to output"""
        ret = super().to_representation(instance)
        if 'referred_type' in ret:
            ret['@referredType'] = ret.pop('referred_type')
        return ret


class LoyaltyAccountTMFSerializer(serializers.ModelSerializer):
    """TMF-compliant LoyaltyAccount serializer"""
    
    # TMF fields
    id = serializers.CharField(source='id')
    href = serializers.SerializerMethodField()
    status = serializers.CharField(source='status')
    balance = serializers.IntegerField(source='points_balance')
    
    # Related party (customer)
    relatedParty = serializers.SerializerMethodField()
    
    # Loyalty program reference
    loyaltyProgram = serializers.SerializerMethodField()
    
    # Tier reference
    loyaltyTier = serializers.SerializerMethodField()
    
    class Meta:
        model = LoyaltyAccount
        fields = [
            'id', 'href', 'status', 'balance',
            'relatedParty', 'loyaltyProgram', 'loyaltyTier',
            'created_at', 'updated_at'
        ]
    
    def get_href(self, obj):
        return f"/tmf-api/loyaltyManagement/v4/loyaltyAccount/{obj.id}"
    
    def get_relatedParty(self, obj):
        """Map customer_id to TMF RelatedParty"""
        return [{
            'id': str(obj.customer_id),
            'role': 'customer',
            '@referredType': 'Customer'
        }]
    
    def get_loyaltyProgram(self, obj):
        """Map program to TMF reference"""
        return {
            'id': str(obj.program.id),
            'href': f"/tmf-api/loyaltyManagement/v4/loyaltyProgram/{obj.program.id}",
            'name': obj.program.name
        }
    
    def get_loyaltyTier(self, obj):
        """Map tier to TMF reference"""
        if obj.tier:
            return {
                'id': str(obj.tier.id),
                'name': obj.tier.name,
                'minPoints': obj.tier.min_points
            }
        return None


class LoyaltyProgramTMFSerializer(serializers.ModelSerializer):
    """TMF-compliant LoyaltyProgram serializer"""
    
    id = serializers.CharField(source='id')
    href = serializers.SerializerMethodField()
    name = serializers.CharField()
    description = serializers.CharField()
    status = serializers.SerializerMethodField()
    validFor = serializers.SerializerMethodField()
    
    class Meta:
        model = LoyaltyProgram
        fields = [
            'id', 'href', 'name', 'description', 'status',
            'validFor', 'created_at', 'updated_at'
        ]
    
    def get_href(self, obj):
        return f"/tmf-api/loyaltyManagement/v4/loyaltyProgram/{obj.id}"
    
    def get_status(self, obj):
        return 'active' if obj.is_active else 'inactive'
    
    def get_validFor(self, obj):
        """TMF validFor structure"""
        return {
            'startDateTime': obj.start_date.isoformat() if obj.start_date else None,
            'endDateTime': obj.end_date.isoformat() if obj.end_date else None
        }


class LoyaltyTransactionTMFSerializer(serializers.ModelSerializer):
    """TMF-compliant LoyaltyTransaction serializer"""
    
    id = serializers.CharField(source='id')
    href = serializers.SerializerMethodField()
    amount = serializers.IntegerField()
    transactionType = serializers.CharField(source='transaction_type')
    description = serializers.CharField()
    date = serializers.DateTimeField(source='created_at')
    
    # Account reference
    loyaltyAccount = serializers.SerializerMethodField()
    
    class Meta:
        model = LoyaltyTransaction
        fields = [
            'id', 'href', 'amount', 'transactionType',
            'description', 'date', 'loyaltyAccount'
        ]
    
    def get_href(self, obj):
        return f"/tmf-api/loyaltyManagement/v4/loyaltyTransaction/{obj.id}"
    
    def get_loyaltyAccount(self, obj):
        return {
            'id': str(obj.account.id),
            'href': f"/tmf-api/loyaltyManagement/v4/loyaltyAccount/{obj.account.id}"
        }

