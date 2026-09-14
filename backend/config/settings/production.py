from ipaddress import ip_address
from urllib.parse import SplitResult, urlsplit
from uuid import UUID

from django.core.exceptions import ImproperlyConfigured

from .base import *


def _is_local_hostname(hostname: str) -> bool:
    normalized = hostname.lower().rstrip('.')
    if normalized == 'localhost' or normalized.endswith('.localhost'):
        return True
    try:
        return ip_address(normalized).is_loopback
    except ValueError:
        return False


def _production_url(
    value: str,
    setting_name: str,
    *,
    expected_path: str | None = None,
    origin_only: bool = False,
) -> SplitResult:
    try:
        parsed = urlsplit(value)
        # Accessing ``port`` also validates malformed values such as ``:abc``.
        _ = parsed.port
    except (TypeError, ValueError) as exc:
        raise ImproperlyConfigured(f'{setting_name} must be a valid HTTPS URL.') from exc

    if parsed.scheme.lower() != 'https' or not parsed.hostname:
        raise ImproperlyConfigured(f'{setting_name} must be a valid HTTPS URL.')
    if parsed.username is not None or parsed.password is not None:
        raise ImproperlyConfigured(f'{setting_name} must not contain user information.')
    if parsed.query or parsed.fragment:
        raise ImproperlyConfigured(f'{setting_name} must not contain a query or fragment.')
    if _is_local_hostname(parsed.hostname):
        raise ImproperlyConfigured(f'{setting_name} must not use a localhost address.')

    normalized_path = parsed.path or '/'
    if origin_only and normalized_path != '/':
        raise ImproperlyConfigured(f'{setting_name} must contain only the frontend origin.')
    if expected_path is not None and normalized_path != expected_path:
        raise ImproperlyConfigured(f'{setting_name} must use the exact path {expected_path}.')
    return parsed


def _origin(parsed: SplitResult) -> tuple[str, str, int]:
    default_port = 443 if parsed.scheme.lower() == 'https' else 80
    return parsed.scheme.lower(), parsed.hostname.lower().rstrip('.'), parsed.port or default_port


def _hostname_is_allowed(hostname: str, allowed_hosts: list[str]) -> bool:
    normalized = hostname.lower().rstrip('.')
    for allowed_host in allowed_hosts:
        candidate = allowed_host.strip().lower().rstrip('.')
        if candidate.startswith('.'):
            if normalized == candidate[1:] or normalized.endswith(candidate):
                return True
        elif normalized == candidate:
            return True
    return False


def _valid_microsoft_tenant(tenant: str) -> bool:
    normalized = tenant.strip().lower()
    if normalized in {'common', 'organizations', 'consumers'}:
        return True
    try:
        return str(UUID(normalized)) == normalized
    except (ValueError, AttributeError):
        return False


DEBUG = False
PAYMENT_TEST_MODE_ENABLED = False

# Tolerate stray spaces in comma-separated dashboard values
ALLOWED_HOSTS = [h.strip() for h in env('ALLOWED_HOSTS') if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in CSRF_TRUSTED_ORIGINS if o.strip()]
CORS_ALLOWED_ORIGINS = [o.strip() for o in CORS_ALLOWED_ORIGINS if o.strip()]

# Render sets RENDER_EXTERNAL_HOSTNAME on every web service — trust it
# automatically so the deploy works regardless of the ALLOWED_HOSTS value.
RENDER_EXTERNAL_HOSTNAME = env('RENDER_EXTERNAL_HOSTNAME', default='')
if RENDER_EXTERNAL_HOSTNAME:
    if RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    origin = f'https://{RENDER_EXTERNAL_HOSTNAME}'
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
    raise ImproperlyConfigured('Production ALLOWED_HOSTS must be explicit.')

insecure_cors_origins = [
    origin
    for origin in CORS_ALLOWED_ORIGINS
    if origin.startswith('http://') and 'localhost' not in origin and '127.0.0.1' not in origin
]
if insecure_cors_origins:
    raise ImproperlyConfigured('Production CORS_ALLOWED_ORIGINS must use HTTPS.')

if PAYMENT_PROVIDER not in {'payme', 'click'}:
    raise ImproperlyConfigured(
        'Production PAYMENT_PROVIDER must explicitly be payme or click; test fallback is forbidden.'
    )

payment_requirements = {
    'payme': {
        'PAYME_MERCHANT_ID': PAYME_MERCHANT_ID,
        'PAYME_LOGIN': PAYME_LOGIN,
        'PAYME_SECRET_KEY': PAYME_SECRET_KEY,
        'PAYME_CHECKOUT_URL': PAYME_CHECKOUT_URL,
    },
    'click': {
        'CLICK_SERVICE_ID': CLICK_SERVICE_ID,
        'CLICK_MERCHANT_ID': CLICK_MERCHANT_ID,
        'CLICK_SECRET_KEY': CLICK_SECRET_KEY,
        'CLICK_CHECKOUT_URL': CLICK_CHECKOUT_URL,
    },
}
missing_payment_settings = [
    name for name, value in payment_requirements[PAYMENT_PROVIDER].items() if not value
]
if missing_payment_settings:
    raise ImproperlyConfigured(
        f'Missing {PAYMENT_PROVIDER} settings: {", ".join(missing_payment_settings)}.'
    )
if not PAYMENT_FRONTEND_RETURN_URL.startswith('https://'):
    raise ImproperlyConfigured('PAYMENT_FRONTEND_RETURN_URL must use HTTPS in production.')

frontend_url = _production_url(FRONTEND_URL, 'FRONTEND_URL', origin_only=True)
oauth_frontend_callback = _production_url(
    OAUTH_FRONTEND_CALLBACK_URL,
    'OAUTH_FRONTEND_CALLBACK_URL',
    expected_path='/auth/callback',
)
if _origin(frontend_url) != _origin(oauth_frontend_callback):
    raise ImproperlyConfigured(
        'OAUTH_FRONTEND_CALLBACK_URL must use the same origin as FRONTEND_URL.'
    )

for provider_name, provider in OAUTH_PROVIDERS.items():
    supplied = [
        bool(str(provider.get(setting, '')).strip()) for setting in ('client_id', 'client_secret')
    ]
    if any(supplied) and not all(supplied):
        raise ImproperlyConfigured(f'{provider_name.title()} OAuth credentials are incomplete.')
    if not all(supplied):
        continue

    setting_name = f'{provider_name.upper()}_OAUTH_REDIRECT_URI'
    redirect_uri = _production_url(
        provider.get('redirect_uri', ''),
        setting_name,
        expected_path=f'/api/auth/oauth/{provider_name}/callback/',
    )
    if not _hostname_is_allowed(redirect_uri.hostname, ALLOWED_HOSTS):
        raise ImproperlyConfigured(f'{setting_name} hostname must be present in ALLOWED_HOSTS.')

microsoft_tenant = str(OAUTH_PROVIDERS['microsoft'].get('tenant', '')).strip()
if not _valid_microsoft_tenant(microsoft_tenant):
    raise ImproperlyConfigured(
        'MICROSOFT_OAUTH_TENANT must be common, organizations, consumers, or a UUID.'
    )

for setting_name, value in (
    ('OAUTH_ATTEMPT_TTL_SECONDS', OAUTH_ATTEMPT_TTL_SECONDS),
    ('OAUTH_EXCHANGE_TTL_SECONDS', OAUTH_EXCHANGE_TTL_SECONDS),
    ('OAUTH_HTTP_TIMEOUT_SECONDS', OAUTH_HTTP_TIMEOUT_SECONDS),
):
    if value <= 0:
        raise ImproperlyConfigured(f'{setting_name} must be greater than zero.')

# Static files served by WhiteNoise (hashed filenames + gzip/brotli)
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Behind a PaaS reverse proxy (Render / Railway / Fly), trust its TLS header
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env('SECURE_HSTS_SECONDS', default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
