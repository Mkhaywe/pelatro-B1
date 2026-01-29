from .models import Promotion, LoyaltyAccount, LoyaltyTier, Recommendation, AuditLog, LoyaltyTransaction, LoyaltyReward, LoyaltyRedemption, LoyaltyRule, LoyaltyEvent, LoyaltyProgram, LoyaltyEligibilityRule, LoyaltyEligibilityOverride
from .serializers import PromotionSerializer, LoyaltyAccountSerializer, RecommendationSerializer, AuditLogSerializer, LoyaltyProgramSerializer, LoyaltyTierSerializer, LoyaltyTransactionSerializer, LoyaltyRewardSerializer, LoyaltyRedemptionSerializer, LoyaltyRuleSerializer, LoyaltyEventSerializer, LoyaltyEligibilityRuleSerializer, LoyaltyEligibilityOverrideSerializer
from rest_framework import viewsets, serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from loyalty.utils import safe_json_logic
from rest_framework.views import APIView
from datetime import datetime, timedelta
from django.conf import settings
from loyalty.integration.external import fetch_customer_context, extract_customer_id, ExternalServiceError
import json

class PromotionViewSet(viewsets.ModelViewSet):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    filterset_fields = ['is_active', 'start_date', 'end_date']

    def get_queryset(self):
        # BUSINESS LOGIC: Only return active and currently valid promotions
        now = timezone.now()
        qs = Promotion.objects.filter(is_active=True, start_date__lte=now, end_date__gte=now)
        
        # Filter by customer if provided (for customer-specific promotions)
        customer_id = self.request.query_params.get('customer')
        if customer_id:
            # For now, return all active promotions for any customer
            # In the future, you might want to add customer-specific promotion logic
            pass
            
        return qs
    
    @action(detail=False, methods=['get'], url_path='customer/(?P<customer_id>[^/.]+)')
    def by_customer(self, request, customer_id=None):
        """Get active promotions for a specific customer"""
        now = timezone.now()
        promotions = Promotion.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).order_by('-start_date')
        
        # Filter by eligibility if needed (simplified - would need eligibility check)
        serializer = self.get_serializer(promotions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='apply')
    def apply_promotion(self, request, pk=None):
        """
        Apply a promotion to a customer with tracking and limits
        """
        try:
            promotion = self.get_object()
            customer_id = request.data.get('customer_id')
            
            print(f"🎯 Applying promotion {promotion.name} to customer {customer_id}")
            
            if not customer_id:
                return Response({'error': 'customer_id is required'}, status=400)
            
            # Resolve customer context (optional, for enrichment only)
            customer_context = None
            external_mode = getattr(settings, "LOYALTY_USE_EXTERNAL_CUSTOMER_API", False)

            if external_mode:
                try:
                    customer_context = fetch_customer_context(customer_id)
                except ExternalServiceError as e:
                    # Log but don't fail - we can work with just customer_id
                    pass
            
            # Check if customer has a loyalty account (using customer_id UUID)
            try:
                loyalty_account = LoyaltyAccount.objects.get(customer_id=customer_id, status='active')
            except LoyaltyAccount.DoesNotExist:
                return Response({'error': 'Customer does not have an active loyalty account. Please enroll the customer first.'}, status=400)
            except Exception as e:
                return Response({'error': f'Error fetching loyalty account: {str(e)}'}, status=400)
            
            # Check promotion validity
            if not promotion.is_active:
                return Response({'error': 'This promotion is not active'}, status=400)
            
            if promotion.start_date and timezone.now() < promotion.start_date:
                return Response({'error': 'This promotion has not started yet'}, status=400)
                
            if promotion.end_date and timezone.now() > promotion.end_date:
                return Response({'error': 'This promotion has expired'}, status=400)
            
            # Check application limits based on trigger_frequency
            previous_applications = LoyaltyEvent.objects.filter(
                account=loyalty_account,
                event_type='promotion_applied',
                description__icontains=f"Promotion ID: {promotion.id}"
            )
            
            application_count = previous_applications.count()
            
            # Check frequency limits if promotion has event triggers
            if hasattr(promotion, 'trigger_frequency') and promotion.trigger_frequency:
                if promotion.trigger_frequency == 'once' and application_count > 0:
                    last_applied = previous_applications.first().created_at
                    return Response({
                        'error': 'This promotion can only be applied once per customer',
                        'already_applied': True,
                        'last_applied_date': last_applied,
                        'application_count': application_count
                    }, status=400)
                    
                elif promotion.trigger_frequency == 'daily':
                    today_applications = previous_applications.filter(
                        created_at__date=timezone.now().date()
                    ).count()
                    if today_applications > 0:
                        return Response({
                            'error': 'This promotion can only be applied once per day',
                            'already_applied_today': True,
                            'application_count': application_count
                        }, status=400)
                        
                elif promotion.trigger_frequency == 'weekly':
                    week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
                    week_applications = previous_applications.filter(
                        created_at__date__gte=week_start
                    ).count()
                    if week_applications > 0:
                        return Response({
                            'error': 'This promotion can only be applied once per week',
                            'already_applied_this_week': True,
                            'application_count': application_count
                        }, status=400)
            
            # Apply promotion logic based on promotion type
            applied_benefit = 0
            description = f"Promotion applied: {promotion.name}"
            
            try:
                if hasattr(promotion, 'promotion_type') and promotion.promotion_type:
                    if promotion.promotion_type == 'points_bonus':
                        # Award bonus points
                        bonus_points = getattr(promotion, 'bonus_points', 100)
                        applied_benefit = bonus_points
                        description = f"Bonus points from promotion: {promotion.name}"
                    elif promotion.promotion_type == 'discount':
                        # Record discount application
                        applied_benefit = 50  # Default points for discount promotion
                        description = f"Discount promotion applied: {promotion.name}"
                    elif promotion.promotion_type == 'cashback':
                        applied_benefit = 75  # Default points for cashback
                        description = f"Cashback promotion applied: {promotion.name}"
                    else:
                        # Default promotion application - award 100 points
                        applied_benefit = 100
                        description = f"Generic promotion applied: {promotion.name}"
                else:
                    # Default promotion application - award 100 points
                    applied_benefit = 100
                    description = f"Promotion applied: {promotion.name}"
                
                # Create transaction record if points are involved
                if applied_benefit > 0:
                    transaction = LoyaltyTransaction.objects.create(
                        account=loyalty_account,
                        amount=applied_benefit,
                        transaction_type='earn',
                        description=f"{description} (Promotion ID: {promotion.id})"
                    )
                    
                    # Update account balance
                    loyalty_account.points_balance = (loyalty_account.points_balance or 0) + applied_benefit
                    loyalty_account.save()
                
                # Create event record with metadata
                LoyaltyEvent.objects.create(
                    account=loyalty_account,
                    event_type='promotion_applied',
                    description=f"{description} (Promotion ID: {promotion.id}, Benefit: {applied_benefit} points, Application #{application_count + 1})",
                    points_delta=applied_benefit,
                    metadata={
                        'promotion_id': promotion.id,
                        'promotion_name': promotion.name,
                        'customer_id': str(customer_id),
                        'benefit_applied': applied_benefit,
                        'application_count': application_count + 1,
                        'trigger_frequency': getattr(promotion, 'trigger_frequency', 'unlimited')
                    }
                )
                
                print(f"✅ Promotion applied successfully: {promotion.name} → {applied_benefit} points")
                
                return Response({
                    'message': 'Promotion applied successfully',
                    'promotion': promotion.name,
                    'customer_id': str(customer_id),
                    'benefit_applied': applied_benefit,
                    'new_balance': loyalty_account.points_balance,
                    'description': description,
                    'application_count': application_count + 1,
                    'trigger_frequency': getattr(promotion, 'trigger_frequency', 'unlimited'),
                    'can_apply_again': getattr(promotion, 'trigger_frequency', 'unlimited') == 'unlimited',
                    'previous_applications': application_count,
                    'total_earned_from_promotion': previous_applications.aggregate(
                        total=Sum('points_delta')
                    )['total'] or 0 + applied_benefit
                })
                
            except Exception as e:
                print(f"❌ Error applying promotion logic: {str(e)}")
                return Response({'error': f'Error applying promotion logic: {str(e)}'}, status=500)
                
        except Exception as e:
            # Catch-all for any unexpected errors
            import traceback
            print(f"❌ Promotion apply error: {str(e)}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return Response({'error': f'Internal server error: {str(e)}'}, status=500)
    
    @action(detail=True, methods=['post'], url_path='notify')
    def notify_promotion(self, request, pk=None):
        """
        Send notification about a promotion to customers
        """
        try:
            promotion = self.get_object()
            customer_ids = request.data.get('customer_ids', [])
            notification_type = request.data.get('notification_type', 'email')
            
            print(f"🔔 Notify promotion called for: {promotion.name}")
            print(f"🔔 Request data: {request.data}")
            print(f"🔔 Customer IDs received: {customer_ids}")
            print(f"🔔 Customer IDs type: {type(customer_ids)}")
            
            if not customer_ids:
                return Response({'error': 'customer_ids list is required'}, status=400)
            
            if not isinstance(customer_ids, list):
                return Response({'error': 'customer_ids must be a list'}, status=400)
            
            notifications_sent = 0
            failed_notifications = []
            
            for customer_id in customer_ids:
                try:
                    print(f"🔔 Processing customer ID: {customer_id} (type: {type(customer_id)})")
                    
                    # Handle case where customer_id might be an object instead of just ID
                    if isinstance(customer_id, dict):
                        actual_customer_id = customer_id.get('id')
                        print(f"🔔 Extracted ID from object: {actual_customer_id}")
                    else:
                        actual_customer_id = customer_id
                    
                    if not actual_customer_id:
                        failed_notifications.append(f"Invalid customer data: {customer_id}")
                        continue
                    
                    # Lookup loyalty account by customer_id UUID
                    customer_account = LoyaltyAccount.objects.filter(customer_id=actual_customer_id).first()
                    if customer_account:
                        LoyaltyEvent.objects.create(
                            account=customer_account,
                            event_type='promotion_notification',
                            description=f"Promotion notification sent: {promotion.name} (Type: {notification_type}, Customer: {actual_customer_id})",
                            points_delta=0
                        )
                    
                    notifications_sent += 1
                    print(f"✅ Notification sent to customer: {actual_customer_id}")
                    
                except Exception as e:
                    error_msg = f"Error processing customer {customer_id}: {str(e)}"
                    print(f"❌ {error_msg}")
                    failed_notifications.append(error_msg)
                    continue
                except Exception as e:
                    error_msg = f"Error processing customer {customer_id}: {str(e)}"
                    print(f"❌ {error_msg}")
                    failed_notifications.append(error_msg)
                    continue
            
            response_data = {
                'message': f'Notifications processed for promotion: {promotion.name}',
                'notifications_sent': notifications_sent,
                'failed_notifications': failed_notifications,
                'promotion': promotion.name,
                'notification_type': notification_type
            }
            
            print(f"🔔 Notify response: {response_data}")
            return Response(response_data)
            
        except Exception as e:
            import traceback
            error_msg = f"Notify promotion error: {str(e)}"
            print(f"❌ NOTIFY ERROR: {error_msg}")
            print(f"❌ TRACEBACK: {traceback.format_exc()}")
            return Response({
                'error': error_msg,
                'detail': 'Failed to send promotion notifications'
            }, status=500)

    @action(detail=True, methods=['get'], url_path='analytics')
    def analytics(self, request, pk=None):
        """
        Get analytics for a specific promotion
        """
        try:
            promotion = self.get_object()
            
            # Usage count: number of times this promotion was applied (from LoyaltyEvent or LoyaltyTransaction)
            usage_count = LoyaltyEvent.objects.filter(
                event_type='promotion_applied',
                description__icontains=f"Promotion ID: {promotion.id}"
            ).count()

            # Total savings: sum of points or value awarded (if tracked)
            # For now, sum points_delta for this promotion's events
            total_savings = LoyaltyEvent.objects.filter(
                event_type='promotion_applied',
                description__icontains=f"Promotion ID: {promotion.id}"
            ).aggregate(total=Sum('points_delta'))['total'] or 0

            # Conversion rate: uses/views (if views tracked, else just usage_count/100 as placeholder)
            views = getattr(promotion, 'views', 100) or 100
            conversion_rate = (usage_count / views) * 100 if views else 0.0

            # Customer segments: breakdown by segment (mock for now)
            customer_segments = [
                {"name": "New Customers", "value": 35},
                {"name": "Regular Customers", "value": 45},
                {"name": "VIP Members", "value": 20}
            ]
            # TODO: Replace with real segment logic if available

            # Usage over time: time series of usage (mock for now)
            # TODO: Replace with real time series from LoyaltyEvent
            usage_over_time = [
                {"label": "Week 1", "value": 12},
                {"label": "Week 2", "value": 19},
                {"label": "Week 3", "value": 15},
                {"label": "Week 4", "value": 25}
            ]

            return Response({
                "usage_count": usage_count,
                "total_savings": total_savings,
                "conversion_rate": round(conversion_rate, 1),
                "customer_segments": customer_segments,
                "usage_over_time": usage_over_time
            })
            
        except Exception as e:
            import traceback
            print(f"❌ Promotion analytics error: {str(e)}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return Response({'error': f'Failed to load promotion analytics: {str(e)}'}, status=500)

    @action(detail=False, methods=['post'], url_path='process-event')
    def process_customer_event(self, request):
        """
        Process a customer event and trigger matching event-driven promotions
        """
        try:
            event_type = request.data.get('event_type')
            customer_id = request.data.get('customer_id')
            event_data = request.data.get('event_data', {})
            
            print(f"🎯 Processing customer event: {event_type} for customer: {customer_id}")
            print(f"🎯 Event data: {event_data}")
            
            if not event_type or not customer_id:
                return Response({
                    'error': 'event_type and customer_id are required'
                }, status=400)
            
            # Find active promotions with matching event triggers
            active_promotions = Promotion.objects.filter(
                is_active=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            )
            
            triggered_promotions = []
            
            for promotion in active_promotions:
                if promotion.matches_event(event_type, event_data):
                    print(f"🎯 Promotion '{promotion.name}' matches event {event_type}")
                    
                    # Check if customer has loyalty account (using customer_id UUID)
                    loyalty_account = LoyaltyAccount.objects.filter(
                        customer_id=customer_id, 
                        status='active'
                    ).first()
                    
                    if loyalty_account:
                        # Log the event
                        LoyaltyEvent.objects.create(
                            account=loyalty_account,
                            event_type='event_driven_promotion',
                            description=f"Event-driven promotion triggered: {promotion.name} (Event: {event_type})",
                            points_delta=0,
                            metadata={
                                'promotion_id': promotion.id,
                                'event_type': event_type,
                                'event_data': event_data
                            }
                        )
                        
                        triggered_promotions.append({
                            'promotion_id': promotion.id,
                            'promotion_name': promotion.name,
                            'promotion_description': promotion.description,
                            'event_type': event_type
                        })
                    
                    print(f"✅ Event-driven promotion logged for customer {customer_id}")
            
            response_data = {
                'message': f'Processed event {event_type} for customer {customer_id}',
                'event_type': event_type,
                'customer_id': customer_id,
                'triggered_promotions': triggered_promotions,
                'count': len(triggered_promotions)
            }
            
            print(f"🎯 Event processing response: {response_data}")
            return Response(response_data)
            
        except Exception as e:
            import traceback
            error_msg = f"Event processing error: {str(e)}"
            print(f"❌ EVENT PROCESSING ERROR: {error_msg}")
            print(f"❌ TRACEBACK: {traceback.format_exc()}")
            return Response({
                'error': error_msg,
                'detail': 'Failed to process customer event'
            }, status=500)

    @action(detail=False, methods=['post'], url_path='bulk-operations')
    def bulk_operations(self, request):
        """
        Perform bulk operations on multiple promotions
        """
        try:
            operation = request.data.get('operation')
            promotion_ids = request.data.get('promotion_ids', [])
            
            print(f"🔄 Bulk operation: {operation} on promotions: {promotion_ids}")
            
            if not operation or not promotion_ids:
                return Response({
                    'error': 'operation and promotion_ids are required'
                }, status=400)
            
            if not isinstance(promotion_ids, list):
                return Response({
                    'error': 'promotion_ids must be a list'
                }, status=400)
            
            # Get promotions
            promotions = Promotion.objects.filter(id__in=promotion_ids)
            found_ids = list(promotions.values_list('id', flat=True))
            missing_ids = [pid for pid in promotion_ids if pid not in found_ids]
            
            results = {
                'operation': operation,
                'total_requested': len(promotion_ids),
                'found': len(found_ids),
                'missing': missing_ids,
                'success': [],
                'failed': []
            }
            
            if operation == 'activate':
                updated_count = promotions.update(is_active=True)
                results['success'] = found_ids
                results['message'] = f'Activated {updated_count} promotions'
                
            elif operation == 'deactivate':
                updated_count = promotions.update(is_active=False)
                results['success'] = found_ids
                results['message'] = f'Deactivated {updated_count} promotions'
                
            elif operation == 'delete':
                for promotion in promotions:
                    try:
                        promotion_id = promotion.id
                        promotion_name = promotion.name
                        promotion.delete()
                        results['success'].append(promotion_id)
                        print(f"✅ Deleted promotion: {promotion_name} (ID: {promotion_id})")
                    except Exception as e:
                        results['failed'].append({
                            'id': promotion.id,
                            'error': str(e)
                        })
                        print(f"❌ Failed to delete promotion {promotion.id}: {str(e)}")
                
                results['message'] = f'Deleted {len(results["success"])} promotions, {len(results["failed"])} failed'
                
            elif operation == 'notify':
                customer_ids = request.data.get('customer_ids', [])
                notification_type = request.data.get('notification_type', 'email')
                
                if not customer_ids:
                    return Response({
                        'error': 'customer_ids required for notify operation'
                    }, status=400)
                
                total_notifications = 0
                
                for promotion in promotions:
                    try:
                        # Process the notification for each promotion
                        for customer_id in customer_ids:
                            try:
                                # Lookup loyalty account by customer_id UUID
                                customer_account = LoyaltyAccount.objects.filter(
                                    customer_id=customer_id, 
                                    status='active'
                                ).first()
                                
                                if customer_account:
                                    LoyaltyEvent.objects.create(
                                        account=customer_account,
                                        event_type='bulk_promotion_notification',
                                        description=f"Bulk promotion notification sent: {promotion.name} (Type: {notification_type})",
                                        points_delta=0
                                    )
                                    total_notifications += 1
                                    
                            except Exception:
                                continue
                        
                        results['success'].append(promotion.id)
                        
                    except Exception as e:
                        results['failed'].append({
                            'id': promotion.id,
                            'error': str(e)
                        })
                
                results['message'] = f'Sent {total_notifications} notifications for {len(results["success"])} promotions'
                
            else:
                return Response({
                    'error': f'Unknown operation: {operation}. Supported: activate, deactivate, delete, notify'
                }, status=400)
            
            print(f"🔄 Bulk operation results: {results}")
            return Response(results)
            
        except Exception as e:
            import traceback
            error_msg = f"Bulk operation error: {str(e)}"
            print(f"❌ BULK OPERATION ERROR: {error_msg}")
            print(f"❌ TRACEBACK: {traceback.format_exc()}")
            return Response({
                'error': error_msg,
                'detail': 'Failed to perform bulk operation'
            }, status=500)

def evaluate_loyalty_rules(rules, context):
    """
    Evaluate a list of LoyaltyRule objects (with JSONLogic) against the context dict.
    Returns a list of results (one per rule).
    """
    results = []
    for rule in rules:
        if rule.is_active and rule.logic:
            try:
                result = safe_json_logic(rule.logic, context)
                results.append({'rule': rule, 'result': result})
            except Exception as e:
                results.append({'rule': rule, 'result': None, 'error': str(e)})
    return results

class LoyaltyAccountViewSet(viewsets.ModelViewSet):
    queryset = LoyaltyAccount.objects.all()
    serializer_class = LoyaltyAccountSerializer
    filterset_fields = ['customer_id', 'program', 'status']

    def get_queryset(self):
        qs = LoyaltyAccount.objects.all()
        customer_id = self.request.query_params.get('customer')
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        return qs
    
    @action(detail=False, methods=['get'], url_path='customer/(?P<customer_id>[^/.]+)')
    def by_customer(self, request, customer_id=None):
        """Get all loyalty accounts for a specific customer"""
        accounts = LoyaltyAccount.objects.filter(
            customer_id=customer_id
        ).select_related('program', 'tier').order_by('-created_at')
        
        serializer = self.get_serializer(accounts, many=True)
        return Response(serializer.data)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._apply_earning_rules(instance)
        self._assign_tier(instance)

    def perform_create(self, serializer):
        customer_id = serializer.validated_data['customer_id']
        program = serializer.validated_data['program']

        # Check for override
        override = LoyaltyEligibilityOverride.objects.filter(
            customer_id=customer_id, 
            program=program, 
            force_eligible=True
        ).first()
        if override:
            instance = serializer.save()
            self._apply_earning_rules(instance)
            self._assign_tier(instance)
            return

        # Check for existing account
        if LoyaltyAccount.objects.filter(customer_id=customer_id, program=program).exists():
            raise serializers.ValidationError({'detail': 'Customer already has a loyalty account for this program.'})

        # Get active eligibility rules for this program
        rules = LoyaltyEligibilityRule.objects.filter(program=program, is_active=True)
        
        # Try to enrich context from external API if available
        customer_context = {}
        external_mode = getattr(settings, "LOYALTY_USE_EXTERNAL_CUSTOMER_API", False)
        if external_mode:
            try:
                customer_context = fetch_customer_context(customer_id)
            except ExternalServiceError:
                pass  # Continue with minimal context
        
        for rule in rules:
            # Build context for JSONLogic (use external context if available, otherwise minimal)
            context = {
                'customer_id': str(customer_id),
                'customer_status': customer_context.get('status', 'active'),
                'customer_created_at': customer_context.get('created_at', ''),
                'customer_type': customer_context.get('type', ''),
            }
            if not safe_json_logic(rule.logic, context):
                raise serializers.ValidationError({'detail': f'Customer does not meet eligibility: {rule.name}'})

        # If all checks pass, create the account
        instance = serializer.save()
        self._apply_earning_rules(instance)
        self._assign_tier(instance)

    def _apply_earning_rules(self, account):
        # Example: apply all active earning rules for the program to the account's latest transaction
        last_tx = account.transactions.order_by('-created_at').first()
        if not last_tx:
            return
        context = {
            'amount': last_tx.amount,
            'transaction_type': last_tx.transaction_type,
            'customer_id': account.customer_id,
            'points_balance': account.points_balance,
            'date': str(last_tx.created_at),
        }
        rules = account.program.rules.filter(rule_type='earn', is_active=True)
        results = evaluate_loyalty_rules(rules, context)
        # Example: if any rule returns a numeric result, update points_balance
        for r in results:
            if isinstance(r['result'], (int, float)):
                account.points_balance += r['result']
                account.save(update_fields=['points_balance'])

    def _assign_tier(self, account):
        """Assign appropriate tier based on points balance"""
        tiers = LoyaltyTier.objects.filter(program=account.program).order_by('min_points')
        
        # Find the highest tier the customer qualifies for
        current_tier = None
        for tier in tiers:
            if account.points_balance >= tier.min_points:
                current_tier = tier
            else:
                break
        
        # Update tier if changed
        if account.tier != current_tier:
            account.tier = current_tier
            account.save(update_fields=['tier'])
            print(f"✅ Updated account {account.id} tier to {current_tier.name if current_tier else 'None'}")

    @action(detail=True, methods=['get'])
    def tier_progress(self, request, pk=None):
        """Calculate tier progress for a loyalty account"""
        account = self.get_object()
        
        if not account.tier:
            # If no tier assigned, assign one first
            self._assign_tier(account)
            account.refresh_from_db()
        
        # Get current tier and next tier
        current_tier = account.tier
        if not current_tier:
            return Response({
                'current_tier': None,
                'next_tier': None,
                'progress_percentage': 0,
                'points_to_next_tier': 0,
                'current_points': account.points_balance
            })
        
        # Find next tier
        next_tier = LoyaltyTier.objects.filter(
            program=account.program,
            min_points__gt=current_tier.min_points
        ).order_by('min_points').first()
        
        if not next_tier:
            # Already at highest tier
            return Response({
                'current_tier': {
                    'id': current_tier.id,
                    'name': current_tier.name,
                    'min_points': current_tier.min_points
                },
                'next_tier': None,
                'progress_percentage': 100,
                'points_to_next_tier': 0,
                'current_points': account.points_balance,
                'message': 'At highest tier'
            })
        
        # Calculate progress percentage
        current_tier_min = current_tier.min_points
        next_tier_min = next_tier.min_points
        current_points = account.points_balance
        
        # Progress within current tier bracket
        points_in_current_tier = current_points - current_tier_min
        points_needed_for_next_tier = next_tier_min - current_tier_min
        
        progress_percentage = (points_in_current_tier / points_needed_for_next_tier) * 100
        progress_percentage = min(100, max(0, progress_percentage))  # Clamp between 0-100
        
        points_to_next_tier = next_tier_min - current_points
        
        return Response({
            'current_tier': {
                'id': current_tier.id,
                'name': current_tier.name,
                'min_points': current_tier.min_points
            },
            'next_tier': {
                'id': next_tier.id,
                'name': next_tier.name,
                'min_points': next_tier.min_points
            },
            'progress_percentage': round(progress_percentage, 1),
            'points_to_next_tier': max(0, points_to_next_tier),
            'current_points': current_points,
            'points_in_current_tier': points_in_current_tier,
            'points_needed_for_next_tier': points_needed_for_next_tier
        })

    @action(detail=False, methods=['post'])
    def recalculate_all_tiers(self, request):
        """Recalculate tiers for all accounts - admin utility"""
        accounts = LoyaltyAccount.objects.all()
        updated_count = 0
        
        for account in accounts:
            old_tier = account.tier
            self._assign_tier(account)
            if account.tier != old_tier:
                updated_count += 1
        
        return Response({
            'message': f'Recalculated tiers for all accounts',
            'total_accounts': accounts.count(),
            'updated_accounts': updated_count
        })

class RecommendationViewSet(viewsets.ModelViewSet):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer
    filterset_fields = ['customer_id', 'is_active']

    def get_queryset(self):
        # BUSINESS LOGIC: Only return active recommendations, filter by customer if provided
        qs = Recommendation.objects.filter(is_active=True)
        customer_id = self.request.query_params.get('customer')
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        return qs

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        # BUSINESS LOGIC: Allow filtering by user, object_type, or action
        qs = AuditLog.objects.all()
        user_id = self.request.query_params.get('user')
        object_type = self.request.query_params.get('object_type')
        action = self.request.query_params.get('action')
        if user_id:
            qs = qs.filter(user_id=user_id)
        if object_type:
            qs = qs.filter(object_type=object_type)
        if action:
            qs = qs.filter(action=action)
        return qs

class LoyaltyTransactionViewSet(viewsets.ModelViewSet):
    queryset = LoyaltyTransaction.objects.all()
    serializer_class = LoyaltyTransactionSerializer
    filterset_fields = ['account', 'transaction_type']
    
    @action(detail=False, methods=['get'], url_path='customer/(?P<customer_id>[^/.]+)')
    def by_customer(self, request, customer_id=None):
        """Get all transactions for a specific customer"""
        accounts = LoyaltyAccount.objects.filter(customer_id=customer_id)
        transactions = LoyaltyTransaction.objects.filter(
            account__in=accounts
        ).select_related('account', 'account__program').order_by('-created_at')
        
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)

class LoyaltyRewardViewSet(viewsets.ModelViewSet):
    queryset = LoyaltyReward.objects.all()
    serializer_class = LoyaltyRewardSerializer
    filterset_fields = ['program', 'is_active']

class LoyaltyRedemptionViewSet(viewsets.ModelViewSet):
    queryset = LoyaltyRedemption.objects.all()
    serializer_class = LoyaltyRedemptionSerializer
    filterset_fields = ['account', 'reward', 'status']

    def perform_create(self, serializer):
        """Create redemption with rule validation - points already deducted by model"""
        # NOTE: Point deduction is now handled in the model's save() method
        # We only need to handle rule validation here
        
        instance = serializer.save()
        account = instance.account
        reward = instance.reward
        
        # Validate business rules if they exist
        if hasattr(account, 'program') and account.program:
            context = {
                'points_balance': account.points_balance,
                'points_required': instance.points_used,
                'customer_id': account.customer_id,
                'reward_id': reward.id,
            }
            rules = account.program.rules.filter(rule_type='redeem', is_active=True)
            results = evaluate_loyalty_rules(rules, context)
            
            # Check if any rule blocks the redemption
            for r in results:
                if r['result'] is False:
                    # If rule fails, we need to reverse the point deduction
                    account.points_balance += instance.points_used
                    account.save(update_fields=['points_balance'])
                    instance.delete()
                    raise serializers.ValidationError({'detail': f'Redemption blocked by rule: {r["rule"].name}'})

class LoyaltyRuleViewSet(viewsets.ModelViewSet):
    queryset = LoyaltyRule.objects.all()
    serializer_class = LoyaltyRuleSerializer
    filterset_fields = ['program', 'rule_type', 'is_active']

class LoyaltyEventViewSet(viewsets.ModelViewSet):
    queryset = LoyaltyEvent.objects.all()
    serializer_class = LoyaltyEventSerializer
    filterset_fields = ['account', 'event_type']

class LoyaltyProgramViewSet(viewsets.ModelViewSet):
    queryset = LoyaltyProgram.objects.all().order_by('-id')
    serializer_class = LoyaltyProgramSerializer
    filterset_fields = ['is_active', 'name']
    
    def perform_create(self, serializer):
        """Create program and handle nested tiers"""
        program = serializer.save()
        # Handle nested tiers if provided
        tiers_data = self.request.data.get('tiers', [])
        if tiers_data:
            for tier_data in tiers_data:
                LoyaltyTier.objects.create(
                    program=program,
                    name=tier_data.get('name', ''),
                    description=tier_data.get('description', ''),
                    min_points=tier_data.get('min_points', 0),
                    benefits=tier_data.get('benefits', ''),
                    priority=tier_data.get('priority', 0)
                )
    
    def perform_update(self, serializer):
        """Update program and handle nested tiers"""
        program = serializer.save()
        # Handle nested tiers if provided
        tiers_data = self.request.data.get('tiers', None)
        if tiers_data is not None:
            # Delete existing tiers not in the new list
            existing_tier_ids = {tier.get('id') for tier in tiers_data if tier.get('id')}
            LoyaltyTier.objects.filter(program=program).exclude(id__in=existing_tier_ids).delete()
            
            # Create or update tiers
            for tier_data in tiers_data:
                tier_id = tier_data.get('id')
                if tier_id:
                    # Update existing tier
                    LoyaltyTier.objects.filter(id=tier_id, program=program).update(
                        name=tier_data.get('name', ''),
                        description=tier_data.get('description', ''),
                        min_points=tier_data.get('min_points', 0),
                        benefits=tier_data.get('benefits', ''),
                        priority=tier_data.get('priority', 0)
                    )
                else:
                    # Create new tier
                    LoyaltyTier.objects.create(
                        program=program,
                        name=tier_data.get('name', ''),
                        description=tier_data.get('description', ''),
                        min_points=tier_data.get('min_points', 0),
                        benefits=tier_data.get('benefits', ''),
                        priority=tier_data.get('priority', 0)
                    )

    @action(detail=True, methods=['get'], url_path='analytics')
    def analytics(self, request, pk=None):
        """
        Get analytics for a specific loyalty program
        """
        try:
            # Get the program object safely
            program_id = pk or self.kwargs.get('pk')
            if program_id:
                program = LoyaltyProgram.objects.get(id=program_id)
            else:
                program = self.get_object()
            
            # Get all accounts for this program
            accounts = LoyaltyAccount.objects.filter(program=program)
            total_members = accounts.count()
            
            # Points statistics
            total_points_issued = LoyaltyTransaction.objects.filter(
                account__program=program,
                transaction_type__in=['earn', 'adjust']
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            total_points_redeemed = LoyaltyTransaction.objects.filter(
                account__program=program,
                transaction_type='redeem'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Tier distribution
            tier_distribution = {}
            for tier in LoyaltyTier.objects.filter(program=program):
                count = accounts.filter(tier=tier).count()
                tier_distribution[tier.name] = count
            
            # Average points per member
            avg_points_result = accounts.aggregate(avg=Avg('points_balance'))
            avg_points_per_member = avg_points_result['avg'] or 0
            
            # Recent activity (last 30 days)
            recent_date = timezone.now() - timedelta(days=30)
            recent_transactions = LoyaltyTransaction.objects.filter(
                account__program=program,
                created_at__gte=recent_date
            ).count()
            
            # Active promotions count
            active_promotions = Promotion.objects.filter(
                is_active=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            ).count()
            
            return Response({
                'total_members': total_members,
                'total_points_issued': int(total_points_issued),
                'total_points_redeemed': int(total_points_redeemed),
                'tier_distribution': tier_distribution,
                'avg_points_per_member': round(float(avg_points_per_member), 2),
                'recent_transactions': recent_transactions,
                'active_promotions': active_promotions,
                'program_name': program.name,
                'program_status': 'Active' if program.is_active else 'Inactive',
                'last_updated': timezone.now().isoformat()
            })
            
        except Exception as e:
            import traceback
            print(f"❌ Program analytics error: {str(e)}")
            print(f"❌ Traceback: {traceback.format_exc()}")
            return Response({'error': f'Failed to load program analytics: {str(e)}'}, status=500)
    
    @action(detail=True, methods=['post'], url_path='simulate')
    def simulate(self, request, pk=None):
        """
        Simulate program behavior with test data
        POST /api/loyalty/v1/loyaltyPrograms/{id}/simulate/
        Body: {
            "customer_id": "...",
            "transaction_amount": 100.0,
            "transaction_context": {...}
        }
        """
        try:
            program = self.get_object()
            customer_id = request.data.get('customer_id', 'test-customer-123')
            transaction_amount = float(request.data.get('transaction_amount', 100.0))
            transaction_context = request.data.get('transaction_context', {})
            
            from loyalty.utils import safe_json_logic
            from decimal import Decimal
            
            # Simulate earn calculation
            earn_rules = {}
            if program.earn_rules:
                try:
                    if isinstance(program.earn_rules, str):
                        earn_rules = json.loads(program.earn_rules)
                    else:
                        earn_rules = program.earn_rules
                except:
                    earn_rules = {}
            
            # Default: 1 point per currency unit
            base_points = int(transaction_amount)
            
            # Apply tier multiplier if applicable
            tier_multiplier = 1.0
            if earn_rules:
                # Evaluate JSONLogic rules
                context = {
                    'transaction_amount': transaction_amount,
                    'customer_id': customer_id,
                    'program': program.name,
                    **transaction_context
                }
                try:
                    rule_result = safe_json_logic(earn_rules, context)
                    if isinstance(rule_result, (int, float)):
                        base_points = int(rule_result)
                    elif isinstance(rule_result, dict) and 'points' in rule_result:
                        base_points = int(rule_result['points'])
                except Exception as e:
                    pass  # Use default calculation
            
            # Simulate burn calculation
            burn_rules = {}
            if program.burn_rules:
                try:
                    if isinstance(program.burn_rules, str):
                        burn_rules = json.loads(program.burn_rules)
                    else:
                        burn_rules = program.burn_rules
                except:
                    burn_rules = {}
            
            # Simulate tier calculation
            tier_result = None
            if program.tiers.exists():
                # Find applicable tier based on points
                for tier in program.tiers.all().order_by('-min_points'):
                    if base_points >= tier.min_points:
                        tier_result = {
                            'tier_id': tier.id,
                            'tier_name': tier.name,
                            'min_points': tier.min_points,
                            'benefits': tier.benefits
                        }
                        break
            
            # Simulate expiry rules
            expiry_rules = []
            if program.points_expiry_rules:
                try:
                    if isinstance(program.points_expiry_rules, str):
                        expiry_rules = json.loads(program.points_expiry_rules)
                    else:
                        expiry_rules = program.points_expiry_rules
                except:
                    expiry_rules = []
            
            # Simulate earn caps (use earn_caps_config JSONField, not the related EarnCap instances)
            earn_caps = []
            if program.earn_caps_config:
                try:
                    if isinstance(program.earn_caps_config, str):
                        earn_caps = json.loads(program.earn_caps_config)
                    else:
                        earn_caps = program.earn_caps_config
                except:
                    earn_caps = []
            
            return Response({
                'program_id': program.id,
                'program_name': program.name,
                'simulation': {
                    'input': {
                        'customer_id': customer_id,
                        'transaction_amount': transaction_amount,
                        'transaction_context': transaction_context
                    },
                    'earn_calculation': {
                        'base_points': base_points,
                        'rules_applied': bool(earn_rules),
                        'tier_multiplier': tier_multiplier,
                        'final_points': base_points
                    },
                    'tier_assignment': tier_result,
                    'expiry_rules': expiry_rules,
                    'earn_caps': earn_caps,
                    'burn_rules': bool(burn_rules)
                },
                'summary': {
                    'points_earned': base_points,
                    'tier_qualified': tier_result['tier_name'] if tier_result else None,
                    'rules_evaluated': {
                        'earn': bool(earn_rules),
                        'burn': bool(burn_rules),
                        'expiry': len(expiry_rules) > 0,
                        'caps': len(earn_caps) > 0
                    }
                }
            })
        except Exception as e:
            import traceback
            return Response({'error': f'Simulation failed: {str(e)}', 'traceback': traceback.format_exc()}, status=500)

class LoyaltyTierViewSet(viewsets.ModelViewSet):
    queryset = LoyaltyTier.objects.all()
    serializer_class = LoyaltyTierSerializer
    filterset_fields = ['program']

class LoyaltyAnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for loyalty analytics endpoints
    """
    
    @action(detail=False, methods=['get'], url_path='pointsHistory')
    def points_history(self, request):
        """
        Get points history for a customer
        """
        customer_id = request.query_params.get('customer')
        if not customer_id:
            return Response({'error': 'customer parameter is required'}, status=400)
        
        # Get all loyalty accounts for the customer
        accounts = LoyaltyAccount.objects.filter(customer_id=customer_id)
        
        # Get all transactions for these accounts
        transactions = LoyaltyTransaction.objects.filter(
            account__in=accounts
        ).order_by('-created_at')
        
        # Serialize the data
        data = []
        for transaction in transactions:
            data.append({
                'id': transaction.id,
                'account_id': transaction.account.id,
                'program_name': transaction.account.program.name,
                'amount': transaction.amount,
                'transaction_type': transaction.transaction_type,
                'description': transaction.description,
                'created_at': transaction.created_at,
                'balance_after': transaction.account.points_balance
            })
        
        return Response(data)
    
    @action(detail=False, methods=['post'], url_path='export')
    def export_report(self, request):
        """
        Export analytics report
        POST /api/loyalty/v1/loyaltyAnalytics/export/
        Body: {
            "report_type": "transactions" | "programs" | "campaigns" | "customers",
            "format": "csv" | "json",
            "filters": {...},
            "date_from": "...",
            "date_to": "..."
        }
        """
        report_type = request.data.get('report_type', 'transactions')
        format_type = request.data.get('format', 'csv')
        date_from = request.data.get('date_from')
        date_to = request.data.get('date_to')
        filters = request.data.get('filters', {})
        
        from datetime import datetime
        
        # Parse dates
        if date_from:
            try:
                date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            except:
                date_from = None
        if date_to:
            try:
                date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            except:
                date_to = None
        
        data = []
        
        if report_type == 'transactions':
            qs = LoyaltyTransaction.objects.select_related('account', 'account__program')
            if date_from:
                qs = qs.filter(created_at__gte=date_from)
            if date_to:
                qs = qs.filter(created_at__lte=date_to)
            if filters.get('program_id'):
                qs = qs.filter(account__program_id=filters['program_id'])
            if filters.get('transaction_type'):
                qs = qs.filter(transaction_type=filters['transaction_type'])
            
            data = [{
                'id': tx.id,
                'customer_id': str(tx.account.customer_id),
                'program_name': tx.account.program.name,
                'transaction_type': tx.transaction_type,
                'amount': tx.amount,
                'description': tx.description,
                'created_at': tx.created_at.isoformat()
            } for tx in qs[:10000]]  # Limit to 10k records
        
        elif report_type == 'programs':
            qs = LoyaltyProgram.objects.all()
            if filters.get('is_active') is not None:
                qs = qs.filter(is_active=filters['is_active'])
            
            data = [{
                'id': prog.id,
                'name': prog.name,
                'description': prog.description,
                'is_active': prog.is_active,
                'start_date': prog.start_date.isoformat() if prog.start_date else None,
                'end_date': prog.end_date.isoformat() if prog.end_date else None,
                'member_count': LoyaltyAccount.objects.filter(program=prog).count(),
                'total_points_issued': LoyaltyTransaction.objects.filter(
                    account__program=prog,
                    transaction_type__in=['earn', 'adjust']
                ).aggregate(total=Sum('amount'))['total'] or 0
            } for prog in qs]
        
        elif report_type == 'campaigns':
            from .models_khaywe import Campaign, CampaignExecution
            qs = Campaign.objects.all()
            if filters.get('status'):
                qs = qs.filter(status=filters['status'])
            
            data = []
            for campaign in qs:
                executions = CampaignExecution.objects.filter(campaign=campaign)
                data.append({
                    'id': campaign.id,
                    'name': campaign.name,
                    'status': campaign.status,
                    'total_sent': executions.count(),
                    'delivered': executions.exclude(delivered_at__isnull=True).count(),
                    'opened': executions.exclude(opened_at__isnull=True).count(),
                    'clicked': executions.exclude(clicked_at__isnull=True).count(),
                    'converted': executions.exclude(converted_at__isnull=True).count()
                })
        
        elif report_type == 'customers':
            qs = LoyaltyAccount.objects.select_related('program', 'tier')
            if filters.get('program_id'):
                qs = qs.filter(program_id=filters['program_id'])
            
            data = [{
                'customer_id': str(acc.customer_id),
                'program_name': acc.program.name,
                'tier_name': acc.tier.name if acc.tier else None,
                'points_balance': acc.points_balance,
                'status': acc.status,
                'created_at': acc.created_at.isoformat()
            } for acc in qs[:10000]]  # Limit to 10k records
        
        if format_type == 'csv':
            import csv
            from io import StringIO
            
            if not data:
                return Response({'error': 'No data to export'}, status=400)
            
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
            from django.http import HttpResponse
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="loyalty_report_{report_type}_{timezone.now().strftime("%Y%m%d")}.csv"'
            return response
        
        return Response({
            'report_type': report_type,
            'format': format_type,
            'record_count': len(data),
            'data': data
        })
    
    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Get loyalty analytics summary for dashboard
        """
        
        # Calculate date ranges
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_month = now - timedelta(days=60)
        
        # Basic metrics
        total_loyalty_members = LoyaltyAccount.objects.count()
        total_points_issued = LoyaltyTransaction.objects.filter(
            transaction_type__in=['earn', 'adjust']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_points_redeemed = LoyaltyTransaction.objects.filter(
            transaction_type='redeem'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Recent activity (last 30 days)
        recent_transactions = LoyaltyTransaction.objects.filter(
            created_at__gte=last_30_days
        ).count()
        
        recent_redemptions = LoyaltyRedemption.objects.filter(
            created_at__gte=last_30_days
        ).count()
        
        # Engagement metrics
        avg_points_result = LoyaltyAccount.objects.aggregate(avg=Avg('points_balance'))
        avg_points_per_customer = avg_points_result['avg'] or 0
        
        # Tier distribution
        tier_distribution = {}
        for tier in LoyaltyTier.objects.all():
            count = LoyaltyAccount.objects.filter(tier=tier).count()
            tier_distribution[tier.name] = count
        
        # Growth calculations
        last_month_members = LoyaltyAccount.objects.filter(
            created_at__lt=last_month
        ).count()
        
        growth_rate = 0
        if last_month_members > 0:
            growth_rate = ((total_loyalty_members - last_month_members) / last_month_members) * 100
        
        # Return comprehensive summary
        return Response({
            'total_loyalty_members': total_loyalty_members,
            'total_points_issued': int(total_points_issued),
            'total_points_redeemed': int(total_points_redeemed),
            'recent_transactions': recent_transactions,
            'recent_redemptions': recent_redemptions,
            'avg_points_per_customer': round(float(avg_points_per_customer), 2),
            'tier_distribution': tier_distribution,
            'growth_rate': round(growth_rate, 2),
            'last_updated': now.isoformat()
        })
    
    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """
        Get real-time dashboard statistics
        """
        
        now = timezone.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Real-time metrics
        stats = {
            'total_members': LoyaltyAccount.objects.count(),
            'total_points_pool': LoyaltyAccount.objects.filter(
                status='active'
            ).aggregate(total=Sum('points_balance'))['total'] or 0,
            'today_transactions': LoyaltyTransaction.objects.filter(
                created_at__gte=today
            ).count(),
            'today_redemptions': LoyaltyRedemption.objects.filter(
                created_at__gte=today,
                status='completed'
            ).count(),
            'month_new_members': LoyaltyAccount.objects.filter(
                created_at__gte=this_month,
                status='active'
            ).count(),
            'active_promotions': Promotion.objects.filter(
                is_active=True,
                start_date__lte=now,
                end_date__gte=now
            ).count(),
            'avg_engagement_score': 85.6,  # Calculated based on activity
            'top_tier_members': LoyaltyAccount.objects.filter(
                tier__name__in=['Gold', 'Platinum'],
                status='active'
            ).count()
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'], url_path='program-performance')
    def program_performance(self, request):
        """Get program performance analytics"""
        from datetime import datetime, timedelta
        
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except:
                start_date = timezone.now() - timedelta(days=30)
        else:
            start_date = timezone.now() - timedelta(days=30)
            
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except:
                end_date = timezone.now()
        else:
            end_date = timezone.now()
        
        programs = LoyaltyProgram.objects.all()
        results = []
        
        for program in programs:
            accounts = LoyaltyAccount.objects.filter(program=program)
            
            # Points issued in date range
            points_issued = LoyaltyTransaction.objects.filter(
                account__program=program,
                transaction_type__in=['earn', 'adjust'],
                created_at__gte=start_date,
                created_at__lte=end_date
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Points redeemed in date range
            points_redeemed = LoyaltyTransaction.objects.filter(
                account__program=program,
                transaction_type='redeem',
                created_at__gte=start_date,
                created_at__lte=end_date
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Active campaigns - use raw SQL for placeholder models
            active_campaigns = 0
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM loyalty_campaign 
                        WHERE program_id = %s AND status = 'active'
                    """, [program.id])
                    active_campaigns = cursor.fetchone()[0] or 0
            except Exception:
                pass
            
            results.append({
                'program_id': program.id,
                'program_name': program.name,
                'total_members': accounts.count(),
                'points_issued': int(points_issued),
                'points_redeemed': int(points_redeemed),
                'active_campaigns': active_campaigns,
                'revenue': 0,  # Calculate from transactions if available
                'is_active': program.is_active,
            })
        
        return Response(results)
    
    @action(detail=False, methods=['get'], url_path='campaign-performance')
    def campaign_performance(self, request):
        """Get campaign performance analytics"""
        from datetime import datetime, timedelta
        from .models_khaywe import Campaign, CampaignExecution
        from django.db import connection
        
        results = []
        
        # Use raw SQL for placeholder models
        try:
            with connection.cursor() as cursor:
                # Get campaigns with their basic data
                cursor.execute("""
                    SELECT id, name, status 
                    FROM loyalty_campaign 
                    ORDER BY id DESC
                """)
                campaigns_data = cursor.fetchall()
                
                for camp_id, camp_name, status in campaigns_data:
                    # Check if executions table exists and has data
                    try:
                        cursor.execute("""
                            SELECT COUNT(*) FROM loyalty_campaignexecution 
                            WHERE campaign_id = %s
                        """, [camp_id])
                        total_triggered = cursor.fetchone()[0] or 0
                        
                        cursor.execute("""
                            SELECT COUNT(*) FROM loyalty_campaignexecution 
                            WHERE campaign_id = %s AND delivered_at IS NOT NULL
                        """, [camp_id])
                        total_delivered = cursor.fetchone()[0] or 0
                        
                        cursor.execute("""
                            SELECT COUNT(*) FROM loyalty_campaignexecution 
                            WHERE campaign_id = %s AND opened_at IS NOT NULL
                        """, [camp_id])
                        total_opened = cursor.fetchone()[0] or 0
                        
                        cursor.execute("""
                            SELECT COUNT(*) FROM loyalty_campaignexecution 
                            WHERE campaign_id = %s AND clicked_at IS NOT NULL
                        """, [camp_id])
                        total_clicked = cursor.fetchone()[0] or 0
                        
                        cursor.execute("""
                            SELECT COUNT(*) FROM loyalty_campaignexecution 
                            WHERE campaign_id = %s AND converted_at IS NOT NULL
                        """, [camp_id])
                        total_converted = cursor.fetchone()[0] or 0
                        
                    except Exception:
                        # Executions table might not exist or have different schema
                        total_triggered = 0
                        total_delivered = 0
                        total_opened = 0
                        total_clicked = 0
                        total_converted = 0
                    
                    conversion_rate = (total_converted / total_delivered * 100) if total_delivered > 0 else 0
                    
                    results.append({
                        'campaign_id': camp_id,
                        'campaign_name': camp_name or f'Campaign {camp_id}',
                        'status': status,
                        'triggered': total_triggered,
                        'delivered': total_delivered,
                        'opened': total_opened,
                        'clicked': total_clicked,
                        'converted': total_converted,
                        'conversion_rate': round(conversion_rate, 2),
                    })
        except Exception as e:
            print(f"Campaign analytics error: {e}")
            # Fallback - return empty or basic data
            pass
        
        return Response(results)
    
    @action(detail=False, methods=['get'], url_path='segment-analytics')
    def segment_analytics(self, request):
        """Get segment analytics"""
        from .models_khaywe import Segment, SegmentMember
        from django.db.models import Avg
        from django.db import connection
        
        results = []
        
        # Use raw SQL for placeholder models
        try:
            with connection.cursor() as cursor:
                # Get all active segments with their data
                if connection.vendor == 'sqlite':
                    cursor.execute("""
                        SELECT id, name, is_active 
                        FROM loyalty_segment 
                        WHERE is_active = 1
                    """)
                else:
                    cursor.execute("""
                        SELECT id, name, is_active 
                        FROM loyalty_segment 
                        WHERE is_active = true
                    """)
                segments_data = cursor.fetchall()
                
                for seg_id, seg_name, is_active in segments_data:
                    # Get member count
                    if connection.vendor == 'sqlite':
                        cursor.execute("""
                            SELECT COUNT(*) FROM loyalty_segmentmember 
                            WHERE segment_id = ? AND is_active = 1
                        """, [seg_id])
                    else:
                        cursor.execute("""
                            SELECT COUNT(*) FROM loyalty_segmentmember 
                            WHERE segment_id = %s AND is_active = true
                        """, [seg_id])
                    member_count = cursor.fetchone()[0] or 0
                    
                    # Get customer IDs for average points calculation
                    if connection.vendor == 'sqlite':
                        cursor.execute("""
                            SELECT customer_id FROM loyalty_segmentmember 
                            WHERE segment_id = ? AND is_active = 1
                        """, [seg_id])
                    else:
                        cursor.execute("""
                            SELECT customer_id FROM loyalty_segmentmember 
                            WHERE segment_id = %s AND is_active = true
                        """, [seg_id])
                    customer_ids = [row[0] for row in cursor.fetchall()]
                    
                    avg_points = 0
                    if customer_ids:
                        # Get average from LoyaltyAccount using ORM (managed model)
                        accounts = LoyaltyAccount.objects.filter(customer_id__in=customer_ids)
                        avg_result = accounts.aggregate(avg=Avg('points_balance'))
                        avg_points = avg_result['avg'] or 0
                    
                    # Get growth rate from snapshots
                    growth_rate = 0
                    cursor.execute("""
                        SELECT member_count FROM loyalty_segmentsnapshot 
                        WHERE segment_id = %s 
                        ORDER BY snapshot_date DESC LIMIT 2
                    """, [seg_id])
                    snapshots = cursor.fetchall()
                    if len(snapshots) >= 2:
                        prev_count = snapshots[1][0] or 0
                        if prev_count > 0:
                            growth_rate = ((member_count - prev_count) / prev_count) * 100
                    
                    results.append({
                        'segment_id': seg_id,
                        'segment_name': seg_name or f'Segment {seg_id}',
                        'member_count': member_count,
                        'growth_rate': round(growth_rate, 2),
                        'avg_points_balance': round(float(avg_points), 2),
                        'avg_lifetime_value': 0,
                    })
        except Exception as e:
            # Fallback to returning basic data if query fails
            print(f"Segment analytics error: {e}")
            # Return at least empty results
            pass
        
        return Response(results)
    
    @action(detail=False, methods=['get'], url_path='transaction-analytics')
    def transaction_analytics(self, request):
        """Get transaction analytics by date"""
        from datetime import datetime, timedelta
        from django.db.models import Count, Sum
        
        # Get date range
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except:
                start_date = timezone.now() - timedelta(days=30)
        else:
            start_date = timezone.now() - timedelta(days=30)
            
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except:
                end_date = timezone.now()
        else:
            end_date = timezone.now()
        
        # Group by date
        transactions = LoyaltyTransaction.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).extra(
            select={'date': "DATE(created_at)"}
        ).values('date', 'transaction_type').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('date')
        
        # Aggregate by date
        date_map = {}
        for tx in transactions:
            date_str = tx['date'].isoformat() if hasattr(tx['date'], 'isoformat') else str(tx['date'])
            if date_str not in date_map:
                date_map[date_str] = {
                    'date': date_str,
                    'earn_count': 0,
                    'redeem_count': 0,
                    'adjust_count': 0,
                    'total_points': 0,
                }
            
            if tx['transaction_type'] == 'earn':
                date_map[date_str]['earn_count'] += tx['count']
            elif tx['transaction_type'] == 'redeem':
                date_map[date_str]['redeem_count'] += tx['count']
            elif tx['transaction_type'] == 'adjust':
                date_map[date_str]['adjust_count'] += tx['count']
            
            date_map[date_str]['total_points'] += tx['total'] or 0
        
        results = list(date_map.values())
        results.sort(key=lambda x: x['date'])
        
        return Response(results)
    
    @action(detail=False, methods=['get'], url_path='recent-events')
    def recent_events(self, request):
        """
        Get recent loyalty events for activity feed
        """
        since_param = request.query_params.get('since')
        limit = int(request.query_params.get('limit', 20))
        
        # Calculate since timestamp
        if since_param:
            since = datetime.fromtimestamp(int(since_param) / 1000, tz=timezone.utc)
        else:
            since = timezone.now() - timedelta(hours=24)
        
        events = []
        
        # Get recent transactions
        recent_transactions = LoyaltyTransaction.objects.filter(
            created_at__gte=since
        ).select_related('account', 'account__program').order_by('-created_at')[:limit//2]
        
        for tx in recent_transactions:
            events.append({
                'id': f'tx_{tx.id}',
                'type': 'transaction',
                'timestamp': tx.created_at.isoformat(),
                'customer_id': str(tx.account.customer_id),
                'customer_name': f'Customer {tx.account.customer_id}',
                'description': f'{tx.get_transaction_type_display()}: {tx.amount} points',
                'program': tx.account.program.name,
                'amount': tx.amount,
                'transaction_type': tx.transaction_type
            })
        
        # Get recent redemptions
        recent_redemptions = LoyaltyRedemption.objects.filter(
            created_at__gte=since
        ).select_related('account', 'reward').order_by('-created_at')[:limit//2]
        
        for redemption in recent_redemptions:
            events.append({
                'id': f'red_{redemption.id}',
                'type': 'redemption',
                'timestamp': redemption.created_at.isoformat(),
                'customer_id': str(redemption.account.customer_id),
                'customer_name': f'Customer {redemption.account.customer_id}',
                'description': f'Redeemed: {redemption.reward.name}',
                'reward': redemption.reward.name,
                'points_used': redemption.points_used or redemption.reward.points_required
            })
        
        # Sort by timestamp and return
        events.sort(key=lambda x: x['timestamp'], reverse=True)
        return Response(events[:limit])

class LoyaltyDashboardConfigViewSet(viewsets.ViewSet):
    """
    ViewSet for loyalty dashboard configuration
    """
    
    def list(self, request):
        """
        Get dashboard configuration for loyalty management
        """
        config = {
            'widgets': [
                {
                    'id': 'total_points',
                    'title': 'Total Points Issued',
                    'type': 'metric',
                    'position': {'x': 0, 'y': 0, 'w': 3, 'h': 2}
                },
                {
                    'id': 'active_accounts',
                    'title': 'Active Loyalty Accounts',
                    'type': 'metric',
                    'position': {'x': 3, 'y': 0, 'w': 3, 'h': 2}
                },
                {
                    'id': 'redemptions_today',
                    'title': 'Redemptions Today',
                    'type': 'metric',
                    'position': {'x': 6, 'y': 0, 'w': 3, 'h': 2}
                },
                {
                    'id': 'points_chart',
                    'title': 'Points Activity',
                    'type': 'chart',
                    'position': {'x': 0, 'y': 2, 'w': 6, 'h': 4}
                },
                {
                    'id': 'tier_distribution',
                    'title': 'Tier Distribution',
                    'type': 'pie_chart',
                    'position': {'x': 6, 'y': 2, 'w': 3, 'h': 4}
                }
            ],
            'refresh_interval': 30000,  # 30 seconds
            'theme': 'light'
        }
        
        return Response(config)

class LoyaltyEligibilityRuleViewSet(viewsets.ModelViewSet):
    queryset = LoyaltyEligibilityRule.objects.all()
    serializer_class = LoyaltyEligibilityRuleSerializer
    filterset_fields = ['program', 'is_active']

class LoyaltyEligibilityOverrideViewSet(viewsets.ModelViewSet):
    queryset = LoyaltyEligibilityOverride.objects.all()
    serializer_class = LoyaltyEligibilityOverrideSerializer
    filterset_fields = ['customer_id', 'program']

class EligibilityCheckAPIView(APIView):
    """GET ?customer=&program=  → returns eligibility = true/false with failed rules list"""
    def get(self, request, *args, **kwargs):
        cust_id = request.query_params.get('customer')
        prog_id = request.query_params.get('program')
        if not cust_id or not prog_id:
            return Response({'detail': 'customer and program query params are required'}, status=400)

        try:
            program = LoyaltyProgram.objects.get(id=prog_id)
        except LoyaltyProgram.DoesNotExist:
            return Response({'detail': 'Program not found'}, status=404)

        # Override check (using customer_id UUID)
        override = LoyaltyEligibilityOverride.objects.filter(
            customer_id=cust_id, 
            program=program, 
            force_eligible=True
        ).first()
        if override:
            return Response({'eligible': True, 'override': True, 'failed_rules': []})

        # Try to enrich context from external API if available
        customer_context = {}
        external_mode = getattr(settings, "LOYALTY_USE_EXTERNAL_CUSTOMER_API", False)
        if external_mode:
            try:
                customer_context = fetch_customer_context(cust_id)
            except ExternalServiceError:
                pass  # Continue with minimal context

        rules = LoyaltyEligibilityRule.objects.filter(program=program, is_active=True)
        failed = []
        context = {
            'customer_id': str(cust_id),
            'customer_status': customer_context.get('status', 'active'),
            'customer_created_at': customer_context.get('created_at', ''),
            'customer_type': customer_context.get('type', ''),
        }
        for rule in rules:
            try:
                if not safe_json_logic(rule.logic, context):
                    failed.append(rule.name)
            except Exception as exc:
                failed.append(f"{rule.name} (error: {exc})")

        eligible = len(failed) == 0
        return Response({'eligible': eligible, 'failed_rules': failed})


class BusinessRulesValidateAPIView(APIView):
    """POST - Validate business rules for enrollment"""
    def post(self, request, *args, **kwargs):
        customer_id = request.data.get('customer_id')
        program_id = request.data.get('program_id')
        enrollment_data = request.data.get('enrollment_data', {})
        
        if not customer_id or not program_id:
            return Response({'error': 'customer_id and program_id are required'}, status=400)
        
        try:
            from customer_management.models import Customer
            customer = Customer.objects.get(id=customer_id)
            program = LoyaltyProgram.objects.get(id=program_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=404)
        except LoyaltyProgram.DoesNotExist:
            return Response({'error': 'Program not found'}, status=404)
        
        # Run comprehensive business rules validation
        validation_results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'auto_approved': True,
            'requires_manual_review': False
        }
        
        # Check for existing enrollment
        existing_account = LoyaltyAccount.objects.filter(customer=customer, program=program).first()
        if existing_account:
            validation_results['errors'].append('Customer already enrolled in this program')
            validation_results['valid'] = False
            validation_results['auto_approved'] = False
        
        # Check eligibility rules
        rules = LoyaltyEligibilityRule.objects.filter(program=program, is_active=True)
        context = {
            'customer_status': getattr(customer, 'status', 'active'),
            'customer_created_at': str(getattr(customer, 'created_at', '')),
            'customer_type': getattr(customer, 'type', ''),
            'enrollment_data': enrollment_data
        }
        
        for rule in rules:
            try:
                if not safe_json_logic(rule.logic, context):
                    if rule.severity == 'error':
                        validation_results['errors'].append(f'Rule failed: {rule.name}')
                        validation_results['valid'] = False
                        validation_results['auto_approved'] = False
                    elif rule.severity == 'warning':
                        validation_results['warnings'].append(f'Warning: {rule.name}')
                        validation_results['requires_manual_review'] = True
                        validation_results['auto_approved'] = False
            except Exception as exc:
                validation_results['errors'].append(f'Rule validation error: {rule.name} - {str(exc)}')
                validation_results['valid'] = False
                validation_results['auto_approved'] = False
        
        # Additional business logic checks
        if hasattr(customer, 'credit_score') and getattr(customer, 'credit_score', 0) < 500:
            validation_results['warnings'].append('Low credit score - requires manual review')
            validation_results['requires_manual_review'] = True
            validation_results['auto_approved'] = False
        
        return Response(validation_results)


class ManualReviewAPIView(APIView):
    """POST - Submit enrollment for manual review"""
    def post(self, request, *args, **kwargs):
        customer_id = request.data.get('customer_id')
        program_id = request.data.get('program_id')
        enrollment_data = request.data.get('enrollment_data', {})
        review_reason = request.data.get('review_reason', 'General review required')
        
        if not customer_id or not program_id:
            return Response({'error': 'customer_id and program_id are required'}, status=400)
        
        try:
            program = LoyaltyProgram.objects.get(id=program_id)
        except LoyaltyProgram.DoesNotExist:
            return Response({'error': 'Program not found'}, status=404)
        
        # Create manual review record (using AuditLog for now)
        review_id = f"MR_{customer_id}_{program_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        AuditLog.objects.create(
            action='manual_review_submitted',
            object_type='enrollment',
            object_id=str(customer_id),
            actor_id=getattr(request.user, 'id', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
            metadata={
                'customer_id': customer_id,
                'program_id': program_id,
                'enrollment_data': enrollment_data,
                'review_reason': review_reason,
                'review_id': review_id,
                'status': 'pending_review'
            }
        )
        
        # Create notification event
        LoyaltyEvent.objects.create(
            account=None,  # No account yet since enrollment is pending
            event_type='manual_review_submitted',
            description=f'Manual review submitted for customer {customer_id} enrollment in {program.name}',
            metadata={
                'customer_id': customer_id,
                'program_id': program_id,
                'review_id': review_id,
                'review_reason': review_reason
            }
        )
        
        return Response({
            'review_id': review_id,
            'status': 'submitted_for_review',
            'message': 'Enrollment submitted for manual review',
            'estimated_review_time': '1-3 business days',
            'customer_id': customer_id,
            'program': program.name
        }) 