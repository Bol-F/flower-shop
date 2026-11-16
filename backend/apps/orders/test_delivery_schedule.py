from datetime import date, datetime, timedelta, timezone as datetime_timezone
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.cart.models import Cart, CartItem
from apps.products.models import Product
from apps.users.models import User
from .delivery_schedule import (
    DELIVERY_TIME_ZONE,
    available_delivery_slots,
    default_delivery_selection,
)
from .models import Order
from .serializers import CreateOrderSerializer


def local_time(hour, minute=0, second=0):
    return datetime(2026, 11, 16, hour, minute, second, tzinfo=DELIVERY_TIME_ZONE)


def serializer_at(now, **overrides):
    payload = {
        'delivery_address': 'Isolated QA address',
        'phone': 'QA-only-phone',
        **overrides,
    }
    with patch('apps.orders.delivery_schedule.timezone.now', return_value=now):
        serializer = CreateOrderSerializer(data=payload)
        serializer.is_valid()
    return serializer


@pytest.mark.parametrize(
    ('slot', 'end_hour'),
    [
        (Order.DeliveryTimeSlot.MORNING, 12),
        (Order.DeliveryTimeSlot.MIDDAY, 15),
        (Order.DeliveryTimeSlot.AFTERNOON, 18),
        (Order.DeliveryTimeSlot.EVENING, 21),
    ],
)
def test_window_is_available_until_its_end_and_rejected_at_the_end(slot, end_hour):
    end = local_time(end_hour)
    before = serializer_at(
        end - timedelta(microseconds=1),
        delivery_date='2026-11-16',
        delivery_time_slot=slot,
    )
    ended = serializer_at(end, delivery_date='2026-11-16', delivery_time_slot=slot)

    assert not before.errors
    assert 'delivery_time_slot' in ended.errors


def test_future_date_accepts_all_existing_windows_after_today_closes():
    now = local_time(23, 59)
    assert available_delivery_slots(date(2026, 11, 17), now=now) == [
        slot for slot, _label in Order.DeliveryTimeSlot.choices
    ]
    for slot, _label in Order.DeliveryTimeSlot.choices:
        assert not serializer_at(
            now,
            delivery_date='2026-11-17',
            delivery_time_slot=slot,
        ).errors


def test_defaults_select_an_open_window_then_tomorrow_when_today_is_closed():
    afternoon = serializer_at(local_time(15))
    closed = serializer_at(local_time(21))

    assert not afternoon.errors
    assert afternoon.validated_data['delivery_date'] == date(2026, 11, 16)
    assert afternoon.validated_data['delivery_time_slot'] == Order.DeliveryTimeSlot.AFTERNOON
    assert not closed.errors
    assert closed.validated_data['delivery_date'] == date(2026, 11, 17)
    assert closed.validated_data['delivery_time_slot'] == Order.DeliveryTimeSlot.MIDDAY


def test_explicit_today_is_not_silently_moved_to_tomorrow():
    serializer = serializer_at(local_time(21), delivery_date='2026-11-16')
    assert 'delivery_time_slot' in serializer.errors


def test_shop_calendar_is_tashkent_even_when_request_timezone_and_utc_date_differ():
    now = datetime(2026, 11, 16, 20, tzinfo=datetime_timezone.utc)
    with timezone.override('America/Los_Angeles'):
        selection = default_delivery_selection(now=now)
        stale = serializer_at(
            now,
            delivery_date='2026-11-16',
            delivery_time_slot=Order.DeliveryTimeSlot.EVENING,
        )
    assert selection == (date(2026, 11, 17), Order.DeliveryTimeSlot.MIDDAY)
    assert 'delivery_date' in stale.errors


@pytest.mark.django_db
def test_expired_checkout_rejects_before_reserving_stock_or_clearing_the_cart():
    user = User.objects.create_user(
        username='schedule-qa', email='schedule-qa@example.test', password='isolated-qa-only'
    )
    product = Product.objects.create(
        name='QA flowers', description='Isolated schedule test', price='10.00', stock=3
    )
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, product=product, quantity=1)
    client = APIClient()
    client.force_authenticate(user)
    with patch('apps.orders.delivery_schedule.timezone.now', return_value=local_time(12)):
        response = client.post(
            '/api/orders/create/',
            {
                'delivery_address': 'Isolated QA address',
                'phone': 'QA-only-phone',
                'delivery_date': '2026-11-16',
                'delivery_time_slot': Order.DeliveryTimeSlot.MORNING,
            },
            format='json',
        )
    assert response.status_code == 400
    assert 'delivery_time_slot' in response.data
    assert not Order.objects.filter(user=user).exists()
    assert cart.items.get(product=product).quantity == 1
    product.refresh_from_db()
    assert product.stock == 3
