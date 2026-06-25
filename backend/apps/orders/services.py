from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.cart.services import get_or_create_cart, clear_cart
from apps.products.models import Product
from .models import Order, OrderItem


@transaction.atomic
def create_order_from_cart(user, shipping_address: str, phone: str, notes: str = '') -> Order:
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

    return order
