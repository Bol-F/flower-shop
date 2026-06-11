from rest_framework.exceptions import ValidationError

from apps.products.models import Product
from .models import Cart, CartItem


def get_or_create_cart(user) -> Cart:
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def add_item_to_cart(user, product_id: int, quantity: int = 1) -> CartItem:
    product = _get_available_product(product_id)
    cart = get_or_create_cart(user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity},
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    return cart_item


def update_cart_item(user, product_id: int, quantity: int) -> CartItem:
    if quantity <= 0:
        raise ValidationError('Quantity must be greater than 0.')

    cart = get_or_create_cart(user)
    try:
        cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
    except CartItem.DoesNotExist:
        raise ValidationError('Item not found in cart.')

    cart_item.quantity = quantity
    cart_item.save()
    return cart_item


def remove_item_from_cart(user, product_id: int) -> None:
    cart = get_or_create_cart(user)
    CartItem.objects.filter(cart=cart, product_id=product_id).delete()


def clear_cart(user) -> None:
    cart = get_or_create_cart(user)
    cart.items.all().delete()


def _get_available_product(product_id: int) -> Product:
    try:
        product = Product.objects.get(id=product_id, is_available=True)
    except Product.DoesNotExist:
        raise ValidationError('Product not found or unavailable.')

    if product.stock <= 0:
        raise ValidationError(f'"{product.name}" is out of stock.')

    return product
