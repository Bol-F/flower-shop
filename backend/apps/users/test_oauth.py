from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .models import OAuthLoginAttempt, SocialIdentity, User
from .oauth import OAuthError, ProviderIdentity


OAUTH_SETTINGS = {
    provider: {
        'client_id': f'{provider}-client',
        'client_secret': f'{provider}-secret',
        'redirect_uri': f'http://testserver/api/auth/oauth/{provider}/callback/',
        **({'tenant': 'common'} if provider == 'microsoft' else {}),
    }
    for provider in ('google', 'github', 'microsoft')
}


def _start(client: APIClient, provider: str):
    response = client.get(reverse('oauth-start', args=[provider]))
    assert response.status_code == 302
    query = parse_qs(urlparse(response['Location']).query)
    return query['state'][0]


@pytest.mark.django_db
class TestOAuthFlow:
    @pytest.fixture(autouse=True)
    def _oauth_settings(self):
        with override_settings(OAUTH_PROVIDERS=OAUTH_SETTINGS):
            yield

    @pytest.mark.parametrize('provider', ('google', 'github', 'microsoft'))
    def test_new_user_login_issues_simplejwt(self, provider):
        client = APIClient()
        state = _start(client, provider)
        identity = ProviderIdentity(
            subject=f'{provider}-123',
            email=f'{provider}@example.com',
            email_verified=provider != 'microsoft',
            username=f'{provider}-user',
        )
        with patch('apps.users.views.exchange_provider_code', return_value=identity):
            callback = client.get(
                reverse('oauth-callback', args=[provider]),
                {'state': state, 'code': 'valid-code'},
            )
        callback_query = parse_qs(urlparse(callback['Location']).query)
        exchange = client.post(
            reverse('oauth-exchange'),
            {'code': callback_query['code'][0]},
            format='json',
        )
        assert exchange.status_code == 200
        assert exchange.data['access']
        assert exchange.data['refresh']
        assert exchange.data['user']['email'] == identity.email
        assert SocialIdentity.objects.filter(provider=provider, subject=identity.subject).exists()
        assert not User.objects.get(email=identity.email).has_usable_password()

    def test_verified_email_collision_links_existing_user(self):
        existing = User.objects.create_user(
            username='john', email='john@example.com', password='safe-password'
        )
        client = APIClient()
        state = _start(client, 'google')
        identity = ProviderIdentity(
            subject='google-john',
            email='john@example.com',
            email_verified=True,
        )
        with patch('apps.users.views.exchange_provider_code', return_value=identity):
            response = client.get(
                reverse('oauth-callback', args=['google']),
                {'state': state, 'code': 'valid-code'},
            )
        assert 'code=' in response['Location']
        assert User.objects.filter(email='john@example.com').count() == 1
        assert SocialIdentity.objects.get(subject='google-john').user == existing

    def test_unverified_collision_requires_authenticated_linking(self):
        User.objects.create_user(username='john', email='john@example.com', password='safe-password')
        client = APIClient()
        state = _start(client, 'microsoft')
        identity = ProviderIdentity(
            subject='microsoft-john',
            email='john@example.com',
            email_verified=False,
        )
        with patch('apps.users.views.exchange_provider_code', return_value=identity):
            response = client.get(
                reverse('oauth-callback', args=['microsoft']),
                {'state': state, 'code': 'valid-code'},
            )
        assert 'error=account_exists' in response['Location']
        assert not SocialIdentity.objects.exists()

    def test_authenticated_user_can_link_unverified_provider_identity(self):
        user = User.objects.create_user(
            username='john', email='john@example.com', password='safe-password'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        start = client.post(reverse('oauth-link-start', args=['microsoft']), {}, format='json')
        state = parse_qs(urlparse(start.data['authorization_url']).query)['state'][0]
        identity = ProviderIdentity(
            subject='microsoft-john',
            email='john@example.com',
            email_verified=False,
        )
        with patch('apps.users.views.exchange_provider_code', return_value=identity):
            response = client.get(
                reverse('oauth-callback', args=['microsoft']),
                {'state': state, 'code': 'valid-code'},
            )
        assert response.status_code == 302
        assert 'connected=microsoft' in response['Location']
        assert SocialIdentity.objects.get(subject='microsoft-john').user == user

    def test_invalid_state_is_rejected(self):
        client = APIClient()
        _start(client, 'google')
        response = client.get(
            reverse('oauth-callback', args=['google']),
            {'state': 'attacker-state', 'code': 'valid-code'},
        )
        assert 'error=invalid_state' in response['Location']

    def test_invalid_authorization_code_returns_safe_error(self):
        client = APIClient()
        state = _start(client, 'github')
        with patch(
            'apps.users.views.exchange_provider_code',
            side_effect=OAuthError('provider_rejected', 'The provider rejected the request.'),
        ):
            response = client.get(
                reverse('oauth-callback', args=['github']),
                {'state': state, 'code': 'bad-code'},
            )
        assert 'error=provider_rejected' in response['Location']
        assert 'bad-code' not in response['Location']

    def test_provider_denial_is_handled(self):
        response = APIClient().get(
            reverse('oauth-callback', args=['google']),
            {'error': 'access_denied'},
        )
        assert 'error=cancelled' in response['Location']

    def test_missing_email_does_not_create_user(self):
        client = APIClient()
        state = _start(client, 'github')
        identity = ProviderIdentity(subject='github-no-email', email='', email_verified=False)
        with patch('apps.users.views.exchange_provider_code', return_value=identity):
            response = client.get(
                reverse('oauth-callback', args=['github']),
                {'state': state, 'code': 'valid-code'},
            )
        assert 'error=email_required' in response['Location']
        assert not User.objects.exists()

    def test_duplicate_callback_and_exchange_are_one_time(self):
        client = APIClient()
        state = _start(client, 'google')
        identity = ProviderIdentity(
            subject='google-once', email='once@example.com', email_verified=True
        )
        with patch('apps.users.views.exchange_provider_code', return_value=identity):
            first = client.get(
                reverse('oauth-callback', args=['google']),
                {'state': state, 'code': 'valid-code'},
            )
            duplicate = client.get(
                reverse('oauth-callback', args=['google']),
                {'state': state, 'code': 'valid-code'},
            )
        assert 'error=already_used' in duplicate['Location']
        raw_code = parse_qs(urlparse(first['Location']).query)['code'][0]
        assert client.post(reverse('oauth-exchange'), {'code': raw_code}, format='json').status_code == 200
        assert client.post(reverse('oauth-exchange'), {'code': raw_code}, format='json').status_code == 400
        assert OAuthLoginAttempt.objects.get().used_at is not None
