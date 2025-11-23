"""Blob repository for image storage

Handles raw binary data storage separately from metadata.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List
from app.logger import ConsoleLogger
import logging
import uuid


class BlobRepository(ABC):
    """Abstract base class for blob storage"""

    @abstractmethod
    def save(self, guid: str, data: bytes, format: str) -> None:
        """Save blob data"""
        pass

    @abstractmethod
    def get(self, guid: str, format: str) -> Optional[bytes]:
        """Get blob data by GUID and format"""
        pass

    @abstractmethod
    def delete(self, guid: str, format: Optional[str] = None) -> bool:
        """Delete blob by GUID (all formats if format not specified)"""
        pass

    @abstractmethod
    def exists(self, guid: str, format: Optional[str] = None) -> bool:
        """Check if blob exists (any format if format not specified)"""
        pass

    @abstractmethod
    def list_all(self) -> List[str]:
        """List all blob GUIDs"""
        pass


class FileBlobRepository(BlobRepository):
    """File-based blob storage"""

    SUPPORTED_FORMATS = ["png", "jpg", "jpeg", "svg", "pdf"]

    def __init__(self, storage_dir: Path):
        """
        Initialize file blob repository

        Args:
            storage_dir: Directory to store blob files
        """
        self.storage_dir = storage_dir
        self.logger = ConsoleLogger(name="blob_repo", level=logging.INFO)

        # Create storage directory if it doesn't exist
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info("Blob storage initialized", directory=str(self.storage_dir))
        except Exception as e:
            self.logger.error("Failed to create storage directory", error=str(e))
            raise RuntimeError(f"Failed to create storage directory: {str(e)}")

    def _get_filepath(self, guid: str, format: str) -> Path:
        """Get file path for a blob"""
        return self.storage_dir / f"{guid}.{format.lower()}"

    def save(self, guid: str, data: bytes, format: str) -> None:
        """Save blob data to file"""
        filepath = self._get_filepath(guid, format)

        try:
            with open(filepath, "wb") as f:
                f.write(data)
            self.logger.debug("Blob saved", guid=guid, format=format, size=len(data))
        except Exception as e:
            self.logger.error("Failed to save blob", guid=guid, error=str(e))
            raise RuntimeError(f"Failed to save blob: {str(e)}")

    def get(self, guid: str, format: str) -> Optional[bytes]:
        """Get blob data from file"""
        filepath = self._get_filepath(guid, format)

        if filepath.exists():
            try:
                with open(filepath, "rb") as f:
                    data = f.read()
                self.logger.debug("Blob retrieved", guid=guid, format=format, size=len(data))
                return data
            except Exception as e:
                self.logger.error("Failed to read blob", guid=guid, error=str(e))
                raise RuntimeError(f"Failed to read blob: {str(e)}")

        return None

    def delete(self, guid: str, format: Optional[str] = None) -> bool:
        """Delete blob file(s)"""
        deleted = False

        formats_to_check = [format] if format else self.SUPPORTED_FORMATS

        for fmt in formats_to_check:
            filepath = self._get_filepath(guid, fmt)
            if filepath.exists():
                try:
                    filepath.unlink()
                    self.logger.debug("Blob deleted", guid=guid, format=fmt)
                    deleted = True
                except Exception as e:
                    self.logger.error("Failed to delete blob", guid=guid, format=fmt, error=str(e))

        return deleted

    def exists(self, guid: str, format: Optional[str] = None) -> bool:
        """Check if blob file exists"""
        if format:
            return self._get_filepath(guid, format).exists()

        # Check any supported format
        for fmt in self.SUPPORTED_FORMATS:
            if self._get_filepath(guid, fmt).exists():
                return True

        return False

    def list_all(self) -> List[str]:
        """List all blob GUIDs"""
        try:
            guids = set()
            for filepath in self.storage_dir.iterdir():
                if filepath.is_file() and filepath.suffix.lstrip(".") in self.SUPPORTED_FORMATS:
                    guid = filepath.stem
                    try:
                        uuid.UUID(guid)
                        guids.add(guid)
                    except ValueError:
                        # Skip non-GUID files
                        pass
            return sorted(guids)
        except Exception as e:
            self.logger.error("Failed to list blobs", error=str(e))
            return []

    def get_format(self, guid: str) -> Optional[str]:
        """
        Detect the format of a stored blob

        Args:
            guid: GUID of the blob

        Returns:
            Format string or None if not found
        """
        for fmt in self.SUPPORTED_FORMATS:
            if self._get_filepath(guid, fmt).exists():
                return fmt
        return None
