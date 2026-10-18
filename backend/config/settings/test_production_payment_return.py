"""Payment checkout must return to the deployed frontend's recovery route."""

import pytest

from .test_production_oauth import _import_production_settings


def test_canonical_production_payment_return_is_accepted():
    result = _import_production_settings()
    assert result.returncode == 0, result.stderr


def test_explicit_default_https_port_has_the_same_payment_return_origin():
    result = _import_production_settings(
        PAYMENT_FRONTEND_RETURN_URL='https://shop.example.com:443/payment/return'
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    'return_url',
    [
        'http://shop.example.com/payment/return',
        'https://localhost/payment/return',
        'https://127.0.0.1/payment/return',
        'https://[::1]/payment/return',
        'https://shop.example.com/does-not-exist',
        'https://shop.example.com/payment/return/',
        'https://shop.example.com/payment/return?status=paid',
        'https://shop.example.com/payment/return#paid',
        'https://user:password@shop.example.com/payment/return',
        'https://shop.example.com:invalid/payment/return',
        'https://',
    ],
)
def test_invalid_payment_return_configuration_fails_startup(return_url):
    result = _import_production_settings(PAYMENT_FRONTEND_RETURN_URL=return_url)
    assert result.returncode != 0
    assert 'PAYMENT_FRONTEND_RETURN_URL' in result.stderr


@pytest.mark.parametrize(
    'return_url',
    [
        'https://unrelated.example.com/payment/return',
        'https://shop.example.com:444/payment/return',
        'https://child.shop.example.com/payment/return',
    ],
)
def test_payment_return_must_use_the_actual_frontend_origin(return_url):
    result = _import_production_settings(PAYMENT_FRONTEND_RETURN_URL=return_url)
    assert result.returncode != 0
    assert 'PAYMENT_FRONTEND_RETURN_URL must use the same origin as FRONTEND_URL.' in result.stderr
