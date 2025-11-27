#!/usr/bin/env bash

#
# TrikuSec Lynis Enrollment Script
# This script enrolls a Debian-based system with TrikuSec for security auditing
#

set -e  # Exit on error
set -o pipefail  # Exit on pipe failure

#==============================================================================
# Configuration Variables
#==============================================================================

TRIKUSEC_LYNIS_UPLOAD_SERVER={{ trikusec_lynis_upload_server }}
TRIKUSEC_CERT_TMP=/tmp/trikusec.crt
TRIKUSEC_CERT_PATH=/etc/lynis/trikusec.crt
TRIKUSEC_LICENSEKEY={{ licensekey }}
USE_SCOPED_CERT=false
IGNORE_SSL_ERRORS={% if ignore_ssl_errors %}true{% else %}false{% endif %}
OVERWRITE_LYNIS_PROFILE={% if overwrite_lynis_profile %}true{% else %}false{% endif %}
USE_CISOFY_REPO={% if use_cisofy_repo %}true{% else %}false{% endif %}
ENABLE_DAILY_REPORTS={% if enable_daily_reports %}true{% else %}false{% endif %}
ADDITIONAL_PACKAGES="{% if additional_packages %}{{ additional_packages }}{% endif %}"
SKIP_TESTS="{% if skip_tests %}{{ skip_tests }}{% endif %}"
{% if plugin_urls %}
PLUGIN_URLS=(
{% for plugin_url in plugin_urls %}
"{{ plugin_url }}"
{% endfor %}
)
{% else %}
PLUGIN_URLS=()
{% endif %}

SUDO=""

#==============================================================================
# Helper Functions
#==============================================================================

print_header() {
    echo ""
    echo "========================================================================"
    echo "$1"
    echo "========================================================================"
    echo ""
}

print_info() {
    echo "[INFO] $1"
}

print_success() {
    echo "[SUCCESS] $1"
}

print_error() {
    echo "[ERROR] $1" >&2
}

print_warning() {
    echo "[WARNING] $1"
}

#==============================================================================
# Overview Display
#==============================================================================

show_overview() {
    print_header "TrikuSec Enrollment Configuration"
    
    echo "System Information:"
    echo "  - Hostname:              $(hostname)"
    echo "  - OS:                    $(grep PRETTY_NAME /etc/os-release | cut -d'"' -f2)"
    echo "  - User:                  $(whoami)"
    echo ""
    
    echo "TrikuSec Configuration:"
    echo "  - Upload Server:         ${TRIKUSEC_LYNIS_UPLOAD_SERVER}"
    echo "  - License Key:           ${TRIKUSEC_LICENSEKEY:0:8}...${TRIKUSEC_LICENSEKEY: -4}"
    echo "  - SSL Validation:        $([ "$IGNORE_SSL_ERRORS" = "true" ] && echo "Disabled" || echo "Enabled")"
    echo ""
    
    echo "Lynis Configuration:"
    echo "  - Overwrite Profile:     $([ "$OVERWRITE_LYNIS_PROFILE" = "true" ] && echo "Yes" || echo "No")"
    echo "  - Lynis Source:          $([ "$USE_CISOFY_REPO" = "true" ] && echo "CISOfy Repository" || echo "System Repository")"
    if [ -n "$ADDITIONAL_PACKAGES" ]; then
        echo "  - Additional Packages:   ${ADDITIONAL_PACKAGES}"
    fi
    if [ -n "$SKIP_TESTS" ]; then
        echo "  - Skip Tests:            ${SKIP_TESTS}"
    fi
    if [ ${#PLUGIN_URLS[@]} -gt 0 ]; then
        echo "  - Plugins to Install:    ${#PLUGIN_URLS[@]}"
    fi
    echo "  - Daily systemd timer:   $([ \"$ENABLE_DAILY_REPORTS\" = \"true\" ] && echo \"Enabled\" || echo \"Disabled\")"
    echo ""
    
    echo "Press ENTER to continue or CTRL+C to abort..."
    read -r
}

#==============================================================================
# Prerequisite Checks
#==============================================================================

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check for Debian-based system
    if [ ! -f /etc/debian_version ]; then
        print_error "This script is only compatible with Debian-based systems."
        exit 1
    fi
    print_success "Debian-based system detected"
    
    # Check for root or sudo
    setup_sudo
}

setup_sudo() {
    if [ "$(id -u)" -ne 0 ]; then
        if [ -x "$(command -v sudo)" ]; then
            SUDO=sudo
            print_info "Running with sudo privileges"
        else
            print_error "Please run this script as root or install sudo."
            exit 1
        fi
    else
        print_info "Running as root"
    fi
}

#==============================================================================
# SSL Certificate Handling
#==============================================================================

setup_ssl_certificate() {
    print_header "SSL Certificate Setup"
    
    if [ "$IGNORE_SSL_ERRORS" = "true" ]; then
        print_warning "Skipping server certificate validation (configured)."
        return 0
    fi
    
    print_info "Checking server certificate..."
    
    # Check if the server is reachable and has a valid certificate
    if ! curl -s "https://${TRIKUSEC_LYNIS_UPLOAD_SERVER}" -o /dev/null; then
        print_warning "Server certificate is self-signed. Saving it for Lynis use only."
        
        # Check if openssl is installed
        if [ ! -x "$(command -v openssl)" ]; then
            print_info "Installing openssl..."
            ${SUDO} apt-get update -qq
            ${SUDO} apt-get install -y openssl
        fi
        
        print_info "Downloading server certificate..."
        if openssl s_client -showcerts -connect "${TRIKUSEC_LYNIS_UPLOAD_SERVER}" </dev/null 2>/dev/null | \
           sed -n -e '/BEGIN\ CERTIFICATE/,/END\ CERTIFICATE/ p' > "${TRIKUSEC_CERT_TMP}"; then
            # Save certificate to Lynis-scoped path instead of system CA store
            ${SUDO} mkdir -p /etc/lynis
            ${SUDO} cp "${TRIKUSEC_CERT_TMP}" "${TRIKUSEC_CERT_PATH}"
            ${SUDO} chmod 644 "${TRIKUSEC_CERT_PATH}"
            rm -f "${TRIKUSEC_CERT_TMP}"
            USE_SCOPED_CERT=true
            print_success "Server certificate saved to ${TRIKUSEC_CERT_PATH}"
        else
            print_error "Failed to download server certificate"
            exit 1
        fi
    else
        print_success "Server certificate is valid"
    fi
}

#==============================================================================
# Package Installation
#==============================================================================

install_packages() {
    print_header "Installing Required Packages"
    
    # Set up CISOfy repository if enabled
    if [ "$USE_CISOFY_REPO" = "true" ]; then
        print_info "Setting up CISOfy Lynis repository..."
        
        # Check if gpg is installed, install if needed
        if [ ! -x "$(command -v gpg)" ]; then
            print_info "Installing gpg..."
            ${SUDO} apt-get update -qq
            ${SUDO} apt-get install -y gpg
        fi
        
        curl -fsSL https://packages.cisofy.com/keys/cisofy-software-public.key | \
            ${SUDO} gpg --dearmor -o /etc/apt/trusted.gpg.d/cisofy-software-public.gpg
        echo "deb [arch=amd64,arm64 signed-by=/etc/apt/trusted.gpg.d/cisofy-software-public.gpg] https://packages.cisofy.com/community/lynis/deb/ stable main" | \
            ${SUDO} tee /etc/apt/sources.list.d/cisofy-lynis.list
        print_success "CISOfy repository configured"
    fi
    
    print_info "Updating package lists..."
    ${SUDO} apt-get update -qq
    
    local packages="curl lynis"
    if [ -n "$ADDITIONAL_PACKAGES" ]; then
        packages="${packages} ${ADDITIONAL_PACKAGES}"
    fi
    
    print_info "Installing packages: ${packages}"
    ${SUDO} apt-get install -y ${packages}
    
    # Get installed Lynis version
    LYNIS_VERSION=$(lynis --version 2>/dev/null || echo "unknown")
    print_success "Lynis version ${LYNIS_VERSION} installed"
}

#==============================================================================
# Lynis Profile Setup
#==============================================================================

setup_lynis_profile() {
    print_header "Setting Up Lynis Profile"
    
    # Handle existing custom profile
    if [ -f /etc/lynis/custom.prf ]; then
        if [ "$OVERWRITE_LYNIS_PROFILE" = "true" ]; then
            print_warning "Existing /etc/lynis/custom.prf detected. Overwriting as requested."
            ${SUDO} rm -f /etc/lynis/custom.prf
        else
            print_error "A custom profile file already exists. Please remove it before running this script or enable overwriting in TrikuSec."
            exit 1
        fi
    fi
    
    # Create custom profile file
    ${SUDO} mkdir -p /etc/lynis
    ${SUDO} touch /etc/lynis/custom.prf
    print_success "Lynis custom profile created"
}

#==============================================================================
# Host Identifiers
#==============================================================================

setup_host_identifiers() {
    print_header "Configuring Host Identifiers"
    
    print_info "Checking host identifiers..."
    
    # Host identifiers (hostid and hostid2) are used by Lynis to uniquely identify systems
    # Reference: https://cisofy.com/documentation/lynis/
    # In some environments (e.g., Docker containers), host identifiers may not be automatically generated
    HOSTIDS_OUTPUT=$(lynis show hostids 2>/dev/null || echo "")
    
    # Extract hostid and hostid2 values from the output
    HOSTID_VALUE=$(echo "$HOSTIDS_OUTPUT" | grep -E "^hostid[[:space:]]*:" | sed 's/.*:[[:space:]]*//' | tr -d '[:space:]' || echo "")
    HOSTID2_VALUE=$(echo "$HOSTIDS_OUTPUT" | grep -E "^hostid2[[:space:]]*:" | sed 's/.*:[[:space:]]*//' | tr -d '[:space:]' || echo "")
    
    if [ -z "$HOSTID_VALUE" ] || [ -z "$HOSTID2_VALUE" ]; then
        print_info "Host identifiers are empty. Generating new identifiers..."
        
        # Generate host identifiers using random data
        # hostid: 40 characters (SHA1 hash)
        # hostid2: 64 characters (SHA256 hash)
        local new_hostid=$(head -c 64 /dev/random | sha1sum | awk '{print $1}')
        local new_hostid2=$(head -c 64 /dev/random | sha256sum | awk '{print $1}')
        
        ${SUDO} lynis configure settings "hostid=${new_hostid}:hostid2=${new_hostid2}"
        print_success "Host identifiers generated successfully"
    else
        print_success "Host identifiers already exist"
        print_info "  - hostid:  ${HOSTID_VALUE}"
        print_info "  - hostid2: ${HOSTID2_VALUE}"
    fi
}

#==============================================================================
# Lynis Configuration
#==============================================================================

configure_lynis() {
    print_header "Configuring Lynis"
    
    print_info "Configuring upload settings..."
    
    # Bugfix: lynis configure does not work correctly with :port in the upload server URL
    # so we need to set the configuration manually
    echo "upload-server=${TRIKUSEC_LYNIS_UPLOAD_SERVER}/api/lynis" | ${SUDO} tee -a /etc/lynis/custom.prf > /dev/null
    
    ${SUDO} lynis configure settings \
        "upload=yes:license-key=${TRIKUSEC_LICENSEKEY}:upload-server=${TRIKUSEC_LYNIS_UPLOAD_SERVER}/api/lynis" \
        "auditor=TrikuSec"
    
    # Configure SSL options (mutually exclusive: --insecure OR --cacert, never both)
    if [ "$IGNORE_SSL_ERRORS" = "true" ]; then
        print_warning "Configuring Lynis to ignore SSL errors"
        echo "upload-options=--insecure" | ${SUDO} tee -a /etc/lynis/custom.prf > /dev/null
    elif [ "$USE_SCOPED_CERT" = "true" ]; then
        print_info "Configuring Lynis to use scoped certificate"
        echo "upload-options=--cacert ${TRIKUSEC_CERT_PATH}" | ${SUDO} tee -a /etc/lynis/custom.prf > /dev/null
    fi
    
    # Handle version-specific configuration
    if [ "$LYNIS_VERSION" != "unknown" ]; then
        LYNIS_MAJOR=$(echo "$LYNIS_VERSION" | awk -F. '{print $1}')
        if [ "$LYNIS_MAJOR" -lt 3 ]; then
            print_info "Lynis version < 3.0.0 detected, adding CRYP-7902 to skip list"
            ${SUDO} lynis configure settings "skip-test=CRYP-7902"
        fi
    fi
    
    # Configure tests to skip
    if [ -n "$SKIP_TESTS" ]; then
        print_info "Configuring Lynis to skip tests: ${SKIP_TESTS}"
        ${SUDO} lynis configure settings "skip-test=${SKIP_TESTS}"
    fi
    
    print_success "Lynis configured successfully"
}

#==============================================================================
# Plugin Installation
#==============================================================================

install_plugins() {
    if [ ${#PLUGIN_URLS[@]} -eq 0 ]; then
        return 0
    fi
    
    print_header "Installing Lynis plugins configured in TrikuSec"
    
    print_info "Finding plugin directory..."
    PLUGIN_DIR=$(lynis show plugindir 2>/dev/null | grep -Eo '/[^[:space:]]+' | head -n1)
    if [ -z "$PLUGIN_DIR" ]; then
        PLUGIN_DIR="/var/lib/lynis/plugins"
        print_warning "Falling back to default plugin directory: ${PLUGIN_DIR}"
    else
        print_info "Using plugin directory: ${PLUGIN_DIR}"
    fi
    
    ${SUDO} mkdir -p "${PLUGIN_DIR}"
    
    local plugin_count=0
    for PLUGIN_URL in "${PLUGIN_URLS[@]}"; do
        print_info "Downloading plugin from ${PLUGIN_URL}"
        
        TMP_PLUGIN=$(mktemp)
        if curl -fsSL "${PLUGIN_URL}" -o "${TMP_PLUGIN}"; then
            PLUGIN_BASENAME=$(basename "${PLUGIN_URL}")
            ${SUDO} mv "${TMP_PLUGIN}" "${PLUGIN_DIR}/${PLUGIN_BASENAME}"
            ${SUDO} chown root:root "${PLUGIN_DIR}/${PLUGIN_BASENAME}"
            ${SUDO} chmod 644 "${PLUGIN_DIR}/${PLUGIN_BASENAME}"
            
            # Get plugin name from the plugin file
            PLUGIN_NAME=$(grep -Eo '# PLUGIN_NAME=.*' "${PLUGIN_DIR}/${PLUGIN_BASENAME}" | sed 's/# PLUGIN_NAME=//' || echo "")
            
            if [ -n "$PLUGIN_NAME" ]; then
                ${SUDO} lynis configure settings "plugin=${PLUGIN_NAME}"
                print_success "Installed and enabled plugin: ${PLUGIN_NAME}"
            else
                print_warning "Installed plugin ${PLUGIN_BASENAME} but could not determine plugin name"
            fi
            
            plugin_count=$((plugin_count + 1))
        else
            print_error "Failed to download Lynis plugin from ${PLUGIN_URL}"
            rm -f "${TMP_PLUGIN}"
            exit 1
        fi
    done
    
    print_success "Installed ${plugin_count} plugin(s)"
}

#==============================================================================
# Daily systemd Timer
#==============================================================================

setup_daily_reports() {
    if [ "$ENABLE_DAILY_REPORTS" != "true" ]; then
        print_info "Daily Lynis systemd timer disabled in TrikuSec settings."
        return 0
    fi

    if ! command -v systemctl >/dev/null 2>&1; then
        print_warning "systemctl not found. Skipping daily timer configuration."
        return 0
    fi

    print_header "Configuring Daily Lynis systemd timer"

    local service_path="/etc/systemd/system/lynis.service"
    local timer_path="/etc/systemd/system/lynis.timer"

    print_info "Installing reference Lynis service unit at ${service_path}"
    cat <<'SERVICE_UNIT' | ${SUDO} tee "${service_path}" > /dev/null
#################################################################################
#
# Lynis service file for systemd
#
#################################################################################
#
# - Adjust path to link to location where Lynis binary is installed
#
# - Place this file together with the lynis.timer file in the related
#   systemd directory (e.g. /etc/systemd/system/)
#
# - See details in lynis.timer file
#
#################################################################################

[Unit]
Description=Security audit and vulnerability scanner
Documentation=https://cisofy.com/docs/

[Service]
Nice=19
IOSchedulingClass=best-effort
IOSchedulingPriority=7
Type=simple
ExecStart=/usr/sbin/lynis audit system --cronjob

[Install]
WantedBy=multi-user.target

#EOF
SERVICE_UNIT
    ${SUDO} chmod 644 "${service_path}"

    print_info "Installing reference Lynis timer unit at ${timer_path}"
    cat <<'TIMER_UNIT' | ${SUDO} tee "${timer_path}" > /dev/null
#################################################################################
#
# Lynis timer file for systemd
#
#################################################################################
#
# - Place this file together with the lynis.service file in the related
#   systemd directory (e.g. /etc/systemd/system)
#
# - Tell systemd you made changes
#   systemctl daemon-reload
#
# - Enable and start the timer (so no reboot is needed):
#   systemctl enable --now lynis.timer
#
#################################################################################

[Unit]
Description=Daily timer for the Lynis security audit and vulnerability scanner

[Timer]
OnCalendar=daily
RandomizedDelaySec=1800
Persistent=false

[Install]
WantedBy=timers.target

#EOF
TIMER_UNIT
    ${SUDO} chmod 644 "${timer_path}"

    print_info "Reloading systemd units..."
    if ! ${SUDO} systemctl daemon-reload; then
        print_error "Failed to reload systemd units."
        exit 1
    fi

    print_info "Enabling and starting lynis.timer..."
    if ${SUDO} systemctl enable --now lynis.timer; then
        print_success "Daily Lynis timer enabled (systemctl enable --now lynis.timer)."
    else
        print_error "Failed to enable lynis.timer. Please inspect systemctl output."
        exit 1
    fi
}

#==============================================================================
# First Audit
#==============================================================================

run_first_audit() {
    print_header "Running First Audit"
    
    print_info "Starting Lynis audit (this may take a few minutes)..."
    if ${SUDO} lynis audit system --upload --quick; then
        print_success "First audit completed successfully!"
    else
        print_error "Audit failed. Please check the output above for errors."
        exit 1
    fi
}

#==============================================================================
# Main Function
#==============================================================================

main() {
    show_overview
    check_prerequisites
    setup_ssl_certificate
    install_packages
    setup_lynis_profile
    setup_host_identifiers
    configure_lynis
    install_plugins
    setup_daily_reports
    run_first_audit
    
    print_header "Enrollment Complete"
    echo "Your system has been successfully enrolled with TrikuSec!"
    echo "Lynis audits will be automatically uploaded to: ${TRIKUSEC_LYNIS_UPLOAD_SERVER}"
    echo ""
}

#==============================================================================
# Script Entry Point
#==============================================================================

main "$@"

