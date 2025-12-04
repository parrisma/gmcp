# Security Guide

This document describes the security architecture, authentication mechanisms, and best practices for the gofr-plot project.

## Overview

gofr-plot implements JWT-based authentication with group-level access control for multi-tenant graph rendering and storage. The security model ensures:

- **Authentication**: Valid JWT tokens required for all protected endpoints
- **Authorization**: Group-based isolation prevents cross-tenant data access
- **Token Management**: Centralized token store with revocation support
- **Secure Defaults**: Authentication enabled by default, explicit disable required

## Authentication Architecture

### JWT Token Flow

```
1. Client requests token (external process)
   └─> Token created with group claim
   
2. Client includes token in request
   └─> Header: Authorization: Bearer <token>
   
3. Server validates token
   ├─> Signature verification (HMAC-SHA256)
   ├─> Expiration check
   ├─> Revocation check (token store)
   └─> Extract group claim
   
4. Server authorizes request
   └─> Resource group matches token group
```

### Token Structure

```json
{
  "group": "analytics_team",
  "exp": 1700000000,
  "iat": 1699999000,
  "jti": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Claims:**
- `group` (string): Tenant/group identifier for access control
- `exp` (int): Expiration timestamp (Unix epoch)
- `iat` (int): Issued-at timestamp
- `jti` (string): Unique token identifier (UUID)

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOFR_PLOT_JWT_SECRET` | Yes* | None | Secret key for JWT signing/verification |
| `GOFR_PLOT_TOKEN_STORE` | No | `data/auth/tokens.json` | Path to token store file |
| `GOFR_PLOT_NO_AUTH` | No | `false` | Set to `true` to disable authentication |

\* Required when authentication is enabled

### Server Startup

**Web Server:**
```bash
# With authentication (recommended)
./scripts/run_web.sh --jwt-secret "your-secret-key"

# Without authentication (dev/testing only)
./scripts/run_web.sh --no-auth

# With custom token store
./scripts/run_web.sh --jwt-secret "secret" --token-store /path/to/tokens.json
```

**MCP Server:**
```bash
# With authentication (recommended)
./scripts/run_mcp.sh --jwt-secret "your-secret-key"

# Without authentication (dev/testing only)
./scripts/run_mcp.sh --no-auth
```

### CLI Arguments Priority

Configuration precedence (highest to lowest):
1. Command-line arguments (`--jwt-secret`, `--token-store`, `--no-auth`)
2. Environment variables (`GOFR_PLOT_JWT_SECRET`, `GOFR_PLOT_TOKEN_STORE`, `GOFR_PLOT_NO_AUTH`)
3. Defaults (auth enabled, default token store path)

## Token Management

### Token Store

The token store is a JSON file tracking:
- Active tokens by JWT ID (jti)
- Token metadata (group, expiration, creation time)
- Revoked tokens (for immediate invalidation)

**Location:** Default is `data/auth/tokens.json`, configurable via `GOFR_PLOT_TOKEN_STORE`

**Format:**
```json
{
  "550e8400-e29b-41d4-a716-446655440000": {
    "group": "analytics_team",
    "created_at": "2025-11-22T10:00:00",
    "expires_at": "2025-11-22T11:00:00",
    "revoked": false
  }
}
```

### Creating Tokens

Tokens are created using the `AuthService`:

```python
from app.auth import AuthService

auth_service = AuthService(
    secret_key="your-jwt-secret",
    token_store_path="data/auth/tokens.json"
)

# Create token for a group (default 1 hour expiry)
token = auth_service.create_token(group="analytics_team")

# Create token with custom expiration
token = auth_service.create_token(
    group="analytics_team",
    expires_in_seconds=3600  # 1 hour
)
```

### Token Revocation

```python
# Revoke a specific token
auth_service.revoke_token(token_string)

# Revoke all tokens for a group
auth_service.revoke_group_tokens(group="analytics_team")
```

### Token Scripts

**Create Token:**
```bash
python scripts/token_manager.py create --group analytics_team --expires-in 3600
```

**Revoke Token:**
```bash
python scripts/token_manager.py revoke --token <token-string>
```

**List Tokens:**
```bash
python scripts/token_manager.py list
```

## Group-Based Access Control

### Resource Isolation

Every stored resource (rendered graph) is associated with a group. Access rules:

1. **Rendering**: Token group becomes resource group
2. **Retrieval**: Resource group must match token group
3. **Proxy Mode**: GUID storage includes group metadata

### Implementation

**Web API (403 Forbidden):**
```python
# app/web_server.py
try:
    image_data = storage.get_image(guid, group=auth_group)
except PermissionDeniedError:
    raise HTTPException(status_code=403, detail="Permission denied")
```

**MCP Server (Error Message):**
```python
# app/mcp_server.py
try:
    image_data = storage.get_image(guid, group=auth_group)
except PermissionDeniedError:
    return TextContent(text="Error: Session not found or access denied")
```

### Security Properties

- **No enumeration**: Failed authorization returns same error as missing resource
- **No leakage**: Error messages don't reveal existence of resources
- **Strict matching**: Group comparison is case-sensitive and exact

## API Security

### Web API Endpoints

All endpoints except `/ping` require authentication:

**Protected Endpoints:**
```
POST /render          - Render graph and store
POST /render/direct   - Render graph without storage
GET  /proxy/{guid}    - Retrieve stored image
```

**Unprotected Endpoints:**
```
GET  /ping           - Health check
```

### Request Format

```bash
curl -X POST http://localhost:8000/render \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Graph",
    "x": [1, 2, 3],
    "y": [4, 5, 6]
  }'
```

### Response Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | Success | Request completed successfully |
| 401 | Unauthorized | Missing, invalid, expired, or revoked token |
| 403 | Forbidden | Valid token but group mismatch |
| 404 | Not Found | Resource doesn't exist (or no access) |

## MCP Security

### Tool Authentication

All MCP tools except `ping` require authentication via the `token` parameter:

```python
result = await session.call_tool(
    "render_graph",
    arguments={
        "title": "My Graph",
        "x": [1, 2, 3],
        "y": [4, 5, 6],
        "token": jwt_token
    }
)
```

### Error Handling

Authentication failures return descriptive error messages:

```json
{
  "content": [{
    "type": "text",
    "text": "Error: Authentication required. Token is missing, invalid, or expired."
  }]
}
```

Group mismatch returns:
```json
{
  "content": [{
    "type": "text",
    "text": "Error: Session not found or access denied"
  }]
}
```

## Best Practices

### Production Deployment

1. **Strong Secrets**
   ```bash
   # Generate secure JWT secret
   openssl rand -base64 32
   
   # Set environment variable
   export GOFR_PLOT_JWT_SECRET="<generated-secret>"
   ```

2. **Token Expiration**
   - Set appropriate expiry for your use case (default: 1 hour)
   - Consider shorter expiry for sensitive operations
   - Implement token refresh for long-running sessions

3. **Token Storage Security**
   - Restrict token store file permissions (600)
   - Use secure storage backends for production
   - Implement automatic cleanup of expired tokens

4. **HTTPS Only**
   - Always use HTTPS in production
   - JWT tokens are bearer tokens (possession = access)
   - Use reverse proxy (nginx, Caddy) for TLS termination

5. **Monitoring**
   - Log authentication failures
   - Monitor for unusual access patterns
   - Track token usage by group

### Development & Testing

1. **Test Mode**
   ```bash
   # Use consistent secret for testing
   export GOFR_PLOT_JWT_SECRET="test-secret-key-for-secure-testing-do-not-use-in-production"
   ```

2. **Disable Auth (Local Only)**
   ```bash
   # Only for local development
   ./scripts/run_web.sh --no-auth
   ./scripts/run_mcp.sh --no-auth
   ```

3. **Token Sharing**
   - Use shared token store in tests (`/tmp/gofr-plot_test_tokens.json`)
   - Cleanup between test runs via `run_tests.sh`

### Code Integration

**Dependency Injection:**
```python
from app.auth import AuthService

# Initialize once
auth_service = AuthService(
    secret_key=os.environ["GOFR_PLOT_JWT_SECRET"],
    token_store_path=os.environ.get("GOFR_PLOT_TOKEN_STORE", "data/auth/tokens.json")
)

# Inject into servers
web_server = GraphWebServer(auth_service=auth_service)
set_auth_service(auth_service)  # For MCP
```

**Middleware Pattern:**
```python
# app/auth/middleware.py automatically validates tokens
# No explicit auth calls needed in route handlers
```

## Threat Model

### Protected Against

- ✅ **Unauthorized access**: All protected endpoints require valid tokens
- ✅ **Token tampering**: HMAC signature verification prevents modification
- ✅ **Cross-tenant access**: Group-based authorization enforces isolation
- ✅ **Token reuse after revocation**: Token store checks prevent revoked token usage
- ✅ **Expired token usage**: Expiration timestamps enforced

### Out of Scope

- ⚠️ **Token storage security**: Application-level responsibility
- ⚠️ **Transport encryption**: Use HTTPS/TLS in production
- ⚠️ **Rate limiting**: Implement at reverse proxy level
- ⚠️ **Brute force protection**: Implement at network/application level
- ⚠️ **Token rotation**: Manual revocation and reissuance required

## Security Checklist

**Before Production:**
- [ ] Strong JWT secret configured (32+ random bytes)
- [ ] HTTPS enabled for all endpoints
- [ ] Token store secured (file permissions or external store)
- [ ] Authentication enabled (`--no-auth` not used)
- [ ] Monitoring and logging configured
- [ ] Token expiration policy defined
- [ ] Backup/recovery plan for token store

**For Development:**
- [ ] Test secret configured in environment
- [ ] Token cleanup automated in test runner
- [ ] Auth disabled only for local testing
- [ ] No production secrets in code or tests

## Related Documentation

- [AUTHENTICATION.md](AUTHENTICATION.md) - Detailed token format and validation
- [TESTING.md](TESTING.md) - Testing with authentication
- [DATA_PERSISTENCE.md](DATA_PERSISTENCE.md) - Storage security considerations
