from rest_framework import serializers
from loyalty.models_khaywe import ExternalSystemConfig


class ExternalSystemConfigSerializer(serializers.ModelSerializer):
    """Serializer for ExternalSystemConfig"""
    
    # Mask sensitive fields in read operations
    client_secret = serializers.CharField(write_only=True, required=False, allow_blank=True)
    api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = ExternalSystemConfig
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'last_tested_at', 'last_sync_at']
    
    def to_representation(self, instance):
        """Mask sensitive fields in response"""
        data = super().to_representation(instance)
        # Don't expose secrets in API responses
        if 'client_secret' in data:
            data['client_secret'] = '***' if instance.client_secret else ''
        if 'api_key' in data:
            data['api_key'] = '***' if instance.api_key else ''
        return data
    
    def validate(self, data):
        """Validate configuration based on auth_type"""
        auth_type = data.get('auth_type', self.instance.auth_type if self.instance else 'jwt')
        
        if auth_type in ['jwt', 'basic']:
            if not data.get('client_id') and not (self.instance and self.instance.client_id):
                raise serializers.ValidationError(f"client_id is required for {auth_type} authentication")
            if not data.get('client_secret') and not (self.instance and self.instance.client_secret):
                raise serializers.ValidationError(f"client_secret is required for {auth_type} authentication")
        
        if auth_type == 'api_key':
            if not data.get('api_key') and not (self.instance and self.instance.api_key):
                raise serializers.ValidationError("api_key is required for API key authentication")
        
        return data

