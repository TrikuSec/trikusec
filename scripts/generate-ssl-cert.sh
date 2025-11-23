#!/bin/bash
# Generate self-signed SSL certificates for development

CERT_DIR="${DJANGO_SSL_CERT_DIR:-/app/certs}"
CERT_FILE="${CERT_DIR}/cert.pem"
KEY_FILE="${CERT_DIR}/key.pem"

mkdir -p "$CERT_DIR"

if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo "Generating self-signed SSL certificate..."
    openssl req -x509 -newkey rsa:4096 -nodes \
        -out "$CERT_FILE" \
        -keyout "$KEY_FILE" \
        -days 365 \
        -subj "/CN=${SSL_CN:-localhost}"
    echo "SSL certificate generated at $CERT_DIR"
else
    echo "SSL certificate already exists at $CERT_DIR"
fi



