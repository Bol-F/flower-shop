from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'product_price', 'quantity', 'subtotal')


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'status', 'status_display', 'total_price',
            'shipping_address', 'phone', 'notes', 'items',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'status', 'total_price', 'created_at', 'updated_at')


class CreateOrderSerializer(serializers.Serializer):
    shipping_address = serializers.CharField(max_length=500)
    phone = serializers.CharField(max_length=20)
    notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)


class UpdateOrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('status',)
