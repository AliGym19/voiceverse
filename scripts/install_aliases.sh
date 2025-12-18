#!/bin/bash

# VoiceVerse Aliases Installer
# Adds VoiceVerse aliases to your shell profile

set -e

PROJECT_DIR="/Users/ali/Desktop/Project"
ALIASES_FILE="$PROJECT_DIR/scripts/aliases.sh"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

function print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

function print_error() {
    echo -e "${RED}✗${NC} $1"
}

function print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🌌 VoiceVerse Aliases Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Detect shell
if [ -n "$ZSH_VERSION" ]; then
    SHELL_NAME="zsh"
    PROFILE_FILE="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_NAME="bash"
    PROFILE_FILE="$HOME/.bash_profile"
    if [ ! -f "$PROFILE_FILE" ]; then
        PROFILE_FILE="$HOME/.bashrc"
    fi
else
    print_error "Unknown shell"
    exit 1
fi

print_info "Detected shell: $SHELL_NAME"
print_info "Profile file: $PROFILE_FILE"
echo ""

# Check if already installed
if grep -q "VoiceVerse aliases" "$PROFILE_FILE" 2>/dev/null; then
    echo "VoiceVerse aliases are already installed in $PROFILE_FILE"
    echo ""
    read -p "Reinstall? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled"
        exit 0
    fi

    # Remove old installation
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' '/# VoiceVerse aliases/,/# End VoiceVerse aliases/d' "$PROFILE_FILE"
    else
        sed -i '/# VoiceVerse aliases/,/# End VoiceVerse aliases/d' "$PROFILE_FILE"
    fi
    print_success "Removed old installation"
fi

# Add aliases to profile
cat >> "$PROFILE_FILE" << EOF

# VoiceVerse aliases
source "$ALIASES_FILE"
# End VoiceVerse aliases
EOF

print_success "Aliases added to $PROFILE_FILE"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_success "Installation complete!"
echo ""
echo "To activate aliases, run one of:"
echo "  source $PROFILE_FILE"
echo "  OR restart your terminal"
echo ""
echo "Available commands:"
echo "  vv-start    - Start the app"
echo "  vv-stop     - Stop the app"
echo "  vv-restart  - Restart the app"
echo "  vv-status   - Check app status"
echo "  vv-logs     - View app logs"
echo "  vv-health   - Run health check"
echo "  vv-backup   - Backup database"
echo "  vv-deploy   - Quick deploy"
echo "  vv-info     - Show all commands"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
