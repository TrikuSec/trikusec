<!-- 064e5101-467f-4723-9223-069ed01b076a a768d06b-8317-44b9-aea0-ed08cffdacdc -->
# Phase 1: Critical Security Fixes Implementation Plan

## Overview

This plan addresses all 10 critical security issues identified in Phase 1. Implementation will be done incrementally with testing at each step to ensure the critical Lynis API endpoints remain functional.

## Prerequisites

- All changes will be tested using: `docker compose -f docker-compose.dev.yml --profile test run --rm test`
- Critical Lynis endpoints (`/api/lynis/upload/`, `/api/lynis/license/`) must remain functional
- Tests must pass after each major change

## Implementation Order

### 1. Fix Open Redirect Vulnerability (Issue #1)

**Files**: `src/frontend/views.py`

**Vulnerable lines**: 110, 303, 316

**Changes**:

- Replace `request.META.get('HTTP_REFERER')` with `redirect('device_list')` or other safe defaults
- Add a helper function `safe_redirect()` that validates URLs against a whitelist
- Update three functions: `device_update()`, `rule_update()`, `rule_create()`

**Implementation**:

```python
# Add at top of views.py
from django.urls import reverse
from urllib.parse import urlparse

def safe_redirect(request, fallback_url='device_list'):
    """Safely redirect to referer or fallback URL"""
    referer = request.META.get('HTTP_REFERER')
    if referer:
        parsed = urlparse(referer)
        # Only allow same-origin redirects
        if parsed.netloc == request.get_host():
            return redirect(referer)
    return redirect(fallback_url)
```

Replace unsafe redirects:

- Line 110: `return safe_redirect(request, 'device_detail', device_id=device_id)`
- Line 303: `return safe_redirect(request, 'rule_list')`
- Line 316: `return safe_redirect(request, 'rule_list')`

### 2. Remove Weak Default Credentials (Issue #2)

**Files**: `docker-compose.yml`, `.env.example` (create)

**Current issue**: Line 12 has hardcoded `COMPLEASY_ADMIN_PASSWORD=compleasy`

**Changes**:

1. Create `.env.example`:
```bash
# Django Security
SECRET_KEY=GENERATE_THIS_SECRET_KEY_AS_EXPLAINED_ABOVE
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=*

# Admin Credentials (CHANGE THESE IN PRODUCTION!)
COMPLEASY_ADMIN_USERNAME=admin
COMPLEASY_ADMIN_PASSWORD=compleasy

# Application Settings
COMPLEASY_URL=https://localhost:3000

# Nginx Certificate
NGINX_CERT_CN=localhost

# Database (SQLite is default, see docs for PostgreSQL)
# DATABASE_URL=postgresql://user:password@localhost:5432/compleasy

# Logging
DJANGO_LOG_LEVEL=INFO

# Rate Limiting (requests per hour)
RATELIMIT_ENABLE=True
```

2. Update `docker-compose.yml` line 12:
```yaml
- COMPLEASY_ADMIN_PASSWORD=${COMPLEASY_ADMIN_PASSWORD:-compleasy}
```

3. Add comment warning in docker-compose.yml above credentials:
```yaml
# SECURITY WARNING: Change admin credentials in production!
# Set COMPLEASY_ADMIN_PASSWORD in .env file
```


### 3. Fix Overly Permissive ALLOWED_HOSTS (Issue #3)

**Files**: `src/compleasy/settings.py`

**Current issue**: Lines 51-54 default to `['*']`

**Changes**:

```python
# Line 51-54, replace with:
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

# Add warning comment
# SECURITY WARNING: In production, set DJANGO_ALLOWED_HOSTS to your actual domain(s)
# Example: DJANGO_ALLOWED_HOSTS=example.com,www.example.com
# Default '*' is ONLY for development
```

Update `.env.example`:

```bash
# For production, specify your actual hosts (comma-separated)
# DJANGO_ALLOWED_HOSTS=yourserver.com,www.yourserver.com
DJANGO_ALLOWED_HOSTS=*
```

### 4. Fix DEBUG Logging in Production (Issue #4)

**Files**: `src/compleasy/settings.py`

**Current issue**: Lines 17-29 hardcode DEBUG level

**Changes**:

```python
# Lines 17-29, replace with:
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
        'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
    },
}

# Add comment:
# SECURITY NOTE: Log level defaults to INFO for production.
# Set DJANGO_LOG_LEVEL=DEBUG only in development environments
```

### 5. Add Missing Security Headers (Issue #5)

**Files**: `src/compleasy/settings.py`

**Location**: After line 183 (end of file)

**Changes**:

```python
# Security Headers
# These settings improve security in production deployments
# See: https://docs.djangoproject.com/en/4.2/topics/security/

# HTTPS and HSTS (HTTP Strict Transport Security)
# Enable these when deploying with HTTPS
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() in ('true', '1', 'yes')
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False').lower() in ('true', '1', 'yes')
SECURE_HSTS_PRELOAD = os.environ.get('SECURE_HSTS_PRELOAD', 'False').lower() in ('true', '1', 'yes')

# Content Security and MIME type sniffing protection
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'  # Already have ClickjackingMiddleware, this reinforces it

# Session Security
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'False').lower() in ('true', '1', 'yes')
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
```

Update `.env.example`:

```bash
# Security Headers (enable in production with HTTPS)
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

### 6. Add Input Validation in Views (Issue #6)

**Files**: `src/frontend/views.py`

**Vulnerable functions**: `enroll_sh()` (lines 140-152), `download_lynis_custom_profile()` (lines 154-180)

**Changes**:

1. Add validation helper at top of file:
```python
import re

def validate_license_key(licensekey):
    """Validate license key format and existence"""
    if not licensekey:
        return False, 'No license key provided'
    
    # Basic format validation (alphanumeric, hyphens, underscores)
    if not re.match(r'^[a-zA-Z0-9_-]+$', licensekey):
        return False, 'Invalid license key format'
    
    # Length check
    if len(licensekey) > 255:
        return False, 'License key too long'
    
    # Check if exists in database
    if not LicenseKey.objects.filter(licensekey=licensekey).exists():
        return False, 'Invalid license key'
    
    return True, None
```

2. Update `enroll_sh()` (lines 140-152):
```python
def enroll_sh(request):
    """Enroll view: generate enroll bash script to install the agent on a new device"""
    licensekey = request.GET.get('licensekey', '').strip()
    
    valid, error = validate_license_key(licensekey)
    if not valid:
        return HttpResponse(error, status=400 if 'format' in error or 'provided' in error else 401)
    
    compleasy_url = request.build_absolute_uri('/').rstrip('/')
    return render(request, 'enroll.html', {'compleasy_url': compleasy_url, 'licensekey': licensekey})
```

3. Update `download_lynis_custom_profile()` (lines 154-180):
```python
def download_lynis_custom_profile(request):
    """Generate a custom Lynis profile with the provided license key"""
    lynis_version = request.GET.get('lynis_version', '2.7.5').strip()
    licensekey = request.GET.get('licensekey', '').strip()
    
    # Validate license key
    valid, error = validate_license_key(licensekey)
    if not valid:
        return HttpResponse(error, status=400 if 'format' in error or 'provided' in error else 401)
    
    # Validate lynis_version format (x.y.z)
    if not re.match(r'^\d+\.\d+\.\d+$', lynis_version):
        return HttpResponse('Invalid Lynis version format', status=400)
    
    base_url = request.build_absolute_uri('/').rstrip('/')
    server_address_without_proto = base_url.split('://', 1)[1]
    compleasy_upload_server = f'{server_address_without_proto}/api/lynis'
    
    return render(request, 'lynis_custom_profile.html',
                  {
                      'compleasy_upload_server': compleasy_upload_server,
                      'license_key': licensekey,
                      'lynis_version': lynis_version
                  },
                  content_type='text/plain')
```


### 7. Implement Rate Limiting (Issue #7)

**Files**: `src/requirements.txt`, `src/requirements-dev.txt`, `src/compleasy/settings.py`, `src/api/views.py`

**Changes**:

1. Add django-ratelimit to `src/requirements.txt`:
```
django-ratelimit>=4.1.0
```

2. Update `src/compleasy/settings.py` - add to INSTALLED_APPS (after line 69):
```python
# Line ~70, no need to add to INSTALLED_APPS, just configure
# Rate limiting configuration
RATELIMIT_ENABLE = os.environ.get('RATELIMIT_ENABLE', 'True').lower() in ('true', '1', 'yes')
RATELIMIT_USE_CACHE = 'default'
```

3. Add cache backend to settings.py (after DATABASES section, around line 115):
```python
# Cache configuration for rate limiting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ratelimit-cache',
    }
}
```

4. Update `src/api/views.py` - add rate limiting decorators:
```python
# Add import at top
from django_ratelimit.decorators import ratelimit

# Update upload_report (line 11)
@csrf_exempt
@ratelimit(key='ip', rate='100/h', method='POST')
def upload_report(request):
    # ... existing code

# Update check_license (line 81)
@csrf_exempt
@ratelimit(key='ip', rate='50/h', method='POST')
def check_license(request):
    # ... existing code
```


### 8. Update Python Version (Issue #8)

**Files**: `Dockerfile`, `Dockerfile.test`

**Current issue**: Line 1 uses `python:3.8-slim` (EOL October 2024)

**Changes**:

Both files need updating from `FROM python:3.8-slim` to `FROM python:3.12-slim`

Verification needed:

- Test all functionality after upgrade
- Ensure dependencies are compatible with Python 3.12

### 9. Pin Dependencies (Issue #9)

**Files**: `src/requirements.txt`, `src/requirements-dev.txt`

**Current issue**: Using ranges like `>=4.2,<5.0`

**Changes**:

1. Create a script to generate pinned versions (for documentation):
```bash
# Run in test container to get exact versions
docker compose -f docker-compose.dev.yml --profile test run --rm test pip freeze > requirements.lock
```

2. Update `src/requirements.txt`:
```
# Production dependencies - pinned versions
# Last updated: 2025-11-11
# To update: pip install -r requirements.txt --upgrade, then pip freeze

Django==4.2.16
pyyaml==6.0.2
pyparsing==3.1.4
django-ratelimit==4.1.0
```

3. Update `src/requirements-dev.txt`:
```
# Development dependencies - pinned versions
pytest==8.3.3
pytest-django==4.9.0
pytest-cov==5.0.0
coverage==7.6.4
factory-boy==3.3.1
requests==2.32.3
```

4. Add upgrade documentation to README section.

### 10. Add PostgreSQL Support (Issue #10)

**Files**: `src/compleasy/settings.py`, `src/requirements.txt`, `.env.example`

**Current issue**: Lines 109-114 only support SQLite

**Changes**:

1. Add psycopg2 to `src/requirements.txt`:
```
psycopg2-binary==2.9.10
```

2. Update `src/compleasy/settings.py` (lines 109-114):
```python
# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Support both SQLite (development) and PostgreSQL (production)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # PostgreSQL configuration from DATABASE_URL
    # Format: postgresql://user:password@host:port/dbname
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
    if match:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': match.group(5),
                'USER': match.group(1),
                'PASSWORD': match.group(2),
                'HOST': match.group(3),
                'PORT': match.group(4),
                'CONN_MAX_AGE': 600,
                'OPTIONS': {
                    'connect_timeout': 10,
                }
            }
        }
    else:
        raise ValueError('Invalid DATABASE_URL format. Expected: postgresql://user:password@host:port/dbname')
else:
    # SQLite configuration (default for development)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'compleasy.sqlite3',
        }
    }
```

3. Update `.env.example`:
```bash
# Database Configuration
# For development (default): SQLite
# For production: PostgreSQL
# DATABASE_URL=postgresql://compleasy:your-secure-password@localhost:5432/compleasy
```

4. Add PostgreSQL documentation to README with migration instructions.

## Testing Strategy

After each change:

1. Run unit tests: `docker compose -f docker-compose.dev.yml --profile test run --rm test`
2. Verify Lynis endpoints work: test upload and license check
3. Check no new linter errors
4. Commit changes incrementally

## Rollback Plan

Each issue is independent and can be reverted individually if tests fail:

- Git commit after each successful fix
- Tag working states
- Keep `.env.example` backward compatible

## Documentation Updates

Update README.md to document:

- New environment variables in `.env.example`
- Security best practices for production
- PostgreSQL setup instructions
- Dependency update process
- Rate limiting configuration

## Success Criteria

- All tests pass
- Lynis API endpoints remain functional
- No open redirect vulnerabilities
- No hardcoded credentials in version control
- Security headers present in responses
- Rate limiting active on API endpoints
- Python 3.12 compatibility verified
- All dependencies pinned
- PostgreSQL support available

### To-dos

- [x] Fix open redirect vulnerability in device_update, rule_update, and rule_create views
- [ ] Create .env.example and remove hardcoded credentials from docker-compose.yml
- [x] Make ALLOWED_HOSTS configurable via environment variable
- [x] Make logging level configurable via DJANGO_LOG_LEVEL environment variable
- [x] Add security headers (HSTS, Content-Type-Options, cookie security) to settings.py
- [x] Add license key validation in enroll_sh and download_lynis_custom_profile views
- [x] Install django-ratelimit and add rate limiting to upload_report and check_license endpoints
- [x] Update Dockerfile and Dockerfile.test from Python 3.8 to Python 3.12
- [x] Pin exact versions in requirements.txt and requirements-dev.txt
- [x] Add PostgreSQL support with DATABASE_URL configuration in settings.py
- [x] Update README.md with new environment variables and security best practices
- [x] Run complete test suite and verify Lynis integration still works