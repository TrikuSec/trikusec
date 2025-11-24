# Installation

This section covers installing and setting up TrikuSec.

## Overview

TrikuSec can be installed easily using __*Docker Compose*__. By default, __*SQLite*__ is used for the database. You should consider using __*PostgreSQL*__ for production deployments.


## Architecture

**TrikuSec** uses a split architecture:

1. **trikusec-manager** (Port 8000) - Admin UI and frontend
2. **trikusec-lynis-api** (Port 8001) - Lynis API endpoints for device enrollment and report uploads

Both services share the same database and are served by the same nginx reverse proxy.

![Architecture](../assets/img/trikusec_architecture.png)

## Prerequisites

Before installing **TrikuSec**, ensure you have:

- *Docker* and *Docker Compose* installed

## Quick Start

The simplest installation method is using *Docker* with pre-built images:

1. [Download](https://raw.githubusercontent.com/TrikuSec/trikusec/refs/heads/main/docker-compose.yml) `docker-compose.yml` from [the repository](https://github.com/TrikuSec/trikusec/blob/main/docker-compose.yml)
2. Create a `.env` file with the following environment variables:
    - `SECRET_KEY` - A secure secret key for Django. Generate a new key with: `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`
    - `TRIKUSEC_DOMAIN` - The domain name (or subdomain) for your installation. Example: `trikusec.yourdomain.com`. This automatically configures the service URLs.
3. Run `docker compose up -d`

See the [Docker Installation Guide](docker.md) for detailed instructions.

## Next Steps

After installation, proceed to:

- [Getting Started](../usage/getting-started.md) - Learn how to use TrikuSec
- [Configuration](../configuration/index.md) - Configure environment variables and security settings
