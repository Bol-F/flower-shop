"""Retries and late provider events must not replace the successful charge."""

from decimal import Decimal

import pytest
from django.test import override_settings
from rest_framework.exceptions import ValidationError

from apps.users.models import User

from .models import Order, PaymentAttempt, PaymentEvent
from .payments import initialize_payment, transition_payment
from .test_payments import CLICK_SETTINGS


@pytest.fixture
def order(db):
    user = User.objects.create_user(username='reconciliation', email='reconcile@example.test')
    return Order.objects.create(
        user=user,
        total_price=Decimal('10.00'),
        shipping_address='Tashkent',
        phone='+998901234567',
        payment_method=Order.PaymentMethod.CARD,
        payment_status=Order.PaymentStatus.PENDING,
    )


def change(payment, status, event):
    return transition_payment(
        payment,
        status,
        source=PaymentEvent.Source.PROVIDER,
        event_type=event,
        external_event_id=event,
    )


@override_settings(**CLICK_SETTINGS)
def test_late_failure_does_not_undo_successful_retry(order):
    old, _ = initialize_payment(order, provider_name='click', idempotency_key='first')
    change(old, PaymentAttempt.Status.FAILED, 'old-failed')
    latest, _ = initialize_payment(order, provider_name='click', idempotency_key='retry')
    change(latest, PaymentAttempt.Status.PAID, 'retry-paid')
    order.refresh_from_db()
    reference = order.payment_reference
    paid_at = order.paid_at
    change(old, PaymentAttempt.Status.FAILED, 'late-old-failure')

    order.refresh_from_db()
    assert order.payment_status == Order.PaymentStatus.PAID
    assert order.payment_reference == reference
    assert order.paid_at == paid_at


@override_settings(**CLICK_SETTINGS)
def test_stale_attempt_cannot_reverse_a_committed_payment_transition(order):
    payment, _ = initialize_payment(order, provider_name='click', idempotency_key='first')
    stale = PaymentAttempt.objects.get(pk=payment.pk)
    change(payment, PaymentAttempt.Status.PAID, 'paid')

    with pytest.raises(ValidationError, match='Cannot change payment from paid to failed'):
        change(stale, PaymentAttempt.Status.FAILED, 'stale-failure')

    payment.refresh_from_db()
    assert payment.status == PaymentAttempt.Status.PAID


@override_settings(**CLICK_SETTINGS)
def test_late_old_failure_does_not_replace_current_pending_attempt(order):
    old, _ = initialize_payment(order, provider_name='click', idempotency_key='first')
    change(old, PaymentAttempt.Status.FAILED, 'old-failed')
    latest, _ = initialize_payment(order, provider_name='click', idempotency_key='retry')
    order.refresh_from_db()
    reference = order.payment_reference

    change(old, PaymentAttempt.Status.FAILED, 'late-old-failure')

    order.refresh_from_db()
    assert order.payment_status == Order.PaymentStatus.PENDING
    assert order.payment_reference == reference == latest.provider_reference
