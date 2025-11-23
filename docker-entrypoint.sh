#!/usr/bin/env bash

set -e

# Set default environment variables if not provided
# These defaults work for both manager and API services

# Django environment
DJANGO_ENV=${DJANGO_ENV:-production}
DJANGO_DEBUG=${DJANGO_DEBUG:-False}
DJANGO_ALLOWED_HOSTS=${DJANGO_ALLOWED_HOSTS:-localhost}

# SSL configuration
DJANGO_SSL_ENABLED=${DJANGO_SSL_ENABLED:-True}
DJANGO_SSL_CERTFILE=${DJANGO_SSL_CERTFILE:-/app/certs/cert.pem}
DJANGO_SSL_KEYFILE=${DJANGO_SSL_KEYFILE:-/app/certs/key.pem}
SSL_CN=${SSL_CN:-localhost}

# Port and WSGI application (service-specific, but set defaults)
PORT=${PORT:-8000}
WSGI_APPLICATION=${WSGI_APPLICATION:-trikusec.wsgi:application}

# TrikuSec URLs (service-specific defaults)
TRIKUSEC_URL=${TRIKUSEC_URL:-https://localhost:8000}
TRIKUSEC_LYNIS_API_URL=${TRIKUSEC_LYNIS_API_URL:-https://localhost:8001}

# Admin user configuration
TRIKUSEC_ADMIN_USERNAME=${TRIKUSEC_ADMIN_USERNAME:-admin}
TRIKUSEC_ADMIN_EMAIL=${TRIKUSEC_ADMIN_EMAIL:-empty@domain.com}
TRIKUSEC_ADMIN_PASSWORD=${TRIKUSEC_ADMIN_PASSWORD:-trikusec}

# CSRF trusted origins
TRIKUSEC_CSRF_TRUSTED_ORIGINS=${TRIKUSEC_CSRF_TRUSTED_ORIGINS:-${TRIKUSEC_URL}}
DJANGO_CSRF_TRUSTED_ORIGINS=${DJANGO_CSRF_TRUSTED_ORIGINS:-${TRIKUSEC_CSRF_TRUSTED_ORIGINS}}

# Export Django environment variables
DJANGO_SUPERUSER_PASSWORD=${TRIKUSEC_ADMIN_PASSWORD}
export DJANGO_SUPERUSER_PASSWORD
export DJANGO_ALLOWED_HOSTS
export DJANGO_CSRF_TRUSTED_ORIGINS
export DJANGO_ENV
export DJANGO_DEBUG
export DJANGO_SSL_ENABLED
export DJANGO_SSL_CERTFILE
export DJANGO_SSL_KEYFILE
export SSL_CN
export PORT
export WSGI_APPLICATION
export TRIKUSEC_URL
export TRIKUSEC_LYNIS_API_URL
export TRIKUSEC_ADMIN_USERNAME
export TRIKUSEC_ADMIN_EMAIL
export TRIKUSEC_ADMIN_PASSWORD

# Generate SSL certificates if enabled
if [ "${DJANGO_SSL_ENABLED}" = "True" ]; then
    /opt/scripts/generate-ssl-cert.sh
fi

# Show database migrations
if [ "${SKIP_MIGRATIONS}" != "True" ]; then
    python manage.py showmigrations
    # Apply database migrations
    python manage.py migrate
fi

# Collect static files for production (skip if SKIP_COLLECTSTATIC is set)
if [ "${SKIP_COLLECTSTATIC}" != "True" ]; then
    python manage.py collectstatic --no-input --clear || true
fi

# Create admin user (ignore errors)
if [ "${SKIP_ADMIN_SETUP}" != "True" ]; then
    python manage.py createsuperuser --noinput --username=${TRIKUSEC_ADMIN_USERNAME} --email=${TRIKUSEC_ADMIN_EMAIL} || true

    # Update admin user password (from environment variable)
    # Allow this to fail without crashing the container
    python manage.py change_admin_password || true

    # Add a license key (use provided env var if available, otherwise generate)
    # Allow this to fail without crashing the container
    if [ -n "${TRIKUSEC_LICENSE_KEY}" ]; then
      python manage.py populate_db_licensekey "${TRIKUSEC_LICENSE_KEY}" || true
    else
      python manage.py populate_db_licensekey || true
    fi
fi

# Start server logic
# If the command is "gunicorn" (or starts with it), we assume we want to start the server using our configured params
# Check if first argument is gunicorn, or if gunicorn appears anywhere in the command
# Note: When CMD is in shell form, Docker wraps it as /bin/sh -c "gunicorn ...", so we check $* for "gunicorn"
if [[ "$1" == "gunicorn"* ]] || [[ "$*" == *"gunicorn"* ]] || [[ "$3" == *"gunicorn"* ]]; then
    if [ "${DJANGO_SSL_ENABLED}" = "True" ]; then
        exec gunicorn \
            --bind 0.0.0.0:${PORT} \
            --certfile ${DJANGO_SSL_CERTFILE} \
            --keyfile ${DJANGO_SSL_KEYFILE} \
            --workers 4 \
            --timeout 120 \
            "${WSGI_APPLICATION}"
    else
        exec gunicorn \
            --bind 0.0.0.0:${PORT} \
            --workers 4 \
            --timeout 120 \
            "${WSGI_APPLICATION}"
    fi
else
    # Execute provided command (e.g. /bin/bash, python manage.py test, etc.)
    exec "$@"
fi
