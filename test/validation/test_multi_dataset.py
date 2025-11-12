"""Tests for multi-dataset rendering functionality"""

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


def test_render_two_datasets_line(renderer):
    """Test rendering line chart with two datasets"""
    params = GraphParams(
        title="Two Dataset Line Chart",
        x=[1, 2, 3, 4, 5],
        y1=[10, 20, 15, 25, 30],
        y2=[8, 18, 13, 23, 28],
        label1="Series A",
        label2="Series B",
        color1="red",
        color2="blue",
        type="line",
        format="png",
    )

    result = renderer.render(params)
    assert result is not None
    assert isinstance(result, str)  # base64 encoded

    # Verify it's a valid image
    image_data = base64.b64decode(result)
    img = Image.open(io.BytesIO(image_data))
    assert img.format == "PNG"


def test_render_three_datasets_line(renderer):
    """Test rendering line chart with three datasets"""
    params = GraphParams(
        title="Three Dataset Line Chart",
        x=[1, 2, 3, 4, 5],
        y1=[10, 20, 15, 25, 30],
        y2=[8, 18, 13, 23, 28],
        y3=[12, 22, 17, 27, 32],
        label1="Series A",
        label2="Series B",
        label3="Series C",
        color1="red",
        color2="blue",
        color3="green",
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


def test_render_five_datasets_line(renderer):
    """Test rendering line chart with maximum five datasets"""
    params = GraphParams(
        title="Five Dataset Line Chart",
        x=[1, 2, 3, 4, 5, 6, 7],
        y1=[20, 22, 21, 23, 25, 24, 26],
        y2=[18, 20, 19, 21, 23, 22, 24],
        y3=[22, 24, 23, 25, 27, 26, 28],
        y4=[19, 21, 20, 22, 24, 23, 25],
        y5=[21, 23, 22, 24, 26, 25, 27],
        label1="Station 1",
        label2="Station 2",
        label3="Station 3",
        label4="Station 4",
        label5="Station 5",
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


def test_render_two_datasets_scatter(renderer):
    """Test rendering scatter plot with two datasets"""
    params = GraphParams(
        title="Two Dataset Scatter Plot",
        x=[1, 2, 3, 4, 5],
        y1=[10, 20, 15, 25, 30],
        y2=[8, 18, 13, 23, 28],
        label1="Group A",
        label2="Group B",
        color1="purple",
        color2="orange",
        type="scatter",
        marker_size=50,
        format="png",
    )

    result = renderer.render(params)
    assert result is not None
    assert isinstance(result, str)

    # Verify it's a valid image
    image_data = base64.b64decode(result)
    img = Image.open(io.BytesIO(image_data))
    assert img.format == "PNG"


def test_render_three_datasets_bar(renderer):
    """Test rendering bar chart with three datasets (grouped bars)"""
    params = GraphParams(
        title="Three Dataset Bar Chart",
        y1=[100, 120, 110, 130],
        y2=[90, 100, 95, 110],
        y3=[80, 95, 85, 100],
        label1="Product A",
        label2="Product B",
        label3="Product C",
        color1="#FF5733",
        color2="#33FF57",
        color3="#3357FF",
        type="bar",
        format="png",
    )

    result = renderer.render(params)
    assert result is not None
    assert isinstance(result, str)

    # Verify it's a valid image
    image_data = base64.b64decode(result)
    img = Image.open(io.BytesIO(image_data))
    assert img.format == "PNG"


def test_render_without_x_axis(renderer):
    """Test rendering with auto-generated X-axis (no x parameter)"""
    params = GraphParams(
        title="Auto-indexed X-axis",
        y1=[100, 150, 120, 180, 160],
        y2=[80, 120, 100, 150, 130],
        label1="Online",
        label2="In-store",
        color1="purple",
        color2="orange",
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


def test_render_without_labels(renderer):
    """Test rendering multiple datasets without labels (no legend)"""
    params = GraphParams(
        title="No Labels",
        x=[1, 2, 3, 4, 5],
        y1=[10, 20, 15, 25, 30],
        y2=[8, 18, 13, 23, 28],
        color1="red",
        color2="blue",
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


def test_render_without_colors(renderer):
    """Test rendering multiple datasets without custom colors (theme defaults)"""
    params = GraphParams(
        title="Default Colors",
        x=[1, 2, 3, 4, 5],
        y1=[10, 20, 15, 25, 30],
        y2=[8, 18, 13, 23, 28],
        label1="Series A",
        label2="Series B",
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


def test_render_with_axis_controls(renderer):
    """Test multi-dataset rendering with axis controls"""
    params = GraphParams(
        title="Multi-Dataset with Axis Controls",
        x=[1, 2, 3, 4, 5, 6],
        y1=[20, 25, 22, 28, 24, 30],
        y2=[18, 23, 20, 26, 22, 28],
        label1="Forecast",
        label2="Actual",
        color1="red",
        color2="blue",
        type="line",
        xmin=0,
        xmax=7,
        ymin=15,
        ymax=35,
        x_major_ticks=[0, 2, 4, 6],
        y_major_ticks=[15, 20, 25, 30, 35],
        format="png",
    )

    result = renderer.render(params)
    assert result is not None
    assert isinstance(result, str)

    # Verify it's a valid image
    image_data = base64.b64decode(result)
    img = Image.open(io.BytesIO(image_data))
    assert img.format == "PNG"


def test_render_different_formats(renderer):
    """Test multi-dataset rendering in different formats"""
    formats = ["png", "jpg", "svg", "pdf"]

    for fmt in formats:
        params = GraphParams(
            title=f"Multi-Dataset {fmt.upper()}",
            x=[1, 2, 3],
            y1=[10, 20, 15],
            y2=[8, 18, 13],
            label1="A",
            label2="B",
            type="line",
            format=fmt,
        )

        result = renderer.render(params)
        assert result is not None
        assert isinstance(result, str)

        # Verify it's valid base64 (except PDF which might be binary)
        if fmt != "pdf":
            image_data = base64.b64decode(result)
            assert len(image_data) > 0


def test_render_different_themes(renderer):
    """Test multi-dataset rendering with different themes"""
    themes = ["light", "dark", "bizlight", "bizdark"]

    for theme in themes:
        params = GraphParams(
            title=f"Multi-Dataset {theme} Theme",
            x=[1, 2, 3],
            y1=[10, 20, 15],
            y2=[8, 18, 13],
            label1="A",
            label2="B",
            type="line",
            theme=theme,
            format="png",
        )

        result = renderer.render(params)
        assert result is not None
        assert isinstance(result, str)

        # Verify it's a valid image
        image_data = base64.b64decode(result)
        img = Image.open(io.BytesIO(image_data))
        assert img.format == "PNG"


def test_backward_compatible_y_parameter(renderer):
    """Test backward compatibility - old 'y' parameter maps to y1"""
    params = GraphParams(
        title="Backward Compatible",
        x=[1, 2, 3, 4, 5],
        y=[10, 20, 15, 25, 30],  # Old parameter
        color="green",  # Old parameter
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

    # Verify backward compatibility mapping worked
    assert params.y1 == [10, 20, 15, 25, 30]
    assert params.color1 == "green"


def test_partial_dataset_labels(renderer):
    """Test rendering with only some datasets having labels"""
    params = GraphParams(
        title="Partial Labels",
        x=[1, 2, 3, 4, 5],
        y1=[10, 20, 15, 25, 30],
        y2=[8, 18, 13, 23, 28],
        y3=[12, 22, 17, 27, 32],
        label1="Series A",
        # No label2
        label3="Series C",
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


def test_partial_dataset_colors(renderer):
    """Test rendering with only some datasets having custom colors"""
    params = GraphParams(
        title="Partial Colors",
        x=[1, 2, 3, 4, 5],
        y1=[10, 20, 15, 25, 30],
        y2=[8, 18, 13, 23, 28],
        y3=[12, 22, 17, 27, 32],
        color1="red",
        # No color2 (will use theme default)
        color3="green",
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
