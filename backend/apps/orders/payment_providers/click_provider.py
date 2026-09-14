from uuid import UUID
from urllib.parse import urlencode

from django.conf import settings
from django.db.models import Q
from rest_framework.exceptions import ValidationError

from apps.orders.models import PaymentAttempt

from .base import BasePaymentProvider, PaymentInitialization


class ClickPaymentProvider(BasePaymentProvider):
    provider_name = 'click'
    required_settings = ('CLICK_SERVICE_ID', 'CLICK_MERCHANT_ID', 'CLICK_SECRET_KEY')

    def is_configured(self) -> bool:
        return bool(
            settings.CLICK_SERVICE_ID and settings.CLICK_MERCHANT_ID and settings.CLICK_SECRET_KEY
        )

    def create_payment(self, payment):
        self.ensure_configured()
        return_url = f'{settings.PAYMENT_FRONTEND_RETURN_URL}?' + urlencode(
            {'order': payment.order_id, 'payment': payment.public_id}
        )
        checkout_url = f'{settings.CLICK_CHECKOUT_URL}?{
            urlencode(
                {
                    "service_id": settings.CLICK_SERVICE_ID,
                    "merchant_id": settings.CLICK_MERCHANT_ID,
                    "amount": f"{payment.amount:.2f}",
                    "transaction_param": str(payment.public_id),
                    "return_url": return_url,
                }
            )
        }'
        return PaymentInitialization(
            provider=self.provider_name,
            status=PaymentAttempt.Status.PENDING,
            checkout_url=checkout_url,
            reference=str(payment.public_id),
            message='Continue to Click to authorize payment.',
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
            raise ValidationError({'payment_reference': 'Click payment was not found.'})
        return PaymentInitialization(
            provider=self.provider_name,
            status=payment.status,
            reference=str(payment.public_id),
            message='Status recorded from authenticated Click merchant callbacks.',
        )

    def handle_webhook(self, payload: dict):
        self.ensure_configured()
        from apps.orders.payment_webhooks import (
            click_response,
            handle_click_complete,
            handle_click_prepare,
        )

        action = str(payload.get('action') or '')
        if action == '0':
            return handle_click_prepare(payload)
        if action == '1':
            return handle_click_complete(payload)
        return click_response(-3)

    def refund_payment(self, order):
        self.ensure_configured()
        raise NotImplementedError('Click refunds are not implemented yet.')
