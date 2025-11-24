# Docker Installation

Docker is the recommended way to install **TrikuSec**. This guide will walk you through the simple setup process using pre-built Docker images.

## Quick Installation

**TrikuSec** uses pre-built Docker images published on GitHub Container Registry, making installation as simple as:

1. Download `docker-compose.yml`
2. Create a `.env` file with your environment variables
3. Run `docker compose up -d`

No need to clone the repository or build images from source!

## Prerequisites

- *Docker* and *Docker Compose* installed

## Installation Steps

### 1. Download docker-compose.yml

[Download the docker-compose.yml file](https://raw.githubusercontent.com/TrikuSec/trikusec/refs/heads/main/docker-compose.yml)

Download the `docker-compose.yml` file from the [TrikuSec repository](https://github.com/trikusec/trikusec/blob/main/docker-compose.yml) and save it to your desired location.

### 2. Create Environment File

Create a `.env` file in the same directory as `docker-compose.yml`:

**Generate a secure SECRET_KEY:**

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

**Create your `.env` file:**

```bash
SECRET_KEY=your-generated-secret-key-here
TRIKUSEC_DOMAIN=trikusec.yourdomain.com
```

The following environment variables are **recommended**:

- `SECRET_KEY` - (Required) Django secret key for cryptographic signing
- `TRIKUSEC_DOMAIN` - (Recommended) Your domain (or subdomain) name. This automatically configures:
    - Admin UI URL: `https://trikusec.yourdomain.com:8000`
    - API URL: `https://trikusec.yourdomain.com:8001`
    - SSL Certificates
    - Allowed Hosts


```
# Filename: .env

# Required variables
SECRET_KEY=your-generated-secret-key-here
TRIKUSEC_DOMAIN=trikusec.yourdomain.com

# Set admin password (recommended for first run, otherwise it will be set to 'trikusec')
TRIKUSEC_ADMIN_PASSWORD=your-secure-password
```

Other environment variables are optional. See the [Configuration Guide](../configuration/environment-variables.md) for all available options.

### 3. Start TrikuSec

```bash
docker compose up -d
```

This will:

- Pull the pre-built Docker images from GitHub Container Registry:
  - `ghcr.io/trikusec/trikusec-nginx:latest`
  - `ghcr.io/trikusec/trikusec-manager:latest`
  - `ghcr.io/trikusec/trikusec-lynis-api:latest`
- Start all services (nginx reverse proxy, manager, and API)
- Generate SSL certificates
- Initialize the database
- Create the default admin user

### 4. Access TrikuSec

Once started, access TrikuSec at:

```
https://trikusec.yourdomain.com:8000
```

Default credentials:
- **Username:** `admin`
- **Password:** `trikusec`

!!! warning "Change Default Password"
    For production deployments:
    
    1. Set `TRIKUSEC_ADMIN_PASSWORD` in your `.env` file for the initial deployment
    2. After first login, change your password through the Django admin interface
    3. Comment out or remove `TRIKUSEC_ADMIN_PASSWORD` from your `.env` file to prevent accidental overwrites
    
    The password is only set automatically during initial admin user creation. If you manually change it via the UI and `TRIKUSEC_ADMIN_PASSWORD` is not set in the environment, your custom password will be preserved on container restarts.

## Optional Configuration

### Development Mode

For development environments only, you can enable DEBUG mode:

```bash
DJANGO_DEBUG=True
```

!!! danger "Security Warning"
    **NEVER** set `DJANGO_DEBUG=True` in production environments. Running with DEBUG enabled exposes sensitive information including stack traces, environment variables, and database queries to potential attackers.

### Production Settings

For production, we recommend using `TRIKUSEC_DOMAIN` which automatically configures allowed hosts.

If you need to manually override it:

```bash
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## Production Deployment

### Static Files

The Docker images automatically collect static files during startup, so no manual collection is needed. Static files are served by the nginx container.

### Enable HTTPS Security Headers

Add to your `.env` file:

```bash
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### PostgreSQL Setup

For production, PostgreSQL is strongly recommended. See the [PostgreSQL Setup Guide](postgresql.md) for detailed instructions.

## Architecture

TrikuSec uses a split architecture with three services:

1. **nginx** (Port 8000, 8001) - Reverse proxy handling HTTPS termination
2. **trikusec-manager** (Port 8000) - Admin UI and frontend
3. **trikusec-lynis-api** (Port 8001) - Lynis API endpoints for device enrollment and report uploads

All services use pre-built images from GitHub Container Registry, ensuring consistent and secure deployments.

![Architecture](../assets/img/trikusec_architecture.png)

## Next Steps

- [Configure Client](client-setup.md) - Set up Lynis clients
- [Configuration Guide](../configuration/index.md) - Advanced configuration options

