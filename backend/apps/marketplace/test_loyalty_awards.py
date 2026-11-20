from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

import pytest
from django.db import close_old_connections, connection, connections

from apps.marketplace.services import award_loyalty_points_if_eligible
from apps.orders.models import Order
from apps.users.models import User


@pytest.fixture
def customer(db):
    return User.objects.create_user(username='loyalty-customer', email='loyalty@example.test')


def delivered_order(customer, total='25.00'):
    return Order.objects.create(
        user=customer,
        status=Order.Status.DELIVERED,
        total_price=Decimal(total),
        shipping_address='Tashkent',
        phone='+998901234567',
        payment_method=Order.PaymentMethod.CASH,
        payment_status=Order.PaymentStatus.PAID,
    )


@pytest.mark.django_db
def test_stale_copies_of_the_same_order_cannot_award_twice(customer):
    order = delivered_order(customer)
    first = Order.objects.select_related('user').get(pk=order.pk)
    stale = Order.objects.get(pk=order.pk)

    assert award_loyalty_points_if_eligible(first) is first
    assert first.user.loyalty_points == 25
    assert award_loyalty_points_if_eligible(stale) is stale
    customer.refresh_from_db()
    assert customer.loyalty_points == 25
    assert stale.loyalty_points_earned == 25
    assert stale.user.loyalty_points == 25


@pytest.mark.django_db
def test_orders_with_stale_user_balances_do_not_overwrite_awards(customer):
    first = delivered_order(customer, '25.00')
    second = delivered_order(customer, '40.00')
    first = Order.objects.select_related('user').get(pk=first.pk)
    second = Order.objects.select_related('user').get(pk=second.pk)

    award_loyalty_points_if_eligible(first)
    award_loyalty_points_if_eligible(second)

    customer.refresh_from_db()
    assert customer.loyalty_points == 65


@pytest.mark.django_db
def test_awards_use_persisted_order_eligibility(customer):
    stale = delivered_order(customer)
    Order.objects.filter(pk=stale.pk).update(payment_status=Order.PaymentStatus.REFUNDED)

    award_loyalty_points_if_eligible(stale)

    customer.refresh_from_db()
    stale.refresh_from_db()
    assert customer.loyalty_points == 0
    assert stale.loyalty_points_earned == 0


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('same_order', [True, False])
def test_concurrent_loyalty_awards_use_persisted_marker_and_atomic_balance(same_order):
    if connection.vendor != 'postgresql':
        pytest.skip('Requires PostgreSQL row locks.')
    customer = User.objects.create_user(
        username='concurrent-loyalty', email='concurrent@example.test'
    )
    first = delivered_order(customer)
    second = first if same_order else delivered_order(customer, '40.00')
    barrier = Barrier(2)

    def award(order_id):
        close_old_connections()
        try:
            stale = Order.objects.select_related('user').get(pk=order_id)
            barrier.wait(timeout=10)
            award_loyalty_points_if_eligible(stale)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [pool.submit(award, order.pk) for order in (first, second)]
        for result in results:
            result.result(timeout=20)
    customer.refresh_from_db()
    assert customer.loyalty_points == (25 if same_order else 65)
    first.refresh_from_db()
    assert first.loyalty_points_earned == 25
