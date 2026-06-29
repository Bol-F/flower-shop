from django.conf import settings

from .base import BasePaymentProvider


class StripePaymentProvider(BasePaymentProvider):
    provider_name = 'stripe'
    required_settings = ('STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET')

    def is_configured(self) -> bool:
        return bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET)

    def create_payment(self, order):
        self.ensure_configured()
        raise NotImplementedError(
            'Stripe integration requires official Stripe API docs, test mode '
            'credentials, webhook verification, and an approved implementation plan.'
        )

    def verify_payment(self, payment_reference: str):
        self.ensure_configured()
        raise NotImplementedError('Stripe payment verification is not implemented yet.')

    def handle_webhook(self, payload: dict):
        self.ensure_configured()
        raise NotImplementedError('Stripe webhook handling is not implemented yet.')

    def refund_payment(self, order):
        self.ensure_configured()
        raise NotImplementedError('Stripe refunds are not implemented yet.')
