"""Frontend-specific settings with full Django features"""
from .base import *
import os

# Debug mode
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

# Full middleware stack
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.middleware.AuditLoggingMiddleware',
]

ROOT_URLCONF = 'trikusec.urls_frontend'

# SSL configuration (development)
DJANGO_SSL_ENABLED = os.environ.get('DJANGO_SSL_ENABLED', 'True').lower() in ('true', '1', 'yes')
DJANGO_SSL_CERTFILE = os.environ.get('DJANGO_SSL_CERTFILE', '/app/certs/cert.pem')
DJANGO_SSL_KEYFILE = os.environ.get('DJANGO_SSL_KEYFILE', '/app/certs/key.pem')

# Security configuration
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')
