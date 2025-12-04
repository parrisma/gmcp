#!/usr/bin/env python3
"""
Multi-Dataset Graph Examples - Web API

Demonstrates how to plot multiple datasets on a single graph using the gofr-plot web API.
"""

import requests
import base64
import os

# Configuration
API_URL = "http://localhost:8000/render"
TOKEN = os.environ.get("GOFR_PLOT_JWT_TOKEN", "your-jwt-token-here")


def save_image(base64_data: str, filename: str):
    """Save base64-encoded image to file"""
    image_data = base64.b64decode(base64_data)
    with open(filename, "wb") as f:
        f.write(image_data)
    print(f"Saved: {filename}")


def example_two_datasets():
    """Plot two datasets with labels and colors"""
    print("\n1. Two Datasets - Temperature Comparison")

    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "title": "Temperature Comparison",
            "x": [1, 2, 3, 4, 5, 6, 7],
            "y1": [20, 22, 21, 23, 25, 24, 26],
            "y2": [18, 20, 19, 21, 23, 22, 24],
            "label1": "City A",
            "label2": "City B",
            "color1": "red",
            "color2": "blue",
            "xlabel": "Day",
            "ylabel": "Temperature (°C)",
            "type": "line",
            "format": "png",
        },
    )

    if response.status_code == 200:
        data = response.json()
        save_image(data["image"], "example_two_datasets.png")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def example_three_datasets_bar():
    """Plot three datasets as grouped bars"""
    print("\n2. Three Datasets - Grouped Bar Chart")

    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "title": "Quarterly Sales by Product",
            "y1": [100, 120, 110, 130],
            "y2": [90, 100, 95, 110],
            "y3": [80, 95, 85, 100],
            "label1": "Product A",
            "label2": "Product B",
            "label3": "Product C",
            "color1": "#FF5733",
            "color2": "#33FF57",
            "color3": "#3357FF",
            "xlabel": "Quarter",
            "ylabel": "Sales ($1000s)",
            "type": "bar",
            "format": "png",
        },
    )

    if response.status_code == 200:
        data = response.json()
        save_image(data["image"], "example_three_datasets_bar.png")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def example_five_datasets():
    """Plot maximum five datasets"""
    print("\n3. Five Datasets - Weather Stations")

    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "title": "Temperature from 5 Weather Stations",
            "x": [1, 2, 3, 4, 5, 6, 7],
            "y1": [20, 22, 21, 23, 25, 24, 26],
            "y2": [18, 20, 19, 21, 23, 22, 24],
            "y3": [22, 24, 23, 25, 27, 26, 28],
            "y4": [19, 21, 20, 22, 24, 23, 25],
            "y5": [21, 23, 22, 24, 26, 25, 27],
            "label1": "Station 1",
            "label2": "Station 2",
            "label3": "Station 3",
            "label4": "Station 4",
            "label5": "Station 5",
            "xlabel": "Day",
            "ylabel": "Temperature (°C)",
            "type": "line",
            "line_width": 1.5,
            "format": "png",
        },
    )

    if response.status_code == 200:
        data = response.json()
        save_image(data["image"], "example_five_datasets.png")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def example_no_x_axis():
    """Plot datasets without specifying X-axis (auto-indexed)"""
    print("\n4. Auto-indexed X-axis")

    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "title": "Product Sales (Auto-indexed)",
            "y1": [100, 150, 120, 180, 160],
            "y2": [80, 120, 100, 150, 130],
            "label1": "Online",
            "label2": "In-store",
            "color1": "purple",
            "color2": "orange",
            "ylabel": "Sales ($1000s)",
            "type": "scatter",
            "marker_size": 80,
            "format": "png",
        },
    )

    if response.status_code == 200:
        data = response.json()
        save_image(data["image"], "example_no_x_axis.png")
        print("Note: X-axis automatically set to [0, 1, 2, 3, 4]")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def example_with_axis_controls():
    """Multi-dataset with custom axis limits and ticks"""
    print("\n5. Multi-Dataset with Axis Controls")

    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "title": "Temperature with Custom Axes",
            "x": [1, 2, 3, 4, 5, 6],
            "y1": [20, 25, 22, 28, 24, 30],
            "y2": [18, 23, 20, 26, 22, 28],
            "label1": "Forecast",
            "label2": "Actual",
            "color1": "red",
            "color2": "blue",
            "xlabel": "Hour",
            "ylabel": "Temperature (°C)",
            "type": "line",
            "xmin": 0,
            "xmax": 7,
            "ymin": 15,
            "ymax": 35,
            "x_major_ticks": [0, 2, 4, 6],
            "y_major_ticks": [15, 20, 25, 30, 35],
            "format": "png",
        },
    )

    if response.status_code == 200:
        data = response.json()
        save_image(data["image"], "example_with_axis_controls.png")
    else:
        print(f"Error: {response.status_code} - {response.text}")


def example_backward_compatible():
    """Backward compatible - using old 'y' and 'color' parameters"""
    print("\n6. Backward Compatible (old API style)")

    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "title": "Sales Data (Old API)",
            "x": [1, 2, 3, 4, 5],
            "y": [10, 25, 18, 30, 42],  # Maps to y1
            "color": "green",  # Maps to color1
            "type": "line",
            "format": "png",
        },
    )

    if response.status_code == 200:
        data = response.json()
        save_image(data["image"], "example_backward_compatible.png")
        print("Note: 'y' mapped to 'y1', 'color' mapped to 'color1'")
    else:
        print(f"Error: {response.status_code} - {response.text}")


if __name__ == "__main__":
    print("=" * 70)
    print("Multi-Dataset Graph Examples - Web API")
    print("=" * 70)
    print("\nMake sure:")
    print("1. Web server is running: python -m app.main_web")
    print("2. GOFR_PLOT_JWT_TOKEN environment variable is set")
    print("=" * 70)

    # Run all examples
    example_two_datasets()
    example_three_datasets_bar()
    example_five_datasets()
    example_no_x_axis()
    example_with_axis_controls()
    example_backward_compatible()

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)
