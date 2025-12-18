#!/usr/bin/env bash
# session-start.sh - Automatic session registration hook
# This script runs automatically when a Claude Code session starts

# Generate unique session ID
SESSION_ID="Session_$(hostname -s)_$$_$(date +%Y%m%d%H%M%S)"
SESSION_START=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Export for other hooks to use
export CLAUDE_SESSION_ID="$SESSION_ID"
export CLAUDE_SESSION_START="$SESSION_START"

# Log file
LOGS_DIR="${HOME}/Desktop/Project/TTS_App/.logs/coordination"
mkdir -p "$LOGS_DIR"
LOG_FILE="${LOGS_DIR}/session-${SESSION_ID}.log"

# Log session start
echo "=========================================" >> "$LOG_FILE"
echo "Session Started: $SESSION_START" >> "$LOG_FILE"
echo "Session ID: $SESSION_ID" >> "$LOG_FILE"
echo "PID: $$" >> "$LOG_FILE"
echo "Working Directory: $(pwd)" >> "$LOG_FILE"
echo "=========================================" >> "$LOG_FILE"

# Note: Actual Knowledge Graph operations will be handled by Claude Code
# using the mcp__knowledge-graph tools, as bash cannot directly call MCP servers

# Create a marker file that Claude Code can detect
MARKER_DIR="${HOME}/.claude/session-markers"
mkdir -p "$MARKER_DIR"
MARKER_FILE="${MARKER_DIR}/${SESSION_ID}"

cat > "$MARKER_FILE" << EOF
SESSION_ID=${SESSION_ID}
SESSION_START=${SESSION_START}
PID=$$
PWD=$(pwd)
STATUS=starting
EOF

echo "Session marker created: $MARKER_FILE" >> "$LOG_FILE"

# Display coordination message (Claude will see this)
cat << EOF

🔗 Session Coordination Active
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Session ID: ${SESSION_ID}
Status: Registering...

To complete registration, Claude will:
1. Check for other active sessions
2. Register this session in Knowledge Graph
3. Display coordination status

EOF

exit 0
