from django.utils import timezone
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
    status_timeline = serializers.SerializerMethodField()
    payment_method_display = serializers.CharField(
        source='get_payment_method_display',
        read_only=True,
    )
    delivery_time_slot_display = serializers.CharField(
        source='get_delivery_time_slot_display',
        read_only=True,
    )
    subtotal_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id', 'status', 'status_display', 'status_timeline',
            'subtotal_price', 'total_price',
            'shipping_address', 'phone', 'payment_method',
            'payment_method_display', 'delivery_address',
            'delivery_lat', 'delivery_lng', 'delivery_date',
            'delivery_time_slot', 'delivery_time_slot_display',
            'recipient_name', 'recipient_phone', 'gift_note',
            'call_recipient_before_delivery', 'delivery_fee',
            'notes', 'items',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'status', 'total_price', 'created_at', 'updated_at')

    def get_subtotal_price(self, obj):
        subtotal = obj.total_price - obj.delivery_fee
        return f'{subtotal:.2f}'

    def get_status_timeline(self, obj):
        timeline = [
            (Order.Status.PENDING, str(Order.Status.PENDING.label)),
            (Order.Status.CONFIRMED, str(Order.Status.CONFIRMED.label)),
            (Order.Status.PREPARING, str(Order.Status.PREPARING.label)),
            (Order.Status.COURIER_PICKED_UP, str(Order.Status.COURIER_PICKED_UP.label)),
            (Order.Status.DELIVERED, str(Order.Status.DELIVERED.label)),
        ]
        legacy_statuses = {
            Order.Status.PROCESSING: Order.Status.PREPARING,
            Order.Status.SHIPPED: Order.Status.COURIER_PICKED_UP,
        }
        current_status = legacy_statuses.get(obj.status, obj.status)
        current_index = next(
            (index for index, (status, _) in enumerate(timeline) if status == current_status),
            None,
        )

        return [
            {
                'id': status,
                'label': label,
                'active': status == current_status,
                'completed': current_index is not None and index < current_index,
            }
            for index, (status, label) in enumerate(timeline)
        ]


class CreateOrderSerializer(serializers.Serializer):
    shipping_address = serializers.CharField(max_length=500, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(
        choices=Order.PaymentMethod.choices,
        default=Order.PaymentMethod.CASH,
    )
    delivery_address = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
    )
    delivery_lat = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )
    delivery_lng = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )
    delivery_date = serializers.DateField(required=False)
    delivery_time_slot = serializers.ChoiceField(
        choices=Order.DeliveryTimeSlot.choices,
        required=False,
        default=Order.DeliveryTimeSlot.MIDDAY,
    )
    recipient_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    recipient_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    gift_note = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    call_recipient_before_delivery = serializers.BooleanField(required=False, default=False)
    notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        today = timezone.localdate()
        delivery_address = attrs.get('delivery_address') or attrs.get('shipping_address')
        phone = attrs.get('phone') or attrs.get('recipient_phone')
        delivery_date = attrs.get('delivery_date') or today

        if not delivery_address:
            raise serializers.ValidationError(
                {'delivery_address': 'Delivery address is required.'}
            )
        if not phone:
            raise serializers.ValidationError({'phone': 'Phone is required.'})
        if delivery_date < today:
            raise serializers.ValidationError(
                {'delivery_date': 'Delivery date cannot be in the past.'}
            )

        default_recipient_name = 'Recipient'
        if user and getattr(user, 'is_authenticated', False):
            full_name = user.get_full_name() if hasattr(user, 'get_full_name') else ''
            default_recipient_name = (
                full_name
                or getattr(user, 'username', '')
                or getattr(user, 'email', '')
                or default_recipient_name
            )

        attrs['delivery_address'] = delivery_address
        attrs['shipping_address'] = attrs.get('shipping_address') or delivery_address
        attrs['phone'] = phone
        attrs['delivery_date'] = delivery_date
        attrs['delivery_time_slot'] = (
            attrs.get('delivery_time_slot') or Order.DeliveryTimeSlot.MIDDAY
        )
        attrs['recipient_name'] = attrs.get('recipient_name') or default_recipient_name
        attrs['recipient_phone'] = attrs.get('recipient_phone') or phone
        return attrs


class UpdateOrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('status',)
