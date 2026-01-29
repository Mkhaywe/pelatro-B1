from rest_framework.routers import DefaultRouter
from .views import (
    LoyaltyProgramViewSet, LoyaltyTierViewSet, LoyaltyAccountViewSet, LoyaltyTransactionViewSet,
    LoyaltyRewardViewSet, LoyaltyRedemptionViewSet, LoyaltyRuleViewSet, LoyaltyEventViewSet,
    PromotionViewSet, RecommendationViewSet, AuditLogViewSet, LoyaltyAnalyticsViewSet, LoyaltyDashboardConfigViewSet,
    LoyaltyEligibilityRuleViewSet, LoyaltyEligibilityOverrideViewSet, EligibilityCheckAPIView,
    BusinessRulesValidateAPIView, ManualReviewAPIView
)
from .views_dwh import DWHIntegrationViewSet
from .views_khaywe import (
    CampaignViewSet, CampaignExecutionViewSet,
    SegmentViewSet, SegmentMemberViewSet, SegmentSnapshotViewSet,
    MissionViewSet, MissionProgressViewSet, BadgeViewSet, BadgeAwardViewSet,
    LeaderboardViewSet, LeaderboardEntryViewSet, StreakViewSet,
    JourneyViewSet, JourneyNodeViewSet, JourneyEdgeViewSet, JourneyExecutionViewSet,
    ExperimentViewSet, ExperimentAssignmentViewSet, HoldoutGroupViewSet,
    PartnerViewSet, PartnerProgramViewSet, PartnerSettlementViewSet, CoalitionViewSet,
    RoleViewSet, PermissionViewSet, RolePermissionViewSet, UserRoleViewSet,
    ApprovalWorkflowViewSet, ApprovalRequestViewSet, ApprovalDecisionViewSet,
    PointsExpiryRuleViewSet, PointsExpiryEventViewSet,
    EarnCapViewSet, CapUsageViewSet,
)

router = DefaultRouter()
router.register(r'loyaltyPrograms', LoyaltyProgramViewSet, basename='loyaltyprogram')
router.register(r'loyaltyTiers', LoyaltyTierViewSet, basename='loyaltytier')
router.register(r'loyaltyAccounts', LoyaltyAccountViewSet, basename='loyaltyaccount')
router.register(r'loyaltyTransactions', LoyaltyTransactionViewSet, basename='loyaltytransaction')
router.register(r'loyaltyRewards', LoyaltyRewardViewSet, basename='loyaltyreward')
router.register(r'loyaltyRedemptions', LoyaltyRedemptionViewSet, basename='loyaltyredemption')
router.register(r'loyaltyRules', LoyaltyRuleViewSet, basename='loyaltyrule')
router.register(r'loyaltyEvents', LoyaltyEventViewSet, basename='loyaltyevent')
router.register(r'promotions', PromotionViewSet, basename='promotion')
router.register(r'recommendations', RecommendationViewSet, basename='recommendation')
router.register(r'auditLogs', AuditLogViewSet, basename='auditlog')
router.register(r'loyaltyAnalytics', LoyaltyAnalyticsViewSet, basename='loyaltyanalytics')
router.register(r'loyaltyDashboardConfig', LoyaltyDashboardConfigViewSet, basename='loyaltydashboardconfig')
router.register(r'loyaltyEligibilityRules', LoyaltyEligibilityRuleViewSet, basename='loyaltyeligibilityrule')
router.register(r'loyaltyEligibilityOverrides', LoyaltyEligibilityOverrideViewSet, basename='loyaltyeligibilityoverride')
router.register(r'dwh', DWHIntegrationViewSet, basename='dwh-integration')

# Khaywe models
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'campaignExecutions', CampaignExecutionViewSet, basename='campaignexecution')
router.register(r'segments', SegmentViewSet, basename='segment')
router.register(r'segmentMembers', SegmentMemberViewSet, basename='segmentmember')
router.register(r'segmentSnapshots', SegmentSnapshotViewSet, basename='segmentsnapshot')
router.register(r'missions', MissionViewSet, basename='mission')
router.register(r'missionProgress', MissionProgressViewSet, basename='missionprogress')
router.register(r'badges', BadgeViewSet, basename='badge')
router.register(r'badgeAwards', BadgeAwardViewSet, basename='badgeaward')
router.register(r'leaderboards', LeaderboardViewSet, basename='leaderboard')
router.register(r'leaderboardEntries', LeaderboardEntryViewSet, basename='leaderboardentry')
router.register(r'streaks', StreakViewSet, basename='streak')
router.register(r'journeys', JourneyViewSet, basename='journey')
router.register(r'journeyNodes', JourneyNodeViewSet, basename='journeynode')
router.register(r'journeyEdges', JourneyEdgeViewSet, basename='journeyedge')
router.register(r'journeyExecutions', JourneyExecutionViewSet, basename='journeyexecution')
router.register(r'experiments', ExperimentViewSet, basename='experiment')
router.register(r'experimentAssignments', ExperimentAssignmentViewSet, basename='experimentassignment')
router.register(r'holdoutGroups', HoldoutGroupViewSet, basename='holdoutgroup')
router.register(r'partners', PartnerViewSet, basename='partner')
router.register(r'partnerPrograms', PartnerProgramViewSet, basename='partnerprogram')
router.register(r'partnerSettlements', PartnerSettlementViewSet, basename='partnersettlement')
router.register(r'coalitions', CoalitionViewSet, basename='coalition')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'rolePermissions', RolePermissionViewSet, basename='rolepermission')
router.register(r'userRoles', UserRoleViewSet, basename='userrole')
router.register(r'approvalWorkflows', ApprovalWorkflowViewSet, basename='approvalworkflow')
router.register(r'approvalRequests', ApprovalRequestViewSet, basename='approvalrequest')
router.register(r'approvalDecisions', ApprovalDecisionViewSet, basename='approvaldecision')
router.register(r'pointsExpiryRules', PointsExpiryRuleViewSet, basename='pointsexpiryrule')
router.register(r'pointsExpiryEvents', PointsExpiryEventViewSet, basename='pointsexpiryevent')
router.register(r'earnCaps', EarnCapViewSet, basename='earncap')
router.register(r'capUsage', CapUsageViewSet, basename='capusage')

urlpatterns = router.urls

# Endpoints:
# GET /loyaltyPrograms/
# GET /loyaltyTiers/
# GET /loyaltyAccounts/?customer={id}
# GET /loyaltyTransactions/?account={id}
# GET /loyaltyRewards/
# POST /loyaltyRedemptions/
# GET /loyaltyRules/
# POST /loyaltyEvents/

# Non-ViewSet endpoints
from django.urls import path
from .views_dashboard import DashboardStatsViewSet
from .views_services import (
    PointsServiceViewSet, EligibilityServiceViewSet, TierServiceViewSet,
    CampaignEngineViewSet, JourneyEngineViewSet, SegmentEngineViewSet
)
from .views_config import ConfigurationViewSet
from .views_gamification import (
    DataSourceConfigViewSet, CustomerEventViewSet,
    CustomerBehaviorScoreViewSet, MissionTemplateViewSet
)
from .views_webhooks import CustomerEventWebhookView, WebhookViewSet
from .views_products import ProductViewSet
from .views_external_systems import ExternalSystemConfigViewSet

dashboard_router = DefaultRouter()
dashboard_router.register(r'dashboard', DashboardStatsViewSet, basename='dashboard-stats')

# Service routers
services_router = DefaultRouter()
services_router.register(r'points', PointsServiceViewSet, basename='points-service')
services_router.register(r'eligibility', EligibilityServiceViewSet, basename='eligibility-service')
services_router.register(r'tier', TierServiceViewSet, basename='tier-service')
services_router.register(r'campaign-engine', CampaignEngineViewSet, basename='campaign-engine')
services_router.register(r'journey-engine', JourneyEngineViewSet, basename='journey-engine')
services_router.register(r'segment-engine', SegmentEngineViewSet, basename='segment-engine')

# Configuration router
config_router = DefaultRouter()
config_router.register(r'config', ConfigurationViewSet, basename='config')

# Gamification router
gamification_router = DefaultRouter()
gamification_router.register(r'data-sources', DataSourceConfigViewSet, basename='data-source-config')
gamification_router.register(r'customer-events', CustomerEventViewSet, basename='customer-event')
gamification_router.register(r'behavior-scores', CustomerBehaviorScoreViewSet, basename='behavior-score')
gamification_router.register(r'mission-templates', MissionTemplateViewSet, basename='mission-template')

# Products router
products_router = DefaultRouter()
products_router.register(r'products', ProductViewSet, basename='product')

# External Systems router
external_systems_router = DefaultRouter()
external_systems_router.register(r'external-systems', ExternalSystemConfigViewSet, basename='external-system-config')

# Webhook router
webhook_router = DefaultRouter()
webhook_router.register(r'webhooks', WebhookViewSet, basename='webhook')

urlpatterns = router.urls + dashboard_router.urls + services_router.urls + config_router.urls + gamification_router.urls + products_router.urls + external_systems_router.urls + webhook_router.urls + [
    path('eligibilityCheck/', EligibilityCheckAPIView.as_view(), name='eligibility-check'),
    path('business-rules/validate/', BusinessRulesValidateAPIView.as_view(), name='business-rules-validate'),
    path('manual-review/', ManualReviewAPIView.as_view(), name='manual-review'),
    # Webhook endpoint (no CSRF for external systems)
    path('webhooks/customer-events/', CustomerEventWebhookView.as_view(), name='customer-event-webhook'),
] 