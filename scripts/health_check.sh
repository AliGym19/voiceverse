#!/bin/bash

# VoiceVerse Health Check Script
# Comprehensive system health monitoring

set -e

PROJECT_DIR="/Users/ali/Desktop/Project"
APP_URL="https://127.0.0.1:5000"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

function print_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "  ${CYAN}🏥 VoiceVerse Health Check${NC}"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

function print_section() {
    echo ""
    echo -e "${BLUE}▼ $1${NC}"
    echo "────────────────────────────────────────"
}

function print_check() {
    echo -n "  $1... "
}

function print_pass() {
    echo -e "${GREEN}✓ PASS${NC} $1"
}

function print_fail() {
    echo -e "${RED}✗ FAIL${NC} $1"
}

function print_warn() {
    echo -e "${YELLOW}⚠ WARN${NC} $1"
}

function print_info() {
    echo -e "  ${CYAN}ℹ${NC} $1"
}

cd "$PROJECT_DIR"

print_header

FAILURES=0
WARNINGS=0

# ============================================================================
# 1. Application Process
# ============================================================================
print_section "Application Process"

if [ -f ".app.pid" ]; then
    PID=$(cat .app.pid)
    if ps -p "$PID" > /dev/null 2>&1; then
        print_pass "App is running (PID: $PID)"

        # Memory usage
        MEM=$(ps -o rss= -p "$PID" | awk '{printf "%.1f", $1/1024}')
        if (( $(echo "$MEM > 500" | bc -l) )); then
            print_warn "High memory usage: ${MEM}MB"
            WARNINGS=$((WARNINGS + 1))
        else
            print_info "Memory: ${MEM}MB"
        fi

        # CPU usage
        CPU=$(ps -o %cpu= -p "$PID" | xargs)
        if (( $(echo "$CPU > 80" | bc -l) )); then
            print_warn "High CPU usage: ${CPU}%"
            WARNINGS=$((WARNINGS + 1))
        else
            print_info "CPU: ${CPU}%"
        fi

        # Uptime
        UPTIME=$(ps -o etime= -p "$PID" | xargs)
        print_info "Uptime: $UPTIME"
    else
        print_fail "PID file exists but process not running"
        FAILURES=$((FAILURES + 1))
    fi
else
    print_fail "App is not running"
    FAILURES=$((FAILURES + 1))
fi

# ============================================================================
# 2. Network & Port
# ============================================================================
print_section "Network & Connectivity"

PORT_PID=$(lsof -ti:5000 2>/dev/null || echo "")
if [ -n "$PORT_PID" ]; then
    print_pass "Port 5000 is open (PID: $PORT_PID)"
else
    print_fail "Port 5000 is not in use"
    FAILURES=$((FAILURES + 1))
fi

# HTTP Response check
print_check "HTTP response"
HTTP_CODE=$(curl -k -s -o /dev/null -w "%{http_code}" "$APP_URL" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo -e "${GREEN}✓${NC}"
    print_info "HTTP status: $HTTP_CODE"
else
    echo -e "${RED}✗${NC}"
    print_fail "HTTP status: $HTTP_CODE"
    FAILURES=$((FAILURES + 1))
fi

# Response time
print_check "Response time"
START=$(date +%s%N)
curl -k -s -o /dev/null "$APP_URL" 2>/dev/null || true
END=$(date +%s%N)
RESPONSE_MS=$(( (END - START) / 1000000 ))

if [ $RESPONSE_MS -lt 1000 ]; then
    echo -e "${GREEN}✓${NC}"
    print_info "Response time: ${RESPONSE_MS}ms"
elif [ $RESPONSE_MS -lt 3000 ]; then
    echo -e "${YELLOW}⚠${NC}"
    print_warn "Slow response: ${RESPONSE_MS}ms"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${RED}✗${NC}"
    print_fail "Very slow response: ${RESPONSE_MS}ms"
    FAILURES=$((FAILURES + 1))
fi

# ============================================================================
# 3. Database
# ============================================================================
print_section "Database"

if [ -f "voiceverse.db" ]; then
    print_pass "Database file exists"

    DB_SIZE=$(ls -lh voiceverse.db | awk '{print $5}')
    print_info "Size: $DB_SIZE"

    # Check if database is locked
    if sqlite3 voiceverse.db "SELECT 1;" > /dev/null 2>&1; then
        print_pass "Database is accessible"

        # Count tables
        TABLE_COUNT=$(sqlite3 voiceverse.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo "0")
        print_info "Tables: $TABLE_COUNT"

        # Count users
        USER_COUNT=$(sqlite3 voiceverse.db "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")
        print_info "Users: $USER_COUNT"

        # Count audio files
        AUDIO_COUNT=$(sqlite3 voiceverse.db "SELECT COUNT(*) FROM audio_files;" 2>/dev/null || echo "0")
        print_info "Audio files: $AUDIO_COUNT"
    else
        print_fail "Database is locked or corrupted"
        FAILURES=$((FAILURES + 1))
    fi

    # Check last backup
    if [ -d "backups" ]; then
        LAST_BACKUP=$(ls -1t backups/voiceverse_backup_*.db 2>/dev/null | head -1)
        if [ -n "$LAST_BACKUP" ]; then
            BACKUP_AGE=$(( ($(date +%s) - $(stat -f %m "$LAST_BACKUP")) / 86400 ))
            if [ $BACKUP_AGE -eq 0 ]; then
                print_pass "Backup is current (today)"
            elif [ $BACKUP_AGE -lt 7 ]; then
                print_info "Last backup: ${BACKUP_AGE} days ago"
            else
                print_warn "Last backup: ${BACKUP_AGE} days ago"
                WARNINGS=$((WARNINGS + 1))
            fi
        else
            print_warn "No database backups found"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        print_warn "No backup directory found"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    print_fail "Database file not found"
    FAILURES=$((FAILURES + 1))
fi

# ============================================================================
# 4. File System
# ============================================================================
print_section "File System"

# Check disk space
DISK_USAGE=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    print_pass "Disk space: ${DISK_USAGE}% used"
else
    print_warn "Disk space: ${DISK_USAGE}% used"
    WARNINGS=$((WARNINGS + 1))
fi

# Check directories
REQUIRED_DIRS=("saved_audio" "static" "migrations" "workflows" "agents")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        print_pass "Directory exists: $dir"
    else
        print_fail "Missing directory: $dir"
        FAILURES=$((FAILURES + 1))
    fi
done

# Check audio files
if [ -d "saved_audio" ]; then
    MP3_COUNT=$(find saved_audio -name "*.mp3" 2>/dev/null | wc -l | xargs)
    AUDIO_SIZE=$(du -sh saved_audio 2>/dev/null | awk '{print $1}')
    print_info "Audio files: $MP3_COUNT ($AUDIO_SIZE)"

    if [ $MP3_COUNT -gt 100 ]; then
        print_warn "Large number of audio files ($MP3_COUNT)"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Check log file
if [ -f "app.log" ]; then
    LOG_SIZE=$(ls -lh app.log | awk '{print $5}')
    LOG_SIZE_BYTES=$(stat -f %z app.log)

    if [ $LOG_SIZE_BYTES -gt 10485760 ]; then  # 10MB
        print_warn "Large log file: $LOG_SIZE"
        WARNINGS=$((WARNINGS + 1))
    else
        print_pass "Log file: $LOG_SIZE"
    fi

    # Check for errors in logs
    ERROR_COUNT=$(grep -i "error" app.log 2>/dev/null | wc -l | xargs)
    if [ $ERROR_COUNT -gt 0 ]; then
        print_warn "$ERROR_COUNT errors found in logs"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    print_warn "No log file found"
    WARNINGS=$((WARNINGS + 1))
fi

# ============================================================================
# 5. Environment
# ============================================================================
print_section "Environment Configuration"

if [ -f ".env" ]; then
    print_pass ".env file exists"

    # Check required variables
    REQUIRED_VARS=("SECRET_KEY" "OPENAI_API_KEY")
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^$var=" .env && [ "$(grep "^$var=" .env | cut -d'=' -f2)" != "" ]; then
            print_pass "$var is set"
        else
            print_fail "$var is not set"
            FAILURES=$((FAILURES + 1))
        fi
    done

    # Check for default values
    if grep -q "SECRET_KEY=CHANGE_THIS" .env || grep -q "SECRET_KEY=your-" .env; then
        print_warn "SECRET_KEY appears to be a default value"
        WARNINGS=$((WARNINGS + 1))
    fi

    if grep -q "OPENAI_API_KEY=sk-your-" .env || grep -q "OPENAI_API_KEY=your-" .env; then
        print_warn "OPENAI_API_KEY appears to be a placeholder"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    print_fail ".env file not found"
    FAILURES=$((FAILURES + 1))
fi

# Check Python dependencies
if [ -f "requirements.txt" ]; then
    print_pass "requirements.txt exists"

    # Check if all packages are installed
    MISSING=0
    while IFS= read -r package; do
        if [ -n "$package" ] && [[ ! "$package" =~ ^# ]]; then
            PKG_NAME=$(echo "$package" | cut -d'>' -f1 | cut -d'=' -f1 | cut -d'<' -f1)
            if ! python3 -c "import $PKG_NAME" 2>/dev/null; then
                MISSING=$((MISSING + 1))
            fi
        fi
    done < requirements.txt

    if [ $MISSING -eq 0 ]; then
        print_pass "All dependencies installed"
    else
        print_warn "$MISSING dependencies missing"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $FAILURES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ ALL SYSTEMS OPERATIONAL${NC}"
    echo ""
    echo "  No issues detected"
    EXIT_CODE=0
elif [ $FAILURES -eq 0 ]; then
    echo -e "${YELLOW}⚠ SYSTEM HEALTHY WITH WARNINGS${NC}"
    echo ""
    echo "  Warnings: $WARNINGS"
    echo "  Review warnings above"
    EXIT_CODE=1
else
    echo -e "${RED}✗ SYSTEM ISSUES DETECTED${NC}"
    echo ""
    echo "  Failures: $FAILURES"
    echo "  Warnings: $WARNINGS"
    echo "  Immediate attention required"
    EXIT_CODE=2
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit $EXIT_CODE
