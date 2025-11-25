#!/usr/bin/env bash


# CONFIGURATION

TRIKUSEC_LYNIS_UPLOAD_SERVER=localhost:8001
TRIKUSEC_LICENSEKEY=cb01e362-e3bfb0f0-335582a7
ignore_ssl_errors=False
overwrite_lynis_profile=False
additional_packages=rkhunter auditd
skip_tests=

function overview() {
    echo "=== TrikuSec Lynis Enrollment Script ==="
    echo "Server URL: ${TRIKUSEC_LYNIS_UPLOAD_SERVER}"
    echo "License Key: ${TRIKUSEC_LICENSEKEY}"
    echo "Ignore SSL Errors: ${ignore_ssl_errors}"
    echo "Overwrite Lynis Profile: ${overwrite_lynis_profile}"
    echo "Additional Packages: ${additional_packages}"
    echo "Skip Tests: ${skip_tests}"
}

function check_server_reachability() {
    echo "Checking server reachability..."

    # Try with SSL
    curl -s "https://${TRIKUSEC_LYNIS_UPLOAD_SERVER}" -o /dev/null
    if [ $? -ne 0 ]; then
        echo "Server is not reachable. Trying with ignore SSL errors..."
    fi

    # Try ignoring SSL errors
    curl -s "https://${TRIKUSEC_LYNIS_UPLOAD_SERVER}" -o /dev/null --insecure
    if [ $? -ne 0 ]; then
        echo "Server is not reachable. Please check the server URL."
        exit 1
    fi
}

# Print overview
overview

# Continue?
read -p "Continue? (y/n): " continue </dev/tty
if [ "$continue" != "y" ]; then
    echo "Exiting..."
    exit 1
fi

check_server_reachability

# TRIKUSEC_LYNIS_API_URL is used for certificate download and API operations
TRIKUSEC_LYNIS_UPLOAD_SERVER=localhost:8001
TRIKUSEC_CERT_TMP=/tmp/trikusec.crt
TRIKUSEC_LICENSEKEY=cb01e362-e3bfb0f0-335582a7

if [ ! -f /etc/debian_version ]; then
    echo "This script is only compatible with Debian-based systems."
    exit 1
fi

# If user is not root, use sudo if available
if [ $(id -u) -ne 0 ]; then
    if [ -x "$(command -v sudo)" ]; then
        SUDO=sudo
    else
        echo "Please run this script as root or install sudo."
        exit 1
    fi
fi


# Check if the server is reachable and has a valid certificate
curl -s "https://${TRIKUSEC_LYNIS_UPLOAD_SERVER}" -o /dev/null
if [ $? -ne 0 ]; then
    echo "Server certificate is self-signed. Adding it to the trusted certificates."
    # Check if openssl and ca-certificates are installed
    if [ ! -x "$(command -v openssl)" ] || [ ! -x "$(command -v update-ca-certificates)" ]; then
        echo "openssl or ca-certificates are not installed. Installing them..."
        ${SUDO} apt-get update && ${SUDO} apt-get install -y openssl ca-certificates
    fi
    
    openssl s_client -showcerts -connect "${TRIKUSEC_LYNIS_UPLOAD_SERVER}" </dev/null 2>/dev/null | sed -n -e '/BEGIN\ CERTIFICATE/,/END\ CERTIFICATE/ p' > ${TRIKUSEC_CERT_TMP}
    ${SUDO} cp ${TRIKUSEC_CERT_TMP} /usr/local/share/ca-certificates/trikusec.crt
    ${SUDO} update-ca-certificates
    rm -f ${TRIKUSEC_CERT_TMP}
else
    echo "Server certificate is valid."
fi


# Update and install necessary packages
${SUDO} apt-get update
${SUDO} apt-get install -y curl lynis rkhunter auditd



# Get installed Lynis version
LYNIS_VERSION=$(lynis --version)

# If a custom profile file already exists, handle per configuration
if [ -f /etc/lynis/custom.prf ]; then
    
    echo "A custom profile file already exists. Please remove it before running this script or enable overwriting in TrikuSec."
    exit 1
    
fi

# Create custom profile file if it doesn't exist
${SUDO} touch /etc/lynis/custom.prf

# Check and generate host identifiers if needed
# Host identifiers (hostid and hostid2) are used by Lynis to uniquely identify systems
# Reference: https://cisofy.com/documentation/lynis/
# In some environments (e.g., Docker containers), host identifiers may not be automatically generated
# If they are empty, we need to generate them manually
echo "Checking host identifiers..."
HOSTIDS_OUTPUT=$(lynis show hostids 2>/dev/null || echo "")
# Extract hostid and hostid2 values from the output
HOSTID_VALUE=$(echo "$HOSTIDS_OUTPUT" | grep -E "^hostid[[:space:]]*:" | sed 's/.*:[[:space:]]*//' | tr -d '[:space:]' || echo "")
HOSTID2_VALUE=$(echo "$HOSTIDS_OUTPUT" | grep -E "^hostid2[[:space:]]*:" | sed 's/.*:[[:space:]]*//' | tr -d '[:space:]' || echo "")

if [ -z "$HOSTID_VALUE" ] || [ -z "$HOSTID2_VALUE" ]; then
    echo "Host identifiers are empty. Generating new identifiers..."
    # Create custom profile file if it doesn't exist (required for lynis configure settings)
    ${SUDO} mkdir -p /etc/lynis
    ${SUDO} touch /etc/lynis/custom.prf
    # Generate host identifiers using random data
    # hostid: 40 characters (SHA1 hash)
    # hostid2: 64 characters (SHA256 hash)
    # Reference: https://cisofy.com/documentation/lynis/
    ${SUDO} lynis configure settings hostid=$(head -c 64 /dev/random | sha1sum | awk '{print $1}'):hostid2=$(head -c 64 /dev/random | sha256sum | awk '{print $1}')
    echo "Host identifiers generated successfully."
else
    echo "Host identifiers already exist."
fi


#
# Configure Lynis custom configuration by command
#
# Configure upload settings: enable upload, set license key, and upload server endpoint

# Bugfix: lynis configure does not work correctly with :port in the upload server URL
# so we need to set the configuration manually
echo "upload-server=${TRIKUSEC_LYNIS_UPLOAD_SERVER}/api/lynis" >> /etc/lynis/custom.prf

${SUDO} lynis configure settings upload=yes:license-key=${TRIKUSEC_LICENSEKEY}:upload-server=${TRIKUSEC_LYNIS_UPLOAD_SERVER}/api/lynis auditor=TrikuSec


# If lynis version is older than 3.0.0, add skip-test=CRYP-7902 to the custom profile
# Extract major version number for comparison
LYNIS_MAJOR=$(echo "$LYNIS_VERSION" | awk -F. '{print $1}')
# Add test skip if major version is less than 3 (i.e., version < 3.0.0)
if [ "$LYNIS_MAJOR" -lt 3 ]; then
    ${SUDO} lynis configure settings skip-test=CRYP-7902
fi


# Install optional Lynis plugins defined in TrikuSec (https://cisofy.com/documentation/lynis/plugins/)

echo "Installing Lynis plugins configured in TrikuSec..."
PLUGIN_DIR=$(lynis show plugindir 2>/dev/null | grep -Eo '/[^[:space:]]+' | head -n1)
if [ -z "$PLUGIN_DIR" ]; then
    PLUGIN_DIR="/var/lib/lynis/plugins"
    echo "Falling back to default plugin directory: ${PLUGIN_DIR}"
fi
${SUDO} mkdir -p "${PLUGIN_DIR}"
PLUGIN_URLS=(

"https://raw.githubusercontent.com/TrikuSec/trikusec/refs/heads/main/trikusec-lynis-plugin/plugin_trikusec_phase1"

)
for PLUGIN_URL in "${PLUGIN_URLS[@]}"; do
    echo "Downloading plugin from ${PLUGIN_URL}"
    TMP_PLUGIN=$(mktemp)
    if curl -fsSL "${PLUGIN_URL}" -o "${TMP_PLUGIN}"; then
        PLUGIN_BASENAME=$(basename "${PLUGIN_URL}")
        ${SUDO} mv "${TMP_PLUGIN}" "${PLUGIN_DIR}/${PLUGIN_BASENAME}"
        ${SUDO} chmod 755 "${PLUGIN_DIR}/${PLUGIN_BASENAME}"
        echo "Installed Lynis plugin ${PLUGIN_BASENAME} into ${PLUGIN_DIR}"

        # Set right permissions for the plugin
        ${SUDO} chmod 644 "${PLUGIN_DIR}/${PLUGIN_BASENAME}"
        echo "Set permissions for ${PLUGIN_BASENAME} to 644"

        # Get plugin name from the plugin file
        # #PLUGIN_NAME=pluginname
        PLUGIN_NAME=$(grep -Eo '# PLUGIN_NAME=.*' "${PLUGIN_DIR}/${PLUGIN_BASENAME}" | sed 's/# PLUGIN_NAME=//')

        # Enable the plugin in the custom profile
        ${SUDO} lynis configure settings "plugin=${PLUGIN_NAME}"
        echo "Enabled ${PLUGIN_NAME} plugin in custom profile"
    else
        echo "Failed to download Lynis plugin from ${PLUGIN_URL}. Aborting."
        rm -f "${TMP_PLUGIN}"
        exit 1
    fi
done





# First audit
lynis audit system --upload --quick

