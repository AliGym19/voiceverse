#!/usr/bin/env bash
# session-manager.sh - Main session coordination script
# Manages session registration, conflict detection, and cleanup

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="${SKILL_DIR}/config/coordination.yaml"
LOGS_DIR="${HOME}/Desktop/Project/TTS_App/.logs/coordination"
MARKER_DIR="${HOME}/.claude/session-markers"

# Ensure directories exist
mkdir -p "$LOGS_DIR" "$MARKER_DIR"

# Function to display usage
usage() {
    cat << EOF
Session Manager - Multi-Session Coordination Tool

Usage: $0 <command> [options]

Commands:
    register        Register a new session
    status          Show all active sessions
    locks           Show all file locks
    unlock <file>   Release file lock (use with caution)
    cleanup         Clean up stale sessions
    refresh         Refresh coordination state
    history         Show session history
    test            Test coordination setup

Options:
    --force         Force operation (for unlock, cleanup)
    --session-id    Specify session ID
    --help          Show this help message

Examples:
    $0 register
    $0 status
    $0 unlock auth.py --force
    $0 cleanup --force
    $0 test

EOF
    exit 1
}

# Function to check if Knowledge Graph is available
check_kg_available() {
    # Note: This is a placeholder. Actual KG operations happen in Claude Code
    # using MCP tools. This script provides shell utilities and markers.
    return 0
}

# Function to get active sessions from markers
get_active_sessions() {
    if [ ! -d "$MARKER_DIR" ]; then
        return 0
    fi

    local count=0
    for marker in "$MARKER_DIR"/Session_*; do
        if [ -f "$marker" ]; then
            ((count++))
        fi
    done

    echo "$count"
}

# Function to display session status
show_status() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════${NC}"
    echo -e "${BLUE}   Active Sessions${NC}"
    echo -e "${BLUE}═══════════════════════════════════${NC}"
    echo ""

    local count=0

    if [ ! -d "$MARKER_DIR" ]; then
        echo -e "${YELLOW}No active sessions found${NC}"
        echo ""
        return 0
    fi

    for marker in "$MARKER_DIR"/Session_*; do
        if [ -f "$marker" ]; then
            ((count++))

            # Read marker file
            source "$marker"

            # Calculate duration
            if [ -n "$SESSION_START" ]; then
                START_EPOCH=$(date -jf "%Y-%m-%dT%H:%M:%SZ" "$SESSION_START" +%s 2>/dev/null || echo "0")
                NOW_EPOCH=$(date +%s)
                DURATION=$((NOW_EPOCH - START_EPOCH))
                MINUTES=$((DURATION / 60))
                DURATION_STR="${MINUTES} min"
            else
                DURATION_STR="unknown"
            fi

            echo -e "${GREEN}Session ${count}:${NC} $(basename "$marker")"
            echo "  PID: ${PID:-unknown}"
            echo "  Started: ${SESSION_START:-unknown}"
            echo "  Duration: $DURATION_STR"
            echo "  Status: ${STATUS:-unknown}"
            echo "  Directory: ${PWD:-unknown}"
            echo ""
        fi
    done

    if [ $count -eq 0 ]; then
        echo -e "${YELLOW}No active sessions found${NC}"
        echo ""
        echo "Sessions auto-register when Claude Code starts."
        echo "Open a new terminal and run: cd ~/Desktop/Project/TTS_App && claude"
    fi

    echo ""
}

# Function to show file locks
show_locks() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════${NC}"
    echo -e "${BLUE}   File Locks${NC}"
    echo -e "${BLUE}═══════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Note: File lock data is stored in Knowledge Graph${NC}"
    echo "Use Claude Code to query locks:"
    echo "  aim_search_nodes(\"lock_\")"
    echo ""
}

# Function to test coordination setup
test_coordination() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════${NC}"
    echo -e "${BLUE}   Testing Coordination Setup${NC}"
    echo -e "${BLUE}═══════════════════════════════════${NC}"
    echo ""

    # Check directories
    echo -n "Checking logs directory... "
    if [ -d "$LOGS_DIR" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC} (creating...)"
        mkdir -p "$LOGS_DIR"
    fi

    echo -n "Checking marker directory... "
    if [ -d "$MARKER_DIR" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC} (creating...)"
        mkdir -p "$MARKER_DIR"
    fi

    # Check hooks
    echo -n "Checking session-start hook... "
    if [ -f "${HOME}/.claude/hooks/session-start.sh" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC} (run install-hooks.sh)"
    fi

    echo -n "Checking session-end hook... "
    if [ -f "${HOME}/.claude/hooks/session-end.sh" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC} (run install-hooks.sh)"
    fi

    echo -n "Checking pre-tool-call hook... "
    if [ -f "${HOME}/.claude/hooks/pre-tool-call.sh" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC} (run install-hooks.sh)"
    fi

    # Check configuration
    echo -n "Checking configuration... "
    if [ -f "$CONFIG_FILE" ]; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC} (run install-hooks.sh)"
    fi

    # Check active sessions
    echo ""
    local session_count=$(get_active_sessions)
    echo "Active sessions: $session_count"

    echo ""
    echo -e "${GREEN}Setup verification complete!${NC}"
    echo ""

    if [ $session_count -eq 0 ]; then
        echo "To test coordination:"
        echo "  1. Open Terminal 1: cd ~/Desktop/Project/TTS_App && claude"
        echo "  2. Open Terminal 2: cd ~/Desktop/Project/TTS_App && claude"
        echo "  3. Both sessions will coordinate automatically"
    fi

    echo ""
}

# Function to cleanup stale sessions
cleanup_stale() {
    local force=$1
    echo ""
    echo -e "${BLUE}═══════════════════════════════════${NC}"
    echo -e "${BLUE}   Cleaning Up Stale Sessions${NC}"
    echo -e "${BLUE}═══════════════════════════════════${NC}"
    echo ""

    if [ ! -d "$MARKER_DIR" ]; then
        echo -e "${YELLOW}No sessions to clean up${NC}"
        echo ""
        return 0
    fi

    local cleaned=0
    local now=$(date +%s)

    for marker in "$MARKER_DIR"/Session_*; do
        if [ -f "$marker" ]; then
            source "$marker"

            # Check if process is still running
            if [ -n "$PID" ]; then
                if ! kill -0 "$PID" 2>/dev/null; then
                    echo -e "${YELLOW}Stale session found:${NC} $(basename "$marker")"
                    echo "  PID $PID is not running"

                    if [ "$force" = true ]; then
                        # Archive the marker
                        ARCHIVE_DIR="${LOGS_DIR}/archived-sessions"
                        mkdir -p "$ARCHIVE_DIR"
                        mv "$marker" "${ARCHIVE_DIR}/$(basename "$marker")" 2>/dev/null || true
                        echo -e "  ${GREEN}✓ Cleaned up${NC}"
                        ((cleaned++))
                    else
                        echo "  Use --force to clean up"
                    fi
                    echo ""
                fi
            fi
        fi
    done

    if [ $cleaned -eq 0 ]; then
        echo -e "${GREEN}No stale sessions to clean up${NC}"
    else
        echo -e "${GREEN}Cleaned up $cleaned stale session(s)${NC}"
    fi

    echo ""
}

# Function to show history
show_history() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════${NC}"
    echo -e "${BLUE}   Session History${NC}"
    echo -e "${BLUE}═══════════════════════════════════${NC}"
    echo ""

    ARCHIVE_DIR="${LOGS_DIR}/archived-sessions"

    if [ ! -d "$ARCHIVE_DIR" ] || [ -z "$(ls -A "$ARCHIVE_DIR" 2>/dev/null)" ]; then
        echo -e "${YELLOW}No session history found${NC}"
        echo ""
        return 0
    fi

    local count=0
    for marker in "$ARCHIVE_DIR"/Session_*; do
        if [ -f "$marker" ]; then
            ((count++))
            source "$marker"

            echo -e "${GREEN}Session $(basename "$marker"):${NC}"
            echo "  Started: ${SESSION_START:-unknown}"
            echo "  Status: ${STATUS:-unknown}"
            echo "  Directory: ${PWD:-unknown}"
            echo ""

            if [ $count -ge 10 ]; then
                echo -e "${YELLOW}Showing last 10 sessions...${NC}"
                break
            fi
        fi
    done

    echo ""
}

# Main script logic
main() {
    if [ $# -eq 0 ]; then
        usage
    fi

    local command=$1
    shift

    case "$command" in
        register)
            echo "Session registration happens automatically on Claude Code start"
            echo "Check ${HOME}/.claude/hooks/session-start.sh"
            ;;
        status)
            show_status
            ;;
        locks)
            show_locks
            ;;
        unlock)
            echo "File unlock operations must be done through Claude Code"
            echo "Use: aim_delete_entities([\"lock_filename\"])"
            ;;
        cleanup)
            local force=false
            if [ "$1" = "--force" ]; then
                force=true
            fi
            cleanup_stale "$force"
            ;;
        refresh)
            echo "Refreshing coordination state..."
            cleanup_stale true
            show_status
            ;;
        history)
            show_history
            ;;
        test)
            test_coordination
            ;;
        --help|-h)
            usage
            ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            usage
            ;;
    esac
}

# Run main function
main "$@"
