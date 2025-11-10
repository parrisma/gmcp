"""Image storage module

Provides abstract base class and concrete implementations for image storage.
"""

from app.storage.base import ImageStorageBase
from app.storage.file_storage import FileStorage
from typing import Optional

# Global storage instance
_storage: Optional[ImageStorageBase] = None


def get_storage(storage_dir: str = "/tmp/gplot_images") -> ImageStorageBase:
    """
    Get or create the global storage instance

    Args:
        storage_dir: Directory for file storage (only used on first call)

    Returns:
        ImageStorageBase implementation (currently FileStorage)
    """
    global _storage
    if _storage is None:
        _storage = FileStorage(storage_dir)
    return _storage


def set_storage(storage: ImageStorageBase) -> None:
    """
    Set a custom storage implementation

    Args:
        storage: Custom storage implementation
    """
    global _storage
    _storage = storage


__all__ = [
    "ImageStorageBase",
    "FileStorage",
    "get_storage",
    "set_storage",
]
