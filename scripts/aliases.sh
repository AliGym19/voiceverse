#!/bin/bash

# VoiceVerse Command Aliases
# Source this file to add convenient shortcuts to your shell
# Usage: source scripts/aliases.sh
# Or add to ~/.zshrc: source /Users/ali/Desktop/Project/scripts/aliases.sh

PROJECT_DIR="/Users/ali/Desktop/Project"

# App management aliases
alias vv-start="$PROJECT_DIR/scripts/app_manager.sh start"
alias vv-stop="$PROJECT_DIR/scripts/app_manager.sh stop"
alias vv-restart="$PROJECT_DIR/scripts/app_manager.sh restart"
alias vv-status="$PROJECT_DIR/scripts/app_manager.sh status"
alias vv-logs="$PROJECT_DIR/scripts/app_manager.sh logs"

# Database aliases
alias vv-backup="$PROJECT_DIR/scripts/backup_db.sh"
alias vv-restore="$PROJECT_DIR/scripts/restore_db.sh"

# Development aliases
alias vv-health="$PROJECT_DIR/scripts/health_check.sh"
alias vv-cleanup="$PROJECT_DIR/scripts/cleanup.sh"
alias vv-deploy="$PROJECT_DIR/scripts/quick_deploy.sh"
alias vv-setup="$PROJECT_DIR/scripts/setup_dev.sh"

# Quick navigation
alias vv="cd $PROJECT_DIR"
alias vv-logs-dir="cd $PROJECT_DIR && tail -f app.log"
alias vv-audio="cd $PROJECT_DIR/saved_audio && ls -lht | head -20"

# Git shortcuts
alias vv-git-status="cd $PROJECT_DIR && git status"
alias vv-git-pull="cd $PROJECT_DIR && git pull"
alias vv-git-log="cd $PROJECT_DIR && git log --oneline -10"

# Python shortcuts
alias vv-shell="cd $PROJECT_DIR && python3"
alias vv-db-shell="cd $PROJECT_DIR && sqlite3 voiceverse.db"

# Quick info
alias vv-info="echo '🌌 VoiceVerse TTS Application'; echo ''; echo 'Location: $PROJECT_DIR'; echo 'URL: https://127.0.0.1:5000'; echo ''; echo 'Quick commands:'; echo '  vv-start    - Start the app'; echo '  vv-stop     - Stop the app'; echo '  vv-restart  - Restart the app'; echo '  vv-status   - Check status'; echo '  vv-logs     - View logs'; echo '  vv-health   - Health check'; echo '  vv-backup   - Backup database'; echo ''"

# Display loaded message
echo "✓ VoiceVerse aliases loaded"
echo "  Type 'vv-info' for available commands"
