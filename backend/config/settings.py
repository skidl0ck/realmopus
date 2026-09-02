"""
Django settings for the Real Estate Sales Management System.
"""

from datetime import timedelta
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Off by default -- see core/utils.py:get_client_ip() for why. Only enable
# this once you've confirmed your production reverse proxy strips/overwrites
# any client-supplied X-Forwarded-For header rather than passing it through.
TRUST_PROXY_HEADERS = config('TRUST_PROXY_HEADERS', default=False, cast=bool)

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

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
# Generic SMTP settings — work with Gmail (app password) for local testing, or swap
# to AWS SES's SMTP interface with zero code changes once deployed. Falls back to
# printing emails to the console when EMAIL_HOST isn't set (default local dev).
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@estateos.local')
if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'