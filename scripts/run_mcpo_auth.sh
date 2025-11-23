#!/bin/bash
# gplot MCPO Wrapper Startup Script (With Authentication)
# Starts MCPO with API key authentication enabled.

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Locate project root relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

# Default API key for development/testing
DEFAULT_API_KEY="mcpo-dev-test-key-do-not-use-in-production"
MCPO_API_KEY="${GPLOT_MCPO_API_KEY:-${DEFAULT_API_KEY}}"

echo -e "${BLUE}=== Starting MCPO Wrapper (With Authentication) ===${NC}"
echo -e "${GREEN}✓ MCPO API key authentication enabled${NC}"
echo ""

# Call the main run_mcpo.sh script with API key
exec "${SCRIPT_DIR}/run_mcpo.sh" --api-key "${MCPO_API_KEY}" "$@"
