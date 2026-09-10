import base64
from uuid import UUID
from urllib.parse import urlencode

from django.conf import settings
from django.db.models import Q
from rest_framework.exceptions import ValidationError

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
        reference = str(payment_reference or '').strip()
        lookup = Q(external_payment_id=reference) | Q(provider_reference=reference)
        try:
            lookup |= Q(public_id=UUID(reference))
        except ValueError:
            pass
        payment = PaymentAttempt.objects.filter(lookup, provider=self.provider_name).first()
        if payment is None:
            raise ValidationError({'payment_reference': 'Payme payment was not found.'})
        return PaymentInitialization(
            provider=self.provider_name,
            status=payment.status,
            reference=str(payment.public_id),
            message='Status recorded from authenticated Payme merchant callbacks.',
        )

    def handle_webhook(self, payload: dict):
        self.ensure_configured()
        # HTTP Basic authentication and the production IP allowlist are enforced
        # by PaymeWebhookView before payload dispatch reaches this adapter.
        from apps.orders.payment_webhooks import handle_payme_request

        return handle_payme_request(payload)

    def refund_payment(self, order):
        self.ensure_configured()
        raise NotImplementedError('Payme refunds are not implemented yet.')
