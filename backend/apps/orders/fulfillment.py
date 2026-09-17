"""Guarded staff operations for order fulfillment.

The Django administration and staff API must share these rules: neither may
silently skip timestamps, customer notifications, or payment restrictions.
"""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.marketplace.models import Courier
from apps.marketplace.services import award_loyalty_points_if_eligible

from . import notifications
from .models import Order

_STAGES = (
    Order.Status.PENDING,
    Order.Status.CONFIRMED,
    Order.Status.PREPARING,
    Order.Status.COURIER_PICKED_UP,
    Order.Status.DELIVERED,
)
_LEGACY_STAGES = {
    Order.Status.PROCESSING: Order.Status.PREPARING,
    Order.Status.SHIPPED: Order.Status.COURIER_PICKED_UP,
}


@transaction.atomic
def change_order_status(order: Order, next_status: str) -> tuple[Order, bool]:
    """Advance an order, allowing a forward skip for manual recovery.

    A no-op is idempotent. Terminal orders cannot be reopened here; cancellation
    and provider refunds belong to their respective payment workflows.
    """
    order = Order.objects.select_for_update().select_related('user').get(pk=order.pk)
    if next_status not in _STAGES[1:]:
        raise ValidationError({'status': 'Choose a supported fulfillment stage.'})
    if order.status == next_status:
        return order, False
    current_status = _LEGACY_STAGES.get(order.status, order.status)
    if current_status not in _STAGES or _STAGES.index(next_status) <= _STAGES.index(current_status):
        raise ValidationError({'status': 'A fulfilled or cancelled order cannot move backwards.'})
    if (
        order.payment_method != Order.PaymentMethod.CASH
        and order.payment_status != Order.PaymentStatus.PAID
        and next_status in _STAGES[2:]
    ):
        raise ValidationError(
            {'status': 'Online/card payment must be verified before fulfillment.'}
        )
    if (
        order.payment_method == Order.PaymentMethod.CASH
        and order.payment_status in (Order.PaymentStatus.FAILED, Order.PaymentStatus.REFUNDED)
        and next_status in _STAGES[2:]
    ):
        raise ValidationError({'status': 'Failed or refunded cash orders cannot be fulfilled.'})

    order.status = next_status
    update_fields = ['status', 'updated_at']
    now = timezone.now()
    if next_status == Order.Status.COURIER_PICKED_UP and order.courier_picked_up_at is None:
        order.courier_picked_up_at = now
        update_fields.append('courier_picked_up_at')
    if next_status == Order.Status.DELIVERED and order.delivered_at is None:
        order.delivered_at = now
        update_fields.append('delivered_at')
    order.save(update_fields=update_fields)
    award_loyalty_points_if_eligible(order)
    notifications.notify_order_status_changed(order)
    return order, True


@transaction.atomic
def assign_order_courier(order: Order, courier: Courier | None) -> tuple[Order, bool]:
    """Assign an available courier while an order is still in dispatch."""
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status in (
        Order.Status.COURIER_PICKED_UP,
        Order.Status.SHIPPED,
        Order.Status.DELIVERED,
        Order.Status.CANCELLED,
    ):
        raise ValidationError({'courier_id': 'This order is no longer available for assignment.'})
    if courier is not None:
        courier = Courier.objects.filter(pk=courier.pk).first()
        if courier is None:
            raise ValidationError({'courier_id': 'Selected courier is no longer available.'})
        if not courier.is_active or courier.current_status == Courier.Status.OFFLINE:
            raise ValidationError({'courier_id': 'Choose an active, on-duty courier.'})
        if order.city_id and courier.city_id and order.city_id != courier.city_id:
            raise ValidationError({'courier_id': 'Courier and order must belong to the same city.'})
    courier_id = courier.pk if courier else None
    if order.assigned_courier_id == courier_id:
        return order, False
    order.assigned_courier = courier
    order.courier_assigned_at = timezone.now() if courier else None
    order.save(update_fields=['assigned_courier', 'courier_assigned_at', 'updated_at'])
    return order, True
