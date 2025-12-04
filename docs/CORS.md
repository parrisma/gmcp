# CORS Configuration

Cross-Origin Resource Sharing (CORS) is configured for both MCP and Web servers to control which origins can access the API.

## Configuration

CORS is controlled via the `GOFR_PLOT_CORS_ORIGINS` environment variable.

### Environment Variable

```bash
# Allow specific origins (recommended for production)
export GOFR_PLOT_CORS_ORIGINS="https://example.com,https://app.example.com"

# Allow common development origins (default if not set)
export GOFR_PLOT_CORS_ORIGINS="http://localhost:3000,http://localhost:8000"

# Allow all origins (not recommended for production)
export GOFR_PLOT_CORS_ORIGINS="*"
```

### Default Behavior

If `GOFR_PLOT_CORS_ORIGINS` is not set, the servers default to:
```
http://localhost:3000,http://localhost:8000
```

This allows development from common frontend dev ports (React, Next.js, etc.).

## CORS Settings

Both servers are configured with:

- **Allow Origins**: Configurable via `GOFR_PLOT_CORS_ORIGINS`
- **Allow Credentials**: `true` (allows cookies and Authorization headers)
- **Allow Methods**: 
  - Web server: `*` (all methods)
  - MCP server: `GET, POST, DELETE` (MCP streamable HTTP methods)
- **Allow Headers**: `*` (all headers, including Authorization)
- **Expose Headers**: 
  - MCP server: `Mcp-Session-Id` (required for MCP protocol)

## Security Considerations

### Production Deployment

**Never use `*` for CORS origins in production.** Always specify exact origins:

```bash
# Good - specific origins
export GOFR_PLOT_CORS_ORIGINS="https://myapp.com,https://www.myapp.com"

# Bad - allows any origin
export GOFR_PLOT_CORS_ORIGINS="*"
```

### Allow Credentials

The servers are configured with `allow_credentials=true` which:

1. Allows cookies and Authorization headers to be sent
2. Requires exact origin matching (wildcards don't work with credentials)
3. Enables authenticated cross-origin requests

### Origin Validation

- Origins must match exactly (including protocol and port)
- Invalid origins receive HTTP 400 (Web server) or are rejected (MCP server)
- CORS preflight requests are automatically handled by middleware

## Testing

Test CORS configuration using preflight requests:

```bash
# Test allowed origin
curl -X OPTIONS http://localhost:8000/ping \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Check response headers:
# - access-control-allow-origin: http://localhost:3000
# - access-control-allow-credentials: true
```

## Implementation Details

### Web Server (FastAPI)

CORS middleware is added during server initialization in `GraphWebServer.__init__`:

```python
self.app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### MCP Server (Starlette)

CORS middleware wraps the Starlette app before starting:

```python
starlette_app = CORSMiddleware(
    starlette_app,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],
)
```

## Examples

### Multiple Origins

```bash
export GOFR_PLOT_CORS_ORIGINS="https://app1.com,https://app2.com,https://admin.app1.com"
```

### Development vs Production

```bash
# Development
export GOFR_PLOT_CORS_ORIGINS="http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000"

# Production
export GOFR_PLOT_CORS_ORIGINS="https://myapp.com,https://www.myapp.com"
```

### Docker Compose

```yaml
services:
  gofr-plot:
    environment:
      - GOFR_PLOT_CORS_ORIGINS=https://myapp.com,https://www.myapp.com
```

## Troubleshooting

### CORS Error in Browser

If you see CORS errors in the browser console:

1. Check the origin is in `GOFR_PLOT_CORS_ORIGINS`
2. Ensure exact match (including protocol: `https://` vs `http://`)
3. Verify port number matches (`:3000` vs `:8000`)
4. Check browser DevTools Network tab for preflight requests

### 400 Bad Request on Preflight

If preflight requests return 400:

1. The origin is not in the allowed list
2. Check `GOFR_PLOT_CORS_ORIGINS` contains the exact origin
3. Restart the server after changing environment variables

### Wildcard Not Working

If `GOFR_PLOT_CORS_ORIGINS="*"` doesn't work:

- This is expected with `allow_credentials=true`
- Browsers reject wildcard origins with credentials
- Use specific origins instead

## Tests

CORS configuration is tested in `test/web/test_cors.py`:

- Default origins (localhost:3000, localhost:8000)
- Custom origin whitelisting
- Blocked origin rejection
- Wildcard configuration
- Preflight request handling
- Actual request CORS headers

Run tests:
```bash
pytest test/web/test_cors.py -v
```
