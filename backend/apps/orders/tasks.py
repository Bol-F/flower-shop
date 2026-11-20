from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Order, PaymentEvent
from .payments import cancel_unpaid_order


@shared_task
def expire_unpaid_orders() -> int:
    """Release stock held by abandoned online checkouts."""
    cutoff = timezone.now() - timedelta(minutes=settings.PAYMENT_RESERVATION_TTL_MINUTES)
    eligible = Order.objects.filter(
        payment_method__in=(Order.PaymentMethod.CARD, Order.PaymentMethod.ONLINE),
        payment_status__in=(Order.PaymentStatus.PENDING, Order.PaymentStatus.FAILED),
        status__in=(Order.Status.PENDING, Order.Status.CONFIRMED),
        inventory_released_at__isnull=True,
        updated_at__lt=cutoff,
    )
    expired = 0
    for order_id in eligible.values_list('id', flat=True).iterator(chunk_size=200):
        try:
            with transaction.atomic():
                # Callback/checkout activity can refresh the reservation after
                # the candidate query. Recheck every eligibility rule locked.
                order = eligible.select_for_update().filter(pk=order_id).first()
                if order is None:
                    continue
                cancel_unpaid_order(
                    order,
                    source=PaymentEvent.Source.SYSTEM,
                    event_type='payment_reservation_expired',
                    message='Payment reservation expired before confirmation.',
                )
        except (ValidationError, Order.DoesNotExist):
            # A callback may have paid or advanced the order after the candidate
            # query. The locked service re-check is authoritative.
            continue
        expired += 1
    return expired
