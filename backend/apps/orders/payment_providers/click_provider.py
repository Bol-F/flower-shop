from django.conf import settings

from .base import BasePaymentProvider


class ClickPaymentProvider(BasePaymentProvider):
    provider_name = 'click'
    required_settings = ('CLICK_SERVICE_ID', 'CLICK_SECRET_KEY')

    def is_configured(self) -> bool:
        return bool(settings.CLICK_SERVICE_ID and settings.CLICK_SECRET_KEY)

    def create_payment(self, order):
        self.ensure_configured()
        raise NotImplementedError(
            'Click integration requires official Click documentation, merchant '
            'credentials, signature verification, and an approved implementation plan.'
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
