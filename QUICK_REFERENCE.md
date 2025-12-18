# ⚡ VoiceVerse Quick Reference Card

**Essential Commands Cheat Sheet**

---

## 🚀 Getting Started (First Time)

```bash
# 1. Setup environment
./scripts/setup_dev.sh

# 2. Install aliases (optional but recommended)
./scripts/install_aliases.sh
source ~/.zshrc

# 3. Start application
vv-start  # or ./scripts/app_manager.sh start
```

---

## 📱 Daily Commands

### With Aliases (Recommended)

```bash
vv-start      # Start the app
vv-stop       # Stop the app
vv-restart    # Restart the app
vv-status     # Check status
vv-logs       # View logs
vv-health     # Health check
vv-backup     # Backup database
```

### Without Aliases

```bash
./scripts/app_manager.sh start
./scripts/app_manager.sh stop
./scripts/app_manager.sh restart
./scripts/app_manager.sh status
./scripts/app_manager.sh logs
./scripts/health_check.sh
./scripts/backup_db.sh
```

---

## 🔧 Common Tasks

### Check Everything
```bash
vv-health     # Comprehensive health check
vv-status     # Quick status
```

### Deploy Updates
```bash
vv-deploy     # Auto: pull + backup + restart + verify
```

### Manage Database
```bash
vv-backup                 # Backup now
vv-restore                # List backups
vv-restore <backup-file>  # Restore specific backup
```

### Cleanup
```bash
vv-cleanup    # Clean old files (interactive)
```

### View Logs
```bash
vv-logs       # Tail logs (Ctrl+C to exit)
tail -100 app.log         # Last 100 lines
grep "error" app.log      # Find errors
```

---

## 🆘 Emergency Commands

### App Not Responding
```bash
vv-health              # Diagnose
vv-stop                # Force stop
lsof -ti:5000 | xargs kill -9    # Kill port 5000
vv-start               # Start fresh
```

### Database Issues
```bash
vv-restore             # List backups
vv-restore <backup>    # Restore backup
```

### Out of Space
```bash
vv-cleanup             # Clean files
du -sh saved_audio/    # Check audio size
du -sh backups/        # Check backup size
```

---

## 📊 Status Codes

### Health Check Exit Codes
- `0` = ✅ All systems operational
- `1` = ⚠️  Warnings detected
- `2` = ❌ Critical failures

---

## 📁 Important Files

```bash
app.log               # Application logs
voiceverse.db         # Main database
.env                  # Environment config
backups/              # Database backups
saved_audio/          # Generated audio files
scripts/              # Automation scripts
```

---

## 🔗 URLs

- **Application**: https://127.0.0.1:5000
- **Settings**: https://127.0.0.1:5000/settings
- **Analytics**: https://127.0.0.1:5000/analytics

---

## 💡 Pro Tips

1. **Daily backup**: `vv-backup` (takes 10 seconds)
2. **Weekly cleanup**: `vv-cleanup` (frees space)
3. **Before deploy**: `vv-backup` (safety first)
4. **Check health**: `vv-health` (catch issues early)
5. **Use aliases**: Saves ~3 seconds per command

---

## 📞 Help

```bash
vv-info                      # Show all commands
./scripts/app_manager.sh help
cat AUTOMATION_GUIDE.md      # Full documentation
cat AUTOMATION_ROADMAP.md    # Strategy & roadmap
```

---

**Shortcut to this file**:
```bash
cat QUICK_REFERENCE.md
```

---

*Last Updated: October 27, 2025*
