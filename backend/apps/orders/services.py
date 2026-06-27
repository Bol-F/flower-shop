from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.cart.services import get_or_create_cart, clear_cart
from apps.products.models import Product
from . import notifications
from .models import Order, OrderItem
from .payments import initial_payment_status
from .pricing import calculate_delivery_fee


@transaction.atomic
def create_order_from_cart(
    user,
    shipping_address: str,
    phone: str,
    delivery_address: str,
    delivery_date,
    delivery_time_slot: str,
    recipient_name: str,
    recipient_phone: str,
    payment_method: str = Order.PaymentMethod.CASH,
    delivery_zone=None,
    delivery_lat=None,
    delivery_lng=None,
    gift_note: str = '',
    call_recipient_before_delivery: bool = False,
    notes: str = '',
) -> Order:
    cart = get_or_create_cart(user)
    cart_items = list(cart.items.select_related('product').all())

    if not cart_items:
        raise ValidationError('Your cart is empty.')

    product_ids = [item.product_id for item in cart_items]
    products = Product.objects.select_for_update().in_bulk(product_ids)

    for item in cart_items:
        product = products.get(item.product_id)
        if not product or not product.is_available:
            raise ValidationError(f'"{item.product.name}" is no longer available.')
        if item.quantity > product.stock:
            raise ValidationError(
                f'Only {product.stock} item(s) available for "{product.name}".'
            )

    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    delivery_fee = calculate_delivery_fee(subtotal, delivery_zone)
    delivery_requires_confirmation = (
        delivery_zone.requires_manual_confirmation if delivery_zone else False
    )

    order = Order.objects.create(
        user=user,
        total_price=subtotal + delivery_fee,
        shipping_address=shipping_address,
        phone=phone,
        payment_method=payment_method,
        payment_status=initial_payment_status(payment_method),
        delivery_address=delivery_address,
        delivery_lat=delivery_lat,
        delivery_lng=delivery_lng,
        delivery_date=delivery_date,
        delivery_time_slot=delivery_time_slot,
        delivery_zone=delivery_zone,
        delivery_requires_confirmation=delivery_requires_confirmation,
        recipient_name=recipient_name,
        recipient_phone=recipient_phone,
        gift_note=gift_note,
        call_recipient_before_delivery=call_recipient_before_delivery,
        delivery_fee=delivery_fee,
        notes=notes,
    )

    order_items = [
        OrderItem(
            order=order,
            product=products[item.product_id],
            product_name=products[item.product_id].name,
            product_price=products[item.product_id].price,
            quantity=item.quantity,
        )
        for item in cart_items
    ]
    OrderItem.objects.bulk_create(order_items)

    for item in cart_items:
        products[item.product_id].stock -= item.quantity
    Product.objects.bulk_update(list(products.values()), ['stock'])

    clear_cart(user)
    notifications.notify_order_created(order)

    return order
