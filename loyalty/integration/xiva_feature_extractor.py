"""
Extract customer features from Xiva API responses.
Converts Xiva data into feature format compatible with FeatureStore.
"""

from typing import Dict, Any, Optional
from loyalty.integration.xiva_client import get_xiva_client, XivaAPIError
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)


class XivaFeatureExtractor:
    """Extract features from Xiva API for segmentation and ML"""
    
    @staticmethod
    def extract_customer_features(customer_id: str) -> Dict[str, Any]:
        """
        Extract customer features from Xiva API.
        
        Returns features in the same format as DWH features:
        {
            'customer_id': '...',
            'total_revenue': 1000.0,
            'transaction_count': 50,
            'customer_status': 'active',
            ...
        }
        """
        client = get_xiva_client()
        features = {
            'customer_id': customer_id,
        }
        
        try:
            # Get full customer context (best endpoint - has everything)
            context = client.get_customer_full_context(customer_id)
            
            # Extract customer basic info
            customer = context.get('customer', {})
            if customer:
                features.update(XivaFeatureExtractor._extract_customer_basic(customer))
            
            # Extract financial features
            try:
                financial = client.get_customer_360_financial(customer_id)
                features.update(XivaFeatureExtractor._extract_financial_features(financial))
            except XivaAPIError as e:
                logger.warning(f"Could not fetch financial data for {customer_id}: {e}")
            
            # Extract service/product features
            services = context.get('services', {})
            if services:
                features.update(XivaFeatureExtractor._extract_service_features(services))
            
            # Extract usage features
            try:
                usage = client.get_customer_360_usage(customer_id, current_month_only=True)
                features.update(XivaFeatureExtractor._extract_usage_features(usage))
            except XivaAPIError as e:
                logger.warning(f"Could not fetch usage data for {customer_id}: {e}")
            
            return features
            
        except XivaAPIError as e:
            logger.error(f"Error extracting features from Xiva for customer {customer_id}: {e}")
            return features
    
    @staticmethod
    def _extract_customer_basic(customer: Dict) -> Dict[str, Any]:
        """Extract basic customer information"""
        features = {}
        
        # Status
        features['customer_status'] = customer.get('status', 'unknown')
        
        # Customer type
        features['customer_type'] = customer.get('customerType', 'unknown')
        
        # Individual details
        individual = customer.get('engagedIndividual', {})
        if individual:
            features['first_name'] = individual.get('givenName', '')
            features['last_name'] = individual.get('familyName', '')
            features['gender'] = individual.get('gender', '')
            features['nationality'] = individual.get('nationality', '')
            
            # Age calculation
            birth_date_str = individual.get('birthDate')
            if birth_date_str:
                try:
                    birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                    today = date.today()
                    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                    features['age'] = age
                except Exception:
                    pass
        
        # Contact info
        contact_medium = customer.get('contactMedium', [])
        if contact_medium:
            for contact in contact_medium:
                if contact.get('type') == 'email' and contact.get('email'):
                    features['email'] = contact.get('email')
                elif contact.get('type') == 'phone' and contact.get('phoneNumber'):
                    features['phone'] = contact.get('phoneNumber')
        
        return features
    
    @staticmethod
    def _extract_financial_features(financial: Dict) -> Dict[str, Any]:
        """Extract financial features"""
        features = {}
        
        # Revenue/Spend
        features['total_revenue'] = float(financial.get('total_bills', 0) or 0)
        features['current_month_spend'] = float(financial.get('current_balance', 0) or 0)
        features['outstanding_amount'] = float(financial.get('outstanding_amount', 0) or 0)
        
        # Credit
        features['credit_limit'] = float(financial.get('credit_limit', 0) or 0)
        features['credit_utilization'] = 0.0
        if features['credit_limit'] > 0:
            features['credit_utilization'] = abs(features['outstanding_amount']) / features['credit_limit']
        
        # Payment behavior
        features['last_payment_amount'] = float(financial.get('last_payment_amount', 0) or 0)
        last_payment_date = financial.get('last_payment_date')
        if last_payment_date:
            try:
                # Handle different date formats
                if 'T' in last_payment_date:
                    payment_date = datetime.fromisoformat(last_payment_date.replace('Z', '+00:00'))
                else:
                    payment_date = datetime.strptime(last_payment_date, '%Y-%m-%d')
                
                days_since_payment = (datetime.now(payment_date.tzinfo) if payment_date.tzinfo else datetime.now()) - payment_date.replace(tzinfo=None)
                features['days_since_last_payment'] = days_since_payment.days
            except Exception:
                pass
        
        # Payment ratio
        total_payments = float(financial.get('total_payments', 0) or 0)
        if features['total_revenue'] > 0:
            features['payment_ratio'] = total_payments / features['total_revenue']
        else:
            features['payment_ratio'] = 0.0
        
        return features
    
    @staticmethod
    def _extract_service_features(services: Dict) -> Dict[str, Any]:
        """Extract service/product features"""
        features = {}
        
        # Product instances
        product_instances = services.get('product_instances', [])
        features['active_products_count'] = len(product_instances)
        
        # Active services
        features['active_services_count'] = services.get('active_services', 0)
        features['total_services_count'] = services.get('total_services', 0)
        
        # Service status
        individual_services = services.get('individual_services', [])
        active_voice = sum(1 for s in individual_services if s.get('category') == 'voice' and s.get('state') == 'active')
        active_data = sum(1 for s in individual_services if s.get('category') == 'data' and s.get('state') == 'active')
        active_sms = sum(1 for s in individual_services if s.get('category') == 'sms' and s.get('state') == 'active')
        
        features['has_voice_service'] = active_voice > 0
        features['has_data_service'] = active_data > 0
        features['has_sms_service'] = active_sms > 0
        
        # Product names (for segmentation by plan)
        product_names = [p.get('name', '') for p in product_instances if p.get('status') == 'active']
        features['product_names'] = product_names
        if product_names:
            features['primary_product'] = product_names[0]
        
        return features
    
    @staticmethod
    def _extract_usage_features(usage: Dict) -> Dict[str, Any]:
        """Extract usage features"""
        features = {}
        
        usage_summary = usage.get('usage_summary', {})
        
        # Spend
        features['current_month_usage_spend'] = float(usage_summary.get('current_month_spend', 0) or 0)
        features['total_usage_spend'] = float(usage_summary.get('total_spend', 0) or 0)
        features['usage_records_count'] = int(usage_summary.get('total_records', 0) or 0)
        
        # Usage by type (if available)
        by_date = usage.get('by_date_and_type', {})
        if isinstance(by_date, dict):
            # Aggregate usage by type
            voice_usage = 0
            data_usage = 0
            sms_usage = 0
            
            for date_key, usage_data in by_date.items():
                if isinstance(usage_data, dict):
                    voice_usage += float(usage_data.get('VOICE_LOCAL', {}).get('volume_mb', 0) or 0)
                    data_usage += float(usage_data.get('DATA', {}).get('volume_mb', 0) or 0)
                    sms_usage += float(usage_data.get('SMS', {}).get('count', 0) or 0)
            
            features['voice_usage_mb'] = voice_usage
            features['data_usage_mb'] = data_usage
            features['sms_usage_count'] = sms_usage
        
        return features

