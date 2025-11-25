# Devices

Learn how to list and manage devices in TrikuSec.

## Devices Overview

The list of devices is the main page of the manager.

![TrikuSec Devices List](../assets/img/trikusec-devices.png)

### Key Metrics

- **Total Devices** - Number of servers being monitored
- **Compliance Rate** - Overall compliance percentage
- **Active Warnings** - Number of security warnings
- **Recent Reports** - Latest audit reports

### Navigation

- **Devices** - View and manage all devices
- **Policies** - Create and manage compliance policies
- **Reports** - View detailed audit reports
- **Activity** - Recent activity log

## Device Identification

TrikuSec uses **5-factor device identification** to prevent duplicates when identifiers change (e.g., after re-imaging or Lynis updates). Devices are matched using:

1. HostID / HostID2 (Lynis identifiers)
2. Hostname
3. Primary IP Address (on gateway network)
4. Primary MAC Address

A device is matched if **2+ factors coincide** (same license key). When matched, the existing device is updated instead of creating a duplicate, preserving historical data.

## Device Management

### Viewing Devices

1. Click **Devices** from the main menu
2. See list of all devices
3. Filter by compliance status, license key, or date

### Device Details

Click on a device to view:

- **Compliance Status** - Current compliance percentage
- **Hardening Index** - Lynis hardening score (0-100)
- **Last Report** - Date and time of last audit
- **Warnings** - Security warnings and recommendations
- **Suggestions** - Improvement suggestions
- **Report History** - Historical compliance data

![Device Detail Page](../assets/img/trikusec-device-detail.png)

### Hardening Index

The **Lynis Hardening Index** is a unique security metric displayed for each device, calculated by Lynis during each audit scan. This index provides an indicator of how well a system has been hardened with security safeguards.

**Key Points:**

- **Range**: The index ranges from 0 to 100, displayed as `X/100` in the device details
- **Purpose**: It reflects the number of security measures implemented on the system
- **Not a Safety Percentage**: The index is an indicator of taken security measures, not a percentage of how "safe" a system might be
- **Updated Per Scan**: The hardening index is recalculated with each Lynis audit report upload

**How to Increase the Hardening Index:**

The best way to improve your hardening index is to implement the security safeguards recommended by Lynis:

1. **Review Warnings and Suggestions** - Check the device detail page for security warnings and improvement suggestions
2. **Apply Security Measures** - Implement the recommended security configurations
3. **Re-run Audits** - After making changes, have Lynis perform another audit to see the updated index

**Using the Hardening Index:**

- **Device Comparison**: Sort devices by hardening index to identify systems that need attention
- **Policy Rules**: Use the hardening index in policy queries to automatically identify devices below a certain threshold (e.g., `hardening_index < 60`)
- **Compliance Tracking**: Monitor how the hardening index changes over time in the report history

!!! tip "Learn More"
    For more information about the Lynis Hardening Index, see the [official Lynis documentation](https://linux-audit.com/lynis/lynis-hardening-index/).

### Device Actions

From the device detail page, use the **Actions** dropdown menu (located in the top-right corner of the Overview section) to access:

- **Export to PDF** - Generate and download a comprehensive PDF report containing device overview, audit details, compliance status, and security feedback
- **Delete Device** - Permanently remove a device and all its associated reports (requires confirmation)

Additional actions available on the device detail page:

- **View Compliance** - Detailed compliance breakdown
- **View Warnings** - Security warnings for this device
- **View Suggestions** - Recommendations for improvement

## Policy Management

See [Policies](policies.md) for detailed policy management guide.

## Report Analysis

See [Reports](reports.md) for detailed report analysis guide.

## Search and Filtering

Use the search bar to:
- Find devices by hostname
- Search by license key
- Filter by compliance status

## Activity Log

The Activity page shows a chronological log of all device events, including enrollments, report uploads, and compliance changes. You can filter by device, event type, and date range.

![Activity Log](../assets/img/trikusec-activity.png)

## Tips and Tricks

- **Bookmark Devices** - Bookmark frequently accessed devices
- **Export Data** - Export reports and compliance data
- **Set Alerts** - Configure alerts for compliance issues

