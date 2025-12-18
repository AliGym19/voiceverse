# VoiceVerse Production Deployment Checklist

## Pre-Deployment Preparation ✅

### Configuration Files Ready
- [x] `.env.production` - Production secrets generated
- [x] `nginx.conf.example` - Nginx configuration template
- [x] `scripts/deploy.sh` - Automated deployment script
- [x] DEPLOYMENT.md - Complete deployment guide
- [x] SECURITY.md - Security documentation
- [x] SECURITY_AUDIT_REPORT.md - Security audit results

### Security Configuration ✅
- [x] SECRET_KEY generated (64-character hex)
- [x] IP_HASH_SALT generated (URL-safe random string)
- [x] DEBUG=false
- [x] SECURE_COOKIES=true
- [x] USE_HTTPS=true
- [x] Session security configured
- [x] .gitignore protecting sensitive files

## Server Requirements

### Minimum Hardware
- **CPU:** 2 cores
- **RAM:** 2GB
- **Storage:** 20GB SSD
- **Network:** Stable internet connection

### Software Requirements
- **OS:** Ubuntu 20.04/22.04 LTS or Debian 11/12
- **Python:** 3.8+
- **Domain:** Registered domain with DNS configured
- **Access:** Root/sudo privileges

## Deployment Steps

### Option A: Automated Deployment (Recommended)

1. **Prepare Server**
   ```bash
   # On your production server
   sudo apt-get update
   sudo apt-get upgrade -y
   ```

2. **Transfer Files**
   ```bash
   # From your local machine
   scp -r /path/to/voiceverse user@your-server:/tmp/voiceverse
   ```

3. **Run Deployment Script**
   ```bash
   # On production server
   cd /tmp/voiceverse
   sudo bash scripts/deploy.sh
   ```

4. **Configure API Key**
   ```bash
   sudo nano /var/www/voiceverse/.env
   # Update OPENAI_API_KEY with your production key
   ```

5. **Restart Service**
   ```bash
   sudo systemctl restart voiceverse
   ```

### Option B: Manual Deployment

Follow the detailed steps in [DEPLOYMENT.md](DEPLOYMENT.md)

## Post-Deployment Tasks

### 1. SSL/TLS Certificate ⏳
- [ ] Domain DNS A record configured
- [ ] Let's Encrypt certificate obtained
- [ ] Auto-renewal tested
- [ ] HTTPS redirect working

**Command:**
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
sudo certbot renew --dry-run
```

### 2. Fail2ban Configuration ⏳
- [ ] Fail2ban installed
- [ ] VoiceVerse jail configured
- [ ] Service running and enabled

**Command:**
```bash
sudo systemctl status fail2ban
sudo fail2ban-client status voiceverse-auth
```

### 3. Firewall Rules ⏳
- [ ] UFW enabled
- [ ] SSH allowed (port 22)
- [ ] HTTP/HTTPS allowed (ports 80/443)
- [ ] Default deny incoming

**Command:**
```bash
sudo ufw status verbose
```

### 4. Automated Backups ⏳
- [ ] Backup script installed
- [ ] Cron job configured (daily at 2 AM)
- [ ] Backup location: `/var/backups/voiceverse`
- [ ] Tested backup restoration

**Command:**
```bash
sudo /usr/local/bin/voiceverse-backup.sh
ls -lh /var/backups/voiceverse/
```

### 5. Log Monitoring ⏳
- [ ] Application logs: `/var/www/voiceverse/logs/`
- [ ] Security logs: `/var/www/voiceverse/logs/security_audit.log`
- [ ] Nginx logs: `/var/log/nginx/voiceverse_*.log`
- [ ] Systemd journal: `journalctl -u voiceverse`

**Setup Log Monitoring:**
```bash
# Install log monitoring (optional)
sudo apt-get install logwatch
# Or use a service like Papertrail, Loggly, etc.
```

### 6. Application Health Checks ⏳
- [ ] Application accessible at https://yourdomain.com
- [ ] User registration working
- [ ] User login working
- [ ] TTS generation working
- [ ] File upload working
- [ ] Audio playback working

### 7. Security Verification ✓
- [x] Bcrypt password hashing (14 rounds)
- [x] Session management secure
- [x] Rate limiting active
- [x] Security headers configured
- [x] PII protection in logs
- [x] Input validation present

### 8. Performance Monitoring ⏳
- [ ] Setup monitoring service (UptimeRobot, Pingdom, etc.)
- [ ] Configure alerts for downtime
- [ ] Monitor resource usage (CPU, RAM, Disk)
- [ ] Set up application performance monitoring

**Recommended Tools:**
- UptimeRobot (uptime monitoring)
- Datadog/New Relic (APM)
- Sentry (error tracking)

## Production Environment Variables

Update `/var/www/voiceverse/.env` with production values:

```bash
# Required
OPENAI_API_KEY=your-production-api-key-here  # ⚠️ UPDATE THIS

# Already Configured ✓
SECRET_KEY=a949e2da20cfa47b1fa4f2efb3f69af102471fe5dbb49948de3a38378fe3350a
IP_HASH_SALT=JOhe3hjc1qU8ZTgjAL-dCHTDXaOZ6o-BhX3WRh7nD08
DEBUG=false
SECURE_COOKIES=true
USE_HTTPS=true

# Update After SSL Setup
SSL_CERT_PATH=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/yourdomain.com/privkey.pem
```

## Maintenance Commands

### Service Management
```bash
# Check status
sudo systemctl status voiceverse

# Restart service
sudo systemctl restart voiceverse

# View logs
sudo journalctl -u voiceverse -f

# Stop service
sudo systemctl stop voiceverse

# Start service
sudo systemctl start voiceverse
```

### Database Management
```bash
# Backup database
sqlite3 /var/www/voiceverse/data/voiceverse.db ".backup /tmp/backup.db"

# Check database integrity
sqlite3 /var/www/voiceverse/data/voiceverse.db "PRAGMA integrity_check;"

# View tables
sqlite3 /var/www/voiceverse/data/voiceverse.db ".tables"
```

### Nginx Management
```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo systemctl reload nginx

# View access logs
sudo tail -f /var/log/nginx/voiceverse_access.log

# View error logs
sudo tail -f /var/log/nginx/voiceverse_error.log
```

## Troubleshooting

### Application Won't Start
```bash
# Check logs
sudo journalctl -u voiceverse -n 50 --no-pager

# Check Python environment
cd /var/www/voiceverse
./venv/bin/python3 -c "import sys; print(sys.version)"

# Test manually
cd /var/www/voiceverse
./venv/bin/python3 tts_app19.py
```

### SSL Certificate Issues
```bash
# Check certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run
```

### Database Locked
```bash
# Check for active connections
sudo lsof /var/www/voiceverse/data/voiceverse.db

# Restart application
sudo systemctl restart voiceverse
```

## Security Incident Response

If you suspect a security breach:

1. **Isolate:** Immediately stop the service
   ```bash
   sudo systemctl stop voiceverse
   ```

2. **Investigate:** Check security logs
   ```bash
   sudo tail -100 /var/www/voiceverse/logs/security_audit.log
   ```

3. **Review:** Check fail2ban bans
   ```bash
   sudo fail2ban-client status voiceverse-auth
   ```

4. **Secure:** Change all secrets
   - Generate new SECRET_KEY and IP_HASH_SALT
   - Update .env file
   - Force all users to re-login (clear sessions)

5. **Report:** Document the incident in SECURITY.md

## Compliance & Best Practices

### Regular Maintenance
- [ ] Weekly: Review security logs
- [ ] Weekly: Check backup integrity
- [ ] Monthly: Update system packages
- [ ] Monthly: Review fail2ban reports
- [ ] Quarterly: Security audit
- [ ] Quarterly: Certificate renewal check (automated)

### Update Procedure
```bash
# 1. Backup
sudo /usr/local/bin/voiceverse-backup.sh

# 2. Pull latest code
cd /var/www/voiceverse
sudo -u voiceverse git pull

# 3. Update dependencies
sudo -u voiceverse ./venv/bin/pip install -r requirements.txt --upgrade

# 4. Restart
sudo systemctl restart voiceverse

# 5. Verify
curl -I https://yourdomain.com
```

## Support & Documentation

- **Full Deployment Guide:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Security Documentation:** [SECURITY.md](SECURITY.md)
- **Security Audit Report:** [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md)
- **README:** [README.md](README.md)

## Completion Status

**Local Configuration:** ✅ COMPLETE
- All secrets generated
- Configuration files ready
- Deployment scripts prepared
- Documentation complete

**Server Deployment:** ⏳ PENDING
- Requires production server
- Requires domain name
- Requires SSL certificate setup

**To Deploy:**
1. Acquire a production server (VPS, Cloud instance)
2. Purchase/configure domain name
3. Run `scripts/deploy.sh` on the server
4. Update OpenAI API key in .env
5. Complete post-deployment checklist

---

**Last Updated:** 2025-10-25
**Status:** Ready for Production Deployment
**Security Audit:** PASS
