"""Tests for multi-dataset rendering via web API"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.logger import ConsoleLogger
from app.web_server import GraphWebServer
from app.auth import TokenInfo, verify_token
from datetime import datetime, timedelta
import logging


def mock_verify_token():
    """Mock token verification for testing without authentication"""
    return TokenInfo(
        token="mock-token",
        group="test-group",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        issued_at=datetime.utcnow(),
    )


@pytest.fixture
def server():
    """Create a GraphWebServer instance"""
    return GraphWebServer(jwt_secret="test-secret-for-unit-tests")


@pytest.fixture
def app(server):
    """Get the FastAPI app from the server with auth dependency overridden"""
    # Override the verify_token dependency to bypass authentication in tests
    server.app.dependency_overrides[verify_token] = mock_verify_token
    return server.app


@pytest.mark.asyncio
async def test_render_two_datasets_web(app):
    """Test rendering two datasets via web API"""
    logger = ConsoleLogger(name="web_multi_dataset_test", level=logging.INFO)
    logger.info("Testing web API with two datasets")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/render",
            json={
                "title": "Two Dataset Web Test",
                "x": [1, 2, 3, 4, 5],
                "y1": [10, 20, 15, 25, 30],
                "y2": [8, 18, 13, 23, 28],
                "label1": "Series A",
                "label2": "Series B",
                "color1": "red",
                "color2": "blue",
                "type": "line",
                "return_base64": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "image" in data
        assert len(data["image"]) > 0


@pytest.mark.asyncio
async def test_render_three_datasets_bar_web(app):
    """Test rendering three datasets as grouped bars via web API"""
    logger = ConsoleLogger(name="web_multi_dataset_test", level=logging.INFO)
    logger.info("Testing web API with three datasets (bar chart)")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/render",
            json={
                "title": "Three Dataset Bar Chart",
                "y1": [100, 120, 110, 130],
                "y2": [90, 100, 95, 110],
                "y3": [80, 95, 85, 100],
                "label1": "Product A",
                "label2": "Product B",
                "label3": "Product C",
                "type": "bar",
                "return_base64": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "image" in data


@pytest.mark.asyncio
async def test_render_five_datasets_web(app):
    """Test rendering maximum five datasets via web API"""
    logger = ConsoleLogger(name="web_multi_dataset_test", level=logging.INFO)
    logger.info("Testing web API with five datasets")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/render",
            json={
                "title": "Five Dataset Test",
                "x": [1, 2, 3, 4, 5],
                "y1": [20, 22, 21, 23, 25],
                "y2": [18, 20, 19, 21, 23],
                "y3": [22, 24, 23, 25, 27],
                "y4": [19, 21, 20, 22, 24],
                "y5": [21, 23, 22, 24, 26],
                "label1": "Station 1",
                "label2": "Station 2",
                "label3": "Station 3",
                "label4": "Station 4",
                "label5": "Station 5",
                "type": "line",
                "return_base64": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "image" in data


@pytest.mark.asyncio
async def test_render_without_x_axis_web(app):
    """Test rendering with auto-generated X-axis via web API"""
    logger = ConsoleLogger(name="web_multi_dataset_test", level=logging.INFO)
    logger.info("Testing web API without x-axis (auto-indexed)")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/render",
            json={
                "title": "Auto X-axis Test",
                "y1": [100, 150, 120, 180],
                "y2": [80, 120, 100, 150],
                "label1": "Online",
                "label2": "In-store",
                "type": "scatter",
                "return_base64": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "image" in data


@pytest.mark.asyncio
async def test_render_scatter_multi_dataset_web(app):
    """Test rendering scatter plot with multiple datasets via web API"""
    logger = ConsoleLogger(name="web_multi_dataset_test", level=logging.INFO)
    logger.info("Testing web API scatter plot with multiple datasets")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/render",
            json={
                "title": "Multi-Dataset Scatter",
                "x": [1, 2, 3, 4, 5],
                "y1": [10, 20, 15, 25, 30],
                "y2": [8, 18, 13, 23, 28],
                "label1": "Group A",
                "label2": "Group B",
                "type": "scatter",
                "marker_size": 50,
                "return_base64": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "image" in data


@pytest.mark.asyncio
async def test_render_without_labels_web(app):
    """Test rendering multiple datasets without labels via web API"""
    logger = ConsoleLogger(name="web_multi_dataset_test", level=logging.INFO)
    logger.info("Testing web API without labels")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/render",
            json={
                "title": "No Labels",
                "x": [1, 2, 3, 4, 5],
                "y1": [10, 20, 15, 25, 30],
                "y2": [8, 18, 13, 23, 28],
                "type": "line",
                "return_base64": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "image" in data


@pytest.mark.asyncio
async def test_render_with_axis_controls_web(app):
    """Test multi-dataset rendering with axis controls via web API"""
    logger = ConsoleLogger(name="web_multi_dataset_test", level=logging.INFO)
    logger.info("Testing web API with multi-dataset and axis controls")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/render",
            json={
                "title": "Multi-Dataset with Axis Controls",
                "x": [1, 2, 3, 4, 5, 6],
                "y1": [20, 25, 22, 28, 24, 30],
                "y2": [18, 23, 20, 26, 22, 28],
                "label1": "Forecast",
                "label2": "Actual",
                "type": "line",
                "xmin": 0,
                "xmax": 7,
                "ymin": 15,
                "ymax": 35,
                "return_base64": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "image" in data


@pytest.mark.asyncio
async def test_render_backward_compatible_web(app):
    """Test backward compatibility (old 'y' parameter) via web API"""
    logger = ConsoleLogger(name="web_multi_dataset_test", level=logging.INFO)
    logger.info("Testing web API with backward compatible parameters")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/render",
            json={
                "title": "Backward Compatible Test",
                "x": [1, 2, 3, 4, 5],
                "y": [10, 20, 15, 25, 30],  # Old parameter
                "color": "green",  # Old parameter
                "type": "line",
                "return_base64": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "image" in data


@pytest.mark.asyncio
async def test_render_different_formats_web(app):
    """Test multi-dataset rendering in different formats via web API"""
    logger = ConsoleLogger(name="web_multi_dataset_test", level=logging.INFO)
    logger.info("Testing web API with different formats")

    formats = ["png", "jpg", "svg"]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for fmt in formats:
            response = await client.post(
                "/render",
                json={
                    "title": f"Multi-Dataset {fmt.upper()}",
                    "y1": [10, 20, 15],
                    "y2": [8, 18, 13],
                    "type": "line",
                    "format": fmt,
                    "return_base64": True,
                },
            )

            assert response.status_code == 200, f"Failed for format {fmt}"


@pytest.mark.asyncio
async def test_render_different_themes_web(app):
    """Test multi-dataset rendering with different themes via web API"""
    logger = ConsoleLogger(name="web_multi_dataset_test", level=logging.INFO)
    logger.info("Testing web API with different themes")

    themes = ["light", "dark", "bizlight", "bizdark"]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for theme in themes:
            response = await client.post(
                "/render",
                json={
                    "title": f"Multi-Dataset {theme} Theme",
                    "y1": [10, 20, 15],
                    "y2": [8, 18, 13],
                    "type": "line",
                    "theme": theme,
                    "return_base64": True,
                },
            )

            assert response.status_code == 200, f"Failed for theme {theme}"


@pytest.mark.asyncio
async def test_validation_mismatched_lengths_web(app):
    """Test validation error for mismatched dataset lengths via web API"""
    logger = ConsoleLogger(name="web_multi_dataset_test", level=logging.INFO)
    logger.info("Testing web API validation with mismatched lengths")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/render",
            json={
                "title": "Mismatched Lengths",
                "y1": [10, 20, 15],
                "y2": [8, 18],  # Different length
                "type": "line",
            },
        )

        assert response.status_code == 400  # Validation error
        data = response.json()
        assert "error" in data or "detail" in data


@pytest.mark.asyncio
async def test_validation_x_length_mismatch_web(app):
    """Test validation error for X-axis length mismatch via web API"""
    logger = ConsoleLogger(name="web_multi_dataset_test", level=logging.INFO)
    logger.info("Testing web API validation with X length mismatch")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/render",
            json={
                "title": "X Length Mismatch",
                "x": [1, 2, 3, 4, 5],  # 5 points
                "y1": [10, 20, 15],  # 3 points
                "type": "line",
            },
        )

        assert response.status_code == 400  # Validation error
        data = response.json()
        assert "error" in data or "detail" in data


@pytest.mark.asyncio
async def test_render_direct_image_multi_dataset_web(app):
    """Test rendering multiple datasets as direct image bytes via web API"""
    logger = ConsoleLogger(name="web_multi_dataset_test", level=logging.INFO)
    logger.info("Testing web API with direct image response")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/render",
            json={
                "title": "Multi-Dataset Direct Image",
                "y1": [10, 20, 15],
                "y2": [8, 18, 13],
                "type": "line",
                "return_base64": False,  # Direct image bytes
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/")
        assert len(response.content) > 0
