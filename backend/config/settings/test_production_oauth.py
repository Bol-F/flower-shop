import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]

VALID_PRODUCTION_ENV = {
    'DJANGO_SETTINGS_MODULE': 'config.settings.production',
    'SECRET_KEY': 'production-settings-test-key',
    'DEBUG': 'False',
    'ALLOWED_HOSTS': 'api.example.com',
    'CORS_ALLOWED_ORIGINS': 'https://shop.example.com',
    'CSRF_TRUSTED_ORIGINS': 'https://api.example.com',
    'RENDER_EXTERNAL_HOSTNAME': '',
    'DATABASE_URL': '',
    'PAYMENT_PROVIDER': 'payme',
    'PAYMENT_TEST_MODE_ENABLED': 'false',
    'PAYMENT_FRONTEND_RETURN_URL': 'https://shop.example.com/payment/return',
    'PAYME_MERCHANT_ID': 'merchant',
    'PAYME_LOGIN': 'Paycom',
    'PAYME_SECRET_KEY': 'payment-secret',
    'PAYME_CHECKOUT_URL': 'https://checkout.paycom.uz',
    'FRONTEND_URL': 'https://shop.example.com',
    'OAUTH_FRONTEND_CALLBACK_URL': 'https://shop.example.com/auth/callback',
    'OAUTH_ATTEMPT_TTL_SECONDS': '600',
    'OAUTH_EXCHANGE_TTL_SECONDS': '60',
    'OAUTH_HTTP_TIMEOUT_SECONDS': '10',
    'GOOGLE_OAUTH_CLIENT_ID': 'google-client',
    'GOOGLE_OAUTH_CLIENT_SECRET': 'google-secret',
    'GOOGLE_OAUTH_REDIRECT_URI': ('https://api.example.com/api/auth/oauth/google/callback/'),
    'GITHUB_OAUTH_CLIENT_ID': 'github-client',
    'GITHUB_OAUTH_CLIENT_SECRET': 'github-secret',
    'GITHUB_OAUTH_REDIRECT_URI': ('https://api.example.com/api/auth/oauth/github/callback/'),
    'MICROSOFT_OAUTH_CLIENT_ID': 'microsoft-client',
    'MICROSOFT_OAUTH_CLIENT_SECRET': 'microsoft-secret',
    'MICROSOFT_OAUTH_REDIRECT_URI': ('https://api.example.com/api/auth/oauth/microsoft/callback/'),
    'MICROSOFT_OAUTH_TENANT': 'common',
}


def _import_production_settings(**overrides: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.update(VALID_PRODUCTION_ENV)
    environment.update(overrides)
    return subprocess.run(
        [sys.executable, '-c', 'import config.settings.production'],
        cwd=BACKEND_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_valid_production_oauth_configuration_imports():
    result = _import_production_settings()
    assert result.returncode == 0, result.stderr


def test_valid_canonical_guid_microsoft_tenant_imports():
    result = _import_production_settings(
        MICROSOFT_OAUTH_TENANT='11111111-2222-3333-4444-555555555555'
    )
    assert result.returncode == 0, result.stderr


def test_subdomain_callback_matches_dot_prefixed_allowed_host():
    result = _import_production_settings(ALLOWED_HOSTS='.example.com')
    assert result.returncode == 0, result.stderr


def test_valid_multiple_production_origins_import():
    result = _import_production_settings(
        CORS_ALLOWED_ORIGINS='https://shop.example.com,https://assets.example.com',
        CSRF_TRUSTED_ORIGINS='https://api.example.com,https://admin.example.com',
    )
    assert result.returncode == 0, result.stderr


def test_unconfigured_providers_do_not_require_production_redirects():
    result = _import_production_settings(
        GOOGLE_OAUTH_CLIENT_ID='',
        GOOGLE_OAUTH_CLIENT_SECRET='',
        GOOGLE_OAUTH_REDIRECT_URI='http://localhost:8000/api/auth/oauth/google/callback/',
        GITHUB_OAUTH_CLIENT_ID='',
        GITHUB_OAUTH_CLIENT_SECRET='',
        GITHUB_OAUTH_REDIRECT_URI='http://localhost:8000/api/auth/oauth/github/callback/',
        MICROSOFT_OAUTH_CLIENT_ID='',
        MICROSOFT_OAUTH_CLIENT_SECRET='',
        MICROSOFT_OAUTH_REDIRECT_URI=('http://localhost:8000/api/auth/oauth/microsoft/callback/'),
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ('overrides', 'expected_error'),
    (
        ({'FRONTEND_URL': 'https://localhost'}, 'must not use a localhost address'),
        (
            {'FRONTEND_URL': 'https://shop.example.com/store'},
            'must contain only the frontend origin',
        ),
        (
            {'CORS_ALLOWED_ORIGINS': 'https://other.example.com'},
            'must include the exact FRONTEND_URL origin',
        ),
        (
            {'CORS_ALLOWED_ORIGINS': 'https://shop.example.com:443'},
            'must include the exact FRONTEND_URL origin',
        ),
        (
            {'CORS_ALLOWED_ORIGINS': 'https://shop.example.com/'},
            'must contain only an HTTPS origin without a trailing slash',
        ),
        (
            {'CORS_ALLOWED_ORIGINS': ('https://shop.example.com,https://assets.example.com?')},
            'must contain only an HTTPS origin without a trailing slash',
        ),
        (
            {'CORS_ALLOWED_ORIGINS': ('https://shop.example.com,ftp://assets.example.com')},
            'CORS_ALLOWED_ORIGINS entry must be a valid HTTPS URL',
        ),
        (
            {'CORS_ALLOWED_ORIGINS': ('https://shop.example.com,https://localhost:3000')},
            'CORS_ALLOWED_ORIGINS entry must not use a localhost address',
        ),
        (
            {'CSRF_TRUSTED_ORIGINS': 'http://api.example.com'},
            'CSRF_TRUSTED_ORIGINS entry must be a valid HTTPS URL',
        ),
        (
            {'CSRF_TRUSTED_ORIGINS': 'https://api.example.com/admin'},
            'must contain only an HTTPS origin without a trailing slash',
        ),
        (
            {'CSRF_TRUSTED_ORIGINS': 'https://api.example.com#'},
            'must contain only an HTTPS origin without a trailing slash',
        ),
        (
            {'CSRF_TRUSTED_ORIGINS': 'https://127.0.0.1'},
            'CSRF_TRUSTED_ORIGINS entry must not use a localhost address',
        ),
        (
            {'OAUTH_FRONTEND_CALLBACK_URL': 'http://shop.example.com/auth/callback'},
            'must be a valid HTTPS URL',
        ),
        (
            {'OAUTH_FRONTEND_CALLBACK_URL': 'https://other.example.com/auth/callback'},
            'must use the same origin as FRONTEND_URL',
        ),
        (
            {'OAUTH_FRONTEND_CALLBACK_URL': 'https://shop.example.com/auth/callback/'},
            'must use the exact path /auth/callback',
        ),
        (
            {
                'OAUTH_FRONTEND_CALLBACK_URL': (
                    'https://shop.example.com/auth/callback?code=unexpected'
                )
            },
            'must not contain a query or fragment',
        ),
        (
            {'GOOGLE_OAUTH_CLIENT_SECRET': ''},
            'Google OAuth credentials are incomplete',
        ),
        (
            {
                'GOOGLE_OAUTH_REDIRECT_URI': (
                    'https://api.example.com/api/auth/oauth/github/callback/'
                )
            },
            'must use the exact path /api/auth/oauth/google/callback/',
        ),
        (
            {
                'GITHUB_OAUTH_REDIRECT_URI': (
                    'https://api.example.com/api/auth/oauth/github/callback/#fragment'
                )
            },
            'must not contain a query or fragment',
        ),
        (
            {
                'GITHUB_OAUTH_REDIRECT_URI': (
                    'https://user@api.example.com/api/auth/oauth/github/callback/'
                )
            },
            'must not contain user information',
        ),
        (
            {
                'MICROSOFT_OAUTH_REDIRECT_URI': (
                    'https://accounts.example.net/api/auth/oauth/microsoft/callback/'
                )
            },
            'hostname must be present in ALLOWED_HOSTS',
        ),
        (
            {'MICROSOFT_OAUTH_TENANT': 'example.onmicrosoft.com'},
            'must be common, organizations, consumers, or a UUID',
        ),
        (
            {'OAUTH_EXCHANGE_TTL_SECONDS': '0'},
            'OAUTH_EXCHANGE_TTL_SECONDS must be greater than zero',
        ),
    ),
)
def test_invalid_production_oauth_configuration_fails(overrides, expected_error):
    result = _import_production_settings(**overrides)
    assert result.returncode != 0
    assert expected_error in result.stderr
