"""File-based storage implementation

Stores images as files in a directory with GUID-based filenames.
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Tuple, List
from app.storage.base import ImageStorageBase
from app.logger import ConsoleLogger
import logging


class FileStorage(ImageStorageBase):
    """File-based image storage using GUID filenames"""

    def __init__(self, storage_dir: str = "/tmp/gplot_images"):
        """
        Initialize file storage

        Args:
            storage_dir: Directory to store images (default: /tmp/gplot_images)
        """
        self.storage_dir = Path(storage_dir)
        self.logger = ConsoleLogger(name="file_storage", level=logging.INFO)

        # Create storage directory if it doesn't exist
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info("File storage initialized", directory=str(self.storage_dir))
        except Exception as e:
            self.logger.error("Failed to create storage directory", error=str(e))
            raise RuntimeError(f"Failed to create storage directory: {str(e)}")

    def save_image(self, image_data: bytes, format: str = "png") -> str:
        """
        Save image data to disk with a unique GUID

        Args:
            image_data: Raw image bytes
            format: Image format (png, jpg, svg, pdf, etc.)

        Returns:
            GUID string (identifier without extension)

        Raises:
            RuntimeError: If save fails
        """
        # Generate unique GUID
        guid = str(uuid.uuid4())
        filename = f"{guid}.{format.lower()}"
        filepath = self.storage_dir / filename

        self.logger.debug("Saving image to file", guid=guid, format=format, size=len(image_data))

        try:
            with open(filepath, "wb") as f:
                f.write(image_data)
            self.logger.info("Image saved to file", guid=guid, path=str(filepath))
            return guid
        except Exception as e:
            self.logger.error("Failed to save image file", guid=guid, error=str(e))
            raise RuntimeError(f"Failed to save image: {str(e)}")

    def get_image(self, identifier: str) -> Optional[Tuple[bytes, str]]:
        """
        Retrieve image data by GUID

        Args:
            identifier: GUID string (without extension)

        Returns:
            Tuple of (image_data, format) or None if not found

        Raises:
            ValueError: If GUID format is invalid
        """
        # Validate GUID format
        try:
            uuid.UUID(identifier)
        except ValueError:
            self.logger.warning("Invalid GUID format", guid=identifier)
            raise ValueError(f"Invalid GUID format: {identifier}")

        self.logger.debug("Retrieving image from file", guid=identifier)

        # Try common formats
        for ext in ["png", "jpg", "jpeg", "svg", "pdf"]:
            filepath = self.storage_dir / f"{identifier}.{ext}"
            if filepath.exists():
                try:
                    with open(filepath, "rb") as f:
                        image_data = f.read()
                    self.logger.info(
                        "Image retrieved from file",
                        guid=identifier,
                        format=ext,
                        size=len(image_data),
                    )
                    return (image_data, ext)
                except Exception as e:
                    self.logger.error("Failed to read image file", guid=identifier, error=str(e))
                    raise RuntimeError(f"Failed to read image: {str(e)}")

        self.logger.warning("Image file not found", guid=identifier)
        return None

    def delete_image(self, identifier: str) -> bool:
        """
        Delete image file by GUID

        Args:
            identifier: GUID string (without extension)

        Returns:
            True if deleted, False if not found
        """
        # Validate GUID format
        try:
            uuid.UUID(identifier)
        except ValueError:
            self.logger.warning("Invalid GUID format for deletion", guid=identifier)
            return False

        deleted = False
        for ext in ["png", "jpg", "jpeg", "svg", "pdf"]:
            filepath = self.storage_dir / f"{identifier}.{ext}"
            if filepath.exists():
                try:
                    filepath.unlink()
                    self.logger.info("Image file deleted", guid=identifier, format=ext)
                    deleted = True
                except Exception as e:
                    self.logger.error("Failed to delete image file", guid=identifier, error=str(e))

        return deleted

    def list_images(self) -> List[str]:
        """
        List all stored image GUIDs

        Returns:
            List of GUID strings
        """
        try:
            guids = set()
            for filepath in self.storage_dir.iterdir():
                if filepath.is_file():
                    # Extract GUID (filename without extension)
                    guid = filepath.stem
                    try:
                        uuid.UUID(guid)
                        guids.add(guid)
                    except ValueError:
                        # Skip non-GUID files
                        pass
            self.logger.debug("Listed image files", count=len(guids))
            return sorted(guids)
        except Exception as e:
            self.logger.error("Failed to list image files", error=str(e))
            return []

    def exists(self, identifier: str) -> bool:
        """
        Check if an image file exists

        Args:
            identifier: GUID string (without extension)

        Returns:
            True if image exists, False otherwise
        """
        # Validate GUID format
        try:
            uuid.UUID(identifier)
        except ValueError:
            return False

        # Check for any matching file with common extensions
        for ext in ["png", "jpg", "jpeg", "svg", "pdf"]:
            filepath = self.storage_dir / f"{identifier}.{ext}"
            if filepath.exists():
                return True

        return False
