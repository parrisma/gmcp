"""Test CORS configuration for web server"""

import pytest
from fastapi.testclient import TestClient
from app.web_server.web_server import GraphWebServer
from app.auth import AuthService
import os


@pytest.fixture
def auth_service():
    """Create auth service for testing"""
    return AuthService(
        secret_key="test-secret-cors",
        token_store_path=":memory:",
    )


@pytest.fixture
def server_with_default_cors(auth_service):
    """Server with default CORS configuration"""
    # Save original env
    original_cors = os.environ.get("GPLOT_CORS_ORIGINS")

    # Use default CORS
    if "GPLOT_CORS_ORIGINS" in os.environ:
        del os.environ["GPLOT_CORS_ORIGINS"]

    server = GraphWebServer(
        require_auth=False,
        auth_service=auth_service,
    )

    yield server

    # Restore original env
    if original_cors is not None:
        os.environ["GPLOT_CORS_ORIGINS"] = original_cors


@pytest.fixture
def server_with_custom_cors(auth_service):
    """Server with custom CORS configuration"""
    # Save original env
    original_cors = os.environ.get("GPLOT_CORS_ORIGINS")

    # Set custom CORS origins
    os.environ["GPLOT_CORS_ORIGINS"] = "https://example.com,https://app.example.com"

    server = GraphWebServer(
        require_auth=False,
        auth_service=auth_service,
    )

    yield server

    # Restore original env
    if original_cors is not None:
        os.environ["GPLOT_CORS_ORIGINS"] = original_cors
    else:
        del os.environ["GPLOT_CORS_ORIGINS"]


@pytest.fixture
def server_with_wildcard_cors(auth_service):
    """Server with wildcard CORS configuration"""
    # Save original env
    original_cors = os.environ.get("GPLOT_CORS_ORIGINS")

    # Set wildcard CORS
    os.environ["GPLOT_CORS_ORIGINS"] = "*"

    server = GraphWebServer(
        require_auth=False,
        auth_service=auth_service,
    )

    yield server

    # Restore original env
    if original_cors is not None:
        os.environ["GPLOT_CORS_ORIGINS"] = original_cors
    else:
        del os.environ["GPLOT_CORS_ORIGINS"]


def test_cors_default_origins(server_with_default_cors):
    """Test default CORS origins are configured"""
    client = TestClient(server_with_default_cors.app)

    # Preflight request from allowed origin
    response = client.options(
        "/ping",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-credentials" in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_custom_origins_allowed(server_with_custom_cors):
    """Test custom CORS origins are enforced - allowed origin"""
    client = TestClient(server_with_custom_cors.app)

    # Preflight request from allowed origin
    response = client.options(
        "/ping",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://example.com"


def test_cors_custom_origins_blocked(server_with_custom_cors):
    """Test custom CORS origins are enforced - blocked origin"""
    client = TestClient(server_with_custom_cors.app)

    # Preflight request from blocked origin
    response = client.options(
        "/ping",
        headers={
            "Origin": "https://malicious.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    # FastAPI CORS middleware returns 400 for disallowed origins
    assert response.status_code == 400
    # The origin should not be in the allowed origins
    assert response.headers.get("access-control-allow-origin") != "https://malicious.com"


def test_cors_wildcard_allows_all(server_with_wildcard_cors):
    """Test wildcard CORS allows all origins"""
    client = TestClient(server_with_wildcard_cors.app)

    # Preflight request from any origin
    response = client.options(
        "/ping",
        headers={
            "Origin": "https://any-domain.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    # With allow_credentials=True, browsers don't allow "*" origin
    # FastAPI will echo back the origin instead
    assert "access-control-allow-origin" in response.headers


def test_cors_actual_request_with_origin(server_with_default_cors):
    """Test actual request includes CORS headers"""
    client = TestClient(server_with_default_cors.app)

    # Actual request with Origin header
    response = client.get(
        "/ping",
        headers={"Origin": "http://localhost:3000"},
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_includes_methods(server_with_default_cors):
    """Test preflight response includes allowed methods"""
    client = TestClient(server_with_default_cors.app)

    response = client.options(
        "/render",
        headers={
            "Origin": "http://localhost:8000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert "access-control-allow-methods" in response.headers
    # FastAPI CORS allows all methods by default when configured with ["*"]
    methods = response.headers["access-control-allow-methods"]
    assert "POST" in methods or "*" in methods


def test_cors_preflight_includes_headers(server_with_default_cors):
    """Test preflight response includes allowed headers"""
    client = TestClient(server_with_default_cors.app)

    response = client.options(
        "/render",
        headers={
            "Origin": "http://localhost:8000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )

    assert response.status_code == 200
    assert "access-control-allow-headers" in response.headers
