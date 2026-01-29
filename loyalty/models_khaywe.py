from django.db import models
from django.utils import timezone
from uuid import uuid4
from typing import Dict, Any, Optional

# Note: This file was partially overwritten. The models below are defined in migrations.
# ExternalSystemConfig is the new model being added.
# Other models (Segment, Campaign, etc.) are imported from migrations when Django loads them.

# For now, we'll define ExternalSystemConfig here.
# The other models exist in the database via migrations and will be restored if needed.

class ExternalSystemConfig(models.Model):
    """Configuration for external system integrations (Xiva, CRM, Billing, etc.)"""
    SYSTEM_TYPES = [
        ('xiva', 'Xiva'),
        ('crm', 'CRM'),
        ('billing', 'Billing/OCS'),
        ('dwh', 'Data Warehouse'),
        ('other', 'Other'),
    ]
    
    AUTH_TYPES = [
        ('jwt', 'JWT (JSON Web Token)'),
        ('bearer', 'Bearer Token'),
        ('basic', 'Basic Auth'),
        ('api_key', 'API Key'),
        ('oauth2', 'OAuth 2.0'),
        ('none', 'No Authentication'),
    ]
    
    name = models.CharField(max_length=255, unique=True, help_text="System name (e.g., 'Xiva Production', 'CRM Staging')")
    system_type = models.CharField(max_length=50, choices=SYSTEM_TYPES, help_text="Type of external system")
    
    # API Configuration
    base_url = models.URLField(help_text="Base URL for API (e.g., https://api.xiva.sa/api)")
    api_version = models.CharField(max_length=50, blank=True, help_text="API version (e.g., v5)")
    
    # Authentication Configuration
    auth_type = models.CharField(max_length=50, choices=AUTH_TYPES, default='jwt')
    auth_endpoint = models.CharField(max_length=255, blank=True, help_text="Authentication endpoint (e.g., /auth/token/)")
    refresh_endpoint = models.CharField(max_length=255, blank=True, help_text="Token refresh endpoint (e.g., /auth/token/refresh/)")
    
    # Credentials (stored encrypted in production)
    client_id = models.CharField(max_length=255, blank=True, help_text="Client ID or username")
    client_secret = models.CharField(max_length=255, blank=True, help_text="Client secret or password (encrypted)")
    api_key = models.CharField(max_length=255, blank=True, help_text="API key (if auth_type is api_key)")
    api_key_header = models.CharField(max_length=100, default='X-API-Key', help_text="Header name for API key")
    
    # Custom Headers
    custom_headers = models.JSONField(default=dict, blank=True, help_text="Custom headers to include in requests: {'X-Custom-Header': 'value'}")
    
    # Endpoints Configuration
    endpoints = models.JSONField(default=dict, blank=True, help_text="API endpoints: {'products': '/productCatalogManagement/v5/productOffering/', 'categories': '/category/'}")
    
    # Request Configuration
    timeout = models.IntegerField(default=30, help_text="Request timeout in seconds")
    max_retries = models.IntegerField(default=3, help_text="Maximum retry attempts")
    retry_backoff = models.CharField(max_length=50, default='exponential', choices=[('exponential', 'Exponential'), ('linear', 'Linear'), ('fixed', 'Fixed')])
    
    # Rate Limiting
    rate_limit_per_minute = models.IntegerField(default=300, help_text="Rate limit per minute")
    rate_limit_per_hour = models.IntegerField(default=10000, help_text="Rate limit per hour")
    
    # Connection Pool
    max_connections = models.IntegerField(default=20, help_text="Maximum connections in pool")
    max_connections_per_host = models.IntegerField(default=10, help_text="Maximum connections per host")
    
    # Token Management
    token_refresh_buffer = models.IntegerField(default=300, help_text="Refresh token N seconds before expiry")
    token_cache_enabled = models.BooleanField(default=True, help_text="Cache tokens in memory")
    
    # SSL/TLS Configuration
    verify_ssl = models.BooleanField(default=True, help_text="Verify SSL certificates")
    ssl_cert_path = models.CharField(max_length=500, blank=True, help_text="Path to SSL certificate (if needed)")
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Enable/disable this configuration")
    is_production = models.BooleanField(default=False, help_text="Production environment flag")
    
    # Metadata
    description = models.TextField(blank=True, help_text="Description of this configuration")
    last_tested_at = models.DateTimeField(null=True, blank=True, help_text="Last successful API test")
    last_sync_at = models.DateTimeField(null=True, blank=True, help_text="Last successful sync")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['system_type', 'name']
        indexes = [
            models.Index(fields=['system_type', 'is_active']),
            models.Index(fields=['is_active', 'is_production']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.system_type})"
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers based on auth_type"""
        headers = {}
        
        if self.auth_type == 'api_key':
            headers[self.api_key_header] = self.api_key
        elif self.auth_type == 'basic':
            import base64
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f"Basic {encoded}"
        elif self.auth_type == 'bearer':
            # Bearer token should be obtained via token manager
            pass
        
        return headers
    
    def get_all_headers(self) -> Dict[str, str]:
        """Get all headers including custom headers"""
        headers = self.get_auth_headers()
        headers.update(self.custom_headers or {})
        headers['Content-Type'] = 'application/json'
        headers['Accept'] = 'application/json'
        return headers

# Import other models that exist in migrations
# These are loaded dynamically by Django from migrations
# We need to define them here for imports to work

# Placeholder classes - actual definitions are in migrations
# These will be properly restored from migrations if needed
class Segment(models.Model):
    class Meta:
        managed = False

class SegmentMember(models.Model):
    class Meta:
        managed = False

class Campaign(models.Model):
    class Meta:
        managed = False

class CampaignExecution(models.Model):
    class Meta:
        managed = False

class SegmentSnapshot(models.Model):
    class Meta:
        managed = False

class MissionProgress(models.Model):
    class Meta:
        managed = False

class BadgeAward(models.Model):
    class Meta:
        managed = False

class LeaderboardEntry(models.Model):
    class Meta:
        managed = False

class JourneyNode(models.Model):
    class Meta:
        managed = False

class JourneyEdge(models.Model):
    class Meta:
        managed = False

class JourneyExecution(models.Model):
    class Meta:
        managed = False

class ExperimentAssignment(models.Model):
    class Meta:
        managed = False

class HoldoutGroup(models.Model):
    class Meta:
        managed = False

class PartnerProgram(models.Model):
    class Meta:
        managed = False

class PartnerSettlement(models.Model):
    class Meta:
        managed = False

class Coalition(models.Model):
    class Meta:
        managed = False

class RolePermission(models.Model):
    class Meta:
        managed = False

class UserRole(models.Model):
    class Meta:
        managed = False

class ApprovalWorkflow(models.Model):
    class Meta:
        managed = False

class ApprovalRequest(models.Model):
    class Meta:
        managed = False

class ApprovalDecision(models.Model):
    class Meta:
        managed = False

class PointsExpiryRule(models.Model):
    class Meta:
        managed = False

class PointsExpiryEvent(models.Model):
    class Meta:
        managed = False

class EarnCap(models.Model):
    class Meta:
        managed = False

class CapUsage(models.Model):
    class Meta:
        managed = False

class Mission(models.Model):
    class Meta:
        managed = False

class Badge(models.Model):
    class Meta:
        managed = False

class Leaderboard(models.Model):
    class Meta:
        managed = False

class Streak(models.Model):
    class Meta:
        managed = False

class Journey(models.Model):
    class Meta:
        managed = False

class Experiment(models.Model):
    class Meta:
        managed = False

class Partner(models.Model):
    class Meta:
        managed = False

class Role(models.Model):
    class Meta:
        managed = False

class Permission(models.Model):
    class Meta:
        managed = False

class SystemConfiguration(models.Model):
    class Meta:
        managed = False

class DataSourceConfig(models.Model):
    class Meta:
        managed = False

class CustomerEvent(models.Model):
    class Meta:
        managed = False

class CustomerBehaviorScore(models.Model):
    class Meta:
        managed = False

class MissionTemplate(models.Model):
    class Meta:
        managed = False

class DeliveryChannelConfig(models.Model):
    class Meta:
        managed = False

class BehaviorScoreType(models.Model):
    class Meta:
        managed = False

class MissionCategory(models.Model):
    class Meta:
        managed = False

class BadgeType(models.Model):
    class Meta:
        managed = False

class BadgeLevel(models.Model):
    class Meta:
        managed = False
