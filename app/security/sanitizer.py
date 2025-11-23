"""Input sanitization utilities

Prevents injection attacks, path traversal, and XSS in outputs.
"""

import re
import html
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse


class SanitizationError(Exception):
    """Exception raised when input fails sanitization"""

    pass


class Sanitizer:
    """Input sanitization for security

    Provides methods to sanitize various types of input:
    - Chart parameters (type, format, theme)
    - File paths (prevent traversal)
    - String inputs (prevent XSS, injection)
    - Numeric ranges (prevent overflow)

    Example:
        sanitizer = Sanitizer()

        # Sanitize chart type
        chart_type = sanitizer.sanitize_chart_type(user_input)

        # Sanitize file path
        safe_path = sanitizer.sanitize_path(user_path, base_dir="/data")

        # Sanitize for SVG output
        safe_text = sanitizer.sanitize_for_svg(user_title)
    """

    # Allowed values for chart parameters
    ALLOWED_CHART_TYPES = {"line", "scatter", "bar"}
    ALLOWED_FORMATS = {"png", "jpg", "jpeg", "svg", "pdf"}
    ALLOWED_THEMES = {"light", "dark", "bizlight", "bizdark"}
    ALLOWED_SCALES = {"linear", "log", "symlog", "logit"}

    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\.",  # Parent directory
        r"~",  # Home directory
        r"/etc",  # System directories
        r"/proc",
        r"/sys",
        r"\\",  # Windows paths
    ]

    # SQL injection patterns (for future database features)
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|\/\*|\*\/)",  # SQL comments
        r"(\bOR\b.*=.*\bOR\b)",  # OR injection
        r"(\bUNION\b.*\bSELECT\b)",  # UNION injection
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"onclick\s*=",
    ]

    def __init__(self, strict: bool = True):
        """Initialize sanitizer

        Args:
            strict: If True, reject suspicious input; if False, attempt to clean
        """
        self.strict = strict

    def sanitize_chart_type(self, chart_type: str) -> str:
        """Sanitize chart type parameter

        Args:
            chart_type: User-provided chart type

        Returns:
            Sanitized chart type

        Raises:
            SanitizationError: If chart type is invalid
        """
        if not isinstance(chart_type, str):
            raise SanitizationError(f"Chart type must be string, got {type(chart_type)}")

        chart_type = chart_type.lower().strip()

        if chart_type not in self.ALLOWED_CHART_TYPES:
            raise SanitizationError(
                f"Invalid chart type: {chart_type}. "
                f"Allowed: {', '.join(self.ALLOWED_CHART_TYPES)}"
            )

        return chart_type

    def sanitize_format(self, format: str) -> str:
        """Sanitize output format parameter

        Args:
            format: User-provided format

        Returns:
            Sanitized format

        Raises:
            SanitizationError: If format is invalid
        """
        if not isinstance(format, str):
            raise SanitizationError(f"Format must be string, got {type(format)}")

        format = format.lower().strip()

        if format not in self.ALLOWED_FORMATS:
            raise SanitizationError(
                f"Invalid format: {format}. " f"Allowed: {', '.join(self.ALLOWED_FORMATS)}"
            )

        return format

    def sanitize_theme(self, theme: str) -> str:
        """Sanitize theme parameter

        Args:
            theme: User-provided theme

        Returns:
            Sanitized theme

        Raises:
            SanitizationError: If theme is invalid
        """
        if not isinstance(theme, str):
            raise SanitizationError(f"Theme must be string, got {type(theme)}")

        theme = theme.lower().strip()

        if theme not in self.ALLOWED_THEMES:
            raise SanitizationError(
                f"Invalid theme: {theme}. " f"Allowed: {', '.join(self.ALLOWED_THEMES)}"
            )

        return theme

    def sanitize_scale(self, scale: str) -> str:
        """Sanitize axis scale parameter

        Args:
            scale: User-provided scale

        Returns:
            Sanitized scale

        Raises:
            SanitizationError: If scale is invalid
        """
        if not isinstance(scale, str):
            raise SanitizationError(f"Scale must be string, got {type(scale)}")

        scale = scale.lower().strip()

        if scale not in self.ALLOWED_SCALES:
            raise SanitizationError(
                f"Invalid scale: {scale}. " f"Allowed: {', '.join(self.ALLOWED_SCALES)}"
            )

        return scale

    def sanitize_path(
        self, path: str, base_dir: Optional[str] = None, must_exist: bool = False
    ) -> Path:
        """Sanitize file path to prevent traversal attacks

        Args:
            path: User-provided path
            base_dir: Required base directory (path must be within this)
            must_exist: If True, path must exist

        Returns:
            Sanitized Path object

        Raises:
            SanitizationError: If path is suspicious or invalid
        """
        if not isinstance(path, str):
            raise SanitizationError(f"Path must be string, got {type(path)}")

        # Check for path traversal patterns
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                raise SanitizationError(f"Suspicious path pattern detected: {pattern}")

        # Convert to Path object and resolve
        try:
            safe_path = Path(path).resolve()
        except Exception as e:
            raise SanitizationError(f"Invalid path: {e}")

        # Check if within base directory
        if base_dir:
            base = Path(base_dir).resolve()
            try:
                safe_path.relative_to(base)
            except ValueError:
                raise SanitizationError(f"Path {path} is outside base directory {base_dir}")

        # Check existence if required
        if must_exist and not safe_path.exists():
            raise SanitizationError(f"Path does not exist: {path}")

        return safe_path

    def sanitize_string(
        self, text: str, max_length: int = 1000, allow_newlines: bool = True
    ) -> str:
        """Sanitize general string input

        Args:
            text: User-provided text
            max_length: Maximum allowed length
            allow_newlines: Whether to allow newline characters

        Returns:
            Sanitized string

        Raises:
            SanitizationError: If string is suspicious or too long
        """
        if not isinstance(text, str):
            raise SanitizationError(f"Text must be string, got {type(text)}")

        # Check length
        if len(text) > max_length:
            if self.strict:
                raise SanitizationError(f"String too long: {len(text)} > {max_length}")
            else:
                text = text[:max_length]

        # Check for SQL injection patterns
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise SanitizationError("Suspicious SQL pattern detected")

        # Check for XSS patterns
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                raise SanitizationError("Suspicious XSS pattern detected")

        # Remove newlines if not allowed
        if not allow_newlines:
            text = text.replace("\n", " ").replace("\r", " ")

        return text.strip()

    def sanitize_for_svg(self, text: str) -> str:
        """Sanitize text for inclusion in SVG output

        SVG can contain JavaScript, so we need to escape carefully.

        Args:
            text: Text to include in SVG

        Returns:
            Escaped text safe for SVG
        """
        # First do general sanitization
        text = self.sanitize_string(text, max_length=500, allow_newlines=False)

        # HTML escape to prevent script injection
        text = html.escape(text, quote=True)

        # Remove any remaining potentially dangerous characters
        text = text.replace("<", "&lt;").replace(">", "&gt;")
        text = text.replace("&", "&amp;").replace('"', "&quot;")

        return text

    def sanitize_numeric_range(
        self,
        value: Union[int, float],
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
    ) -> Union[int, float]:
        """Sanitize numeric value to be within range

        Args:
            value: Numeric value
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            Sanitized numeric value

        Raises:
            SanitizationError: If value is out of range
        """
        if not isinstance(value, (int, float)):
            raise SanitizationError(f"Value must be numeric, got {type(value)}")

        if min_val is not None and value < min_val:
            raise SanitizationError(f"Value {value} below minimum {min_val}")

        if max_val is not None and value > max_val:
            raise SanitizationError(f"Value {value} above maximum {max_val}")

        return value

    def sanitize_url(self, url: str) -> str:
        """Sanitize URL to prevent SSRF attacks

        Args:
            url: User-provided URL

        Returns:
            Sanitized URL

        Raises:
            SanitizationError: If URL is suspicious
        """
        if not isinstance(url, str):
            raise SanitizationError(f"URL must be string, got {type(url)}")

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise SanitizationError(f"Invalid URL: {e}")

        # Check scheme (only allow http/https)
        if parsed.scheme not in ("http", "https"):
            raise SanitizationError(
                f"Invalid URL scheme: {parsed.scheme}. " "Only http/https allowed"
            )

        # Check for localhost/private IPs (prevent SSRF)
        hostname = parsed.hostname
        if hostname:
            hostname_lower = hostname.lower()
            if hostname_lower in ("localhost", "127.0.0.1", "::1"):
                raise SanitizationError("Localhost URLs not allowed")

            # Check for private IP ranges
            if hostname_lower.startswith(("10.", "172.16.", "192.168.")):
                raise SanitizationError("Private IP addresses not allowed")

        return url

    def sanitize_dict(
        self, data: Dict[str, Any], allowed_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Sanitize dictionary by checking keys

        Args:
            data: User-provided dictionary
            allowed_keys: List of allowed keys (None for no restriction)

        Returns:
            Sanitized dictionary

        Raises:
            SanitizationError: If dictionary contains disallowed keys
        """
        if not isinstance(data, dict):
            raise SanitizationError(f"Data must be dict, got {type(data)}")

        if allowed_keys is not None:
            for key in data.keys():
                if key not in allowed_keys:
                    raise SanitizationError(
                        f"Disallowed key: {key}. " f"Allowed: {', '.join(allowed_keys)}"
                    )

        return data


# Global sanitizer instance
_global_sanitizer: Optional[Sanitizer] = None


def get_sanitizer(strict: bool = True) -> Sanitizer:
    """Get global sanitizer instance

    Args:
        strict: Whether to use strict mode

    Returns:
        Sanitizer instance
    """
    global _global_sanitizer
    if _global_sanitizer is None or _global_sanitizer.strict != strict:
        _global_sanitizer = Sanitizer(strict=strict)
    return _global_sanitizer
