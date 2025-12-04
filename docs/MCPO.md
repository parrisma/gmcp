# MCPO (Model Context Protocol to OpenAPI) Integration

## Overview

MCPO is a proxy layer that exposes the gofr-plot MCP server as OpenAPI-compatible REST endpoints. This enables integration with OpenWebUI, LangChain, and other tools that consume OpenAPI specifications rather than native MCP.

**Architecture:**
```
LLM Client (OpenWebUI, etc.) → MCPO (port 8002) → MCP Server (port 8001) → gofr-plot rendering
```

## Quick Start

### 1. Start MCP Server
```bash
# Terminal 1: Start the MCP server
./scripts/run_mcp.sh

# Or with authentication:
export GOFR_PLOT_JWT_SECRET="your-secret-key"
./scripts/run_mcp.sh
```

### 2. Start MCPO Wrapper (Choose One Method)

#### Option A: Python Wrapper (Recommended)
```bash
# Terminal 2: Start MCPO using Python wrapper
export GOFR_PLOT_MCP_PORT=8001
export GOFR_PLOT_MCPO_PORT=8002
python -m app.main_mcpo
```

#### Option B: Shell Script
```bash
# Terminal 2: Start MCPO using shell script
./scripts/run_mcpo.sh
```

#### Option C: Direct uv Command
```bash
# Terminal 2: Start MCPO directly
uv tool run mcpo --port 8002 --server-type streamable-http -- http://localhost:8001/mcp
```

### 3. Verify MCPO is Running
```bash
# Check OpenAPI specification
curl http://localhost:8002/openapi.json | jq .

# Test ping endpoint (no auth required)
curl -X POST http://localhost:8002/ping \
  -H "Content-Type: application/json" \
  -d '{}'

# List available tools
curl http://localhost:8002/tools/list \
  -H "Content-Type: application/json"
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOFR_PLOT_MCP_PORT` | 8001 | Port where MCP server is running |
| `GOFR_PLOT_MCPO_PORT` | 8002 | Port for MCPO proxy to listen on |
| `GOFR_PLOT_MCPO_API_KEY` | None | Optional API key for MCPO authentication layer |
| `GOFR_PLOT_JWT_TOKEN` | None | JWT token to pass through to MCP server (authenticated mode) |
| `GOFR_PLOT_MCPO_MODE` | public | Mode: `auth` (pass JWT) or `public` (no JWT) |

### Authentication Modes

#### 1. Public Mode (Default)
No authentication at MCPO layer. MCP handles all JWT auth.

```bash
python -m app.main_mcpo
```

#### 2. MCPO API Key Mode
Protect MCPO endpoints with an API key (but no JWT to MCP):

```bash
export GOFR_PLOT_MCPO_API_KEY="your-api-key-here"
python -m app.main_mcpo

# Use it:
curl -X POST http://localhost:8002/render_graph \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"title": "Test", "y1": [1,2,3], "token": "your-jwt-token"}'
```

#### 3. Authenticated Mode
Pass a JWT token through to MCP for all requests:

```bash
export GOFR_PLOT_JWT_TOKEN="your-jwt-token"
export GOFR_PLOT_MCPO_MODE="auth"
python -m app.main_mcpo

# MCP will receive the JWT automatically
curl -X POST http://localhost:8002/render_graph \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "y1": [1,2,3]}'
```

## Python Wrapper API

The `MCPOWrapper` class provides programmatic control:

```python
from app.mcpo.wrapper import start_mcpo_wrapper

# Start MCPO wrapper
wrapper = start_mcpo_wrapper(
    mcp_host="localhost",
    mcp_port=8001,
    mcpo_port=8002,
    mcpo_api_key=None,  # Optional: API key for MCPO auth
    auth_token=None,    # Optional: JWT token for MCP auth
    use_auth=False      # True to pass token to MCP
)

# Check if running
if wrapper.is_running():
    print("MCPO is running!")

# Stop wrapper
wrapper.stop()
```

### Async Usage
```python
import asyncio
from app.mcpo.wrapper import start_mcpo_wrapper

async def main():
    wrapper = start_mcpo_wrapper(mcpo_port=8002)
    try:
        await wrapper.run_async()  # Runs until interrupted
    except KeyboardInterrupt:
        wrapper.stop()

asyncio.run(main())
```

## OpenAPI Endpoints

Once MCPO is running, the following REST endpoints are available:

### 1. Ping (Health Check)
```bash
POST /ping
Body: {}
Response: "Server is running\nTimestamp: ...\nService: gofr-plot"
```

### 2. Render Graph
```bash
POST /render_graph
Body: {
  "title": "My Chart",
  "y1": [1, 2, 3, 4, 5],
  "x": [0, 1, 2, 3, 4],
  "token": "your-jwt-token",
  "chart_type": "line",
  "theme": "light",
  "format": "png"
}
Response: {
  "image": "base64-encoded-image-data..."
}
```

### 3. List Themes
```bash
POST /list_themes
Body: {}
Response: "Available themes:\n- light: ...\n- dark: ..."
```

### 4. List Handlers
```bash
POST /list_handlers
Body: {}
Response: "Available chart types:\n- line: ...\n- bar: ..."
```

### 5. Get Image (Proxy Mode)
```bash
POST /get_image
Body: {
  "guid": "uuid-from-render-graph",
  "token": "your-jwt-token"
}
Response: {
  "image": "base64-encoded-image-data...",
  "format": "png"
}
```

## OpenWebUI Integration

### 1. Configure OpenWebUI

Add gofr-plot as an OpenAPI function in OpenWebUI:

1. Navigate to **Workspace → Functions**
2. Click **+ New Function**
3. Select **Add from OpenAPI Spec**
4. Enter: `http://localhost:8002/openapi.json`
5. Click **Import**

### 2. Use in Chat

Once imported, OpenWebUI will automatically call gofr-plot tools when needed:

```
User: "Create a line chart showing sales data: [100, 150, 200, 180, 220]"
AI: [Calls render_graph tool via MCPO]
AI: "Here's your sales chart: [displays image]"
```

### 3. Authentication

If using JWT tokens with gofr-plot:

1. Generate a token:
   ```bash
   python scripts/token_manager.py add test_user test_group
   ```

2. Configure in OpenWebUI function settings:
   - Add default parameter: `token=your-jwt-token-here`
   - Or configure as environment variable

## Testing

### Manual Testing

```bash
# Test MCPO integration manually
export GOFR_PLOT_JWT_SECRET="test-secret"
export GOFR_PLOT_TOKEN_STORE="/tmp/test_tokens.json"

# Start servers
./scripts/run_mcp.sh &
python -m app.main_mcpo &

# Create test token
python scripts/token_manager.py add test_user test_group

# Use the token
curl -X POST http://localhost:8002/render_graph \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Chart",
    "y1": [1, 2, 3, 4, 5],
    "token": "<token-from-above>",
    "chart_type": "line"
  }'
```

### Automated Testing

Run full test suite including MCPO tests:

```bash
# Run all tests with MCPO integration
./scripts/run_tests.sh --with-mcpo

# Run only MCPO tests
pytest test/mcpo/ -v
```

The test suite includes:
- **test_mcpo_openapi.py**: 17 tests for MCPO functionality
  - Health and OpenAPI spec validation
  - Tool invocation (ping, list_themes, list_handlers, render_graph)
  - Authentication tests (missing token, invalid token, valid token)
  - Proxy mode tests (GUID workflow, cross-group access)
  - Multi-dataset rendering
  - Error handling

Tests are automatically skipped if MCPO is not running (use `--with-mcpo` flag).

## Architecture Details

### Components

1. **MCP Server** (`app/main_mcp.py`)
   - Native MCP protocol (streamable HTTP)
   - Runs on port 8001
   - Handles JWT authentication
   - Provides tools: render_graph, get_image, ping, list_themes, list_handlers

2. **MCPO Proxy** (`mcpo` tool)
   - Translates OpenAPI REST → MCP protocol
   - Runs on port 8002
   - Exposes MCP tools as POST endpoints
   - Provides /openapi.json specification

3. **MCPO Wrapper** (`app/mcpo/wrapper.py`)
   - Python wrapper for managing mcpo subprocess
   - Handles lifecycle (start, stop, health checks)
   - Supports authenticated/public modes
   - Environment variable resolution

### Data Flow

#### Basic Render Request
```
1. LLM → POST /render_graph → MCPO (port 8002)
2. MCPO → MCP tools/call → MCP Server (port 8001)
3. MCP Server → Validates JWT token
4. MCP Server → Renders graph with matplotlib
5. MCP Server → Returns base64 image → MCPO
6. MCPO → Returns JSON response → LLM
```

#### Proxy Mode Workflow
```
1. LLM → POST /render_graph (proxy=true) → MCPO
2. MCPO → MCP tools/call → MCP Server
3. MCP Server → Saves image to storage
4. MCP Server → Returns GUID → MCPO
5. MCPO → Returns {"guid": "..."} → LLM

Later:
6. LLM → POST /get_image (guid) → MCPO
7. MCPO → MCP tools/call → MCP Server
8. MCP Server → Retrieves from storage
9. MCP Server → Returns base64 image → MCPO
10. MCPO → Returns JSON response → LLM
```

## Troubleshooting

### MCPO Not Starting

**Symptom:** `uv tool run mcpo` fails or port 8002 already in use

**Solution:**
```bash
# Check if something is using port 8002
lsof -i :8002

# Kill existing mcpo processes
pkill -9 -f mcpo

# Check if MCP server is running
curl http://localhost:8001/
# Should return 404 (expected)

# Restart MCPO
python -m app.main_mcpo
```

### Connection Refused

**Symptom:** `curl http://localhost:8002/openapi.json` fails

**Solution:**
1. Verify MCP server is running:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/
   # Should return 404
   ```

2. Check MCPO process:
   ```bash
   ps aux | grep mcpo
   ```

3. Check logs:
   ```bash
   # If using test runner:
   tail -f /tmp/gofr-plot_mcpo_test.log
   ```

### Authentication Errors

**Symptom:** 401 Unauthorized or "Invalid token"

**Solution:**
1. Verify token is valid:
   ```bash
   python scripts/token_manager.py list
   ```

2. Check token expiry:
   ```bash
   python scripts/token_manager.py verify <token>
   ```

3. Regenerate token:
   ```bash
   python scripts/token_manager.py add test_user test_group
   ```

### OpenAPI Spec Not Loading

**Symptom:** OpenWebUI can't import the spec

**Solution:**
1. Verify spec is valid JSON:
   ```bash
   curl http://localhost:8002/openapi.json | jq .
   ```

2. Check MCPO is exposing gofr-plot service:
   ```bash
   curl http://localhost:8002/openapi.json | jq '.info.title'
   # Should return: "gofr-plot-renderer"
   ```

3. Test direct tool call:
   ```bash
   curl -X POST http://localhost:8002/ping -H "Content-Type: application/json" -d '{}'
   ```

## Performance Considerations

### MCPO Overhead

MCPO adds minimal overhead (<10ms per request) for protocol translation:
- REST JSON → MCP binary protocol
- Automatic serialization/deserialization
- HTTP connection pooling

### Scaling

For production deployments:

1. **Multiple MCPO instances:**
   ```bash
   # Instance 1
   python -m app.main_mcpo --mcpo-port 8002
   
   # Instance 2
   python -m app.main_mcpo --mcpo-port 8003
   
   # Load balancer in front
   ```

2. **Separate MCPO per MCP server:**
   ```bash
   # MCP 1 + MCPO 1
   python app/main_mcp.py --port 8001 &
   python -m app.main_mcpo --mcp-port 8001 --mcpo-port 8002 &
   
   # MCP 2 + MCPO 2 (use different port range to avoid conflicts)
   python app/main_mcp.py --port 9001 &
   python -m app.main_mcpo --mcp-port 9001 --mcpo-port 9002 &
   ```

## Related Documentation

- **[MCP_README.md](MCP_README.md)**: Native MCP protocol details
- **[AUTHENTICATION.md](AUTHENTICATION.md)**: JWT token management
- **[PROXY_MODE.md](PROXY_MODE.md)**: Image persistence and retrieval
- **[N8N_INTEGRATION.md](N8N_INTEGRATION.md)**: Alternative integration via n8n
- **[TEST_MCP.md](TEST_MCP.md)**: MCP testing guide
- **[TEST_WEB.md](TEST_WEB.md)**: Web API testing guide

## Dependencies

- **mcpo**: Model Context Protocol to OpenAPI proxy (>=0.0.19)
- **requests**: HTTP library for testing (>=2.32.5)
- **uv**: Fast Python package installer

Install via:
```bash
uv pip install mcpo requests
# or
uv tool install mcpo
```

## Summary

MCPO enables seamless integration of gofr-plot's MCP server with OpenAPI-compatible tools like OpenWebUI, providing:

✅ RESTful endpoints for all gofr-plot tools  
✅ Automatic OpenAPI 3.1 specification generation  
✅ Flexible authentication (public, API key, JWT passthrough)  
✅ Minimal performance overhead  
✅ Simple deployment (Python wrapper or shell script)  
✅ Full test coverage (17 automated tests)  

The Python wrapper provides the most control and best integration with gofr-plot's architecture, while the shell script offers quick standalone usage.
