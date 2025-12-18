#!/usr/bin/env bash
# VoiceVerse Production Deployment Script
# This script automates the deployment of VoiceVerse to a production server
#
# Usage: sudo bash scripts/deploy.sh
#
# Prerequisites:
# - Ubuntu 20.04/22.04 LTS or Debian 11/12
# - Root/sudo access
# - Domain name configured (A record pointing to server IP)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
DOMAIN="${DOMAIN:-}"
APP_USER="${APP_USER:-voiceverse}"
APP_DIR="${APP_DIR:-/var/www/voiceverse}"
PYTHON_VERSION="3.11"

# Functions
print_header() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root or with sudo"
        exit 1
    fi
}

prompt_domain() {
    if [ -z "$DOMAIN" ]; then
        echo -n "Enter your domain name (e.g., voiceverse.com): "
        read DOMAIN
        if [ -z "$DOMAIN" ]; then
            print_error "Domain name is required"
            exit 1
        fi
    fi
}

# Step 1: System Update and Dependencies
install_dependencies() {
    print_header "Step 1: Installing System Dependencies"

    apt-get update
    apt-get upgrade -y

    apt-get install -y \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-venv \
        python3-pip \
        nginx \
        certbot \
        python3-certbot-nginx \
        fail2ban \
        ufw \
        git \
        curl \
        sqlite3 \
        supervisor

    print_success "System dependencies installed"
}

# Step 2: Create Application User
create_app_user() {
    print_header "Step 2: Creating Application User"

    if id "$APP_USER" &>/dev/null; then
        print_warning "User $APP_USER already exists"
    else
        useradd -m -s /bin/bash "$APP_USER"
        print_success "User $APP_USER created"
    fi
}

# Step 3: Setup Application Directory
setup_app_directory() {
    print_header "Step 3: Setting Up Application Directory"

    mkdir -p "$APP_DIR"
    mkdir -p "$APP_DIR/data"
    mkdir -p "$APP_DIR/logs"
    mkdir -p "$APP_DIR/saved_audio"

    # Copy application files (assuming running from project root)
    cp -r tts_app19.py database.py logger.py requirements.txt .env.production "$APP_DIR/"

    # Create virtual environment
    python${PYTHON_VERSION} -m venv "$APP_DIR/venv"

    # Install Python dependencies
    "$APP_DIR/venv/bin/pip" install --upgrade pip
    "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

    # Set permissions
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    chmod 750 "$APP_DIR"
    chmod 700 "$APP_DIR/data"
    chmod 700 "$APP_DIR/logs"
    chmod 750 "$APP_DIR/saved_audio"

    print_success "Application directory configured"
}

# Step 4: Configure Environment
configure_environment() {
    print_header "Step 4: Configuring Environment"

    # Copy production environment file
    cp "$APP_DIR/.env.production" "$APP_DIR/.env"

    print_warning "IMPORTANT: Update $APP_DIR/.env with:"
    print_warning "  - Your OpenAI API key"
    print_warning "  - Production SECRET_KEY and IP_HASH_SALT"
    print_warning "  - SSL certificate paths after Let's Encrypt setup"

    echo ""
    read -p "Press Enter to continue after updating .env file..."
}

# Step 5: Configure Nginx
configure_nginx() {
    print_header "Step 5: Configuring Nginx"

    cat > /etc/nginx/sites-available/voiceverse <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN} www.${DOMAIN};

    # SSL certificates (will be configured by certbot)
    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    client_max_body_size 16M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/voiceverse /etc/nginx/sites-enabled/

    # Test nginx configuration
    nginx -t

    print_success "Nginx configured"
}

# Step 6: SSL Certificate
setup_ssl() {
    print_header "Step 6: Setting Up SSL Certificate"

    # Obtain Let's Encrypt certificate
    certbot --nginx -d "${DOMAIN}" -d "www.${DOMAIN}" --non-interactive --agree-tos --email "admin@${DOMAIN}"

    # Test auto-renewal
    certbot renew --dry-run

    print_success "SSL certificate configured and auto-renewal tested"
}

# Step 7: Configure Systemd Service
configure_systemd() {
    print_header "Step 7: Configuring Systemd Service"

    cat > /etc/systemd/system/voiceverse.service <<EOF
[Unit]
Description=VoiceVerse TTS Application
After=network.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin"
ExecStart=${APP_DIR}/venv/bin/python3 tts_app19.py
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${APP_DIR}/data ${APP_DIR}/logs ${APP_DIR}/saved_audio

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable voiceverse
    systemctl start voiceverse

    print_success "Systemd service configured and started"
}

# Step 8: Configure Fail2ban
configure_fail2ban() {
    print_header "Step 8: Configuring Fail2ban"

    cat > /etc/fail2ban/jail.d/voiceverse.conf <<EOF
[voiceverse-auth]
enabled = true
port = http,https
logpath = ${APP_DIR}/logs/security_audit.log
maxretry = 5
bantime = 3600
findtime = 600
EOF

    systemctl restart fail2ban
    systemctl enable fail2ban

    print_success "Fail2ban configured"
}

# Step 9: Configure Firewall
configure_firewall() {
    print_header "Step 9: Configuring Firewall"

    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 'Nginx Full'
    ufw --force enable

    print_success "Firewall configured"
}

# Step 10: Setup Log Rotation
setup_logrotate() {
    print_header "Step 10: Setting Up Log Rotation"

    cat > /etc/logrotate.d/voiceverse <<EOF
${APP_DIR}/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ${APP_USER} ${APP_USER}
    sharedscripts
    postrotate
        systemctl reload voiceverse > /dev/null 2>&1 || true
    endscript
}
EOF

    print_success "Log rotation configured"
}

# Step 11: Setup Automated Backups
setup_backups() {
    print_header "Step 11: Setting Up Automated Backups"

    mkdir -p /var/backups/voiceverse

    cat > /usr/local/bin/voiceverse-backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/voiceverse"
APP_DIR="/var/www/voiceverse"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
sqlite3 ${APP_DIR}/data/voiceverse.db ".backup ${BACKUP_DIR}/voiceverse_${DATE}.db"

# Backup configuration
tar -czf ${BACKUP_DIR}/config_${DATE}.tar.gz -C ${APP_DIR} .env

# Keep only last 7 days of backups
find ${BACKUP_DIR} -name "voiceverse_*.db" -mtime +7 -delete
find ${BACKUP_DIR} -name "config_*.tar.gz" -mtime +7 -delete
EOF

    chmod +x /usr/local/bin/voiceverse-backup.sh

    # Add cron job for daily backups at 2 AM
    (crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/voiceverse-backup.sh") | crontab -

    print_success "Automated backups configured (daily at 2 AM)"
}

# Main deployment flow
main() {
    print_header "VoiceVerse Production Deployment"

    check_root
    prompt_domain

    install_dependencies
    create_app_user
    setup_app_directory
    configure_environment
    configure_nginx
    setup_ssl
    configure_systemd
    configure_fail2ban
    configure_firewall
    setup_logrotate
    setup_backups

    print_header "Deployment Complete!"
    print_success "VoiceVerse is now running at https://${DOMAIN}"
    print_success "Check status: systemctl status voiceverse"
    print_success "View logs: journalctl -u voiceverse -f"
    print_success "Nginx logs: tail -f /var/log/nginx/voiceverse_*.log"

    echo -e "\n${YELLOW}Post-Deployment Checklist:${NC}"
    echo "  1. Verify application is accessible at https://${DOMAIN}"
    echo "  2. Test user registration and authentication"
    echo "  3. Test TTS generation"
    echo "  4. Monitor logs for any errors"
    echo "  5. Setup monitoring alerts (recommended: UptimeRobot, Datadog, etc.)"
    echo "  6. Document your production API keys in a secure location"
}

# Run main function
main
