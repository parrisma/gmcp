# Dependency Injection Pattern

## Overview

As of Phase 2, the gplot authentication system supports **dependency injection** for `AuthService` instances, enabling cleaner testing, better modularity, and explicit control over service initialization.

## Architecture

### Web Server (FastAPI)

**GraphWebServer** accepts an optional `AuthService` instance in its constructor:

```python
server = GraphWebServer(
    require_auth=True,
    auth_service=my_auth_service,  # Inject pre-configured service
)
```

**Implementation:**
- `app/web_server.py` - `GraphWebServer.__init__` accepts `auth_service` parameter
- `app/main_web.py` - Creates `AuthService` instance and injects it
- `app/auth/middleware.py` - `init_auth_service()` accepts injected service or creates new one

### MCP Server

**MCP Server** uses a module-level variable with a clean setter function:

```python
from app.mcp_server import set_auth_service

set_auth_service(my_auth_service)  # Inject pre-configured service
```

**Implementation:**
- `app/mcp_server.py` - `set_auth_service()` function sets module-level variable
- `app/main_mcp.py` - Calls `set_auth_service()` with configured instance

## Usage Patterns

### Pattern 1: Dependency Injection (Preferred)

Create an `AuthService` instance and inject it into the server:

```python
from app.auth.service import AuthService
from app.web_server import GraphWebServer

# Create AuthService with explicit configuration
auth_service = AuthService(
    secret_key="my-secret-key",
    token_store_path="/path/to/tokens.json"
)

# Inject into web server
server = GraphWebServer(
    require_auth=True,
    auth_service=auth_service  # Dependency injection
)
```

**Benefits:**
- Explicit service creation
- Easy to mock for testing
- Clear dependency flow
- Easier to unit test

### Pattern 2: Legacy Parameters (Backward Compatible)

Pass JWT secret and token store path directly:

```python
from app.web_server import GraphWebServer

# Legacy initialization (still supported)
server = GraphWebServer(
    jwt_secret="my-secret-key",
    token_store_path="/path/to/tokens.json",
    require_auth=True
)
```

**When to use:**
- Maintaining backward compatibility
- Simple use cases
- Quick prototyping

## Implementation Details

### `app/auth/middleware.py`

The `init_auth_service()` function supports both patterns:

```python
def init_auth_service(
    secret_key: Optional[str] = None,
    token_store_path: Optional[str] = None,
    auth_service: Optional[AuthService] = None,  # NEW: DI support
) -> AuthService:
    """
    Initialize the global auth service

    Supports two initialization patterns:
    1. Dependency Injection: Pass an existing AuthService instance
    2. Legacy: Create new AuthService from secret_key and token_store_path
    """
    global _auth_service
    
    if auth_service is not None:
        # Dependency injection: use provided instance
        _auth_service = auth_service
    else:
        # Legacy: create new instance from parameters
        _auth_service = AuthService(secret_key=secret_key, token_store_path=token_store_path)
    
    return _auth_service
```

### `app/web_server.py`

The `GraphWebServer` constructor accepts injected service:

```python
class GraphWebServer:
    def __init__(
        self,
        jwt_secret: Optional[str] = None,         # Legacy
        token_store_path: Optional[str] = None,   # Legacy
        require_auth: bool = True,
        auth_service: Optional[AuthService] = None,  # NEW: DI support
    ):
        # Initialize auth service - prefer injected instance, fallback to legacy init
        if require_auth:
            if auth_service is not None:
                # Use injected AuthService instance (dependency injection)
                init_auth_service(auth_service=auth_service)
            else:
                # Legacy path: create AuthService from jwt_secret and token_store_path
                init_auth_service(secret_key=jwt_secret, token_store_path=token_store_path)
```

### `app/mcp_server.py`

The MCP server provides a clean setter function:

```python
# Module-level variable
auth_service: AuthService | None = None

def set_auth_service(service: AuthService | None) -> None:
    """
    Set the module-level auth service instance (dependency injection)
    
    Args:
        service: AuthService instance or None to disable authentication
    """
    global auth_service
    auth_service = service
```

## Testing

### Testing with Mock Services

Dependency injection makes testing easier:

```python
from unittest.mock import MagicMock
from app.auth.service import AuthService
from app.web_server import GraphWebServer

# Create mock AuthService
mock_service = MagicMock(spec=AuthService)
mock_service.verify_token.return_value = TokenInfo(group="test", expiry=123456)

# Inject mock into server
server = GraphWebServer(
    require_auth=True,
    auth_service=mock_service  # No need to configure real token store
)

# Test server behavior without real authentication
```

### Test Coverage

See `test/auth/test_dependency_injection.py` for comprehensive DI tests:
- `TestAuthServiceDependencyInjection` - Tests for `init_auth_service()` DI patterns
- `TestGraphWebServerDependencyInjection` - Tests for `GraphWebServer` DI patterns
- `TestMCPServerDependencyInjection` - Tests for `set_auth_service()` function
- `TestDependencyInjectionLogging` - Tests for logging DI usage
- `TestDependencyInjectionDocumentation` - Tests for proper documentation

## Migration Guide

### Updating Existing Code

**Before (Legacy Pattern):**
```python
server = GraphWebServer(
    jwt_secret=os.environ.get("JWT_SECRET"),
    token_store_path="/tmp/tokens.json",
    require_auth=True
)
```

**After (Dependency Injection):**
```python
from app.auth.service import AuthService

# Create service explicitly
auth_service = AuthService(
    secret_key=os.environ.get("JWT_SECRET"),
    token_store_path="/tmp/tokens.json"
)

# Inject service
server = GraphWebServer(
    require_auth=True,
    auth_service=auth_service
)
```

### No Breaking Changes

The legacy pattern is **fully supported** - no changes required to existing code. Dependency injection is an **optional enhancement** for better testability and modularity.

## Benefits

1. **Testability:** Easy to inject mock services for testing
2. **Explicit Dependencies:** Clear service initialization flow
3. **Modularity:** Services can be configured independently
4. **Flexibility:** Different services for different contexts
5. **Backward Compatible:** Legacy patterns still work

## See Also

- `test/auth/test_dependency_injection.py` - Comprehensive DI test suite
- `docs/PHASED_PLAN_STATUS.md` - Phase 2 implementation details
- `docs/AUTHENTICATION.md` - General authentication documentation
