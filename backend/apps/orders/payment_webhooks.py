import base64
import hashlib
import hmac
import time
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Order, PaymentAttempt, PaymentEvent
from .payments import release_inventory_for_cancelled_order, transition_payment


PAYME_TIMEOUT_MS = 43_200_000


class PaymeProtocolError(Exception):
    def __init__(self, code: int, message: str, data: str = ''):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


def payme_error(request_id, code: int, message: str, data: str = '') -> dict:
    return {
        'error': {
            'code': code,
            'message': {'en': message, 'ru': message, 'uz': message},
            'data': data,
        },
        'id': request_id,
    }


def payme_result(request_id, result: dict) -> dict:
    return {'result': result, 'id': request_id}


def payme_authenticated(authorization: str) -> bool:
    if not authorization.startswith('Basic '):
        return False
    try:
        decoded = base64.b64decode(authorization[6:], validate=True).decode('utf-8')
        login, password = decoded.split(':', 1)
    except (ValueError, UnicodeDecodeError):
        return False
    return hmac.compare_digest(login, settings.PAYME_LOGIN) and hmac.compare_digest(
        password,
        settings.PAYME_SECRET_KEY,
    )


def _payment_from_account(params: dict, *, lock: bool = False) -> PaymentAttempt:
    account = params.get('account') or {}
    public_id = account.get('payment_id')
    queryset = PaymentAttempt.objects.select_related('order')
    if lock:
        queryset = queryset.select_for_update()
    try:
        payment = queryset.filter(public_id=public_id, provider='payme').first()
    except (DjangoValidationError, ValueError):
        payment = None
    if payment is None:
        raise PaymeProtocolError(-31050, 'Payment account was not found.', 'payment_id')
    return payment


def _payment_from_transaction(transaction_id: str, *, lock: bool = False) -> PaymentAttempt:
    queryset = PaymentAttempt.objects.select_related('order')
    if lock:
        queryset = queryset.select_for_update()
    payment = queryset.filter(provider='payme', external_payment_id=transaction_id).first()
    if payment is None:
        raise PaymeProtocolError(-31003, 'Transaction was not found.', 'id')
    return payment


def _validate_payme_amount(payment: PaymentAttempt, amount) -> None:
    if payment.currency != 'UZS':
        raise PaymeProtocolError(-31001, 'Incorrect payment currency.', 'amount')
    try:
        received = int(amount)
    except (TypeError, ValueError) as exc:
        raise PaymeProtocolError(-31001, 'Incorrect payment amount.', 'amount') from exc
    if received != int(payment.amount * 100):
        raise PaymeProtocolError(-31001, 'Incorrect payment amount.', 'amount')


def _payme_state(payment: PaymentAttempt) -> int:
    if payment.status == PaymentAttempt.Status.PAID:
        return 2
    if payment.status == PaymentAttempt.Status.REFUNDED:
        return -2
    if payment.status == PaymentAttempt.Status.CANCELLED:
        return -1
    return 1


def _payme_transaction(payment: PaymentAttempt) -> dict:
    return {
        'id': payment.external_payment_id,
        'time': payment.provider_create_time or 0,
        'amount': int(payment.amount * 100),
        'account': {'payment_id': str(payment.public_id)},
        'create_time': payment.provider_create_time or 0,
        'perform_time': payment.provider_perform_time or 0,
        'cancel_time': payment.provider_cancel_time or 0,
        'transaction': str(payment.public_id),
        'state': _payme_state(payment),
        'reason': payment.cancellation_reason,
        'receivers': None,
    }


@transaction.atomic
def handle_payme_request(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return payme_error(None, -32600, 'Invalid JSON-RPC request.')
    request_id = payload.get('id')
    method = payload.get('method')
    params = payload.get('params') or {}
    handlers = {
        'CheckPerformTransaction': _payme_check_perform,
        'CreateTransaction': _payme_create,
        'PerformTransaction': _payme_perform,
        'CancelTransaction': _payme_cancel,
        'CheckTransaction': _payme_check,
        'GetStatement': _payme_statement,
    }
    handler = handlers.get(method)
    if handler is None:
        return payme_error(request_id, -32601, 'Requested method was not found.', 'method')
    try:
        return payme_result(request_id, handler(params))
    except PaymeProtocolError as exc:
        return payme_error(request_id, exc.code, exc.message, exc.data)
    except Exception:
        return payme_error(request_id, -32400, 'A merchant system error occurred.')


def _payme_check_perform(params: dict) -> dict:
    payment = _payment_from_account(params)
    _validate_payme_amount(payment, params.get('amount'))
    if payment.order.status == Order.Status.CANCELLED or payment.status in {
        PaymentAttempt.Status.CANCELLED,
        PaymentAttempt.Status.REFUNDED,
    }:
        raise PaymeProtocolError(-31008, 'Payment cannot be performed.', 'payment_id')
    return {'allow': True}


def _payme_create(params: dict) -> dict:
    transaction_id = str(params.get('id') or '')
    if len(transaction_id) != 24:
        raise PaymeProtocolError(-31003, 'Transaction identifier is invalid.', 'id')
    existing = PaymentAttempt.objects.select_for_update().filter(
        provider='payme', external_payment_id=transaction_id,
    ).first()
    if existing:
        _validate_payme_amount(existing, params.get('amount'))
        return {
            'create_time': existing.provider_create_time or 0,
            'transaction': str(existing.public_id),
            'state': _payme_state(existing),
            'receivers': None,
        }

    payment = _payment_from_account(params, lock=True)
    _validate_payme_amount(payment, params.get('amount'))
    if payment.external_payment_id and payment.external_payment_id != transaction_id:
        raise PaymeProtocolError(-31008, 'Another transaction is already attached.', 'id')
    if payment.status in {
        PaymentAttempt.Status.PAID,
        PaymentAttempt.Status.CANCELLED,
        PaymentAttempt.Status.REFUNDED,
    }:
        raise PaymeProtocolError(-31008, 'Payment cannot be created in its current state.', 'id')
    try:
        provider_time = int(params.get('time'))
    except (TypeError, ValueError) as exc:
        raise PaymeProtocolError(-32600, 'Transaction time is invalid.', 'time') from exc
    payment.external_payment_id = transaction_id
    payment.provider_create_time = provider_time
    payment.save(update_fields=('external_payment_id', 'provider_create_time', 'updated_at'))
    transition_payment(
        payment,
        PaymentAttempt.Status.PROCESSING,
        source=PaymentEvent.Source.PROVIDER,
        event_type='payme_create_transaction',
        external_event_id=f'payme:create:{transaction_id}',
        metadata={'provider_time': provider_time},
    )
    return {
        'create_time': provider_time,
        'transaction': str(payment.public_id),
        'state': 1,
        'receivers': None,
    }


def _payme_perform(params: dict) -> dict:
    transaction_id = str(params.get('id') or '')
    payment = _payment_from_transaction(transaction_id, lock=True)
    if payment.status == PaymentAttempt.Status.PAID:
        return {
            'transaction': str(payment.public_id),
            'perform_time': payment.provider_perform_time or 0,
            'state': 2,
        }
    if payment.status in {PaymentAttempt.Status.CANCELLED, PaymentAttempt.Status.REFUNDED}:
        raise PaymeProtocolError(-31008, 'Transaction cannot be performed.', 'id')
    now_ms = int(time.time() * 1000)
    if payment.provider_create_time and now_ms - payment.provider_create_time >= PAYME_TIMEOUT_MS:
        transition_payment(
            payment,
            PaymentAttempt.Status.CANCELLED,
            source=PaymentEvent.Source.PROVIDER,
            event_type='payme_timeout',
            external_event_id=f'payme:timeout:{transaction_id}',
            cancellation_reason=4,
            provider_time=now_ms,
        )
        release_inventory_for_cancelled_order(payment.order)
        raise PaymeProtocolError(-31008, 'Transaction timed out.', 'id')
    transition_payment(
        payment,
        PaymentAttempt.Status.PAID,
        source=PaymentEvent.Source.PROVIDER,
        event_type='payme_perform_transaction',
        external_event_id=f'payme:perform:{transaction_id}',
        provider_time=now_ms,
    )
    return {'transaction': str(payment.public_id), 'perform_time': now_ms, 'state': 2}


def _payme_cancel(params: dict) -> dict:
    transaction_id = str(params.get('id') or '')
    payment = _payment_from_transaction(transaction_id, lock=True)
    if payment.order.status == Order.Status.DELIVERED:
        raise PaymeProtocolError(-31007, 'A delivered order cannot be cancelled.', 'id')
    if payment.status in {PaymentAttempt.Status.CANCELLED, PaymentAttempt.Status.REFUNDED}:
        return {
            'transaction': str(payment.public_id),
            'cancel_time': payment.provider_cancel_time or 0,
            'state': _payme_state(payment),
        }
    try:
        reason = int(params.get('reason'))
    except (TypeError, ValueError) as exc:
        raise PaymeProtocolError(-32600, 'Cancellation reason is invalid.', 'reason') from exc
    now_ms = int(time.time() * 1000)
    next_status = (
        PaymentAttempt.Status.REFUNDED
        if payment.status == PaymentAttempt.Status.PAID
        else PaymentAttempt.Status.CANCELLED
    )
    transition_payment(
        payment,
        next_status,
        source=PaymentEvent.Source.PROVIDER,
        event_type='payme_cancel_transaction',
        external_event_id=f'payme:cancel:{transaction_id}:{reason}',
        cancellation_reason=reason,
        provider_time=now_ms,
    )
    if next_status == PaymentAttempt.Status.CANCELLED:
        release_inventory_for_cancelled_order(payment.order)
    return {
        'transaction': str(payment.public_id),
        'cancel_time': now_ms,
        'state': _payme_state(payment),
    }


def _payme_check(params: dict) -> dict:
    payment = _payment_from_transaction(str(params.get('id') or ''))
    return {
        'create_time': payment.provider_create_time or 0,
        'perform_time': payment.provider_perform_time or 0,
        'cancel_time': payment.provider_cancel_time or 0,
        'transaction': str(payment.public_id),
        'state': _payme_state(payment),
        'reason': payment.cancellation_reason,
    }


def _payme_statement(params: dict) -> dict:
    try:
        time_from = int(params.get('from'))
        time_to = int(params.get('to'))
    except (TypeError, ValueError) as exc:
        raise PaymeProtocolError(-32600, 'Statement range is invalid.') from exc
    payments = PaymentAttempt.objects.filter(
        provider='payme',
        external_payment_id__gt='',
        provider_create_time__gte=time_from,
        provider_create_time__lte=time_to,
    ).order_by('provider_create_time')
    return {'transactions': [_payme_transaction(payment) for payment in payments]}


CLICK_ERRORS = {
    0: 'Success',
    -1: 'SIGN CHECK FAILED!',
    -2: 'Incorrect amount',
    -3: 'Action not found',
    -4: 'Already paid',
    -5: 'Order does not exist',
    -6: 'Transaction does not exist',
    -7: 'Failed to update order',
    -8: 'Error in request from Click',
    -9: 'Transaction cancelled',
}


def click_response(error: int, **fields) -> dict:
    return {**fields, 'error': error, 'error_note': CLICK_ERRORS[error]}


def click_signature_valid(data: dict) -> bool:
    action = str(data.get('action') or '')
    pieces = [
        str(data.get('click_trans_id') or ''),
        str(data.get('service_id') or ''),
        settings.CLICK_SECRET_KEY,
        str(data.get('merchant_trans_id') or ''),
    ]
    if action == '1':
        pieces.append(str(data.get('merchant_prepare_id') or ''))
    pieces.extend((str(data.get('amount') or ''), action, str(data.get('sign_time') or '')))
    expected = hashlib.md5(''.join(pieces).encode('utf-8')).hexdigest()
    return hmac.compare_digest(expected, str(data.get('sign_string') or '').lower())


def _click_common_checks(data: dict, expected_action: str):
    if not click_signature_valid(data):
        return None, click_response(-1)
    if str(data.get('service_id') or '') != settings.CLICK_SERVICE_ID:
        return None, click_response(-8)
    if str(data.get('action') or '') != expected_action:
        return None, click_response(-3)
    try:
        payment = PaymentAttempt.objects.select_for_update().select_related('order').filter(
            public_id=data.get('merchant_trans_id'),
            provider='click',
        ).first()
    except (DjangoValidationError, ValueError):
        payment = None
    if payment is None:
        return None, click_response(-5)
    if payment.currency != 'UZS':
        return None, click_response(-2)
    try:
        amount = Decimal(str(data.get('amount'))).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError):
        return None, click_response(-2)
    if amount != payment.amount:
        return None, click_response(-2)
    return payment, None


@transaction.atomic
def handle_click_prepare(data: dict) -> dict:
    payment, error = _click_common_checks(data, '0')
    if error:
        return error
    base = {
        'click_trans_id': data.get('click_trans_id'),
        'merchant_trans_id': str(payment.public_id),
        'merchant_prepare_id': payment.id,
    }
    if payment.status == PaymentAttempt.Status.PAID:
        return click_response(-4, **base)
    if payment.status in {PaymentAttempt.Status.CANCELLED, PaymentAttempt.Status.REFUNDED}:
        return click_response(-9, **base)
    try:
        provider_error = int(data.get('error') or 0)
    except (TypeError, ValueError):
        return click_response(-8, **base)
    if provider_error < 0:
        transition_payment(
            payment,
            PaymentAttempt.Status.CANCELLED,
            source=PaymentEvent.Source.PROVIDER,
            event_type='click_prepare_cancelled',
            external_event_id=f'click:prepare-error:{data.get("click_trans_id")}',
            failure_code=str(provider_error),
            failure_message=str(data.get('error_note') or ''),
        )
        release_inventory_for_cancelled_order(payment.order)
        return click_response(-9, **base)
    click_id = str(data.get('click_trans_id') or '')
    if payment.external_payment_id and payment.external_payment_id != click_id:
        return click_response(-4, **base)
    payment.external_payment_id = click_id
    payment.provider_reference = str(data.get('click_paydoc_id') or '')
    payment.provider_create_time = int(time.time() * 1000)
    try:
        payment.save(update_fields=(
            'external_payment_id', 'provider_reference', 'provider_create_time', 'updated_at',
        ))
    except IntegrityError:
        return click_response(-4, **base)
    transition_payment(
        payment,
        PaymentAttempt.Status.PROCESSING,
        source=PaymentEvent.Source.PROVIDER,
        event_type='click_prepare',
        external_event_id=f'click:prepare:{click_id}',
    )
    return click_response(0, **base)


@transaction.atomic
def handle_click_complete(data: dict) -> dict:
    payment, error = _click_common_checks(data, '1')
    if error:
        return error
    base = {
        'click_trans_id': data.get('click_trans_id'),
        'merchant_trans_id': str(payment.public_id),
        'merchant_confirm_id': payment.id,
    }
    if str(data.get('merchant_prepare_id') or '') != str(payment.id):
        return click_response(-6, **base)
    if str(data.get('click_trans_id') or '') != payment.external_payment_id:
        return click_response(-6, **base)
    try:
        provider_error = int(data.get('error') or 0)
    except (TypeError, ValueError):
        return click_response(-8, **base)
    if provider_error < 0:
        if payment.status == PaymentAttempt.Status.PAID:
            return click_response(-4, **base)
        if payment.status not in {PaymentAttempt.Status.CANCELLED, PaymentAttempt.Status.REFUNDED}:
            transition_payment(
                payment,
                PaymentAttempt.Status.CANCELLED,
                source=PaymentEvent.Source.PROVIDER,
                event_type='click_complete_cancelled',
                external_event_id=f'click:complete-error:{payment.external_payment_id}',
                failure_code=str(provider_error),
                failure_message=str(data.get('error_note') or ''),
            )
            release_inventory_for_cancelled_order(payment.order)
        return click_response(-9, **base)
    if payment.status == PaymentAttempt.Status.PAID:
        return click_response(-4, **base)
    if payment.status in {PaymentAttempt.Status.CANCELLED, PaymentAttempt.Status.REFUNDED}:
        return click_response(-9, **base)
    transition_payment(
        payment,
        PaymentAttempt.Status.PAID,
        source=PaymentEvent.Source.PROVIDER,
        event_type='click_complete',
        external_event_id=f'click:complete:{payment.external_payment_id}',
        provider_time=int(time.time() * 1000),
    )
    return click_response(0, **base)
