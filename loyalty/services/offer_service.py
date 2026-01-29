"""
Offer Management Service
Handles offer catalog, syncing from external systems, and linking to ML predictions
"""
from typing import Dict, List, Optional
from django.utils import timezone
from django.db import transaction
from loyalty.models import Offer
from loyalty.integration.xiva_client import get_xiva_client, XivaAPIError
import logging

logger = logging.getLogger(__name__)


class OfferSyncService:
    """Sync offers from external systems"""
    
    def sync_from_xiva(self) -> Dict:
        """
        Sync offers from Xiva API
        
        Returns:
            Dict with sync results
        """
        try:
            client = get_xiva_client()
            # Note: Adjust API endpoint based on Xiva's actual offer API
            # This is a placeholder - you'll need to check Xiva API docs
            offers_data = []  # client.get_offers() or similar
            
            synced_count = 0
            created_count = 0
            updated_count = 0
            
            for offer_data in offers_data:
                offer_id = offer_data.get('id')
                if not offer_id:
                    continue
                
                offer, created = Offer.objects.update_or_create(
                    external_offer_id=str(offer_id),
                    external_system='xiva',
                    defaults={
                        'offer_id': offer_id % 8,  # Map to 0-7 range
                        'name': offer_data.get('name', f'Offer {offer_id}'),
                        'description': offer_data.get('description', ''),
                        'category': self._map_category(offer_data.get('category')),
                        'is_active': offer_data.get('is_active', True),
                        'last_synced': timezone.now(),
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                synced_count += 1
            
            return {
                'success': True,
                'synced': synced_count,
                'created': created_count,
                'updated': updated_count,
            }
        except XivaAPIError as e:
            logger.error(f"Error syncing offers from Xiva: {e}")
            return {
                'success': False,
                'error': str(e),
            }
        except Exception as e:
            logger.error(f"Unexpected error syncing offers: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def _map_category(self, category: str) -> str:
        """Map external category to internal category"""
        category_map = {
            'points': 'points',
            'discount': 'discount',
            'free_shipping': 'shipping',
            'vip': 'access',
            'special': 'special',
            'referral': 'referral',
            'sale': 'sale',
            'upgrade': 'tier',
        }
        return category_map.get(category.lower(), 'points')
    
    def sync_manual(self, offers: List[Dict]) -> Dict:
        """
        Manually sync offers (for testing or manual entry)
        
        Args:
            offers: List of offer dicts with offer_id, name, description, category
        """
        synced_count = 0
        created_count = 0
        updated_count = 0
        
        for offer_data in offers:
            offer_id = offer_data.get('offer_id')
            if offer_id is None:
                continue
            
            offer, created = Offer.objects.update_or_create(
                offer_id=offer_id,
                defaults={
                    'name': offer_data.get('name', f'Offer {offer_id}'),
                    'description': offer_data.get('description', ''),
                    'category': offer_data.get('category', 'points'),
                    'lifecycle_stage': offer_data.get('lifecycle_stage'),
                    'target_value_segment': offer_data.get('target_value_segment', 'all'),
                    'is_active': offer_data.get('is_active', True),
                    'external_system': 'manual',
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
            synced_count += 1
        
        return {
            'success': True,
            'synced': synced_count,
            'created': created_count,
            'updated': updated_count,
        }


class OfferCatalogService:
    """Manage offer catalog and link to ML predictions"""
    
    def get_offer_by_id(self, offer_id: int) -> Optional[Offer]:
        """Get offer by numeric ID (used by ML models)"""
        try:
            return Offer.objects.get(offer_id=offer_id, is_active=True)
        except Offer.DoesNotExist:
            return None
    
    def get_offers_for_customer(self, customer_id: str, ml_predictions: Dict) -> List[Dict]:
        """
        Get offer details for ML predictions
        
        Args:
            customer_id: Customer ID
            ml_predictions: ML prediction result with offer_scores or recommended_offer
        
        Returns:
            List of offer details with probabilities
        """
        offers = []
        
        if 'offer_scores' in ml_predictions:
            # Get all offers with scores
            offer_scores = ml_predictions['offer_scores']
            for idx, score in enumerate(offer_scores):
                offer = self.get_offer_by_id(idx)
                if offer:
                    offers.append({
                        'offer_id': offer.offer_id,
                        'name': offer.name,
                        'description': offer.description,
                        'category': offer.category,
                        'lifecycle_stage': offer.lifecycle_stage,
                        'target_value_segment': offer.target_value_segment,
                        'probability': score,
                        'confidence': score,
                    })
                else:
                    # Fallback if offer not in catalog
                    offers.append({
                        'offer_id': idx,
                        'name': f'Offer #{idx}',
                        'description': 'Offer details not available',
                        'category': 'points',
                        'probability': score,
                        'confidence': score,
                    })
        elif 'recommended_offer' in ml_predictions:
            # Get single recommended offer
            offer_id = ml_predictions['recommended_offer']
            offer = self.get_offer_by_id(offer_id)
            if offer:
                offers.append({
                    'offer_id': offer.offer_id,
                    'name': offer.name,
                    'description': offer.description,
                    'category': offer.category,
                    'lifecycle_stage': offer.lifecycle_stage,
                    'target_value_segment': offer.target_value_segment,
                    'probability': ml_predictions.get('confidence', 0),
                    'confidence': ml_predictions.get('confidence', 0),
                })
            else:
                offers.append({
                    'offer_id': offer_id,
                    'name': f'Offer #{offer_id}',
                    'description': 'Offer details not available',
                    'category': 'points',
                    'probability': ml_predictions.get('confidence', 0),
                    'confidence': ml_predictions.get('confidence', 0),
                })
        
        # Sort by probability/confidence
        offers.sort(key=lambda x: x.get('probability', 0), reverse=True)
        return offers
    
    def get_offers_by_lifecycle_stage(self, stage: str) -> List[Offer]:
        """Get offers targeting a specific lifecycle stage"""
        return list(Offer.objects.filter(
            lifecycle_stage=stage,
            is_active=True
        ).order_by('offer_id'))
    
    def get_offers_by_value_segment(self, segment: str) -> List[Offer]:
        """Get offers targeting a specific value segment"""
        return list(Offer.objects.filter(
            target_value_segment__in=[segment, 'all'],
            is_active=True
        ).order_by('offer_id'))

