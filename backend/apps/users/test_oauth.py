import hashlib
import time
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from django.conf import settings
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from .models import (
    OAuthExchangeCode,
    OAuthLinkExchangeCode,
    OAuthLoginAttempt,
    SocialIdentity,
    User,
)
from .oauth import OAuthError, ProviderIdentity, _verified_oidc_claims, resolve_social_user

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


def _callback_fragment(response):
    return parse_qs(urlparse(response['Location']).fragment)


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
        callback_query = _callback_fragment(callback)
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
        User.objects.create_user(
            username='john', email='john@example.com', password='safe-password'
        )
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
        assert not SocialIdentity.objects.exists()
        link_code = _callback_fragment(response)['link_code'][0]
        exchange = client.post(
            reverse('oauth-link-exchange'),
            {'code': link_code},
            format='json',
        )
        assert exchange.status_code == 200
        assert exchange.data['user']['email'] == user.email
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
        client = APIClient()
        state = _start(client, 'google')
        response = client.get(
            reverse('oauth-callback', args=['google']),
            {'error': 'access_denied', 'state': state},
        )
        assert 'error=cancelled' in response['Location']
        attempt = OAuthLoginAttempt.objects.get()
        assert attempt.used_at is not None
        assert attempt.code_verifier == ''
        assert attempt.nonce == ''

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
        assert 'error=invalid_state' in duplicate['Location']
        raw_code = _callback_fragment(first)['code'][0]
        assert (
            client.post(reverse('oauth-exchange'), {'code': raw_code}, format='json').status_code
            == 200
        )
        assert (
            client.post(reverse('oauth-exchange'), {'code': raw_code}, format='json').status_code
            == 400
        )
        attempt = OAuthLoginAttempt.objects.get()
        assert attempt.used_at is not None
        assert attempt.code_verifier == ''
        assert attempt.nonce == ''

    def test_login_state_is_bound_to_the_browser_session(self):
        initiating_client = APIClient()
        other_client = APIClient()
        state = _start(initiating_client, 'google')
        identity = ProviderIdentity(
            subject='google-browser-bound',
            email='browser-bound@example.com',
            email_verified=True,
        )
        with patch(
            'apps.users.views.exchange_provider_code', return_value=identity
        ) as exchange_provider:
            rejected = other_client.get(
                reverse('oauth-callback', args=['google']),
                {'state': state, 'code': 'valid-code'},
            )
            accepted = initiating_client.get(
                reverse('oauth-callback', args=['google']),
                {'state': state, 'code': 'valid-code'},
            )
        assert 'error=invalid_state' in rejected['Location']
        assert _callback_fragment(accepted)['code']
        assert exchange_provider.call_count == 1

    def test_parallel_login_attempts_in_one_session_both_complete(self):
        client = APIClient()
        first_state = _start(client, 'google')
        second_state = _start(client, 'google')
        identities = [
            ProviderIdentity(
                subject='google-parallel-1',
                email='parallel-1@example.com',
                email_verified=True,
            ),
            ProviderIdentity(
                subject='google-parallel-2',
                email='parallel-2@example.com',
                email_verified=True,
            ),
        ]
        with patch('apps.users.views.exchange_provider_code', side_effect=identities):
            first = client.get(
                reverse('oauth-callback', args=['google']),
                {'state': first_state, 'code': 'first-code'},
            )
            second = client.get(
                reverse('oauth-callback', args=['google']),
                {'state': second_state, 'code': 'second-code'},
            )
        assert _callback_fragment(first)['code']
        assert _callback_fragment(second)['code']
        assert SocialIdentity.objects.count() == 2

    def test_denial_without_valid_state_is_rejected(self):
        response = APIClient().get(
            reverse('oauth-callback', args=['google']),
            {'error': 'access_denied'},
        )
        assert 'error=invalid_state' in response['Location']

    def test_expired_login_attempt_is_rejected(self):
        client = APIClient()
        state = _start(client, 'google')
        OAuthLoginAttempt.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        response = client.get(
            reverse('oauth-callback', args=['google']),
            {'state': state, 'code': 'valid-code'},
        )
        assert 'error=expired' in response['Location']

    def test_expired_exchange_code_is_rejected(self):
        client = APIClient()
        state = _start(client, 'google')
        identity = ProviderIdentity(
            subject='google-expired',
            email='expired@example.com',
            email_verified=True,
        )
        with patch('apps.users.views.exchange_provider_code', return_value=identity):
            callback = client.get(
                reverse('oauth-callback', args=['google']),
                {'state': state, 'code': 'valid-code'},
            )
        raw_code = _callback_fragment(callback)['code'][0]
        OAuthExchangeCode.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        response = client.post(reverse('oauth-exchange'), {'code': raw_code}, format='json')
        assert response.status_code == 400
        assert response.data['code'] == 'invalid_exchange'

    def test_inactive_user_cannot_exchange_code_for_jwt(self):
        client = APIClient()
        state = _start(client, 'google')
        identity = ProviderIdentity(
            subject='google-disabled',
            email='disabled@example.com',
            email_verified=True,
        )
        with patch('apps.users.views.exchange_provider_code', return_value=identity):
            callback = client.get(
                reverse('oauth-callback', args=['google']),
                {'state': state, 'code': 'valid-code'},
            )
        raw_code = _callback_fragment(callback)['code'][0]
        user = User.objects.get(email=identity.email)
        user.is_active = False
        user.save(update_fields=('is_active',))
        response = client.post(reverse('oauth-exchange'), {'code': raw_code}, format='json')
        assert response.status_code == 403
        assert response.data['code'] == 'account_inactive'
        assert (
            client.post(reverse('oauth-exchange'), {'code': raw_code}, format='json').status_code
            == 400
        )

    def test_link_exchange_requires_the_user_that_started_it_and_is_one_time(self):
        owner = User.objects.create_user(
            username='owner', email='owner@example.com', password='safe-password'
        )
        other = User.objects.create_user(
            username='other', email='other@example.com', password='safe-password'
        )
        owner_client = APIClient()
        owner_client.force_authenticate(user=owner)
        start = owner_client.post(reverse('oauth-link-start', args=['github']), {}, format='json')
        state = parse_qs(urlparse(start.data['authorization_url']).query)['state'][0]
        identity = ProviderIdentity(
            subject='github-owner',
            email='owner@example.com',
            email_verified=True,
        )
        with patch('apps.users.views.exchange_provider_code', return_value=identity):
            callback = owner_client.get(
                reverse('oauth-callback', args=['github']),
                {'state': state, 'code': 'valid-code'},
            )
        link_code = _callback_fragment(callback)['link_code'][0]
        assert OAuthLinkExchangeCode.objects.count() == 1
        assert not SocialIdentity.objects.exists()
        assert (
            APIClient()
            .post(reverse('oauth-link-exchange'), {'code': link_code}, format='json')
            .status_code
            == 401
        )
        other_client = APIClient()
        other_client.force_authenticate(user=other)
        mismatch = other_client.post(
            reverse('oauth-link-exchange'), {'code': link_code}, format='json'
        )
        assert mismatch.status_code == 403
        assert OAuthLinkExchangeCode.objects.get().used_at is None
        completed = owner_client.post(
            reverse('oauth-link-exchange'), {'code': link_code}, format='json'
        )
        assert completed.status_code == 200
        assert SocialIdentity.objects.get(subject=identity.subject).user == owner
        assert (
            owner_client.post(
                reverse('oauth-link-exchange'), {'code': link_code}, format='json'
            ).status_code
            == 400
        )

    def test_expired_link_exchange_is_rejected(self):
        user = User.objects.create_user(
            username='link-expired',
            email='link-expired@example.com',
            password='safe-password',
        )
        client = APIClient()
        client.force_authenticate(user=user)
        start = client.post(reverse('oauth-link-start', args=['google']), {}, format='json')
        state = parse_qs(urlparse(start.data['authorization_url']).query)['state'][0]
        identity = ProviderIdentity(
            subject='google-link-expired',
            email=user.email,
            email_verified=True,
        )
        with patch('apps.users.views.exchange_provider_code', return_value=identity):
            callback = client.get(
                reverse('oauth-callback', args=['google']),
                {'state': state, 'code': 'valid-code'},
            )
        raw_code = _callback_fragment(callback)['link_code'][0]
        OAuthLinkExchangeCode.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        response = client.post(reverse('oauth-link-exchange'), {'code': raw_code}, format='json')
        assert response.status_code == 400
        assert not SocialIdentity.objects.exists()

    def test_only_one_identity_per_provider_can_be_linked(self):
        user = User.objects.create_user(
            username='already-linked',
            email='already-linked@example.com',
            password='safe-password',
        )
        SocialIdentity.objects.create(
            user=user,
            provider='google',
            issuer='https://accounts.google.com',
            subject='existing-google-subject',
            email=user.email,
            email_verified=True,
        )
        client = APIClient()
        client.force_authenticate(user=user)
        start = client.post(reverse('oauth-link-start', args=['google']), {}, format='json')
        state = parse_qs(urlparse(start.data['authorization_url']).query)['state'][0]
        identity = ProviderIdentity(
            subject='different-google-subject',
            issuer='https://accounts.google.com',
            email=user.email,
            email_verified=True,
        )
        with patch('apps.users.views.exchange_provider_code', return_value=identity):
            callback = client.get(
                reverse('oauth-callback', args=['google']),
                {'state': state, 'code': 'valid-code'},
            )
        link_code = _callback_fragment(callback)['link_code'][0]
        response = client.post(reverse('oauth-link-exchange'), {'code': link_code}, format='json')
        assert response.status_code == 400
        assert response.data['code'] == 'provider_already_linked'
        assert SocialIdentity.objects.filter(user=user, provider='google').count() == 1

    @pytest.mark.parametrize(
        'unsafe_next',
        (
            'https://evil.example/steal',
            '//evil.example/steal',
            '/\\evil.example/steal',
            '/%5C%5Cevil.example/steal',
            '/%2F%2Fevil.example/steal',
            'javascript:alert(1)',
            '/safe\nunsafe',
        ),
    )
    def test_unsafe_next_path_falls_back_to_profile(self, unsafe_next):
        client = APIClient()
        response = client.get(
            reverse('oauth-start', args=['google']),
            {'next': unsafe_next},
        )
        assert response.status_code == 302
        assert OAuthLoginAttempt.objects.get().next_path == '/profile'

    def test_start_uses_pkce_and_keeps_raw_state_out_of_database(self):
        client = APIClient()
        response = client.get(
            reverse('oauth-start', args=['google']),
            {'next': '/orders?status=pending'},
        )
        query = parse_qs(urlparse(response['Location']).query)
        state = query['state'][0]
        attempt = OAuthLoginAttempt.objects.get()
        assert query['code_challenge_method'] == ['S256']
        assert query['code_challenge'][0]
        assert 'client_secret' not in query
        assert attempt.state_digest == hashlib.sha256(state.encode()).hexdigest()
        assert state not in attempt.state_digest
        assert attempt.next_path == '/orders?status=pending'

    @override_settings(SESSION_COOKIE_SECURE=True)
    def test_start_session_cookie_is_http_only_lax_and_secure(self):
        response = APIClient().get(reverse('oauth-start', args=['google']))
        cookie = response.cookies[settings.SESSION_COOKIE_NAME]
        assert cookie['httponly'] is True
        assert cookie['samesite'] == 'Lax'
        assert cookie['secure'] is True

    def test_provider_capabilities_and_unconfigured_start(self):
        enabled = APIClient().get(reverse('oauth-providers'))
        assert {item['id'] for item in enabled.data['providers'] if item['enabled']} == {
            'google',
            'github',
            'microsoft',
        }
        with override_settings(OAUTH_PROVIDERS={}):
            disabled = APIClient().get(reverse('oauth-providers'))
            assert not any(item['enabled'] for item in disabled.data['providers'])
            start = APIClient().get(reverse('oauth-start', args=['google']))
        assert 'error=provider_unavailable' in start['Location']

    def test_expired_oauth_rows_can_be_purged_without_touching_live_rows(self):
        client = APIClient()
        _start(client, 'google')
        expired_attempt = OAuthLoginAttempt.objects.get()
        expired_attempt.expires_at = timezone.now() - timedelta(seconds=1)
        expired_attempt.save(update_fields=('expires_at',))
        live_attempt = OAuthLoginAttempt.objects.create(
            provider='github',
            state_digest='a' * 64,
            code_verifier='verifier',
            nonce='nonce',
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        user = User.objects.create_user(
            username='cleanup', email='cleanup@example.com', password='safe-password'
        )
        OAuthExchangeCode.objects.create(
            user=user,
            token_digest='b' * 64,
            expires_at=timezone.now() - timedelta(seconds=1),
        )
        OAuthLinkExchangeCode.objects.create(
            linking_user=user,
            provider='google',
            issuer='https://accounts.google.com',
            subject='cleanup-subject',
            token_digest='c' * 64,
            expires_at=timezone.now() - timedelta(seconds=1),
        )
        call_command('purge_expired_oauth', verbosity=0)
        assert not OAuthLoginAttempt.objects.filter(pk=expired_attempt.pk).exists()
        assert OAuthLoginAttempt.objects.filter(pk=live_attempt.pk).exists()
        assert not OAuthExchangeCode.objects.exists()
        assert not OAuthLinkExchangeCode.objects.exists()

    def test_same_subject_from_different_oidc_issuers_is_not_conflated(self):
        first = resolve_social_user(
            'microsoft',
            ProviderIdentity(
                issuer='https://login.microsoftonline.com/11111111-1111-4111-8111-111111111111/v2.0',
                subject='pairwise-subject',
                email='first-tenant@example.com',
                email_verified=False,
            ),
        )
        second = resolve_social_user(
            'microsoft',
            ProviderIdentity(
                issuer='https://login.microsoftonline.com/22222222-2222-4222-8222-222222222222/v2.0',
                subject='pairwise-subject',
                email='second-tenant@example.com',
                email_verified=False,
            ),
        )
        assert first != second
        assert (
            SocialIdentity.objects.filter(provider='microsoft', subject='pairwise-subject').count()
            == 2
        )


def _oidc_claims(**overrides):
    claims = {
        'iss': 'https://accounts.google.com',
        'aud': 'google-client',
        'exp': int(time.time()) + 300,
        'iat': int(time.time()),
        'sub': 'google-subject',
        'nonce': 'expected-nonce',
        'email': 'verified@example.com',
    }
    claims.update(overrides)
    return claims


def test_oidc_claims_require_verified_signature_audience_issuer_and_nonce():
    claims = _oidc_claims()
    with (
        patch('apps.users.oauth._fetch_json', return_value={'keys': []}),
        patch('apps.users.oauth.KeySet.import_key_set', return_value=object()),
        patch('apps.users.oauth.jwt.decode', return_value=SimpleNamespace(claims=claims)) as decode,
    ):
        verified = _verified_oidc_claims(
            'google', {'client_id': 'google-client'}, 'signed-id-token', 'expected-nonce'
        )
    assert verified['sub'] == 'google-subject'
    assert decode.call_args.kwargs['algorithms'] == ['RS256']


@pytest.mark.parametrize(
    'overrides',
    (
        {'nonce': 'attacker-nonce'},
        {'aud': 'another-client'},
        {'iss': 'https://attacker.example'},
        {'exp': 1},
        {'iat': None},
    ),
)
def test_oidc_invalid_security_claims_are_rejected(overrides):
    with (
        patch('apps.users.oauth._fetch_json', return_value={'keys': []}),
        patch('apps.users.oauth.KeySet.import_key_set', return_value=object()),
        patch(
            'apps.users.oauth.jwt.decode',
            return_value=SimpleNamespace(claims=_oidc_claims(**overrides)),
        ),
    ):
        with pytest.raises(OAuthError) as error:
            _verified_oidc_claims(
                'google', {'client_id': 'google-client'}, 'signed-id-token', 'expected-nonce'
            )
    assert error.value.code == 'invalid_token'


def test_microsoft_common_tenant_requires_signed_tenant_id():
    claims = _oidc_claims(
        iss='https://login.microsoftonline.com/tenant-id/v2.0',
        aud='microsoft-client',
    )
    with (
        patch('apps.users.oauth._fetch_json', return_value={'keys': []}),
        patch('apps.users.oauth.KeySet.import_key_set', return_value=object()),
        patch('apps.users.oauth.jwt.decode', return_value=SimpleNamespace(claims=claims)),
    ):
        with pytest.raises(OAuthError):
            _verified_oidc_claims(
                'microsoft',
                {'client_id': 'microsoft-client', 'tenant': 'common'},
                'signed-id-token',
                'expected-nonce',
            )


def test_microsoft_common_tenant_accepts_matching_signed_issuer():
    tenant_id = '11111111-1111-4111-8111-111111111111'
    claims = _oidc_claims(
        iss=f'https://login.microsoftonline.com/{tenant_id}/v2.0',
        tid=tenant_id,
        aud='microsoft-client',
    )
    with (
        patch('apps.users.oauth._fetch_json', return_value={'keys': []}),
        patch('apps.users.oauth.KeySet.import_key_set', return_value=object()),
        patch('apps.users.oauth.jwt.decode', return_value=SimpleNamespace(claims=claims)),
    ):
        verified = _verified_oidc_claims(
            'microsoft',
            {'client_id': 'microsoft-client', 'tenant': 'common'},
            'signed-id-token',
            'expected-nonce',
        )
    assert verified['tid'] == tenant_id


@pytest.mark.parametrize(
    ('tenant', 'tenant_id'),
    (
        ('organizations', '9188040d-6c67-4c5b-b112-36a304b66dad'),
        ('consumers', '11111111-1111-4111-8111-111111111111'),
    ),
)
def test_microsoft_tenant_alias_rejects_wrong_account_type(tenant, tenant_id):
    claims = _oidc_claims(
        iss=f'https://login.microsoftonline.com/{tenant_id}/v2.0',
        tid=tenant_id,
        aud='microsoft-client',
    )
    with (
        patch('apps.users.oauth._fetch_json', return_value={'keys': []}),
        patch('apps.users.oauth.KeySet.import_key_set', return_value=object()),
        patch('apps.users.oauth.jwt.decode', return_value=SimpleNamespace(claims=claims)),
        pytest.raises(OAuthError) as error,
    ):
        _verified_oidc_claims(
            'microsoft',
            {'client_id': 'microsoft-client', 'tenant': tenant},
            'signed-id-token',
            'expected-nonce',
        )
    assert error.value.code == 'invalid_token'


def test_oidc_multiple_audiences_require_authorized_party():
    claims = _oidc_claims(aud=['google-client', 'another-audience'])
    with (
        patch('apps.users.oauth._fetch_json', return_value={'keys': []}),
        patch('apps.users.oauth.KeySet.import_key_set', return_value=object()),
        patch('apps.users.oauth.jwt.decode', return_value=SimpleNamespace(claims=claims)),
        pytest.raises(OAuthError) as error,
    ):
        _verified_oidc_claims(
            'google', {'client_id': 'google-client'}, 'signed-id-token', 'expected-nonce'
        )
    assert error.value.code == 'invalid_token'
