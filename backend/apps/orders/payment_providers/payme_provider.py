import base64
from urllib.parse import urlencode

from django.conf import settings

from apps.orders.models import PaymentAttempt

from .base import BasePaymentProvider, PaymentInitialization


class PaymePaymentProvider(BasePaymentProvider):
    provider_name = 'payme'
    required_settings = ('PAYME_MERCHANT_ID', 'PAYME_SECRET_KEY')

    def is_configured(self) -> bool:
        return bool(settings.PAYME_MERCHANT_ID and settings.PAYME_SECRET_KEY)

    def create_payment(self, payment):
        self.ensure_configured()
        return_url = (
            f'{settings.PAYMENT_FRONTEND_RETURN_URL}?'
            + urlencode({'order': payment.order_id, 'payment': payment.public_id})
        )
        params = ';'.join((
            f'm={settings.PAYME_MERCHANT_ID}',
            f'ac.payment_id={payment.public_id}',
            f'a={int(payment.amount * 100)}',
            f'c={return_url}',
            'ct=15000',
        ))
        encoded = base64.b64encode(params.encode('utf-8')).decode('ascii')
        checkout_url = f'{settings.PAYME_CHECKOUT_URL.rstrip("/")}/{encoded}'
        return PaymentInitialization(
            provider=self.provider_name,
            status=PaymentAttempt.Status.PENDING,
            checkout_url=checkout_url,
            reference=str(payment.public_id),
            message='Continue to Payme to authorize payment.',
        )

    def verify_payment(self, payment_reference: str):
        self.ensure_configured()
        raise NotImplementedError('Payme payment verification is not implemented yet.')

    def handle_webhook(self, payload: dict):
        self.ensure_configured()
        raise NotImplementedError('Payme webhook handling is not implemented yet.')

    def refund_payment(self, order):
        self.ensure_configured()
        raise NotImplementedError('Payme refunds are not implemented yet.')
