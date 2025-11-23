"""Application configuration (DEPRECATED - use app.settings instead)

This module is maintained for backward compatibility.
New code should use app.settings.Settings instead.

Legacy exports:
- Config class: Use app.settings.Config (backward compatible wrapper)
- get_default_storage_dir(): Use app.settings.get_settings().storage.storage_dir
- get_default_token_store_path(): Use app.settings.get_settings().auth.token_store_path
"""

# Re-export from settings for backward compatibility
from app.settings import (
    Config,
    get_default_storage_dir,
    get_default_token_store_path,
)

__all__ = [
    "Config",
    "get_default_storage_dir",
    "get_default_token_store_path",
]
