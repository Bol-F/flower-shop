from rest_framework import serializers

from apps.products.serializers import ProductListSerializer
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'product_id', 'quantity', 'subtotal')


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ('id', 'items', 'total_price', 'total_items', 'updated_at')


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1, min_value=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class GuestCartItemSerializer(serializers.Serializer):
    product_slug = serializers.SlugField(max_length=200)
    quantity = serializers.IntegerField(min_value=1, max_value=999)


class GuestSelectionMergeSerializer(serializers.Serializer):
    merge_id = serializers.UUIDField()
    items = GuestCartItemSerializer(many=True, max_length=100, default=list)
    wishlist = serializers.ListField(
        child=serializers.SlugField(max_length=200),
        max_length=100,
        default=list,
    )
