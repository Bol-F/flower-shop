from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Order
from .payment_providers import get_payment_provider
from .payment_providers.base import PaymentResult
from .payment_providers.test_provider import TestPaymentProvider


CASH_PAYMENT_PROVIDER = 'cash'
TEST_PAYMENT_PROVIDER = TestPaymentProvider.provider_name

PAYMENT_METHOD_DEFAULTS = {
    Order.PaymentMethod.CASH: {
        'payment_status': Order.PaymentStatus.UNPAID,
        'payment_provider': CASH_PAYMENT_PROVIDER,
    },
    Order.PaymentMethod.CARD: {
        'payment_status': Order.PaymentStatus.PENDING,
        'payment_provider': TEST_PAYMENT_PROVIDER,
    },
    Order.PaymentMethod.ONLINE: {
        'payment_status': Order.PaymentStatus.PENDING,
        'payment_provider': TEST_PAYMENT_PROVIDER,
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
    if payment_method == Order.PaymentMethod.CASH:
        return PAYMENT_METHOD_DEFAULTS[payment_method]['payment_provider']
    return settings.PAYMENT_PROVIDER


def is_test_payment_method(payment_method: str) -> bool:
    return payment_method in {Order.PaymentMethod.CARD, Order.PaymentMethod.ONLINE}


def generate_test_payment_reference() -> str:
    return TestPaymentProvider.generate_reference()


def initial_payment_reference(payment_method: str) -> str:
    validate_payment_method(payment_method)
    return ''


def calculate_payment_amount(order: Order):
    return order.total_price


def ensure_test_payment_initialized(order: Order) -> Order:
    if not is_test_payment_method(order.payment_method):
        return order

    update_fields = []
    if order.payment_provider != TEST_PAYMENT_PROVIDER:
        order.payment_provider = TEST_PAYMENT_PROVIDER
        update_fields.append('payment_provider')
    if not order.payment_reference:
        order.payment_reference = generate_test_payment_reference()
        update_fields.append('payment_reference')

    if update_fields:
        update_fields.append('updated_at')
        order.save(update_fields=update_fields)

    return order


def _save_payment_result(order: Order, result: PaymentResult) -> Order:
    update_fields = []
    if order.payment_provider != result.provider:
        order.payment_provider = result.provider
        update_fields.append('payment_provider')
    if result.reference and order.payment_reference != result.reference:
        order.payment_reference = result.reference
        update_fields.append('payment_reference')
    if order.payment_status != result.status:
        validate_payment_status_transition(order.payment_status, result.status)
        order.payment_status = result.status
        update_fields.append('payment_status')

    if update_fields:
        update_fields.append('updated_at')
        order.save(update_fields=update_fields)

    return order


def create_provider_payment(order: Order) -> Order:
    if not is_test_payment_method(order.payment_method):
        return order

    try:
        provider = get_payment_provider(order.payment_provider)
        result = provider.create_payment(order)
    except NotImplementedError as exc:
        raise ValidationError({'payment_provider': str(exc)}) from exc

    return _save_payment_result(order, result)


def create_test_payment(order: Order) -> dict:
    ensure_test_payment_initialized(order)
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


def pay_test_order(order: Order) -> Order:
    if not is_test_payment_method(order.payment_method):
        raise ValidationError(
            {'payment_method': 'Cash orders do not use test payments.'}
    )

    if order.payment_status == Order.PaymentStatus.PAID:
        return order

    if order.payment_status != Order.PaymentStatus.PENDING:
        raise ValidationError(
            {'payment_status': 'Only pending test payments can be completed.'}
        )

    if order.payment_provider and order.payment_provider != TEST_PAYMENT_PROVIDER:
        raise ValidationError(
            {'payment_provider': 'Test payment is only available for test provider orders.'}
        )

    ensure_test_payment_initialized(order)
    return update_payment_status(
        order,
        get_payment_provider(TEST_PAYMENT_PROVIDER)
        .verify_payment(order.payment_reference)
        .status,
        payment_provider=TEST_PAYMENT_PROVIDER,
        payment_reference=order.payment_reference,
    )
