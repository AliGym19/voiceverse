#!/usr/bin/env bash
# pre-tool-call.sh - Pre-operation conflict detection hook
# This script runs before file edit/write operations

# Check if this is a file operation that needs coordination
TOOL_NAME="$1"
FILE_PATH="$2"

# Only intercept Edit and Write operations
if [[ "$TOOL_NAME" != "Edit" ]] && [[ "$TOOL_NAME" != "Write" ]]; then
    exit 0  # Allow other operations through
fi

# Skip if no file path provided
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Get session ID
SESSION_ID="${CLAUDE_SESSION_ID:-Session_$(hostname -s)_$$}"

# Log file
LOGS_DIR="${HOME}/Desktop/Project/TTS_App/.logs/coordination"
LOG_FILE="${LOGS_DIR}/session-${SESSION_ID}.log"

# Log the operation attempt
echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Pre-check: ${TOOL_NAME} ${FILE_PATH}" >> "$LOG_FILE"

# Create a conflict marker that Claude can check
CONFLICT_MARKER_DIR="${HOME}/.claude/conflict-checks"
mkdir -p "$CONFLICT_MARKER_DIR"

CONFLICT_MARKER="${CONFLICT_MARKER_DIR}/check-$(basename "$FILE_PATH")-$$"

cat > "$CONFLICT_MARKER" << EOF
TOOL=${TOOL_NAME}
FILE=${FILE_PATH}
SESSION=${SESSION_ID}
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
STATUS=needs_check
EOF

# Note: Claude Code will read this marker and:
# 1. Check Knowledge Graph for file locks using: aim_search_nodes("lock_${filename}")
# 2. If locked by another session -> Display warning and block
# 3. If available -> Create lock: aim_create_entities([{name: "lock_${filename}", ...}])
# 4. Proceed with operation

# The actual lock check and acquisition happens in Claude Code using MCP tools
# This script just signals that a check is needed

exit 0
