<!-- 5eabc3a6-3f2b-48ab-9018-4a87111ebee9 dbe9bd1c-aef3-46ca-b6c0-d19676e93186 -->
# Split Django Architecture into Two Processes with Separate Dockerfiles

## Overview

Migrate TrikuSec to a 2-container architecture with dedicated Dockerfiles for each service:

- `trikusec-manager` (port 8000): Frontend, admin UI, full dependencies. Built from `Dockerfile.frontend`.
- `trikusec-lynis-api` (port 8001): API only, minimal dependencies. Built from `Dockerfile.api`.

This separation allows for:

- Publishing distinct images: `trikusec/manager` and `trikusec/lynis-api`
- Reducing API image size and attack surface
- Independent security configuration

## Architecture Changes

### Services

- **trikusec-manager**: Handles web UI, admin, sessions. Direct SSL support.
- **trikusec-lynis-api**: Handles Lynis report uploads and checks. Direct SSL support. No admin UI.

### Configuration

- **Development**: Self-signed SSL certificates generated at startup. Direct access to ports 8000/8001.
- **Production**: SSL handled by reverse proxy (documented) or by containers if desired.

## Implementation Steps

### 1. Create Separate URL Configurations

- `src/trikusec/urls_frontend.py`: Admin + Frontend URLs
- `src/trikusec/urls_api.py`: API URLs only

### 2. Create Separate Settings Modules

- `src/trikusec/settings/frontend.py`: Full middleware, all apps
- `src/trikusec/settings/api.py`: Minimal middleware, API apps only, no sessions

### 3. Create Separate WSGI Applications

- `src/trikusec/wsgi_frontend.py`: Uses frontend settings
- `src/trikusec/wsgi_api.py`: Uses API settings

### 4. Create Separate Requirement Files

- `src/requirements-api.txt`: Excludes WeasyPrint and frontend-only libs
- `src/requirements-frontend.txt`: Full set of dependencies (includes `requirements-api.txt`)

### 5. Create SSL Helper Script

- `scripts/generate-ssl-cert.sh`: Helper to generate self-signed certs if missing

### 6. Create Separate Dockerfiles

**Dockerfile.frontend**

- Base: python:3.12-slim
- Installs: system dependencies for WeasyPrint (pango, cairo, etc.) + openssl
- Pip: `src/requirements-frontend.txt`
- CMD: runs `trikusec.wsgi_frontend` via gunicorn

**Dockerfile.api**

- Base: python:3.12-slim
- Installs: minimal system dependencies + openssl
- Pip: `src/requirements-api.txt`
- CMD: runs `trikusec.wsgi_api` via gunicorn

### 7. Update Entrypoint Script

- Update `docker-entrypoint.sh` to handle SSL generation and service-specific startup logic (skip admin setup for API)

### 8. Update Docker Compose Files

**docker-compose.yml**

- Service `trikusec-manager`: builds `Dockerfile.frontend`, port 8000
- Service `trikusec-lynis-api`: builds `Dockerfile.api`, port 8001

**docker-compose.dev.yml**

- Updates to match new service names
- Retains development specific settings (volumes, debug mode)

### 9. Documentation & Testing

- Update `AGENTS.md` with new architecture
- Update `.env.example`
- Create reverse proxy documentation
- Test both containers independently

## Migration Steps

1. Create WSGI, URLs, and Settings files
2. Split requirements
3. Create Dockerfiles
4. Update Entrypoint
5. Update Docker Compose
6. Verify functionality

### To-dos

- [ ] Create separate URL configurations (urls_frontend.py, urls_api.py)
- [ ] Create separate settings modules (settings/frontend.py, settings/api.py)
- [ ] Create separate WSGI applications (wsgi_frontend.py, wsgi_api.py)
- [ ] Create separate requirements files (requirements-api.txt, requirements-frontend.txt)
- [ ] Create SSL certificate generation script
- [ ] Create Dockerfile.frontend
- [ ] Create Dockerfile.api
- [ ] Update docker-entrypoint.sh logic
- [ ] Update docker-compose.yml with new services and Dockerfiles
- [ ] Update docker-compose.dev.yml with new services
- [ ] Create reverse proxy documentation
- [ ] Update .env.example and docs
- [ ] Update test fixtures (conftest.py)
- [ ] Update AGENTS.md