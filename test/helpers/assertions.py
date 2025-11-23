"""Custom assertion helpers

Domain-specific assertions for improved test readability and better error messages.
"""

from typing import Any, Dict, List, Optional, Union
import json
from pathlib import Path


def assert_valid_image(
    image_data: bytes, format: str, min_size: int = 100, max_size: Optional[int] = None
) -> None:
    """Assert image data is valid

    Args:
        image_data: Raw image bytes
        format: Expected format (png, jpg, svg, pdf)
        min_size: Minimum expected size in bytes
        max_size: Maximum expected size in bytes

    Raises:
        AssertionError: If image is invalid
    """
    assert image_data, "Image data is empty"
    assert isinstance(image_data, bytes), f"Image data must be bytes, got {type(image_data)}"

    size = len(image_data)
    assert size >= min_size, f"Image too small: {size} bytes (min {min_size})"
    if max_size:
        assert size <= max_size, f"Image too large: {size} bytes (max {max_size})"

    # Format-specific magic number checks
    if format == "png":
        assert image_data[:8] == b"\x89PNG\r\n\x1a\n", "Invalid PNG header"
    elif format in ["jpg", "jpeg"]:
        assert image_data[:2] == b"\xff\xd8", "Invalid JPEG header"
        assert image_data[-2:] == b"\xff\xd9", "Invalid JPEG footer"
    elif format == "svg":
        # SVG is XML text
        try:
            text = image_data.decode("utf-8")
            assert "<svg" in text.lower(), "Missing <svg> tag in SVG"
        except UnicodeDecodeError:
            raise AssertionError("SVG is not valid UTF-8 text")
    elif format == "pdf":
        assert image_data[:4] == b"%PDF", "Invalid PDF header"


def assert_chart_structure(
    chart_data: Dict[str, Any],
    expected_type: Optional[str] = None,
    has_guid: bool = True,
    has_format: bool = True,
) -> None:
    """Assert chart data has expected structure

    Args:
        chart_data: Chart metadata dictionary
        expected_type: Expected chart type
        has_guid: Whether GUID is expected
        has_format: Whether format is expected

    Raises:
        AssertionError: If structure is invalid
    """
    assert isinstance(chart_data, dict), f"Chart data must be dict, got {type(chart_data)}"

    if has_guid:
        assert "guid" in chart_data, "Chart data missing 'guid'"
        assert isinstance(chart_data["guid"], str), "GUID must be string"
        assert len(chart_data["guid"]) > 0, "GUID is empty"

    if has_format:
        assert "format" in chart_data, "Chart data missing 'format'"
        assert chart_data["format"] in [
            "png",
            "jpg",
            "svg",
            "pdf",
        ], f"Invalid format: {chart_data.get('format')}"

    if expected_type:
        assert "type" in chart_data, "Chart data missing 'type'"
        assert (
            chart_data["type"] == expected_type
        ), f"Expected type '{expected_type}', got '{chart_data.get('type')}'"


def assert_storage_state(
    storage,
    expected_count: Optional[int] = None,
    expected_groups: Optional[List[str]] = None,
    group_counts: Optional[Dict[str, int]] = None,
) -> None:
    """Assert storage is in expected state

    Args:
        storage: Storage instance
        expected_count: Expected total number of images
        expected_groups: Expected list of group names
        group_counts: Expected count per group {group: count}

    Raises:
        AssertionError: If storage state is unexpected
    """
    all_images = storage.list_images()

    if expected_count is not None:
        actual_count = len(all_images)
        assert (
            actual_count == expected_count
        ), f"Expected {expected_count} images, found {actual_count}"

    if expected_groups is not None:
        actual_groups = set(img.get("group") for img in all_images if img.get("group"))
        expected_set = set(expected_groups)
        assert (
            actual_groups == expected_set
        ), f"Expected groups {expected_set}, found {actual_groups}"

    if group_counts is not None:
        for group, expected in group_counts.items():
            if group is None:
                actual = len([img for img in all_images if not img.get("group")])
            else:
                actual = len([img for img in all_images if img.get("group") == group])
            assert (
                actual == expected
            ), f"Group '{group}': expected {expected} images, found {actual}"


def assert_metadata_valid(
    metadata: Dict[str, Any],
    required_fields: Optional[List[str]] = None,
    guid: Optional[str] = None,
    format: Optional[str] = None,
    group: Optional[str] = None,
) -> None:
    """Assert metadata dictionary is valid

    Args:
        metadata: Metadata dictionary
        required_fields: List of required field names
        guid: Expected GUID value
        format: Expected format value
        group: Expected group value

    Raises:
        AssertionError: If metadata is invalid
    """
    assert isinstance(metadata, dict), f"Metadata must be dict, got {type(metadata)}"

    # Default required fields
    if required_fields is None:
        required_fields = ["guid", "format", "timestamp"]

    for field in required_fields:
        assert field in metadata, f"Metadata missing required field: {field}"

    # Validate GUID if present
    if "guid" in metadata:
        assert isinstance(metadata["guid"], str), "GUID must be string"
        assert len(metadata["guid"]) > 0, "GUID is empty"
        if guid:
            assert metadata["guid"] == guid, f"Expected GUID '{guid}', got '{metadata['guid']}'"

    # Validate format if present
    if "format" in metadata:
        assert metadata["format"] in [
            "png",
            "jpg",
            "svg",
            "pdf",
        ], f"Invalid format: {metadata['format']}"
        if format:
            assert (
                metadata["format"] == format
            ), f"Expected format '{format}', got '{metadata['format']}'"

    # Validate group if checking
    if group is not None:
        assert (
            metadata.get("group") == group
        ), f"Expected group '{group}', got '{metadata.get('group')}'"

    # Validate timestamp if present
    if "timestamp" in metadata:
        from datetime import datetime

        try:
            # Try to parse ISO format timestamp
            datetime.fromisoformat(metadata["timestamp"].replace("Z", "+00:00"))
        except (ValueError, AttributeError) as e:
            raise AssertionError(f"Invalid timestamp format: {metadata['timestamp']}: {e}")


def assert_error_response(
    response: Union[Dict, Any],
    expected_error: Optional[str] = None,
    error_contains: Optional[str] = None,
) -> None:
    """Assert response is an error with expected message

    Args:
        response: Response dictionary or object
        expected_error: Exact expected error message
        error_contains: String that should be in error message

    Raises:
        AssertionError: If not an error or message doesn't match
    """
    if isinstance(response, dict):
        # MCP-style response
        assert "success" in response, "Response missing 'success' field"
        assert response["success"] is False, "Expected error response, got success"
        assert "error" in response, "Error response missing 'error' field"
        error_msg = response["error"]
    else:
        # HTTP response
        assert response.status_code >= 400, f"Expected error status, got {response.status_code}"
        try:
            error_data = response.json()
            error_msg = error_data.get("error", error_data.get("message", ""))
        except:  # noqa: E722 - intentionally broad
            error_msg = response.text

    if expected_error:
        assert error_msg == expected_error, f"Expected error '{expected_error}', got '{error_msg}'"

    if error_contains:
        assert (
            error_contains in error_msg
        ), f"Expected error to contain '{error_contains}', got '{error_msg}'"


def assert_success_response(
    response: Dict[str, Any], has_data: bool = False, data_fields: Optional[List[str]] = None
) -> None:
    """Assert response indicates success

    Args:
        response: MCP response dictionary
        has_data: Whether data field is expected
        data_fields: Required fields in data dict

    Raises:
        AssertionError: If not a success response
    """
    assert "success" in response, "Response missing 'success' field"
    assert response["success"] is True, f"Expected success, got error: {response.get('error')}"

    if has_data:
        assert "data" in response, "Success response missing 'data' field"
        data = response["data"]
        assert isinstance(data, dict), f"Data must be dict, got {type(data)}"

        if data_fields:
            for field in data_fields:
                assert field in data, f"Data missing required field: {field}"


def assert_list_response(
    response: Union[Dict, List],
    min_count: int = 0,
    max_count: Optional[int] = None,
    all_have_fields: Optional[List[str]] = None,
) -> List[Dict]:
    """Assert response is a list with expected properties

    Args:
        response: Response containing list (dict with 'data' or direct list)
        min_count: Minimum expected items
        max_count: Maximum expected items
        all_have_fields: Fields that all items must have

    Returns:
        The list of items

    Raises:
        AssertionError: If list is invalid
    """
    # Extract list from response
    if isinstance(response, dict):
        if "data" in response:
            items = response["data"]
        elif "items" in response:
            items = response["items"]
        else:
            items = response
    else:
        items = response

    assert isinstance(items, list), f"Expected list, got {type(items)}"

    count = len(items)
    assert count >= min_count, f"Expected at least {min_count} items, got {count}"
    if max_count is not None:
        assert count <= max_count, f"Expected at most {max_count} items, got {count}"

    if all_have_fields:
        for i, item in enumerate(items):
            assert isinstance(item, dict), f"Item {i} is not a dict: {type(item)}"
            for field in all_have_fields:
                assert field in item, f"Item {i} missing field: {field}"

    return items


def assert_file_exists(path: Union[str, Path], is_dir: bool = False) -> None:
    """Assert file or directory exists

    Args:
        path: Path to check
        is_dir: Whether expecting directory (vs file)

    Raises:
        AssertionError: If path doesn't exist or is wrong type
    """
    path = Path(path)
    assert path.exists(), f"Path does not exist: {path}"

    if is_dir:
        assert path.is_dir(), f"Expected directory, got file: {path}"
    else:
        assert path.is_file(), f"Expected file, got directory: {path}"


def assert_json_matches(
    actual: Union[str, Dict], expected: Union[str, Dict], ignore_fields: Optional[List[str]] = None
) -> None:
    """Assert JSON data matches expected (ignoring specified fields)

    Args:
        actual: Actual JSON (string or dict)
        expected: Expected JSON (string or dict)
        ignore_fields: Fields to ignore in comparison

    Raises:
        AssertionError: If JSON doesn't match
    """
    # Parse strings to dicts
    if isinstance(actual, str):
        actual = json.loads(actual)
    if isinstance(expected, str):
        expected = json.loads(expected)

    # Remove ignored fields
    if ignore_fields:
        actual = {k: v for k, v in actual.items() if k not in ignore_fields}  # type: ignore[union-attr]
        expected = {k: v for k, v in expected.items() if k not in ignore_fields}  # type: ignore[union-attr]

    assert actual == expected, f"JSON mismatch:\nActual: {actual}\nExpected: {expected}"
