#!/usr/bin/env bash
#
# Run tests with coverage reporting
#
# Usage:
#   ./scripts/run_tests_with_coverage.sh [pytest-args]
#
# Examples:
#   ./scripts/run_tests_with_coverage.sh
#   ./scripts/run_tests_with_coverage.sh --with-servers
#   ./scripts/run_tests_with_coverage.sh test/storage/
#

set -e

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running tests with coverage...${NC}"

# Parse arguments to check for --with-servers
WITH_SERVERS=false
PYTEST_ARGS=()
for arg in "$@"; do
    if [ "$arg" == "--with-servers" ]; then
        WITH_SERVERS=true
    else
        PYTEST_ARGS+=("$arg")
    fi
done

# Start servers if requested
if [ "$WITH_SERVERS" == "true" ]; then
    echo -e "${YELLOW}Starting test servers...${NC}"
    
    # Configuration
    export GPLOT_JWT_SECRET="test-secret-key-for-secure-testing-do-not-use-in-production"
    export GPLOT_DATA_DIR="$(pwd)/test/data"
    
    # Start MCP server
    python -m app.main_mcp --port 8001 > test_mcp_server.log 2>&1 &
    MCP_PID=$!
    echo "Started MCP server (PID: $MCP_PID)"
    
    # Start Web server
    python -m app.main_web --port 8000 > test_web_server.log 2>&1 &
    WEB_PID=$!
    echo "Started Web server (PID: $WEB_PID)"
    
    # Start MCPO server
    python -m mcpo --port 8002 --target http://localhost:8001 > test_mcpo_server.log 2>&1 &
    MCPO_PID=$!
    echo "Started MCPO server (PID: $MCPO_PID)"
    
    # Wait for servers to be ready
    echo -e "${YELLOW}Waiting for servers to be ready...${NC}"
    sleep 3
    
    # Cleanup function
    cleanup() {
        echo -e "${YELLOW}Stopping test servers...${NC}"
        kill $MCP_PID $WEB_PID $MCPO_PID 2>/dev/null || true
        wait $MCP_PID $WEB_PID $MCPO_PID 2>/dev/null || true
        echo -e "${GREEN}Servers stopped${NC}"
    }
    trap cleanup EXIT
fi

# Run pytest with coverage
python -m pytest \
    --cov=app \
    --cov-report=html \
    --cov-report=xml \
    --cov-report=term-missing \
    "${PYTEST_ARGS[@]}"

PYTEST_EXIT=$?

# Print coverage summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Coverage Report Generated${NC}"
echo -e "${GREEN}========================================${NC}"
echo "HTML report: file://$(pwd)/htmlcov/index.html"
echo "XML report:  $(pwd)/coverage.xml"
echo ""

# Open HTML report in browser if available
if command -v xdg-open >/dev/null 2>&1; then
    echo "Opening coverage report in browser..."
    xdg-open htmlcov/index.html 2>/dev/null || true
elif command -v open >/dev/null 2>&1; then
    echo "Opening coverage report in browser..."
    open htmlcov/index.html 2>/dev/null || true
fi

exit $PYTEST_EXIT
