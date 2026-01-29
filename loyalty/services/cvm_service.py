"""
Customer Value Management (CVM) Service
Manages customer value segmentation and value-based targeting
"""
from typing import Dict, Optional, List
from django.utils import timezone
from django.db import models
from decimal import Decimal
from loyalty.models import CustomerValueSegment  # This is in models.py
from loyalty.ml.inference import MLInferenceService
from loyalty.integration.feature_store import FeatureStore
import logging

logger = logging.getLogger(__name__)


class CVMService:
    """Customer Value Management Service"""
    
    def __init__(self):
        self.ml_service = MLInferenceService()
    
    def calculate_customer_value(self, customer_id: str) -> Dict:
        """
        Calculate customer value using RFM + LTV prediction
        
        Returns:
            Dict with value metrics and segment
        """
        # Get RFM scores
        rfm_result = self.ml_service.calculate_rfm(customer_id)
        
        # Get customer features
        features = FeatureStore.get_customer_features(customer_id)
        
        # Calculate lifetime value (use actual or predicted)
        lifetime_value = float(features.get('lifetime_value', 0) or 0)
        
        # Try to get LTV prediction if model exists
        predicted_ltv = None
        try:
            if 'ltv' in self.ml_service.models:
                ltv_result = self.ml_service.predict_ltv(customer_id)
                if 'error' not in ltv_result:
                    predicted_ltv = float(ltv_result.get('predicted_ltv', lifetime_value))
        except:
            pass  # LTV model not available yet
        
        # Calculate value score (0-100)
        # Formula: RFM M-score (0-5) * 20 + LTV normalized (0-5) * 20
        rfm_m_score = rfm_result.get('m_score', 0) if 'error' not in rfm_result else 0
        rfm_segment = rfm_result.get('segment', 'Unknown') if 'error' not in rfm_result else 'Unknown'
        
        # Normalize LTV to 0-5 scale (adjust thresholds based on your business)
        ltv_for_score = predicted_ltv if predicted_ltv else lifetime_value
        if ltv_for_score >= 5000:
            ltv_score = 5
        elif ltv_for_score >= 2000:
            ltv_score = 4
        elif ltv_for_score >= 1000:
            ltv_score = 3
        elif ltv_for_score >= 500:
            ltv_score = 2
        elif ltv_for_score > 0:
            ltv_score = 1
        else:
            ltv_score = 0
        
        # Calculate value score
        value_score = (rfm_m_score * 20) + (ltv_score * 20)
        value_score = min(100, max(0, value_score))  # Clamp to 0-100
        
        # Determine value segment
        if value_score >= 70:
            segment = 'high_value'
        elif value_score >= 40:
            segment = 'medium_value'
        else:
            segment = 'low_value'
        
        return {
            'customer_id': customer_id,
            'lifetime_value': Decimal(str(lifetime_value)),
            'predicted_ltv': Decimal(str(predicted_ltv)) if predicted_ltv else None,
            'rfm_segment': rfm_segment,
            'rfm_m_score': rfm_m_score,
            'value_score': Decimal(str(value_score)),
            'value_segment': segment,
        }
    
    def update_customer_value_segment(self, customer_id: str) -> CustomerValueSegment:
        """
        Calculate and update customer value segment
        
        Returns:
            CustomerValueSegment instance
        """
        value_data = self.calculate_customer_value(customer_id)
        
        segment, created = CustomerValueSegment.objects.update_or_create(
            customer_id=customer_id,
            defaults={
                'segment': value_data['value_segment'],
                'lifetime_value': value_data['lifetime_value'],
                'predicted_ltv': value_data['predicted_ltv'],
                'value_score': value_data['value_score'],
                'rfm_segment': value_data['rfm_segment'],
            }
        )
        
        return segment
    
    def get_value_based_offers(self, customer_id: str) -> List[Dict]:
        """
        Get offers based on customer value segment
        
        Returns:
            List of recommended offers
        """
        value_data = self.calculate_customer_value(customer_id)
        segment = value_data['value_segment']
        
        # Get NBO prediction
        nbo_result = self.ml_service.predict_nbo(customer_id)
        
        # Get offers from catalog service
        from loyalty.services.offer_service import OfferCatalogService
        offer_service = OfferCatalogService()
        
        offers = offer_service.get_offers_for_customer(customer_id, nbo_result)
        
        # Filter by value segment
        filtered_offers = []
        for offer in offers:
            target_segment = offer.get('target_value_segment', 'all')
            if target_segment == 'all' or target_segment == segment:
                filtered_offers.append(offer)
        
        return filtered_offers
    
    def get_segment_statistics(self, segment: Optional[str] = None) -> Dict:
        """
        Get statistics for value segments
        
        Args:
            segment: Optional segment name to filter
        
        Returns:
            Dict with segment statistics
        """
        queryset = CustomerValueSegment.objects.all()
        
        if segment:
            queryset = queryset.filter(segment=segment)
        
        stats = {}
        for value_segment in queryset.values('segment').distinct():
            segment_name = value_segment['segment']
            count = queryset.filter(segment=segment_name).count()
            avg_value = queryset.filter(segment=segment_name).aggregate(
                avg_value=models.Avg('value_score')
            )['avg_value'] or 0
            avg_ltv = queryset.filter(segment=segment_name).aggregate(
                avg_ltv=models.Avg('lifetime_value')
            )['avg_ltv'] or 0
            
            stats[segment_name] = {
                'count': count,
                'avg_value_score': float(avg_value),
                'avg_lifetime_value': float(avg_ltv),
            }
        
        return stats

