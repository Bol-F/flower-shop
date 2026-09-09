from django.core.exceptions import ImproperlyConfigured

from .base import *

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
    origin for origin in CORS_ALLOWED_ORIGINS
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

for provider_name, provider in OAUTH_PROVIDERS.items():
    supplied = [provider.get('client_id'), provider.get('client_secret')]
    if any(supplied) and not all(supplied):
        raise ImproperlyConfigured(f'{provider_name.title()} OAuth credentials are incomplete.')
    if all(supplied) and not provider.get('redirect_uri', '').startswith('https://'):
        raise ImproperlyConfigured(
            f'{provider_name.title()} OAuth redirect URI must use HTTPS in production.'
        )

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
