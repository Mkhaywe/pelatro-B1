"""
Xiva BSS API Client for Pelatro Loyalty Integration

This module provides a comprehensive client for integrating with Xiva BSS system
to fetch customer data, products, usage, and billing information.

Based on TMF-compliant APIs:
- TMF629: Customer Management
- TMF622: Product Ordering
- TMF635: Usage Management
- TMF620: Product Catalog
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, date
import requests
import os
from django.conf import settings
from .external import ExternalServiceError

logger = logging.getLogger(__name__)


class XivaAPIError(Exception):
    """Raised when Xiva API call fails"""
    pass


class XivaClient:
    """
    Client for Xiva BSS API integration with JWT authentication.
    
    Configuration required in settings:
    - XIVA_API_BASE_URL: Base URL for Xiva API (e.g., https://www.xiva.ca/api)
    - XIVA_API_AUTH_TYPE: Authentication type ('JWT', 'Token', or 'Bearer')
    - XIVA_API_USERNAME: Username for JWT login (if using JWT)
    - XIVA_API_PASSWORD: Password for JWT login (if using JWT)
    - XIVA_API_AUTH_TOKEN: Static token (if using Token/Bearer auth)
    - XIVA_API_TIMEOUT: Request timeout in seconds (default: 30)
    """
    
    def __init__(self):
        # Force reload .env file to ensure credentials are available
        try:
            from pathlib import Path
            # Get project root (go up from loyalty/integration to project root)
            project_root = Path(__file__).resolve().parent.parent.parent
            env_path = project_root / '.env'
            
            if env_path.exists():
                # Try using dotenv first
                try:
                    from dotenv import load_dotenv
                    load_dotenv(env_path, override=True)
                    logger.info(f"Reloaded .env file using dotenv from {env_path}")
                except ImportError:
                    # If dotenv not available, parse manually
                    logger.warning("python-dotenv not available, parsing .env manually")
                    try:
                        with open(env_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#') and '=' in line:
                                    key, value = line.split('=', 1)
                                    key = key.strip()
                                    value = value.strip().strip('"').strip("'")
                                    if key.startswith('XIVA_'):
                                        os.environ[key] = value
                                        logger.debug(f"Loaded {key} from .env")
                        logger.info(f"Manually loaded .env file from {env_path}")
                    except Exception as e:
                        logger.error(f"Could not manually load .env file: {e}")
                except Exception as e:
                    logger.error(f"Error using dotenv: {e}, trying manual load")
                    # Fallback to manual parsing
                    try:
                        with open(env_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#') and '=' in line:
                                    key, value = line.split('=', 1)
                                    key = key.strip()
                                    value = value.strip().strip('"').strip("'")
                                    if key.startswith('XIVA_'):
                                        os.environ[key] = value
                        logger.info(f"Manually loaded .env file (fallback) from {env_path}")
                    except Exception as e2:
                        logger.error(f"Could not manually load .env file: {e2}")
            else:
                logger.warning(f".env file not found at {env_path}")
        except Exception as e:
            logger.error(f"Could not reload .env file: {e}")
        
        # Read from os.environ first (most reliable), then fall back to settings
        self.base_url = (os.environ.get('XIVA_API_BASE_URL', '') or getattr(settings, 'XIVA_API_BASE_URL', '')).rstrip('/')
        self.auth_type = (os.environ.get('XIVA_API_AUTH_TYPE', '') or getattr(settings, 'XIVA_API_AUTH_TYPE', 'JWT')).upper()  # JWT, Token, or Bearer
        self.timeout = int(os.environ.get('XIVA_API_TIMEOUT', '') or getattr(settings, 'XIVA_API_TIMEOUT', '30'))
        
        # JWT authentication
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
        # Static token (for Token/Bearer auth)
        self.auth_token = os.environ.get('XIVA_API_AUTH_TOKEN', '') or getattr(settings, 'XIVA_API_AUTH_TOKEN', '')
        
        if not self.base_url:
            logger.warning("XIVA_API_BASE_URL not configured. Xiva integration disabled.")
        
        # Auto-login if using JWT and credentials are provided
        if self.auth_type == 'JWT':
            # Read from os.environ first (most reliable)
            username = os.environ.get('XIVA_API_USERNAME', '') or getattr(settings, 'XIVA_API_USERNAME', '')
            password = os.environ.get('XIVA_API_PASSWORD', '') or getattr(settings, 'XIVA_API_PASSWORD', '')
            logger.info(f"XivaClient.__init__: Attempting auto-login. Username: {'SET' if username else 'NOT SET'}, Password: {'SET' if password else 'NOT SET'}")
            if username and password:
                try:
                    self.login(username, password)
                    logger.info("XivaClient.__init__: Auto-login successful")
                except Exception as e:
                    logger.warning(f"Auto-login failed: {e}. Will login on first request.")
            else:
                logger.warning(f"XivaClient.__init__: Credentials not available for auto-login. os.environ XIVA_API_USERNAME: {os.environ.get('XIVA_API_USERNAME', 'NOT SET')}")
    
    def login(self, username: str = None, password: str = None) -> str:
        """
        Get JWT tokens from Xiva API
        
        Args:
            username: Username or email for login
            password: Password for login
        
        Returns:
            Access token string
        
        Raises:
            XivaAPIError: If login fails
        """
        if not username:
            username = getattr(settings, 'XIVA_API_USERNAME', '')
        if not password:
            password = getattr(settings, 'XIVA_API_PASSWORD', '')
        
        if not username or not password:
            raise XivaAPIError("Username/email and password required for JWT login")
        
        url = f"{self.base_url}/auth/jwt/create/"
        
        # Xiva API accepts either "username" or "email" field
        # If it looks like an email, use "email", otherwise use "username"
        if '@' in username:
            payload = {
                "email": username,
                "password": password
            }
        else:
            payload = {
                "username": username,
                "password": password
            }
        
        try:
            logger.debug(f"Logging in to Xiva API as {username}")
            response = requests.post(url, json=payload, timeout=self.timeout)
            
            if not response.ok:
                error_msg = f"Login failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise XivaAPIError(error_msg)
            
            data = response.json()
            self.access_token = data.get('access')
            self.refresh_token = data.get('refresh')
            
            if not self.access_token:
                raise XivaAPIError("No access token in login response")
            
            # Access token expires in 2 hours
            self.token_expires_at = datetime.now() + timedelta(hours=2)
            
            logger.info("Successfully logged in to Xiva API")
            return self.access_token
        
        except requests.exceptions.RequestException as e:
            raise XivaAPIError(f"Login request failed: {str(e)}")
    
    def refresh_access_token(self) -> str:
        """
        Refresh access token using refresh token
        
        Returns:
            New access token string
        
        Raises:
            XivaAPIError: If refresh fails
        """
        if not self.refresh_token:
            raise XivaAPIError("No refresh token available. Please login first.")
        
        url = f"{self.base_url}/auth/jwt/refresh/"
        payload = {
            "refresh": self.refresh_token
        }
        
        try:
            logger.debug("Refreshing Xiva API access token")
            response = requests.post(url, json=payload, timeout=self.timeout)
            
            if not response.ok:
                error_msg = f"Token refresh failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                # If refresh fails, try to login again
                logger.info("Refresh token expired, attempting to login again")
                username = getattr(settings, 'XIVA_API_USERNAME', '')
                password = getattr(settings, 'XIVA_API_PASSWORD', '')
                if username and password:
                    return self.login(username, password)
                raise XivaAPIError(error_msg)
            
            data = response.json()
            self.access_token = data.get('access')
            
            if not self.access_token:
                raise XivaAPIError("No access token in refresh response")
            
            # Access token expires in 2 hours
            self.token_expires_at = datetime.now() + timedelta(hours=2)
            
            logger.debug("Successfully refreshed access token")
            return self.access_token
        
        except requests.exceptions.RequestException as e:
            raise XivaAPIError(f"Token refresh request failed: {str(e)}")
    
    def _ensure_valid_token(self):
        """Ensure access token is valid, refresh if needed"""
        if self.auth_type != 'JWT':
            return  # Only needed for JWT
        
        if not self.access_token:
            # Try to login - always check os.environ first, then settings
            username = os.environ.get('XIVA_API_USERNAME', '') or getattr(settings, 'XIVA_API_USERNAME', '')
            password = os.environ.get('XIVA_API_PASSWORD', '') or getattr(settings, 'XIVA_API_PASSWORD', '')
            if username and password:
                try:
                    logger.info(f"Attempting to login to Xiva API with username: {username}")
                    self.login(username, password)
                    logger.info("Successfully logged in to Xiva API")
                except Exception as e:
                    logger.error(f"Failed to login to Xiva API: {e}")
                    raise XivaAPIError(f"Failed to authenticate with Xiva API: {str(e)}")
            else:
                logger.error(f"Xiva credentials not found. Username: {'SET' if username else 'NOT SET'}, Password: {'SET' if password else 'NOT SET'}")
                raise XivaAPIError("Not authenticated. Please configure XIVA_API_USERNAME and XIVA_API_PASSWORD")
        
        # Check if token is about to expire (within 5 minutes)
        if self.token_expires_at and datetime.now() >= (self.token_expires_at - timedelta(minutes=5)):
            try:
                self.refresh_access_token()
            except Exception as e:
                logger.warning(f"Token refresh failed, trying login: {e}")
                username = getattr(settings, 'XIVA_API_USERNAME', '')
                password = getattr(settings, 'XIVA_API_PASSWORD', '')
                if username and password:
                    self.login(username, password)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        if self.auth_type == 'JWT':
            self._ensure_valid_token()
            if self.access_token:
                headers['Authorization'] = f'JWT {self.access_token}'
        elif self.auth_type == 'BEARER':
            if self.auth_token:
                headers['Authorization'] = f'Bearer {self.auth_token}'
        else:  # Token (default)
            if self.auth_token:
                headers['Authorization'] = f'Token {self.auth_token}'
        
        return headers
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                 data: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request to Xiva API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (without base URL)
            params: Query parameters
            data: Request body data
        
        Returns:
            JSON response as dict
        
        Raises:
            XivaAPIError: If request fails
        """
        if not self.base_url:
            raise XivaAPIError("Xiva API base URL not configured")
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        try:
            logger.debug(f"Xiva API {method} {url} with params={params}")
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=self.timeout
            )
            
            # Log response for debugging
            logger.debug(f"Xiva API response: {response.status_code}")
            
            # Handle errors
            if response.status_code == 404:
                raise XivaAPIError(f"Resource not found: {endpoint}")
            elif response.status_code == 401:
                raise XivaAPIError("Authentication failed. Check XIVA_API_AUTH_TOKEN")
            elif response.status_code == 403:
                raise XivaAPIError("Access forbidden. Check API permissions")
            elif not response.ok:
                error_msg = f"Xiva API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise XivaAPIError(error_msg)
            
            # Parse JSON response
            try:
                return response.json()
            except ValueError:
                logger.warning(f"Non-JSON response from Xiva API: {response.text[:200]}")
                return {'raw_response': response.text}
        
        except requests.exceptions.Timeout:
            raise XivaAPIError(f"Request timeout after {self.timeout}s")
        except requests.exceptions.ConnectionError as e:
            raise XivaAPIError(f"Connection error: {str(e)}")
        except XivaAPIError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error calling Xiva API: {e}")
            raise XivaAPIError(f"Unexpected error: {str(e)}")
    
    # ============================================================================
    # Customer Management APIs (TMF629)
    # ============================================================================
    
    def get_customer_list(self, search: Optional[str] = None, 
                         status: Optional[str] = None,
                         customer_type: Optional[str] = None,
                         ordering: Optional[str] = None,
                         fetch_all: bool = False,
                         limit: Optional[int] = None) -> List[Dict]:
        """
        Get customer list
        
        GET /api/customerManagement/v4/customer/
        
        Args:
            search: Search by name, email, phone
            status: Filter by status (active, suspended, etc.)
            customer_type: Filter by type (individual, organization)
            ordering: Sort by field (e.g., '-creationDate')
            fetch_all: If True, fetch all customers by making multiple requests (default: False)
                      Note: Xiva API has a hard limit of 50 results per request
            limit: Maximum number of results to return (None = no limit when fetch_all=True)
        
        Returns:
            List of customer objects
        """
        params = {}
        if search:
            params['search'] = search
        if status:
            params['status'] = status
        if customer_type:
            params['customerType'] = customer_type
        if ordering:
            params['ordering'] = ordering
        
        # Base URL already includes /api, so don't add it again
        response = self._request('GET', 'customerManagement/v4/customer/', params=params)
        
        # Handle paginated responses
        if isinstance(response, list):
            customers = response
        elif isinstance(response, dict) and 'results' in response:
            customers = response['results']
        elif isinstance(response, dict) and 'data' in response:
            customers = response['data']
        else:
            customers = [response] if response else []
        
        # If fetch_all is True and we got 50 results, try to get more
        # Note: Xiva API appears to have a hard limit of 50 results per request
        # and pagination may not be fully supported. This is a best-effort attempt.
        if fetch_all and len(customers) == 50:
            logger.info(f"Got 50 customers (API limit). Attempting to fetch more...")
            
            # Try offset-based pagination
            all_customers = customers.copy()
            offset = 50
            max_attempts = 100  # Safety limit to prevent infinite loops
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    # Try with offset parameter
                    offset_params = params.copy()
                    offset_params['offset'] = str(offset)
                    
                    offset_response = self._request('GET', 'customerManagement/v4/customer/', params=offset_params)
                    
                    if isinstance(offset_response, list):
                        offset_customers = offset_response
                    elif isinstance(offset_response, dict) and 'results' in offset_response:
                        offset_customers = offset_response['results']
                    elif isinstance(offset_response, dict) and 'data' in offset_response:
                        offset_customers = offset_response['data']
                    else:
                        offset_customers = [offset_response] if offset_response else []
                    
                    # If we got no results or same results, stop
                    if not offset_customers or len(offset_customers) == 0:
                        logger.debug(f"No more customers at offset {offset}")
                        break
                    
                    # Check if we're getting duplicate results (pagination not working)
                    if offset_customers[0].get('id') == all_customers[0].get('id'):
                        logger.warning(f"Pagination not working - got same results at offset {offset}")
                        break
                    
                    all_customers.extend(offset_customers)
                    
                    # If we got less than 50, we've reached the end
                    if len(offset_customers) < 50:
                        break
                    
                    # Apply limit if specified
                    if limit and len(all_customers) >= limit:
                        all_customers = all_customers[:limit]
                        break
                    
                    offset += len(offset_customers)
                    attempt += 1
                    
                except XivaAPIError as e:
                    logger.warning(f"Error fetching customers at offset {offset}: {e}")
                    break
            
            customers = all_customers
            logger.info(f"Fetched {len(customers)} total customers")
        
        # Apply limit if specified and fetch_all is False
        if limit and not fetch_all:
            customers = customers[:limit]
        
        return customers
    
    def get_customer_details(self, customer_id: str) -> Dict:
        """
        Get customer details
        
        GET /api/customerManagement/v4/customer/{customer_id}/
        
        Args:
            customer_id: Customer ID
        
        Returns:
            Full customer object
        """
        return self._request('GET', f'customerManagement/v4/customer/{customer_id}/')
    
    def get_customer_360_overview(self, customer_id: str) -> Dict:
        """
        Get Customer 360 Overview - High-level summary
        
        GET /api/customerManagement/v4/customers/{customer_id}/360/overview/
        
        Returns:
            Customer summary, status, key metrics
        """
        return self._request('GET', f'customerManagement/v4/customers/{customer_id}/360/overview/')
    
    def get_customer_360_services(self, customer_id: str) -> Dict:
        """
        Get Customer 360 Services - Products, subscriptions, usage
        
        GET /api/customerManagement/v4/customers/{customer_id}/360/services/
        
        This is the BEST endpoint for Pelatro - combines products and usage in one call!
        
        Returns:
            Active product instances, subscriptions, service history, usage summary
        """
        return self._request('GET', f'customerManagement/v4/customers/{customer_id}/360/services/')
    
    def get_customer_360_usage(self, customer_id: str,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None,
                               usage_type: Optional[str] = None,
                               current_month_only: Optional[bool] = None) -> Dict:
        """
        Get Customer 360 Usage - Detailed usage data
        
        GET /api/customerManagement/v4/customers/{customer_id}/360/usage/
        
        Args:
            customer_id: Customer ID
            start_date: Filter from date (YYYY-MM-DD)
            end_date: Filter to date (YYYY-MM-DD)
            usage_type: Filter by type (VOICE_LOCAL, DATA, SMS)
            current_month_only: If true, only current month
        
        Returns:
            Usage summary with by_date_and_type breakdown
        """
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if usage_type:
            params['usage_type'] = usage_type
        if current_month_only is not None:
            params['current_month_only'] = str(current_month_only).lower()
        
        return self._request('GET', f'customerManagement/v4/customers/{customer_id}/360/usage/', params=params)
    
    def get_customer_360_financial(self, customer_id: str) -> Dict:
        """
        Get Customer 360 Financial - Billing and payments
        
        GET /api/customerManagement/v4/customers/{customer_id}/360/financial/
        
        Returns:
            Bills, payments, outstanding balances, payment history
        """
        return self._request('GET', f'customerManagement/v4/customers/{customer_id}/360/financial/')
    
    def get_customer_360_complete(self, customer_id: str) -> Dict:
        """
        Get Customer 360 Complete - All customer data in one response
        
        GET /api/customerManagement/v4/customers/{customer_id}/360/complete/
        
        Note: Large payload - use only when needed
        """
        return self._request('GET', f'customerManagement/v4/customers/{customer_id}/360/complete/')
    
    # ============================================================================
    # Product Ordering APIs (TMF622)
    # ============================================================================
    
    def get_customer_product_instances(self, customer_id: str) -> List[Dict]:
        """
        Get product instances for customer
        
        GET /api/productOrdering/v5/customerProductInstances/?customer_id={customer_id}
        
        Returns:
            List of product instances (subscriptions) for the customer
        """
        params = {'customer_id': customer_id}
        response = self._request('GET', 'productOrdering/v5/customerProductInstances/', params=params)
        
        if isinstance(response, list):
            return response
        elif isinstance(response, dict) and 'results' in response:
            return response['results']
        elif isinstance(response, dict) and 'data' in response:
            return response['data']
        else:
            return [response] if response else []
    
    def get_product_instance_details(self, order_id: str) -> Dict:
        """
        Get product instance details from order
        
        GET /api/productOrdering/v5/productOrder/{order_id}/productInstances
        """
        return self._request('GET', f'productOrdering/v5/productOrder/{order_id}/productInstances')
    
    def get_product_inventory(self, customer_id: str) -> List[Dict]:
        """
        Get product inventory for customer
        
        GET /api/productInventoryManagement/v5/product/?customer={customer_id}
        """
        params = {'customer': customer_id}
        response = self._request('GET', 'productInventoryManagement/v5/product/', params=params)
        
        if isinstance(response, list):
            return response
        elif isinstance(response, dict) and 'results' in response:
            return response['results']
        elif isinstance(response, dict) and 'data' in response:
            return response['data']
        else:
            return [response] if response else []
    
    # ============================================================================
    # Usage Management APIs (TMF635)
    # ============================================================================
    
    def get_rated_usage_records(self, customer: Optional[str] = None,
                                billing_account: Optional[str] = None,
                                usage_type: Optional[str] = None,
                                usage_date__gte: Optional[str] = None,
                                usage_date__lte: Optional[str] = None,
                                billing_status: Optional[str] = None) -> List[Dict]:
        """
        Get rated usage records
        
        GET /api/usageManagement/v4/ratedProductUsage/
        
        Args:
            customer: Filter by customer ID
            billing_account: Filter by billing account ID
            usage_type: Filter by type (data, voice, sms)
            usage_date__gte: Filter from date (YYYY-MM-DD)
            usage_date__lte: Filter to date (YYYY-MM-DD)
            billing_status: Filter by status (pending, billed)
        
        Returns:
            Array of rated usage records
        """
        params = {}
        if customer:
            params['customer'] = customer
        if billing_account:
            params['billing_account'] = billing_account
        if usage_type:
            params['usage_type'] = usage_type
        if usage_date__gte:
            params['usage_date__gte'] = usage_date__gte
        if usage_date__lte:
            params['usage_date__lte'] = usage_date__lte
        if billing_status:
            params['billing_status'] = billing_status
        
        response = self._request('GET', 'usageManagement/v4/ratedProductUsage/', params=params)
        
        if isinstance(response, list):
            return response
        elif isinstance(response, dict) and 'results' in response:
            return response['results']
        elif isinstance(response, dict) and 'data' in response:
            return response['data']
        else:
            return [response] if response else []
    
    def get_raw_usage_records(self, customer: Optional[str] = None,
                              billing_account: Optional[str] = None,
                              usage_type: Optional[str] = None,
                              usage_date__gte: Optional[str] = None,
                              usage_date__lte: Optional[str] = None) -> List[Dict]:
        """
        Get raw usage records (CDR records before rating)
        
        GET /api/usageManagement/v4/usageRecord/
        """
        params = {}
        if customer:
            params['customer'] = customer
        if billing_account:
            params['billing_account'] = billing_account
        if usage_type:
            params['usage_type'] = usage_type
        if usage_date__gte:
            params['usage_date__gte'] = usage_date__gte
        if usage_date__lte:
            params['usage_date__lte'] = usage_date__lte
        
        response = self._request('GET', 'usageManagement/v4/usageRecord/', params=params)
        
        if isinstance(response, list):
            return response
        elif isinstance(response, dict) and 'results' in response:
            return response['results']
        elif isinstance(response, dict) and 'data' in response:
            return response['data']
        else:
            return [response] if response else []
    
    # ============================================================================
    # Billing Account APIs (TMF629)
    # ============================================================================
    
    def get_billing_accounts(self, customer: Optional[str] = None,
                            status: Optional[str] = None) -> List[Dict]:
        """
        Get billing accounts
        
        GET /api/customerManagement/v4/customerAccount/
        
        Args:
            customer: Filter by customer ID
            status: Filter by status
        
        Returns:
            List of billing accounts
        """
        params = {}
        if customer:
            params['customer'] = customer
        if status:
            params['status'] = status
        
        response = self._request('GET', 'customerManagement/v4/customerAccount/', params=params)
        
        if isinstance(response, list):
            return response
        elif isinstance(response, dict) and 'results' in response:
            return response['results']
        elif isinstance(response, dict) and 'data' in response:
            return response['data']
        else:
            return [response] if response else []
    
    def get_billing_account_details(self, account_id: str) -> Dict:
        """
        Get billing account details
        
        GET /api/customerManagement/v4/customerAccount/{account_id}/
        """
        return self._request('GET', f'customerManagement/v4/customerAccount/{account_id}/')
    
    # ============================================================================
    # Product Catalog APIs (TMF620)
    # ============================================================================
    
    def get_product_offerings(self, search: Optional[str] = None,
                             status: Optional[str] = None,
                             is_bundle: Optional[bool] = None) -> List[Dict]:
        """
        Get product offerings
        
        GET /api/productCatalogManagement/v5/productOffering/
        
        Args:
            search: Search by name
            status: Filter by status
            is_bundle: Filter bundles
        
        Returns:
            List of available product offerings
        """
        params = {}
        if search:
            params['search'] = search
        if status:
            params['status'] = status
        if is_bundle is not None:
            params['isBundle'] = str(is_bundle).lower()
        
        response = self._request('GET', 'productCatalogManagement/v5/productOffering/', params=params)
        
        if isinstance(response, list):
            return response
        elif isinstance(response, dict) and 'results' in response:
            return response['results']
        elif isinstance(response, dict) and 'data' in response:
            return response['data']
        else:
            return [response] if response else []
    
    def get_product_offering_details(self, offering_id: str) -> Dict:
        """
        Get product offering details
        
        GET /api/productCatalogManagement/v5/productOffering/{offering_id}/
        """
        return self._request('GET', f'productCatalogManagement/v5/productOffering/{offering_id}/')
    
    # ============================================================================
    # Convenience Methods for Common Use Cases
    # ============================================================================
    
    def get_customer_full_context(self, customer_id: str) -> Dict:
        """
        Get comprehensive customer context for loyalty decisions.
        
        This method combines multiple API calls to get all relevant customer data:
        - Customer details
        - Products/services
        - Usage summary
        - Billing accounts
        
        This is the recommended method for getting customer context in loyalty workflows.
        """
        context = {
            'customer_id': customer_id,
            'timestamp': datetime.now().isoformat(),
        }
        
        try:
            # Get customer 360 services (best endpoint - combines products + usage)
            services = self.get_customer_360_services(customer_id)
            context['services'] = services
            
            # Get customer details
            try:
                customer_details = self.get_customer_details(customer_id)
                context['customer'] = customer_details
            except XivaAPIError as e:
                logger.warning(f"Could not fetch customer details: {e}")
                context['customer'] = None
            
            # Get billing accounts
            try:
                billing_accounts = self.get_billing_accounts(customer=customer_id)
                context['billing_accounts'] = billing_accounts
            except XivaAPIError as e:
                logger.warning(f"Could not fetch billing accounts: {e}")
                context['billing_accounts'] = []
        
        except XivaAPIError as e:
            logger.error(f"Error fetching customer context from Xiva: {e}")
            raise
        
        return context


# Singleton instance
_xiva_client = None


def get_xiva_client() -> XivaClient:
    """Get singleton Xiva client instance"""
    global _xiva_client
    
    # Always check os.environ first (most reliable), then settings
    try:
        username = os.environ.get('XIVA_API_USERNAME', '') or getattr(settings, 'XIVA_API_USERNAME', '') or ''
        password = os.environ.get('XIVA_API_PASSWORD', '') or getattr(settings, 'XIVA_API_PASSWORD', '') or ''
    except Exception as e:
        logger.warning(f"Error accessing settings: {e}")
        username = os.environ.get('XIVA_API_USERNAME', '') or ''
        password = os.environ.get('XIVA_API_PASSWORD', '') or ''
    
    # Check if we need to recreate the client (e.g., if credentials weren't available before)
    if _xiva_client is None:
        logger.info("Creating new XivaClient instance")
        _xiva_client = XivaClient()
    elif _xiva_client.auth_type == 'JWT' and not _xiva_client.access_token:
        # If client exists but has no token, always try to recreate it
        # This handles the case where the singleton was created before credentials were loaded
        logger.warning(f"XivaClient exists but no token. Recreating client to pick up credentials...")
        logger.info(f"  Current settings - Username: {'SET' if username else 'NOT SET'}, Password: {'SET' if password else 'NOT SET'}")
        try:
            _xiva_client = XivaClient()
            if _xiva_client.access_token:
                logger.info("Successfully recreated XivaClient with credentials")
            else:
                logger.warning("Recreated XivaClient but still no token - credentials may not be available")
        except Exception as e:
            logger.error(f"Failed to recreate XivaClient: {e}")
    
    return _xiva_client


def reset_xiva_client():
    """Reset the singleton Xiva client instance (useful for testing or after config changes)"""
    global _xiva_client
    _xiva_client = None
