"""Security audit logging

Structured logging for security events with severity levels.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


class SecurityLevel(Enum):
    """Security event severity levels"""

    INFO = "INFO"  # Normal security events
    WARNING = "WARNING"  # Suspicious activity
    ERROR = "ERROR"  # Security violations
    CRITICAL = "CRITICAL"  # Critical security incidents


@dataclass
class SecurityEvent:
    """Security event record

    Structured format for security-related events.
    """

    timestamp: str
    level: SecurityLevel
    event_type: str
    client_id: str
    endpoint: Optional[str] = None
    message: str = ""
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        d = asdict(self)
        d["level"] = self.level.value
        return d

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class SecurityAuditor:
    """Security audit logger

    Logs security events to file and/or console with structured format.

    Example:
        auditor = SecurityAuditor("/var/log/gofr-plot/security.log")

        # Log authentication failure
        auditor.log_auth_failure(
            client_id="192.168.1.1",
            reason="Invalid token"
        )

        # Log rate limit hit
        auditor.log_rate_limit(
            client_id="192.168.1.100",
            endpoint="/render",
            limit=10
        )
    """

    def __init__(
        self,
        log_file: Optional[str] = None,
        console: bool = True,
        min_level: SecurityLevel = SecurityLevel.INFO,
    ):
        """Initialize security auditor

        Args:
            log_file: Path to log file (None for no file logging)
            console: Whether to log to console
            min_level: Minimum severity level to log
        """
        self.log_file = Path(log_file) if log_file else None
        self.console = console
        self.min_level = min_level

        # Create log directory if needed
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _should_log(self, level: SecurityLevel) -> bool:
        """Check if event should be logged based on level"""
        level_order = {
            SecurityLevel.INFO: 0,
            SecurityLevel.WARNING: 1,
            SecurityLevel.ERROR: 2,
            SecurityLevel.CRITICAL: 3,
        }
        return level_order[level] >= level_order[self.min_level]

    def _write_event(self, event: SecurityEvent) -> None:
        """Write event to log destinations"""
        if not self._should_log(event.level):
            return

        log_line = event.to_json()

        # Write to file
        if self.log_file:
            try:
                with open(self.log_file, "a") as f:
                    f.write(log_line + "\n")
            except Exception as e:
                print(f"Failed to write security log: {e}")

        # Write to console
        if self.console:
            prefix = f"[SECURITY:{event.level.value}]"
            print(f"{prefix} {event.message} | {log_line}")

    def log_event(
        self,
        level: SecurityLevel,
        event_type: str,
        client_id: str,
        message: str,
        endpoint: Optional[str] = None,
        **details,
    ) -> None:
        """Log security event

        Args:
            level: Severity level
            event_type: Type of event (auth_failure, rate_limit, etc.)
            client_id: Client identifier
            message: Human-readable message
            endpoint: Optional endpoint path
            **details: Additional event details
        """
        event = SecurityEvent(
            timestamp=datetime.utcnow().isoformat(),
            level=level,
            event_type=event_type,
            client_id=client_id,
            endpoint=endpoint,
            message=message,
            details=details if details else None,
        )
        self._write_event(event)

    def log_auth_failure(
        self, client_id: str, reason: str, endpoint: Optional[str] = None, **details
    ) -> None:
        """Log authentication failure

        Args:
            client_id: Client identifier (IP, user, etc.)
            reason: Reason for failure
            endpoint: Endpoint being accessed
            **details: Additional details
        """
        self.log_event(
            level=SecurityLevel.WARNING,
            event_type="auth_failure",
            client_id=client_id,
            endpoint=endpoint,
            message=f"Authentication failed: {reason}",
            reason=reason,
            **details,
        )

    def log_auth_success(
        self, client_id: str, user: Optional[str] = None, endpoint: Optional[str] = None
    ) -> None:
        """Log successful authentication

        Args:
            client_id: Client identifier
            user: Username or user ID
            endpoint: Endpoint being accessed
        """
        self.log_event(
            level=SecurityLevel.INFO,
            event_type="auth_success",
            client_id=client_id,
            endpoint=endpoint,
            message=f"Authentication successful for {user or 'unknown'}",
            user=user,
        )

    def log_rate_limit(self, client_id: str, endpoint: str, limit: int, window: int) -> None:
        """Log rate limit exceeded

        Args:
            client_id: Client identifier
            endpoint: Endpoint being accessed
            limit: Rate limit threshold
            window: Time window in seconds
        """
        self.log_event(
            level=SecurityLevel.WARNING,
            event_type="rate_limit_exceeded",
            client_id=client_id,
            endpoint=endpoint,
            message=f"Rate limit exceeded: {limit} requests per {window}s",
            limit=limit,
            window=window,
        )

    def log_sanitization_failure(
        self, client_id: str, input_type: str, reason: str, endpoint: Optional[str] = None
    ) -> None:
        """Log input sanitization failure

        Args:
            client_id: Client identifier
            input_type: Type of input (path, string, etc.)
            reason: Reason for failure
            endpoint: Endpoint being accessed
        """
        self.log_event(
            level=SecurityLevel.ERROR,
            event_type="sanitization_failure",
            client_id=client_id,
            endpoint=endpoint,
            message=f"Input sanitization failed for {input_type}: {reason}",
            input_type=input_type,
            reason=reason,
        )

    def log_suspicious_pattern(
        self, client_id: str, pattern_type: str, description: str, endpoint: Optional[str] = None
    ) -> None:
        """Log detection of suspicious pattern

        Args:
            client_id: Client identifier
            pattern_type: Type of pattern (sql_injection, xss, etc.)
            description: Pattern description
            endpoint: Endpoint being accessed
        """
        self.log_event(
            level=SecurityLevel.ERROR,
            event_type="suspicious_pattern",
            client_id=client_id,
            endpoint=endpoint,
            message=f"Suspicious {pattern_type} pattern detected: {description}",
            pattern_type=pattern_type,
            description=description,
        )

    def log_token_revoked(
        self, client_id: str, reason: str, token_id: Optional[str] = None
    ) -> None:
        """Log token revocation

        Args:
            client_id: Client identifier
            reason: Reason for revocation
            token_id: Token identifier
        """
        self.log_event(
            level=SecurityLevel.INFO,
            event_type="token_revoked",
            client_id=client_id,
            message=f"Token revoked: {reason}",
            reason=reason,
            token_id=token_id,
        )

    def log_permission_denied(
        self, client_id: str, resource: str, action: str, endpoint: Optional[str] = None
    ) -> None:
        """Log permission denied event

        Args:
            client_id: Client identifier
            resource: Resource being accessed
            action: Action being attempted
            endpoint: Endpoint being accessed
        """
        self.log_event(
            level=SecurityLevel.WARNING,
            event_type="permission_denied",
            client_id=client_id,
            endpoint=endpoint,
            message=f"Permission denied: {action} on {resource}",
            resource=resource,
            action=action,
        )

    def log_critical_event(
        self, client_id: str, event_description: str, endpoint: Optional[str] = None, **details
    ) -> None:
        """Log critical security event

        Args:
            client_id: Client identifier
            event_description: Description of critical event
            endpoint: Endpoint being accessed
            **details: Additional details
        """
        self.log_event(
            level=SecurityLevel.CRITICAL,
            event_type="critical_security_event",
            client_id=client_id,
            endpoint=endpoint,
            message=f"CRITICAL: {event_description}",
            description=event_description,
            **details,
        )


# Global auditor instance
_global_auditor: Optional[SecurityAuditor] = None


def get_security_auditor() -> SecurityAuditor:
    """Get global security auditor instance"""
    global _global_auditor
    if _global_auditor is None:
        _global_auditor = SecurityAuditor()
    return _global_auditor


def configure_security_auditor(
    log_file: Optional[str] = None,
    console: bool = True,
    min_level: SecurityLevel = SecurityLevel.INFO,
) -> SecurityAuditor:
    """Configure global security auditor

    Args:
        log_file: Path to log file
        console: Whether to log to console
        min_level: Minimum severity level

    Returns:
        Configured SecurityAuditor instance
    """
    global _global_auditor
    _global_auditor = SecurityAuditor(log_file, console, min_level)
    return _global_auditor
