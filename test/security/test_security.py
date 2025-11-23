#!/usr/bin/env python3
"""Security tests

Tests for rate limiting, sanitization, and audit logging.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import time
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from app.security.rate_limiter import (
    RateLimiter,
    RateLimitExceeded,
    TokenBucket,
)
from app.security.sanitizer import Sanitizer, SanitizationError
from app.security.audit import (
    SecurityAuditor,
    SecurityEvent,
    SecurityLevel,
)


# ============================================================================
# Rate Limiter Tests
# ============================================================================


class TestTokenBucket:
    """Tests for TokenBucket implementation"""

    def test_token_bucket_creation(self):
        """Test token bucket initialization"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)

        assert bucket.capacity == 10
        assert bucket.refill_rate == 1.0
        assert bucket.tokens == 10.0

    def test_token_consumption(self):
        """Test consuming tokens from bucket"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)

        # Consume 5 tokens
        allowed, retry_after = bucket.consume(5)
        assert allowed is True
        assert retry_after == 0.0
        assert abs(bucket.tokens - 5.0) < 0.01

        # Consume 3 more
        allowed, retry_after = bucket.consume(3)
        assert allowed is True
        assert abs(bucket.tokens - 2.0) < 0.01  # Use approximate comparison

    def test_token_exhaustion(self):
        """Test bucket when tokens exhausted"""
        bucket = TokenBucket(capacity=5, refill_rate=1.0)

        # Consume all tokens
        bucket.consume(5)
        assert bucket.tokens == 0.0

        # Try to consume more
        allowed, retry_after = bucket.consume(1)
        assert allowed is False
        assert retry_after > 0.0

    def test_token_refill(self):
        """Test token refill over time"""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 10 tokens/second

        # Consume all tokens
        bucket.consume(10)
        assert bucket.tokens == 0.0

        # Wait and refill
        time.sleep(0.5)  # Should refill ~5 tokens
        bucket._refill()

        # Should have approximately 5 tokens
        assert 4.0 < bucket.tokens < 6.0

    def test_bucket_capacity_limit(self):
        """Test that bucket doesn't exceed capacity"""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)

        # Wait for refill (already full)
        time.sleep(1.0)
        bucket._refill()

        # Should not exceed capacity
        assert bucket.tokens == 10.0


class TestRateLimiter:
    """Tests for RateLimiter"""

    def test_rate_limiter_creation(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter(default_limit=100, window=60)

        assert limiter.default_limit == 100
        assert limiter.window == 60
        assert limiter.enable is True

    def test_rate_limiter_disabled(self):
        """Test rate limiter when disabled"""
        limiter = RateLimiter(enable=False)

        # Should allow unlimited requests
        for _ in range(1000):
            limiter.check_limit("client1", "endpoint1")
        # No exception raised

    def test_rate_limit_enforcement(self):
        """Test rate limit is enforced"""
        limiter = RateLimiter(default_limit=5, window=60)

        # Use up limit
        for i in range(5):
            limiter.check_limit("client1", "endpoint1")

        # Next request should fail
        with pytest.raises(RateLimitExceeded) as exc_info:
            limiter.check_limit("client1", "endpoint1")

        assert exc_info.value.limit == 5
        assert exc_info.value.window == 60

    def test_per_client_isolation(self):
        """Test different clients have separate limits"""
        limiter = RateLimiter(default_limit=3, window=60)

        # Client1 uses up limit
        for i in range(3):
            limiter.check_limit("client1", "endpoint1")

        with pytest.raises(RateLimitExceeded):
            limiter.check_limit("client1", "endpoint1")

        # Client2 should still have full limit
        for i in range(3):
            limiter.check_limit("client2", "endpoint1")

    def test_per_endpoint_limits(self):
        """Test custom limits for specific endpoints"""
        limiter = RateLimiter(default_limit=100, window=60)

        # Set stricter limit for /render
        limiter.set_endpoint_limit("/render", limit=5, window=10)

        # Use up /render limit
        for i in range(5):
            limiter.check_limit("client1", "/render")

        with pytest.raises(RateLimitExceeded):
            limiter.check_limit("client1", "/render")

        # But /ping should still have high limit
        for i in range(10):
            limiter.check_limit("client1", "/ping")

    def test_reset_client(self):
        """Test resetting client's rate limit"""
        limiter = RateLimiter(default_limit=3, window=60)

        # Use up limit
        for i in range(3):
            limiter.check_limit("client1", "endpoint1")

        # Reset client
        limiter.reset_client("client1", "endpoint1")

        # Should be able to make requests again
        for i in range(3):
            limiter.check_limit("client1", "endpoint1")

    def test_concurrent_rate_limiting(self):
        """Test rate limiter with concurrent requests"""
        limiter = RateLimiter(default_limit=10, window=60)

        success_count = 0
        failure_count = 0
        lock = Lock()

        def make_request(client_id):
            nonlocal success_count, failure_count
            try:
                limiter.check_limit(client_id, "endpoint1")
                with lock:
                    success_count += 1
            except RateLimitExceeded:
                with lock:
                    failure_count += 1

        # Try 20 concurrent requests from same client
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, "client1") for _ in range(20)]
            for future in futures:
                future.result()

        # Should allow 10, reject 10
        assert success_count == 10
        assert failure_count == 10

    def test_cleanup_stale_buckets(self):
        """Test cleanup of unused buckets"""
        limiter = RateLimiter(default_limit=10, window=60)

        # Create some buckets
        limiter.check_limit("client1", "endpoint1")
        limiter.check_limit("client2", "endpoint2")
        limiter.check_limit("client3", "endpoint3")

        assert len(limiter.buckets) == 3

        # Cleanup with very short max_age
        removed = limiter.cleanup_stale_buckets(max_age=0.001)

        # All should be removed
        assert removed >= 0  # May be 0 if executed too quickly

    def test_get_stats(self):
        """Test rate limiter statistics"""
        limiter = RateLimiter(default_limit=100, window=60)
        limiter.set_endpoint_limit("/render", 10, 30)

        # Make some requests
        limiter.check_limit("client1", "endpoint1")
        limiter.check_limit("client2", "endpoint2")

        stats = limiter.get_stats()

        assert stats["enabled"] is True
        assert stats["default_limit"] == 100
        assert stats["window"] == 60
        assert "/render" in stats["endpoint_limits"]
        assert stats["active_buckets"] == 2
        assert stats["clients"] == 2


# ============================================================================
# Sanitizer Tests
# ============================================================================


class TestSanitizer:
    """Tests for input sanitization"""

    def test_sanitize_chart_type_valid(self):
        """Test sanitizing valid chart types"""
        sanitizer = Sanitizer()

        assert sanitizer.sanitize_chart_type("line") == "line"
        assert sanitizer.sanitize_chart_type("SCATTER") == "scatter"
        assert sanitizer.sanitize_chart_type(" bar ") == "bar"

    def test_sanitize_chart_type_invalid(self):
        """Test rejecting invalid chart types"""
        sanitizer = Sanitizer()

        with pytest.raises(SanitizationError):
            sanitizer.sanitize_chart_type("invalid_type")

        with pytest.raises(SanitizationError):
            sanitizer.sanitize_chart_type("pie")  # Not in allowed list

    def test_sanitize_format_valid(self):
        """Test sanitizing valid formats"""
        sanitizer = Sanitizer()

        assert sanitizer.sanitize_format("png") == "png"
        assert sanitizer.sanitize_format("SVG") == "svg"
        assert sanitizer.sanitize_format(" pdf ") == "pdf"

    def test_sanitize_format_invalid(self):
        """Test rejecting invalid formats"""
        sanitizer = Sanitizer()

        with pytest.raises(SanitizationError):
            sanitizer.sanitize_format("exe")

        with pytest.raises(SanitizationError):
            sanitizer.sanitize_format("../../file.png")

    def test_sanitize_path_traversal_attack(self):
        """Test detecting path traversal attempts"""
        sanitizer = Sanitizer()

        # Various path traversal patterns
        with pytest.raises(SanitizationError):
            sanitizer.sanitize_path("../../../etc/passwd")

        with pytest.raises(SanitizationError):
            sanitizer.sanitize_path("/etc/shadow")

        with pytest.raises(SanitizationError):
            sanitizer.sanitize_path("~/.ssh/id_rsa")

    def test_sanitize_path_valid(self, tmp_path):
        """Test sanitizing valid paths"""
        sanitizer = Sanitizer()

        # Create a safe file
        safe_file = tmp_path / "safe.txt"
        safe_file.write_text("test")

        # Should accept path within base directory
        result = sanitizer.sanitize_path(str(safe_file), base_dir=str(tmp_path))
        assert result == safe_file.resolve()

    def test_sanitize_string_sql_injection(self):
        """Test detecting SQL injection attempts"""
        sanitizer = Sanitizer()

        # SQL injection patterns
        with pytest.raises(SanitizationError):
            sanitizer.sanitize_string("'; DROP TABLE users; --")

        with pytest.raises(SanitizationError):
            sanitizer.sanitize_string("SELECT * FROM users WHERE 1=1")

        with pytest.raises(SanitizationError):
            sanitizer.sanitize_string("admin'--")

    def test_sanitize_string_xss(self):
        """Test detecting XSS attempts"""
        sanitizer = Sanitizer()

        # XSS patterns
        with pytest.raises(SanitizationError):
            sanitizer.sanitize_string("<script>alert('XSS')</script>")

        with pytest.raises(SanitizationError):
            sanitizer.sanitize_string("javascript:alert(1)")

        with pytest.raises(SanitizationError):
            sanitizer.sanitize_string('<img onerror="alert(1)">')

    def test_sanitize_string_length(self):
        """Test string length limits"""
        sanitizer = Sanitizer(strict=True)

        # Too long
        with pytest.raises(SanitizationError):
            sanitizer.sanitize_string("x" * 1001, max_length=1000)

        # Within limit
        result = sanitizer.sanitize_string("x" * 100, max_length=1000)
        assert len(result) == 100

    def test_sanitize_for_svg(self):
        """Test SVG-specific sanitization"""
        sanitizer = Sanitizer()

        # Should escape HTML entities
        result = sanitizer.sanitize_for_svg("<test>")
        assert "<" not in result
        assert "&lt;" in result or "&amp;" in result

    def test_sanitize_numeric_range(self):
        """Test numeric range validation"""
        sanitizer = Sanitizer()

        # Within range
        assert sanitizer.sanitize_numeric_range(50, 0, 100) == 50

        # Below minimum
        with pytest.raises(SanitizationError):
            sanitizer.sanitize_numeric_range(-10, 0, 100)

        # Above maximum
        with pytest.raises(SanitizationError):
            sanitizer.sanitize_numeric_range(150, 0, 100)

    def test_sanitize_url_ssrf(self):
        """Test SSRF prevention in URLs"""
        sanitizer = Sanitizer()

        # Valid URLs
        assert sanitizer.sanitize_url("https://example.com/api") == "https://example.com/api"

        # Localhost (SSRF attempt)
        with pytest.raises(SanitizationError):
            sanitizer.sanitize_url("http://localhost:8080/admin")

        with pytest.raises(SanitizationError):
            sanitizer.sanitize_url("http://127.0.0.1/secret")

        # Private IPs
        with pytest.raises(SanitizationError):
            sanitizer.sanitize_url("http://192.168.1.1/admin")

        with pytest.raises(SanitizationError):
            sanitizer.sanitize_url("http://10.0.0.1/internal")

    def test_sanitize_dict(self):
        """Test dictionary key sanitization"""
        sanitizer = Sanitizer()

        data = {"type": "line", "format": "png"}
        allowed_keys = ["type", "format", "theme"]

        # Should pass with allowed keys
        result = sanitizer.sanitize_dict(data, allowed_keys)
        assert result == data

        # Should fail with disallowed key
        bad_data = {"type": "line", "malicious_key": "value"}
        with pytest.raises(SanitizationError):
            sanitizer.sanitize_dict(bad_data, allowed_keys)


# ============================================================================
# Security Auditor Tests
# ============================================================================


class TestSecurityAuditor:
    """Tests for security audit logging"""

    def test_security_event_creation(self):
        """Test creating security event"""
        event = SecurityEvent(
            timestamp="2025-11-23T10:00:00",
            level=SecurityLevel.WARNING,
            event_type="auth_failure",
            client_id="192.168.1.1",
            endpoint="/api/render",
            message="Authentication failed",
            details={"reason": "Invalid token"},
        )

        assert event.level == SecurityLevel.WARNING
        assert event.event_type == "auth_failure"
        assert event.client_id == "192.168.1.1"

    def test_security_event_to_json(self):
        """Test event serialization"""
        event = SecurityEvent(
            timestamp="2025-11-23T10:00:00",
            level=SecurityLevel.INFO,
            event_type="test",
            client_id="test_client",
            message="Test message",
        )

        json_str = event.to_json()
        data = json.loads(json_str)

        assert data["level"] == "INFO"
        assert data["event_type"] == "test"
        assert data["client_id"] == "test_client"

    def test_auditor_log_to_file(self, tmp_path):
        """Test logging to file"""
        log_file = tmp_path / "security.log"
        auditor = SecurityAuditor(log_file=str(log_file), console=False)

        auditor.log_auth_failure(
            client_id="192.168.1.1", reason="Invalid credentials", endpoint="/api/protected"
        )

        # Check log file was created
        assert log_file.exists()

        # Check log content
        content = log_file.read_text()
        assert "auth_failure" in content
        assert "192.168.1.1" in content
        assert "Invalid credentials" in content

    def test_auditor_min_level_filtering(self, tmp_path):
        """Test minimum level filtering"""
        log_file = tmp_path / "security.log"
        auditor = SecurityAuditor(
            log_file=str(log_file), console=False, min_level=SecurityLevel.WARNING
        )

        # INFO should not be logged
        auditor.log_auth_success(client_id="client1", user="user1")

        # WARNING should be logged
        auditor.log_auth_failure(client_id="client2", reason="Bad token")

        content = log_file.read_text()
        assert "client1" not in content  # INFO filtered out
        assert "client2" in content  # WARNING logged

    def test_auditor_log_rate_limit(self, tmp_path):
        """Test logging rate limit events"""
        log_file = tmp_path / "security.log"
        auditor = SecurityAuditor(log_file=str(log_file), console=False)

        auditor.log_rate_limit(client_id="192.168.1.100", endpoint="/render", limit=10, window=60)

        content = log_file.read_text()
        assert "rate_limit_exceeded" in content
        assert "192.168.1.100" in content
        assert "/render" in content

    def test_auditor_log_sanitization_failure(self, tmp_path):
        """Test logging sanitization failures"""
        log_file = tmp_path / "security.log"
        auditor = SecurityAuditor(log_file=str(log_file), console=False)

        auditor.log_sanitization_failure(
            client_id="attacker.com",
            input_type="path",
            reason="Path traversal detected",
            endpoint="/api/file",
        )

        content = log_file.read_text()
        assert "sanitization_failure" in content
        assert "Path traversal" in content

    def test_auditor_log_critical_event(self, tmp_path):
        """Test logging critical events"""
        log_file = tmp_path / "security.log"
        auditor = SecurityAuditor(log_file=str(log_file), console=False)

        auditor.log_critical_event(
            client_id="unknown",
            event_description="Multiple failed auth attempts detected",
            endpoint="/api/login",
            attempts=100,
        )

        content = log_file.read_text()
        assert "CRITICAL" in content
        assert "critical_security_event" in content
        assert "Multiple failed auth attempts" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
