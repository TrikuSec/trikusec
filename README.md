# TrikuSec

> [!WARNING]
> This project is still in development and should NOT be used in production.

**TrikuSec** is a centralized Linux server auditing and compliance management platform built on [Lynis](https://cisofy.com/lynis/). It collects, stores, and analyzes security audit reports from multiple Linux servers in one place, enabling centralized monitoring and policy compliance management across your infrastructure.

## Use Cases

TrikuSec is ideal for:

- **Security Compliance Monitoring**: Ensure servers meet security policies and regulatory requirements
- **Infrastructure Auditing**: Track security posture across multiple servers from a single dashboard
- **Change Tracking**: Monitor changes between audit runs to identify security drift
- **Policy Enforcement**: Automatically evaluate compliance against organizational policies
- **Centralized Reporting**: Single point of visibility for all server audits across your infrastructure

## Features

### Core Capabilities

- **Centralized Audit Collection**: Receives audit reports from multiple Linux servers via Lynis clients, storing full reports and generating diff reports to track changes over time
- **Device Management**: Tracks all monitored servers with metadata including hostname, OS, distribution, version, and compliance status
- **Policy & Compliance Management**: Define custom compliance rules using a query language and automatically evaluate devices against assigned policies
- **Report Analysis**: View complete audit reports, track changes between audits, and analyze historical compliance trends
- **PDF Export**: Export comprehensive device reports to PDF format for documentation and compliance audits
- **Web Dashboard**: User-friendly interface for viewing devices, compliance status, policies, and reports
- **API Integration**: Lynis-compatible API endpoints for seamless integration with existing Lynis installations

### Screenshots

![TrikuSec Devices Dashboard](docs/assets/img/trikusec-devices.png)

![Device Detail View](docs/assets/img/trikusec-device-detail.png)

## Quick Start

1. **Download `docker-compose.yml`** from the [repository](https://github.com/trikusec/trikusec/blob/main/docker-compose.yml)

2. **Create a `.env` file** with your `SECRET_KEY`:
   ```bash
   # Generate a secure SECRET_KEY
   python3 -c "import secrets; print(secrets.token_urlsafe(50))"
   
   # Add to .env file
   SECRET_KEY=your-generated-secret-key-here
   ```

3. **Start TrikuSec**:
   ```bash
   docker compose up -d
   ```

4. **Access TrikuSec** at `https://localhost:8000`
   - Default credentials: `admin` / `trikusec`
   - ⚠️ **Change the default password in production!**

## Documentation

📚 **Full documentation available at:** [https://trikusec.github.io/trikusec/](https://trikusec.github.io/trikusec/)

The documentation includes:
- **Installation** - Detailed installation guides
- **Configuration** - Environment variables and security settings
- **Usage** - Dashboard, policies, and reports guides
- **API Reference** - Complete API documentation
- **Development** - Contributing and development setup

## Security Philosophy

TrikuSec follows a **read-only security model** - it only receives audit data from your servers and never pushes changes or executes commands. The only requirement on monitored servers is [Lynis](https://cisofy.com/lynis/), a well-established open-source tool available in standard Linux repositories.

## License

TrikuSec is licensed under the **GNU General Public License v3.0** (GPL-3.0).

See the [LICENSE](LICENSE) file for the full license text.

## Acknowledgments

TrikuSec is built on [Lynis](https://cisofy.com/lynis/), an excellent open-source security auditing tool. We are grateful to the Lynis project and its community for providing such a robust foundation.

### Important Note

**TrikuSec is not a professional product.** This is an open-source project in active development. If you are looking for a robust, production-ready security solution with professional support, service level agreements, and enterprise features, we recommend considering [Lynis Enterprise](https://cisofy.com/pricing/) by CISOfy.

> **Note:** We have no relationship, affiliation, or partnership with CISOfy. This recommendation is made solely to help users find appropriate solutions for their needs.
