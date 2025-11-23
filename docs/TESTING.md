# Testing Guide

This document describes the testing infrastructure, workflow, and conventions for the gplot project.

## Overview

gplot maintains a comprehensive test suite covering:
- Authentication and authorization
- MCP server functionality
- Web API endpoints
- Storage operations and concurrency
- Graph rendering and validation
- Multi-dataset support

**Current Status**: 210 tests passing in ~9.7 seconds

## Test Runner

### Quick Start

```bash
# Run tests without starting servers (unit/validation tests only)
./scripts/run_tests.sh --no-servers

# Run full integration tests with servers
./scripts/run_tests.sh --with-servers

# Run specific test file
./scripts/run_tests.sh --no-servers test/auth/test_authentication.py
```

### How It Works

The `run_tests.sh` script:

1. **Sets up environment variables** for consistent configuration
2. **Manages server lifecycle** (when using `--with-servers`)
3. **Cleans up resources** before and after test runs
4. **Provides colored output** for easy status tracking

### Environment Variables

The test runner automatically configures:

| Variable | Default | Purpose |
|----------|---------|---------|
| `GPLOT_JWT_SECRET` | `test-secret-key-for...` | JWT token signing secret |
| `GPLOT_TOKEN_STORE` | `/tmp/gplot_test_tokens.json` | Shared token store path |
| `GPLOT_MCP_PORT` | `8001` | MCP server port |
| `GPLOT_WEB_PORT` | `8000` | Web server port |

## Test Organization

```
test/
├── conftest.py              # Shared pytest fixtures
├── auth/                    # Authentication & authorization tests
│   ├── test_authentication.py
│   ├── test_auth_config.py
│   ├── test_dependency_injection.py
│   └── test_token_store_reload.py
├── mcp/                     # MCP server tests
│   ├── test_mcp_rendering.py
│   ├── test_mcp_handlers.py
│   ├── test_mcp_themes.py
│   └── manual_*.py         # Manual test scripts (excluded from pytest)
├── storage/                 # Storage layer tests
│   ├── test_concurrent_access.py
│   ├── test_metadata_corruption.py
│   ├── test_storage_failures.py
│   └── test_storage_purge.py
├── validation/              # Validation and rendering tests
│   ├── test_multi_dataset.py
│   ├── test_axis_controls.py
│   └── test_extreme_values.py
└── web/                     # Web API tests
    ├── test_web_rendering.py
    ├── test_web_multi_dataset.py
    └── manual_*.py         # Manual test scripts (excluded)
```

## Test Fixtures

### Session-Scoped Fixtures (conftest.py)

```python
@pytest.fixture(scope="session")
def test_auth_service():
    """Shared authentication service for all tests"""
    
@pytest.fixture(scope="session")
def test_token():
    """Valid JWT token for testing"""
    
@pytest.fixture(scope="session")
def invalid_token():
    """Invalid token for auth failure tests"""
```

### Function-Scoped Fixtures

```python
@pytest.fixture
def temp_storage_dir(tmp_path):
    """Isolated storage directory per test"""
    
@pytest.fixture
def logger():
    """Test logger instance"""
```

## Running Specific Tests

### By File

```bash
./scripts/run_tests.sh --no-servers test/auth/test_authentication.py
```

### By Class

```bash
pytest test/auth/test_authentication.py::TestMCPAuthentication
```

### By Test Name

```bash
pytest test/auth/test_authentication.py::TestMCPAuthentication::test_mcp_render_with_valid_token
```

### By Marker

```bash
pytest -m asyncio  # Run all async tests
```

## Test Modes

### Unit/Validation Tests (`--no-servers`)

- Fastest execution (~6 seconds)
- No external server dependencies
- Covers validation logic, storage, and auth service
- Ideal for TDD and quick feedback

### Integration Tests (`--with-servers`)

- Complete end-to-end testing (~10 seconds)
- Starts MCP and Web servers automatically
- Tests full request/response cycles
- Validates authentication, rendering, storage

## pytest Configuration

Settings in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["."]
addopts = "--strict-markers --ignore=test/mcp/manual_test_mcp_server.py --ignore=test/mcp/manual_mcp_discovery.py --ignore=test/web/manual_test_web_server.py"
filterwarnings = [
    "ignore::RuntimeWarning:matplotlib",
]
```

**Key settings:**
- `--strict-markers`: Enforces declared markers, catches typos
- `--ignore`: Excludes manual test scripts from discovery
- `asyncio_mode = "auto"`: Automatic async test detection

## Zero-Skip Policy

Tests should not use `pytest.skip()` for missing dependencies or server availability. Instead:

1. **Use test modes**: Run unit tests with `--no-servers`, integration tests with `--with-servers`
2. **Use fixtures**: Make dependencies explicit via pytest fixtures
3. **Use markers**: Tag tests appropriately (`@pytest.mark.asyncio`, etc.)

## Writing New Tests

### Authentication Required

```python
@pytest.mark.asyncio
async def test_authenticated_endpoint(test_auth_service, test_token):
    """Test that requires authentication"""
    auth_service = test_auth_service
    token = test_token
    
    # Your test logic here
```

### Storage Required

```python
def test_storage_operation(temp_storage_dir, logger):
    """Test requiring isolated storage"""
    storage = FileStorage(base_dir=temp_storage_dir, logger=logger)
    
    # Your test logic here
```

### MCP/Web Server Required

```python
@pytest.mark.asyncio
async def test_mcp_endpoint(test_token):
    """Test requiring running MCP server"""
    # Run with: ./scripts/run_tests.sh --with-servers
    
    async with httpx.AsyncClient() as client:
        response = await client.post(...)
```

## Common Test Patterns

### Testing Authentication

```python
# Valid token
response = await client.post(url, headers={"Authorization": f"Bearer {test_token}"})
assert response.status_code == 200

# Missing token
response = await client.post(url)
assert response.status_code == 401

# Invalid token
response = await client.post(url, headers={"Authorization": f"Bearer {invalid_token}"})
assert response.status_code == 401
```

### Testing Group Security

```python
# Create resource in group1
token1 = auth_service.create_token(group="group1")
guid = create_resource(token=token1)

# Try to access from group2 (should fail)
token2 = auth_service.create_token(group="group2")
response = await client.get(f"/proxy/{guid}", headers={"Authorization": f"Bearer {token2}"})
assert response.status_code == 403  # Forbidden
```

### Testing Storage Concurrency

```python
async def test_concurrent_operations():
    tasks = [
        save_data(storage, f"data_{i}")
        for i in range(10)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    assert all(not isinstance(r, Exception) for r in results)
```

## Debugging Failed Tests

### View Full Output

```bash
pytest -v -s test/path/to/test.py
```

### Run with Debugging

```python
import pdb; pdb.set_trace()  # Add breakpoint
```

Or use VS Code's debugging:
- Set breakpoint in test
- Run "Python: Debug Tests" from command palette

### Check Server Logs

When using `--with-servers`, logs are saved to:
- `/tmp/gplot_mcp_test.log`
- `/tmp/gplot_web_test.log`

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run tests
  run: |
    ./scripts/run_tests.sh --with-servers
```

### Docker

```bash
docker run gplot ./scripts/run_tests.sh --with-servers
```

## Test Metrics

Current baseline (as of Phase 5):
- **Total Tests**: 210
- **Duration**: ~9.7 seconds (with servers)
- **Coverage**: Auth, MCP, Web, Storage, Validation
- **Skipped**: 0 (zero-skip policy enforced)

## Best Practices

1. **Use fixtures**: Don't create auth services or storage in tests directly
2. **Isolate tests**: Use `temp_storage_dir` for storage tests
3. **Test one thing**: Each test should verify a single behavior
4. **Clear names**: Test names should describe what they verify
5. **Fast feedback**: Keep unit tests under 0.1s each
6. **Clean up**: Use fixtures with teardown or context managers
7. **No sleeps**: Use mocking instead of timing-based tests

## Troubleshooting

### Port Already in Use

```bash
# Kill existing servers
pkill -9 -f "python.*main_mcp.py"
pkill -9 -f "python.*main_web.py"
```

### Token Store Conflicts

The test runner automatically cleans the token store. If you see auth failures:

```bash
rm /tmp/gplot_test_tokens.json
```

### Stale Server Processes

The test runner includes detection for stale log files. If tests hang:

```bash
./scripts/run_tests.sh --with-servers  # Includes automatic cleanup
```

## Related Documentation

- [SECURITY.md](SECURITY.md) - Authentication and authorization details
- [AUTHENTICATION.md](AUTHENTICATION.md) - JWT token usage
- [STORAGE.md](STORAGE.md) - Storage layer design
