#!/usr/bin/env bash

set -e

# Domain-based configuration (simplifies setup)
# If TRIKUSEC_DOMAIN is set, derive other variables from it
if [ -n "${TRIKUSEC_DOMAIN}" ]; then
    # Derive URLs from domain if not explicitly set
    TRIKUSEC_URL=${TRIKUSEC_URL:-https://${TRIKUSEC_DOMAIN}:8000}
    TRIKUSEC_LYNIS_API_URL=${TRIKUSEC_LYNIS_API_URL:-https://${TRIKUSEC_DOMAIN}:8001}
    
    # Set allowed hosts to include both localhost and the domain
    if [ -z "${DJANGO_ALLOWED_HOSTS}" ]; then
        DJANGO_ALLOWED_HOSTS="localhost,${TRIKUSEC_DOMAIN}"
    fi
    
    # Set SSL certificate CN
    SSL_CN=${SSL_CN:-${TRIKUSEC_DOMAIN}}
fi

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

# Database Directory
# Default to /app/data for shared volume usage in Docker
export TRIKUSEC_DB_DIR=${TRIKUSEC_DB_DIR:-/app/data}

# Service Detection
# Check if we are running the API service based on settings module
IS_API_SERVICE=false
if [[ "${DJANGO_SETTINGS_MODULE}" == *"api"* ]]; then
    IS_API_SERVICE=true
    # For API service in production, skip collectstatic by default if not specified
    if [ -z "${SKIP_COLLECTSTATIC}" ]; then
        export SKIP_COLLECTSTATIC=True
    fi
fi

# Admin user configuration
TRIKUSEC_ADMIN_USERNAME=${TRIKUSEC_ADMIN_USERNAME:-admin}
TRIKUSEC_ADMIN_EMAIL=${TRIKUSEC_ADMIN_EMAIL:-empty@domain.com}
# Note: TRIKUSEC_ADMIN_PASSWORD has no default here
# This allows us to detect if it was explicitly set by the user

# CSRF trusted origins
TRIKUSEC_CSRF_TRUSTED_ORIGINS=${TRIKUSEC_CSRF_TRUSTED_ORIGINS:-${TRIKUSEC_URL}}
DJANGO_CSRF_TRUSTED_ORIGINS=${DJANGO_CSRF_TRUSTED_ORIGINS:-${TRIKUSEC_CSRF_TRUSTED_ORIGINS}}

# Export Django environment variables
# Set DJANGO_SUPERUSER_PASSWORD for createsuperuser command
# Use provided password or default to 'trikusec' for initial user creation
DJANGO_SUPERUSER_PASSWORD=${TRIKUSEC_ADMIN_PASSWORD:-trikusec}
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
# Note: TRIKUSEC_ADMIN_PASSWORD is exported conditionally below when needed

# Generate SSL certificates if enabled
if [ "${DJANGO_SSL_ENABLED}" = "True" ]; then
    /opt/scripts/generate-ssl-cert.sh
fi

# Show database migrations
if [ "${SKIP_MIGRATIONS}" != "True" ]; then
    # Fix database file permissions in development mode BEFORE accessing it
    # This allows multiple containers to access the same SQLite database file
    if [ "${DJANGO_ENV}" = "development" ]; then
        DB_FILE="/app/data/trikusec-dev.sqlite3"
        
        # Ensure the database directory exists and is writable
        mkdir -p /app/data 2>/dev/null || true
        chmod 777 /app/data 2>/dev/null || true
        
        # If database file exists, fix its permissions
        if [ -f "${DB_FILE}" ]; then
            chmod 666 "${DB_FILE}" 2>/dev/null || true
            echo "Fixed existing database file permissions for development mode"
        fi
    fi
    
    python manage.py showmigrations
    # Apply database migrations
    python manage.py migrate
    
    # Fix database file permissions again after creation (in case it was just created)
    if [ "${DJANGO_ENV}" = "development" ]; then
        DB_FILE="/app/data/trikusec-dev.sqlite3"
        if [ -f "${DB_FILE}" ]; then
            chmod 666 "${DB_FILE}" 2>/dev/null || true
            # Also fix any journal files
            chmod 666 "${DB_FILE}-shm" 2>/dev/null || true
            chmod 666 "${DB_FILE}-wal" 2>/dev/null || true
            echo "Fixed database file permissions after migrations"
        fi
    fi
else
    # If we skip migrations (e.g. API service), we must wait for the database to be ready
    # This prevents race conditions when starting API and Manager simultaneously
    echo "Skipping migrations. Waiting for database to be ready..."
    
    until python -c "
import sys
import django
from django.db import connections
from django.db.utils import OperationalError
django.setup()
try:
    c = connections['default'].cursor()
    # Check if auth_user table exists (created by migrations)
    c.execute('SELECT 1 FROM auth_user LIMIT 1')
except OperationalError:
    sys.exit(1)
except Exception:
    sys.exit(1)
sys.exit(0)
"; do
        echo "Database not ready yet, waiting..."
        sleep 2
    done
    echo "Database is ready."
fi

# Collect static files for production (skip if SKIP_COLLECTSTATIC is set)
if [ "${SKIP_COLLECTSTATIC}" != "True" ]; then
    python manage.py collectstatic --no-input --clear || true
fi

# Create admin user (idempotent - only creates if doesn't exist)
# Capture output to detect if user already exists
CREATE_USER_OUTPUT=$(python manage.py createsuperuser --noinput --username=${TRIKUSEC_ADMIN_USERNAME} --email=${TRIKUSEC_ADMIN_EMAIL} 2>&1) || true
echo "$CREATE_USER_OUTPUT"

# Check if user already existed
if echo "$CREATE_USER_OUTPUT" | grep -q "already exists"; then
    USER_EXISTS=true
else
    USER_EXISTS=false
fi

# Password management logic:
# - If user was just created: set password (use provided or default 'trikusec')
# - If user already exists AND TRIKUSEC_ADMIN_PASSWORD is set: update password
# - If user already exists AND TRIKUSEC_ADMIN_PASSWORD is NOT set: keep existing password
if [ "$USER_EXISTS" = "false" ]; then
    # New user - set initial password
    echo "Setting initial admin password..."
    export TRIKUSEC_ADMIN_PASSWORD="${TRIKUSEC_ADMIN_PASSWORD:-trikusec}"
    python manage.py change_admin_password || true
elif [ -n "${TRIKUSEC_ADMIN_PASSWORD+x}" ]; then
    # Existing user - only update if TRIKUSEC_ADMIN_PASSWORD was explicitly set
    echo "TRIKUSEC_ADMIN_PASSWORD is set, updating admin password..."
    python manage.py change_admin_password || true
else
    echo "Admin user already exists and TRIKUSEC_ADMIN_PASSWORD not set, keeping existing password"
fi

# Add a license key (use provided env var if available, otherwise generate)
# Allow this to fail without crashing the container
if [ -n "${TRIKUSEC_LICENSE_KEY}" ]; then
  python manage.py populate_db_licensekey "${TRIKUSEC_LICENSE_KEY}" || true
else
  python manage.py populate_db_licensekey || true
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
