#!/bin/bash

# VoiceVerse Development Environment Setup
# Automatically sets up everything needed to run the app

set -e

PROJECT_DIR="/Users/ali/Desktop/Project"
VENV_DIR="venv"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

function print_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "  ${BLUE}🌌 VoiceVerse Development Setup${NC}"
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

# Step 1: Check Python
print_step "1" "8" "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

echo ""

# Step 2: Create virtual environment
print_step "2" "8" "Creating virtual environment..."
if [ -d "$VENV_DIR" ]; then
    print_warning "Virtual environment already exists"
    read -p "Recreate it? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment recreated"
    else
        print_success "Using existing virtual environment"
    fi
else
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created"
fi

echo ""

# Step 3: Activate virtual environment
print_step "3" "8" "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
print_success "Virtual environment activated"

echo ""

# Step 4: Upgrade pip
print_step "4" "8" "Upgrading pip..."
pip install --upgrade pip --quiet
print_success "Pip upgraded to $(pip --version | awk '{print $2}')"

echo ""

# Step 5: Install dependencies
print_step "5" "8" "Installing dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    print_success "Dependencies installed"
else
    print_error "requirements.txt not found!"
    exit 1
fi

echo ""

# Step 6: Setup environment variables
print_step "6" "8" "Setting up environment variables..."
if [ -f ".env" ]; then
    print_warning ".env file already exists"

    # Validate required variables
    MISSING_VARS=()
    while IFS= read -r line; do
        if [[ $line =~ ^([A-Z_]+)= ]]; then
            VAR_NAME="${BASH_REMATCH[1]}"
            if ! grep -q "^$VAR_NAME=" .env; then
                MISSING_VARS+=("$VAR_NAME")
            fi
        fi
    done < <(echo "SECRET_KEY=
OPENAI_API_KEY=
SECURE_COOKIES=false
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
SESSION_LIFETIME=3600
IP_HASH_SALT=
ADMIN_EMAIL=
SMTP_SERVER=
SMTP_PORT=587")

    if [ ${#MISSING_VARS[@]} -gt 0 ]; then
        print_warning "Missing environment variables: ${MISSING_VARS[*]}"
        echo "Please add them to your .env file"
    else
        print_success ".env file configured correctly"
    fi
else
    print_warning ".env file not found, creating template..."

    cat > .env << 'EOF'
# VoiceVerse Configuration

# Security (REQUIRED)
SECRET_KEY=CHANGE_THIS_TO_RANDOM_VALUE
OPENAI_API_KEY=sk-your-api-key-here

# Session Configuration
SECURE_COOKIES=false
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
SESSION_LIFETIME=3600

# Security
IP_HASH_SALT=change-this-salt

# Email Alerts (Optional)
ADMIN_EMAIL=admin@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
EOF

    print_success ".env template created"
    print_warning "⚠️  IMPORTANT: Edit .env and set your SECRET_KEY and OPENAI_API_KEY"
fi

echo ""

# Step 7: Setup directories
print_step "7" "8" "Creating required directories..."
mkdir -p saved_audio
mkdir -p voice_samples
mkdir -p workflows
mkdir -p agents
mkdir -p data
mkdir -p certs
mkdir -p static
mkdir -p migrations
print_success "Directories created"

echo ""

# Step 8: Initialize database
print_step "8" "8" "Checking database..."
if [ -f "voiceverse.db" ]; then
    DB_SIZE=$(ls -lh voiceverse.db | awk '{print $5}')
    print_success "Database exists ($DB_SIZE)"
else
    print_warning "Database not found"
    echo "  It will be created on first run"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_success "Development environment setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your API keys"
echo "  2. Run: ./scripts/app_manager.sh start"
echo "  3. Visit: https://127.0.0.1:5000"
echo ""
echo "Helpful commands:"
echo "  ./scripts/app_manager.sh status   - Check app health"
echo "  ./scripts/app_manager.sh logs     - View logs"
echo "  ./scripts/app_manager.sh restart  - Restart app"
echo ""
