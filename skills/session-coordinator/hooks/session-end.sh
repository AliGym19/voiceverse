#!/usr/bin/env bash
# session-end.sh - Automatic session cleanup hook
# This script runs automatically when a Claude Code session ends

# Get session ID from environment or generate one
SESSION_ID="${CLAUDE_SESSION_ID:-Session_$(hostname -s)_$$}"
SESSION_END=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Log file
LOGS_DIR="${HOME}/Desktop/Project/TTS_App/.logs/coordination"
LOG_FILE="${LOGS_DIR}/session-${SESSION_ID}.log"

# Log session end
if [ -f "$LOG_FILE" ]; then
    echo "" >> "$LOG_FILE"
    echo "=========================================" >> "$LOG_FILE"
    echo "Session Ended: $SESSION_END" >> "$LOG_FILE"

    # Calculate duration if we have start time
    if [ -n "$CLAUDE_SESSION_START" ]; then
        START_EPOCH=$(date -jf "%Y-%m-%dT%H:%M:%SZ" "$CLAUDE_SESSION_START" +%s 2>/dev/null || echo "0")
        END_EPOCH=$(date +%s)
        DURATION=$((END_EPOCH - START_EPOCH))
        MINUTES=$((DURATION / 60))
        echo "Duration: ${MINUTES} minutes" >> "$LOG_FILE"
    fi

    echo "=========================================" >> "$LOG_FILE"
fi

# Remove session marker
MARKER_DIR="${HOME}/.claude/session-markers"
MARKER_FILE="${MARKER_DIR}/${SESSION_ID}"

if [ -f "$MARKER_FILE" ]; then
    # Update status before removal
    sed -i '' 's/STATUS=.*/STATUS=completed/' "$MARKER_FILE" 2>/dev/null || true
    echo "Session marker updated: $MARKER_FILE" >> "$LOG_FILE"

    # Archive marker instead of deleting (for history)
    ARCHIVE_DIR="${LOGS_DIR}/archived-sessions"
    mkdir -p "$ARCHIVE_DIR"
    mv "$MARKER_FILE" "${ARCHIVE_DIR}/$(basename "$MARKER_FILE")" 2>/dev/null || true
fi

# Note: Claude Code will handle Knowledge Graph cleanup using MCP tools
# This includes:
# - Releasing file locks
# - Updating session status
# - Archiving session data

# Display cleanup message
cat << EOF

🧹 Session Cleanup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Session: ${SESSION_ID}
Status: Cleanup initiated

Claude will:
1. Release all file locks
2. Update session status to completed
3. Archive session data

EOF

exit 0
