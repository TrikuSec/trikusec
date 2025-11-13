"""
Development-specific settings for Compleasy.

These settings are used when DJANGO_ENV=development (default).
"""
from .base import *  # noqa

# Development-specific settings
DEBUG = True
ALLOWED_HOSTS = ['*']

# Less strict security for local development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Verbose logging for debugging
LOGGING['root']['level'] = 'DEBUG'

# Email backend for development (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Custom SQLite database filename for development
# Override the default 'compleasy.sqlite3' to keep dev and production databases separate
if not os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'compleasy-dev.sqlite3',
        }
    }

