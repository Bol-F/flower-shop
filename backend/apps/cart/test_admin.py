from decimal import Decimal

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from apps.categories.models import Category
from apps.products.models import Product
from apps.users.models import User

from .admin import CartAdmin, CartItemInline
from .models import Cart, CartItem


@pytest.mark.django_db
def test_cart_admin_totals_use_one_query_for_multiple_carts(django_assert_num_queries):
    category = Category.objects.create(name='Admin bouquets', slug='admin-bouquets')
    rose = Product.objects.create(
        name='Admin rose', description='Rose', price='10.00', category=category, stock=10
    )
    tulip = Product.objects.create(
        name='Admin tulip', description='Tulip', price='5.00', category=category, stock=10
    )
    for index in range(3):
        customer = User.objects.create_user(
            username=f'cart-admin-customer-{index}',
            email=f'cart-admin-customer-{index}@example.com',
            password='safe-password',
        )
        cart = Cart.objects.create(user=customer)
        if index != 2:
            CartItem.objects.create(cart=cart, product=rose, quantity=index + 1)
            CartItem.objects.create(cart=cart, product=tulip, quantity=2)

    request = RequestFactory().get('/admin/cart/cart/')
    cart_admin = CartAdmin(Cart, AdminSite())
    assert cart_admin.has_add_permission(request) is False

    with django_assert_num_queries(1):
        totals = [
            (cart_admin.item_total(cart), cart_admin.price_total(cart))
            for cart in cart_admin.get_queryset(request).order_by('id')
        ]

    assert totals == [
        (3, Decimal('20.00')),
        (4, Decimal('30.00')),
        (0, Decimal('0.00')),
    ]


@pytest.mark.django_db
def test_cart_item_inline_prefetches_product_for_subtotal(django_assert_num_queries):
    customer = User.objects.create_user(
        username='inline-cart-customer',
        email='inline-cart-customer@example.com',
        password='safe-password',
    )
    category = Category.objects.create(name='Inline bouquets', slug='inline-bouquets')
    product = Product.objects.create(
        name='Inline rose', description='Rose', price='12.50', category=category, stock=10
    )
    cart = Cart.objects.create(user=customer)
    CartItem.objects.create(cart=cart, product=product, quantity=2)
    request = RequestFactory().get('/admin/cart/cart/')
    request.user = User.objects.create_superuser(
        username='inline-cart-admin',
        email='inline-cart-admin@example.com',
        password='safe-password',
    )
    inline = CartItemInline(CartItem, AdminSite())

    with django_assert_num_queries(1):
        subtotals = [
            inline.subtotal(item) for item in inline.get_queryset(request).filter(cart=cart)
        ]

    assert subtotals == [Decimal('25.00')]
