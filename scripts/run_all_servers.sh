#!/bin/bash
# Start all gplot servers in order with verification
# Servers: MCP (8001) -> MCPO (8002) -> Web (8000)

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

# JWT Configuration
JWT_SECRET="${GPLOT_JWT_SECRET:-$(openssl rand -base64 32)}"
TOKEN_STORE="${GPLOT_TOKEN_STORE:-/tmp/gplot_tokens.json}"

# Logging
LOG_FILE="/tmp/gplot_start_servers.log"
echo "=== Starting gplot Servers at $(date) ===" > "$LOG_FILE"

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

# Check if server is responding
check_server() {
    local name=$1
    local url=$2
    local max_attempts=${3:-30}
    local attempt=0
    
    log "Waiting for $name to be ready..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" 2>&1 | grep -q "200\|404\|405"; then
            success "$name is ready at $url"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    error "$name failed to start within ${max_attempts} seconds"
    return 1
}

# Kill existing servers
cleanup_existing() {
    log "Checking for existing server processes..."
    
    # Kill by port
    for port in $MCP_PORT $MCPO_PORT $WEB_PORT; do
        local pid=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$pid" ]; then
            log "Killing process on port $port (PID: $pid)"
            kill -9 $pid 2>/dev/null || true
            sleep 1
        fi
    done
    
    # Kill by process name
    pkill -9 -f "main_mcp.py" 2>/dev/null || true
    pkill -9 -f "main_web.py" 2>/dev/null || true
    pkill -9 -f "mcpo.*8002" 2>/dev/null || true
    
    sleep 2
    success "Cleanup complete"
}

# Main startup sequence
echo ""
echo "================================================================"
echo "  Starting gplot Server Stack"
echo "================================================================"
echo ""
echo "Configuration:"
echo "  MCP Port:     $MCP_PORT"
echo "  MCPO Port:    $MCPO_PORT"
echo "  Web Port:     $WEB_PORT"
echo "  JWT Secret:   ${JWT_SECRET:0:10}..."
echo "  Token Store:  $TOKEN_STORE"
echo ""

# Cleanup existing processes
cleanup_existing

# 1. MCP Server (8001)
log "Step 1/3: Starting MCP Server on port $MCP_PORT"
nohup python app/main_mcp.py \
    --port $MCP_PORT \
    --jwt-secret "$JWT_SECRET" \
    --token-store "$TOKEN_STORE" \
    > /tmp/mcp_server.log 2>&1 &
MCP_PID=$!
echo $MCP_PID > /tmp/gplot_mcp.pid
log "MCP Server started (PID: $MCP_PID)"

if check_server "MCP Server" "http://localhost:$MCP_PORT/" 30; then
    echo ""
else
    error "MCP Server failed to start. Check /tmp/mcp_server.log"
    exit 1
fi

# 2. Web Server (8000)
log "Step 2/3: Starting Web Server on port $WEB_PORT"
nohup python app/main_web.py \
    --port $WEB_PORT \
    --jwt-secret "$JWT_SECRET" \
    --token-store "$TOKEN_STORE" \
    > /tmp/web_server.log 2>&1 &
WEB_PID=$!
echo $WEB_PID > /tmp/gplot_web.pid
log "Web Server started (PID: $WEB_PID)"

if check_server "Web Server" "http://localhost:$WEB_PORT/ping" 30; then
    echo ""
else
    error "Web Server failed to start. Check /tmp/web_server.log"
    exit 1
fi

# 3. MCPO (8002) - depends on MCP
log "Step 3/3: Starting MCPO on port $MCPO_PORT"

# Check if uv tool is available
if ! command -v uv &> /dev/null; then
    error "uv tool not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Start MCPO wrapper
nohup uv tool run mcpo \
    --port $MCPO_PORT \
    --server-type "streamable-http" \
    -- "http://localhost:$MCP_PORT/mcp" \
    > /tmp/mcpo_server.log 2>&1 &
MCPO_PID=$!
echo $MCPO_PID > /tmp/gplot_mcpo.pid
log "MCPO started (PID: $MCPO_PID)"

if check_server "MCPO" "http://localhost:$MCPO_PORT/openapi.json" 30; then
    echo ""
else
    error "MCPO failed to start. Check /tmp/mcpo_server.log"
    exit 1
fi

# Success summary
echo ""
echo "================================================================"
success "All servers started successfully!"
echo "================================================================"
echo ""
echo "📊 Server Status:"
echo "  ✓ MCP Server:    http://localhost:$MCP_PORT (PID: $MCP_PID)"
echo "  ✓ Web Server:    http://localhost:$WEB_PORT (PID: $WEB_PID)"
echo "  ✓ MCPO:          http://localhost:$MCPO_PORT (PID: $MCPO_PID)"
echo ""
echo "📝 Logs:"
echo "  Startup log:     $LOG_FILE"
echo "  MCP:             /tmp/mcp_server.log"
echo "  Web:             /tmp/web_server.log"
echo "  MCPO:            /tmp/mcpo_server.log"
echo ""
echo "🔑 Authentication:"
echo "  JWT Secret:      $JWT_SECRET"
echo "  Token Store:     $TOKEN_STORE"
echo ""
echo "🌐 API Endpoints:"
echo "  MCP Tools:       http://localhost:$MCP_PORT/"
echo "  Web API:         http://localhost:$WEB_PORT/render"
echo "  MCPO Swagger:    http://localhost:$MCPO_PORT/docs"
echo "  Ping (Web):      http://localhost:$WEB_PORT/ping"
echo "  Ping (MCPO):     http://localhost:$MCPO_PORT/ping"
echo ""
echo "🛑 To stop all servers:"
echo "  pkill -f 'main_mcp.py|main_web.py|mcpo'"
echo "  or kill $MCP_PID $WEB_PID $MCPO_PID"
echo ""
echo "================================================================"
echo ""
