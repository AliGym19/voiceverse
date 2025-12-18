#!/bin/bash

# VoiceVerse Database Backup Script
# Automatically backs up database with versioning and cleanup

set -e

PROJECT_DIR="/Users/ali/Desktop/Project"
BACKUP_DIR="$PROJECT_DIR/backups"
DB_FILE="voiceverse.db"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="voiceverse_backup_$TIMESTAMP.db"

# Retention settings
KEEP_DAILY=7        # Keep daily backups for 7 days
KEEP_WEEKLY=4       # Keep weekly backups for 4 weeks
KEEP_MONTHLY=3      # Keep monthly backups for 3 months

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

function print_status() {
    echo -e "${BLUE}[Backup]${NC} $1"
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

# Create backup directory
mkdir -p "$BACKUP_DIR"

print_status "Starting database backup..."

# Check if database exists
if [ ! -f "$DB_FILE" ]; then
    print_error "Database file not found: $DB_FILE"
    exit 1
fi

# Get database size
DB_SIZE=$(ls -lh "$DB_FILE" | awk '{print $5}')
print_status "Database size: $DB_SIZE"

# Create backup
print_status "Creating backup: $BACKUP_FILE"
cp "$DB_FILE" "$BACKUP_DIR/$BACKUP_FILE"

if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(ls -lh "$BACKUP_DIR/$BACKUP_FILE" | awk '{print $5}')
    print_success "Backup created successfully ($BACKUP_SIZE)"
else
    print_error "Backup failed!"
    exit 1
fi

# Create checksums for verification
print_status "Creating checksum..."
cd "$BACKUP_DIR"
shasum -a 256 "$BACKUP_FILE" > "${BACKUP_FILE}.sha256"
print_success "Checksum created"

# Cleanup old backups
print_status "Cleaning up old backups..."

# Daily backups - keep last 7 days
DAILY_COUNT=$(find "$BACKUP_DIR" -name "voiceverse_backup_*.db" -mtime -7 | wc -l | xargs)

# Weekly backups - keep files from 7-28 days ago (keep one per week)
# Monthly backups - keep files older than 28 days (keep one per month)

# Get total backup count
TOTAL_BACKUPS=$(find "$BACKUP_DIR" -name "voiceverse_backup_*.db" | wc -l | xargs)

# Delete backups older than 90 days
DELETED=$(find "$BACKUP_DIR" -name "voiceverse_backup_*.db" -mtime +90 -delete -print | wc -l | xargs)

if [ "$DELETED" -gt 0 ]; then
    print_success "Deleted $DELETED old backups (>90 days)"
fi

# Show backup statistics
echo ""
print_status "Backup Statistics:"
echo "  Total backups: $TOTAL_BACKUPS"
echo "  Recent backups (7 days): $DAILY_COUNT"
echo "  Backup directory size: $(du -sh $BACKUP_DIR | awk '{print $1}')"

# List recent backups
echo ""
print_status "Recent backups:"
ls -lht "$BACKUP_DIR"/voiceverse_backup_*.db | head -5 | awk '{printf "  %s %s  %s\n", $6, $7, $9}' | sed "s|$BACKUP_DIR/||g"

echo ""
print_success "Backup complete!"
print_status "Backup location: $BACKUP_DIR/$BACKUP_FILE"

# Show restoration command
echo ""
echo "To restore this backup:"
echo "  ./scripts/restore_db.sh $BACKUP_FILE"
