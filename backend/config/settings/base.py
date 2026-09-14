from datetime import timedelta
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
    CORS_ALLOWED_ORIGINS=(list, ['http://localhost:3000', 'http://localhost:3001']),
    CSRF_TRUSTED_ORIGINS=(list, []),
    DATABASE_URL=(str, ''),
    DB_NAME=(str, 'flower_shop_db'),
    DB_USER=(str, 'postgres'),
    DB_PASSWORD=(str, 'postgres'),
    DB_HOST=(str, 'localhost'),
    DB_PORT=(str, '5432'),
    REDIS_URL=(str, 'redis://127.0.0.1:6379/0'),
    PEXELS_API_KEY=(str, ''),
    EMAIL_HOST=(str, ''),
    EMAIL_PORT=(int, 587),
    EMAIL_HOST_USER=(str, ''),
    EMAIL_HOST_PASSWORD=(str, ''),
    EMAIL_USE_TLS=(bool, True),
    DEFAULT_FROM_EMAIL=(str, ''),
    NOTIFICATIONS_ENABLED=(bool, True),
    EMAIL_NOTIFICATIONS_ENABLED=(bool, False),
    TELEGRAM_NOTIFICATIONS_ENABLED=(bool, False),
    TELEGRAM_BOT_TOKEN=(str, ''),
    TELEGRAM_ADMIN_CHAT_ID=(str, ''),
    PAYMENT_PROVIDER=(str, 'test'),
    PAYMENT_TEST_MODE_ENABLED=(bool, False),
    FRONTEND_URL=(str, 'http://localhost:3000'),
    OAUTH_FRONTEND_CALLBACK_URL=(str, 'http://localhost:3000/auth/callback'),
    OAUTH_ATTEMPT_TTL_SECONDS=(int, 600),
    OAUTH_EXCHANGE_TTL_SECONDS=(int, 60),
    OAUTH_HTTP_TIMEOUT_SECONDS=(int, 10),
    GOOGLE_OAUTH_CLIENT_ID=(str, ''),
    GOOGLE_OAUTH_CLIENT_SECRET=(str, ''),
    GOOGLE_OAUTH_REDIRECT_URI=(str, 'http://localhost:8000/api/auth/oauth/google/callback/'),
    GITHUB_OAUTH_CLIENT_ID=(str, ''),
    GITHUB_OAUTH_CLIENT_SECRET=(str, ''),
    GITHUB_OAUTH_REDIRECT_URI=(str, 'http://localhost:8000/api/auth/oauth/github/callback/'),
    MICROSOFT_OAUTH_CLIENT_ID=(str, ''),
    MICROSOFT_OAUTH_CLIENT_SECRET=(str, ''),
    MICROSOFT_OAUTH_REDIRECT_URI=(str, 'http://localhost:8000/api/auth/oauth/microsoft/callback/'),
    MICROSOFT_OAUTH_TENANT=(str, 'common'),
    PAYMENT_FRONTEND_RETURN_URL=(str, 'http://localhost:3000/payment/return'),
    PAYMENT_UZS_PER_PRICE_UNIT=(str, '12650'),
    PAYMENT_HTTP_TIMEOUT_SECONDS=(int, 10),
    STRIPE_SECRET_KEY=(str, ''),
    STRIPE_WEBHOOK_SECRET=(str, ''),
    CLICK_SERVICE_ID=(str, ''),
    CLICK_MERCHANT_ID=(str, ''),
    CLICK_SECRET_KEY=(str, ''),
    CLICK_CHECKOUT_URL=(str, 'https://my.click.uz/services/pay'),
    PAYME_MERCHANT_ID=(str, ''),
    PAYME_LOGIN=(str, 'Paycom'),
    PAYME_SECRET_KEY=(str, ''),
    PAYME_CHECKOUT_URL=(str, 'https://checkout.paycom.uz'),
    PAYME_ALLOWED_IPS=(
        list,
        [
            '185.234.113.1',
            '185.234.113.2',
            '185.234.113.3',
            '185.234.113.4',
            '185.234.113.5',
            '185.234.113.6',
            '185.234.113.7',
            '185.234.113.8',
            '185.234.113.9',
            '185.234.113.10',
            '185.234.113.11',
            '185.234.113.12',
            '185.234.113.13',
            '185.234.113.14',
            '185.234.113.15',
        ],
    ),
    SECURE_HSTS_SECONDS=(int, 0),
)

environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')

INSTALLED_APPS = [
    'daphne',  # must be before django.contrib.staticfiles
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'channels',
    'django_celery_beat',
    'django_celery_results',
    'django_extensions',
    # Local apps
    'apps.users',
    'apps.categories',
    'apps.products',
    'apps.cart',
    'apps.orders',
    'apps.marketplace',
    'apps.contact',
    'apps.reviews',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ── Django Channels ────────────────────────────────────────────────────────────
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [env('REDIS_URL')],
        },
    },
}

# ── Celery ─────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = env('REDIS_URL')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# ── Celery Beat ────────────────────────────────────────────────────────────────
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE = {
    'daily-unread-messages-summary': {
        'task': 'apps.contact.tasks.unread_messages_daily_summary',
        'schedule': 86400,  # every 24 hours
    },
}

# Either a single DATABASE_URL (postgres://user:pass@host:port/name)
# or the individual DB_* variables.
if env('DATABASE_URL'):
    DATABASES = {'default': env.db('DATABASE_URL')}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DB_NAME'),
            'USER': env('DB_USER'),
            'PASSWORD': env('DB_PASSWORD'),
            'HOST': env('DB_HOST'),
            'PORT': env('DB_PORT'),
        }
    }

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'  # English is the default everywhere
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Admin is served in these languages: /admin/ (English, default),
# /ru/admin/ and /uz/admin/ via i18n_patterns in config.urls.
LANGUAGES = [
    ('en', 'English'),
    ('ru', 'Русский'),
    ('uz', 'Oʻzbekcha'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.common.pagination.StandardResultsPagination',
    'PAGE_SIZE': 12,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'auth_login': '5/minute',
        'auth_register': '3/hour',
        'auth_refresh': '10/minute',
        'auth_password': '5/hour',
        'auth_oauth_start': '20/hour',
        'auth_oauth_callback': '30/hour',
        'auth_oauth_exchange': '10/minute',
        'support_message': '10/hour',
        'promo_validate': '20/hour',
        'order_create': '20/hour',
        'test_payment': '20/hour',
        'payment_create': '20/hour',
        'payment_webhook': '240/minute',
        'review_write': '30/hour',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CORS_ALLOWED_ORIGINS = env('CORS_ALLOWED_ORIGINS')
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS')

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_REFERRER_POLICY = 'same-origin'

EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = env('EMAIL_USE_TLS')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
NOTIFICATIONS_ENABLED = env('NOTIFICATIONS_ENABLED')
EMAIL_NOTIFICATIONS_ENABLED = env('EMAIL_NOTIFICATIONS_ENABLED')
TELEGRAM_NOTIFICATIONS_ENABLED = env('TELEGRAM_NOTIFICATIONS_ENABLED')
TELEGRAM_BOT_TOKEN = env('TELEGRAM_BOT_TOKEN')
TELEGRAM_ADMIN_CHAT_ID = env('TELEGRAM_ADMIN_CHAT_ID')
PAYMENT_PROVIDER = env('PAYMENT_PROVIDER').strip().lower()
PAYMENT_TEST_MODE_ENABLED = env('PAYMENT_TEST_MODE_ENABLED')
FRONTEND_URL = env('FRONTEND_URL').rstrip('/')
OAUTH_FRONTEND_CALLBACK_URL = env('OAUTH_FRONTEND_CALLBACK_URL')
OAUTH_ATTEMPT_TTL_SECONDS = env('OAUTH_ATTEMPT_TTL_SECONDS')
OAUTH_EXCHANGE_TTL_SECONDS = env('OAUTH_EXCHANGE_TTL_SECONDS')
OAUTH_HTTP_TIMEOUT_SECONDS = env('OAUTH_HTTP_TIMEOUT_SECONDS')
OAUTH_PROVIDERS = {
    'google': {
        'client_id': env('GOOGLE_OAUTH_CLIENT_ID'),
        'client_secret': env('GOOGLE_OAUTH_CLIENT_SECRET'),
        'redirect_uri': env('GOOGLE_OAUTH_REDIRECT_URI'),
    },
    'github': {
        'client_id': env('GITHUB_OAUTH_CLIENT_ID'),
        'client_secret': env('GITHUB_OAUTH_CLIENT_SECRET'),
        'redirect_uri': env('GITHUB_OAUTH_REDIRECT_URI'),
    },
    'microsoft': {
        'client_id': env('MICROSOFT_OAUTH_CLIENT_ID'),
        'client_secret': env('MICROSOFT_OAUTH_CLIENT_SECRET'),
        'redirect_uri': env('MICROSOFT_OAUTH_REDIRECT_URI'),
        'tenant': env('MICROSOFT_OAUTH_TENANT'),
    },
}
PAYMENT_FRONTEND_RETURN_URL = env('PAYMENT_FRONTEND_RETURN_URL')
PAYMENT_UZS_PER_PRICE_UNIT = env('PAYMENT_UZS_PER_PRICE_UNIT')
PAYMENT_HTTP_TIMEOUT_SECONDS = env('PAYMENT_HTTP_TIMEOUT_SECONDS')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET')
CLICK_SERVICE_ID = env('CLICK_SERVICE_ID')
CLICK_MERCHANT_ID = env('CLICK_MERCHANT_ID')
CLICK_SECRET_KEY = env('CLICK_SECRET_KEY')
CLICK_CHECKOUT_URL = env('CLICK_CHECKOUT_URL')
PAYME_MERCHANT_ID = env('PAYME_MERCHANT_ID')
PAYME_LOGIN = env('PAYME_LOGIN')
PAYME_SECRET_KEY = env('PAYME_SECRET_KEY')
PAYME_CHECKOUT_URL = env('PAYME_CHECKOUT_URL')
PAYME_ALLOWED_IPS = env('PAYME_ALLOWED_IPS')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'apps.orders.notifications': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
