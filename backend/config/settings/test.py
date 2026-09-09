import os

os.environ.setdefault('SECRET_KEY', 'test-only-secret-key-that-is-at-least-32-bytes')

from .base import *  # noqa: E402,F403


DEBUG = True
PAYMENT_TEST_MODE_ENABLED = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
CELERY_TASK_ALWAYS_EAGER = True
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    scope: '10000/minute'
    for scope in REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']
}
