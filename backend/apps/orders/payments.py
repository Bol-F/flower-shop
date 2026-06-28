from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Order


PAYMENT_STATUS_TRANSITIONS = {
    Order.PaymentStatus.UNPAID: {
        Order.PaymentStatus.PENDING,
        Order.PaymentStatus.PAID,
        Order.PaymentStatus.FAILED,
    },
    Order.PaymentStatus.PENDING: {
        Order.PaymentStatus.PAID,
        Order.PaymentStatus.FAILED,
    },
    Order.PaymentStatus.PAID: {
        Order.PaymentStatus.REFUNDED,
    },
    Order.PaymentStatus.FAILED: {
        Order.PaymentStatus.PENDING,
    },
    Order.PaymentStatus.REFUNDED: set(),
}


def initial_payment_status(payment_method: str) -> str:
    if payment_method == Order.PaymentMethod.CASH:
        return Order.PaymentStatus.UNPAID
    return Order.PaymentStatus.PENDING


def initial_payment_provider(payment_method: str) -> str:
    if payment_method == Order.PaymentMethod.CASH:
        return 'cash'
    return 'manual'


def calculate_payment_amount(order: Order):
    return order.total_price


def create_test_payment(order: Order) -> dict:
    return {
        'order_id': order.id,
        'amount': str(calculate_payment_amount(order)),
        'payment_method': order.payment_method,
        'payment_status': order.payment_status,
        'provider': order.payment_provider or initial_payment_provider(order.payment_method),
        'reference': order.payment_reference,
    }


def validate_payment_status_transition(current_status: str, next_status: str) -> None:
    allowed = PAYMENT_STATUS_TRANSITIONS.get(current_status, set())
    if next_status == current_status:
        return
    if next_status not in allowed:
        raise ValidationError(
            f'Cannot change payment status from "{current_status}" to "{next_status}".'
        )


def update_payment_status(
    order: Order,
    next_status: str,
    *,
    payment_provider: str = '',
    payment_reference: str = '',
) -> Order:
    validate_payment_status_transition(order.payment_status, next_status)
    order.payment_status = next_status
    update_fields = ['payment_status', 'updated_at']

    if payment_provider:
        order.payment_provider = payment_provider
        update_fields.append('payment_provider')
    elif not order.payment_provider:
        order.payment_provider = initial_payment_provider(order.payment_method)
        update_fields.append('payment_provider')

    if payment_reference:
        order.payment_reference = payment_reference
        update_fields.append('payment_reference')

    if next_status == Order.PaymentStatus.PAID and order.paid_at is None:
        order.paid_at = timezone.now()
        update_fields.append('paid_at')

    order.save(update_fields=update_fields)
    return order
