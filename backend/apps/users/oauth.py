import base64
import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass
from datetime import timedelta
from urllib.parse import urlencode, urlparse

import requests
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import KeySet
from joserfc.jwt import JWTClaimsRegistry

from .models import OAuthLoginAttempt, SocialIdentity, User


class OAuthError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class ProviderIdentity:
    subject: str
    email: str
    email_verified: bool
    username: str = ''
    first_name: str = ''
    last_name: str = ''


PROVIDER_ENDPOINTS = {
    'google': {
        'authorize': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token': 'https://oauth2.googleapis.com/token',
        'jwks': 'https://www.googleapis.com/oauth2/v3/certs',
        'scope': 'openid profile email',
    },
    'github': {
        'authorize': 'https://github.com/login/oauth/authorize',
        'token': 'https://github.com/login/oauth/access_token',
        'scope': 'read:user user:email',
    },
    'microsoft': {
        'scope': 'openid profile email',
    },
}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode('ascii')).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')


def provider_config(provider: str) -> dict:
    if provider not in PROVIDER_ENDPOINTS:
        raise OAuthError('unsupported_provider', 'Unsupported sign-in provider.')
    config = settings.OAUTH_PROVIDERS.get(provider, {})
    if not config.get('client_id') or not config.get('client_secret'):
        raise OAuthError(
            'provider_unavailable',
            f'{provider.title()} sign-in is not configured.',
        )
    return config


def configured_providers() -> list[str]:
    return [
        provider
        for provider in PROVIDER_ENDPOINTS
        if settings.OAUTH_PROVIDERS.get(provider, {}).get('client_id')
        and settings.OAUTH_PROVIDERS.get(provider, {}).get('client_secret')
    ]


def safe_next_path(value: str | None, default: str = '/profile') -> str:
    value = (value or '').strip()
    parsed = urlparse(value)
    if not value.startswith('/') or value.startswith('//') or parsed.scheme or parsed.netloc:
        return default
    return value[:500]


def create_login_attempt(provider: str, *, next_path: str = '', linking_user=None):
    config = provider_config(provider)
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    nonce = secrets.token_urlsafe(32)
    attempt = OAuthLoginAttempt.objects.create(
        provider=provider,
        state_digest=_sha256(state),
        code_verifier=verifier,
        nonce=nonce,
        next_path=safe_next_path(next_path),
        linking_user=linking_user,
        expires_at=timezone.now() + timedelta(seconds=settings.OAUTH_ATTEMPT_TTL_SECONDS),
    )
    return attempt, state, _authorization_url(provider, config, state, verifier, nonce)


def _authorization_url(provider: str, config: dict, state: str, verifier: str, nonce: str) -> str:
    common = {
        'client_id': config['client_id'],
        'redirect_uri': config['redirect_uri'],
        'response_type': 'code',
        'scope': PROVIDER_ENDPOINTS[provider]['scope'],
        'state': state,
        'code_challenge': _pkce_challenge(verifier),
        'code_challenge_method': 'S256',
    }
    if provider == 'google':
        common.update({'nonce': nonce, 'prompt': 'select_account'})
        endpoint = PROVIDER_ENDPOINTS[provider]['authorize']
    elif provider == 'microsoft':
        common.update({'nonce': nonce, 'prompt': 'select_account'})
        tenant = config.get('tenant') or 'common'
        endpoint = f'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize'
    else:
        common['allow_signup'] = 'true'
        endpoint = PROVIDER_ENDPOINTS[provider]['authorize']
    return f'{endpoint}?{urlencode(common)}'


@transaction.atomic
def consume_login_attempt(provider: str, state: str) -> OAuthLoginAttempt:
    state_digest = _sha256(state or '')
    attempt = (
        OAuthLoginAttempt.objects.select_for_update()
        .select_related('linking_user')
        .filter(provider=provider, state_digest=state_digest)
        .first()
    )
    if attempt is None or not hmac.compare_digest(attempt.state_digest, state_digest):
        raise OAuthError('invalid_state', 'The sign-in request could not be verified.')
    if attempt.used_at is not None:
        raise OAuthError('already_used', 'This sign-in request has already been used.')
    if attempt.expires_at <= timezone.now():
        raise OAuthError('expired', 'This sign-in request has expired. Please try again.')
    attempt.used_at = timezone.now()
    attempt.save(update_fields=('used_at',))
    return attempt


def exchange_provider_code(
    provider: str, code: str, attempt: OAuthLoginAttempt
) -> ProviderIdentity:
    config = provider_config(provider)
    token = _token_exchange(provider, config, code, attempt.code_verifier)
    if provider == 'github':
        return _github_identity(token)
    id_token = token.get('id_token')
    if not id_token:
        raise OAuthError('invalid_token', 'The identity provider did not return an ID token.')
    claims = _verified_oidc_claims(provider, config, id_token, attempt.nonce)
    if provider == 'google':
        return ProviderIdentity(
            subject=str(claims['sub']),
            email=str(claims.get('email') or '').strip().lower(),
            email_verified=claims.get('email_verified') is True,
            username=str(claims.get('name') or ''),
            first_name=str(claims.get('given_name') or ''),
            last_name=str(claims.get('family_name') or ''),
        )
    # Microsoft documents email/preferred_username as mutable and not suitable
    # for identity or automatic account linking. The signed sub claim is the key.
    email = str(claims.get('email') or claims.get('preferred_username') or '').strip().lower()
    return ProviderIdentity(
        subject=str(claims['sub']),
        email=email if '@' in email else '',
        email_verified=False,
        username=str(claims.get('name') or ''),
        first_name=str(claims.get('given_name') or ''),
        last_name=str(claims.get('family_name') or ''),
    )


def _token_exchange(provider: str, config: dict, code: str, verifier: str) -> dict:
    if not code:
        raise OAuthError('missing_code', 'The identity provider did not return a code.')
    if provider == 'microsoft':
        tenant = config.get('tenant') or 'common'
        endpoint = f'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token'
    else:
        endpoint = PROVIDER_ENDPOINTS[provider]['token']
    headers = {'Accept': 'application/json'}
    payload = {
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'code': code,
        'redirect_uri': config['redirect_uri'],
        'grant_type': 'authorization_code',
        'code_verifier': verifier,
    }
    try:
        response = requests.post(
            endpoint,
            data=payload,
            headers=headers,
            timeout=settings.OAUTH_HTTP_TIMEOUT_SECONDS,
        )
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise OAuthError('provider_error', 'The identity provider could not be reached.') from exc
    if not response.ok or data.get('error') or not data.get('access_token'):
        raise OAuthError('provider_rejected', 'The identity provider rejected the sign-in request.')
    return data


def _fetch_json(url: str, *, token: str = '') -> dict | list:
    headers = {'Accept': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    try:
        response = requests.get(url, headers=headers, timeout=settings.OAUTH_HTTP_TIMEOUT_SECONDS)
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise OAuthError('provider_error', 'The identity provider could not be reached.') from exc
    if not response.ok:
        raise OAuthError('provider_rejected', 'The identity provider rejected the profile request.')
    return data


def _verified_oidc_claims(provider: str, config: dict, id_token: str, nonce: str):
    if provider == 'google':
        jwks_url = PROVIDER_ENDPOINTS['google']['jwks']
    else:
        jwks_url = 'https://login.microsoftonline.com/common/discovery/v2.0/keys'
    jwks = _fetch_json(jwks_url)
    try:
        token = jwt.decode(
            id_token,
            KeySet.import_key_set(jwks),
            algorithms=['RS256'],
        )
        claims = token.claims
    except (JoseError, ValueError, TypeError, KeyError) as exc:
        raise OAuthError('invalid_token', 'The identity token could not be verified.') from exc

    issuer = str(claims.get('iss') or '')
    if provider == 'google':
        valid_issuers = ['https://accounts.google.com', 'accounts.google.com']
    else:
        tenant = config.get('tenant') or 'common'
        tenant_id = str(claims.get('tid') or '')
        if tenant in {'common', 'organizations', 'consumers'}:
            valid_issuers = (
                [f'https://login.microsoftonline.com/{tenant_id}/v2.0'] if tenant_id else []
            )
        else:
            valid_issuers = [f'https://login.microsoftonline.com/{tenant}/v2.0']
    if not valid_issuers:
        raise OAuthError('invalid_token', 'The identity token issuer is not trusted.')
    try:
        JWTClaimsRegistry(
            leeway=60,
            iss={'essential': True, 'values': valid_issuers},
            aud={'essential': True, 'value': config['client_id']},
            exp={'essential': True},
            sub={'essential': True},
            nonce={'essential': True, 'value': nonce},
        ).validate(claims)
    except (JoseError, ValueError, TypeError, KeyError) as exc:
        raise OAuthError(
            'invalid_token', 'The identity token claims could not be verified.'
        ) from exc
    return claims


def _github_identity(token: dict) -> ProviderIdentity:
    access_token = str(token['access_token'])
    profile = _fetch_json('https://api.github.com/user', token=access_token)
    emails = _fetch_json('https://api.github.com/user/emails', token=access_token)
    if not isinstance(profile, dict) or not isinstance(emails, list):
        raise OAuthError('invalid_profile', 'GitHub returned an invalid profile.')
    verified = [item for item in emails if item.get('verified') and item.get('email')]
    primary = next((item for item in verified if item.get('primary')), None)
    selected = primary or (verified[0] if verified else None)
    email = str(selected.get('email')).strip().lower() if selected else ''
    full_name = str(profile.get('name') or '').strip()
    first_name, _, last_name = full_name.partition(' ')
    return ProviderIdentity(
        subject=str(profile.get('id') or ''),
        email=email,
        email_verified=bool(selected),
        username=str(profile.get('login') or full_name),
        first_name=first_name,
        last_name=last_name,
    )


def _unique_username(identity: ProviderIdentity) -> str:
    source = identity.username or identity.email.partition('@')[0] or 'flower-friend'
    base = re.sub(r'[^\w.@+-]', '-', source.lower()).strip('-')[:130] or 'flower-friend'
    candidate = base
    for suffix in range(1, 10000):
        if not User.objects.filter(username__iexact=candidate).exists():
            return candidate
        candidate = f'{base[: 140 - len(str(suffix))]}-{suffix}'
    return f'flower-friend-{secrets.token_hex(6)}'


@transaction.atomic
def resolve_social_user(provider: str, identity: ProviderIdentity, *, linking_user=None) -> User:
    if not identity.subject:
        raise OAuthError('invalid_profile', 'The provider profile has no stable identifier.')
    existing_identity = (
        SocialIdentity.objects.select_for_update()
        .select_related('user')
        .filter(provider=provider, subject=identity.subject)
        .first()
    )
    if existing_identity:
        if linking_user and existing_identity.user_id != linking_user.id:
            raise OAuthError('identity_in_use', 'This provider account is linked elsewhere.')
        existing_identity.email = identity.email
        existing_identity.email_verified = identity.email_verified
        existing_identity.save(update_fields=('email', 'email_verified', 'updated_at'))
        return existing_identity.user

    user = linking_user
    if user is None:
        if not identity.email:
            raise OAuthError(
                'email_required',
                'A usable email address is required to create an account.',
            )
        user = User.objects.filter(email__iexact=identity.email).first()
        if user and not identity.email_verified:
            raise OAuthError(
                'account_exists',
                'Sign in with your existing account, then connect this provider in Profile.',
            )
        if user is None:
            user = User(
                email=identity.email,
                username=_unique_username(identity),
                first_name=identity.first_name[:150],
                last_name=identity.last_name[:150],
            )
            user.set_unusable_password()
            user.save()

    try:
        SocialIdentity.objects.create(
            user=user,
            provider=provider,
            subject=identity.subject,
            email=identity.email,
            email_verified=identity.email_verified,
        )
    except IntegrityError as exc:
        raise OAuthError('identity_in_use', 'This provider account is linked elsewhere.') from exc
    user.last_login = timezone.now()
    user.save(update_fields=('last_login',))
    return user
