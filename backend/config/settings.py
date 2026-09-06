"""
Django settings for the Real Estate Sales Management System.
"""

from datetime import timedelta
from pathlib import Path
from decouple import config, Csv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# DEBUG defaults to False -- secure by default. Local development explicitly
# opts IN via DEBUG=True in .env, rather than production having to remember
# to opt OUT. A deployment that forgets to set this still fails safe.
DEBUG = config('DEBUG', default=False, cast=bool)

# SECRET_KEY signs session cookies, CSRF tokens, and password-reset tokens --
# a predictable default here means anyone can forge them. A convenience
# fallback is fine for local dev (DEBUG=True), but production must supply a
# real one explicitly; startup fails loudly here rather than silently
# running with a well-known, guessable key.
SECRET_KEY = config('SECRET_KEY', default='')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-local-dev-only-1234567890'  # nosec: only ever reached with DEBUG=True
    else:
        raise ImproperlyConfigured(
            "SECRET_KEY environment variable is not set. Generate one with:\n"
            "  python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\"\n"
            "and set it in your production environment before starting the server."
        )

# Same fail-loud principle: the default ('localhost,127.0.0.1') would make a
# real deployment completely unreachable (Django rejects any request whose
# Host header isn't in this list) -- but a *misconfigured* one (e.g. still
# pointing at localhost) would fail the same way, silently, with no hint why.
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())
if not DEBUG and ALLOWED_HOSTS == ['localhost', '127.0.0.1']:
    raise ImproperlyConfigured(
        "ALLOWED_HOSTS is still at its localhost-only default with DEBUG=False. "
        "Set the ALLOWED_HOSTS environment variable to your actual production domain(s)."
    )

# Off by default -- see core/utils.py:get_client_ip() for why. Only enable
# this once you've confirmed your production reverse proxy strips/overwrites
# any client-supplied X-Forwarded-For header rather than passing it through.
TRUST_PROXY_HEADERS = config('TRUST_PROXY_HEADERS', default=False, cast=bool)

# HTTPS/cookie/browser hardening -- meaningless (and actively annoying) in
# local HTTP development, so these only apply once DEBUG=False. Covers the
# gaps a security audit found: no HSTS, no Secure flag on cookies, no
# forced HTTPS redirect, no clickjacking protection were configured at all.
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # Only trust X-Forwarded-Proto from the reverse proxy if it's been
    # explicitly confirmed safe to -- same reasoning as TRUST_PROXY_HEADERS
    # above; a proxy that doesn't strip/overwrite this header would let a
    # client spoof "I'm on HTTPS" and defeat SECURE_SSL_REDIRECT.
    if TRUST_PROXY_HEADERS:
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    # 'django.contrib.admin' deliberately excluded — it gives raw, unrestricted
    # CRUD access to every registered model (User, Contract, Payment, ...),
    # completely bypassing the RBAC checks and audit logging admin_panel
    # carefully implements throughout. The app-level admin.py files (e.g.
    # sales/admin.py) are now inert without this — kept as-is rather than
    # deleted, since removing this one line already fully disables them.
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
    'django.contrib.humanize',

    # Local apps
    'accounts',
    'properties',
    'sales',
    'payments',
    'expenses',
    'core',
    'admin_panel',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
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
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'admin_panel.context_processors.notifications',
                'admin_panel.context_processors.role_permissions',
                'admin_panel.context_processors.nav_state',
                'admin_panel.context_processors.currency',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database: SQLite for local dev; swap to Postgres (RDS free tier) via env vars in production.
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=BASE_DIR / 'db.sqlite3'),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
    }
}

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Media storage — local disk by default (fine for dev), S3 in production.
#
# A security audit found that contract/receipt/SOA PDFs are saved as plain
# FileFields with sequential, predictable filenames (contract_GV-2026-0001.pdf,
# from a straightforward incrementing counter). The application's own API
# already scopes who can see a given Contract/Receipt correctly (verified
# directly — a second client's token gets 404, not 200, on another client's
# records) — but the *file URL* itself, once returned to a legitimate user's
# browser, was just a plain, permanent link with no auth check of its own.
# With a predictable filename, that's a real gap regardless of how careful
# the API-level scoping is.
#
# S3Boto3Storage with AWS_DEFAULT_ACL='private' and AWS_QUERYSTRING_AUTH=True
# (both defaults for private buckets) closes this: every FileField.url becomes
# a presigned, time-limited, signed URL minted by the backend on demand —
# guessing a filename is no longer enough on its own, since a valid signature
# can only come from a request that already passed the app's own permission
# check to see the object in the first place.
#
# Gated behind AWS_STORAGE_BUCKET_NAME so local dev (no S3 env vars set)
# keeps using local disk storage unchanged -- only production, once the
# bucket is actually provisioned, switches over.
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default='')

if AWS_STORAGE_BUCKET_NAME:
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_DEFAULT_ACL = 'private'
    AWS_QUERYSTRING_AUTH = True  # generate presigned, expiring URLs -- not permanent public links
    AWS_QUERYSTRING_EXPIRE = config('AWS_QUERYSTRING_EXPIRE', default=3600, cast=int)  # 1 hour
    AWS_S3_FILE_OVERWRITE = False  # never silently clobber an existing upload with the same name

    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3.S3Storage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# Explicit logging config -- a security audit found the project had none at
# all, relying entirely on Django's implicit default (WARNING+ to console
# for the 'django' logger only). Two gaps that left: nothing guaranteed
# these logs were actually captured/persisted by the deployment platform,
# and application code had no dedicated logger of its own for
# security-relevant events (failed logins, deactivated-account login
# attempts -- see accounts/auth.py's LoginRateThrottle and
# ClientAwareTokenObtainPairSerializer). Everything still goes to
# console/stdout, which every mainstream PaaS captures as platform logs --
# this isn't a shipped alerting pipeline, just making sure the events exist
# and are structured enough to find, rather than not existing at all.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        # Dedicated logger for auth/security events specifically, so these
        # are easy to grep/filter for separately from routine app logs.
        'security': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# CORS - allow the Next.js frontend
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS', default='http://localhost:3000', cast=Csv()
)

# Payment gateways (set real keys via environment variables / .env, never commit them)
PAYPAL_CLIENT_ID = config('PAYPAL_CLIENT_ID', default='')
PAYPAL_CLIENT_SECRET = config('PAYPAL_CLIENT_SECRET', default='')
PAYPAL_MODE = config('PAYPAL_MODE', default='sandbox')  # sandbox | live

PAYMONGO_SECRET_KEY = config('PAYMONGO_SECRET_KEY', default='')
PAYMONGO_PUBLIC_KEY = config('PAYMONGO_PUBLIC_KEY', default='')
# Only needed if/when a webhook endpoint is registered in the PayMongo
# dashboard — the primary payment-confirmation path (client returns from
# checkout -> backend polls the Payment Intent directly) doesn't need this.
PAYMONGO_WEBHOOK_SECRET = config('PAYMONGO_WEBHOOK_SECRET', default='')

# AI chatbot — using Google's Gemini API for its free tier (a deliberate cost
# decision — see the project notes). Set a real key via environment variable
# / .env, never commit it. Get one free, no credit card required, at
# https://aistudio.google.com/apikey
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
GEMINI_CHAT_MODEL = config('GEMINI_CHAT_MODEL', default='gemini-3.6-flash')

# Celery — background/periodic jobs (payment reminder escalation, late
# penalties, stale reservation cleanup). Requires Redis running, plus
# separate `celery worker` and `celery beat` processes — see .env.example.
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_TIMEZONE = config('CELERY_TIMEZONE', default='Asia/Manila')
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=False, cast=bool)

# Shared cache, backing DRF's rate-throttling (accounts/auth.py's
# LoginRateThrottle). Without this, Django falls back to LocMemCache --
# in-process only, so with multiple gunicorn workers each one would track
# its own separate attempt count, silently multiplying the effective rate
# limit by the worker count. Redis DB 1, not 0, so cache keys never collide
# with Celery's broker/result data on DB 0.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('CACHE_URL', default='redis://localhost:6379/1'),
    }
}

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
# Generic SMTP settings — work with Gmail (app password) for local testing, or swap
# to AWS SES's SMTP interface with zero code changes once deployed. Falls back to
# printing emails to the console when EMAIL_HOST isn't set (default local dev).
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@realmopus.local')
if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'