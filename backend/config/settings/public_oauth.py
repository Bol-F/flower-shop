"""Validate public OAuth callbacks without importing production payment settings."""

from ipaddress import ip_address
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import URLValidator

from apps.users.oauth_config import valid_microsoft_tenant


def _url(value, name, *, path=None, origin=False):
    try:
        URLValidator(schemes=['https'])(value)
        parsed = urlsplit(value)
        _ = parsed.port
        hostname = (parsed.hostname or '').lower().rstrip('.')
        local = hostname == 'localhost' or hostname.endswith('.localhost')
        try:
            local = local or ip_address(hostname).is_loopback
        except ValueError:
            pass
        invalid = (
            parsed.scheme != 'https'
            or not hostname
            or local
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or (path is not None and parsed.path != path)
            or (origin and value != f'https://{parsed.netloc}')
        )
        if invalid:
            raise ValueError('Invalid public OAuth URL')
    except (TypeError, ValueError, ValidationError) as error:
        raise ImproperlyConfigured(
            f'{name} must be an exact public HTTPS URL with no query, fragment, or user information.'
        ) from error
    return parsed


def validate_public_oauth(*, frontend_url, callback_url, providers, allowed_hosts):
    frontend = _url(frontend_url, 'FRONTEND_URL', origin=True)
    callback = _url(callback_url, 'OAUTH_FRONTEND_CALLBACK_URL', path='/auth/callback')
    if (frontend.hostname, frontend.port or 443) != (callback.hostname, callback.port or 443):
        raise ImproperlyConfigured('OAUTH_FRONTEND_CALLBACK_URL must use the FRONTEND_URL origin.')
    if not valid_microsoft_tenant(providers.get('microsoft', {}).get('tenant', 'common')):
        raise ImproperlyConfigured('MICROSOFT_OAUTH_TENANT is invalid.')
    for name, provider in providers.items():
        supplied = [
            bool(str(provider.get(field, '')).strip()) for field in ('client_id', 'client_secret')
        ]
        if any(supplied) and not all(supplied):
            raise ImproperlyConfigured(f'{name.title()} OAuth credentials are incomplete.')
        if not all(supplied):
            continue
        setting_name = f'{name.upper()}_OAUTH_REDIRECT_URI'
        redirect = _url(
            provider.get('redirect_uri', ''), setting_name, path=f'/api/auth/oauth/{name}/callback/'
        )
        hostname = redirect.hostname.lower().rstrip('.')
        allowed = any(
            hostname == host.strip().lower().rstrip('.').lstrip('.')
            or (host.startswith('.') and hostname.endswith(host.lower().rstrip('.')))
            for host in allowed_hosts
            if host.strip() and host.strip() != '*'
        )
        if not allowed:
            raise ImproperlyConfigured(f'{setting_name} hostname must be present in ALLOWED_HOSTS.')
