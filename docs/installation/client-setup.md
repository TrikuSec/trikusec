# Client Setup

This guide explains how to configure Lynis clients to send audit reports to your TrikuSec server.

!!! info "Security Note"
    TrikuSec uses a **read-only model** - it only receives audit data from your servers. The only requirement is [Lynis](https://cisofy.com/lynis/), a well-established open-source tool that can be installed via standard package managers. No proprietary agents or additional services are required.

There are two main ways to configure a client:

1. **Using enroll script (Automatic)** - Recommended
2. **Manually**

## Using enroll script (Automatic)

This is the recommended method as it handles dependencies and configuration automatically.

### Steps

1. **Choose License**: Log in to TrikuSec and go to the Enrollment section. Decide whether to use the **Default License** (shared) or generate a **Specific License** for this device (recommended).
2. **Copy Command**: Copy the provided command snippet.
3. **Run**: Paste it in your device terminal.



![Enrollment Command](../assets/img/trikusec-enroll-new-device.png)

### What the script does

The enrollment script performs the following actions:

- **SSL Configuration**: Adds the Lynis API SSL certificate to the trust store (only when using self-signed certificates).
- **Dependencies**: Installs required packages (Lynis, etc.).
- **Configuration**: Configures the Lynis custom profile (`custom.prf`) with the correct server URL and license key.
- **First Audit**: Performs the first audit with upload enabled (results will appear in TrikuSec).

### Configuration

The script behavior can be fine-tuned via **Settings - Enroll script configuration** in the TrikuSec web interface.

You can configure:

- **Lynis plugins**: Custom plugins to download and install.
- **Additional packages**: Extra system packages to install (e.g., `rkhunter`, `auditd`).
- **Skip tests**: Specific Lynis tests to skip during audits.


![Enrollment Configuration](../assets/img/trikusec-enrollment-configuration.png)

## Manually

If you prefer to configure the client manually, follow these steps.

### 1. Handle SSL Certificates

If your TrikuSec server uses self-signed certificates, you have two options:
*   **Trust the Certificate**: Download the server certificate and add it to the device's trust store.
*   **Ignore Errors**: Configure Lynis to ignore SSL errors by adding `upload-options=--insecure` to the custom profile (see step 3).

### 2. Install Lynis

Install Lynis using your package manager:

```bash
sudo apt install lynis
```

### 3. Configure Custom Profile

You need to create a custom profile file at `/etc/lynis/custom.prf`. You can obtain the basic parameters (**upload-server** and **license key**) from the Enroll section of TrikuSec.

Example content for `/etc/lynis/custom.prf`:

```ini
# Custom profile for TrikuSec
upload=yes

# License key from TrikuSec server
license-key=YOUR_LICENSE_KEY

# Point to the TrikuSec Lynis API server
upload-server=YOUR_SERVER_ADDRESS

# If using self-signed certs and you didn't add cert to trust store:
# upload-options=--insecure
```

### 4. Perform First Audit

Run the audit command to generate and upload the first report:

```bash
lynis audit system --upload --quick
```

You can also specify a profile explicitly if needed:

```bash
lynis audit system --upload --quick --profile /etc/lynis/custom.prf
```

## Troubleshooting

### Connection Issues

If you're having trouble connecting to the server:

1. **Check server URL**: Ensure `upload-server` points to the correct address (default port is 8001 for the API).
2. **Check firewall**: Ensure port 8001 (or your configured API port) is open.
3. **Check SSL**: If using HTTPS, ensure certificates are valid or use `--insecure` flag.

### License Key Issues

If you get license key errors:

1. Verify the license key is correct in `/etc/lynis/custom.prf`.
2. Check that the license key exists in TrikuSec server.
3. Ensure the license key hasn't been revoked.

### Upload Failures

If uploads fail:

1. Check network connectivity: `curl -k https://yourserver:8001/api/lynis/license`
2. Check server logs: `docker compose logs trikusec-lynis-api`
3. Verify the API endpoint is accessible.
