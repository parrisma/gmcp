#!/usr/bin/env bash
#
# Check test coverage and enforce minimum thresholds
#
# Usage:
#   ./scripts/check_coverage.sh [min-coverage-percent]
#
# Examples:
#   ./scripts/check_coverage.sh        # Use default 90%
#   ./scripts/check_coverage.sh 85     # Require 85% coverage
#

set -e

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default minimum coverage
MIN_COVERAGE=${1:-90}

echo -e "${GREEN}Checking test coverage (minimum: ${MIN_COVERAGE}%)...${NC}"

# Run coverage if coverage.xml doesn't exist
if [ ! -f "coverage.xml" ]; then
    echo -e "${YELLOW}No coverage data found. Running tests with coverage...${NC}"
    python -m pytest --cov=app --cov-report=xml --cov-report=term-missing -q
fi

# Extract coverage percentage from coverage.xml
if [ -f "coverage.xml" ]; then
    # Parse coverage.xml for line coverage percentage
    COVERAGE=$(python3 << 'EOF'
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('coverage.xml')
    root = tree.getroot()
    line_rate = float(root.attrib.get('line-rate', 0))
    coverage_pct = line_rate * 100
    print(f"{coverage_pct:.2f}")
except Exception as e:
    print("0.00")
EOF
)
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Coverage Check Results${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo "Current coverage: ${COVERAGE}%"
    echo "Required minimum: ${MIN_COVERAGE}%"
    echo ""
    
    # Compare coverage to minimum
    PASS=$(python3 -c "print('PASS' if float('$COVERAGE') >= float('$MIN_COVERAGE') else 'FAIL')")
    
    if [ "$PASS" == "PASS" ]; then
        echo -e "${GREEN}✓ Coverage check passed!${NC}"
        echo ""
        exit 0
    else
        echo -e "${RED}✗ Coverage check failed!${NC}"
        echo -e "${RED}Coverage is below minimum threshold.${NC}"
        echo ""
        echo "To see which lines are missing coverage:"
        echo "  python -m pytest --cov=app --cov-report=term-missing"
        echo ""
        echo "To generate HTML report:"
        echo "  python -m pytest --cov=app --cov-report=html"
        echo "  open htmlcov/index.html"
        echo ""
        exit 1
    fi
else
    echo -e "${RED}Error: coverage.xml not found${NC}"
    echo "Run: python -m pytest --cov=app --cov-report=xml"
    exit 1
fi
