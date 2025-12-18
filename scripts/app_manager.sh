#!/bin/bash

# VoiceVerse App Manager
# Easily start, stop, restart, and check status of your TTS application

set -e

PROJECT_DIR="/Users/ali/Desktop/Project"
APP_FILE="tts_app19.py"
LOG_FILE="app.log"
PID_FILE=".app.pid"

cd "$PROJECT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function print_status() {
    echo -e "${BLUE}[VoiceVerse]${NC} $1"
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

function is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            # Stale PID file
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

function get_port() {
    # Check if app is listening on port 5000
    lsof -ti:5000 2>/dev/null || echo ""
}

function start_app() {
    print_status "Starting VoiceVerse TTS Application..."

    if is_running; then
        print_warning "App is already running (PID: $(cat $PID_FILE))"
        return 1
    fi

    # Check environment
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        return 1
    fi

    # Start app in background
    print_status "Launching Flask app..."
    nohup python3 "$APP_FILE" >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    # Wait for startup
    sleep 2

    if is_running; then
        PID=$(cat "$PID_FILE")
        print_success "App started successfully (PID: $PID)"
        print_success "Access at: https://127.0.0.1:5000"

        # Show last few log lines
        echo ""
        print_status "Recent logs:"
        tail -n 5 "$LOG_FILE" | sed 's/^/  /'
    else
        print_error "Failed to start app. Check $LOG_FILE for errors."
        return 1
    fi
}

function stop_app() {
    print_status "Stopping VoiceVerse TTS Application..."

    if ! is_running; then
        print_warning "App is not running"

        # Check if port is in use
        PORT_PID=$(get_port)
        if [ -n "$PORT_PID" ]; then
            print_warning "Port 5000 is in use by PID $PORT_PID"
            read -p "Kill this process? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                kill "$PORT_PID"
                print_success "Killed process $PORT_PID"
            fi
        fi
        return 1
    fi

    PID=$(cat "$PID_FILE")
    kill "$PID" 2>/dev/null

    # Wait for process to stop
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            rm -f "$PID_FILE"
            print_success "App stopped successfully"
            return 0
        fi
        sleep 0.5
    done

    # Force kill if still running
    print_warning "Process not responding, forcing shutdown..."
    kill -9 "$PID" 2>/dev/null
    rm -f "$PID_FILE"
    print_success "App force stopped"
}

function restart_app() {
    print_status "Restarting VoiceVerse TTS Application..."
    stop_app
    sleep 1
    start_app
}

function status_app() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🌌 VoiceVerse TTS - Status Check"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Check if running
    if is_running; then
        PID=$(cat "$PID_FILE")
        print_success "App is RUNNING (PID: $PID)"

        # Check memory usage
        MEM=$(ps -o rss= -p "$PID" | awk '{printf "%.1f", $1/1024}')
        echo "  Memory: ${MEM}MB"

        # Check CPU usage
        CPU=$(ps -o %cpu= -p "$PID")
        echo "  CPU: ${CPU}%"

        # Check uptime
        UPTIME=$(ps -o etime= -p "$PID" | xargs)
        echo "  Uptime: $UPTIME"
    else
        print_error "App is NOT RUNNING"
    fi

    echo ""

    # Check port
    PORT_PID=$(get_port)
    if [ -n "$PORT_PID" ]; then
        print_success "Port 5000 is open (PID: $PORT_PID)"
    else
        print_error "Port 5000 is not in use"
    fi

    echo ""

    # Check database
    if [ -f "voiceverse.db" ]; then
        DB_SIZE=$(ls -lh voiceverse.db | awk '{print $5}')
        print_success "Database exists ($DB_SIZE)"
    else
        print_error "Database not found"
    fi

    # Check log file
    if [ -f "$LOG_FILE" ]; then
        LOG_SIZE=$(ls -lh "$LOG_FILE" | awk '{print $5}')
        LOG_LINES=$(wc -l < "$LOG_FILE")
        print_success "Log file exists ($LOG_SIZE, $LOG_LINES lines)"
    else
        print_warning "No log file found"
    fi

    # Check saved audio
    AUDIO_COUNT=$(find saved_audio -name "*.mp3" 2>/dev/null | wc -l | xargs)
    AUDIO_SIZE=$(du -sh saved_audio 2>/dev/null | awk '{print $1}')
    echo "  Audio files: $AUDIO_COUNT files ($AUDIO_SIZE)"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

function tail_logs() {
    print_status "Tailing logs (Ctrl+C to exit)..."
    tail -f "$LOG_FILE"
}

function show_help() {
    echo ""
    echo "🌌 VoiceVerse App Manager"
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|help}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the application"
    echo "  stop     - Stop the application"
    echo "  restart  - Restart the application"
    echo "  status   - Show app status and health"
    echo "  logs     - Tail application logs"
    echo "  help     - Show this help message"
    echo ""
}

# Main command handler
case "$1" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    status)
        status_app
        ;;
    logs)
        tail_logs
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac

exit 0
