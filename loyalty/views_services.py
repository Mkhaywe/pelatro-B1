"""
API Views for Enterprise Services
Exposes service endpoints for points, eligibility, tier, and execution engines.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from django.utils import timezone
from decimal import Decimal

from loyalty.models import LoyaltyAccount, LoyaltyProgram
from loyalty.services.points_service import PointsService
from loyalty.services.eligibility_service import EligibilityService
from loyalty.services.tier_service import TierService
from loyalty.engines.campaign_engine import CampaignExecutionEngine
from loyalty.engines.journey_engine import JourneyExecutionEngine
from loyalty.engines.segment_engine import SegmentRecalculationEngine


class PointsServiceViewSet(viewsets.ViewSet):
    """API for Points Service"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.points_service = PointsService()
    
    @action(detail=False, methods=['post'], url_path='earn')
    def earn_points(self, request: Request):
        """Earn points for a customer"""
        customer_id = request.data.get('customer_id')
        program_id = request.data.get('program_id')
        transaction_amount = Decimal(str(request.data.get('transaction_amount', 0)))
        transaction_context = request.data.get('transaction_context', {})
        
        if not customer_id or not program_id:
            return Response(
                {'error': 'customer_id and program_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            account = LoyaltyAccount.objects.get(
                customer_id=customer_id,
                program_id=program_id
            )
        except LoyaltyAccount.DoesNotExist:
            return Response(
                {'error': 'Account not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        result = self.points_service.earn_points(
            account, transaction_amount, transaction_context
        )
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='burn')
    def burn_points(self, request: Request):
        """Burn points for a redemption"""
        customer_id = request.data.get('customer_id')
        program_id = request.data.get('program_id')
        reward_cost = int(request.data.get('reward_cost', 0))
        
        if not customer_id or not program_id:
            return Response(
                {'error': 'customer_id and program_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            account = LoyaltyAccount.objects.get(
                customer_id=customer_id,
                program_id=program_id
            )
        except LoyaltyAccount.DoesNotExist:
            return Response(
                {'error': 'Account not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        result = self.points_service.burn_points(account, reward_cost)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='process-expiry')
    def process_expiry(self, request: Request):
        """Process points expiry for an account"""
        customer_id = request.data.get('customer_id')
        program_id = request.data.get('program_id')
        
        if not customer_id or not program_id:
            return Response(
                {'error': 'customer_id and program_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            account = LoyaltyAccount.objects.get(
                customer_id=customer_id,
                program_id=program_id
            )
        except LoyaltyAccount.DoesNotExist:
            return Response(
                {'error': 'Account not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        result = self.points_service.process_expiry(account)
        return Response(result, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='reconcile')
    def reconcile_account(self, request: Request):
        """Reconcile account balance"""
        customer_id = request.data.get('customer_id')
        program_id = request.data.get('program_id')
        
        if not customer_id or not program_id:
            return Response(
                {'error': 'customer_id and program_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            account = LoyaltyAccount.objects.get(
                customer_id=customer_id,
                program_id=program_id
            )
        except LoyaltyAccount.DoesNotExist:
            return Response(
                {'error': 'Account not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        result = self.points_service.reconcile_account(account)
        return Response(result, status=status.HTTP_200_OK)


class EligibilityServiceViewSet(viewsets.ViewSet):
    """API for Eligibility Service"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eligibility_service = EligibilityService()
    
    @action(detail=False, methods=['post'], url_path='check')
    def check_eligibility(self, request: Request):
        """Check customer eligibility"""
        customer_id = request.data.get('customer_id')
        program_id = request.data.get('program_id')
        context = request.data.get('context', {})
        
        if not customer_id or not program_id:
            return Response(
                {'error': 'customer_id and program_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            program = LoyaltyProgram.objects.get(id=program_id)
        except LoyaltyProgram.DoesNotExist:
            return Response(
                {'error': 'Program not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        is_eligible, errors, metadata = self.eligibility_service.check_eligibility(
            customer_id, program, context
        )
        
        return Response({
            'is_eligible': is_eligible,
            'errors': errors,
            'metadata': metadata
        }, status=status.HTTP_200_OK)


class TierServiceViewSet(viewsets.ViewSet):
    """API for Tier Service"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tier_service = TierService()
    
    @action(detail=False, methods=['post'], url_path='calculate-and-update')
    def calculate_and_update_tier(self, request: Request):
        """Calculate and update tier for account"""
        customer_id = request.data.get('customer_id')
        program_id = request.data.get('program_id')
        auto_upgrade = request.data.get('auto_upgrade', True)
        auto_downgrade = request.data.get('auto_downgrade', False)
        
        if not customer_id or not program_id:
            return Response(
                {'error': 'customer_id and program_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            account = LoyaltyAccount.objects.get(
                customer_id=customer_id,
                program_id=program_id
            )
        except LoyaltyAccount.DoesNotExist:
            return Response(
                {'error': 'Account not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        result = self.tier_service.calculate_and_update_tier(
            account, auto_upgrade, auto_downgrade
        )
        return Response(result, status=status.HTTP_200_OK)


class CampaignEngineViewSet(viewsets.ViewSet):
    """API for Campaign Execution Engine"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engine = CampaignExecutionEngine()
    
    @action(detail=False, methods=['post'], url_path='process-event')
    def process_event(self, request: Request):
        """Process an event and trigger campaigns"""
        event_type = request.data.get('event_type')
        event_data = request.data.get('event_data', {})
        
        if not event_type:
            return Response(
                {'error': 'event_type required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = self.engine.process_event_trigger(event_type, event_data)
        return Response({'results': results}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='process-schedule')
    def process_schedule(self, request: Request):
        """Process schedule triggers"""
        current_time = request.data.get('current_time')
        if current_time:
            from datetime import datetime
            current_time = datetime.fromisoformat(current_time)
        
        results = self.engine.process_schedule_trigger(current_time)
        return Response({'results': results}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='process-threshold')
    def process_threshold(self, request: Request):
        """Process threshold triggers for a customer"""
        customer_id = request.data.get('customer_id')
        
        if not customer_id:
            return Response(
                {'error': 'customer_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = self.engine.process_threshold_trigger(customer_id)
        return Response({'results': results}, status=status.HTTP_200_OK)


class JourneyEngineViewSet(viewsets.ViewSet):
    """API for Journey Execution Engine"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engine = JourneyExecutionEngine()
    
    @action(detail=False, methods=['post'], url_path='start')
    def start_journey(self, request: Request):
        """Start a journey for a customer"""
        from loyalty.models_khaywe import Journey
        
        journey_id = request.data.get('journey_id')
        customer_id = request.data.get('customer_id')
        context = request.data.get('context', {})
        
        if not journey_id or not customer_id:
            return Response(
                {'error': 'journey_id and customer_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            journey = Journey.objects.get(id=journey_id)
        except Journey.DoesNotExist:
            return Response(
                {'error': 'Journey not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        execution = self.engine.start_journey(journey, customer_id, context)
        
        return Response({
            'execution_id': str(execution.id),
            'state': execution.state,
            'current_node_id': execution.current_node_id
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='process-event')
    def process_event(self, request: Request):
        """Process an event for journeys"""
        customer_id = request.data.get('customer_id')
        event_type = request.data.get('event_type')
        event_data = request.data.get('event_data', {})
        
        if not customer_id or not event_type:
            return Response(
                {'error': 'customer_id and event_type required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = self.engine.process_event(customer_id, event_type, event_data)
        return Response({'results': results}, status=status.HTTP_200_OK)


class SegmentEngineViewSet(viewsets.ViewSet):
    """API for Segment Recalculation Engine"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engine = SegmentRecalculationEngine()
    
    @action(detail=False, methods=['post'], url_path='recalculate-all')
    def recalculate_all(self, request: Request):
        """Recalculate all dynamic segments"""
        customer_ids = request.data.get('customer_ids')
        
        results = self.engine.recalculate_all_dynamic_segments(customer_ids)
        return Response(results, status=status.HTTP_200_OK)

