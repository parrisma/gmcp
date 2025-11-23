"""Unified Application Settings

Centralized, typed configuration for all gplot components (MCP, Web, scripts).
Consolidates server configuration, authentication, storage, and logging settings.

Design principles:
- Single source of truth for all configuration
- Environment variable overrides with sensible defaults
- Type-safe settings with validation
- Explicit security requirements (e.g., JWT secret enforcement)
- Test mode support for temporary directories
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ServerSettings:
    """Network server configuration"""

    host: str = "0.0.0.0"
    mcp_port: int = 8001
    web_port: int = 8000
    mcpo_port: int = 8002

    @classmethod
    def from_env(cls, prefix: str = "GPLOT") -> "ServerSettings":
        """Load server settings from environment variables"""
        return cls(
            host=os.environ.get(f"{prefix}_HOST", "0.0.0.0"),
            mcp_port=int(os.environ.get(f"{prefix}_MCP_PORT", "8001")),
            web_port=int(os.environ.get(f"{prefix}_WEB_PORT", "8000")),
            mcpo_port=int(os.environ.get(f"{prefix}_MCPO_PORT", "8002")),
        )


@dataclass
class AuthSettings:
    """Authentication and security configuration"""

    jwt_secret: Optional[str] = None
    token_store_path: Optional[Path] = None
    require_auth: bool = True

    def __post_init__(self):
        """Validate authentication settings"""
        if self.require_auth and not self.jwt_secret:
            raise ValueError(
                "JWT secret is required when authentication is enabled. "
                "Set GPLOT_JWT_SECRET environment variable or provide via --jwt-secret"
            )

        # Convert string path to Path object
        if isinstance(self.token_store_path, str):
            self.token_store_path = Path(self.token_store_path)

    @classmethod
    def from_env(cls, prefix: str = "GPLOT", require_auth: bool = True) -> "AuthSettings":
        """Load auth settings from environment variables"""
        jwt_secret = os.environ.get(f"{prefix}_JWT_SECRET")
        token_store = os.environ.get(f"{prefix}_TOKEN_STORE")

        return cls(
            jwt_secret=jwt_secret,
            token_store_path=Path(token_store) if token_store else None,
            require_auth=require_auth,
        )

    def get_secret_fingerprint(self) -> str:
        """Get SHA256 fingerprint of JWT secret for logging (first 12 chars)"""
        if not self.jwt_secret:
            return "none"
        import hashlib

        return f"sha256:{hashlib.sha256(self.jwt_secret.encode()).hexdigest()[:12]}"


@dataclass
class StorageSettings:
    """Data persistence configuration"""

    data_dir: Path
    storage_dir: Path
    auth_dir: Path

    @classmethod
    def from_env(cls, prefix: str = "GPLOT", test_mode: bool = False) -> "StorageSettings":
        """Load storage settings from environment variables"""
        # Check environment variable first
        env_data_dir = os.environ.get(f"{prefix}_DATA_DIR")
        if env_data_dir:
            data_dir = Path(env_data_dir)
        else:
            # Default to project data directory
            project_root = Path(__file__).parent.parent
            data_dir = project_root / "data"

        return cls(
            data_dir=data_dir,
            storage_dir=data_dir / "storage",
            auth_dir=data_dir / "auth",
        )

    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.auth_dir.mkdir(parents=True, exist_ok=True)

    def get_token_store_path(self) -> Path:
        """Get the path to the token store file"""
        return self.auth_dir / "tokens.json"


@dataclass
class LogSettings:
    """Logging configuration"""

    level: str = "INFO"
    format: str = "console"  # console, json, or structured

    @classmethod
    def from_env(cls, prefix: str = "GPLOT") -> "LogSettings":
        """Load logging settings from environment variables"""
        return cls(
            level=os.environ.get(f"{prefix}_LOG_LEVEL", "INFO").upper(),
            format=os.environ.get(f"{prefix}_LOG_FORMAT", "console").lower(),
        )


@dataclass
class Settings:
    """Complete application settings

    Aggregates all configuration domains into a single, typed settings object.
    Can be constructed from environment variables or explicit parameters.
    """

    server: ServerSettings = field(default_factory=ServerSettings)
    auth: AuthSettings = field(
        default_factory=lambda: AuthSettings(jwt_secret=None, require_auth=False)
    )
    storage: StorageSettings = field(default_factory=StorageSettings.from_env)
    log: LogSettings = field(default_factory=LogSettings)

    @classmethod
    def from_env(cls, prefix: str = "GPLOT", require_auth: bool = True) -> "Settings":
        """
        Load complete settings from environment variables

        Args:
            prefix: Environment variable prefix (default: GPLOT)
            require_auth: Whether authentication is required (default: True)

        Returns:
            Settings object populated from environment

        Environment variables:
            GPLOT_HOST: Server host (default: 0.0.0.0)
            GPLOT_MCP_PORT: MCP server port (default: 8001)
            GPLOT_WEB_PORT: Web server port (default: 8000)
            GPLOT_MCPO_PORT: MCPO proxy port (default: 8002)
            GPLOT_JWT_SECRET: JWT secret key (required if auth enabled)
            GPLOT_TOKEN_STORE: Token store path (default: {data_dir}/auth/tokens.json)
            GPLOT_DATA_DIR: Data directory (default: {project_root}/data)
            GPLOT_LOG_LEVEL: Logging level (default: INFO)
            GPLOT_LOG_FORMAT: Log format (default: console)
        """
        return cls(
            server=ServerSettings.from_env(prefix),
            auth=AuthSettings.from_env(prefix, require_auth),
            storage=StorageSettings.from_env(prefix),
            log=LogSettings.from_env(prefix),
        )

    def resolve_defaults(self) -> None:
        """
        Resolve any missing configuration with intelligent defaults

        - If token_store_path is None, use {storage.auth_dir}/tokens.json
        - Ensure all storage directories exist
        """
        # Ensure storage directories exist
        self.storage.ensure_directories()

        # Default token store to standard location if not specified
        if self.auth.token_store_path is None:
            self.auth.token_store_path = self.storage.get_token_store_path()

    def validate(self) -> None:
        """
        Validate settings for consistency and security

        Raises:
            ValueError: If settings are invalid or insecure
        """
        # Auth validation is handled in AuthSettings.__post_init__
        pass


# Singleton instance for backward compatibility
_global_settings: Optional[Settings] = None


def get_settings(reload: bool = False, require_auth: bool = True) -> Settings:
    """
    Get or create global settings instance

    Args:
        reload: If True, reload settings from environment
        require_auth: Whether authentication is required

    Returns:
        Global Settings instance
    """
    global _global_settings

    if _global_settings is None or reload:
        _global_settings = Settings.from_env(require_auth=require_auth)
        _global_settings.resolve_defaults()
        _global_settings.validate()

    return _global_settings


def reset_settings() -> None:
    """Reset global settings (primarily for testing)"""
    global _global_settings
    _global_settings = None


# Backward compatibility with existing Config class
class Config:
    """Legacy Config class for backward compatibility

    Wraps new Settings system to maintain existing API.
    """

    _test_mode: bool = False
    _test_data_dir: Optional[Path] = None

    @classmethod
    def get_data_dir(cls) -> Path:
        """Get the data directory for persistent storage"""
        if cls._test_mode and cls._test_data_dir:
            return cls._test_data_dir

        settings = get_settings(require_auth=False)
        return settings.storage.data_dir

    @classmethod
    def get_storage_dir(cls) -> Path:
        """Get the directory for image storage"""
        if cls._test_mode and cls._test_data_dir:
            return cls._test_data_dir / "storage"

        settings = get_settings(require_auth=False)
        return settings.storage.storage_dir

    @classmethod
    def get_auth_dir(cls) -> Path:
        """Get the directory for authentication data"""
        if cls._test_mode and cls._test_data_dir:
            return cls._test_data_dir / "auth"

        settings = get_settings(require_auth=False)
        return settings.storage.auth_dir

    @classmethod
    def get_token_store_path(cls) -> Path:
        """Get the path to the token store file"""
        if cls._test_mode and cls._test_data_dir:
            return cls._test_data_dir / "auth" / "tokens.json"

        settings = get_settings(require_auth=False)
        return settings.storage.get_token_store_path()

    @classmethod
    def set_test_mode(cls, test_data_dir: Optional[Path] = None) -> None:
        """Enable test mode with optional custom data directory"""
        cls._test_mode = True
        cls._test_data_dir = test_data_dir

    @classmethod
    def clear_test_mode(cls) -> None:
        """Disable test mode and return to normal configuration"""
        cls._test_mode = False
        cls._test_data_dir = None

    @classmethod
    def is_test_mode(cls) -> bool:
        """Check if currently in test mode"""
        return cls._test_mode


# Convenience functions for backward compatibility
def get_default_storage_dir() -> str:
    """Get default storage directory as string"""
    return str(Config.get_storage_dir())


def get_default_token_store_path() -> str:
    """Get default token store path as string"""
    return str(Config.get_token_store_path())
