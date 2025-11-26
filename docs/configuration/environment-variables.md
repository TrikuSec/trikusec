# Environment Variables

Complete reference of all environment variables used by TrikuSec.

## Simplified Configuration (Recommended)

### TRIKUSEC_DOMAIN

The easiest way to configure TrikuSec is using a single domain variable. When set, this automatically derives other settings:

```bash
TRIKUSEC_DOMAIN=yourdomain.com
```

**This automatically configures:**

- `TRIKUSEC_URL=https://yourdomain.com:8000` (Admin UI)
- `TRIKUSEC_LYNIS_API_URL=https://yourdomain.com:8001` (Lynis API)
- `DJANGO_ALLOWED_HOSTS=localhost,yourdomain.com`
- `NGINX_CERT_CN=yourdomain.com` (SSL certificate)

You can still override any of these individually if needed for advanced configurations.

**Examples:**

For local development:
```bash
TRIKUSEC_DOMAIN=localhost
```

For production:
```bash
TRIKUSEC_DOMAIN=trikusec.example.com
```

!!! tip "Recommended Approach"
    Using `TRIKUSEC_DOMAIN` simplifies configuration and reduces errors. You only need to set one variable and everything else is automatically configured consistently.

## Required Variables

### SECRET_KEY

Django secret key for cryptographic signing.

```bash
SECRET_KEY=your-secret-key-here
```

!!! danger "Security Critical"
    **NEVER** commit your actual secret key to version control. Generate a new unique key for each deployment.

**Generate a secure key:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

## Django Settings

### DJANGO_DEBUG

Enable or disable Django debug mode.

```bash
DJANGO_DEBUG=False  # Production (default)
DJANGO_DEBUG=True   # Development only
```

!!! warning "Never Enable in Production"
    Setting `DJANGO_DEBUG=True` in production exposes sensitive information including stack traces, environment variables, and database queries.

### DJANGO_ALLOWED_HOSTS

Comma-separated list of allowed hostnames.

```bash
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

For development, you can use:
```bash
DJANGO_ALLOWED_HOSTS=*
```

!!! warning "Production Security"
    Never use `*` in production. Always specify exact hostnames.

### DJANGO_ENV

Environment type selector.

```bash
DJANGO_ENV=development   # Development settings (default)
DJANGO_ENV=production    # Production settings
DJANGO_ENV=testing       # Testing settings
```

## Database Configuration

### DATABASE_URL

Database connection URL. Defaults to SQLite if not set.

```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@host:5432/dbname

# SQLite (default)
# DATABASE_URL not set or empty
```

## Admin Configuration

### TRIKUSEC_ADMIN_USERNAME

Default admin username.

```bash
TRIKUSEC_ADMIN_USERNAME=admin
```

### TRIKUSEC_ADMIN_PASSWORD

Admin password behavior depends on whether the admin user already exists:

**On fresh installation:**
```bash
TRIKUSEC_ADMIN_PASSWORD=secure-password
```

If not set, defaults to `trikusec`. The password is used to create the initial admin user.

**On existing installation:**

- If `TRIKUSEC_ADMIN_PASSWORD` is **set** (explicitly in environment): Password will be updated to the new value
- If `TRIKUSEC_ADMIN_PASSWORD` is **not set** or **commented out**: Existing password is preserved

!!! tip "Best Practice"
    Set this variable for initial deployment, then comment it out or remove it from your `.env` file to prevent accidental password overwrites. Change the password via the Django admin UI after first login.

!!! warning "Production Security"
    Never use the default `trikusec` password in production. Always set a strong password for initial deployment.

## HTTPS Security

### SSL_CERT_DAYS

Overrides the validity period (in days) for the self-signed SSL certificates generated.

```bash
SSL_CERT_DAYS=365    # example: 1-year validity
```

If not set, defaults to 1825 days.

### SECURE_SSL_REDIRECT

Redirect all HTTP traffic to HTTPS.

```bash
SECURE_SSL_REDIRECT=True
```

### SECURE_HSTS_SECONDS

HTTP Strict Transport Security (HSTS) duration in seconds.

```bash
SECURE_HSTS_SECONDS=31536000  # 1 year
```

### SESSION_COOKIE_SECURE

Only send session cookies over HTTPS.

```bash
SESSION_COOKIE_SECURE=True
```

### CSRF_COOKIE_SECURE

Only send CSRF cookies over HTTPS.

```bash
CSRF_COOKIE_SECURE=True
```

## Rate Limiting

### RATELIMIT_ENABLE

Enable or disable rate limiting on API endpoints.

```bash
RATELIMIT_ENABLE=True   # Enabled (default)
RATELIMIT_ENABLE=False  # Disabled
```

## Server Configuration

### TRIKUSEC_URL

TrikuSec admin UI server URL (used for generating admin interface links).

```bash
TRIKUSEC_URL=https://localhost:443
```

This is the endpoint used for accessing the web management interface. It should point to your nginx reverse proxy or direct Django server for admin access.

In the enrollment workflow, `TRIKUSEC_URL` is only used for authenticated admin interactions (no device traffic).

### TRIKUSEC_LYNIS_API_URL

TrikuSec Lynis API server URL (used for device enrollment and report uploads).

```bash
TRIKUSEC_LYNIS_API_URL=https://localhost:8443
```

This is the endpoint used by monitored servers for:
- Downloading the enrollment script (`/api/lynis/enroll/`)
- Downloading self-signed certificate (via openssl)
- License validation (`/api/lynis/license/`)
- Uploading audit reports (`/api/lynis/upload/`)

If not set, falls back to `TRIKUSEC_URL` for backward compatibility.

!!! tip "Security Best Practice"
    Use separate endpoints for admin UI and Lynis API to improve security. This allows you to configure different firewall rules for each endpoint. See [Security Configuration](../configuration/security.md#api-endpoint-separation-architecture) for details.

## Example .env Files

### Simple Configuration (Recommended)

```bash
# Required
SECRET_KEY=your-generated-secret-key-here

# Domain-based configuration (automatically derives URLs and settings)
TRIKUSEC_DOMAIN=yourdomain.com

# Admin
TRIKUSEC_ADMIN_USERNAME=admin
TRIKUSEC_ADMIN_PASSWORD=your-secure-password

# Optional: Database
DATABASE_URL=postgresql://trikusec_user:password@postgres:5432/trikusec
```

### Advanced Configuration (All Options)

```bash
# Required
SECRET_KEY=your-generated-secret-key-here

# Domain (recommended)
TRIKUSEC_DOMAIN=yourdomain.com

# Django
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_ENV=production

# Database
DATABASE_URL=postgresql://trikusec_user:password@postgres:5432/trikusec

# Admin
TRIKUSEC_ADMIN_USERNAME=admin
TRIKUSEC_ADMIN_PASSWORD=your-secure-password

# HTTPS
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Rate Limiting
RATELIMIT_ENABLE=True

# Server (manual override - not needed if TRIKUSEC_DOMAIN is set)
TRIKUSEC_URL=https://yourdomain.com:8000
TRIKUSEC_LYNIS_API_URL=https://yourdomain.com:8001
```

