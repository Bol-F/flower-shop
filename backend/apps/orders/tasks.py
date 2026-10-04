from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Order, PaymentEvent
from .payments import cancel_unpaid_order


@shared_task
def expire_unpaid_orders() -> int:
    """Release stock held by abandoned online checkouts."""
    cutoff = timezone.now() - timedelta(minutes=settings.PAYMENT_RESERVATION_TTL_MINUTES)
    order_ids = list(
        Order.objects.filter(
            payment_method__in=(Order.PaymentMethod.CARD, Order.PaymentMethod.ONLINE),
            payment_status__in=(Order.PaymentStatus.PENDING, Order.PaymentStatus.FAILED),
            status__in=(Order.Status.PENDING, Order.Status.CONFIRMED),
            inventory_released_at__isnull=True,
            updated_at__lt=cutoff,
        ).values_list('id', flat=True)
    )
    expired = 0
    for order_id in order_ids:
        order = Order.objects.filter(pk=order_id).first()
        if order is None:
            continue
        try:
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
