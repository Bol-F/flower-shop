"""Real PostgreSQL contention checks; SQLite cannot verify row locks."""

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier, Event

import pytest
from django.db import close_old_connections, connection, transaction
from django.test import override_settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.cart.models import Cart, CartItem
from apps.products.models import Product
from apps.users.models import User

from .models import Order, PaymentAttempt
from .payment_webhooks import handle_payme_request
from .payments import cancel_unpaid_order
from .services import create_order_from_cart

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def postgres_only():
    if connection.vendor != 'postgresql':
        pytest.skip('PostgreSQL row locks required')


def isolated_connection(fn):
    def run(*args):
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET statement_timeout = '10s'")
            return fn(*args)
        finally:
            connection.close()

    return run


def test_concurrent_checkouts_cannot_sell_the_last_bouquet_twice():
    product = Product.objects.create(name='Last rose', description='Fresh', price='20.00', stock=1)
    users = [
        User.objects.create_user(username=f'last-rose-{i}', email=f'last-rose-{i}@example.test')
        for i in range(2)
    ]
    for user in users:
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
    ready = Barrier(2)

    @isolated_connection
    def checkout(user):
        ready.wait(timeout=5)
        try:
            return create_order_from_cart(
                user=user,
                shipping_address='Flower street',
                phone='+998901234567',
                delivery_address='Flower street',
                delivery_date=timezone.localdate() + timedelta(days=1),
                delivery_time_slot=Order.DeliveryTimeSlot.MIDDAY,
                recipient_name='Recipient',
                recipient_phone='+998901234567',
            ).pk
        except ValidationError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(checkout, users))

    assert sum(result is not None for result in results) == 1
    assert Order.objects.count() == 1
    assert CartItem.objects.count() == 1  # The failed customer's cart survives.
    product.refresh_from_db()
    assert product.stock == 0


@override_settings(PAYMENT_PROVIDER='payme')
def test_provider_confirmation_and_order_cancellation_share_lock_order():
    user = User.objects.create_user(username='payment-race', email='payment-race@example.test')
    order = Order.objects.create(
        user=user,
        total_price='20.00',
        shipping_address='Flower street',
        phone='+998901234567',
        payment_method=Order.PaymentMethod.CARD,
        payment_status=Order.PaymentStatus.PENDING,
    )
    payment = PaymentAttempt.objects.create(
        order=order,
        provider='payme',
        amount='253000.00',
        status=PaymentAttempt.Status.PROCESSING,
        external_payment_id='1' * 24,
        provider_create_time=int(time.time() * 1000),
        idempotency_key='payment-race',
    )
    order_locked, callback_started, release_cancellation = Event(), Event(), Event()
    callback_pid = []

    @isolated_connection
    def cancel():
        with transaction.atomic():
            Order.objects.select_for_update().get(pk=order.pk)
            order_locked.set()
            assert release_cancellation.wait(timeout=8)
            with pytest.raises(ValidationError, match='confirmation is in progress'):
                cancel_unpaid_order(order)

    @isolated_connection
    def confirm():
        assert order_locked.wait(timeout=5)
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_backend_pid()')
            callback_pid.append(cursor.fetchone()[0])
        callback_started.set()
        return handle_payme_request(
            {'id': 1, 'method': 'PerformTransaction', 'params': {'id': '1' * 24}}
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        cancel_future = pool.submit(cancel)
        confirm_future = pool.submit(confirm)
        try:
            assert callback_started.wait(timeout=5)
            deadline = time.monotonic() + 5
            blocked = False
            while time.monotonic() < deadline:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT cardinality(pg_blocking_pids(%s))', [callback_pid[0]])
                    blocked = cursor.fetchone()[0] > 0
                if blocked:
                    break
                time.sleep(0.01)
            assert blocked, 'The callback must contend with the cancellation order lock.'
        finally:
            release_cancellation.set()
        cancel_future.result(timeout=10)
        result = confirm_future.result(timeout=10)

    assert 'error' not in result, result
    assert result['result']['state'] == 2
    order.refresh_from_db()
    payment.refresh_from_db()
    assert payment.status == PaymentAttempt.Status.PAID
    assert order.payment_status == Order.PaymentStatus.PAID
    assert order.status == Order.Status.PENDING
    assert order.inventory_released_at is None
