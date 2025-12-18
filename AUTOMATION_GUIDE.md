# 🤖 VoiceVerse Automation Guide

**Complete automation toolkit for VoiceVerse TTS Application**

Created: October 27, 2025
Status: ✅ Production Ready
Scripts: 9 automation tools

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Scripts Overview](#scripts-overview)
- [Installation](#installation)
- [Usage Examples](#usage-examples)
- [Time Savings](#time-savings)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### 1. Set Up Development Environment

```bash
# First time setup
./scripts/setup_dev.sh
```

This will:
- Create virtual environment
- Install all dependencies
- Create .env template
- Set up required directories

### 2. Install Command Aliases (Optional but Recommended)

```bash
# Add convenient shortcuts to your shell
./scripts/install_aliases.sh
source ~/.zshrc  # or ~/.bash_profile
```

Now you can use short commands like:
- `vv-start` instead of `./scripts/app_manager.sh start`
- `vv-status` instead of `./scripts/app_manager.sh status`
- `vv-logs` instead of `./scripts/app_manager.sh logs`

### 3. Start the Application

```bash
# With aliases
vv-start

# Without aliases
./scripts/app_manager.sh start
```

---

## 📦 Scripts Overview

### 🎯 **HIGH PRIORITY** (Use Daily)

#### 1. **app_manager.sh** - Application Management
**Purpose**: Start, stop, restart, and monitor your application

**Commands**:
```bash
./scripts/app_manager.sh start     # Start the app
./scripts/app_manager.sh stop      # Stop the app
./scripts/app_manager.sh restart   # Restart the app
./scripts/app_manager.sh status    # Detailed status check
./scripts/app_manager.sh logs      # Tail logs in real-time
```

**Features**:
- ✅ PID tracking for process management
- ✅ Automatic port conflict detection
- ✅ Memory and CPU monitoring
- ✅ Uptime tracking
- ✅ Log preview on start

**Time Saved**: ~5 minutes per restart (vs manual process killing)

---

#### 2. **health_check.sh** - System Health Monitoring
**Purpose**: Comprehensive health check of entire system

**Usage**:
```bash
./scripts/health_check.sh
```

**Checks**:
- ✅ Application process status
- ✅ Memory and CPU usage
- ✅ Network connectivity
- ✅ HTTP response time
- ✅ Database accessibility
- ✅ Disk space
- ✅ Required directories
- ✅ Environment configuration
- ✅ Backup status
- ✅ Log file size
- ✅ Audio file count

**Exit Codes**:
- `0` = All systems operational
- `1` = Healthy with warnings
- `2` = Critical issues detected

**Time Saved**: ~3 minutes per check (vs manual verification)

---

#### 3. **backup_db.sh** - Database Backup
**Purpose**: Automatic database backup with versioning

**Usage**:
```bash
./scripts/backup_db.sh
```

**Features**:
- ✅ Timestamped backups
- ✅ SHA256 checksum verification
- ✅ Automatic cleanup (keeps 90 days)
- ✅ Backup statistics
- ✅ Restoration instructions

**Backup Location**: `backups/voiceverse_backup_YYYYMMDD_HHMMSS.db`

**Retention**:
- Last 7 days: All backups
- Last 90 days: Weekly backups
- Older: Monthly backups

**Time Saved**: ~2 minutes per backup (automated vs manual copy)

---

#### 4. **restore_db.sh** - Database Restoration
**Purpose**: Restore database from backup with safety checks

**Usage**:
```bash
# List available backups
./scripts/restore_db.sh

# Restore specific backup
./scripts/restore_db.sh voiceverse_backup_20251027_120000.db
```

**Features**:
- ✅ Lists all available backups
- ✅ Shows backup date and size
- ✅ Verifies backup integrity
- ✅ Checks if app is running
- ✅ Backs up current DB before restore
- ✅ Confirmation prompts

**Safety**:
- Creates pre-restore backup automatically
- Prevents restore while app is running
- Verifies checksums before restoration

**Time Saved**: ~5 minutes per restore (with safety checks)

---

### 🔧 **MEDIUM PRIORITY** (Use Weekly/As Needed)

#### 5. **quick_deploy.sh** - Rapid Deployment
**Purpose**: Pull latest code and deploy in one command

**Usage**:
```bash
./scripts/quick_deploy.sh
```

**Steps**:
1. ✅ Check git status
2. ✅ Backup database
3. ✅ Pull latest code
4. ✅ Show what changed
5. ✅ Update dependencies
6. ✅ Run migrations
7. ✅ Restart application
8. ✅ Verify deployment

**Features**:
- Warns about uncommitted changes
- Shows commit diff
- Handles migration failures
- Verifies app is responding

**Time Saved**: ~10 minutes per deployment (vs manual steps)

---

#### 6. **cleanup.sh** - File System Cleanup
**Purpose**: Clean up old files, logs, and temporary data

**Usage**:
```bash
# Interactive mode (recommended)
./scripts/cleanup.sh

# Force mode (no prompts)
./scripts/cleanup.sh --force
```

**Cleans**:
- ✅ Python cache files (`__pycache__`, `*.pyc`)
- ✅ Test audio files (`*test*.mp3`)
- ✅ Old audio files (>30 days)
- ✅ Large log files (>1MB)
- ✅ Old backups (>90 days)
- ✅ Temporary files (`*.tmp`, `*.bak`)
- ✅ Empty directories

**Features**:
- Interactive prompts for each category
- Shows size before deletion
- Reports total space freed
- Safe defaults

**Time Saved**: ~5 minutes per cleanup

---

#### 7. **setup_dev.sh** - Development Environment Setup
**Purpose**: One-command development environment setup

**Usage**:
```bash
./scripts/setup_dev.sh
```

**Steps**:
1. ✅ Check Python installation
2. ✅ Create virtual environment
3. ✅ Activate venv
4. ✅ Upgrade pip
5. ✅ Install dependencies
6. ✅ Setup .env file
7. ✅ Create directories
8. ✅ Check database

**Perfect For**:
- New development machines
- Fresh clones of repository
- Team member onboarding
- Environment reset

**Time Saved**: ~30 minutes for new environment setup

---

### 💡 **CONVENIENCE** (Quality of Life)

#### 8. **aliases.sh** - Command Shortcuts
**Purpose**: Short commands for common operations

**Installation**:
```bash
./scripts/install_aliases.sh
```

**Available Aliases**:
```bash
# App Management
vv-start      # Start application
vv-stop       # Stop application
vv-restart    # Restart application
vv-status     # Show status
vv-logs       # Tail logs

# Database
vv-backup     # Backup database
vv-restore    # Restore database

# Development
vv-health     # Health check
vv-cleanup    # Cleanup files
vv-deploy     # Quick deploy
vv-setup      # Setup environment

# Navigation
vv            # cd to project directory
vv-audio      # List audio files
vv-db-shell   # Open SQLite shell

# Git
vv-git-status # Git status
vv-git-pull   # Git pull
vv-git-log    # Git log

# Info
vv-info       # Show all commands
```

**Time Saved**: ~30 seconds per command (typing time)

---

#### 9. **install_aliases.sh** - Alias Installer
**Purpose**: Add aliases to your shell profile

**Usage**:
```bash
./scripts/install_aliases.sh
```

**Features**:
- ✅ Auto-detects shell (zsh/bash)
- ✅ Checks existing installation
- ✅ Safe reinstallation
- ✅ Provides activation instructions

---

## 📊 Time Savings Analysis

### Daily Operations (5-10x faster)

| Task | Manual Time | With Scripts | Time Saved |
|------|-------------|--------------|------------|
| Start/Stop App | 2 min | 5 sec | 1.9 min |
| Check Status | 3 min | 10 sec | 2.8 min |
| Health Check | 5 min | 15 sec | 4.7 min |
| Backup Database | 3 min | 10 sec | 2.8 min |

**Daily Savings**: ~12 minutes

### Weekly Operations (10-20x faster)

| Task | Manual Time | With Scripts | Time Saved |
|------|-------------|--------------|------------|
| Deploy Update | 15 min | 2 min | 13 min |
| Cleanup Files | 10 min | 2 min | 8 min |
| Restore Backup | 8 min | 1 min | 7 min |

**Weekly Savings**: ~28 minutes

### One-Time Operations (30-60x faster)

| Task | Manual Time | With Scripts | Time Saved |
|------|-------------|--------------|------------|
| Dev Environment | 45 min | 3 min | 42 min |
| Alias Setup | 15 min | 1 min | 14 min |

**Total Potential Monthly Savings**: ~5-6 hours

---

## 🎯 Usage Examples

### Example 1: Daily Development Workflow

```bash
# Morning: Start your day
vv-status           # Check if app is running
vv-start            # Start app if not running
vv-health           # Quick health check

# During development
vv-logs             # Monitor logs
vv-restart          # Restart after code changes

# End of day
vv-backup           # Backup database
vv-status           # Final status check
```

### Example 2: Deploying Updates

```bash
# Quick deployment (recommended)
vv-deploy

# Manual deployment (more control)
vv-backup           # 1. Backup first
git pull            # 2. Pull changes
vv-restart          # 3. Restart app
vv-health           # 4. Verify health
```

### Example 3: Weekly Maintenance

```bash
# Sunday maintenance routine
vv-health           # Check system health
vv-cleanup          # Clean old files
vv-backup           # Create backup
vv-status           # Verify everything
```

### Example 4: Troubleshooting

```bash
# App not responding?
vv-status           # Check what's wrong
vv-health           # Detailed diagnostics
vv-logs             # Check recent errors

# Need to restore?
vv-restore          # List backups
vv-restore voiceverse_backup_20251027_120000.db
```

### Example 5: New Team Member Onboarding

```bash
# Setup everything in 5 minutes
git clone <repository>
cd Project
./scripts/setup_dev.sh
./scripts/install_aliases.sh
source ~/.zshrc
vv-start
```

---

## 🔧 Troubleshooting

### App Won't Start

```bash
# Check what's wrong
vv-health

# Check port conflicts
lsof -ti:5000

# Force stop any process on port 5000
vv-stop

# Try starting again
vv-start
```

### Database Issues

```bash
# Check database health
vv-health

# If corrupted, restore from backup
vv-restore

# List available backups
ls -lht backups/
```

### Out of Disk Space

```bash
# Clean up old files
vv-cleanup

# Check current usage
du -sh .
du -sh saved_audio/
du -sh backups/
```

### Scripts Not Found

```bash
# Make sure scripts are executable
chmod +x scripts/*.sh

# Verify path
ls -la scripts/
```

### Aliases Not Working

```bash
# Reinstall aliases
./scripts/install_aliases.sh

# Reload shell
source ~/.zshrc  # or ~/.bash_profile

# Verify installation
vv-info
```

---

## 📁 Script Locations

All scripts are located in: `/Users/ali/Desktop/Project/scripts/`

```
scripts/
├── app_manager.sh         # App lifecycle management
├── health_check.sh        # System health monitoring
├── backup_db.sh           # Database backup
├── restore_db.sh          # Database restoration
├── quick_deploy.sh        # Rapid deployment
├── cleanup.sh             # File system cleanup
├── setup_dev.sh           # Environment setup
├── aliases.sh             # Command shortcuts
└── install_aliases.sh     # Alias installer
```

---

## 🔐 Security Notes

### .env File
- Never commit `.env` to version control
- Keep backups of `.env` separately
- Use strong SECRET_KEY values

### Database Backups
- Stored in `backups/` directory
- Excluded from git via `.gitignore`
- Include SHA256 checksums for integrity

### Logs
- May contain sensitive information
- Rotated by cleanup script
- Review before sharing

---

## 🆘 Getting Help

### View Script Documentation
```bash
./scripts/app_manager.sh help
./scripts/health_check.sh --help
```

### Check Script Status
```bash
ls -lh scripts/
```

### Common Commands Quick Reference
```bash
vv-info              # Show all available commands
vv-status            # Show current status
vv-health            # Run health check
vv-logs              # View logs
```

---

## 🚀 Next Steps

1. **Run setup** if first time: `./scripts/setup_dev.sh`
2. **Install aliases** for convenience: `./scripts/install_aliases.sh`
3. **Start app**: `vv-start` or `./scripts/app_manager.sh start`
4. **Run health check**: `vv-health`
5. **Create first backup**: `vv-backup`

---

## 📞 Support

If you encounter issues:
1. Check this guide's troubleshooting section
2. Run `vv-health` for diagnostics
3. Check `app.log` for errors
4. Review script source code for details

---

**Created**: October 27, 2025
**Version**: 1.0.0
**Status**: ✅ Production Ready
**Scripts**: 9 automation tools
**Estimated Time Savings**: 5-6 hours/month

🌌 **Happy Automating!**
