"""Metadata repository for image storage

Separates metadata management from blob storage for better separation of concerns.
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from app.logger import ConsoleLogger
import logging


class ImageMetadata:
    """Immutable image metadata"""

    def __init__(
        self,
        guid: str,
        format: str,
        size: int,
        created_at: str,
        group: Optional[str] = None,
        **kwargs,
    ):
        self.guid = guid
        self.format = format
        self.size = size
        self.created_at = created_at
        self.group = group
        self.extra = kwargs  # Additional metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        data = {
            "format": self.format,
            "size": self.size,
            "created_at": self.created_at,
        }
        if self.group is not None:
            data["group"] = self.group
        if self.extra:
            data.update(self.extra)
        return data

    @classmethod
    def from_dict(cls, guid: str, data: Dict[str, Any]) -> "ImageMetadata":
        """Create from dictionary representation"""
        return cls(
            guid=guid,
            format=data.get("format", "png"),
            size=data.get("size", 0),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            group=data.get("group"),
            **{k: v for k, v in data.items() if k not in ["format", "size", "created_at", "group"]},
        )

    def __repr__(self) -> str:
        return f"ImageMetadata(guid={self.guid}, format={self.format}, size={self.size}, group={self.group})"


class MetadataRepository(ABC):
    """Abstract base class for metadata storage"""

    @abstractmethod
    def save(self, metadata: ImageMetadata) -> None:
        """Save image metadata"""
        pass

    @abstractmethod
    def get(self, guid: str) -> Optional[ImageMetadata]:
        """Get metadata by GUID"""
        pass

    @abstractmethod
    def delete(self, guid: str) -> bool:
        """Delete metadata by GUID"""
        pass

    @abstractmethod
    def list_all(self, group: Optional[str] = None) -> List[str]:
        """List all GUIDs, optionally filtered by group"""
        pass

    @abstractmethod
    def exists(self, guid: str) -> bool:
        """Check if metadata exists"""
        pass

    @abstractmethod
    def filter_by_age(self, age_days: int, group: Optional[str] = None) -> List[ImageMetadata]:
        """Get metadata for images older than specified age"""
        pass


class JsonMetadataRepository(MetadataRepository):
    """JSON file-based metadata repository"""

    def __init__(self, metadata_file: Path):
        """
        Initialize JSON metadata repository

        Args:
            metadata_file: Path to metadata JSON file
        """
        self.metadata_file = metadata_file
        self.logger = ConsoleLogger(name="metadata_repo", level=logging.INFO)
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        """Load metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._data = data
                        self.logger.debug("Metadata loaded", count=len(self._data))
                    else:
                        self.logger.warning("Metadata has unexpected structure, resetting")
                        self._data = {}
            except Exception as e:
                self.logger.error("Failed to load metadata", error=str(e))
                self._data = {}
        else:
            self._data = {}
            self.logger.debug("Metadata initialized as empty")

    def _save(self) -> None:
        """Save metadata to file"""
        try:
            # Ensure directory exists
            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metadata_file, "w") as f:
                json.dump(self._data, f, indent=2)
            self.logger.debug("Metadata saved", count=len(self._data))
        except Exception as e:
            self.logger.error("Failed to save metadata", error=str(e))
            raise RuntimeError(f"Failed to save metadata: {str(e)}")

    def save(self, metadata: ImageMetadata) -> None:
        """Save image metadata"""
        self._data[metadata.guid] = metadata.to_dict()
        self._save()
        self.logger.debug("Metadata saved", guid=metadata.guid)

    def get(self, guid: str) -> Optional[ImageMetadata]:
        """Get metadata by GUID"""
        if guid in self._data:
            return ImageMetadata.from_dict(guid, self._data[guid])
        return None

    def delete(self, guid: str) -> bool:
        """Delete metadata by GUID"""
        if guid in self._data:
            del self._data[guid]
            self._save()
            self.logger.debug("Metadata deleted", guid=guid)
            return True
        return False

    def list_all(self, group: Optional[str] = None) -> List[str]:
        """List all GUIDs, optionally filtered by group"""
        if group is None:
            return list(self._data.keys())
        return [guid for guid, data in self._data.items() if data.get("group") == group]

    def exists(self, guid: str) -> bool:
        """Check if metadata exists"""
        return guid in self._data

    def filter_by_age(self, age_days: int, group: Optional[str] = None) -> List[ImageMetadata]:
        """Get metadata for images older than specified age"""
        from datetime import timedelta

        results = []
        cutoff_time = None if age_days == 0 else datetime.utcnow() - timedelta(days=age_days)

        for guid, data in self._data.items():
            # Filter by group if specified
            if group is not None and data.get("group") != group:
                continue

            # Check age
            if age_days == 0:
                # Include all matching group
                results.append(ImageMetadata.from_dict(guid, data))
            elif cutoff_time is not None and "created_at" in data:
                try:
                    created_at = datetime.fromisoformat(data["created_at"])
                    if created_at < cutoff_time:
                        results.append(ImageMetadata.from_dict(guid, data))
                except (ValueError, TypeError):
                    # If we can't parse, include it for cleanup
                    results.append(ImageMetadata.from_dict(guid, data))

        return results
