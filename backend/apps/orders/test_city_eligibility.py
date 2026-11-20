"""Checkout enforces delivery eligibility and uses current zone configuration."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.cart.models import Cart, CartItem
from apps.marketplace.models import City, Vendor
from apps.products.models import Product
from apps.users.models import User

from .models import DeliveryZone, Order
from .serializers import CreateOrderSerializer
from .services import create_order_from_cart


@pytest.fixture
def checkout_context(db):
    tashkent, _ = City.objects.get_or_create(slug='tashkent', defaults={'name': 'Tashkent'})
    samarkand, _ = City.objects.get_or_create(slug='samarkand', defaults={'name': 'Samarkand'})
    user = User.objects.create_user(username='city-checkout', email='city-checkout@example.test')
    product = Product.objects.create(
        name='Local roses', description='Fresh', price='20.00', stock=3
    )
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, product=product, quantity=1)
    payload = {
        'delivery_address': 'Flower street',
        'phone': '+998901234567',
        'city_slug': 'tashkent',
        'delivery_date': (timezone.localdate() + timedelta(days=1)).isoformat(),
        'delivery_time_slot': Order.DeliveryTimeSlot.MIDDAY,
    }
    return tashkent, samarkand, user, product, cart, payload


@pytest.mark.parametrize('assigned_to', ['product', 'vendor'])
def test_api_rejects_bouquets_assigned_to_another_delivery_city(checkout_context, assigned_to):
    _, samarkand, user, product, cart, payload = checkout_context
    if assigned_to == 'product':
        product.city = samarkand
    else:
        product.vendor = Vendor.objects.create(name='Samarkand florist', city=samarkand)
    product.save()
    client = APIClient()
    client.force_authenticate(user)

    response = client.post(reverse('order-create'), payload, format='json')

    assert response.status_code == 400
    assert 'city_slug' in response.data
    assert not Order.objects.exists()
    assert cart.items.count() == 1
    product.refresh_from_db()
    assert product.stock == 3


@pytest.mark.parametrize('local_assignment', [False, True])
def test_api_accepts_local_and_unassigned_catalog(checkout_context, local_assignment):
    tashkent, _, user, product, _, payload = checkout_context
    if local_assignment:
        product.city = tashkent
        product.vendor = Vendor.objects.create(name='Tashkent florist', city=tashkent)
        product.save()
    client = APIClient()
    client.force_authenticate(user)

    response = client.post(reverse('order-create'), payload, format='json')

    assert response.status_code == 201
    assert Order.objects.get().city == tashkent


@pytest.mark.parametrize('disabled', ['zone', 'city'])
def test_checkout_rejects_zone_disabled_after_serializer_validation(checkout_context, disabled):
    tashkent, _, user, _, _, payload = checkout_context
    zone = DeliveryZone.objects.create(name='Central', city=tashkent, fee='2.00')
    # With no explicit city the previous implementation reused the stale zone
    # and silently selected its city, even after that city had been disabled.
    payload = {**payload, 'city_slug': '', 'delivery_zone_id': zone.pk}
    serializer = CreateOrderSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors
    if disabled == 'zone':
        DeliveryZone.objects.filter(pk=zone.pk).update(is_active=False)
    else:
        City.objects.filter(pk=tashkent.pk).update(is_active=False)

    with pytest.raises(ValidationError):
        create_order_from_cart(user=user, **serializer.validated_data)

    assert not Order.objects.exists()


def test_checkout_uses_current_delivery_zone_fee(checkout_context):
    tashkent, _, user, _, _, payload = checkout_context
    zone = DeliveryZone.objects.create(name='Central', city=tashkent, fee='2.00')
    serializer = CreateOrderSerializer(data={**payload, 'delivery_zone_id': zone.pk})
    assert serializer.is_valid(), serializer.errors
    DeliveryZone.objects.filter(pk=zone.pk).update(fee='9.00', requires_manual_confirmation=True)

    order = create_order_from_cart(user=user, **serializer.validated_data)

    assert order.delivery_fee == Decimal('9.00')
    assert order.total_price == Decimal('29.00')
    assert order.delivery_requires_confirmation
