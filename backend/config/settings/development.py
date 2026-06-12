from .base import *

DEBUG = True

ALLOWED_HOSTS = env('ALLOWED_HOSTS')

CORS_ALLOW_ALL_ORIGINS = True

# Local development always uses the local PostgreSQL from the DB_* variables,
# even when .env also carries a production DATABASE_URL for deploys.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='flower_shop_db'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default='postgres'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
    }
}
