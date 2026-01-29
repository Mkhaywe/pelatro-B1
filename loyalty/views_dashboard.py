"""
Dashboard views for loyalty microservice
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import AllowAny
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import LoyaltyProgram, LoyaltyAccount, LoyaltyTransaction
from .models_khaywe import Campaign


class DashboardStatsViewSet(ViewSet):
    """
    Dashboard statistics endpoint
    """
    permission_classes = [AllowAny]  # Allow unauthenticated access for development
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get dashboard statistics
        """
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Active programs - count all programs with is_active=True
        active_programs = LoyaltyProgram.objects.filter(is_active=True).count()
        
        # Active campaigns - use raw SQL for placeholder model
        active_campaigns = 0
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM loyalty_campaign 
                    WHERE status = 'active' OR status IS NULL
                """)
                active_campaigns = cursor.fetchone()[0] or 0
        except Exception:
            # Fallback: count all campaigns
            try:
                active_campaigns = Campaign.objects.count()
            except:
                active_campaigns = 0
        
        # Total members (loyalty accounts) - count all accounts (no status field)
        total_members = LoyaltyAccount.objects.count()
        
        # Points issued this month
        points_issued = LoyaltyTransaction.objects.filter(
            transaction_type='earn',
            created_at__gte=start_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Points redeemed this month
        points_redeemed = LoyaltyTransaction.objects.filter(
            transaction_type='redeem',
            created_at__gte=start_of_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Recent transactions (last 10)
        recent_transactions = LoyaltyTransaction.objects.select_related(
            'account', 'account__program'
        ).filter(account__isnull=False).order_by('-created_at')[:10]
        
        # Campaign performance data - use raw SQL for placeholder models
        campaign_performance = []
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                # Get campaign data
                cursor.execute("""
                    SELECT id, name, status FROM loyalty_campaign 
                    WHERE status = 'active' OR status IS NULL
                    ORDER BY id DESC LIMIT 10
                """)
                campaigns = cursor.fetchall()
                
                for camp_id, camp_name, status in campaigns:
                    # Try to get execution stats
                    triggered = 0
                    delivered = 0
                    converted = 0
                    try:
                        cursor.execute("""
                            SELECT COUNT(*) FROM loyalty_campaignexecution 
                            WHERE campaign_id = %s
                        """, [camp_id])
                        triggered = cursor.fetchone()[0] or 0
                        
                        cursor.execute("""
                            SELECT COUNT(*) FROM loyalty_campaignexecution 
                            WHERE campaign_id = %s AND delivered_at IS NOT NULL
                        """, [camp_id])
                        delivered = cursor.fetchone()[0] or 0
                        
                        cursor.execute("""
                            SELECT COUNT(*) FROM loyalty_campaignexecution 
                            WHERE campaign_id = %s AND converted_at IS NOT NULL
                        """, [camp_id])
                        converted = cursor.fetchone()[0] or 0
                    except Exception:
                        pass  # Execution table might not exist
                    
                    campaign_performance.append({
                        'name': (camp_name or f'Campaign {camp_id}')[:30],
                        'triggered': triggered,
                        'delivered': delivered,
                        'converted': converted,
                    })
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error getting campaign performance: {e}")
        
        return Response({
            'active_programs': active_programs,
            'active_campaigns': active_campaigns,
            'total_members': total_members,
            'points_issued_this_month': points_issued,
            'points_redeemed_this_month': points_redeemed,
            'campaign_performance': campaign_performance,
            'recent_activity': [
                {
                    'id': str(tx.id),
                    'customer_id': str(tx.account.customer_id),
                    'program_name': tx.account.program.name,
                    'type': tx.transaction_type,
                    'amount': tx.amount,
                    'description': tx.description or f"{tx.transaction_type} {tx.amount} points",
                    'timestamp': tx.created_at.isoformat(),
                }
                for tx in recent_transactions
            ]
        })
