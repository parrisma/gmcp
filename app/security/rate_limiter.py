"""Rate limiting using token bucket algorithm

Provides per-client and per-endpoint rate limiting to prevent abuse.
"""

import time
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass, field
from threading import Lock


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""

    def __init__(self, limit: int, window: int, retry_after: float):
        self.limit = limit
        self.window = window
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded: {limit} requests per {window}s. "
            f"Retry after {retry_after:.1f}s"
        )


@dataclass
class TokenBucket:
    """Token bucket for rate limiting

    Implements the token bucket algorithm:
    - Tokens are added at a fixed rate
    - Requests consume tokens
    - If no tokens available, request is denied
    """

    capacity: int  # Maximum tokens
    refill_rate: float  # Tokens added per second
    tokens: float = field(init=False)
    last_refill: float = field(init=False)

    def __post_init__(self):
        self.tokens = float(self.capacity)
        self.last_refill = time.time()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill

        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def consume(self, tokens: int = 1) -> Tuple[bool, float]:
        """Consume tokens from bucket

        Args:
            tokens: Number of tokens to consume

        Returns:
            Tuple of (success, retry_after_seconds)
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True, 0.0
        else:
            # Calculate how long until enough tokens available
            tokens_needed = tokens - self.tokens
            retry_after = tokens_needed / self.refill_rate
            return False, retry_after


class RateLimiter:
    """Rate limiter with per-client and per-endpoint limits

    Uses token bucket algorithm for smooth rate limiting.
    Supports different limits for different endpoints and clients.

    Example:
        limiter = RateLimiter(default_limit=100, window=60)

        # Set custom limit for expensive endpoint
        limiter.set_endpoint_limit("/render", limit=10, window=60)

        # Check if request allowed
        try:
            limiter.check_limit(client_id="192.168.1.1", endpoint="/render")
            # Process request
        except RateLimitExceeded as e:
            # Return 429 with Retry-After header
            pass
    """

    def __init__(self, default_limit: int = 100, window: int = 60, enable: bool = True):
        """Initialize rate limiter

        Args:
            default_limit: Default requests per window
            window: Time window in seconds
            enable: Whether rate limiting is enabled
        """
        self.default_limit = default_limit
        self.window = window
        self.enable = enable

        # Endpoint-specific limits: {endpoint: (limit, window)}
        self.endpoint_limits: Dict[str, Tuple[int, int]] = {}

        # Client buckets: {(client_id, endpoint): TokenBucket}
        self.buckets: Dict[Tuple[str, str], TokenBucket] = {}
        self._lock = Lock()

    def set_endpoint_limit(self, endpoint: str, limit: int, window: Optional[int] = None) -> None:
        """Set custom rate limit for specific endpoint

        Args:
            endpoint: Endpoint path (e.g., "/render")
            limit: Requests per window
            window: Time window in seconds (uses default if None)
        """
        with self._lock:
            self.endpoint_limits[endpoint] = (limit, window or self.window)

    def get_limit(self, endpoint: str) -> Tuple[int, int]:
        """Get rate limit for endpoint

        Args:
            endpoint: Endpoint path

        Returns:
            Tuple of (limit, window)
        """
        if endpoint in self.endpoint_limits:
            return self.endpoint_limits[endpoint]
        return self.default_limit, self.window

    def _get_bucket(self, client_id: str, endpoint: str) -> TokenBucket:
        """Get or create token bucket for client+endpoint

        Args:
            client_id: Client identifier (IP, user ID, etc.)
            endpoint: Endpoint path

        Returns:
            TokenBucket for this client+endpoint
        """
        key = (client_id, endpoint)

        with self._lock:
            if key not in self.buckets:
                limit, window = self.get_limit(endpoint)
                capacity = limit
                refill_rate = limit / window
                self.buckets[key] = TokenBucket(capacity, refill_rate)

            return self.buckets[key]

    def check_limit(self, client_id: str, endpoint: str = "default", cost: int = 1) -> None:
        """Check if request is within rate limit

        Args:
            client_id: Client identifier (IP, user ID, token, etc.)
            endpoint: Endpoint path
            cost: Token cost of this request (default 1)

        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        if not self.enable:
            return

        bucket = self._get_bucket(client_id, endpoint)
        allowed, retry_after = bucket.consume(cost)

        if not allowed:
            limit, window = self.get_limit(endpoint)
            raise RateLimitExceeded(limit, window, retry_after)

    def reset_client(self, client_id: str, endpoint: Optional[str] = None) -> None:
        """Reset rate limit for client

        Args:
            client_id: Client identifier
            endpoint: Specific endpoint (None for all endpoints)
        """
        with self._lock:
            if endpoint:
                key = (client_id, endpoint)
                if key in self.buckets:
                    del self.buckets[key]
            else:
                # Remove all buckets for this client
                keys_to_remove = [key for key in self.buckets.keys() if key[0] == client_id]
                for key in keys_to_remove:
                    del self.buckets[key]

    def cleanup_stale_buckets(self, max_age: float = 3600) -> int:
        """Remove buckets that haven't been used recently

        Args:
            max_age: Maximum age in seconds

        Returns:
            Number of buckets removed
        """
        now = time.time()
        removed = 0

        with self._lock:
            keys_to_remove = [
                key for key, bucket in self.buckets.items() if now - bucket.last_refill > max_age
            ]

            for key in keys_to_remove:
                del self.buckets[key]
                removed += 1

        return removed

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics

        Returns:
            Dict with stats about buckets and limits
        """
        with self._lock:
            return {
                "enabled": self.enable,
                "default_limit": self.default_limit,
                "window": self.window,
                "endpoint_limits": dict(self.endpoint_limits),
                "active_buckets": len(self.buckets),
                "clients": len(set(key[0] for key in self.buckets.keys())),
            }


# Global rate limiter instance (can be configured via settings)
_global_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = RateLimiter()
    return _global_limiter


def configure_rate_limiter(
    default_limit: int = 100, window: int = 60, enable: bool = True
) -> RateLimiter:
    """Configure global rate limiter

    Args:
        default_limit: Default requests per window
        window: Time window in seconds
        enable: Whether to enable rate limiting

    Returns:
        Configured RateLimiter instance
    """
    global _global_limiter
    _global_limiter = RateLimiter(default_limit, window, enable)
    return _global_limiter
