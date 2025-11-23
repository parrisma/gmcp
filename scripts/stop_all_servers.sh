#!/bin/bash
# Stop all gplot servers and verify they are completely terminated
# Stops: MCP, MCPO, Web

set -e  # Exit on error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MCP_PORT=8001
MCPO_PORT=8002
WEB_PORT=8000

# Logging
LOG_FILE="/tmp/gplot_stop_servers.log"
echo "=== Stopping gplot Servers at $(date) ===" > "$LOG_FILE"

# Helper functions
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
    echo "[$(date '+%H:%M:%S')] $1" >> "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
    echo "✓ $1" >> "$LOG_FILE"
}

error() {
    echo -e "${RED}✗${NC} $1"
    echo "✗ $1" >> "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    echo "⚠ $1" >> "$LOG_FILE"
}

# Kill process by pattern and verify
kill_process() {
    local name=$1
    local pattern=$2
    local max_attempts=${3:-10}
    
    log "Stopping $name..."
    
    # Find and kill processes
    local pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    
    if [ -z "$pids" ]; then
        warn "$name was not running"
        return 0
    fi
    
    # Try graceful shutdown first (SIGTERM)
    echo "$pids" | xargs kill -TERM 2>/dev/null || true
    
    # Wait and verify termination
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        pids=$(pgrep -f "$pattern" 2>/dev/null || true)
        if [ -z "$pids" ]; then
            success "$name stopped"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 0.5
    done
    
    # Force kill if still running (SIGKILL)
    pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        warn "$name not responding, force killing..."
        echo "$pids" | xargs kill -KILL 2>/dev/null || true
        sleep 1
        
        # Final verification
        pids=$(pgrep -f "$pattern" 2>/dev/null || true)
        if [ -z "$pids" ]; then
            success "$name force stopped"
            return 0
        else
            error "$name could not be stopped (PIDs: $pids)"
            return 1
        fi
    fi
}

# Kill by port
kill_by_port() {
    local name=$1
    local port=$2
    
    log "Checking port $port for $name..."
    
    local pid=$(lsof -ti:$port 2>/dev/null || true)
    
    if [ -z "$pid" ]; then
        warn "$name not running on port $port"
        return 0
    fi
    
    log "Found $name on port $port (PID: $pid)"
    kill -TERM $pid 2>/dev/null || true
    sleep 1
    
    # Check if still running
    if kill -0 $pid 2>/dev/null; then
        warn "$name not responding, force killing..."
        kill -KILL $pid 2>/dev/null || true
        sleep 1
    fi
    
    # Final verification
    if kill -0 $pid 2>/dev/null; then
        error "$name could not be stopped (PID: $pid)"
        return 1
    else
        success "$name stopped (port $port)"
        return 0
    fi
}

# Verify port is free
verify_port_free() {
    local name=$1
    local port=$2
    
    if lsof -i ":$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
        local pid=$(lsof -i ":$port" -sTCP:LISTEN -t 2>/dev/null || true)
        error "Port $port still in use by process $pid ($name)"
        return 1
    else
        success "Port $port is free ($name)"
        return 0
    fi
}

# Main shutdown sequence
echo ""
echo "================================================================"
echo "  Stopping gplot Server Stack"
echo "================================================================"
echo ""

ERRORS=0

# Method 1: Stop by process pattern
kill_process "MCP Server" "main_mcp.py" || ERRORS=$((ERRORS + 1))
kill_process "Web Server" "main_web.py" || ERRORS=$((ERRORS + 1))
kill_process "MCPO" "mcpo.*--port $MCPO_PORT" || ERRORS=$((ERRORS + 1))

# Method 2: Stop by port (backup)
kill_by_port "MCP" $MCP_PORT || true
kill_by_port "Web" $WEB_PORT || true
kill_by_port "MCPO" $MCPO_PORT || true

# Clean up PID files
log "Cleaning up PID files..."
rm -f /tmp/gplot_mcp.pid /tmp/gplot_web.pid /tmp/gplot_mcpo.pid 2>/dev/null || true
success "PID files removed"

echo ""
log "Verifying all services are stopped..."
echo ""

# Verify ports are free
VERIFY_ERRORS=0
verify_port_free "MCP" $MCP_PORT || VERIFY_ERRORS=$((VERIFY_ERRORS + 1))
verify_port_free "Web" $WEB_PORT || VERIFY_ERRORS=$((VERIFY_ERRORS + 1))
verify_port_free "MCPO" $MCPO_PORT || VERIFY_ERRORS=$((VERIFY_ERRORS + 1))

# Additional process verification
log "Double-checking for any remaining processes..."
remaining=$(pgrep -f "main_mcp.py|main_web.py|mcpo.*--port" 2>/dev/null || true)
if [ -n "$remaining" ]; then
    error "Some processes still running: $remaining"
    VERIFY_ERRORS=$((VERIFY_ERRORS + 1))
else
    success "No remaining server processes"
fi

echo ""
echo "================================================================"
if [ $ERRORS -eq 0 ] && [ $VERIFY_ERRORS -eq 0 ]; then
    success "All servers stopped successfully and verified!"
    echo "================================================================"
    echo ""
    echo "📊 Final Status:"
    echo "  ✓ All processes terminated"
    echo "  ✓ All ports released"
    echo "  ✓ PID files cleaned up"
    echo ""
    echo "📝 Log: $LOG_FILE"
    echo "🚀 To restart: bash scripts/run_all_servers.sh"
    echo "================================================================"
    echo ""
    exit 0
else
    error "Some servers could not be stopped cleanly"
    echo "================================================================"
    echo ""
    echo "⚠️  Issues detected:"
    echo "  Stop errors:         $ERRORS"
    echo "  Verification errors: $VERIFY_ERRORS"
    echo ""
    echo "📝 Check log: $LOG_FILE"
    echo ""
    echo "Manual cleanup commands:"
    echo "  Kill processes:  pkill -9 -f 'main_mcp.py|main_web.py|mcpo'"
    echo "  Free port 8001:  kill -9 \$(lsof -ti:8001)"
    echo "  Free port 8000:  kill -9 \$(lsof -ti:8000)"
    echo "  Free port 8002:  kill -9 \$(lsof -ti:8002)"
    echo "  Check ports:     lsof -i :8001 -i :8000 -i :8002"
    echo "================================================================"
    echo ""
    exit 1
fi
