#!/bin/sh

CERT_DIR="/etc/nginx/certs"
CERT_FILE="$CERT_DIR/cert.pem"
KEY_FILE="$CERT_DIR/key.pem"

# Resolve CN from env var, defaulting to localhost
CERT_SUBJ_CN="${NGINX_CERT_CN:-localhost}"
SUBJECT="/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=${CERT_SUBJ_CN}"

# Create the certificates directory if it doesn't exist
mkdir -p "$CERT_DIR"

# Generate certificates if they do not exist
if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo "Generating self-signed certificates for CN=${CERT_SUBJ_CN}..."

    # Check if openssl is available
    if ! command -v openssl >/dev/null 2>&1; then
        echo "ERROR: openssl is not installed. Cannot generate certificates."
        exit 1
    fi

    openssl req -new -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -subj "$SUBJECT"

    if [ $? -eq 0 ] && [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
        echo "Certificates generated successfully at $CERT_DIR/"
    else
        echo "ERROR: Failed to generate certificates."
        exit 1
    fi
else
    echo "Certificates already exist at $CERT_DIR/"
fi

# Execute the original Nginx entrypoint
exec "$@"
