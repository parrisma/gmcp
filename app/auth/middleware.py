"""Authentication middleware

Provides utilities for validating JWT tokens in web requests.
"""

import hashlib
from typing import Optional
from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.service import AuthService, TokenInfo
from app.security import SecurityAuditor

# Global auth service instance
_auth_service: Optional[AuthService] = None

# Global security auditor instance
_security_auditor: Optional[SecurityAuditor] = None

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def _generate_fingerprint(request: Request) -> str:
    """
    Generate a device fingerprint from request context

    Combines User-Agent and client IP to create a stable fingerprint.
    Used for token binding to prevent token theft.

    Args:
        request: FastAPI request object

    Returns:
        SHA256 hash of user-agent + IP
    """
    user_agent = request.headers.get("user-agent", "unknown")
    client_ip = request.client.host if request.client else "unknown"
    fingerprint_data = f"{user_agent}:{client_ip}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()


def init_auth_service(
    secret_key: Optional[str] = None,
    token_store_path: Optional[str] = None,
    auth_service: Optional[AuthService] = None,
) -> AuthService:
    """
    Initialize the global auth service

    Supports two initialization patterns:
    1. Dependency Injection: Pass an existing AuthService instance
    2. Legacy: Create new AuthService from secret_key and token_store_path

    Args:
        secret_key: JWT secret key (legacy, ignored if auth_service provided)
        token_store_path: Path to token store (legacy, ignored if auth_service provided)
        auth_service: Existing AuthService instance (preferred)

    Returns:
        AuthService instance

    Raises:
        ValueError: If auth_service is None and both secret_key and token_store_path are None
    """
    global _auth_service

    if auth_service is not None:
        # Dependency injection: use provided instance
        _auth_service = auth_service
    else:
        # Legacy: create new instance from parameters
        _auth_service = AuthService(secret_key=secret_key, token_store_path=token_store_path)

    return _auth_service


def get_auth_service() -> AuthService:
    """
    Get the global auth service instance

    Returns:
        AuthService instance

    Raises:
        RuntimeError: If auth service not initialized
    """
    if _auth_service is None:
        raise RuntimeError("AuthService not initialized. Call init_auth_service() first.")
    return _auth_service


def set_security_auditor(auditor: Optional[SecurityAuditor]) -> None:
    """
    Set the global security auditor instance

    Args:
        auditor: SecurityAuditor instance or None to disable auditing
    """
    global _security_auditor
    _security_auditor = auditor


def get_security_auditor() -> Optional[SecurityAuditor]:
    """
    Get the global security auditor instance

    Returns:
        SecurityAuditor instance or None if not configured
    """
    return _security_auditor


def verify_token(
    request: Request, credentials: HTTPAuthorizationCredentials = Security(security)
) -> TokenInfo:
    """
    Verify JWT token from request with enhanced security checks

    Generates device fingerprint and validates token binding if configured.

    Args:
        request: FastAPI request object (for fingerprinting)
        credentials: HTTP authorization credentials

    Returns:
        TokenInfo with group and expiry information

    Raises:
        HTTPException: If token is invalid or missing
    """
    try:
        auth_service = get_auth_service()
        # Generate fingerprint for token binding validation
        fingerprint = _generate_fingerprint(request)
        token_info = auth_service.verify_token(credentials.credentials, fingerprint=fingerprint)
        return token_info
    except ValueError as e:
        # Log authentication failure
        auditor = get_security_auditor()
        if auditor:
            auditor.log_auth_failure(client_id="token_user", reason=str(e), endpoint="verify_token")
        raise HTTPException(status_code=401, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


def optional_verify_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(optional_security),
) -> Optional[TokenInfo]:
    """
    Optionally verify JWT token from request with enhanced security checks

    Generates device fingerprint and validates token binding if configured.

    Args:
        request: FastAPI request object (for fingerprinting)
        credentials: HTTP authorization credentials (optional)

    Returns:
        TokenInfo if token provided and valid, None if no token provided

    Raises:
        HTTPException: If token is provided but invalid
    """
    if credentials is None:
        # No token provided, return None (anonymous access)
        return None

    try:
        auth_service = get_auth_service()
        # Generate fingerprint for token binding validation
        fingerprint = _generate_fingerprint(request)
        token_info = auth_service.verify_token(credentials.credentials, fingerprint=fingerprint)
        return token_info
    except ValueError as e:
        # Log authentication failure
        auditor = get_security_auditor()
        if auditor:
            auditor.log_auth_failure(
                client_id="optional_token_user", reason=str(e), endpoint="optional_verify_token"
            )
        raise HTTPException(status_code=401, detail=str(e))
    except RuntimeError:
        # Auth service not initialized - allow anonymous access
        return None
