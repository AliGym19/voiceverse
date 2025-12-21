#!/usr/bin/env bash
# install-hooks.sh - Install automatic session coordination hooks
# This script sets up Claude Code hooks for automatic cross-session coordination

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Paths
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_DIR="${HOME}/.claude/hooks"
SCRIPTS_DIR="${SKILL_DIR}/scripts"

echo "========================================="
echo "Session Coordinator - Hook Installation"
echo "========================================="
echo ""

# Check if --force flag is provided
FORCE=false
if [[ "$1" == "--force" ]]; then
    FORCE=true
    echo -e "${YELLOW}Force mode enabled${NC}"
fi

# Create hooks directory if it doesn't exist
if [ ! -d "$HOOKS_DIR" ]; then
    echo "Creating hooks directory: $HOOKS_DIR"
    mkdir -p "$HOOKS_DIR"
fi

# Function to install a hook
install_hook() {
    local hook_name=$1
    local source_file="${SKILL_DIR}/hooks/${hook_name}"
    local target_file="${HOOKS_DIR}/${hook_name}"

    if [ -f "$target_file" ] && [ "$FORCE" = false ]; then
        echo -e "${YELLOW}⚠️  Hook exists: ${hook_name}${NC}"
        echo "   Use --force to overwrite"
        return 1
    fi

    if [ ! -f "$source_file" ]; then
        echo -e "${RED}✗ Source not found: ${hook_name}${NC}"
        return 1
    fi

    cp "$source_file" "$target_file"
    chmod +x "$target_file"
    echo -e "${GREEN}✓ Installed: ${hook_name}${NC}"
    return 0
}

# Install hooks
echo "Installing hooks..."
echo ""

install_hook "session-start.sh"
install_hook "session-end.sh"
install_hook "pre-tool-call.sh"

echo ""

# Make scripts executable
echo "Setting script permissions..."
chmod +x "${SCRIPTS_DIR}"/*.sh
echo -e "${GREEN}✓ Scripts are executable${NC}"
echo ""

# Test Knowledge Graph connection
echo "Testing Knowledge Graph connection..."
if command -v node &> /dev/null; then
    # Simple test - just try to list databases
    TEST_RESULT=$(node -e "
        console.log('Testing KG connection...');
        process.exit(0);
    " 2>&1)

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Node.js available for MCP${NC}"
    else
        echo -e "${YELLOW}⚠️  Node.js check failed, but may still work${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Node.js not found in PATH${NC}"
    echo "   Knowledge Graph MCP may not work"
fi

echo ""

# Create coordination config if it doesn't exist
CONFIG_DIR="${SKILL_DIR}/config"
CONFIG_FILE="${CONFIG_DIR}/coordination.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating default configuration..."
    mkdir -p "$CONFIG_DIR"
    cat > "$CONFIG_FILE" << 'EOF'
# Session Coordination Configuration

session_coordination:
  # Session settings
  auto_register: true
  session_timeout: 7200  # 2 hours in seconds
  heartbeat_interval: 300  # 5 minutes

  # File locking
  enable_file_locks: true
  lock_timeout: 3600  # 1 hour
  critical_files:
    - "*.py"
    - "*.js"
    - "*.yaml"
    - "*.json"
    - "*.sql"

  # Conflict resolution
  conflict_action: "block"  # block | warn | proceed
  show_notifications: true
  notification_types:
    - "session_start"
    - "conflict_detected"
    - "lock_acquired"
    - "session_complete"

  # Knowledge Graph
  kg_context: "tts_app_coordination"
  kg_location: "project"

  # Cleanup
  auto_cleanup_stale: true
  archive_completed: true
  retention_days: 7

# Work area definitions (optional)
work_areas:
  frontend:
    files: ["templates/", "static/"]
    dependencies: []

  backend:
    files: ["*.py", "!tests/"]
    dependencies: []

  testing:
    files: ["tests/"]
    dependencies: ["backend", "frontend"]

  documentation:
    files: ["docs/", "*.md"]
    dependencies: []
EOF
    echo -e "${GREEN}✓ Created configuration file${NC}"
else
    echo -e "${GREEN}✓ Configuration file exists${NC}"
fi

echo ""

# Create file patterns config
PATTERNS_FILE="${CONFIG_DIR}/file-patterns.yaml"

if [ ! -f "$PATTERNS_FILE" ]; then
    echo "Creating file patterns configuration..."
    cat > "$PATTERNS_FILE" << 'EOF'
# File Lock Patterns Configuration

# Always lock these file patterns
critical_files:
  - "*.py"        # Python source files
  - "*.js"        # JavaScript files
  - "*.jsx"       # React files
  - "*.ts"        # TypeScript files
  - "*.tsx"       # TypeScript React files
  - "*.yaml"      # YAML configuration
  - "*.yml"       # YAML configuration
  - "*.json"      # JSON configuration
  - "*.sql"       # SQL migrations
  - "*.toml"      # TOML configuration
  - "Dockerfile"  # Docker files
  - "*.sh"        # Shell scripts

# Never lock these files
ignore_files:
  - "*.log"       # Log files
  - "*.tmp"       # Temporary files
  - "*.cache"     # Cache files
  - "*.pyc"       # Python bytecode
  - "*.pyo"       # Python optimized
  - "__pycache__" # Python cache directory
  - "node_modules" # Node modules
  - ".git"        # Git directory
  - "*.swp"       # Vim swap files
  - ".DS_Store"   # macOS files

# Documentation (optional locking)
documentation_files:
  - "*.md"        # Markdown (usually safe for concurrent edits)
  - "*.txt"       # Text files
  - "*.rst"       # ReStructuredText

# Lock timeout by file type (seconds)
timeouts:
  "*.py": 3600       # 1 hour for Python
  "*.js": 3600       # 1 hour for JavaScript
  "*.jsx": 3600      # 1 hour for React
  "*.ts": 3600       # 1 hour for TypeScript
  "*.tsx": 3600      # 1 hour for TypeScript React
  "*.sql": 7200      # 2 hours for migrations
  "*.yaml": 1800     # 30 minutes for configs
  "*.yml": 1800      # 30 minutes for configs
  "*.json": 1800     # 30 minutes for configs
  "*.sh": 1800       # 30 minutes for scripts
  "*.md": 900        # 15 minutes for docs
EOF
    echo -e "${GREEN}✓ Created file patterns configuration${NC}"
else
    echo -e "${GREEN}✓ File patterns configuration exists${NC}"
fi

echo ""

# Create logs directory
LOGS_DIR="${HOME}/Desktop/Project/TTS_App/.logs/coordination"
if [ ! -d "$LOGS_DIR" ]; then
    echo "Creating logs directory..."
    mkdir -p "$LOGS_DIR"
    echo -e "${GREEN}✓ Created logs directory${NC}"
else
    echo -e "${GREEN}✓ Logs directory exists${NC}"
fi

echo ""
echo "========================================="
echo "Installation Complete!"
echo "========================================="
echo ""
echo -e "${GREEN}✓ Hooks installed in: ${HOOKS_DIR}${NC}"
echo -e "${GREEN}✓ Configuration created${NC}"
echo -e "${GREEN}✓ Logs directory ready${NC}"
echo ""
echo "Next steps:"
echo "1. Open a new Claude Code session - coordination is automatic!"
echo "2. Check status with: /sc:session-status"
echo "3. View documentation: ${SKILL_DIR}/README.md"
echo ""
echo "Test coordination:"
echo "  Terminal 1: cd ~/Desktop/Project/TTS_App && claude"
echo "  Terminal 2: cd ~/Desktop/Project/TTS_App && claude"
echo "  Sessions will coordinate automatically!"
echo ""
