#!/bin/bash

# VoiceVerse Cleanup Script
# Clean up old files, logs, and temporary data

set -e

PROJECT_DIR="/Users/ali/Desktop/Project"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

function print_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "  ${BLUE}🧹 VoiceVerse Cleanup${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

function print_section() {
    echo ""
    echo -e "${BLUE}▼ $1${NC}"
}

function print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

function print_info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
}

function print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

cd "$PROJECT_DIR"

print_header

# Interactive mode
if [ "$1" != "--force" ]; then
    echo "This will clean up old files, logs, and temporary data."
    echo ""
    read -p "Continue? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cleanup cancelled"
        exit 0
    fi
    echo ""
fi

TOTAL_FREED=0

# ============================================================================
# 1. Python cache files
# ============================================================================
print_section "Python Cache Files"

CACHE_SIZE=$(find . -type d -name __pycache__ -exec du -sk {} \; 2>/dev/null | awk '{sum+=$1} END {print sum}')
if [ -n "$CACHE_SIZE" ] && [ "$CACHE_SIZE" != "0" ]; then
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    print_success "Removed Python cache files (~${CACHE_SIZE}KB)"
    TOTAL_FREED=$((TOTAL_FREED + CACHE_SIZE))
else
    print_info "No Python cache files found"
fi

# ============================================================================
# 2. Test audio files
# ============================================================================
print_section "Test Audio Files"

if [ -d "saved_audio" ]; then
    TEST_FILES=$(find saved_audio -name "*test*.mp3" 2>/dev/null)
    if [ -n "$TEST_FILES" ]; then
        TEST_COUNT=$(echo "$TEST_FILES" | wc -l | xargs)
        TEST_SIZE=$(find saved_audio -name "*test*.mp3" -exec du -sk {} \; 2>/dev/null | awk '{sum+=$1} END {print sum}')

        echo "Found $TEST_COUNT test audio files (~${TEST_SIZE}KB)"
        read -p "Delete test audio files? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            find saved_audio -name "*test*.mp3" -delete 2>/dev/null || true
            print_success "Removed $TEST_COUNT test files (~${TEST_SIZE}KB)"
            TOTAL_FREED=$((TOTAL_FREED + TEST_SIZE))
        else
            print_info "Skipped test files"
        fi
    else
        print_info "No test audio files found"
    fi
fi

# ============================================================================
# 3. Old audio files
# ============================================================================
print_section "Old Audio Files"

if [ -d "saved_audio" ]; then
    # Files older than 30 days
    OLD_FILES=$(find saved_audio -name "*.mp3" -mtime +30 2>/dev/null)
    if [ -n "$OLD_FILES" ]; then
        OLD_COUNT=$(echo "$OLD_FILES" | wc -l | xargs)
        OLD_SIZE=$(find saved_audio -name "*.mp3" -mtime +30 -exec du -sk {} \; 2>/dev/null | awk '{sum+=$1} END {print sum}')

        echo "Found $OLD_COUNT audio files older than 30 days (~${OLD_SIZE}KB)"
        read -p "Delete old audio files? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            find saved_audio -name "*.mp3" -mtime +30 -delete 2>/dev/null || true
            print_success "Removed $OLD_COUNT old files (~${OLD_SIZE}KB)"
            TOTAL_FREED=$((TOTAL_FREED + OLD_SIZE))
        else
            print_info "Skipped old files"
        fi
    else
        print_info "No old audio files found"
    fi
fi

# ============================================================================
# 4. Log files
# ============================================================================
print_section "Log Files"

if [ -f "app.log" ]; then
    LOG_SIZE=$(stat -f %z app.log 2>/dev/null || echo 0)
    LOG_SIZE_KB=$((LOG_SIZE / 1024))

    if [ $LOG_SIZE -gt 1048576 ]; then  # > 1MB
        echo "Log file is ${LOG_SIZE_KB}KB"
        read -p "Archive and clear log file? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            mkdir -p logs/archive
            TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
            mv app.log "logs/archive/app_${TIMESTAMP}.log"
            touch app.log
            print_success "Log archived and cleared (~${LOG_SIZE_KB}KB)"
            TOTAL_FREED=$((TOTAL_FREED + LOG_SIZE_KB))
        else
            print_info "Skipped log file"
        fi
    else
        print_info "Log file is small (${LOG_SIZE_KB}KB)"
    fi
fi

# ============================================================================
# 5. Backup files
# ============================================================================
print_section "Old Backup Files"

if [ -d "backups" ]; then
    OLD_BACKUPS=$(find backups -name "*.db" -mtime +90 2>/dev/null)
    if [ -n "$OLD_BACKUPS" ]; then
        BACKUP_COUNT=$(echo "$OLD_BACKUPS" | wc -l | xargs)
        BACKUP_SIZE=$(find backups -name "*.db" -mtime +90 -exec du -sk {} \; 2>/dev/null | awk '{sum+=$1} END {print sum}')

        echo "Found $BACKUP_COUNT backups older than 90 days (~${BACKUP_SIZE}KB)"
        read -p "Delete old backups? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            find backups -name "*.db" -mtime +90 -delete 2>/dev/null || true
            find backups -name "*.sha256" -mtime +90 -delete 2>/dev/null || true
            print_success "Removed $BACKUP_COUNT old backups (~${BACKUP_SIZE}KB)"
            TOTAL_FREED=$((TOTAL_FREED + BACKUP_SIZE))
        else
            print_info "Skipped old backups"
        fi
    else
        print_info "No old backups found"
    fi
fi

# ============================================================================
# 6. Temporary files
# ============================================================================
print_section "Temporary Files"

TEMP_FILES=$(find . -name "*.tmp" -o -name "*.bak" -o -name "*.swp" -o -name "*~" 2>/dev/null)
if [ -n "$TEMP_FILES" ]; then
    TEMP_COUNT=$(echo "$TEMP_FILES" | wc -l | xargs)
    TEMP_SIZE=$(find . \( -name "*.tmp" -o -name "*.bak" -o -name "*.swp" -o -name "*~" \) -exec du -sk {} \; 2>/dev/null | awk '{sum+=$1} END {print sum}')

    if [ -n "$TEMP_SIZE" ] && [ "$TEMP_SIZE" != "0" ]; then
        echo "Found $TEMP_COUNT temporary files (~${TEMP_SIZE}KB)"
        find . \( -name "*.tmp" -o -name "*.bak" -o -name "*.swp" -o -name "*~" \) -delete 2>/dev/null || true
        print_success "Removed temporary files (~${TEMP_SIZE}KB)"
        TOTAL_FREED=$((TOTAL_FREED + TEMP_SIZE))
    fi
else
    print_info "No temporary files found"
fi

# ============================================================================
# 7. Empty directories
# ============================================================================
print_section "Empty Directories"

EMPTY_DIRS=$(find . -type d -empty 2>/dev/null | grep -v ".git" | grep -v "node_modules" || true)
if [ -n "$EMPTY_DIRS" ]; then
    EMPTY_COUNT=$(echo "$EMPTY_DIRS" | wc -l | xargs)
    echo "Found $EMPTY_COUNT empty directories"
    find . -type d -empty -delete 2>/dev/null || true
    print_success "Removed $EMPTY_COUNT empty directories"
else
    print_info "No empty directories found"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $TOTAL_FREED -gt 1024 ]; then
    FREED_MB=$((TOTAL_FREED / 1024))
    print_success "Cleanup complete! Freed approximately ${FREED_MB}MB"
else
    print_success "Cleanup complete! Freed approximately ${TOTAL_FREED}KB"
fi

# Show current disk usage
echo ""
print_info "Current directory size:"
DU_OUTPUT=$(du -sh . 2>/dev/null | awk '{print $1}')
echo "  Total: $DU_OUTPUT"

if [ -d "saved_audio" ]; then
    AUDIO_SIZE=$(du -sh saved_audio 2>/dev/null | awk '{print $1}')
    AUDIO_COUNT=$(find saved_audio -name "*.mp3" | wc -l | xargs)
    echo "  Audio: $AUDIO_SIZE ($AUDIO_COUNT files)"
fi

if [ -d "backups" ]; then
    BACKUP_SIZE=$(du -sh backups 2>/dev/null | awk '{print $1}')
    BACKUP_COUNT=$(find backups -name "*.db" | wc -l | xargs)
    echo "  Backups: $BACKUP_SIZE ($BACKUP_COUNT files)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
