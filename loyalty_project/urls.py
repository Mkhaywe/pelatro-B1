"""
Main URL configuration for loyalty microservice.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from loyalty.urls import urlpatterns as loyalty_urls
from loyalty.tmf_urls import tmf_urlpatterns
from loyalty.urls_external import urlpatterns as external_urls

@require_http_methods(["GET"])
def root_view(request):
    """Root endpoint showing API information"""
    return JsonResponse({
        'service': 'Khaywe Loyalty Microservice',
        'version': '1.0.0',
        'endpoints': {
            'internal_api': '/api/loyalty/v1/',
            'external_integration': '/api/external/',
            'tmf_api': '/tmf-api/loyaltyManagement/v4/',
            'admin': '/admin/',
        },
        'documentation': {
            'api_base': request.build_absolute_uri('/api/loyalty/v1/'),
            'tmf_base': request.build_absolute_uri('/tmf-api/loyaltyManagement/v4/'),
        }
    })

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('loyalty.urls_auth')),
    path('api/loyalty/v1/', include(loyalty_urls)),
    path('api/external/', include(external_urls)),
    path('tmf-api/loyaltyManagement/v4/', include(tmf_urlpatterns)),
]
