from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.products.models import Product

from .models import Order, PaymentAttempt, PaymentEvent
from .payment_providers import get_payment_provider
from .payment_providers.test_provider import TestPaymentProvider

CASH_PAYMENT_PROVIDER = 'cash'
TEST_PAYMENT_PROVIDER = TestPaymentProvider.provider_name
SUPPORTED_REAL_PROVIDERS = {'payme', 'click'}

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

PAYMENT_TRANSITIONS = {
    PaymentAttempt.Status.CREATED: {
        PaymentAttempt.Status.PENDING,
        PaymentAttempt.Status.PROCESSING,
        PaymentAttempt.Status.PAID,
        PaymentAttempt.Status.FAILED,
        PaymentAttempt.Status.CANCELLED,
    },
    PaymentAttempt.Status.PENDING: {
        PaymentAttempt.Status.PROCESSING,
        PaymentAttempt.Status.PAID,
        PaymentAttempt.Status.FAILED,
        PaymentAttempt.Status.CANCELLED,
    },
    PaymentAttempt.Status.PROCESSING: {
        PaymentAttempt.Status.PAID,
        PaymentAttempt.Status.FAILED,
        PaymentAttempt.Status.CANCELLED,
    },
    PaymentAttempt.Status.PAID: {PaymentAttempt.Status.REFUNDED},
    PaymentAttempt.Status.FAILED: {PaymentAttempt.Status.PENDING},
    PaymentAttempt.Status.CANCELLED: set(),
    PaymentAttempt.Status.REFUNDED: set(),
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
        return CASH_PAYMENT_PROVIDER
    selected = settings.PAYMENT_PROVIDER
    provider = get_payment_provider(selected)
    if selected == TEST_PAYMENT_PROVIDER:
        if not settings.PAYMENT_TEST_MODE_ENABLED:
            raise ValidationError({'payment_provider': 'Test payments are disabled in production.'})
    else:
        provider.ensure_configured()
    return selected


def initial_payment_reference(payment_method: str) -> str:
    validate_payment_method(payment_method)
    return ''


def is_test_payment_method(payment_method: str) -> bool:
    return payment_method in {Order.PaymentMethod.CARD, Order.PaymentMethod.ONLINE}


def calculate_payment_amount(order: Order) -> Decimal:
    rate = Decimal(str(settings.PAYMENT_UZS_PER_PRICE_UNIT))
    return (order.total_price * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def available_payment_methods() -> list[dict]:
    methods = [
        {
            'id': 'cash',
            'payment_method': Order.PaymentMethod.CASH,
            'provider': CASH_PAYMENT_PROVIDER,
            'label': 'Cash on delivery',
            'detail': 'Pay the courier when your flowers arrive',
            'enabled': True,
            'test_mode': False,
        }
    ]
    selected = settings.PAYMENT_PROVIDER
    if selected == TEST_PAYMENT_PROVIDER and settings.PAYMENT_TEST_MODE_ENABLED:
        methods.append(
            {
                'id': 'test',
                'payment_method': Order.PaymentMethod.CARD,
                'provider': TEST_PAYMENT_PROVIDER,
                'label': 'Pay by card',
                'detail': 'Secure test checkout — no money is charged',
                'enabled': True,
                'test_mode': True,
            }
        )
    elif selected in SUPPORTED_REAL_PROVIDERS:
        provider = get_payment_provider(selected)
        methods.append(
            {
                'id': selected,
                'payment_method': Order.PaymentMethod.CARD,
                'provider': selected,
                'label': 'Pay by card',
                'detail': (f'Secure checkout with {"Payme" if selected == "payme" else "Click"}'),
                'enabled': provider.is_configured(),
                'test_mode': False,
            }
        )
    return methods


@transaction.atomic
def initialize_payment(
    order: Order,
    *,
    provider_name: str = '',
    idempotency_key: str = '',
) -> tuple[PaymentAttempt, bool]:
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.payment_method == Order.PaymentMethod.CASH:
        raise ValidationError({'payment_method': 'Cash orders do not use online checkout.'})
    if order.status == Order.Status.CANCELLED:
        raise ValidationError({'order': 'Cancelled orders cannot be paid.'})
    if order.payment_status == Order.PaymentStatus.PAID:
        raise ValidationError({'payment_status': 'This order is already paid.'})

    provider_name = (provider_name or settings.PAYMENT_PROVIDER).strip().lower()
    if provider_name not in SUPPORTED_REAL_PROVIDERS | {TEST_PAYMENT_PROVIDER}:
        raise ValidationError({'provider': 'Unsupported payment provider.'})
    if provider_name != settings.PAYMENT_PROVIDER:
        raise ValidationError({'provider': 'This payment provider is not enabled.'})
    if provider_name == TEST_PAYMENT_PROVIDER and not settings.PAYMENT_TEST_MODE_ENABLED:
        raise ValidationError({'provider': 'Test payments are disabled in production.'})

    idempotency_key = (idempotency_key or f'order-{order.id}-{provider_name}').strip()[:128]
    if not idempotency_key:
        raise ValidationError({'idempotency_key': 'An idempotency key is required.'})
    existing = PaymentAttempt.objects.filter(
        order=order,
        provider=provider_name,
        idempotency_key=idempotency_key,
    ).first()
    if existing:
        return existing, False

    payment = PaymentAttempt.objects.create(
        order=order,
        provider=provider_name,
        amount=calculate_payment_amount(order),
        currency='UZS',
        status=PaymentAttempt.Status.CREATED,
        idempotency_key=idempotency_key,
    )
    provider = get_payment_provider(provider_name)
    result = provider.create_payment(payment)
    payment.status = result.status
    payment.checkout_url = result.checkout_url
    payment.provider_reference = result.reference
    payment.save(
        update_fields=(
            'status',
            'checkout_url',
            'provider_reference',
            'updated_at',
        )
    )
    PaymentEvent.objects.create(
        payment=payment,
        source=PaymentEvent.Source.SYSTEM,
        event_type='payment_initialized',
        status_from=PaymentAttempt.Status.CREATED,
        status_to=payment.status,
        message=result.message,
    )
    order.payment_provider = provider_name
    order.payment_reference = payment.provider_reference or str(payment.public_id)
    order.payment_status = Order.PaymentStatus.PENDING
    order.save(
        update_fields=(
            'payment_provider',
            'payment_reference',
            'payment_status',
            'updated_at',
        )
    )
    return payment, True


def payment_summary(payment: PaymentAttempt) -> dict:
    return {
        'id': str(payment.public_id),
        'order_id': payment.order_id,
        'provider': payment.provider,
        'amount': f'{payment.amount:.2f}',
        'currency': payment.currency,
        'status': payment.status,
        'checkout_url': payment.checkout_url,
        'reference': payment.provider_reference,
        'failure_code': payment.failure_code,
        'failure_message': payment.failure_message,
        'paid_at': payment.paid_at,
        'created_at': payment.created_at,
        'updated_at': payment.updated_at,
    }


def _order_status_for_payment(payment_status: str, current_order_status: str) -> str:
    if payment_status == PaymentAttempt.Status.PAID:
        return Order.PaymentStatus.PAID
    if payment_status == PaymentAttempt.Status.REFUNDED:
        return Order.PaymentStatus.REFUNDED
    if (
        payment_status in {PaymentAttempt.Status.FAILED, PaymentAttempt.Status.CANCELLED}
        and current_order_status != Order.PaymentStatus.PAID
    ):
        return Order.PaymentStatus.FAILED
    return Order.PaymentStatus.PENDING


def transition_payment(
    payment: PaymentAttempt,
    next_status: str,
    *,
    source: str,
    event_type: str,
    external_event_id: str = '',
    message: str = '',
    metadata: dict | None = None,
    actor=None,
    failure_code: str = '',
    failure_message: str = '',
    provider_time: int | None = None,
    cancellation_reason: int | None = None,
) -> PaymentAttempt:
    current = payment.status
    if next_status != current and next_status not in PAYMENT_TRANSITIONS.get(current, set()):
        raise ValidationError(
            {'payment_status': f'Cannot change payment from {current} to {next_status}.'}
        )

    if (
        external_event_id
        and PaymentEvent.objects.filter(
            payment=payment,
            external_event_id=external_event_id,
        ).exists()
    ):
        return payment

    payment.status = next_status
    payment.failure_code = failure_code[:80]
    payment.failure_message = failure_message[:500]
    fields = ['status', 'failure_code', 'failure_message', 'updated_at']
    now = timezone.now()
    if next_status == PaymentAttempt.Status.PAID:
        payment.paid_at = payment.paid_at or now
        payment.provider_perform_time = provider_time or int(now.timestamp() * 1000)
        fields.extend(('paid_at', 'provider_perform_time'))
    if next_status in {PaymentAttempt.Status.CANCELLED, PaymentAttempt.Status.REFUNDED}:
        payment.provider_cancel_time = provider_time or int(now.timestamp() * 1000)
        payment.cancellation_reason = cancellation_reason
        fields.extend(('provider_cancel_time', 'cancellation_reason'))
    payment.save(update_fields=fields)

    order = Order.objects.select_for_update().get(pk=payment.order_id)
    order.payment_provider = payment.provider
    order.payment_reference = (
        payment.external_payment_id or payment.provider_reference or str(payment.public_id)
    )
    order.payment_status = _order_status_for_payment(next_status, order.payment_status)
    order_fields = ['payment_provider', 'payment_reference', 'payment_status', 'updated_at']
    if next_status == PaymentAttempt.Status.PAID and order.paid_at is None:
        order.paid_at = payment.paid_at
        order_fields.append('paid_at')
    order.save(update_fields=order_fields)

    PaymentEvent.objects.create(
        payment=payment,
        source=source,
        event_type=event_type,
        external_event_id=external_event_id,
        status_from=current,
        status_to=next_status,
        message=message[:500],
        metadata=metadata or {},
        actor=actor,
    )
    if source == PaymentEvent.Source.PROVIDER and next_status != current:
        order_id = order.id

        def notify_customer_after_commit():
            from .notifications import notify_payment_status_changed

            notify_payment_status_changed(Order.objects.get(pk=order_id))

        transaction.on_commit(notify_customer_after_commit)
    return payment


def release_inventory_for_cancelled_order(order: Order) -> None:
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.inventory_released_at is not None or order.payment_status == Order.PaymentStatus.PAID:
        return
    items = list(order.items.all())
    product_ids = [item.product_id for item in items if item.product_id]
    products = Product.objects.select_for_update().in_bulk(product_ids)
    for item in items:
        product = products.get(item.product_id)
        if product:
            product.stock += item.quantity
    if products:
        Product.objects.bulk_update(products.values(), ('stock',))
    order.status = Order.Status.CANCELLED
    order.inventory_released_at = timezone.now()
    order.save(update_fields=('status', 'inventory_released_at', 'updated_at'))


@transaction.atomic
def pay_test_order(order: Order) -> Order:
    if settings.PAYMENT_PROVIDER != TEST_PAYMENT_PROVIDER or not settings.PAYMENT_TEST_MODE_ENABLED:
        raise ValidationError({'payment_provider': 'Test payments are not enabled.'})
    payment, _ = initialize_payment(
        order,
        provider_name=TEST_PAYMENT_PROVIDER,
        idempotency_key=f'test-order-{order.id}',
    )
    payment = PaymentAttempt.objects.select_for_update().get(pk=payment.pk)
    if payment.status != PaymentAttempt.Status.PAID:
        transition_payment(
            payment,
            PaymentAttempt.Status.PAID,
            source=PaymentEvent.Source.CUSTOMER,
            event_type='test_payment_completed',
            external_event_id=f'test-paid-{payment.public_id}',
            message='Development test payment completed.',
        )
    return Order.objects.get(pk=order.pk)


@transaction.atomic
def update_payment_status(
    order: Order,
    next_status: str,
    *,
    payment_provider: str = '',
    payment_reference: str = '',
    actor=None,
    reason: str = '',
) -> Order:
    if order.payment_method != Order.PaymentMethod.CASH:
        raise ValidationError(
            {'payment_status': 'Provider-backed payments can only change via verified callbacks.'}
        )
    if not reason.strip():
        raise ValidationError({'reason': 'A reason is required for a manual cash adjustment.'})
    status_map = {
        Order.PaymentStatus.PENDING: PaymentAttempt.Status.PENDING,
        Order.PaymentStatus.PAID: PaymentAttempt.Status.PAID,
        Order.PaymentStatus.FAILED: PaymentAttempt.Status.FAILED,
        Order.PaymentStatus.REFUNDED: PaymentAttempt.Status.REFUNDED,
    }
    if next_status not in status_map:
        raise ValidationError({'payment_status': 'Unsupported manual payment status.'})
    payment, _ = PaymentAttempt.objects.get_or_create(
        order=order,
        provider=CASH_PAYMENT_PROVIDER,
        idempotency_key=f'manual-cash-{order.id}',
        defaults={
            'amount': calculate_payment_amount(order),
            'currency': 'UZS',
            'status': PaymentAttempt.Status.CREATED,
        },
    )
    payment = PaymentAttempt.objects.select_for_update().get(pk=payment.pk)
    transition_payment(
        payment,
        status_map[next_status],
        source=PaymentEvent.Source.ADMIN,
        event_type='manual_cash_adjustment',
        external_event_id=f'admin-{payment.pk}-{payment.events.count() + 1}',
        message=reason,
        metadata={
            'payment_provider': payment_provider[:20],
            'payment_reference': payment_reference[:100],
        },
        actor=actor,
    )
    order = Order.objects.select_for_update().get(pk=order.pk)
    order.payment_provider = (payment_provider or CASH_PAYMENT_PROVIDER)[:20]
    order.payment_reference = payment_reference[:100]
    order.save(update_fields=('payment_provider', 'payment_reference', 'updated_at'))
    return order


def create_provider_payment(order: Order) -> Order:
    """Compatibility shim: checkout creation is now an explicit idempotent API step."""
    return order


def create_test_payment(order: Order) -> dict:
    payment, _ = initialize_payment(
        order,
        provider_name=TEST_PAYMENT_PROVIDER,
        idempotency_key=f'test-order-{order.id}',
    )
    return payment_summary(payment)
