# Security Documentation

## Overview

This document describes the security architecture, threat model, and hardening procedures for the gplot graph rendering service.

## Table of Contents

1. [Security Architecture](#security-architecture)
2. [Threat Model](#threat-model)
3. [Security Features](#security-features)
4. [Hardening Checklist](#hardening-checklist)
5. [Incident Response](#incident-response)
6. [Security Best Practices](#security-best-practices)

---

## Security Architecture

### Components

```
┌─────────────────────────────────────────────────┐
│              Client Requests                     │
└────────────────────┬────────────────────────────┘
                     │
         ┌───────────▼──────────────┐
         │   Rate Limiter           │  ← Token bucket algorithm
         │   (per-client/endpoint)  │     Per-client isolation
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────┐
         │   Authentication         │  ← JWT validation
         │   Middleware             │     Group-based access
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────┐
         │   Input Sanitizer        │  ← Injection prevention
         │                          │     XSS/SSRF blocking
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────┐
         │   Request Validator      │  ← Schema validation
         │                          │     Type checking
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────┐
         │   Business Logic         │  ← Chart rendering
         │                          │     Storage operations
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────┐
         │   Security Auditor       │  ← Event logging
         │                          │     Incident tracking
         └──────────────────────────┘
```

### Defense in Depth

1. **Rate Limiting**: Prevent brute force and DoS attacks
2. **Authentication**: JWT-based access control with group isolation
3. **Input Sanitization**: Block injection attacks (SQL, XSS, path traversal, SSRF)
4. **Validation**: Schema-based validation of all inputs
5. **Audit Logging**: Comprehensive security event tracking

---

## Threat Model

### Attack Surface

#### External Attackers
- **Web API**: Public HTTP endpoints
- **MCP Protocol**: JSON-RPC over HTTP/SSE
- **MCPO Proxy**: Additional wrapper layer

#### Potential Threats

| Threat Category | Attack Vector | Mitigation |
|----------------|---------------|------------|
| **Authentication Bypass** | Stolen/forged JWT tokens | JWT validation, expiry, revocation |
| **Brute Force** | Repeated login attempts | Rate limiting, account lockout |
| **DoS** | Request flooding | Rate limiting, resource limits |
| **Injection Attacks** | SQL, command, XSS payloads | Input sanitization, parameterization |
| **Path Traversal** | Directory traversal in file paths | Path sanitization, base directory enforcement |
| **SSRF** | Internal network requests via URLs | URL validation, private IP blocking |
| **Data Leakage** | Unauthorized access to images | Group-based access control |
| **Resource Exhaustion** | Large data inputs | Input size limits, timeouts |

### Trust Boundaries

1. **Public Internet → Web Server**: Untrusted
2. **Web Server → Application**: Partially trusted (after auth)
3. **Application → Storage**: Trusted
4. **Application → Logging**: Trusted

---

## Security Features

### 1. Rate Limiting

**Implementation**: `app/security/rate_limiter.py`

**Features**:
- Token bucket algorithm for smooth rate limiting
- Per-client isolation (by IP, user ID, or token)
- Per-endpoint custom limits
- Configurable time windows
- Automatic cleanup of stale buckets
- Thread-safe concurrent access

**Usage**:
```python
from app.security import RateLimiter, RateLimitExceeded

limiter = RateLimiter(default_limit=100, window=60)
limiter.set_endpoint_limit("/render", limit=10, window=60)

try:
    limiter.check_limit(client_id=client_ip, endpoint="/render")
    # Process request
except RateLimitExceeded as e:
    # Return 429 with Retry-After header
    return {"error": str(e)}, 429, {"Retry-After": str(int(e.retry_after))}
```

**Configuration**:
- Default: 100 requests/60 seconds
- `/render`: 10 requests/60 seconds (expensive operation)
- `/ping`: 1000 requests/60 seconds (health check)

### 2. Input Sanitization

**Implementation**: `app/security/sanitizer.py`

**Features**:
- Chart parameter validation (type, format, theme, scale)
- Path traversal prevention
- SQL injection detection
- XSS pattern blocking
- SSRF prevention (URL validation)
- Numeric range enforcement
- String length limits

**Usage**:
```python
from app.security import Sanitizer, SanitizationError

sanitizer = Sanitizer(strict=True)

try:
    chart_type = sanitizer.sanitize_chart_type(user_input)
    format = sanitizer.sanitize_format(user_format)
    title = sanitizer.sanitize_for_svg(user_title)
    # Process sanitized inputs
except SanitizationError as e:
    # Return 400 error
    return {"error": str(e)}, 400
```

**Blocked Patterns**:
- Path traversal: `../`, `~`, `/etc`, `/proc`, `/sys`
- SQL injection: `SELECT`, `DROP`, `--`, `OR 1=1`, `UNION SELECT`
- XSS: `<script>`, `javascript:`, `onerror=`, `onload=`
- SSRF: `localhost`, `127.0.0.1`, `192.168.*`, `10.*`

### 3. Security Audit Logging

**Implementation**: `app/security/audit.py`

**Features**:
- Structured JSON event logging
- Severity levels: INFO, WARNING, ERROR, CRITICAL
- Event types: auth_failure, rate_limit_exceeded, sanitization_failure, etc.
- File and console output
- Minimum level filtering

**Usage**:
```python
from app.security import SecurityAuditor, SecurityLevel

auditor = SecurityAuditor(log_file="/var/log/gplot/security.log")

# Log authentication failure
auditor.log_auth_failure(
    client_id="192.168.1.100",
    reason="Invalid token",
    endpoint="/api/render"
)

# Log rate limit hit
auditor.log_rate_limit(
    client_id="192.168.1.100",
    endpoint="/render",
    limit=10,
    window=60
)
```

**Event Format**:
```json
{
  "timestamp": "2025-11-23T10:00:00.000Z",
  "level": "WARNING",
  "event_type": "auth_failure",
  "client_id": "192.168.1.100",
  "endpoint": "/api/render",
  "message": "Authentication failed: Invalid token",
  "details": {
    "reason": "Invalid token"
  }
}
```

### 4. JWT Authentication

**Implementation**: `app/auth/service.py`

**Security Features**:
- HS256 signing with secret key
- Token expiry (configurable)
- Token revocation via blacklist
- Group-based access control
- Fingerprint verification across services

**Best Practices**:
- Use strong secret (256-bit minimum)
- Short expiry times (1-24 hours)
- Rotate secrets regularly
- Revoke tokens on logout/compromise
- Never log tokens in plaintext

---

## Hardening Checklist

### Production Deployment

#### Environment Configuration

- [ ] **Strong JWT Secret**: 256-bit random secret, not default
- [ ] **Secret Rotation**: Regular rotation schedule (30-90 days)
- [ ] **Environment Variables**: All secrets in env vars, not code
- [ ] **HTTPS Only**: Disable HTTP in production
- [ ] **CORS Configuration**: Whitelist specific origins only

#### Rate Limiting

- [ ] **Enable Rate Limiting**: Set appropriate limits per endpoint
- [ ] **Monitor Rate Limits**: Alert on frequent limit hits
- [ ] **DDoS Protection**: Consider external DDoS protection service
- [ ] **IP Blacklisting**: Block known malicious IPs

#### Authentication

- [ ] **Require Authentication**: Enable auth for all sensitive endpoints
- [ ] **Token Expiry**: Use short-lived tokens (1-2 hours)
- [ ] **Revocation Check**: Implement token revocation checking
- [ ] **Group Isolation**: Enforce group-based access control
- [ ] **Failed Login Tracking**: Monitor and alert on failed auth attempts

#### Input Validation

- [ ] **Enable Sanitization**: Apply to all user inputs
- [ ] **Strict Mode**: Use strict=True in production
- [ ] **Size Limits**: Enforce reasonable size limits on all inputs
- [ ] **File Upload Restrictions**: Validate file types and sizes
- [ ] **Error Messages**: Don't leak internal details in error messages

#### Logging and Monitoring

- [ ] **Security Audit Log**: Enable and monitor
- [ ] **Log Rotation**: Configure log rotation to prevent disk fill
- [ ] **Alert on Critical Events**: Set up alerts for CRITICAL level events
- [ ] **Regular Review**: Review security logs weekly
- [ ] **SIEM Integration**: Consider integrating with SIEM system

#### Network Security

- [ ] **Firewall Rules**: Restrict access to necessary ports only
- [ ] **Private Networks**: Use private networks for internal communication
- [ ] **TLS Certificates**: Use valid certificates (Let's Encrypt, etc.)
- [ ] **Disable Debug Mode**: Never run debug mode in production

#### Storage Security

- [ ] **File Permissions**: Restrict storage directory permissions (700)
- [ ] **Encryption at Rest**: Consider encrypting sensitive data
- [ ] **Backup Encryption**: Encrypt backups
- [ ] **Regular Purge**: Implement automated purge of old data

#### Docker Security

- [ ] **Non-Root User**: Run containers as non-root user
- [ ] **Read-Only Filesystem**: Use read-only root filesystem where possible
- [ ] **Minimal Base Image**: Use minimal base images (alpine, distroless)
- [ ] **Scan Images**: Regularly scan images for vulnerabilities
- [ ] **Resource Limits**: Set memory and CPU limits

---

## Incident Response

### Security Incident Types

1. **Authentication Breach**: Compromised credentials/tokens
2. **DoS Attack**: Service unavailability due to flooding
3. **Injection Attack**: Attempted SQL/command/XSS injection
4. **Data Breach**: Unauthorized access to user data
5. **System Compromise**: Server/container compromise

### Response Procedures

#### 1. Detection and Alerting

- Monitor security audit logs for CRITICAL events
- Set up alerts for:
  - Multiple failed authentication attempts (>10 in 5 minutes)
  - Rate limit exceeded frequently (>100 in 10 minutes)
  - Sanitization failures (any occurrence)
  - Unusual access patterns

#### 2. Initial Response (0-15 minutes)

1. **Verify Alert**: Confirm it's a real incident, not false positive
2. **Assess Severity**: Use severity matrix to determine urgency
3. **Notify Team**: Alert security team and relevant stakeholders
4. **Document**: Start incident log with timeline

#### 3. Containment (15-60 minutes)

**For Authentication Breach**:
- Revoke compromised tokens immediately
- Force password reset for affected users
- Review access logs for unauthorized access
- Enable additional authentication factors if available

**For DoS Attack**:
- Identify attack source (IPs, patterns)
- Implement IP-based rate limiting/blocking
- Enable DDoS protection service if available
- Scale resources if needed

**For Injection Attempt**:
- Block offending IP/client immediately
- Review logs for similar attempts
- Verify sanitization is working correctly
- Check for any successful exploits

**For Data Breach**:
- Immediately revoke all access tokens
- Identify scope of exposed data
- Secure vulnerable systems
- Preserve evidence for investigation

#### 4. Eradication (1-4 hours)

- Patch vulnerabilities that were exploited
- Update security configurations
- Deploy security fixes
- Remove any backdoors/malware

#### 5. Recovery (4-24 hours)

- Restore services from clean state
- Regenerate all secrets (JWT, API keys)
- Re-enable services with enhanced monitoring
- Verify system integrity

#### 6. Post-Incident (24-72 hours)

- Conduct root cause analysis
- Update security documentation
- Improve detection/prevention mechanisms
- Train team on lessons learned
- Update incident response procedures

---

## Security Best Practices

### For Developers

1. **Never Commit Secrets**: Use environment variables, never hardcode secrets
2. **Validate All Inputs**: Use Sanitizer for all user-provided data
3. **Use Parameterized Queries**: Prevent SQL injection
4. **Escape Output**: Sanitize data before including in HTML/SVG/PDF
5. **Least Privilege**: Grant minimum necessary permissions
6. **Secure Dependencies**: Regularly update dependencies, scan for vulnerabilities
7. **Code Review**: All security-related code requires peer review
8. **Security Testing**: Write security tests for new features

### For Operations

1. **Regular Updates**: Apply security patches promptly
2. **Monitoring**: Continuously monitor security logs
3. **Backups**: Regular encrypted backups, test restoration
4. **Access Control**: Limit who can access production systems
5. **Audit Logs**: Preserve logs for compliance/forensics (90+ days)
6. **Incident Drills**: Practice incident response procedures
7. **Vulnerability Scanning**: Regular automated security scans
8. **Penetration Testing**: Annual third-party penetration tests

### For Users

1. **Strong Tokens**: Use long, random JWT secrets
2. **Token Management**: Rotate tokens regularly, revoke on compromise
3. **HTTPS Only**: Always use HTTPS in production
4. **Monitor Usage**: Review access logs for suspicious activity
5. **Report Issues**: Report security issues to security@example.com
6. **Stay Updated**: Subscribe to security advisories

---

## Security Contacts

- **Security Issues**: security@example.com
- **Emergency**: security-emergency@example.com (24/7)
- **Bug Bounty**: bugbounty@example.com

---

## Compliance

### Standards

- **OWASP Top 10**: Addressed in design and implementation
- **GDPR**: Data minimization, right to deletion (purge functionality)
- **SOC 2**: Audit logging, access control, incident response

### Audit Trail

Security audit logs provide evidence for:
- Authentication events
- Authorization decisions
- Data access (who accessed what, when)
- Configuration changes
- Security incidents

---

## Additional Resources

- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [Security Headers Best Practices](https://securityheaders.com/)

---

**Document Version**: 1.0  
**Last Updated**: November 23, 2025  
**Review Schedule**: Quarterly
