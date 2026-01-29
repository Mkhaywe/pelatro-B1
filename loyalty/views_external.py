"""
API views for external system integration (Xiva, DWH, etc.)

These endpoints allow testing and integration with external systems
like Xiva BSS for fetching customer data.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
import logging

from loyalty.integration.xiva_client import get_xiva_client, XivaAPIError

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_xiva_connection(request):
    """
    Test Xiva API connection
    
    GET /api/external/xiva/test/
    """
    try:
        client = get_xiva_client()
        
        # Check authentication status
        auth_configured = False
        if client.auth_type == 'JWT':
            auth_configured = bool(client.access_token) or (
                bool(getattr(settings, 'XIVA_API_USERNAME', '')) and 
                bool(getattr(settings, 'XIVA_API_PASSWORD', ''))
            )
        else:
            auth_configured = bool(client.auth_token)
        
        # Try to get customer list (empty query to test connection)
        try:
            customers = client.get_customer_list(ordering='-creationDate')
            return Response({
                'status': 'success',
                'message': 'Xiva API connection successful',
                'config': {
                    'base_url': client.base_url if client.base_url else 'Not configured',
                    'auth_type': client.auth_type,
                    'auth_configured': auth_configured,
                    'has_access_token': bool(client.access_token) if client.auth_type == 'JWT' else None,
                    'timeout': client.timeout,
                },
                'test_result': {
                    'customer_count': len(customers) if isinstance(customers, list) else 0,
                    'sample_customers': customers[:3] if isinstance(customers, list) else [],
                }
            })
        except XivaAPIError as e:
            return Response({
                'status': 'error',
                'message': f'Xiva API connection failed: {str(e)}',
                'config': {
                    'base_url': client.base_url if client.base_url else 'Not configured',
                    'auth_type': client.auth_type,
                    'auth_configured': auth_configured,
                }
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    except Exception as e:
        logger.exception("Error testing Xiva connection")
        return Response({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_customer_from_xiva(request, customer_id):
    """
    Get customer data from Xiva
    
    GET /api/external/xiva/customers/{customer_id}/
    """
    try:
        client = get_xiva_client()
        customer = client.get_customer_details(customer_id)
        return Response(customer)
    except XivaAPIError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.exception(f"Error fetching customer {customer_id} from Xiva")
        return Response({
            'error': f'Unexpected error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_customer_360_services(request, customer_id):
    """
    Get Customer 360 Services from Xiva (Products + Usage)
    
    GET /api/external/xiva/customers/{customer_id}/360/services/
    
    This is the BEST endpoint for Pelatro - combines products and usage in one call!
    """
    try:
        client = get_xiva_client()
        services = client.get_customer_360_services(customer_id)
        return Response(services)
    except XivaAPIError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.exception(f"Error fetching customer 360 services for {customer_id}")
        return Response({
            'error': f'Unexpected error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_customer_360_usage(request, customer_id):
    """
    Get Customer 360 Usage from Xiva
    
    GET /api/external/xiva/customers/{customer_id}/360/usage/
    
    Query Parameters:
    - start_date: YYYY-MM-DD
    - end_date: YYYY-MM-DD
    - usage_type: VOICE_LOCAL, DATA, SMS
    - current_month_only: true/false
    """
    try:
        client = get_xiva_client()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        usage_type = request.query_params.get('usage_type')
        current_month_only = request.query_params.get('current_month_only', '').lower() == 'true'
        
        usage = client.get_customer_360_usage(
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
            usage_type=usage_type,
            current_month_only=current_month_only if current_month_only else None
        )
        return Response(usage)
    except XivaAPIError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.exception(f"Error fetching customer 360 usage for {customer_id}")
        return Response({
            'error': f'Unexpected error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_customer_full_context(request, customer_id):
    """
    Get comprehensive customer context from Xiva
    
    GET /api/external/xiva/customers/{customer_id}/context/
    
    Combines:
    - Customer details
    - Products/services (360 Services)
    - Usage summary
    - Billing accounts
    
    This is the recommended endpoint for loyalty workflows.
    """
    try:
        client = get_xiva_client()
        context = client.get_customer_full_context(customer_id)
        return Response(context)
    except XivaAPIError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.exception(f"Error fetching customer context for {customer_id}")
        return Response({
            'error': f'Unexpected error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_customers_xiva(request):
    """
    Search customers in Xiva
    
    GET /api/external/xiva/customers/?search=john&status=active
    
    Query Parameters:
    - search: Search by name, email, phone
    - status: Filter by status
    - customer_type: Filter by type
    - ordering: Sort field (e.g., -creationDate)
    """
    try:
        client = get_xiva_client()
        
        search = request.query_params.get('search')
        status_filter = request.query_params.get('status')
        customer_type = request.query_params.get('customer_type')
        ordering = request.query_params.get('ordering')
        
        customers = client.get_customer_list(
            search=search,
            status=status_filter,
            customer_type=customer_type,
            ordering=ordering
        )
        return Response({
            'count': len(customers) if isinstance(customers, list) else 0,
            'results': customers
        })
    except XivaAPIError as e:
        logger.error(f"XivaAPIError in search_customers_xiva: {str(e)}")
        return Response({
            'error': str(e),
            'detail': 'Xiva API authentication or connection failed. Check server logs for details.'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.exception("Error searching customers in Xiva")
        return Response({
            'error': f'Unexpected error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_customer_product_instances(request, customer_id):
    """
    Get product instances for customer from Xiva
    
    GET /api/external/xiva/customers/{customer_id}/products/
    """
    try:
        client = get_xiva_client()
        products = client.get_customer_product_instances(customer_id)
        return Response({
            'count': len(products) if isinstance(products, list) else 0,
            'results': products
        })
    except XivaAPIError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.exception(f"Error fetching products for customer {customer_id}")
        return Response({
            'error': f'Unexpected error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_customer_billing_accounts(request, customer_id):
    """
    Get billing accounts for customer from Xiva
    
    GET /api/external/xiva/customers/{customer_id}/billing-accounts/
    """
    try:
        client = get_xiva_client()
        accounts = client.get_billing_accounts(customer=customer_id)
        return Response({
            'count': len(accounts) if isinstance(accounts, list) else 0,
            'results': accounts
        })
    except XivaAPIError as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.exception(f"Error fetching billing accounts for customer {customer_id}")
        return Response({
            'error': f'Unexpected error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

