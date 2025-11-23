# Reverse Proxy Configuration

TrikuSec supports advanced production deployments using a reverse proxy (Nginx, Traefik, Caddy) to handle SSL termination and traffic routing.

## Overview

In this architecture:
1. **Reverse Proxy**: Handles SSL/TLS, terminates port 443 (HTTPS), and routes traffic.
2. **TrikuSec Manager**: Receives traffic for the Admin UI and Frontend (e.g., `https://trikusec.example.com`).
3. **TrikuSec Lynis API**: Receives traffic for the Lynis API (e.g., `https://api.trikusec.example.com`).

To use a reverse proxy, disable internal SSL in TrikuSec containers by setting `DJANGO_SSL_ENABLED=False`.

## Configuration Examples

### 1. Nginx

```nginx
# /etc/nginx/conf.d/trikusec.conf

upstream trikusec_manager {
    server trikusec-manager:8000;
}

upstream trikusec_api {
    server trikusec-lynis-api:8001;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name trikusec.example.com api.trikusec.example.com;
    return 301 https://$host$request_uri;
}

# Manager (Frontend)
server {
    listen 443 ssl;
    server_name trikusec.example.com;

    ssl_certificate /etc/letsencrypt/live/trikusec.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/trikusec.example.com/privkey.pem;

    location / {
        proxy_pass http://trikusec_manager;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Lynis API
server {
    listen 443 ssl;
    server_name api.trikusec.example.com;

    ssl_certificate /etc/letsencrypt/live/api.trikusec.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.trikusec.example.com/privkey.pem;

    location / {
        proxy_pass http://trikusec_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Traefik

Add labels to your `docker-compose.yml`:

```yaml
services:
  trikusec-manager:
    # ... existing config ...
    environment:
      - DJANGO_SSL_ENABLED=False
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.trikusec-manager.rule=Host(`trikusec.example.com`)"
      - "traefik.http.routers.trikusec-manager.entrypoints=websecure"
      - "traefik.http.routers.trikusec-manager.tls.certresolver=myresolver"
      - "traefik.http.services.trikusec-manager.loadbalancer.server.port=8000"

  trikusec-lynis-api:
    # ... existing config ...
    environment:
      - DJANGO_SSL_ENABLED=False
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.trikusec-api.rule=Host(`api.trikusec.example.com`)"
      - "traefik.http.routers.trikusec-api.entrypoints=websecure"
      - "traefik.http.routers.trikusec-api.tls.certresolver=myresolver"
      - "traefik.http.services.trikusec-api.loadbalancer.server.port=8001"
```

### 3. Caddy

Create a `Caddyfile`:

```caddyfile
trikusec.example.com {
    reverse_proxy trikusec-manager:8000
}

api.trikusec.example.com {
    reverse_proxy trikusec-lynis-api:8001
}
```

Ensure your `docker-compose.yml` sets `DJANGO_SSL_ENABLED=False` for both services.


