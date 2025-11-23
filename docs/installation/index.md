# Installation

This section covers installing and setting up TrikuSec.

## Overview

TrikuSec can be installed easily using Docker Compose. By default, *SQLite* is used for the database. You should consider using *PostgreSQL* for production deployments.


## Architecture
TrikuSec uses a split architecture with two WSGI applications:

1. **trikusec-manager** (Port 8000) - Admin UI and frontend
2. **trikusec-lynis-api** (Port 8001) - Lynis API endpoints for device enrollment and report uploads

Both services share the same database and are served by the same nginx reverse proxy.

![Architecture](../assets/img/trikusec_architecture.png)

## Installation Options

- **[Docker Installation](docker.md)** - Recommended for most users (quick setup)
- **[PostgreSQL Setup](postgresql.md)** - Database configuration for production
- **[Client Setup](client-setup.md)** - Configuring Lynis clients to send reports
- **[Backup & Recovery](backup-recovery.md)** - Backup strategies and recovery procedures

## Prerequisites

Before installing TrikuSec, ensure you have:

- Docker and Docker Compose installed

## Quick Start

The simplest installation method is using Docker with pre-built images:

1. Download `docker-compose.yml` from the repository
2. Create a `.env` file with the following environment variables:
    - `SECRET_KEY` - A secure secret key for Django. Generate a new key with: `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`
    - `TRIKUSEC_URL` - The URL of the TrikuSec server. Example: `https://yourserver:8000`
    - `TRIKUSEC_LYNIS_API_URL` - The URL of the Lynis API. Example: `https://yourserver:8001`
3. Run `docker compose up -d`

See the [Docker Installation Guide](docker.md) for detailed instructions.

## Next Steps

After installation, proceed to:

- [Configuration](../configuration/index.md) - Configure environment variables and security settings
- [Getting Started](../usage/getting-started.md) - Learn how to use TrikuSec

