from django.conf import settings

from .base import BasePaymentProvider


class PaymePaymentProvider(BasePaymentProvider):
    provider_name = 'payme'
    required_settings = ('PAYME_MERCHANT_ID', 'PAYME_SECRET_KEY')

    def is_configured(self) -> bool:
        return bool(settings.PAYME_MERCHANT_ID and settings.PAYME_SECRET_KEY)

    def create_payment(self, order):
        self.ensure_configured()
        raise NotImplementedError(
            'Payme integration requires official Payme documentation, merchant '
            'credentials, signature verification, and an approved implementation plan.'
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
