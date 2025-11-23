"""Test data factories

Builder pattern implementations for creating test data with sensible defaults.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import uuid


class ChartRequestBuilder:
    """Builder for chart request data

    Example:
        request = (ChartRequestBuilder()
            .with_type("line")
            .with_data([1, 2, 3, 4, 5])
            .with_theme("dark")
            .build())
    """

    def __init__(self):
        self._data: Dict[str, Any] = {
            "type": "line",
            "data": [1, 2, 3, 4, 5],
            "format": "png",
        }

    def with_type(self, chart_type: str) -> "ChartRequestBuilder":
        """Set chart type (line, scatter, bar)"""
        self._data["type"] = chart_type
        return self

    def with_data(self, data: Union[List, Dict]) -> "ChartRequestBuilder":
        """Set chart data (list for single dataset, dict for multi-dataset)"""
        self._data["data"] = data
        return self

    def with_format(self, format: str) -> "ChartRequestBuilder":
        """Set output format (png, jpg, svg, pdf)"""
        self._data["format"] = format
        return self

    def with_theme(self, theme: str) -> "ChartRequestBuilder":
        """Set theme (light, dark, bizlight, bizdark)"""
        self._data["theme"] = theme
        return self

    def with_title(self, title: str) -> "ChartRequestBuilder":
        """Set chart title"""
        self._data["title"] = title
        return self

    def with_xlabel(self, xlabel: str) -> "ChartRequestBuilder":
        """Set x-axis label"""
        self._data["xlabel"] = xlabel
        return self

    def with_ylabel(self, ylabel: str) -> "ChartRequestBuilder":
        """Set y-axis label"""
        self._data["ylabel"] = ylabel
        return self

    def with_group(self, group: str) -> "ChartRequestBuilder":
        """Set storage group"""
        self._data["group"] = group
        return self

    def with_guid(self, guid: str) -> "ChartRequestBuilder":
        """Set specific GUID"""
        self._data["guid"] = guid
        return self

    def with_axis_controls(self, **controls) -> "ChartRequestBuilder":
        """Set axis control parameters (xlim, ylim, xscale, yscale)"""
        self._data.update(controls)
        return self

    def with_multi_dataset(self, datasets: List[Dict]) -> "ChartRequestBuilder":
        """Set multi-dataset configuration

        Args:
            datasets: List of dicts with 'data', 'label', optional 'color'
        """
        self._data["data"] = {"datasets": datasets}
        return self

    def build(self) -> Dict[str, Any]:
        """Build the request dictionary"""
        return self._data.copy()


class DatasetBuilder:
    """Builder for dataset configurations

    Example:
        dataset = (DatasetBuilder()
            .with_data([1, 2, 3])
            .with_label("Series A")
            .with_color("#FF0000")
            .build())
    """

    def __init__(self):
        self._data: Dict[str, Any] = {
            "data": [1, 2, 3, 4, 5],
        }

    def with_data(self, data: List) -> "DatasetBuilder":
        """Set dataset values"""
        self._data["data"] = data
        return self

    def with_label(self, label: str) -> "DatasetBuilder":
        """Set dataset label"""
        self._data["label"] = label
        return self

    def with_color(self, color: str) -> "DatasetBuilder":
        """Set dataset color"""
        self._data["color"] = color
        return self

    def build(self) -> Dict[str, Any]:
        """Build the dataset dictionary"""
        return self._data.copy()


class ThemeBuilder:
    """Builder for theme configurations

    Example:
        theme = (ThemeBuilder()
            .with_colors(primary="#FF0000", background="#FFFFFF")
            .with_fonts(title=14, labels=10)
            .build())
    """

    def __init__(self, base_theme: Optional[str] = None):
        self._data: Dict[str, Any] = {
            "base": base_theme or "light",
            "colors": {},
            "fonts": {},
        }

    def with_colors(self, **colors) -> "ThemeBuilder":
        """Set theme colors (primary, secondary, background, etc.)"""
        self._data["colors"].update(colors)
        return self

    def with_fonts(self, **fonts) -> "ThemeBuilder":
        """Set font sizes (title, labels, legend, etc.)"""
        self._data["fonts"].update(fonts)
        return self

    def build(self) -> Dict[str, Any]:
        """Build the theme dictionary"""
        return self._data.copy()


class AuthTokenBuilder:
    """Builder for authentication tokens

    Example:
        token = (AuthTokenBuilder()
            .with_user("test_user")
            .with_expiry(hours=24)
            .build())
    """

    def __init__(self):
        self._data: Dict[str, Any] = {
            "user": "test_user",
            "exp": None,
            "iat": datetime.utcnow(),
        }

    def with_user(self, username: str) -> "AuthTokenBuilder":
        """Set username"""
        self._data["user"] = username
        return self

    def with_expiry(self, hours: int = 24) -> "AuthTokenBuilder":
        """Set token expiry (hours from now)"""
        self._data["exp"] = datetime.utcnow() + timedelta(hours=hours)
        return self

    def with_issued_at(self, issued_at: datetime) -> "AuthTokenBuilder":
        """Set token issued timestamp"""
        self._data["iat"] = issued_at
        return self

    def expired(self, hours_ago: int = 1) -> "AuthTokenBuilder":
        """Make token expired by hours_ago"""
        now = datetime.utcnow()
        self._data["iat"] = now - timedelta(hours=hours_ago + 1)
        self._data["exp"] = now - timedelta(hours=hours_ago)
        return self

    def build(self) -> Dict[str, Any]:
        """Build the token payload dictionary"""
        return self._data.copy()


class StorageFixtureBuilder:
    """Builder for storage test fixtures with pre-populated data

    Example:
        storage = (StorageFixtureBuilder(storage_instance)
            .with_group("group1", count=3, format="png")
            .with_group("group2", count=2, format="svg")
            .with_orphan_blobs(count=1)
            .build())
    """

    def __init__(self, storage):
        self.storage = storage
        self._guids: Dict[str, List[str]] = {}
        self._orphans: List[str] = []

    def with_group(
        self, group: str, count: int = 1, format: str = "png"
    ) -> "StorageFixtureBuilder":
        """Add images to a specific group"""
        self._guids[group] = []
        for i in range(count):
            data = f"{group}_image_{i}".encode()
            guid = self.storage.save_image(data, format=format, group=group)
            self._guids[group].append(guid)
        return self

    def with_ungrouped(self, count: int = 1, format: str = "png") -> "StorageFixtureBuilder":
        """Add images without a group"""
        if None not in self._guids:
            self._guids[None] = []  # type: ignore[index]
        for i in range(count):
            data = f"ungrouped_image_{i}".encode()
            guid = self.storage.save_image(data, format=format, group=None)
            self._guids[None].append(guid)  # type: ignore[index]
        return self

    def with_orphan_blobs(self, count: int = 1) -> "StorageFixtureBuilder":
        """Add orphaned blobs (files without metadata)"""
        # This would need storage implementation support
        # Placeholder for now
        return self

    def build(self) -> Dict[str, Any]:
        """Build and return storage state

        Returns:
            Dict with 'guids' (by group) and 'storage' instance
        """
        return {
            "storage": self.storage,
            "guids": self._guids,
            "orphans": self._orphans,
        }


def make_test_image_data(size: int = 100, prefix: str = "test") -> bytes:
    """Create deterministic test image data

    Args:
        size: Number of bytes
        prefix: Prefix for content

    Returns:
        Bytes of test data
    """
    content = f"{prefix}_" * (size // (len(prefix) + 1))
    return content[:size].encode()


def make_test_metadata(
    guid: Optional[str] = None,
    format: str = "png",
    group: Optional[str] = None,
    timestamp: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Create test metadata dictionary

    Args:
        guid: Image GUID (generated if None)
        format: Image format
        group: Storage group
        timestamp: Creation timestamp (now if None)

    Returns:
        Metadata dictionary
    """
    return {
        "guid": guid or str(uuid.uuid4()),
        "format": format,
        "group": group,
        "timestamp": (timestamp or datetime.utcnow()).isoformat(),
        "size": 1024,
    }
