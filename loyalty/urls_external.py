"""
URL patterns for external system integration (Xiva, DWH, etc.)
"""
from django.urls import path
from .views_external import (
    test_xiva_connection,
    get_customer_from_xiva,
    get_customer_360_services,
    get_customer_360_usage,
    get_customer_full_context,
    search_customers_xiva,
    get_customer_product_instances,
    get_customer_billing_accounts,
)

urlpatterns = [
    # Xiva API Integration
    path('xiva/test/', test_xiva_connection, name='xiva-test'),
    path('xiva/customers/', search_customers_xiva, name='xiva-customers-search'),
    path('xiva/customers/<str:customer_id>/', get_customer_from_xiva, name='xiva-customer-details'),
    path('xiva/customers/<str:customer_id>/360/services/', get_customer_360_services, name='xiva-customer-360-services'),
    path('xiva/customers/<str:customer_id>/360/usage/', get_customer_360_usage, name='xiva-customer-360-usage'),
    path('xiva/customers/<str:customer_id>/context/', get_customer_full_context, name='xiva-customer-context'),
    path('xiva/customers/<str:customer_id>/products/', get_customer_product_instances, name='xiva-customer-products'),
    path('xiva/customers/<str:customer_id>/billing-accounts/', get_customer_billing_accounts, name='xiva-customer-billing-accounts'),
]

