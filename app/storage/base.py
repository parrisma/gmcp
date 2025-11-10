"""Base storage interface for image storage

Defines the abstract interface that all storage implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, List


class ImageStorageBase(ABC):
    """Abstract base class for image storage implementations"""

    @abstractmethod
    def save_image(self, image_data: bytes, format: str = "png") -> str:
        """
        Save image data and return a unique identifier

        Args:
            image_data: Raw image bytes
            format: Image format (png, jpg, svg, pdf, etc.)

        Returns:
            Unique identifier (e.g., GUID, key, path) for the saved image

        Raises:
            RuntimeError: If save fails
        """
        pass

    @abstractmethod
    def get_image(self, identifier: str) -> Optional[Tuple[bytes, str]]:
        """
        Retrieve image data by identifier

        Args:
            identifier: Unique identifier for the image

        Returns:
            Tuple of (image_data, format) or None if not found

        Raises:
            ValueError: If identifier format is invalid
            RuntimeError: If retrieval fails
        """
        pass

    @abstractmethod
    def delete_image(self, identifier: str) -> bool:
        """
        Delete image by identifier

        Args:
            identifier: Unique identifier for the image

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If identifier format is invalid
        """
        pass

    @abstractmethod
    def list_images(self) -> List[str]:
        """
        List all stored image identifiers

        Returns:
            List of identifier strings
        """
        pass

    @abstractmethod
    def exists(self, identifier: str) -> bool:
        """
        Check if an image exists

        Args:
            identifier: Unique identifier for the image

        Returns:
            True if image exists, False otherwise
        """
        pass
