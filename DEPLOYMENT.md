# VoiceVerse Production Deployment Guide

This guide provides comprehensive instructions for deploying VoiceVerse in a production environment with enterprise-grade security.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Installation Steps](#installation-steps)
4. [Database Setup and Migration](#database-setup-and-migration)
5. [HTTPS/SSL Configuration](#httpsssl-configuration)
6. [Nginx Reverse Proxy Setup](#nginx-reverse-proxy-setup)
7. [Security Configuration](#security-configuration)
8. [Systemd Service Setup](#systemd-service-setup)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)
10. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Specifications
- **OS:** Ubuntu 20.04 LTS / Debian 11+ / CentOS 8+ / RHEL 8+
- **CPU:** 2 cores (4+ recommended for production)
- **RAM:** 2 GB (4+ GB recommended)
- **Disk:** 10 GB available space (+ space for audio files and logs)
- **Python:** 3.8 or higher
- **Network:** Public IP address for HTTPS access

### Required Software
- Python 3.8+
- pip (Python package manager)
- Nginx (1.18+ recommended)
- SQLite 3 (included with Python)
- Certbot (Let's Encrypt client)
- Git (for version control)

### Optional but Recommended
- UFW/firewalld (firewall)
- fail2ban (intrusion prevention)
- logrotate (log management)
- Monitoring tools (Prometheus, Grafana, etc.)

---

## Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] **Domain name** pointed to your server's public IP
- [ ] **DNS A record** configured (e.g., `voiceverse.yourdomain.com`)
- [ ] **Server access** via SSH with sudo privileges
- [ ] **Firewall rules** reviewed (ports 80, 443, 22)
- [ ] **OpenAI API key** (for TTS functionality)
- [ ] **Backup strategy** planned
- [ ] **SSL certificate** approach decided (Let's Encrypt recommended)
- [ ] **Environment secrets** management solution

---

## Installation Steps

### 1. System Update and Dependencies

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# OR
sudo dnf update -y  # CentOS/RHEL

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git

# Install optional security tools
sudo apt install -y ufw fail2ban
```

### 2. Create Application User

```bash
# Create dedicated user (security best practice)
sudo useradd -m -s /bin/bash voiceverse
sudo usermod -aG www-data voiceverse  # Add to web server group
```

### 3. Clone Application

```bash
# Switch to application user
sudo su - voiceverse

# Clone repository to /var/www/voiceverse
sudo mkdir -p /var/www/voiceverse
sudo chown voiceverse:voiceverse /var/www/voiceverse
cd /var/www/voiceverse

# Clone your repository
git clone https://github.com/yourusername/voiceverse.git .

# Or upload files via SCP/SFTP
```

### 4. Python Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "import flask; print('Flask version:', flask.__version__)"
```

### 5. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Generate strong SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env

# Generate IP_HASH_SALT
python3 -c "import secrets; print('IP_HASH_SALT=' + secrets.token_urlsafe(32))" >> .env

# Edit .env with your configuration
nano .env
```

**Required .env Configuration:**
```bash
# Flask Security
SECRET_KEY=<generated-secret-key>
IP_HASH_SALT=<generated-salt>

# OpenAI API
OPENAI_API_KEY=<your-api-key>

# Application Settings
DEBUG=false
HOST=127.0.0.1  # Only listen on localhost (Nginx will proxy)
PORT=5000

# HTTPS (Nginx handles SSL termination)
USE_HTTPS=false  # Flask doesn't need HTTPS when behind Nginx
SECURE_COOKIES=true  # Still require secure cookies

# Session Security
SESSION_LIFETIME=1800  # 30 minutes
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Strict
```

---

## Database Setup and Migration

### 1. Create Database Directory

```bash
# Create data directory
mkdir -p /var/www/voiceverse/data
chmod 750 /var/www/voiceverse/data
```

### 2. Initialize Database

```bash
# Run database schema creation
cd /var/www/voiceverse
source venv/bin/activate
python3 -c "from database import Database; db = Database(); print('Database initialized')"
```

### 3. Set Database Permissions

```bash
# Set correct ownership and permissions
sudo chown voiceverse:voiceverse /var/www/voiceverse/data/voiceverse.db
chmod 640 /var/www/voiceverse/data/voiceverse.db
```

---

## HTTPS/SSL Configuration

### Option 1: Let's Encrypt (Recommended)

Let's Encrypt provides free, automated SSL certificates trusted by all browsers.

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate (interactive)
sudo certbot --nginx -d voiceverse.yourdomain.com

# Or non-interactive
sudo certbot --nginx -d voiceverse.yourdomain.com --non-interactive --agree-tos --email admin@yourdomain.com

# Verify certificate
sudo certbot certificates

# Test auto-renewal
sudo certbot renew --dry-run
```

**Certificate Auto-Renewal:**

Certbot automatically creates a systemd timer for renewal:

```bash
# Check renewal timer
sudo systemctl status certbot.timer

# Manual renewal (if needed)
sudo certbot renew
```

### Option 2: Commercial SSL Certificate

If using a commercial certificate:

```bash
# Place certificate files
sudo mkdir -p /etc/ssl/voiceverse
sudo cp fullchain.pem /etc/ssl/voiceverse/
sudo cp privkey.pem /etc/ssl/voiceverse/

# Set permissions
sudo chmod 600 /etc/ssl/voiceverse/privkey.pem
sudo chmod 644 /etc/ssl/voiceverse/fullchain.pem

# Update Nginx configuration to point to these files
```

### Option 3: Self-Signed (Development/Testing Only)

**WARNING:** Never use self-signed certificates in production!

```bash
cd /var/www/voiceverse
mkdir -p certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout certs/dev-key.pem \
    -out certs/dev-cert.pem \
    -subj "/CN=localhost"
```

---

## Nginx Reverse Proxy Setup

### 1. Install and Configure Nginx

```bash
# Install Nginx
sudo apt install -y nginx

# Copy example configuration
sudo cp nginx.conf.example /etc/nginx/sites-available/voiceverse

# Edit configuration with your domain
sudo nano /etc/nginx/sites-available/voiceverse
```

**Update the following in nginx.conf:**
- Replace `yourdomain.com` with your actual domain
- Verify certificate paths match your Let's Encrypt or commercial cert locations
- Adjust proxy_pass port if Flask runs on different port

### 2. Enable Site

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/voiceverse /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### 3. Firewall Configuration

```bash
# Configure UFW (Ubuntu/Debian)
sudo ufw allow 'Nginx Full'  # Allow HTTP and HTTPS
sudo ufw allow OpenSSH  # Keep SSH access
sudo ufw enable

# Or firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

---

## Security Configuration

### 1. Application Security

Ensure `.env` has these production settings:

```bash
DEBUG=false
SECURE_COOKIES=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Strict
SESSION_LIFETIME=1800
```

### 2. File Permissions

```bash
# Set correct ownership
sudo chown -R voiceverse:www-data /var/www/voiceverse

# Set directory permissions (750: owner rwx, group rx, other none)
find /var/www/voiceverse -type d -exec chmod 750 {} \;

# Set file permissions (640: owner rw, group r, other none)
find /var/www/voiceverse -type f -exec chmod 640 {} \;

# Protect sensitive files
chmod 600 /var/www/voiceverse/.env
chmod 600 /var/www/voiceverse/data/voiceverse.db

# Audio files directory (if serving through Flask)
mkdir -p /var/www/voiceverse/saved_audio
chmod 750 /var/www/voiceverse/saved_audio
```

### 3. Fail2ban Configuration

Protect against brute-force attacks:

```bash
# Create Fail2ban filter
sudo nano /etc/fail2ban/filter.d/voiceverse.conf
```

Add filter:

```ini
[Definition]
failregex = AUTH_FAILURE.*"ip": "<HOST>"
ignoreregex =
```

Create jail:

```bash
sudo nano /etc/fail2ban/jail.d/voiceverse.conf
```

Add jail configuration:

```ini
[voiceverse]
enabled = true
port = http,https
filter = voiceverse
logpath = /var/www/voiceverse/logs/security_audit.log
maxretry = 5
bantime = 3600
findtime = 600
```

Restart Fail2ban:

```bash
sudo systemctl restart fail2ban
sudo fail2ban-client status voiceverse
```

### 4. Log Rotation

Configure logrotate to prevent log files from growing indefinitely:

```bash
sudo nano /etc/logrotate.d/voiceverse
```

Add configuration:

```
/var/www/voiceverse/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 640 voiceverse voiceverse
    sharedscripts
    postrotate
        systemctl reload voiceverse > /dev/null 2>&1 || true
    endscript
}
```

---

## Systemd Service Setup

### 1. Create Service File

```bash
sudo nano /etc/systemd/system/voiceverse.service
```

Add service configuration:

```ini
[Unit]
Description=VoiceVerse TTS Application
After=network.target
Documentation=https://github.com/yourusername/voiceverse

[Service]
Type=simple
User=voiceverse
Group=voiceverse
WorkingDirectory=/var/www/voiceverse
Environment="PATH=/var/www/voiceverse/venv/bin"
ExecStart=/var/www/voiceverse/venv/bin/python3 tts_app19.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=voiceverse

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/www/voiceverse/data /var/www/voiceverse/logs /var/www/voiceverse/saved_audio

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable voiceverse

# Start service
sudo systemctl start voiceverse

# Check status
sudo systemctl status voiceverse

# View logs
sudo journalctl -u voiceverse -f
```

### 3. Service Management Commands

```bash
# Start service
sudo systemctl start voiceverse

# Stop service
sudo systemctl stop voiceverse

# Restart service
sudo systemctl restart voiceverse

# Reload configuration (no downtime)
sudo systemctl reload voiceverse

# View status
sudo systemctl status voiceverse

# View logs
sudo journalctl -u voiceverse -n 100  # Last 100 lines
sudo journalctl -u voiceverse -f      # Follow logs
sudo journalctl -u voiceverse --since "1 hour ago"
```

---

## Monitoring and Maintenance

### 1. Health Checks

Monitor application health:

```bash
# Check if service is running
sudo systemctl is-active voiceverse

# Check Nginx status
sudo systemctl status nginx

# Check SSL certificate expiry
sudo certbot certificates

# Test HTTPS connection
curl -I https://voiceverse.yourdomain.com/health
```

### 2. Log Monitoring

**Security Audit Logs:**
```bash
# View security events
tail -f /var/www/voiceverse/logs/security_audit.log

# Search for failed logins
grep "AUTH_FAILURE" /var/www/voiceverse/logs/security_audit.log

# Count authentication attempts by IP
grep "AUTH" /var/www/voiceverse/logs/security_audit.log | jq -r '.ip' | sort | uniq -c | sort -rn
```

**Application Logs:**
```bash
# View Flask application logs
sudo journalctl -u voiceverse -f

# View Nginx access logs
sudo tail -f /var/log/nginx/voiceverse_access.log

# View Nginx error logs
sudo tail -f /var/log/nginx/voiceverse_error.log
```

### 3. Database Maintenance

```bash
# Check database size
du -h /var/www/voiceverse/data/voiceverse.db

# Optimize database (SQLite vacuum)
sqlite3 /var/www/voiceverse/data/voiceverse.db "VACUUM;"

# Backup database
cp /var/www/voiceverse/data/voiceverse.db /var/www/voiceverse/backups/voiceverse-$(date +%Y%m%d).db
```

### 4. Automated Backups

Create backup script:

```bash
sudo nano /usr/local/bin/voiceverse-backup.sh
```

Add script:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/voiceverse"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp /var/www/voiceverse/data/voiceverse.db $BACKUP_DIR/db-$DATE.db

# Backup audio files
tar -czf $BACKUP_DIR/audio-$DATE.tar.gz /var/www/voiceverse/saved_audio

# Backup configuration
cp /var/www/voiceverse/.env $BACKUP_DIR/env-$DATE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Make executable and schedule:

```bash
sudo chmod +x /usr/local/bin/voiceverse-backup.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/voiceverse-backup.sh >> /var/log/voiceverse-backup.log 2>&1
```

### 5. Updates and Patches

```bash
# Pull latest code
cd /var/www/voiceverse
sudo -u voiceverse git pull

# Update dependencies
sudo -u voiceverse source venv/bin/activate
sudo -u voiceverse pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart voiceverse
```

---

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
sudo journalctl -u voiceverse -n 50 --no-pager
```

**Common issues:**
- **Port already in use:** Check if another process is using port 5000
  ```bash
  sudo lsof -i :5000
  ```
- **Permission denied:** Check file ownership and permissions
  ```bash
  ls -la /var/www/voiceverse
  ```
- **Missing dependencies:** Reinstall requirements
  ```bash
  source venv/bin/activate && pip install -r requirements.txt
  ```

### HTTPS Not Working

**Check Nginx configuration:**
```bash
sudo nginx -t
```

**Check certificate:**
```bash
sudo certbot certificates
openssl s_client -connect voiceverse.yourdomain.com:443 -servername voiceverse.yourdomain.com
```

**Check firewall:**
```bash
sudo ufw status  # Ubuntu
sudo firewall-cmd --list-all  # CentOS
```

### Database Errors

**Check database permissions:**
```bash
ls -l /var/www/voiceverse/data/voiceverse.db
```

**Check database integrity:**
```bash
sqlite3 /var/www/voiceverse/data/voiceverse.db "PRAGMA integrity_check;"
```

**Restore from backup:**
```bash
sudo systemctl stop voiceverse
cp /var/backups/voiceverse/db-YYYYMMDD.db /var/www/voiceverse/data/voiceverse.db
sudo chown voiceverse:voiceverse /var/www/voiceverse/data/voiceverse.db
sudo systemctl start voiceverse
```

### High Memory Usage

**Check process memory:**
```bash
ps aux | grep python3
```

**Restart service:**
```bash
sudo systemctl restart voiceverse
```

**Adjust worker processes** (if using Gunicorn):
```bash
# In .env or systemd service file
WORKERS=2  # Reduce number of workers
```

### Logs Not Rotating

**Check logrotate configuration:**
```bash
sudo logrotate -d /etc/logrotate.d/voiceverse  # Dry run
sudo logrotate -f /etc/logrotate.d/voiceverse  # Force rotation
```

### SSL Certificate Expiry

**Renew manually:**
```bash
sudo certbot renew
sudo systemctl reload nginx
```

**Check auto-renewal:**
```bash
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
```

---

## Security Checklist

Before going live, verify:

- [x] All passwords are hashed (bcrypt)
- [x] Database uses parameterized queries
- [x] File access requires authentication and ownership check
- [x] Rate limiting enabled on sensitive endpoints
- [x] HTTPS enforced (HTTP redirects to HTTPS)
- [x] Security headers configured (HSTS, CSP, etc.)
- [x] Debug mode disabled (`DEBUG=false`)
- [x] Secrets in environment variables (not in code)
- [x] Secure cookies enabled (`SECURE_COOKIES=true`)
- [x] Security logging covers all critical events
- [x] Logs don't contain PII or passwords
- [x] Firewall configured (only ports 80, 443, 22 open)
- [x] Fail2ban configured for brute-force protection
- [x] Regular backups scheduled
- [x] SSL certificate auto-renewal tested
- [x] File permissions correctly set
- [x] Service runs as non-root user

---

## Performance Optimization

### Database Optimization

```sql
-- Run these commands in SQLite console
PRAGMA journal_mode=WAL;  -- Write-Ahead Logging for better concurrency
PRAGMA synchronous=NORMAL;  -- Balance between safety and performance
ANALYZE;  -- Update query planner statistics
```

### Nginx Caching

Add to nginx.conf:

```nginx
# Cache static files
location /static {
    expires 30d;
    add_header Cache-Control "public, immutable";
}

# Cache audio files briefly
location /saved_audio {
    expires 1h;
    add_header Cache-Control "private, must-revalidate";
}
```

### Connection Pooling

For high-traffic scenarios, consider using Gunicorn with multiple workers:

```bash
pip install gunicorn
```

Update systemd service:

```ini
ExecStart=/var/www/voiceverse/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 wsgi:app
```

---

## Getting Help

- **Documentation:** Check README.md and SECURITY.md
- **Logs:** Always check logs first (`journalctl -u voiceverse`)
- **Issues:** Report bugs on GitHub
- **Security Issues:** Report privately to security@yourdomain.com

---

## License

This deployment guide is part of the VoiceVerse project. See LICENSE file for details.
