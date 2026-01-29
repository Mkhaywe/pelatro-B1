"""
Authentication views for the loyalty microservice.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from loyalty.models_khaywe import UserRole, Role, Permission, RolePermission


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login endpoint: POST /api/auth/login/
    Body: { "username": "...", "password": "..." }
    Returns: { "token": "...", "user": {...}, "permissions": [...] }
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Authenticate user
    user = authenticate(request=request, username=username, password=password)
    
    if not user:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {'error': 'User account is disabled'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get or create token
    token, created = Token.objects.get_or_create(user=user)
    
    # Get user permissions
    permissions = get_user_permissions(user)
    
    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        },
        'permissions': permissions
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout endpoint: POST /api/auth/logout/
    Deletes the user's token
    """
    try:
        request.user.auth_token.delete()
    except Exception:
        pass  # Token doesn't exist or already deleted
    
    return Response({'message': 'Successfully logged out'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """
    Get current user info: GET /api/auth/me/
    Returns: { "user": {...}, "permissions": [...] }
    """
    user = request.user
    permissions = get_user_permissions(user)
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        },
        'permissions': permissions
    })


def get_user_permissions(user):
    """
    Get all permissions for a user (from roles and direct permissions)
    """
    permissions = set()
    
    # Superusers have all permissions
    if user.is_superuser:
        return ['*']  # Wildcard for all permissions
    
    # Get permissions from roles
    # UserRole.user_id is a CharField, so convert user.id to string
    user_roles = UserRole.objects.filter(user_id=str(user.id), is_active=True).select_related('role')
    for user_role in user_roles:
        role = user_role.role
        if role:
            # Get permissions for this role
            role_permissions = RolePermission.objects.filter(
                role=role,
                is_active=True
            ).select_related('permission')
            
            for rp in role_permissions:
                if rp.permission:
                    permissions.add(rp.permission.codename)
    
    return list(permissions)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_permission(request):
    """
    Check if user has a specific permission: POST /api/auth/check-permission/
    Body: { "permission": "..." }
    Returns: { "has_permission": true/false }
    """
    permission_codename = request.data.get('permission')
    
    if not permission_codename:
        return Response(
            {'error': 'Permission codename is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = request.user
    user_permissions = get_user_permissions(user)
    
    # Check if user has the permission (wildcard means all permissions)
    has_permission = '*' in user_permissions or permission_codename in user_permissions
    
    return Response({
        'has_permission': has_permission,
        'permission': permission_codename
    })

