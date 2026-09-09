from uuid import uuid4

from apps.orders.models import PaymentAttempt

from .base import BasePaymentProvider, PaymentInitialization


class TestPaymentProvider(BasePaymentProvider):
    provider_name = 'test'

    def create_payment(self, payment):
        reference = payment.provider_reference or self.generate_reference()
        return PaymentInitialization(
            provider=self.provider_name,
            reference=reference,
            status=PaymentAttempt.Status.PENDING,
            message='Test payment created. No real money will be charged.',
        )

    def verify_payment(self, payment_reference: str):
        return PaymentInitialization(
            provider=self.provider_name,
            reference=payment_reference,
            status=PaymentAttempt.Status.PAID,
            message='Test payment verified.',
        )

    def handle_webhook(self, payload: dict):
        reference = str(payload.get('payment_reference') or payload.get('reference') or '')
        status = str(payload.get('payment_status') or PaymentAttempt.Status.PAID)
        return PaymentInitialization(
            provider=self.provider_name,
            reference=reference,
            status=status,
            message='Test webhook handled.',
        )

    def refund_payment(self, order):
        return PaymentInitialization(
            provider=self.provider_name,
            reference=order.provider_reference,
            status=PaymentAttempt.Status.REFUNDED,
            message='Test payment refunded.',
        )

    @staticmethod
    def generate_reference() -> str:
        return f'TEST-{uuid4().hex[:12].upper()}'
