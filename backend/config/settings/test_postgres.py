"""Isolated PostgreSQL tests; never reuse DATABASE_URL or deployment DB_* values."""

import os

from .test import *  # noqa: F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('TEST_POSTGRES_DB', 'flower_shop_tests'),
        'USER': os.environ.get('TEST_POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('TEST_POSTGRES_PASSWORD', ''),
        'HOST': os.environ.get('TEST_POSTGRES_HOST', '127.0.0.1'),
        'PORT': os.environ.get('TEST_POSTGRES_PORT', '5432'),
    }
}
