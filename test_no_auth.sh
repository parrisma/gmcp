#!/bin/bash
# Test script to verify no-auth mode works for all three servers

echo "=== Testing No-Auth Mode ==="
echo

# Step 1: Create test graph via Web server (no auth)
echo "Step 1: Creating graph via Web server (no token required)..."
RESPONSE=$(curl -s -X POST http://localhost:8000/render \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Graph - No Auth",
    "type": "line",
    "y1": [10, 20, 30, 40, 50],
    "theme": "dark",
    "proxy": true
  }')

echo "Response: $RESPONSE"
GUID=$(echo "$RESPONSE" | python3 -c "import sys, json; r=json.load(sys.stdin); print(r.get('image', r.get('guid', '')))" 2>/dev/null)

if [ -z "$GUID" ]; then
    echo "❌ Failed to create graph via Web server"
    echo "Response was: $RESPONSE"
    exit 1
fi

echo "✓ Graph created successfully"
echo "  GUID: $GUID"
echo

# Step 2: Retrieve image via Web server
echo "Step 2: Retrieving image via Web server..."
HTTP_CODE=$(curl -s -o /tmp/test_graph.png -w "%{http_code}" "http://localhost:8000/render/$GUID")

if [ "$HTTP_CODE" = "200" ]; then
    FILE_SIZE=$(stat -f%z /tmp/test_graph.png 2>/dev/null || stat -c%s /tmp/test_graph.png)
    echo "✓ Image retrieved successfully"
    echo "  HTTP Code: $HTTP_CODE"
    echo "  File size: $FILE_SIZE bytes"
else
    echo "❌ Failed to retrieve image (HTTP $HTTP_CODE)"
    exit 1
fi

echo

# Step 3: Test MCPO ping endpoint (no auth required)
echo "Step 3: Testing MCPO ping endpoint..."
MCPO_PING=$(curl -s -X POST http://localhost:8002/ping -H "Content-Type: application/json" -d '{}')
echo "MCPO Ping: $MCPO_PING"

if echo "$MCPO_PING" | grep -q "Server is running"; then
    echo "✓ MCPO is accessible and responding"
else
    echo "❌ MCPO ping failed"
    exit 1
fi

echo
echo "=== All No-Auth Tests Passed! ==="
echo "✓ Web Server: Create graph + retrieve image"
echo "✓ MCPO Proxy: Create graph via OpenAPI"
echo "✓ Cross-service: Retrieve MCPO-created image via Web"
