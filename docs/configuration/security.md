# Security Configuration

Security best practices and hardening guide for TrikuSec.

## Production Security Checklist

- [ ] `DJANGO_DEBUG=False` is set
- [ ] `DJANGO_ALLOWED_HOSTS` is configured (not `*`)
- [ ] `SECRET_KEY` is unique and secure
- [ ] Default admin password is changed
- [ ] HTTPS is enabled with security headers
- [ ] Rate limiting is enabled
- [ ] PostgreSQL is used (not SQLite)
- [ ] Regular backups are configured

## Critical Security Settings

### Debug Mode

!!! danger "Critical"
    **NEVER** enable debug mode in production.

```bash
DJANGO_DEBUG=False
```

Debug mode exposes:
- Stack traces with code
- Environment variables
- Database queries
- Internal file paths

### Allowed Hosts

Always specify exact hostnames:

```bash
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

Never use:
```bash
DJANGO_ALLOWED_HOSTS=*  # INSECURE
```

### Secret Key

Generate a unique, secure secret key for each deployment:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

Never reuse secret keys across deployments.

## HTTPS Configuration

### Enable HTTPS Redirect

```bash
SECURE_SSL_REDIRECT=True
```

### HTTP Strict Transport Security (HSTS)

```bash
SECURE_HSTS_SECONDS=31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### Secure Cookies

```bash
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## Rate Limiting

Enable rate limiting to protect against abuse:

```bash
RATELIMIT_ENABLE=True
```

Rate limits apply to:
- API endpoints (`/api/lynis/upload/`, `/api/lynis/license/`)
- Login attempts
- Registration attempts

## Database Security

### Use PostgreSQL in Production

SQLite is fine for development, but PostgreSQL provides:
- Better concurrency
- Connection pooling
- Better security features

See [PostgreSQL Setup](../installation/postgresql.md) for details.

### Database Credentials

- Use strong passwords
- Limit database user permissions
- Use connection encryption
- Regularly rotate credentials

## Authentication Security

### Change Default Credentials

Never use default admin credentials in production:

```bash
TRIKUSEC_ADMIN_USERNAME=admin
TRIKUSEC_ADMIN_PASSWORD=your-strong-password-here
```

### Password Requirements

Ensure strong passwords:
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Not dictionary words
- Not reused from other services

## Network Security

### API Endpoint Separation Architecture

TrikuSec uses a **dual-endpoint architecture** to improve security by separating admin UI access from Lynis API access:

- **Admin UI Endpoint** (`TRIKUSEC_URL`, default: `https://localhost:8000`): 
  - Used for accessing the web management interface
  - Requires authentication (login required)
  - Should only be accessible to sysadmins
  - Typically accessed on port 443 via nginx reverse proxy

- **Lynis API Endpoint** (`TRIKUSEC_LYNIS_API_URL`, default: `https://localhost:8001`):
  - Used by monitored servers for downloading `enroll.sh`, certificate download, license validation, and report uploads
  - No authentication UI exposed (API-only endpoints)
  - Should be accessible from your server network
  - Typically accessed on a separate port (e.g., 8443) via nginx

#### Security Benefits

This separation provides important security advantages:

1. **Compromised Server Isolation**: If a monitored server is compromised, the attacker cannot access the admin UI or authentication forms, even if they can upload reports to the API.

2. **Firewall Rule Granularity**: Sysadmins can configure different firewall rules:
   - **Admin UI**: Restrict access to corporate IPs, VPN networks, or specific admin workstations
   - **Lynis API**: Allow access from server networks, data centers, or cloud provider IP ranges

3. **Attack Surface Reduction**: The admin interface is not exposed to the same network as monitored servers, reducing the risk of credential theft or session hijacking.
4. **Enrollment Isolation**: Devices download `enroll.sh` directly from the Lynis API endpoint, so production servers never need outbound access to the admin UI.

#### Example Firewall Configuration

```bash
# Allow admin UI access only from corporate network
iptables -A INPUT -p tcp --dport 8000 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP

# Allow Lynis API access from server network
iptables -A INPUT -p tcp --dport 8001 -s 192.168.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 8001 -j DROP
```

#### Configuration

Set `TRIKUSEC_LYNIS_API_URL` to your Lynis API endpoint. If not set, it falls back to `TRIKUSEC_URL` for backward compatibility.

See [Environment Variables](../configuration/environment-variables.md) for configuration details.

### Firewall Configuration

Only expose necessary ports:
- `8000` (or your configured port) for Admin UI HTTP/HTTPS
- `8001` (or your configured port) for Lynis API HTTP/HTTPS
- Database port only to application server (if external)

### Reverse Proxy

Use a reverse proxy (Nginx, Apache) for:
- SSL/TLS termination
- Additional security headers
- Rate limiting
- DDoS protection

By default, **TrikuSec** uses a reverse proxy (nginx) to handle HTTPS termination. The nginx configuration is included in the Docker images and automatically handles SSL/TLS termination.

## Security Headers

TrikuSec includes security headers, but you can add more via reverse proxy:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

## Backup and Recovery

All the data is stored in the database. See [Backup and Recovery](../installation/backup-recovery.md) for details.

## Additional Resources

- [Django Security Documentation](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)

