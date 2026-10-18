import hashlib
import json

from django.db import transaction
from django.db.models import Prefetch
from rest_framework.exceptions import ValidationError

from apps.marketplace.models import WishlistItem
from apps.products.models import Product
from .models import Cart, CartItem, GuestSelectionMerge


def get_or_create_cart(user) -> Cart:
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def get_cart_for_update(user) -> Cart:
    """Call inside atomic(); all cart writers acquire this lock first."""
    get_or_create_cart(user)
    return Cart.objects.select_for_update().get(user=user)


def get_cart_for_response(user) -> Cart:
    get_or_create_cart(user)
    return Cart.objects.prefetch_related(
        Prefetch(
            'items',
            queryset=CartItem.objects.select_related(
                'product__category', 'product__city', 'product__vendor'
            ),
        )
    ).get(user=user)


@transaction.atomic
def add_item_to_cart(user, product_id: int, quantity: int = 1) -> CartItem:
    cart = get_cart_for_update(user)
    product = _get_available_product(product_id)
    _ensure_stock(product, quantity)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity},
    )

    if not created:
        next_quantity = cart_item.quantity + quantity
        _ensure_stock(product, next_quantity)
        cart_item.quantity = next_quantity
        cart_item.save()

    return cart_item


@transaction.atomic
def update_cart_item(user, product_id: int, quantity: int) -> CartItem:
    if quantity <= 0:
        raise ValidationError('Quantity must be greater than 0.')

    cart = get_cart_for_update(user)
    try:
        cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
    except CartItem.DoesNotExist:
        raise ValidationError('Item not found in cart.')

    _ensure_stock(cart_item.product, quantity)
    cart_item.quantity = quantity
    cart_item.save()
    return cart_item


@transaction.atomic
def remove_item_from_cart(user, product_id: int) -> None:
    cart = get_cart_for_update(user)
    CartItem.objects.filter(cart=cart, product_id=product_id).delete()


@transaction.atomic
def clear_cart(user) -> None:
    cart = get_cart_for_update(user)
    cart.items.all().delete()


@transaction.atomic
def merge_guest_selections(*, user, merge_id, items, wishlist):
    cart = get_cart_for_update(user)
    quantities = {}
    for item in items:
        slug = item['product_slug']
        quantities[slug] = quantities.get(slug, 0) + item['quantity']
    wishes = set(wishlist)
    canonical = json.dumps(
        {'items': sorted(quantities.items()), 'wishlist': sorted(wishes)},
        separators=(',', ':'),
    )
    fingerprint = hashlib.sha256(canonical.encode()).hexdigest()
    receipt = GuestSelectionMerge.objects.filter(user=user, merge_id=merge_id).first()
    if receipt:
        if receipt.payload_hash != fingerprint:
            raise ValidationError(
                {'merge_id': 'This merge ID was already used for different selections.'}
            )
        return receipt.adjustments

    products = {p.slug: p for p in Product.objects.filter(slug__in=set(quantities) | wishes)}
    current = {item.product_id: item for item in cart.items.all()}
    adjusted, unavailable = [], []
    for slug, quantity in quantities.items():
        product = products.get(slug)
        if not product or not product.is_available or product.stock <= 0 or product.price <= 0:
            unavailable.append(slug)
            continue
        existing = current.get(product.pk)
        wanted = (existing.quantity if existing else 0) + quantity
        final_quantity = min(wanted, product.stock)
        if final_quantity != wanted:
            adjusted.append(slug)
        if existing:
            existing.quantity = final_quantity
            existing.save(update_fields=['quantity'])
        else:
            CartItem.objects.create(cart=cart, product=product, quantity=final_quantity)
    for slug in wishes:
        product = products.get(slug)
        if product and product.is_available:
            WishlistItem.objects.get_or_create(user=user, product=product)
        elif slug not in unavailable:
            unavailable.append(slug)
    result = {'adjusted_products': sorted(adjusted), 'unavailable_products': sorted(unavailable)}
    GuestSelectionMerge.objects.create(
        user=user,
        merge_id=merge_id,
        payload_hash=fingerprint,
        adjustments=result,
    )
    cart.save(update_fields=['updated_at'])
    return result


def _get_available_product(product_id: int) -> Product:
    try:
        product = Product.objects.get(id=product_id, is_available=True)
    except Product.DoesNotExist:
        raise ValidationError('Product not found or unavailable.')

    if product.stock <= 0:
        raise ValidationError(f'"{product.name}" is out of stock.')

    return product


def _ensure_stock(product: Product, quantity: int) -> None:
    if quantity > product.stock:
        raise ValidationError(f'Only {product.stock} item(s) available for "{product.name}".')
