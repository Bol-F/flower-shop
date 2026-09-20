"""Public portfolio-demo settings.

This module is intentionally separate from production: it enables only the
explicit test payment provider and serves the repository's synthetic demo
images. It must never be used for a real shop.
"""

from django.core.exceptions import ImproperlyConfigured

from .base import *


if env("FLOWER_DEMO_MODE", default="") != "acknowledged-test-payments":
    raise ImproperlyConfigured(
        "Public demo mode requires FLOWER_DEMO_MODE=acknowledged-test-payments."
    )

DEBUG = False
ALLOWED_HOSTS = [host.strip() for host in env("ALLOWED_HOSTS") if host.strip()]
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOWED_ORIGINS if origin.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in CSRF_TRUSTED_ORIGINS if origin.strip()]

RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", default="").strip()
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("Demo ALLOWED_HOSTS must be explicit.")
if not FRONTEND_URL.startswith("https://"):
    raise ImproperlyConfigured("Demo FRONTEND_URL must use HTTPS.")
if FRONTEND_URL not in CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured("CORS_ALLOWED_ORIGINS must include FRONTEND_URL.")
if not PAYMENT_FRONTEND_RETURN_URL.startswith(f"{FRONTEND_URL}/"):
    raise ImproperlyConfigured("PAYMENT_FRONTEND_RETURN_URL must use FRONTEND_URL.")

# The portfolio demo supports email/password login only. Ignore any stray OAuth
# values so an incomplete dashboard configuration cannot expose broken buttons.
OAUTH_PROVIDERS = {
    provider: {key: "" for key in values}
    for provider, values in OAUTH_PROVIDERS.items()
}

PAYMENT_PROVIDER = "test"
PAYMENT_TEST_MODE_ENABLED = True
NOTIFICATIONS_ENABLED = False
EMAIL_NOTIFICATIONS_ENABLED = False
TELEGRAM_NOTIFICATIONS_ENABLED = False

# A single Render web process is enough for the demo. Real deployments should
# use managed Redis and separate Celery workers instead.
CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# Demo assets are checked into the repository and re-seeded on every cold
# start. This is deliberately not an upload-storage solution.
DEMO_SERVE_MEDIA = True

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
