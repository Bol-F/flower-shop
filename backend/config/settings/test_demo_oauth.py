import os
import subprocess
import sys
from pathlib import Path

import pytest

from config.settings.public_oauth import validate_public_oauth
from django.core.exceptions import ImproperlyConfigured


def configuration():
    return {
        'frontend_url': 'https://shop.example.com',
        'callback_url': 'https://shop.example.com/auth/callback',
        'allowed_hosts': ['api.example.com'],
        'providers': {
            'google': {
                'client_id': 'configured-client',
                'client_secret': 'configured-secret',
                'redirect_uri': 'https://api.example.com/api/auth/oauth/google/callback/',
            }
        },
    }


def test_public_demo_oauth_configuration_is_validated():
    validate_public_oauth(**configuration())


@pytest.mark.parametrize(
    'value',
    [
        'http://api.example.com/api/auth/oauth/google/callback/',
        'https://localhost/api/auth/oauth/google/callback/',
        'https://127.0.0.1/api/auth/oauth/google/callback/',
        'https://evil.example.com/api/auth/oauth/google/callback/',
        'https://api.example.com/auth/callback',
        'https://api.example.com/api/auth/oauth/google/callback/?next=evil',
        'https://user:secret@api.example.com/api/auth/oauth/google/callback/',
    ],
)
def test_demo_rejects_unsafe_provider_redirects(value):
    config = configuration()
    config['providers']['google']['redirect_uri'] = value
    with pytest.raises(ImproperlyConfigured):
        validate_public_oauth(**config)


@pytest.mark.parametrize(
    'changes',
    [
        {'frontend_url': 'http://shop.example.com'},
        {'frontend_url': 'https://shop.example.com/path'},
        {'callback_url': 'https://elsewhere.example.com/auth/callback'},
        {'callback_url': 'https://shop.example.com/wrong'},
        {'callback_url': 'https://shop.example.com/auth/callback#fragment'},
    ],
)
def test_demo_rejects_unsafe_frontend_configuration(changes):
    with pytest.raises(ImproperlyConfigured):
        validate_public_oauth(**{**configuration(), **changes})


def test_demo_rejects_partial_provider_credentials():
    config = configuration()
    config['providers']['google']['client_secret'] = ''
    with pytest.raises(ImproperlyConfigured, match='incomplete'):
        validate_public_oauth(**config)


@pytest.mark.parametrize('enabled', [False, True])
def test_demo_oauth_is_explicit_opt_in_and_test_payments_remain(enabled):
    environment = os.environ.copy()
    environment.update(
        {
            'SECRET_KEY': 'test-only-config-secret',
            'FLOWER_DEMO_MODE': 'acknowledged-test-payments',
            'DJANGO_SETTINGS_MODULE': 'config.settings.demo',
            'ALLOWED_HOSTS': 'api.example.com',
            'FRONTEND_URL': 'https://shop.example.com',
            'CORS_ALLOWED_ORIGINS': 'https://shop.example.com',
            'PAYMENT_FRONTEND_RETURN_URL': 'https://shop.example.com/payment/return',
            'OAUTH_FRONTEND_CALLBACK_URL': 'https://shop.example.com/auth/callback',
            'GOOGLE_OAUTH_CLIENT_ID': 'configured-client',
            'GOOGLE_OAUTH_CLIENT_SECRET': 'configured-secret',
            'GOOGLE_OAUTH_REDIRECT_URI': 'https://api.example.com/api/auth/oauth/google/callback/',
            'GITHUB_OAUTH_CLIENT_ID': '',
            'GITHUB_OAUTH_CLIENT_SECRET': '',
            'MICROSOFT_OAUTH_CLIENT_ID': '',
            'MICROSOFT_OAUTH_CLIENT_SECRET': '',
            'MICROSOFT_OAUTH_TENANT': 'common',
            'DEMO_OAUTH_ENABLED': str(enabled).lower(),
            'DATABASE_URL': '',
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            '-c',
            'import config.settings.demo as s; print(bool(s.OAUTH_PROVIDERS["google"]["client_id"])); print(s.PAYMENT_PROVIDER)',
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [str(enabled), 'test']
