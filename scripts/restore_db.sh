#!/bin/bash

# VoiceVerse Database Restore Script
# Restore database from backup with safety checks

set -e

PROJECT_DIR="/Users/ali/Desktop/Project"
BACKUP_DIR="$PROJECT_DIR/backups"
DB_FILE="voiceverse.db"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

function print_status() {
    echo -e "${BLUE}[Restore]${NC} $1"
}

function print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

function print_error() {
    echo -e "${RED}✗${NC} $1"
}

function print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

cd "$PROJECT_DIR"

# Show available backups if no argument provided
if [ -z "$1" ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🌌 VoiceVerse Database Restore"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    print_status "Available backups:"
    echo ""

    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A $BACKUP_DIR/voiceverse_backup_*.db 2>/dev/null)" ]; then
        print_error "No backups found in $BACKUP_DIR"
        exit 1
    fi

    # List backups with numbers
    COUNT=1
    ls -1t "$BACKUP_DIR"/voiceverse_backup_*.db | while read -r backup; do
        FILENAME=$(basename "$backup")
        SIZE=$(ls -lh "$backup" | awk '{print $5}')
        DATE=$(echo "$FILENAME" | sed 's/voiceverse_backup_\([0-9]*\)_\([0-9]*\)\.db/\1 \2/' | awk '{print substr($1,1,4)"-"substr($1,5,2)"-"substr($1,7,2)" "substr($2,1,2)":"substr($2,3,2)":"substr($2,5,2)}')
        echo "  [$COUNT] $FILENAME"
        echo "      Date: $DATE | Size: $SIZE"
        echo ""
        COUNT=$((COUNT + 1))
    done

    echo ""
    echo "Usage: $0 <backup_filename>"
    echo "Example: $0 voiceverse_backup_20251027_120000.db"
    echo ""
    exit 0
fi

BACKUP_FILE="$1"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILE"

# Check if backup exists
if [ ! -f "$BACKUP_PATH" ]; then
    print_error "Backup file not found: $BACKUP_PATH"
    exit 1
fi

# Show backup info
print_status "Backup file: $BACKUP_FILE"
BACKUP_SIZE=$(ls -lh "$BACKUP_PATH" | awk '{print $5}')
BACKUP_DATE=$(ls -lh "$BACKUP_PATH" | awk '{print $6, $7, $8}')
print_status "Backup size: $BACKUP_SIZE"
print_status "Backup date: $BACKUP_DATE"

# Verify checksum if available
if [ -f "${BACKUP_PATH}.sha256" ]; then
    print_status "Verifying backup integrity..."
    cd "$BACKUP_DIR"
    if shasum -a 256 -c "${BACKUP_FILE}.sha256" --quiet 2>/dev/null; then
        print_success "Backup integrity verified"
    else
        print_error "Backup integrity check failed!"
        print_warning "The backup file may be corrupted"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    cd "$PROJECT_DIR"
fi

# Check if app is running
if [ -f ".app.pid" ]; then
    PID=$(cat .app.pid)
    if ps -p "$PID" > /dev/null 2>&1; then
        print_error "Application is currently running!"
        print_warning "You must stop the app before restoring the database"
        echo ""
        echo "Run: ./scripts/app_manager.sh stop"
        exit 1
    fi
fi

# Backup current database before restore
if [ -f "$DB_FILE" ]; then
    CURRENT_SIZE=$(ls -lh "$DB_FILE" | awk '{print $5}')
    print_warning "Current database exists ($CURRENT_SIZE)"
    print_warning "This will be backed up before restoration"

    mkdir -p "$BACKUP_DIR/pre_restore"
    PRE_RESTORE_FILE="voiceverse_pre_restore_$(date +%Y%m%d_%H%M%S).db"
    cp "$DB_FILE" "$BACKUP_DIR/pre_restore/$PRE_RESTORE_FILE"
    print_success "Current database backed up: $PRE_RESTORE_FILE"
fi

# Confirm restoration
echo ""
print_warning "⚠️  WARNING: This will replace the current database!"
read -p "Are you sure you want to restore from $BACKUP_FILE? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Restore cancelled"
    exit 0
fi

# Perform restore
print_status "Restoring database..."
cp "$BACKUP_PATH" "$DB_FILE"

if [ -f "$DB_FILE" ]; then
    RESTORED_SIZE=$(ls -lh "$DB_FILE" | awk '{print $5}')
    print_success "Database restored successfully"
    print_success "New database size: $RESTORED_SIZE"
else
    print_error "Restore failed!"
    exit 1
fi

echo ""
print_success "Restore complete!"
echo ""
echo "Next steps:"
echo "  1. Start the application: ./scripts/app_manager.sh start"
echo "  2. Verify data integrity in the web interface"
echo ""
echo "If there are issues:"
echo "  - Pre-restore backup: $BACKUP_DIR/pre_restore/$PRE_RESTORE_FILE"
echo "  - Run: ./scripts/restore_db.sh $PRE_RESTORE_FILE"
echo ""
