import base64
import hashlib
import time
from decimal import Decimal
from urllib.parse import urlencode

import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.products.models import Product
from apps.users.models import User

from .models import Order, OrderItem, PaymentAttempt, PaymentEvent
from .payments import available_payment_methods, initialize_payment, transition_payment
from .payment_webhooks import payme_authenticated


PAYME_SETTINGS = {
    'PAYMENT_PROVIDER': 'payme',
    'PAYME_MERCHANT_ID': 'merchant-id',
    'PAYME_LOGIN': 'Paycom',
    'PAYME_SECRET_KEY': 'payme-secret',
    'PAYME_CHECKOUT_URL': 'https://checkout.paycom.uz',
}

CLICK_SETTINGS = {
    'PAYMENT_PROVIDER': 'click',
    'CLICK_SERVICE_ID': '12345',
    'CLICK_MERCHANT_ID': '67890',
    'CLICK_SECRET_KEY': 'click-secret',
    'CLICK_CHECKOUT_URL': 'https://my.click.uz/services/pay',
}


@pytest.fixture
def payment_user(db):
    return User.objects.create_user(
        username='payer', email='payer@example.com', password='safe-password'
    )


@pytest.fixture
def online_order(payment_user):
    return Order.objects.create(
        user=payment_user,
        total_price=Decimal('10.00'),
        shipping_address='Tashkent',
        phone='+998901234567',
        payment_method=Order.PaymentMethod.ONLINE,
        payment_status=Order.PaymentStatus.PENDING,
        payment_provider='payme',
    )


def _payme_auth():
    encoded = base64.b64encode(b'Paycom:payme-secret').decode('ascii')
    return f'Basic {encoded}'


def _payme_auth_with_secret(secret):
    encoded = base64.b64encode(f'Paycom:{secret}'.encode()).decode('ascii')
    return f'Basic {encoded}'


def _payme_post(client, method, params, request_id=1, auth=None):
    client.credentials(
        HTTP_AUTHORIZATION=auth or _payme_auth(),
        REMOTE_ADDR='185.234.113.1',
    )
    response = client.post(
        reverse('payme-webhook'),
        {'id': request_id, 'method': method, 'params': params},
        format='json',
    )
    client.credentials()
    return response


def _click_sign(data):
    parts = [
        str(data['click_trans_id']),
        str(data['service_id']),
        'click-secret',
        str(data['merchant_trans_id']),
    ]
    if str(data['action']) == '1':
        parts.append(str(data['merchant_prepare_id']))
    parts.extend((str(data['amount']), str(data['action']), str(data['sign_time'])))
    return hashlib.md5(''.join(parts).encode()).hexdigest()


def _click_post(client, name, data):
    return client.post(
        reverse(name),
        urlencode(data),
        content_type='application/x-www-form-urlencoded',
    )


@pytest.mark.django_db
class TestPaymePayments:
    @pytest.fixture(autouse=True)
    def _payme_settings(self):
        with override_settings(**PAYME_SETTINGS):
            yield

    def test_initialization_is_idempotent_and_provider_hosted(self, payment_user, online_order):
        client = APIClient()
        client.force_authenticate(user=payment_user)
        url = reverse('payment-initialize', args=[online_order.id])
        first = client.post(url, {'provider': 'payme', 'idempotency_key': 'cart-1'}, format='json')
        second = client.post(url, {'provider': 'payme', 'idempotency_key': 'cart-1'}, format='json')
        assert first.status_code == 201
        assert second.status_code == 200
        assert first.data['id'] == second.data['id']
        assert first.data['amount'] == '126500.00'
        assert first.data['checkout_url'].startswith('https://checkout.paycom.uz/')
        assert PaymentAttempt.objects.count() == 1

    def test_invalid_and_unauthorized_orders(self, payment_user, online_order):
        stranger = User.objects.create_user(
            username='stranger', email='stranger@example.com', password='safe-password'
        )
        client = APIClient()
        client.force_authenticate(user=stranger)
        assert client.post(
            reverse('payment-initialize', args=[online_order.id]),
            {'provider': 'payme'},
            format='json',
        ).status_code == 404
        assert client.post(
            reverse('payment-initialize', args=[99999]),
            {'provider': 'payme'},
            format='json',
        ).status_code == 404

    def test_verified_webhook_marks_paid_and_duplicate_is_safe(self, payment_user, online_order):
        payment, _ = initialize_payment(online_order, provider_name='payme', idempotency_key='one')
        client = APIClient()
        amount = int(payment.amount * 100)
        account = {'payment_id': str(payment.public_id)}
        assert payme_authenticated(_payme_auth())
        checked = _payme_post(
            client, 'CheckPerformTransaction', {'amount': amount, 'account': account}
        )
        assert 'result' in checked.data, checked.data
        assert checked.data['result']['allow']
        transaction_id = 'a' * 24
        create = _payme_post(
            client,
            'CreateTransaction',
            {'id': transaction_id, 'time': int(time.time() * 1000), 'amount': amount, 'account': account},
        )
        assert create.data['result']['state'] == 1
        paid = _payme_post(client, 'PerformTransaction', {'id': transaction_id})
        duplicate = _payme_post(client, 'PerformTransaction', {'id': transaction_id})
        assert paid.data['result']['state'] == 2
        assert duplicate.data['result']['perform_time'] == paid.data['result']['perform_time']
        online_order.refresh_from_db()
        assert online_order.payment_status == Order.PaymentStatus.PAID
        assert PaymentEvent.objects.filter(payment=payment, event_type='payme_perform_transaction').count() == 1

    def test_invalid_auth_and_wrong_amount_are_rejected(self, online_order):
        payment, _ = initialize_payment(online_order, provider_name='payme', idempotency_key='two')
        client = APIClient()
        account = {'payment_id': str(payment.public_id)}
        bad_auth = _payme_post(
            client, 'CheckPerformTransaction', {'amount': 1, 'account': account}, auth='Basic bad'
        )
        wrong_amount = _payme_post(
            client, 'CheckPerformTransaction', {'amount': 1, 'account': account}
        )
        assert bad_auth.data['error']['code'] == -32504
        assert wrong_amount.data['error']['code'] == -31001

    @override_settings(PAYME_SECRET_KEY='')
    def test_unconfigured_callback_rejects_empty_secret_authentication(self):
        response = _payme_post(
            APIClient(),
            'CheckPerformTransaction',
            {'amount': 100, 'account': {'payment_id': 'not-a-uuid'}},
            auth=_payme_auth_with_secret(''),
        )
        assert response.data['error']['code'] == -32504

    def test_malformed_payment_identifier_is_a_protocol_error(self):
        response = _payme_post(
            APIClient(),
            'CheckPerformTransaction',
            {'amount': 100, 'account': {'payment_id': 'not-a-uuid'}},
        )
        assert response.data['error']['code'] == -31050

    def test_cancellation_restores_reserved_inventory_once(self, online_order):
        product = Product.objects.create(
            name='Reserved roses', description='Roses', price='5.00', stock=8
        )
        OrderItem.objects.create(
            order=online_order,
            product=product,
            product_name=product.name,
            product_price=product.price,
            quantity=2,
        )
        payment, _ = initialize_payment(online_order, provider_name='payme', idempotency_key='cancel')
        transaction_id = 'b' * 24
        params = {
            'id': transaction_id,
            'time': int(time.time() * 1000),
            'amount': int(payment.amount * 100),
            'account': {'payment_id': str(payment.public_id)},
        }
        client = APIClient()
        _payme_post(client, 'CreateTransaction', params)
        first = _payme_post(client, 'CancelTransaction', {'id': transaction_id, 'reason': 3})
        second = _payme_post(client, 'CancelTransaction', {'id': transaction_id, 'reason': 3})
        product.refresh_from_db()
        online_order.refresh_from_db()
        assert first.data['result']['state'] == -1
        assert second.data['result']['state'] == -1
        assert product.stock == 10
        assert online_order.status == Order.Status.CANCELLED


@pytest.mark.django_db
class TestClickPayments:
    @pytest.fixture(autouse=True)
    def _click_settings(self):
        with override_settings(**CLICK_SETTINGS):
            yield

    def test_prepare_complete_signature_amount_and_duplicates(self, online_order):
        payment, _ = initialize_payment(online_order, provider_name='click', idempotency_key='click-one')
        client = APIClient()
        prepare = {
            'click_trans_id': '901',
            'service_id': '12345',
            'click_paydoc_id': '801',
            'merchant_trans_id': str(payment.public_id),
            'amount': f'{payment.amount:.2f}',
            'action': '0',
            'error': '0',
            'error_note': 'Success',
            'sign_time': '2026-09-09 12:00:00',
        }
        prepare['sign_string'] = _click_sign(prepare)
        prepared = _click_post(client, 'click-prepare', prepare)
        assert prepared.data['error'] == 0
        complete = {**prepare, 'action': '1', 'merchant_prepare_id': str(payment.id)}
        complete['sign_string'] = _click_sign(complete)
        completed = _click_post(client, 'click-complete', complete)
        duplicate = _click_post(client, 'click-complete', complete)
        assert completed.data['error'] == 0
        assert duplicate.data['error'] == -4
        online_order.refresh_from_db()
        assert online_order.payment_status == Order.PaymentStatus.PAID

    def test_invalid_signature_and_wrong_amount(self, online_order):
        payment, _ = initialize_payment(online_order, provider_name='click', idempotency_key='click-two')
        data = {
            'click_trans_id': '902',
            'service_id': '12345',
            'click_paydoc_id': '802',
            'merchant_trans_id': str(payment.public_id),
            'amount': '1.00',
            'action': '0',
            'error': '0',
            'error_note': 'Success',
            'sign_time': '2026-09-09 12:00:00',
        }
        data['sign_string'] = 'attacker-signature'
        assert _click_post(APIClient(), 'click-prepare', data).data['error'] == -1
        data['sign_string'] = _click_sign(data)
        assert _click_post(APIClient(), 'click-prepare', data).data['error'] == -2

    def test_signed_malformed_payment_identifier_is_rejected_safely(self):
        data = {
            'click_trans_id': '903',
            'service_id': '12345',
            'click_paydoc_id': '803',
            'merchant_trans_id': 'not-a-uuid',
            'amount': '1000.00',
            'action': '0',
            'error': '0',
            'error_note': 'Success',
            'sign_time': '2026-09-09 12:00:00',
        }
        data['sign_string'] = _click_sign(data)
        assert _click_post(APIClient(), 'click-prepare', data).data['error'] == -5

    @override_settings(CLICK_SECRET_KEY='')
    def test_unconfigured_callback_rejects_empty_secret_signature(self):
        data = {
            'click_trans_id': '904',
            'service_id': '12345',
            'click_paydoc_id': '804',
            'merchant_trans_id': 'not-a-uuid',
            'amount': '1000.00',
            'action': '0',
            'error': '0',
            'error_note': 'Success',
            'sign_time': '2026-09-09 12:00:00',
        }
        signature_parts = [
            data['click_trans_id'],
            data['service_id'],
            '',
            data['merchant_trans_id'],
            data['amount'],
            data['action'],
            data['sign_time'],
        ]
        data['sign_string'] = hashlib.md5(''.join(signature_parts).encode()).hexdigest()
        assert _click_post(APIClient(), 'click-prepare', data).data['error'] == -8


@pytest.mark.django_db
def test_real_provider_status_cannot_be_manually_overridden(payment_user, online_order):
    client = APIClient()
    payment_user.is_staff = True
    payment_user.save(update_fields=('is_staff',))
    client.force_authenticate(user=payment_user)
    response = client.patch(
        reverse('order-payment-status-update', args=[online_order.id]),
        {'payment_status': 'paid', 'reason': 'not allowed'},
        format='json',
    )
    assert response.status_code == 400


@pytest.mark.django_db
@override_settings(PAYMENT_PROVIDER='test', PAYMENT_TEST_MODE_ENABLED=False)
def test_test_provider_never_appears_as_production_capability():
    assert [method['id'] for method in available_payment_methods()] == ['cash']


@pytest.mark.django_db
def test_illegal_payment_transition_is_rejected(online_order):
    payment = PaymentAttempt.objects.create(
        order=online_order,
        provider='payme',
        amount='1000.00',
        status=PaymentAttempt.Status.PAID,
        idempotency_key='transition',
    )
    with pytest.raises(ValidationError):
        transition_payment(
            payment,
            PaymentAttempt.Status.FAILED,
            source=PaymentEvent.Source.SYSTEM,
            event_type='invalid',
        )
