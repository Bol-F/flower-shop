from uuid import uuid4

from apps.orders.models import Order

from .base import BasePaymentProvider, PaymentResult


class TestPaymentProvider(BasePaymentProvider):
    provider_name = 'test'

    def create_payment(self, order):
        reference = order.payment_reference or self.generate_reference()
        return PaymentResult(
            provider=self.provider_name,
            reference=reference,
            status=Order.PaymentStatus.PENDING,
            message='Test payment created. No real money will be charged.',
        )

    def verify_payment(self, payment_reference: str):
        return PaymentResult(
            provider=self.provider_name,
            reference=payment_reference,
            status=Order.PaymentStatus.PAID,
            message='Test payment verified.',
        )

    def handle_webhook(self, payload: dict):
        reference = str(payload.get('payment_reference') or payload.get('reference') or '')
        status = str(payload.get('payment_status') or Order.PaymentStatus.PAID)
        return PaymentResult(
            provider=self.provider_name,
            reference=reference,
            status=status,
            message='Test webhook handled.',
        )

    def refund_payment(self, order):
        return PaymentResult(
            provider=self.provider_name,
            reference=order.payment_reference,
            status=Order.PaymentStatus.REFUNDED,
            message='Test payment refunded.',
        )

    @staticmethod
    def generate_reference() -> str:
        return f'TEST-{uuid4().hex[:12].upper()}'
