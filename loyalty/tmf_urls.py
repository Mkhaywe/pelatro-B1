"""
TMF (TM Forum) API adapter layer.
Maps internal loyalty models to TMF-compliant API structure.
"""

from rest_framework.routers import DefaultRouter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets
from django.urls import path
from loyalty.models import LoyaltyAccount, LoyaltyProgram, LoyaltyTransaction, LoyaltyReward
from loyalty.serializers import LoyaltyAccountSerializer, LoyaltyProgramSerializer
from loyalty.tmf_serializers import (
    LoyaltyAccountTMFSerializer,
    LoyaltyProgramTMFSerializer,
    LoyaltyTransactionTMFSerializer,
)


class LoyaltyAccountTMFViewSet(viewsets.ModelViewSet):
    """
    TMF LoyaltyAccount resource
    GET /tmf-api/loyaltyManagement/v4/loyaltyAccount/{id}
    """
    queryset = LoyaltyAccount.objects.all()
    serializer_class = LoyaltyAccountTMFSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        # Add TMF metadata
        data = serializer.data
        data['@type'] = 'LoyaltyAccount'
        data['@baseType'] = 'LoyaltyAccount'
        data['href'] = f"/tmf-api/loyaltyManagement/v4/loyaltyAccount/{instance.id}"
        return Response(data)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        # TMF list response format
        return Response({
            '@type': 'LoyaltyAccount',
            'loyaltyAccount': serializer.data
        })


class LoyaltyProgramTMFViewSet(viewsets.ModelViewSet):
    """
    TMF LoyaltyProgram resource
    GET /tmf-api/loyaltyManagement/v4/loyaltyProgram/{id}
    """
    queryset = LoyaltyProgram.objects.all()
    serializer_class = LoyaltyProgramTMFSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        data['@type'] = 'LoyaltyProgram'
        data['@baseType'] = 'LoyaltyProgram'
        data['href'] = f"/tmf-api/loyaltyManagement/v4/loyaltyProgram/{instance.id}"
        return Response(data)


class LoyaltyTransactionTMFViewSet(viewsets.ReadOnlyModelViewSet):
    """
    TMF LoyaltyTransaction resource
    """
    queryset = LoyaltyTransaction.objects.all()
    serializer_class = LoyaltyTransactionTMFSerializer


# TMF Router
tmf_router = DefaultRouter()
tmf_router.register(r'loyaltyAccount', LoyaltyAccountTMFViewSet, basename='tmf-loyaltyaccount')
tmf_router.register(r'loyaltyProgram', LoyaltyProgramTMFViewSet, basename='tmf-loyaltyprogram')
tmf_router.register(r'loyaltyTransaction', LoyaltyTransactionTMFViewSet, basename='tmf-loyaltytransaction')

tmf_urlpatterns = tmf_router.urls

