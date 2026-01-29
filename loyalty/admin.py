from django.contrib import admin
from .models import LoyaltyProgram, LoyaltyTier, LoyaltyAccount, LoyaltyTransaction, LoyaltyReward, LoyaltyRedemption, LoyaltyRule, LoyaltyEvent, Promotion, Recommendation, AuditLog, LoyaltyEligibilityRule, LoyaltyEligibilityOverride

admin.site.register(LoyaltyProgram)
admin.site.register(LoyaltyTier)
admin.site.register(LoyaltyAccount)
admin.site.register(LoyaltyTransaction)
admin.site.register(LoyaltyReward)
admin.site.register(LoyaltyRedemption)
admin.site.register(LoyaltyRule)
admin.site.register(LoyaltyEvent)
admin.site.register(Promotion)
admin.site.register(Recommendation)
admin.site.register(AuditLog)
admin.site.register(LoyaltyEligibilityRule)
admin.site.register(LoyaltyEligibilityOverride) 