from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.cart.services import get_or_create_cart, clear_cart
from .models import Order, OrderItem


@transaction.atomic
def create_order_from_cart(user, shipping_address: str, phone: str, notes: str = '') -> Order:
    cart = get_or_create_cart(user)
    cart_items = cart.items.select_related('product').all()

    if not cart_items.exists():
        raise ValidationError('Your cart is empty.')

    order = Order.objects.create(
        user=user,
        total_price=cart.total_price,
        shipping_address=shipping_address,
        phone=phone,
        notes=notes,
    )

    order_items = [
        OrderItem(
            order=order,
            product=item.product,
            product_name=item.product.name,
            product_price=item.product.price,
            quantity=item.quantity,
        )
        for item in cart_items
    ]
    OrderItem.objects.bulk_create(order_items)

    clear_cart(user)

    return order
