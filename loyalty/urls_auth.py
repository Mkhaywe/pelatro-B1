"""
Authentication URL patterns
"""
from django.urls import path
from .views_auth import login, logout, me, check_permission

urlpatterns = [
    path('login/', login, name='auth-login'),
    path('logout/', logout, name='auth-logout'),
    path('me/', me, name='auth-me'),
    path('check-permission/', check_permission, name='auth-check-permission'),
]

