#!/usr/bin/env python3
"""
Example demonstrating axis limits and tick controls

This script shows how to use the new axis limit and tick control features.
"""

import requests
import json
import base64
from pathlib import Path

# API endpoint
BASE_URL = "http://localhost:8000"


def save_image(base64_data: str, filename: str):
    """Save base64 image to file"""
    image_data = base64.b64decode(base64_data)
    output_dir = Path("examples/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    with open(output_path, "wb") as f:
        f.write(image_data)
    print(f"Saved: {output_path}")


def example_1_axis_limits():
    """Example 1: Basic axis limits"""
    print("\n1. Chart with custom axis limits")

    data = {
        "title": "Sales Data with Custom Axis Range",
        "x": [1, 2, 3, 4, 5],
        "y": [100, 150, 120, 180, 200],
        "xlabel": "Month",
        "ylabel": "Sales ($)",
        "type": "line",
        "format": "png",
        "xmin": 0,
        "xmax": 6,
        "ymin": 0,
        "ymax": 250,
    }

    response = requests.post(f"{BASE_URL}/render", json=data)
    if response.status_code == 200:
        save_image(response.json()["image"], "axis_limits.png")
    else:
        print(f"Error: {response.status_code}")


def example_2_major_ticks():
    """Example 2: Custom major tick positions"""
    print("\n2. Chart with custom major ticks")

    data = {
        "title": "Temperature Over Time",
        "x": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24],
        "y": [15, 16, 18, 21, 24, 27, 29, 28, 26, 23, 20, 18, 16],
        "xlabel": "Hour of Day",
        "ylabel": "Temperature (°C)",
        "type": "line",
        "format": "png",
        "x_major_ticks": [0, 6, 12, 18, 24],
        "y_major_ticks": [10, 15, 20, 25, 30],
    }

    response = requests.post(f"{BASE_URL}/render", json=data)
    if response.status_code == 200:
        save_image(response.json()["image"], "major_ticks.png")
    else:
        print(f"Error: {response.status_code}")


def example_3_minor_ticks():
    """Example 3: Major and minor ticks together"""
    print("\n3. Chart with major and minor ticks")

    data = {
        "title": "Precise Measurement Data",
        "x": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "y": [0, 5, 12, 18, 22, 24, 23, 20, 15, 8, 0],
        "xlabel": "Position",
        "ylabel": "Value",
        "type": "scatter",
        "format": "png",
        "xmin": 0,
        "xmax": 10,
        "ymin": 0,
        "ymax": 30,
        "x_major_ticks": [0, 5, 10],
        "x_minor_ticks": [1, 2, 3, 4, 6, 7, 8, 9],
        "y_major_ticks": [0, 10, 20, 30],
        "y_minor_ticks": [5, 15, 25],
        "marker_size": 50,
    }

    response = requests.post(f"{BASE_URL}/render", json=data)
    if response.status_code == 200:
        save_image(response.json()["image"], "major_minor_ticks.png")
    else:
        print(f"Error: {response.status_code}")


def example_4_all_combined():
    """Example 4: All features combined"""
    print("\n4. Chart with all axis controls")

    data = {
        "title": "Complete Axis Control Example",
        "x": [1, 2, 3, 4, 5, 6, 7, 8],
        "y": [45, 52, 48, 65, 70, 68, 75, 80],
        "xlabel": "Week",
        "ylabel": "Performance Score",
        "type": "line",
        "format": "png",
        "color": "#2E86AB",
        "line_width": 2.5,
        "xmin": 0,
        "xmax": 9,
        "ymin": 40,
        "ymax": 85,
        "x_major_ticks": [0, 2, 4, 6, 8],
        "y_major_ticks": [40, 50, 60, 70, 80],
        "x_minor_ticks": [1, 3, 5, 7],
        "y_minor_ticks": [45, 55, 65, 75],
        "theme": "dark",
    }

    response = requests.post(f"{BASE_URL}/render", json=data)
    if response.status_code == 200:
        save_image(response.json()["image"], "all_controls.png")
    else:
        print(f"Error: {response.status_code}")


def main():
    print("=" * 60)
    print("Axis Limits and Tick Controls Examples")
    print("=" * 60)
    print("\nMake sure the web server is running:")
    print("  python -m app.main_web --host 0.0.0.0 --port 8000 --no-auth")
    print()

    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/ping")
        if response.status_code != 200:
            print("Error: Server not responding")
            return

        # Run examples
        example_1_axis_limits()
        example_2_major_ticks()
        example_3_minor_ticks()
        example_4_all_combined()

        print("\n" + "=" * 60)
        print("All examples completed!")
        print("Check the examples/output/ directory for the generated images")
        print("=" * 60)

    except requests.ConnectionError:
        print("\nError: Cannot connect to server at", BASE_URL)
        print("Please start the server first:")
        print("  python -m app.main_web --host 0.0.0.0 --port 8000 --no-auth")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
