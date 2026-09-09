from urllib.parse import urlencode

from django.conf import settings

from apps.orders.models import PaymentAttempt

from .base import BasePaymentProvider, PaymentInitialization


class ClickPaymentProvider(BasePaymentProvider):
    provider_name = 'click'
    required_settings = ('CLICK_SERVICE_ID', 'CLICK_MERCHANT_ID', 'CLICK_SECRET_KEY')

    def is_configured(self) -> bool:
        return bool(
            settings.CLICK_SERVICE_ID
            and settings.CLICK_MERCHANT_ID
            and settings.CLICK_SECRET_KEY
        )

    def create_payment(self, payment):
        self.ensure_configured()
        return_url = (
            f'{settings.PAYMENT_FRONTEND_RETURN_URL}?'
            + urlencode({'order': payment.order_id, 'payment': payment.public_id})
        )
        checkout_url = f'{settings.CLICK_CHECKOUT_URL}?{urlencode({
            "service_id": settings.CLICK_SERVICE_ID,
            "merchant_id": settings.CLICK_MERCHANT_ID,
            "amount": f"{payment.amount:.2f}",
            "transaction_param": str(payment.public_id),
            "return_url": return_url,
        })}'
        return PaymentInitialization(
            provider=self.provider_name,
            status=PaymentAttempt.Status.PENDING,
            checkout_url=checkout_url,
            reference=str(payment.public_id),
            message='Continue to Click to authorize payment.',
        )

    def verify_payment(self, payment_reference: str):
        self.ensure_configured()
        raise NotImplementedError('Click payment verification is not implemented yet.')

    def handle_webhook(self, payload: dict):
        self.ensure_configured()
        raise NotImplementedError('Click webhook handling is not implemented yet.')

    def refund_payment(self, order):
        self.ensure_configured()
        raise NotImplementedError('Click refunds are not implemented yet.')
