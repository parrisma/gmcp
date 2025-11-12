"""Tests for axis limits and tick controls"""

import pytest
import base64
import io
from PIL import Image

from app.graph_params import GraphParams
from app.render import GraphRenderer


@pytest.fixture
def renderer():
    """Create a graph renderer"""
    return GraphRenderer()


def test_render_with_axis_limits(renderer):
    """Test rendering with custom axis limits"""
    params = GraphParams(
        title="Chart with Axis Limits",
        x=[1, 2, 3, 4, 5],
        y1=[2, 4, 6, 8, 10],
        type="line",
        format="png",
        xmin=0,
        xmax=6,
        ymin=0,
        ymax=12,
    )

    result = renderer.render(params)
    assert result is not None
    assert isinstance(result, str)  # base64 encoded

    # Verify it's a valid image
    image_data = base64.b64decode(result)
    img = Image.open(io.BytesIO(image_data))
    assert img.format == "PNG"


def test_render_with_partial_axis_limits(renderer):
    """Test rendering with only some axis limits set"""
    params = GraphParams(
        title="Chart with Partial Limits",
        x=[1, 2, 3, 4, 5],
        y1=[2, 4, 6, 8, 10],
        type="line",
        format="png",
        xmin=0,  # Only set minimum
        ymax=15,  # Only set maximum
    )

    result = renderer.render(params)
    assert result is not None
    assert isinstance(result, str)


def test_render_with_major_ticks(renderer):
    """Test rendering with custom major tick positions"""
    params = GraphParams(
        title="Chart with Major Ticks",
        x=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        y1=[2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        type="line",
        format="png",
        x_major_ticks=[2, 4, 6, 8, 10],
        y_major_ticks=[0, 5, 10, 15, 20],
    )

    result = renderer.render(params)
    assert result is not None
    assert isinstance(result, str)

    # Verify it's a valid image
    image_data = base64.b64decode(result)
    img = Image.open(io.BytesIO(image_data))
    assert img.format == "PNG"


def test_render_with_minor_ticks(renderer):
    """Test rendering with custom minor tick positions"""
    params = GraphParams(
        title="Chart with Minor Ticks",
        x=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        y1=[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        type="line",
        format="png",
        x_major_ticks=[0, 5, 10],
        x_minor_ticks=[1, 2, 3, 4, 6, 7, 8, 9],
        y_major_ticks=[0, 10, 20],
        y_minor_ticks=[2, 4, 6, 8, 12, 14, 16, 18],
    )

    result = renderer.render(params)
    assert result is not None
    assert isinstance(result, str)

    # Verify it's a valid image
    image_data = base64.b64decode(result)
    img = Image.open(io.BytesIO(image_data))
    assert img.format == "PNG"


def test_render_with_all_axis_controls(renderer):
    """Test rendering with all axis controls combined"""
    params = GraphParams(
        title="Chart with All Controls",
        x=[1, 2, 3, 4, 5, 6, 7, 8],
        y1=[10, 20, 15, 25, 30, 22, 28, 35],
        type="scatter",
        format="png",
        xmin=0,
        xmax=9,
        ymin=5,
        ymax=40,
        x_major_ticks=[0, 2, 4, 6, 8],
        y_major_ticks=[10, 20, 30, 40],
        x_minor_ticks=[1, 3, 5, 7],
        y_minor_ticks=[15, 25, 35],
    )

    result = renderer.render(params)
    assert result is not None
    assert isinstance(result, str)

    # Verify it's a valid image
    image_data = base64.b64decode(result)
    img = Image.open(io.BytesIO(image_data))
    assert img.format == "PNG"


def test_render_bar_chart_with_axis_limits(renderer):
    """Test that axis controls work with bar charts"""
    params = GraphParams(
        title="Bar Chart with Limits",
        x=[1, 2, 3, 4, 5],
        y1=[5, 8, 3, 7, 4],
        type="bar",
        format="png",
        ymin=0,
        ymax=10,
    )

    result = renderer.render(params)
    assert result is not None
    assert isinstance(result, str)

    # Verify it's a valid image
    image_data = base64.b64decode(result)
    img = Image.open(io.BytesIO(image_data))
    assert img.format == "PNG"


def test_render_with_negative_limits(renderer):
    """Test rendering with negative axis limits"""
    params = GraphParams(
        title="Chart with Negative Limits",
        x=[-5, -3, -1, 1, 3, 5],
        y1=[-10, -5, 0, 5, 10, 15],
        type="line",
        format="png",
        xmin=-6,
        xmax=6,
        ymin=-15,
        ymax=20,
    )

    result = renderer.render(params)
    assert result is not None
    assert isinstance(result, str)


def test_render_without_axis_controls(renderer):
    """Test that rendering still works without any axis controls (backward compatibility)"""
    params = GraphParams(
        title="Chart without Controls",
        x=[1, 2, 3, 4, 5],
        y1=[2, 4, 6, 8, 10],
        type="line",
        format="png",
    )

    result = renderer.render(params)
    assert result is not None
    assert isinstance(result, str)

    # Verify it's a valid image
    image_data = base64.b64decode(result)
    img = Image.open(io.BytesIO(image_data))
    assert img.format == "PNG"
