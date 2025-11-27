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

- **SSL Configuration**: When using self-signed certificates, saves the TrikuSec server certificate to `/etc/lynis/trikusec.crt` and configures Lynis to use it (via `upload-options=--cacert`). This scopes the certificate to Lynis only—other applications on the system will not trust the TrikuSec server.
- **Dependencies**: Installs required packages (Lynis, etc.).
- **Configuration**: Configures the Lynis custom profile (`custom.prf`) with the correct server URL and license key.
- **First Audit**: Performs the first audit with upload enabled (results will appear in TrikuSec).
- **Daily timer (optional)**: When **Enable daily reports (systemd)** is toggled on (enabled by default), the script installs the upstream `lynis.service`/`lynis.timer` units and enables the timer so reports continue every day.

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

*   **Scoped Certificate (Recommended)**: Download the server certificate to `/etc/lynis/trikusec.crt` and configure Lynis to use it with `upload-options=--cacert /etc/lynis/trikusec.crt`. This limits the certificate trust to Lynis only.
*   **Ignore Errors**: Configure Lynis to ignore SSL errors by adding `upload-options=--insecure` to the custom profile (see step 3).

!!! warning "Mutual Exclusivity"
    Use either `--cacert` or `--insecure`, but never both. These options are mutually exclusive.

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

# If using self-signed certs, choose ONE of the following options:
# Option 1 (recommended): Use scoped certificate
# upload-options=--cacert /etc/lynis/trikusec.crt
#
# Option 2: Skip certificate validation (less secure)
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

## Automate Daily Runs (systemd)

Keep Lynis results current by scheduling a daily execution through `systemd` timers:

> **Tip:** If you leave the **Enable daily reports (systemd)** toggle enabled in *Settings → Enrollment configuration*, the automatic enroll script performs steps 1–3 below for you. Use the manual steps only when configuring hosts by hand or after disabling that toggle.

1. **Create service and timer files**:
   - `/etc/systemd/system/lynis.service`
   - `/etc/systemd/system/lynis.timer`

   You can copy the reference units shipped by the Lynis project and adapt them to your paths and options as needed.  
   Source: [Lynis systemd units](https://github.com/CISOfy/lynis/tree/master/extras/systemd)
   
   TrikuSec also ships copies under `docs/reference/systemd/` for convenience.

2. **Reload systemd to pick up the new units**:

   ```bash
   sudo systemctl daemon-reload
   ```

3. **Enable and start the timer** so it persists across reboots and begins immediately:

   ```bash
   sudo systemctl enable lynis.timer
   sudo systemctl start lynis.timer
   ```

4. **Verify the timer status**:

   ```bash
   sudo systemctl status lynis.timer
   sudo systemctl list-timers lynis.timer
   ```

The timer triggers the service once per day by default (adjust `OnCalendar` in the timer if you need a different cadence), ensuring each client uploads a fresh report to TrikuSec without manual intervention.

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
