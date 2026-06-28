from rest_framework import serializers

from apps.products.serializers import ProductListSerializer

from .models import City, Courier, PromoCode, Vendor, WishlistItem
from .services import validate_promo_code


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = (
            'id', 'name', 'slug', 'country', 'currency', 'is_active',
            'default_delivery_fee', 'free_delivery_threshold',
        )


class VendorSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)

    class Meta:
        model = Vendor
        fields = (
            'id', 'name', 'slug', 'phone', 'address', 'city',
            'is_active', 'commission_percent', 'created_at',
        )


class CourierSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    city = CitySerializer(read_only=True)

    class Meta:
        model = Courier
        fields = (
            'id', 'user', 'user_email', 'user_username', 'phone', 'city',
            'is_active', 'current_status', 'created_at',
        )


class PromoValidationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=40)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, attrs):
        promo, discount = validate_promo_code(attrs['code'], attrs['subtotal'])
        attrs['promo'] = promo
        attrs['discount'] = discount
        return attrs


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = WishlistItem
        fields = ('id', 'product', 'product_id', 'created_at')

    def create(self, validated_data):
        user = self.context['request'].user
        item, _ = WishlistItem.objects.get_or_create(
            user=user,
            product_id=validated_data['product_id'],
        )
        return item
