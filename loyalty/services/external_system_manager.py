"""
External System Manager - Manages connections to external systems
"""
import logging
import time
import requests
from typing import Dict, Optional, Any
from django.utils import timezone
from loyalty.models_khaywe import ExternalSystemConfig

logger = logging.getLogger(__name__)


class TokenManager:
    """Manages JWT tokens for external system authentication"""
    
    def __init__(self, config: ExternalSystemConfig):
        self.config = config
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
    
    def get_valid_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if needed"""
        now = timezone.now().timestamp()
        
        # Check if token is still valid (with buffer)
        if self.access_token and self.token_expiry and (self.token_expiry - now) > self.config.token_refresh_buffer:
            return self.access_token
        
        # Refresh or get new token
        if self.refresh_token:
            if not self._refresh_access_token():
                # Refresh failed, get new token
                return self._authenticate()
        else:
            return self._authenticate()
        
        return self.access_token
    
    def _authenticate(self) -> Optional[str]:
        """Authenticate and get new tokens"""
        if not self.config.auth_endpoint or not self.config.client_id or not self.config.client_secret:
            logger.error(f"Missing authentication credentials for {self.config.name}")
            return None
        
        try:
            auth_url = f"{self.config.base_url.rstrip('/')}/{self.config.auth_endpoint.lstrip('/')}"
            
            # Xiva API accepts either "username" or "email" field
            # If it looks like an email, use "email", otherwise use "username"
            username = self.config.client_id
            if '@' in username:
                payload = {
                    'email': username,
                    'password': self.config.client_secret,
                }
            else:
                payload = {
                    'username': username,
                    'password': self.config.client_secret,
                }
            
            response = requests.post(
                auth_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access')
                self.refresh_token = data.get('refresh')
                # Access token typically expires in 2 hours (7200 seconds)
                expires_in = data.get('access_expires_in', 7200)
                self.token_expiry = timezone.now().timestamp() + expires_in
                logger.info(f"Successfully authenticated with {self.config.name}")
                return self.access_token
            else:
                logger.error(f"Authentication failed for {self.config.name}: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.exception(f"Error authenticating with {self.config.name}: {e}")
            return None
    
    def _refresh_access_token(self) -> bool:
        """Refresh access token using refresh token"""
        if not self.config.refresh_endpoint or not self.refresh_token:
            return False
        
        try:
            refresh_url = f"{self.config.base_url.rstrip('/')}/{self.config.refresh_endpoint.lstrip('/')}"
            
            response = requests.post(
                refresh_url,
                json={'refresh': self.refresh_token},
                headers={'Content-Type': 'application/json'},
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access')
                expires_in = data.get('access_expires_in', 3600)
                self.token_expiry = timezone.now().timestamp() + expires_in
                logger.info(f"Successfully refreshed token for {self.config.name}")
                return True
            else:
                logger.warning(f"Token refresh failed for {self.config.name}: {response.status_code}")
                return False
        except Exception as e:
            logger.exception(f"Error refreshing token for {self.config.name}: {e}")
            return False


class ExternalSystemManager:
    """Manages connections and requests to external systems"""
    
    def __init__(self, config: ExternalSystemConfig):
        self.config = config
        self.token_manager = TokenManager(config) if config.auth_type == 'jwt' else None
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = self.config.get_all_headers()
        
        # Add Bearer token if JWT auth
        if self.config.auth_type == 'jwt' and self.token_manager:
            token = self.token_manager.get_valid_token()
            if token:
                headers['Authorization'] = f"Bearer {token}"
        elif self.config.auth_type == 'bearer':
            # For bearer token, use client_secret as token (or get from token manager)
            if self.config.client_secret:
                headers['Authorization'] = f"Bearer {self.config.client_secret}"
        
        return headers
    
    def make_request(self, endpoint_key: str, method: str = 'GET', params: Optional[Dict] = None, data: Optional[Dict] = None) -> requests.Response:
        """Make HTTP request to external system using endpoint key"""
        endpoint_path = self.config.endpoints.get(endpoint_key)
        if not endpoint_path:
            raise ValueError(f"Endpoint '{endpoint_key}' not configured for system '{self.config.name}'")
        
        url = f"{self.config.base_url.rstrip('/')}/{endpoint_path.lstrip('/')}"
        headers = self.get_headers()
        
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                params=params,
                json=data,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"API request to {url} failed for {self.config.name}: {e}")
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to external system"""
        try:
            # Try to authenticate if JWT
            if self.config.auth_type == 'jwt':
                token = self.token_manager.get_valid_token()
                if not token:
                    return {
                        'success': False,
                        'error': 'Failed to authenticate',
                        'details': {'step': 'authentication'},
                    }
            
            # Try a simple API call (health check or get products)
            if 'products' in (self.config.endpoints or {}):
                # Try to get first page
                try:
                    response = self.make_request('products', method='GET', params={'limit': 1})
                    return {
                        'success': True,
                        'details': {
                            'message': 'Connection and authentication successful',
                            'status_code': response.status_code,
                        },
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'API call failed: {str(e)}',
                        'details': {'error': str(e)},
                    }
            else:
                # No products endpoint, just test auth
                if self.config.auth_type == 'jwt' and self.token_manager.get_valid_token():
                    return {
                        'success': True,
                        'details': {'message': 'Authentication successful'},
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No test endpoint configured',
                    }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Connection timeout',
                'details': {'timeout': self.config.timeout},
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection error - check base_url and network',
                'details': {'base_url': self.config.base_url},
            }
        except Exception as e:
            logger.exception(f"Error testing connection to {self.config.name}: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def get_products(self, **params) -> Dict[str, Any]:
        """Get products from external system"""
        if 'products' not in (self.config.endpoints or {}):
            return {'success': False, 'error': 'Products endpoint not configured. Please configure it in External Systems Config.'}
        
        try:
            # Use make_request which handles authentication
            response = self.make_request('products', method='GET', params=params)
            result = response.json()
            return {
                'success': True,
                'data': result,
            }
        except requests.exceptions.RequestException as e:
            logger.exception(f"Error fetching products from {self.config.name}: {e}")
            status_code = getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500
            response_text = getattr(e.response, 'text', str(e)) if hasattr(e, 'response') else str(e)
            return {
                'success': False,
                'error': f'API request failed: {status_code} - {response_text[:200]}',
                'status_code': status_code,
            }
        except Exception as e:
            logger.exception(f"Error fetching products from {self.config.name}: {e}")
            return {
                'success': False,
                'error': str(e),
            }

