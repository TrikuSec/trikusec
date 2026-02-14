# Dashboard

The **Security Overview Dashboard** is the default landing page after login, providing a comprehensive view of your infrastructure's security posture at a glance.

## Overview

The dashboard aggregates data from all devices to provide key metrics, identify trends, and highlight areas requiring immediate attention.

## Dashboard Sections

### Summary Cards

Four key metric cards provide high-level statistics:

#### Total Devices
- Number of servers currently monitored by TrikuSec
- Includes all devices that have sent at least one report

#### Compliance Rate
- Shows the ratio of compliant devices to total devices
- Visual progress bar color-coded by compliance level:
  - **Green** (≥80%): Good compliance
  - **Yellow** (50-79%): Moderate compliance
  - **Red** (<50%): Poor compliance
- Displays both the fraction (e.g., "12/15") and percentage

#### Total Warnings
- Aggregated count of all security warnings across all devices
- Helps track overall security posture trends
- Each device contributes its warning count to this total

#### Average Hardening Index
- Mean hardening index across all devices with reports
- Ranges from 0 to 100 (higher is better)
- Visual progress bar shows the average score
- Only includes devices that have submitted Lynis reports

### OS Distribution

Visualizes the operating systems deployed across your infrastructure:

- Lists each OS/version combination with device counts
- Horizontal bars show relative distribution
- OS icons for quick visual identification
- Sorted by device count (most common first)

**Use cases:**
- Identify OS standardization opportunities
- Track OS version adoption
- Plan upgrades and migrations

### Top Security Issues

Two side-by-side panels highlight the most common security concerns:

#### Most Common Warnings
- Top 5 warnings by occurrence count
- Shows Lynis test ID (e.g., `PKGS-7392`)
- Brief description of the warning
- Badge showing number of affected devices

#### Most Common Suggestions
- Top 5 security suggestions
- Test ID and description
- Device count showing how widespread the issue is

**Benefits:**
- Prioritize remediation efforts
- Identify systemic security issues
- Track common misconfigurations

### Recent Activity

Shows the last 5 device events with:

- Event type icon (color-coded)
  - **Green**: New device enrolled
  - **Red**: Device deleted
  - **Purple**: Compliance status changed
  - **Gray**: Other events
- Device hostname (with link to device details)
- Event description
- Time since event occurred

**Quick access:** Click "View all" to see the complete activity feed.

### Needs Attention

Critical section highlighting devices that have been non-compliant for extended periods:

**Columns:**
- **Device**: Hostname with link to device details
- **OS**: Operating system with icon
- **Warnings**: Number of active warnings
- **Non-Compliant Since**: Date the device became non-compliant
- **Days**: Duration badge color-coded by severity:
  - **Red** (30+ days): Critical attention needed
  - **Yellow** (7-29 days): Should be reviewed soon
  - **Gray** (<7 days): Recently non-compliant
- **Last Scan**: Time since last report submission

**Sorting:** Devices are sorted by duration (longest non-compliant first) to help prioritize remediation efforts.

## Navigation

From the dashboard, you can:

- **View Device Details**: Click any device name to see full details
- **Access Activity Feed**: Click "View all" in Recent Activity
- **Navigate to Devices**: Use the "Devices" menu item
- **Review Policies**: Access policies via the navigation menu

## Best Practices

### Regular Monitoring

- Check the dashboard daily for new warnings or non-compliant devices
- Review the "Needs Attention" section weekly
- Track compliance rate trends over time

### Prioritization

Use the dashboard to prioritize work:

1. **Critical**: Devices in "Needs Attention" for 30+ days
2. **High**: Most common warnings affecting multiple devices
3. **Medium**: Recently non-compliant devices (7-29 days)
4. **Low**: Individual device warnings

### Trend Analysis

Monitor over time:

- **Compliance Rate**: Should increase as you address issues
- **Total Warnings**: Should decrease with remediation
- **Hardening Index**: Should increase with security improvements
- **Needs Attention**: Should have fewer entries over time

## Performance Notes

The dashboard aggregates data from all devices and reports. For large deployments (hundreds of devices), initial load may take a few seconds. The system optimizes queries to minimize impact:

- Summary cards use efficient database aggregations
- Report parsing is limited to devices with reports
- Top issues use Python counters for fast aggregation
- Recent activity is limited to the last 5 events

## Related Documentation

- [Getting Started](getting-started.md) - Initial setup and login
- [Devices](devices.md) - Device management details
- [Policies](policies.md) - Policy and compliance management
- [Activity Feed](../api/index.md) - Detailed activity tracking

