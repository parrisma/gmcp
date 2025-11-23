#!/usr/bin/env python3
"""Consolidated storage tests

Combines tests for:
- Purge functionality (test_storage_purge.py)
- Concurrent access (test_concurrent_access.py)
- Metadata corruption (test_metadata_corruption.py)
- Storage failures (test_storage_failures.py)

Organized into logical test classes for better structure.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import os
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

from app.storage.file_storage import FileStorage


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def storage_with_images(temp_storage_dir):
    """Create storage with test images in multiple groups"""
    storage = FileStorage(storage_dir=temp_storage_dir)
    guids = {"group1": [], "group2": [], "no_group": []}

    # Add 3 images to group1
    for i in range(3):
        guid = storage.save_image(f"group1_image_{i}".encode(), format="png", group="group1")
        guids["group1"].append(guid)

    # Add 2 images to group2
    for i in range(2):
        guid = storage.save_image(f"group2_image_{i}".encode(), format="png", group="group2")
        guids["group2"].append(guid)

    # Add 2 images with no group
    for i in range(2):
        guid = storage.save_image(f"no_group_image_{i}".encode(), format="png", group=None)
        guids["no_group"].append(guid)

    return storage, guids


# ============================================================================
# Purge Tests
# ============================================================================


class TestStoragePurge:
    """Tests for storage purge functionality"""

    def test_purge_all_images(self, storage_with_images):
        """Test purging all images (age_days=0, no group filter)"""
        storage, guids = storage_with_images

        # Verify initial count
        assert len(storage.list_images()) == 7

        # Purge all images
        deleted = storage.purge(age_days=0)

        # Verify all deleted
        assert deleted == 7
        assert len(storage.list_images()) == 0

    def test_purge_specific_group(self, storage_with_images):
        """Test purging images from a specific group only"""
        storage, guids = storage_with_images

        # Purge only group1 images
        deleted = storage.purge(age_days=0, group="group1")

        # Verify only group1 deleted
        assert deleted == 3
        assert len(storage.list_images()) == 4

        # Verify group1 images are gone
        for guid in guids["group1"]:
            assert not storage.exists(guid)

        # Verify other images still exist
        for guid in guids["group2"] + guids["no_group"]:
            assert storage.exists(guid)

    def test_purge_by_age_no_old_images(self, storage_with_images):
        """Test purging by age when no images are old enough"""
        storage, guids = storage_with_images

        # Try to purge images older than 30 days (all images are brand new)
        deleted = storage.purge(age_days=30)

        # Nothing should be deleted
        assert deleted == 0
        assert len(storage.list_images()) == 7

    def test_purge_by_age_with_old_images(self, temp_storage_dir):
        """Test purging by age with artificially aged images"""
        storage = FileStorage(storage_dir=temp_storage_dir)

        # Create some images
        guid_new = storage.save_image(b"new_image", format="png", group="test")
        guid_old = storage.save_image(b"old_image", format="png", group="test")

        # Artificially age one image
        old_date = (datetime.utcnow() - timedelta(days=31)).isoformat()
        storage.metadata[guid_old]["created_at"] = old_date
        storage._save_metadata()

        # Purge images older than 30 days
        deleted = storage.purge(age_days=30, group="test")

        # Only the old image should be deleted
        assert deleted == 1
        assert storage.exists(guid_new)
        assert not storage.exists(guid_old)

    def test_purge_with_group_filter_and_age(self, temp_storage_dir):
        """Test purging with both group filter and age criteria"""
        storage = FileStorage(storage_dir=temp_storage_dir)

        # Create images in different groups with different ages
        guid_g1_old = storage.save_image(b"group1_old", format="png", group="group1")
        guid_g1_new = storage.save_image(b"group1_new", format="png", group="group1")
        guid_g2_old = storage.save_image(b"group2_old", format="png", group="group2")

        # Age some images
        old_date = (datetime.utcnow() - timedelta(days=31)).isoformat()
        storage.metadata[guid_g1_old]["created_at"] = old_date
        storage.metadata[guid_g2_old]["created_at"] = old_date
        storage._save_metadata()

        # Purge only old group1 images
        deleted = storage.purge(age_days=30, group="group1")

        # Only group1 old image should be deleted
        assert deleted == 1
        assert not storage.exists(guid_g1_old)
        assert storage.exists(guid_g1_new)
        assert storage.exists(guid_g2_old)

    def test_purge_empty_storage(self, temp_storage_dir):
        """Test purging when storage is already empty"""
        storage = FileStorage(storage_dir=temp_storage_dir)

        # Purge empty storage
        deleted = storage.purge(age_days=0)

        assert deleted == 0

    def test_purge_preserves_metadata_file(self, storage_with_images):
        """Test that purge never deletes the metadata.json file"""
        storage, guids = storage_with_images

        metadata_file = storage.storage_dir / "metadata.json"
        assert metadata_file.exists()

        # Purge everything
        storage.purge(age_days=0)

        # Metadata file should still exist
        assert metadata_file.exists()

    def test_purge_cleans_orphaned_metadata(self, temp_storage_dir):
        """Test that purge removes orphaned metadata entries (entries without files)"""
        storage = FileStorage(storage_dir=temp_storage_dir)

        # Create images
        guid1 = storage.save_image(b"image1", format="png", group="test")
        guid2 = storage.save_image(b"image2", format="png", group="test")
        storage.save_image(b"image3", format="png", group="other")

        # Verify initial state
        assert len(storage.metadata) == 3
        assert len(storage.list_images()) == 3

        # Manually delete the files but leave metadata (simulates orphaned metadata)
        (storage.storage_dir / f"{guid1}.png").unlink()
        (storage.storage_dir / f"{guid2}.png").unlink()

        # Verify orphaned state
        assert len(storage.metadata) == 3
        assert len(storage.list_images()) == 1

        # Run purge - should clean up orphaned metadata
        deleted = storage.purge(age_days=0)

        # Should report 3 deletions (2 orphaned metadata + 1 actual file)
        assert deleted == 3
        assert len(storage.metadata) == 0
        assert len(storage.list_images()) == 0

    def test_purge_cleans_orphaned_metadata_with_group_filter(self, temp_storage_dir):
        """Test that purge cleans orphaned metadata only for specified group"""
        storage = FileStorage(storage_dir=temp_storage_dir)

        # Create images in different groups
        guid_g1 = storage.save_image(b"group1", format="png", group="group1")
        guid_g2 = storage.save_image(b"group2", format="png", group="group2")

        # Manually delete only group1 file
        (storage.storage_dir / f"{guid_g1}.png").unlink()

        # Purge only group1
        deleted = storage.purge(age_days=0, group="group1")

        # Should clean up only group1 orphaned metadata
        assert deleted == 1
        assert len(storage.metadata) == 1
        assert guid_g2 in storage.metadata
        assert guid_g1 not in storage.metadata


# ============================================================================
# Concurrent Access Tests
# ============================================================================


class TestStorageConcurrentAccess:
    """Tests for thread safety and concurrent operations"""

    def test_concurrent_saves(self, temp_storage_dir):
        """Test multiple threads saving images simultaneously"""
        storage = FileStorage(storage_dir=temp_storage_dir)
        num_threads = 10
        guids = []
        errors = []

        def save_image(thread_id):
            try:
                test_data = f"image from thread {thread_id}".encode()
                guid = storage.save_image(test_data, format="png", group=f"thread{thread_id}")
                return guid
            except Exception as e:
                errors.append((thread_id, str(e)))
                return None

        # Save images concurrently
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(save_image, i) for i in range(num_threads)]
            for future in as_completed(futures):
                guid = future.result()
                if guid:
                    guids.append(guid)

        # Check for errors
        assert len(errors) == 0, f"Concurrent saves had errors: {errors}"

        # All saves should succeed
        assert len(guids) == num_threads

        # All GUIDs should be unique
        assert len(set(guids)) == num_threads

        # All should be in metadata
        for guid in guids:
            assert guid in storage.metadata

    def test_concurrent_save_and_retrieve(self, temp_storage_dir):
        """Test saving and retrieving images concurrently"""
        storage = FileStorage(storage_dir=temp_storage_dir)

        # Pre-save some images
        saved_guids = []
        for i in range(5):
            test_data = f"pre-saved image {i}".encode()
            guid = storage.save_image(test_data, format="png", group="presaved")
            saved_guids.append((guid, test_data))

        errors = []

        def mixed_operation(op_id):
            """Mix of save and retrieve operations"""
            try:
                if op_id % 2 == 0:
                    # Save operation
                    test_data = f"new image {op_id}".encode()
                    guid = storage.save_image(test_data, format="png", group=f"mixed{op_id}")
                    return ("save", guid)
                else:
                    # Retrieve operation
                    guid, expected_data = saved_guids[op_id % len(saved_guids)]
                    result = storage.get_image(guid, group="presaved")
                    if result:
                        retrieved_data, _ = result
                        assert retrieved_data == expected_data
                    return ("retrieve", guid)
            except Exception as e:
                errors.append((op_id, str(e)))
                return None

        # Run mixed operations concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(mixed_operation, i) for i in range(20)]
            results = [future.result() for future in as_completed(futures)]

        # No errors should occur
        assert len(errors) == 0, f"Concurrent operations had errors: {errors}"
        assert len(results) == 20

    def test_concurrent_purge_and_save(self, temp_storage_dir):
        """Test purging while saving images concurrently"""
        storage = FileStorage(storage_dir=temp_storage_dir)

        # Pre-populate some images
        for i in range(5):
            storage.save_image(f"initial_{i}".encode(), format="png", group="initial")

        errors = []

        def purge_operation():
            try:
                deleted = storage.purge(age_days=0, group="initial")
                return ("purge", deleted)
            except Exception as e:
                errors.append(("purge", str(e)))
                return None

        def save_operation(op_id):
            try:
                test_data = f"new image {op_id}".encode()
                guid = storage.save_image(test_data, format="png", group="new")
                return ("save", guid)
            except Exception as e:
                errors.append((op_id, str(e)))
                return None

        # Run purge and saves concurrently
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = []
            futures.append(executor.submit(purge_operation))
            futures.extend([executor.submit(save_operation, i) for i in range(5)])
            [future.result() for future in as_completed(futures)]

        # No errors should occur
        assert len(errors) == 0, f"Concurrent operations had errors: {errors}"


# ============================================================================
# Metadata Corruption Tests
# ============================================================================


class TestStorageMetadataCorruption:
    """Tests for handling corrupted or missing metadata"""

    def test_corrupted_metadata_json(self, temp_storage_dir):
        """Test recovery when metadata.json contains invalid JSON"""
        # Create metadata file with invalid JSON
        metadata_path = os.path.join(temp_storage_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            f.write("{invalid json here!!!")

        # Initialize storage (should handle corrupted metadata)
        storage = FileStorage(storage_dir=temp_storage_dir)

        # Storage should initialize with empty metadata
        assert storage.metadata == {}

        # Should be able to save new images
        test_data = b"test image after corruption"
        guid = storage.save_image(test_data, format="png", group="test")

        # Verify metadata was rewritten correctly
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        assert guid in metadata

    def test_missing_metadata_json(self, temp_storage_dir):
        """Test initialization when metadata.json doesn't exist"""
        # Initialize storage without metadata file
        storage = FileStorage(storage_dir=temp_storage_dir)

        # Should create new metadata
        test_data = b"test image"
        guid = storage.save_image(test_data, format="png", group="test")

        # Metadata should be created
        metadata_path = os.path.join(temp_storage_dir, "metadata.json")
        assert os.path.exists(metadata_path)

        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        assert guid in metadata

    def test_metadata_with_orphaned_entries(self, temp_storage_dir):
        """Test when metadata references images that don't exist"""
        # Create storage and save an image
        storage = FileStorage(storage_dir=temp_storage_dir)
        test_data = b"test image"
        guid = storage.save_image(test_data, format="png", group="test")

        # Delete the image file but keep metadata
        image_path = os.path.join(temp_storage_dir, f"{guid}.png")
        os.remove(image_path)

        # Try to retrieve (should return None)
        result = storage.get_image(guid, group="test")
        assert result is None

    def test_images_without_metadata_entries(self, temp_storage_dir):
        """Test when image files exist but aren't in metadata"""
        storage = FileStorage(storage_dir=temp_storage_dir)

        # Manually create an image file without metadata
        orphan_guid = "12345678-1234-1234-1234-123456789abc"
        orphan_path = os.path.join(temp_storage_dir, f"{orphan_guid}.png")
        with open(orphan_path, "wb") as f:
            f.write(b"orphan image data")

        # list_images() should not crash - it will list files even without metadata
        images = storage.list_images()

        # Orphan will appear in list (file exists with valid GUID name)
        # but won't have metadata entry
        assert orphan_guid in images
        assert orphan_guid not in storage.metadata

    def test_purge_with_missing_metadata(self, temp_storage_dir):
        """Test purging images that have files but missing metadata"""
        storage = FileStorage(storage_dir=temp_storage_dir)

        # Create an image
        guid = storage.save_image(b"test_image", format="png", group="test")

        # Remove metadata entry (simulate corrupted metadata)
        del storage.metadata[guid]
        storage._save_metadata()

        # Purge should handle missing metadata gracefully (uses file mtime)
        deleted = storage.purge(age_days=0)

        assert deleted == 1

    def test_purge_with_invalid_metadata_timestamps(self, temp_storage_dir):
        """Test purging with corrupted timestamp data in metadata"""
        storage = FileStorage(storage_dir=temp_storage_dir)

        # Create an image
        guid = storage.save_image(b"test_image", format="png", group="test")

        # Corrupt the timestamp
        storage.metadata[guid]["created_at"] = "invalid_date_format"
        storage._save_metadata()

        # Purge should fall back to file modification time
        deleted = storage.purge(age_days=0)

        assert deleted == 1


# ============================================================================
# Storage Failure Tests
# ============================================================================


class TestStorageFailures:
    """Tests for handling storage write failures"""

    def test_storage_write_failure_permission_denied(self, temp_storage_dir):
        """Test handling when storage directory becomes read-only"""
        storage = FileStorage(storage_dir=temp_storage_dir)

        # Save an image successfully first
        test_data = b"fake image data"
        guid = storage.save_image(test_data, format="png", group="test")
        assert guid is not None

        # Make directory read-only
        os.chmod(temp_storage_dir, 0o444)

        try:
            # Try to save another image (should fail)
            with pytest.raises(RuntimeError) as exc_info:
                storage.save_image(test_data, format="png", group="test")

            assert "Failed to save image" in str(exc_info.value) or "Permission denied" in str(
                exc_info.value
            )

        finally:
            # Restore permissions for cleanup
            os.chmod(temp_storage_dir, 0o755)

    def test_storage_metadata_write_failure(self, temp_storage_dir):
        """Test handling when metadata.json cannot be written"""
        storage = FileStorage(storage_dir=temp_storage_dir)

        # Mock the open function to fail on metadata write
        original_open = open

        def mock_open_failure(*args, **kwargs):
            # Allow reading, fail on writing metadata.json
            if len(args) > 0 and "metadata.json" in str(args[0]) and "w" in str(args[1]):
                raise PermissionError("Simulated metadata write failure")
            return original_open(*args, **kwargs)

        with patch("builtins.open", side_effect=mock_open_failure):
            test_data = b"test image"

            # Should raise RuntimeError when metadata cannot be saved
            with pytest.raises(RuntimeError) as exc_info:
                storage.save_image(test_data, format="png", group="test")

            assert "metadata" in str(exc_info.value).lower()

    def test_storage_disk_full_simulation(self, temp_storage_dir):
        """Test handling when disk is full"""
        storage = FileStorage(storage_dir=temp_storage_dir)

        with patch("builtins.open", side_effect=OSError("[Errno 28] No space left on device")):
            test_data = b"test image"

            with pytest.raises((RuntimeError, OSError)):
                storage.save_image(test_data, format="png", group="test")

    def test_storage_retrieve_from_readonly_directory(self, temp_storage_dir):
        """Test that retrieval still works when directory is read-only"""
        storage = FileStorage(storage_dir=temp_storage_dir)

        # Save an image first
        test_data = b"test image"
        guid = storage.save_image(test_data, format="png", group="test")

        # Make file read-only but keep directory accessible
        image_file = os.path.join(temp_storage_dir, f"{guid}.png")
        os.chmod(image_file, 0o444)

        try:
            # Retrieval should still work with read-only file
            result = storage.get_image(guid, group="test")
            assert result is not None
            retrieved_data, format = result
            assert retrieved_data == test_data
            assert format == "png"

        finally:
            # Restore permissions
            os.chmod(image_file, 0o644)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
