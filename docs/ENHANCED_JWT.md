# Enhanced JWT Validation

Enhanced JWT validation adds additional security features to token authentication, including device fingerprinting, additional JWT claims validation, and backward compatibility with older tokens.

## Features

### 1. Token Fingerprinting

Binds tokens to specific devices/clients to prevent token theft and replay attacks.

**How it works:**
- Generates a fingerprint from request context (User-Agent + Client IP)
- Stores fingerprint in JWT `fp` claim during token creation
- Validates fingerprint matches on every token verification

**Usage:**

```python
from app.auth import AuthService

auth = AuthService(secret_key="your-secret")

# Create token with fingerprint
fingerprint = "device-fingerprint-hash"  # Hash of user-agent + IP
token = auth.create_token(
    group="user-group",
    expires_in_seconds=3600,
    fingerprint=fingerprint
)

# Verify token with fingerprint
token_info = auth.verify_token(token, fingerprint=fingerprint)  # ✅ Success

# Attempting to use token from different device fails
different_fp = "different-device-hash"
token_info = auth.verify_token(token, fingerprint=different_fp)  # ❌ Raises ValueError
```

**Automatic Fingerprinting in Middleware:**

The authentication middleware automatically generates and validates fingerprints:

```python
from fastapi import Depends, Request
from app.auth import verify_token

@app.get("/protected")
async def protected_route(
    request: Request,  # Required for fingerprinting
    token_info: TokenInfo = Depends(verify_token)
):
    # Token automatically validated with device fingerprint
    return {"group": token_info.group}
```

### 2. Additional JWT Claims

Enhanced tokens include security-focused JWT standard claims:

| Claim | Description | Required | Validated |
|-------|-------------|----------|-----------|
| `iat` | Issued At - timestamp when token created | Yes | Yes |
| `exp` | Expires - timestamp when token expires | Yes | Yes |
| `nbf` | Not Before - token not valid until this time | Yes | Yes |
| `aud` | Audience - intended recipient (`gplot-api`) | Yes | Yes (if present) |
| `jti` | JWT ID - unique token identifier | Optional | No |
| `fp` | Fingerprint - device binding hash | Optional | Yes (if present) |
| `group` | Group - user's group for access control | Yes | Yes |

**Example Token Payload:**

```json
{
  "group": "analytics-team",
  "iat": 1700000000,
  "exp": 1700003600,
  "nbf": 1700000000,
  "aud": "gplot-api",
  "jti": "unique-token-id-123",
  "fp": "a7f3d8e9c2b1..."
}
```

### 3. Not-Before Validation

Tokens can be created that are not yet valid, useful for:
- Scheduled access grants
- Token rotation with overlap periods
- Pre-provisioned tokens

```python
from datetime import datetime, timedelta

# Create token valid starting 1 hour from now
future_time = datetime.utcnow() + timedelta(hours=1)
# Note: Currently nbf is set to token creation time
# Future enhancement could add custom nbf parameter
```

### 4. Audience Validation

Ensures tokens are intended for gplot API and not reused from other systems:

```python
# Token with correct audience
payload = {
    "group": "users",
    "aud": "gplot-api",  # ✅ Correct
    ...
}

# Token with wrong audience fails validation
payload = {
    "group": "users", 
    "aud": "other-service",  # ❌ Rejected
    ...
}
```

### 5. Backward Compatibility

Enhanced validation is backward compatible with older tokens:

- **No `aud` claim**: Token accepted (audience validation skipped)
- **No `nbf` claim**: Token accepted (not-before validation skipped)
- **No `fp` claim**: Token accepted (fingerprint validation skipped)
- **No `jti` claim**: Token accepted (ID tracking optional)

**Migration Path:**

```python
# Old tokens (still work)
old_token_payload = {
    "group": "users",
    "iat": 1700000000,
    "exp": 1700003600
}

# New tokens (enhanced security)
new_token_payload = {
    "group": "users",
    "iat": 1700000000,
    "exp": 1700003600,
    "nbf": 1700000000,
    "aud": "gplot-api",
    "jti": "token-123",
    "fp": "device-hash"
}

# Both validate successfully
```

## Security Benefits

### Token Theft Prevention

Fingerprinting makes stolen tokens unusable:

1. Attacker steals token from user's browser
2. Attacker tries to use token from different device/IP
3. Fingerprint validation fails → Token rejected

### Replay Attack Mitigation

- `jti` enables tracking individual token usage
- `nbf` prevents premature token use
- `aud` prevents cross-service token reuse

### Token Lifecycle Management

- Store token metadata with fingerprint and jti
- Track token usage patterns
- Detect anomalies (same token from multiple IPs)
- Revoke specific tokens by jti

## Implementation Details

### Fingerprint Generation

```python
def _generate_fingerprint(request: Request) -> str:
    """Generate device fingerprint from request context"""
    user_agent = request.headers.get("user-agent", "unknown")
    client_ip = request.client.host if request.client else "unknown"
    fingerprint_data = f"{user_agent}:{client_ip}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()
```

**Properties:**
- Deterministic (same device → same fingerprint)
- SHA-256 hash (64 hex characters)
- Includes User-Agent and IP
- Handles missing data gracefully

### Token Creation

```python
def create_token(
    self,
    group: str,
    expires_in_seconds: int = 2592000,
    fingerprint: Optional[str] = None,
    token_id: Optional[str] = None,
) -> str:
    """Create enhanced JWT token with security claims"""
```

### Token Verification

```python
def verify_token(
    self, 
    token: str, 
    fingerprint: Optional[str] = None
) -> TokenInfo:
    """Verify JWT with enhanced security checks"""
```

### Validation Options

```python
payload = jwt.decode(
    token,
    secret_key,
    algorithms=["HS256"],
    options={
        "verify_exp": True,   # Verify expiration
        "verify_nbf": True,   # Verify not-before (if present)
        "verify_iat": True,   # Verify issued-at
        "verify_aud": False,  # Don't require audience (backward compat)
    },
)
```

## Testing

Enhanced JWT features are tested in `test/auth/test_enhanced_jwt.py`:

```bash
# Run enhanced JWT tests
pytest test/auth/test_enhanced_jwt.py -v

# Test fingerprinting
pytest test/auth/test_enhanced_jwt.py::test_verify_token_with_matching_fingerprint -v

# Test backward compatibility
pytest test/auth/test_enhanced_jwt.py::test_backward_compatibility_with_old_tokens -v
```

**Test Coverage:**
- Token creation with enhanced claims
- Fingerprint matching/mismatching
- Audience validation
- Not-before validation
- Group consistency validation
- Backward compatibility with old tokens
- Fingerprint generation from requests
- Token metadata storage

## Production Recommendations

### 1. Always Use Fingerprinting

```python
# Create tokens with fingerprints
token = auth.create_token(
    group="users",
    expires_in_seconds=3600,
    fingerprint=generate_fingerprint(request),
    token_id=str(uuid.uuid4())  # Unique ID for tracking
)
```

### 2. Monitor Token Usage

```python
# Log token verification for anomaly detection
logger.info(
    "Token verified",
    group=token_info.group,
    fingerprint=fingerprint[:12],
    jti=payload.get("jti"),
    ip=request.client.host
)
```

### 3. Implement Token Rotation

```python
# Create new token before old one expires
new_token = auth.create_token(
    group=old_token_info.group,
    expires_in_seconds=3600,
    fingerprint=current_fingerprint,
    token_id=str(uuid.uuid4())
)

# Grace period: accept both tokens for 5 minutes
# Then revoke old token
```

### 4. Handle Fingerprint Changes

```python
# User's IP may change (mobile, VPN)
# Consider fingerprint validation failures:
try:
    token_info = auth.verify_token(token, fingerprint)
except ValueError as e:
    if "fingerprint mismatch" in str(e):
        # Log as security event
        audit.log_security_event(
            event="fingerprint_mismatch",
            token=token[:12],
            expected_fp=stored_fp[:12],
            actual_fp=fingerprint[:12]
        )
        # Require re-authentication
        raise HTTPException(401, "Device changed, please log in again")
```

## Limitations

### Fingerprint Stability

User-Agent and IP can change legitimately:
- Mobile devices switching networks (WiFi ↔ Cellular)
- VPN connections
- Browser updates changing User-Agent
- Shared IPs (NAT, corporate proxies)

**Mitigation:**
- Make fingerprint validation a warning, not hard fail
- Allow token refresh on fingerprint mismatch
- Use additional factors (device ID, session tokens)

### Token Store Growth

Every token is stored with metadata:
- Implement token cleanup/purging
- Monitor token store size
- Set reasonable expiration times

### Backward Compatibility Tradeoff

Old tokens lack enhanced security:
- Phase out old tokens gradually
- Force re-authentication for high-value operations
- Document migration timeline

## Future Enhancements

- Token rotation with grace periods
- Customizable `nbf` timestamps
- IP range fingerprinting (allow IP changes within range)
- Device ID claims (more stable than IP)
- Token families (track refresh token chains)
- Automatic token renewal on expiration
