"""Expiry candidates must still be expired after their order lock is acquired."""

from datetime import timedelta

import pytest
from django.db.models.query import QuerySet
from django.test import override_settings
from django.utils import timezone

from apps.users.models import User

from .models import Order
from .tasks import expire_unpaid_orders


@pytest.mark.django_db
@override_settings(PAYMENT_RESERVATION_TTL_MINUTES=60)
def test_new_checkout_activity_protects_a_stale_expiry_candidate(monkeypatch):
    user = User.objects.create_user(username='expiry-race', email='expiry-race@example.test')
    order = Order.objects.create(
        user=user,
        total_price='20.00',
        shipping_address='Flower street',
        phone='+998901234567',
        payment_method=Order.PaymentMethod.CARD,
        payment_status=Order.PaymentStatus.PENDING,
    )
    Order.objects.filter(pk=order.pk).update(updated_at=timezone.now() - timedelta(hours=2))
    original_first = QuerySet.first
    refreshed = False

    def restart_checkout_before_lock(queryset):
        nonlocal refreshed
        if queryset.model is Order and not refreshed:
            refreshed = True
            Order.objects.filter(pk=order.pk).update(updated_at=timezone.now())
        return original_first(queryset)

    monkeypatch.setattr(QuerySet, 'first', restart_checkout_before_lock)

    assert expire_unpaid_orders() == 0
    order.refresh_from_db()
    assert refreshed
    assert order.status == Order.Status.PENDING
    assert order.inventory_released_at is None
