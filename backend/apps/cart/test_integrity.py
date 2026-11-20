"""Every cart writer and checkout obey the same product availability rules."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib import admin
from django.test import RequestFactory
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.marketplace.models import City, Vendor
from apps.orders.models import Order
from apps.orders.services import create_order_from_cart
from apps.products.models import Product
from apps.users.models import User

from .models import Cart, CartItem
from .services import add_item_to_cart, merge_guest_selections, update_cart_item


@pytest.fixture
def selection(db):
    user = User.objects.create_user(username='cart-integrity', email='cart-integrity@example.test')
    product = Product.objects.create(name='Rose', description='Fresh roses', price='20.00', stock=5)
    cart = Cart.objects.create(user=user)
    item = CartItem.objects.create(cart=cart, product=product, quantity=1)
    return user, product, cart, item


def checkout(user):
    return create_order_from_cart(
        user=user,
        shipping_address='Flower street',
        phone='+998901234567',
        delivery_address='Flower street',
        delivery_date=timezone.localdate() + timedelta(days=1),
        delivery_time_slot=Order.DeliveryTimeSlot.MIDDAY,
        recipient_name='Recipient',
        recipient_phone='+998901234567',
    )


@pytest.mark.parametrize('unavailable', ['product', 'city', 'vendor', 'vendor_city'])
def test_unavailable_products_cannot_be_added_updated_merged_or_ordered(selection, unavailable):
    user, product, cart, item = selection
    if unavailable == 'product':
        product.is_available = False
    elif unavailable == 'city':
        product.city = City.objects.create(name='Paused city', is_active=False)
    elif unavailable == 'vendor':
        product.vendor = Vendor.objects.create(name='Paused florist', is_active=False)
    else:
        city = City.objects.create(name='Paused vendor city', is_active=False)
        product.vendor = Vendor.objects.create(name='Florist', city=city)
    product.save()

    with pytest.raises(ValidationError):
        add_item_to_cart(user, product.pk)
    with pytest.raises(ValidationError):
        update_cart_item(user, product.pk, 2)
    result = merge_guest_selections(
        user=user,
        merge_id=uuid4(),
        items=[{'product_slug': product.slug, 'quantity': 2}],
        wishlist=[product.slug],
    )
    assert result['unavailable_products'] == [product.slug]
    item.refresh_from_db()
    assert item.quantity == 1
    assert not user.wishlist_items.exists()
    with pytest.raises(ValidationError):
        checkout(user)
    product.refresh_from_db()
    assert product.stock == 5
    assert not Order.objects.exists()
    assert cart.items.count() == 1


def test_legacy_zero_quantity_cannot_create_an_order(selection):
    user, product, _, item = selection
    item.quantity = 0
    item.save(update_fields=['quantity'])

    with pytest.raises(ValidationError, match='quantity'):
        checkout(user)

    assert not Order.objects.exists()
    product.refresh_from_db()
    assert product.stock == 5


def test_admin_cannot_save_a_zero_quantity(selection):
    user, _, cart, item = selection
    user.is_staff = user.is_superuser = True
    user.save(update_fields=['is_staff', 'is_superuser'])
    request = RequestFactory().get('/admin/cart/cart/')
    request.user = user
    model_admin = admin.site._registry[Cart]
    inline = model_admin.get_inline_instances(request, cart)[0]
    formset_type = inline.get_formset(request, cart)
    form = formset_type.form(
        data={'cart': cart.pk, 'product': item.product_id, 'quantity': 0}, instance=item
    )

    assert not form.is_valid()
    assert 'quantity' in form.errors
