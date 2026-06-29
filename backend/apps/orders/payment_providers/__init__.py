from django.conf import settings
from rest_framework.exceptions import ValidationError

from .click_provider import ClickPaymentProvider
from .payme_provider import PaymePaymentProvider
from .stripe_provider import StripePaymentProvider
from .test_provider import TestPaymentProvider


PROVIDER_REGISTRY = {
    TestPaymentProvider.provider_name: TestPaymentProvider,
    StripePaymentProvider.provider_name: StripePaymentProvider,
    ClickPaymentProvider.provider_name: ClickPaymentProvider,
    PaymePaymentProvider.provider_name: PaymePaymentProvider,
}


def get_payment_provider(provider_name: str = ''):
    selected = (provider_name or settings.PAYMENT_PROVIDER).strip().lower()
    provider_class = PROVIDER_REGISTRY.get(selected)
    if provider_class is None:
        raise ValidationError(
            {
                'payment_provider': (
                    f'Payment provider "{selected}" is not supported. '
                    'Use one of: test, stripe, click, payme.'
                )
            }
        )
    return provider_class()
