"""API-specific settings with minimal middleware"""
from .base import *
import os

# Debug mode
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

# Minimal middleware for API (no sessions, no CSRF - API uses @csrf_exempt)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'api.middleware.AuditLoggingMiddleware',
]

# Disable unnecessary apps for API
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'api',
]

ROOT_URLCONF = 'trikusec.urls_api'

# SSL configuration (development)
DJANGO_SSL_ENABLED = os.environ.get('DJANGO_SSL_ENABLED', 'True').lower() in ('true', '1', 'yes')
DJANGO_SSL_CERTFILE = os.environ.get('DJANGO_SSL_CERTFILE', '/app/certs/cert.pem')
DJANGO_SSL_KEYFILE = os.environ.get('DJANGO_SSL_KEYFILE', '/app/certs/key.pem')

# Security configuration
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')
