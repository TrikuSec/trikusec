# Agent Guidelines for TrikuSec

This document contains critical guidelines and hints for AI agents working on the TrikuSec project.

## Critical Commands

### Docker Compose Syntax

**ALWAYS use `docker compose` (with a space), NEVER `docker-compose` (with a hyphen).**

- ✅ Correct: `docker compose up`
- ✅ Correct: `docker compose -f docker-compose.dev.yml run --rm test`
- ❌ Wrong: `docker-compose up`
- ❌ Wrong: `docker-compose -f docker-compose.dev.yml run --rm test`

This is the modern Docker Compose V2 syntax. All commands, documentation, and scripts should use this format.

## Testing Infrastructure

### All Tests Run in Docker

**Never install dependencies locally. All tests must run inside Docker containers.**

- Tests are run using: `docker compose -f docker-compose.dev.yml --profile test run --rm test`
- The test container automatically runs migrations before executing tests
- Test container has all dependencies pre-installed (pytest, pytest-django, coverage, etc.)
- Source code is mounted as a volume for live testing

### Test Commands

```bash
# Run all unit tests
docker compose -f docker-compose.dev.yml --profile test run --rm test

# Run specific test file
docker compose -f docker-compose.dev.yml --profile test run --rm test pytest api/tests.py -v

# Run with coverage
docker compose -f docker-compose.dev.yml --profile test run --rm test pytest --cov=api --cov=frontend --cov-report=html --cov-report=term-missing

# Run specific test
docker compose -f docker-compose.dev.yml --profile test run --rm test pytest api/tests.py::TestUploadReport::test_upload_report_valid_license_new_device -v

# Access test container shell
docker compose -f docker-compose.dev.yml --profile test run --rm test /bin/bash
```

## Split Architecture

TrikuSec uses a split architecture with two separate Django processes to improve security:

1. **trikusec-manager** (Port 8000):
   - Handles Admin UI, frontend views, and user authentication
   - Includes full middleware stack (sessions, CSRF, admin)
   - Uses `Dockerfile.frontend` and `src/trikusec/urls_frontend.py`

2. **trikusec-lynis-api** (Port 8001):
   - Handles Lynis API endpoints only (enrollment, report uploads)
   - No admin UI, no session middleware, no CSRF middleware (uses `@csrf_exempt`)
   - Uses `Dockerfile.api` and `src/trikusec/urls_api.py`
   - Minimal attack surface

Both services share the same database and code volume in development.

## Critical API Endpoints (DO NOT BREAK)

The following Lynis API endpoints **MUST** remain unchanged to maintain compatibility:

### `/api/lynis/upload/`
- **Location**: `src/api/views.py` - `upload_report()` function
- **URL Pattern**: `/api/lynis/upload/`
- **Method**: POST only
- **Decorator**: `@csrf_exempt` (required for external API)
- **Request Format**: Form data with `licensekey`, `hostid`, `hostid2`, `data`
- **Response Format**: `'OK'` (200) or error messages
- **Critical**: Used by Lynis clients to upload audit reports

### `/api/lynis/license/`
- **Location**: `src/api/views.py` - `check_license()` function
- **URL Pattern**: `/api/lynis/license/`
- **Method**: POST only
- **Decorator**: `@csrf_exempt` (required for external API)
- **Request Format**: Form data with `licensekey`, `collector_version`
- **Response Format**: `'Response 100'` (200) for valid, `'Response 500'` (401) for invalid
- **Critical**: Used by Lynis clients to validate license keys

**When modifying these endpoints:**
- Never change the URL patterns
- Never remove `@csrf_exempt` decorator
- Never change request/response format
- Always test with actual Lynis client before committing changes

## Project Structure

### Key Directories

- `src/` - Main application source code
  - `src/api/` - API application (models, views, forms, tests)
  - `src/frontend/` - Frontend application (views, templates, static files)
  - `src/trikusec/` - Django project settings (now split into frontend/api)
  - `src/utils/` - Shared utilities
  - `src/conftest.py` - Pytest fixtures
- `scripts/` - Helper scripts (e.g. SSL generation)
- `lynis/` - Lynis integration files
- `trikusec-lynis-plugin/` - Lynis custom plugin
- `.github/workflows/` - CI/CD workflows

### Key Files

- `docker-compose.yml` - Production Docker Compose configuration (2 services)
- `docker-compose.dev.yml` - Development Docker Compose configuration
- `Dockerfile.frontend` - Frontend/Manager Docker image
- `Dockerfile.api` - API Docker image
- `Dockerfile.test` - Test Docker image
- `pytest.ini` - Pytest configuration
- `src/requirements-frontend.txt` - Frontend dependencies
- `src/requirements-api.txt` - API dependencies

## Security Considerations

### Critical Security Issues (from plan)

1. **Open Redirect Vulnerability** - `src/frontend/views.py` lines 109, 300, 313
   - Never use `request.META.get('HTTP_REFERER')` directly in redirects
   - Always validate referer against safe URLs

2. **Weak Default Credentials** - `docker-compose.yml` line 12
   - Never hardcode passwords in version control
   - Use environment variables with `.env.example` for defaults

3. **ALLOWED_HOSTS** - `src/trikusec/settings.py` line 54
   - Never use `ALLOWED_HOSTS = ['*']` in production
   - Require explicit configuration via environment variable

4. **DEBUG Logging** - `src/trikusec/settings.py` lines 17-29
   - Root logger set to `DEBUG` exposes sensitive information
   - Make logging level configurable via environment variable

5. **Missing Security Headers** - Add HSTS, X-Content-Type-Options, CSP headers

6. **Unvalidated Input** - `src/frontend/views.py` lines 141-151, 163-177
   - Always validate license keys from URL parameters

7. **No Rate Limiting** - API endpoints need rate limiting protection

## Environment Variables

### Required

- `SECRET_KEY` - Django secret key (must be set, no default)

### Recommended (Simplified Configuration)

- `TRIKUSEC_DOMAIN` - Domain name (automatically configures URLs, allowed hosts, and SSL certificates)
  - Example: `localhost` for local development
  - Example: `yourdomain.com` for production
  - Automatically derives:
    - `TRIKUSEC_URL=https://${TRIKUSEC_DOMAIN}:8000`
    - `TRIKUSEC_LYNIS_API_URL=https://${TRIKUSEC_DOMAIN}:8001`
    - `DJANGO_ALLOWED_HOSTS=localhost,${TRIKUSEC_DOMAIN}`
    - `NGINX_CERT_CN=${TRIKUSEC_DOMAIN}`

### Optional (Advanced Override)

- `TRIKUSEC_URL` - TrikuSec admin UI server URL (default: `https://localhost:8000`, or derived from `TRIKUSEC_DOMAIN`)
- `TRIKUSEC_LYNIS_API_URL` - TrikuSec Lynis API server URL (default: `https://localhost:8001`, or derived from `TRIKUSEC_DOMAIN`)
- `DJANGO_ALLOWED_HOSTS` - Allowed hosts (default: `localhost`, or derived from `TRIKUSEC_DOMAIN`)
- `DJANGO_DEBUG` - Debug mode (default: `False` for security)
- `TRIKUSEC_ADMIN_USERNAME` - Admin username (default: `admin`)
- `TRIKUSEC_ADMIN_PASSWORD` - Admin password (default: `trikusec`)
- `DJANGO_SSL_ENABLED` - Enable internal SSL (default: `True` for dev/standalone)

## Common Tasks

### Running Tests

```bash
# Unit tests only
docker compose -f docker-compose.dev.yml --profile test run --rm test pytest -m "not integration" -v

# Integration tests only
docker compose -f docker-compose.dev.yml --profile test run --rm test pytest -m integration -v

# All tests
docker compose -f docker-compose.dev.yml --profile test run --rm test
```

### Running Development Server

```bash
docker compose -f docker-compose.dev.yml up
# Starts trikusec-manager (8000) and trikusec-lynis-api (8001)
```

### Running Integration Tests with Lynis

```bash
# Set environment variables
export SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
export TRIKUSEC_LICENSE_KEY=test-license-key-$(date +%s)

# Start services
docker compose -f docker-compose.dev.yml up -d trikusec-manager trikusec-lynis-api

# Wait for health check, then run Lynis client
docker compose -f docker-compose.dev.yml up --abort-on-container-exit lynis-client
```
