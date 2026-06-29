from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Order


PAYMENT_METHOD_DEFAULTS = {
    Order.PaymentMethod.CASH: {
        'payment_status': Order.PaymentStatus.UNPAID,
        'payment_provider': 'cash',
    },
    Order.PaymentMethod.CARD: {
        'payment_status': Order.PaymentStatus.PENDING,
        'payment_provider': 'manual',
    },
    Order.PaymentMethod.ONLINE: {
        'payment_status': Order.PaymentStatus.PENDING,
        'payment_provider': 'manual',
    },
}
VALID_PAYMENT_STATUSES = {status for status, _ in Order.PaymentStatus.choices}

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


def validate_payment_method(payment_method: str) -> None:
    if payment_method not in PAYMENT_METHOD_DEFAULTS:
        raise ValidationError({'payment_method': 'Unsupported payment method.'})


def initial_payment_status(payment_method: str) -> str:
    validate_payment_method(payment_method)
    return PAYMENT_METHOD_DEFAULTS[payment_method]['payment_status']


def initial_payment_provider(payment_method: str) -> str:
    validate_payment_method(payment_method)
    return PAYMENT_METHOD_DEFAULTS[payment_method]['payment_provider']


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
    if current_status not in VALID_PAYMENT_STATUSES:
        raise ValidationError({'payment_status': 'Current payment status is not valid.'})
    if next_status not in VALID_PAYMENT_STATUSES:
        raise ValidationError({'payment_status': 'Unsupported payment status.'})

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
