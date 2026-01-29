"""
Mock ML Inference Service for testing without DWH or trained models.
Returns realistic dummy predictions for development/testing.
"""

from typing import Dict, List
import random
from django.conf import settings

# Check if mock mode is enabled
MOCK_ML_ENABLED = getattr(settings, 'ML_MOCK_MODE', False)


class MockMLInferenceService:
    """Mock ML inference service that returns dummy predictions"""
    
    def __init__(self):
        self.mock_customers = {
            # High-value customer
            'high-value-customer': {
                'total_revenue': 5000.0,
                'transaction_count': 25,
                'days_since_last': 5,
                'avg_transaction_value': 200.0,
            },
            # Medium-value customer
            'medium-value-customer': {
                'total_revenue': 1500.0,
                'transaction_count': 10,
                'days_since_last': 15,
                'avg_transaction_value': 150.0,
            },
            # Low-value customer (churn risk)
            'churn-risk-customer': {
                'total_revenue': 300.0,
                'transaction_count': 2,
                'days_since_last': 90,
                'avg_transaction_value': 150.0,
            },
            # New customer
            'new-customer': {
                'total_revenue': 100.0,
                'transaction_count': 1,
                'days_since_last': 2,
                'avg_transaction_value': 100.0,
            },
        }
        
        # Mock offers (for NBO)
        self.mock_offers = [
            {'id': 0, 'name': 'Double Points Weekend', 'category': 'points'},
            {'id': 1, 'name': 'Free Shipping', 'category': 'shipping'},
            {'id': 2, 'name': '10% Discount', 'category': 'discount'},
            {'id': 3, 'name': 'Exclusive VIP Access', 'category': 'access'},
            {'id': 4, 'name': 'Birthday Bonus', 'category': 'special'},
            {'id': 5, 'name': 'Referral Reward', 'category': 'referral'},
            {'id': 6, 'name': 'Flash Sale', 'category': 'sale'},
            {'id': 7, 'name': 'Loyalty Tier Upgrade', 'category': 'tier'},
        ]
    
    def _get_customer_profile(self, customer_id: str) -> Dict:
        """Get mock customer profile based on customer_id"""
        # Check if customer_id matches a known mock customer
        if customer_id in self.mock_customers:
            return self.mock_customers[customer_id]
        
        # Generate random profile based on customer_id hash
        import hashlib
        hash_val = int(hashlib.md5(customer_id.encode()).hexdigest(), 16)
        random.seed(hash_val)
        
        return {
            'total_revenue': random.uniform(100, 5000),
            'transaction_count': random.randint(1, 30),
            'days_since_last': random.randint(1, 120),
            'avg_transaction_value': random.uniform(50, 300),
        }
    
    def predict_nbo(self, customer_id: str) -> Dict:
        """Mock NBO prediction"""
        profile = self._get_customer_profile(customer_id)
        
        # Generate realistic offer scores based on customer profile
        offer_scores = []
        
        # High revenue customers get premium offers
        if profile['total_revenue'] > 3000:
            offer_scores = [0.15, 0.10, 0.20, 0.30, 0.05, 0.10, 0.05, 0.05]
        # Medium revenue customers get standard offers
        elif profile['total_revenue'] > 1000:
            offer_scores = [0.25, 0.20, 0.30, 0.10, 0.05, 0.05, 0.03, 0.02]
        # Low revenue / churn risk get retention offers
        elif profile['days_since_last'] > 60:
            offer_scores = [0.40, 0.15, 0.25, 0.05, 0.05, 0.05, 0.03, 0.02]
        # New customers get onboarding offers
        elif profile['transaction_count'] <= 2:
            offer_scores = [0.30, 0.25, 0.20, 0.05, 0.10, 0.05, 0.03, 0.02]
        # Default
        else:
            offer_scores = [0.20, 0.20, 0.25, 0.10, 0.10, 0.08, 0.05, 0.02]
        
        # Add some randomness
        offer_scores = [max(0, s + random.uniform(-0.05, 0.05)) for s in offer_scores]
        # Normalize
        total = sum(offer_scores)
        offer_scores = [s / total for s in offer_scores]
        
        # Get top offer
        top_idx = offer_scores.index(max(offer_scores))
        
        confidence = max(offer_scores)
        recommended_offer = top_idx
        
        # Generate explanation
        explanation_parts = []
        if profile['total_revenue'] > 3000:
            explanation_parts.append(f"High-value customer (${profile['total_revenue']:.2f} lifetime revenue)")
        elif profile['total_revenue'] > 0:
            explanation_parts.append(f"Customer with ${profile['total_revenue']:.2f} lifetime revenue")
        
        if profile['days_since_last'] > 60:
            explanation_parts.append(f"Last activity was {profile['days_since_last']} days ago - retention offer recommended")
        elif profile['days_since_last'] > 0:
            explanation_parts.append(f"Last activity {profile['days_since_last']} days ago")
        
        if profile['transaction_count'] <= 2:
            explanation_parts.append("New customer - onboarding offer recommended")
        elif profile['transaction_count'] < 10:
            explanation_parts.append(f"Moderate engagement ({profile['transaction_count']} transactions)")
        
        explanation = f"Recommended Offer #{recommended_offer} ({self.mock_offers[recommended_offer]['name']}) with {confidence*100:.0f}% confidence. "
        if explanation_parts:
            explanation += "Based on: " + "; ".join(explanation_parts[:3])
        else:
            explanation += "Based on customer behavior patterns."
        
        return {
            'customer_id': customer_id,
            'offer_scores': offer_scores,
            'recommended_offer': recommended_offer,
            'confidence': confidence,
            'explanation': explanation,
            'offers': [
                {
                    'offer_id': i,
                    'offer_name': self.mock_offers[i]['name'],
                    'category': self.mock_offers[i]['category'],
                    'probability': score
                }
                for i, score in enumerate(offer_scores)
            ],
            'top_offer': {
                'offer_id': top_idx,
                'offer_name': self.mock_offers[top_idx]['name'],
                'category': self.mock_offers[top_idx]['category'],
                'probability': confidence
            }
        }
    
    def predict_churn(self, customer_id: str) -> Dict:
        """Mock churn prediction"""
        profile = self._get_customer_profile(customer_id)
        
        # Calculate churn probability based on profile
        # Factors: days since last, transaction count, revenue
        days_factor = min(profile['days_since_last'] / 90, 1.0)  # 0-1 scale
        frequency_factor = 1.0 - min(profile['transaction_count'] / 20, 1.0)  # Inverse
        revenue_factor = 1.0 - min(profile['total_revenue'] / 3000, 1.0)  # Inverse
        
        # Weighted churn probability
        churn_probability = (
            days_factor * 0.5 +
            frequency_factor * 0.3 +
            revenue_factor * 0.2
        )
        
        # Add some randomness
        churn_probability += random.uniform(-0.1, 0.1)
        churn_probability = max(0.0, min(1.0, churn_probability))
        
        # Determine risk level
        if churn_probability >= 0.7:
            risk = 'high'
            reasons = [
                'No activity in last 60+ days',
                'Low transaction frequency',
                'Declining engagement'
            ]
        elif churn_probability >= 0.4:
            risk = 'medium'
            reasons = [
                'Reduced activity recently',
                'Below average engagement'
            ]
        else:
            risk = 'low'
            reasons = [
                'Active customer',
                'Regular transactions',
                'Good engagement'
            ]
        
        # Generate detailed explanation
        explanation_parts = []
        if profile['days_since_last'] > 30:
            explanation_parts.append(f"Customer hasn't recharged in {profile['days_since_last']} days")
        elif profile['days_since_last'] > 0:
            explanation_parts.append(f"Last recharge was {profile['days_since_last']} days ago")
        
        if profile['transaction_count'] < 3:
            explanation_parts.append(f"Very low transaction count ({profile['transaction_count']})")
        elif profile['transaction_count'] < 10:
            explanation_parts.append(f"Low transaction frequency ({profile['transaction_count']} total)")
        
        if profile['total_revenue'] < 500:
            explanation_parts.append(f"Low lifetime value (${profile['total_revenue']:.2f})")
        
        explanation = f"Churn risk: {risk.upper()} ({churn_probability*100:.0f}%). "
        if explanation_parts:
            explanation += "Key indicators: " + "; ".join(explanation_parts[:5])
        else:
            explanation += "Based on overall customer behavior patterns and engagement metrics."
        
        return {
            'customer_id': customer_id,
            'churn_probability': round(churn_probability, 3),
            'churn_risk': risk,
            'risk_score': churn_probability,
            'explanation': explanation,
            'reasons': reasons,
            'profile': {
                'days_since_last': profile['days_since_last'],
                'transaction_count': profile['transaction_count'],
                'total_revenue': profile['total_revenue']
            }
        }
    
    def calculate_rfm(self, customer_id: str) -> Dict:
        """Mock RFM calculation"""
        profile = self._get_customer_profile(customer_id)
        
        recency = profile['days_since_last']
        frequency = profile['transaction_count']
        monetary = profile['total_revenue']
        
        # RFM Scoring (1-5 scale)
        # Recency: Lower is better (recent = higher score)
        if recency <= 30:
            r_score = 5
        elif recency <= 60:
            r_score = 4
        elif recency <= 90:
            r_score = 3
        elif recency <= 180:
            r_score = 2
        else:
            r_score = 1
        
        # Frequency: Higher is better
        if frequency >= 20:
            f_score = 5
        elif frequency >= 10:
            f_score = 4
        elif frequency >= 5:
            f_score = 3
        elif frequency >= 2:
            f_score = 2
        else:
            f_score = 1
        
        # Monetary: Higher is better
        if monetary >= 3000:
            m_score = 5
        elif monetary >= 1500:
            m_score = 4
        elif monetary >= 500:
            m_score = 3
        elif monetary >= 200:
            m_score = 2
        else:
            m_score = 1
        
        # RFM Segment
        rfm_segment = f"{r_score}{f_score}{m_score}"
        
        # Segment interpretation
        segment_names = {
            '555': 'Champions',
            '554': 'Champions',
            '544': 'Loyal Customers',
            '545': 'Champions',
            '455': 'Potential Loyalists',
            '454': 'Potential Loyalists',
            '445': 'Potential Loyalists',
            '444': 'Loyal Customers',
            '355': 'At Risk',
            '354': 'At Risk',
            '345': 'At Risk',
            '344': 'Need Attention',
            '255': 'Cannot Lose Them',
            '254': 'At Risk',
            '245': 'At Risk',
            '244': 'At Risk',
            '155': 'Cannot Lose Them',
            '154': 'Hibernating',
            '145': 'About to Sleep',
            '144': 'Lost',
            '111': 'Lost',
        }
        
        segment_name = segment_names.get(rfm_segment, 'Regular')
        
        return {
            'customer_id': customer_id,
            'recency': recency,
            'frequency': frequency,
            'monetary': monetary,
            'r_score': r_score,
            'f_score': f_score,
            'm_score': m_score,
            'rfm_segment': rfm_segment,
            'segment': segment_name,
            'recency_score': r_score,
            'frequency_score': f_score,
            'monetary_score': m_score,
            'recency_days': recency,
            'frequency_count': frequency,
            'monetary_value': monetary,
        }
    
    def predict_ltv(self, customer_id: str) -> Dict:
        """Mock LTV prediction"""
        profile = self._get_customer_profile(customer_id)
        # Simple LTV calculation based on revenue and activity
        base_ltv = profile['total_revenue']
        if profile['days_since_last'] < 30:
            predicted_ltv = base_ltv * 1.5  # Active customers have higher future value
        elif profile['days_since_last'] < 60:
            predicted_ltv = base_ltv * 1.2
        else:
            predicted_ltv = base_ltv * 0.8  # Inactive customers have lower future value
        
        return {
            'customer_id': customer_id,
            'predicted_ltv': round(predicted_ltv, 2),
            'confidence': 0.7,
        }
    
    def recommend_products(self, customer_id: str, top_n: int = 5) -> Dict:
        """Mock product recommendation"""
        profile = self._get_customer_profile(customer_id)
        all_products = [
            {'product_id': 'P001', 'name': 'Premium Data Plan', 'category': 'data'},
            {'product_id': 'P002', 'name': 'Voice Bundle', 'category': 'voice'},
            {'product_id': 'P003', 'name': 'SMS Package', 'category': 'sms'},
            {'product_id': 'P004', 'name': 'International Roaming', 'category': 'roaming'},
            {'product_id': 'P005', 'name': 'Streaming Service', 'category': 'entertainment'},
        ]
        recommended = all_products[:top_n]
        for product in recommended:
            product['probability'] = 0.7 - (recommended.index(product) * 0.1)
        return {
            'customer_id': customer_id,
            'recommended_products': recommended,
            'reason': f'Based on customer profile'
        }
    
    def predict_campaign_response(self, customer_id: str, campaign_id: str = None) -> Dict:
        """Mock campaign response prediction"""
        profile = self._get_customer_profile(customer_id)
        if profile['days_since_last'] < 30 and profile['transaction_count'] > 5:
            response_probability = 0.8
        elif profile['days_since_last'] < 60:
            response_probability = 0.5
        else:
            response_probability = 0.2
        return {
            'customer_id': customer_id,
            'campaign_id': campaign_id,
            'response_probability': response_probability,
            'will_respond': response_probability > 0.5,
        }
    
    def predict_payment_default_risk(self, customer_id: str) -> Dict:
        """Mock payment default risk prediction"""
        profile = self._get_customer_profile(customer_id)
        default_risk = 0.1
        if profile.get('credit_utilization', 0) > 0.9:
            default_risk += 0.4
        if profile['days_since_last'] > 90:
            default_risk += 0.3
        default_risk = min(1.0, default_risk)
        return {
            'customer_id': customer_id,
            'default_risk': default_risk,
            'risk_level': 'high' if default_risk > 0.7 else 'medium' if default_risk > 0.4 else 'low',
            'will_default': default_risk > 0.5
        }
    
    def predict_upsell_propensity(self, customer_id: str) -> Dict:
        """Mock upsell propensity prediction"""
        profile = self._get_customer_profile(customer_id)
        upsell_propensity = 0.3
        if profile['total_revenue'] > 1000 and profile.get('active_products', 0) < 3:
            upsell_propensity = 0.8
        elif profile['total_revenue'] > 500 and profile.get('active_products', 0) < 2:
            upsell_propensity = 0.6
        return {
            'customer_id': customer_id,
            'upsell_propensity': upsell_propensity,
            'will_upsell': upsell_propensity > 0.5,
            'recommended_action': 'high' if upsell_propensity > 0.7 else 'medium' if upsell_propensity > 0.5 else 'low'
        }

