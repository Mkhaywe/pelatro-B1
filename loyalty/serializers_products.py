from rest_framework import serializers
from loyalty.models import Product


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        """Validate product data"""
        # Ensure external_product_id and external_system are unique together
        if Product.objects.filter(
            external_product_id=data.get('external_product_id'),
            external_system=data.get('external_system')
        ).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError(
                f"Product with external_product_id '{data.get('external_product_id')}' "
                f"and external_system '{data.get('external_system')}' already exists."
            )
        return data

