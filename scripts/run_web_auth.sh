#!/bin/bash
# gplot Web Server Startup Script (Authentication Mode)
# Starts the Web server with JWT authentication enabled for testing.
# Uses the same JWT secret as conftest.py for test compatibility.

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Locate project root relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

# Test configuration (matches conftest.py)
PORT="${GPLOT_WEB_PORT:-8000}"
JWT_SECRET="test-secret-key-for-secure-testing-do-not-use-in-production"
TOKEN_STORE="/tmp/gplot_test_tokens.json"
LOG_FILE="web_test_server.log"

# Display startup information
echo -e "${GREEN}=== Starting gplot Web Server (Test Auth Mode) ===${NC}"
echo "Port:         ${PORT}"
echo "JWT Secret:   ${JWT_SECRET:0:20}..."
echo "Token Store:  ${TOKEN_STORE}"
echo "Log File:     ${LOG_FILE}"
echo "URL:          http://localhost:${PORT}"
echo "Docs:         http://localhost:${PORT}/docs"
echo ""
echo -e "${BLUE}Note: Uses test JWT secret matching conftest.py${NC}"
echo ""

# Check if port is already in use
if command -v lsof >/dev/null 2>&1; then
    if lsof -i ":${PORT}" >/dev/null 2>&1; then
        echo -e "${YELLOW}Port ${PORT} is already in use:${NC}"
        lsof -i ":${PORT}"
        echo ""
        read -p "Kill existing process and continue? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            lsof -ti ":${PORT}" | xargs kill -9 2>/dev/null || true
            sleep 1
        else
            exit 1
        fi
    fi
fi

# Build and execute command
CMD="uv run python app/main_web.py --host 0.0.0.0 --port ${PORT} --jwt-secret ${JWT_SECRET} --token-store ${TOKEN_STORE}"

echo "Starting server..."
echo "Command: ${CMD}"
echo ""
echo "To create test tokens:"
echo "  python scripts/token_manager.py create --group public --expires 3600"
echo ""
echo "Example proxy mode usage:"
echo "  curl -X POST http://localhost:${PORT}/render \\"
echo "    -H 'Authorization: Bearer <token>' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"title\":\"Test\",\"y1\":[1,2,3],\"proxy\":true}'"
echo ""

# Execute with proper signal handling and logging
exec ${CMD} 2>&1 | tee "${LOG_FILE}"
