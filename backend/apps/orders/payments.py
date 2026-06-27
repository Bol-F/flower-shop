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


def calculate_payment_amount(order: Order):
    return order.total_price


def create_test_payment(order: Order) -> dict:
    return {
        'order_id': order.id,
        'amount': str(calculate_payment_amount(order)),
        'payment_method': order.payment_method,
        'payment_status': order.payment_status,
        'provider': 'manual',
    }


def validate_payment_status_transition(current_status: str, next_status: str) -> None:
    allowed = PAYMENT_STATUS_TRANSITIONS.get(current_status, set())
    if next_status == current_status:
        return
    if next_status not in allowed:
        raise ValidationError(
            f'Cannot change payment status from "{current_status}" to "{next_status}".'
        )


def update_payment_status(order: Order, next_status: str) -> Order:
    validate_payment_status_transition(order.payment_status, next_status)
    order.payment_status = next_status
    order.save(update_fields=['payment_status', 'updated_at'])
    return order
