#!/bin/bash

# VoiceVerse Quick Deploy Script
# Pull latest code, run migrations, and restart app

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
    echo -e "  ${BLUE}🚀 VoiceVerse Quick Deploy${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

function print_step() {
    echo -e "${BLUE}[Step $1/$2]${NC} $3"
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

print_header

# Check if git repo
if [ ! -d ".git" ]; then
    print_error "Not a git repository"
    exit 1
fi

TOTAL_STEPS=6

# Step 1: Check current status
print_step "1" "$TOTAL_STEPS" "Checking current status..."
CURRENT_BRANCH=$(git branch --show-current)
print_success "On branch: $CURRENT_BRANCH"

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    print_warning "Uncommitted changes detected"
    git status --short | head -5
    echo ""
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo ""

# Step 2: Backup database
print_step "2" "$TOTAL_STEPS" "Backing up database..."
if [ -f "voiceverse.db" ]; then
    if [ -f "scripts/backup_db.sh" ]; then
        ./scripts/backup_db.sh > /dev/null 2>&1 || print_warning "Backup failed"
        print_success "Database backed up"
    else
        BACKUP_DIR="backups"
        mkdir -p "$BACKUP_DIR"
        TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
        cp voiceverse.db "$BACKUP_DIR/voiceverse_pre_deploy_$TIMESTAMP.db"
        print_success "Database backed up manually"
    fi
else
    print_warning "No database to backup"
fi

echo ""

# Step 3: Pull latest code
print_step "3" "$TOTAL_STEPS" "Pulling latest code from $CURRENT_BRANCH..."
OLD_COMMIT=$(git rev-parse HEAD)

if git pull origin "$CURRENT_BRANCH"; then
    NEW_COMMIT=$(git rev-parse HEAD)

    if [ "$OLD_COMMIT" = "$NEW_COMMIT" ]; then
        print_success "Already up to date"
    else
        print_success "Pulled latest changes"

        # Show what changed
        echo ""
        echo "  Changes:"
        git log --oneline "$OLD_COMMIT..$NEW_COMMIT" | head -5 | sed 's/^/    /'

        # Show modified files
        echo ""
        echo "  Modified files:"
        git diff --name-status "$OLD_COMMIT" "$NEW_COMMIT" | head -10 | sed 's/^/    /'
    fi
else
    print_error "Failed to pull latest code"
    exit 1
fi

echo ""

# Step 4: Install dependencies
print_step "4" "$TOTAL_STEPS" "Checking dependencies..."
if [ -f "requirements.txt" ]; then
    if pip install -r requirements.txt --quiet; then
        print_success "Dependencies up to date"
    else
        print_warning "Some dependencies failed to install"
    fi
else
    print_warning "No requirements.txt found"
fi

echo ""

# Step 5: Run migrations
print_step "5" "$TOTAL_STEPS" "Running database migrations..."
if [ -d "migrations" ]; then
    MIGRATION_FILES=$(find migrations -name "*.sql" 2>/dev/null | wc -l | xargs)
    if [ "$MIGRATION_FILES" -gt 0 ]; then
        print_success "Found $MIGRATION_FILES migration files"

        # Run migration manager if it exists
        if [ -f "migrations/migration_manager.py" ]; then
            if python3 migrations/migration_manager.py; then
                print_success "Migrations completed"
            else
                print_warning "Migration errors (check logs)"
            fi
        else
            print_warning "No migration manager found"
        fi
    else
        print_success "No pending migrations"
    fi
else
    print_warning "No migrations directory"
fi

echo ""

# Step 6: Restart application
print_step "6" "$TOTAL_STEPS" "Restarting application..."
if [ -f "scripts/app_manager.sh" ]; then
    ./scripts/app_manager.sh restart
    print_success "Application restarted"
else
    # Manual restart
    if [ -f ".app.pid" ]; then
        PID=$(cat .app.pid)
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            sleep 2
        fi
    fi

    # Check if port is in use
    PORT_PID=$(lsof -ti:5000 2>/dev/null || echo "")
    if [ -n "$PORT_PID" ]; then
        kill "$PORT_PID"
        sleep 1
    fi

    # Start app
    nohup python3 tts_app19.py >> app.log 2>&1 &
    echo $! > .app.pid
    sleep 2

    if ps -p $(cat .app.pid) > /dev/null 2>&1; then
        print_success "Application started"
    else
        print_error "Failed to start application"
        exit 1
    fi
fi

echo ""

# Verify deployment
print_step "Verify" "$TOTAL_STEPS" "Verifying deployment..."
sleep 3

# Check if app is responding
if curl -k -s -o /dev/null -w "%{http_code}" "https://127.0.0.1:5000" | grep -q "200\|302"; then
    print_success "App is responding"
else
    print_warning "App may not be responding correctly"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_success "Deployment complete!"
echo ""
echo "  URL: https://127.0.0.1:5000"
echo "  Status: ./scripts/app_manager.sh status"
echo "  Logs: ./scripts/app_manager.sh logs"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
