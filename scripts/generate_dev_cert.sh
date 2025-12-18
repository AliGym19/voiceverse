#!/bin/bash
#
# Generate self-signed certificate for development
# Valid for 365 days
#
# Usage: ./scripts/generate_dev_cert.sh

CERT_DIR="certs"
DAYS_VALID=365

echo "==================================================================="
echo "  VoiceVerse Development Certificate Generator"
echo "==================================================================="
echo ""

# Create certificate directory
echo "Creating certificate directory..."
mkdir -p $CERT_DIR

# Generate private key
echo "Generating private key (2048-bit RSA)..."
openssl genrsa -out $CERT_DIR/dev-key.pem 2048

# Generate self-signed certificate
echo "Generating self-signed certificate (valid for $DAYS_VALID days)..."
openssl req -new -x509 -key $CERT_DIR/dev-key.pem \
    -out $CERT_DIR/dev-cert.pem \
    -days $DAYS_VALID \
    -subj "/C=US/ST=Development/L=Local/O=VoiceVerse/CN=localhost"

# Set appropriate permissions
echo "Setting file permissions..."
chmod 600 $CERT_DIR/dev-key.pem
chmod 644 $CERT_DIR/dev-cert.pem

echo ""
echo "==================================================================="
echo "  Certificate generation complete!"
echo "==================================================================="
echo ""
echo "Files created:"
echo "  - $CERT_DIR/dev-key.pem  (private key)"
echo "  - $CERT_DIR/dev-cert.pem (certificate)"
echo ""
echo "Certificate details:"
openssl x509 -in $CERT_DIR/dev-cert.pem -noout -subject -dates
echo ""
echo "WARNING: This is a self-signed certificate for DEVELOPMENT ONLY."
echo "         For production, use Let's Encrypt or a trusted CA."
echo ""
echo "To use HTTPS in development:"
echo "  1. Update your .env file with:"
echo "     USE_HTTPS=true"
echo "     SSL_CERT_PATH=certs/dev-cert.pem"
echo "     SSL_KEY_PATH=certs/dev-key.pem"
echo ""
echo "  2. Restart the application"
echo ""
echo "  3. Access at https://localhost:5000"
echo "     (You'll need to accept the browser security warning)"
echo ""
echo "==================================================================="
