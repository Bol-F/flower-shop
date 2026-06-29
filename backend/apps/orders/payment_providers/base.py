from dataclasses import dataclass

from rest_framework.exceptions import ValidationError


@dataclass(frozen=True)
class PaymentResult:
    provider: str
    reference: str
    status: str
    message: str = ''


class ProviderNotConfiguredError(ValidationError):
    pass


class BasePaymentProvider:
    provider_name = ''
    required_settings: tuple[str, ...] = ()

    def is_configured(self) -> bool:
        return True

    def not_configured_message(self) -> str:
        return (
            f'{self.provider_name.title()} payment provider is not configured. '
            'Official provider documentation and credentials are required before '
            'real payments can be enabled.'
        )

    def ensure_configured(self) -> None:
        if not self.is_configured():
            raise ProviderNotConfiguredError(
                {'payment_provider': self.not_configured_message()}
            )

    def create_payment(self, order):
        raise NotImplementedError

    def verify_payment(self, payment_reference: str):
        raise NotImplementedError

    def handle_webhook(self, payload: dict):
        raise NotImplementedError

    def refund_payment(self, order):
        raise NotImplementedError
