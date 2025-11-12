# Multi-Dataset Support

## Overview

The gplot rendering service now supports plotting up to 5 datasets on a single graph. This allows you to create comparative visualizations with multiple data series, each with its own styling and legend labels.

## Key Features

- **Up to 5 datasets**: Plot y1, y2, y3, y4, y5 on the same graph
- **Optional X-axis**: X-axis values are optional and default to indices [0, 1, 2, ...]
- **Individual styling**: Each dataset can have its own color
- **Legend support**: Each dataset can have a custom label for the legend
- **All chart types**: Works with line, scatter, and bar charts
- **Backward compatibility**: Old single-dataset `x`, `y` parameters still work

## Parameters

### Required Parameters
- `title` (string): The title of the graph
- `y1` (array of numbers): First dataset (or use `y` for backward compatibility)

### Optional Dataset Parameters
- `x` (array of numbers): Shared X-axis values (defaults to [0, 1, 2, ...])
- `y2`, `y3`, `y4`, `y5` (arrays of numbers): Additional datasets
- `label1`, `label2`, `label3`, `label4`, `label5` (strings): Legend labels for each dataset
- `color1`, `color2`, `color3`, `color4`, `color5` (strings): Colors for each dataset

### Standard Parameters
- `xlabel` (string): Label for X-axis (default: "X-axis")
- `ylabel` (string): Label for Y-axis (default: "Y-axis")
- `type` (string): Chart type: "line", "scatter", or "bar" (default: "line")
- `format` (string): Image format: "png", "jpg", "svg", "pdf" (default: "png")
- `theme` (string): Visual theme: "light", "dark", "bizlight", "bizdark" (default: "light")

## Examples

### Web API Examples

#### Single Dataset (Backward Compatible)
```python
import requests

response = requests.post("http://localhost:8000/render",
    json={
        "title": "Temperature",
        "x": [1, 2, 3, 4, 5],
        "y": [20, 22, 21, 23, 25],  # Maps to y1
        "type": "line"
    }
)
```

#### Two Datasets with Labels
```python
response = requests.post("http://localhost:8000/render",
    json={
        "title": "Temperature Comparison",
        "x": [1, 2, 3, 4, 5],
        "y1": [20, 22, 21, 23, 25],
        "y2": [18, 20, 19, 21, 23],
        "label1": "City A",
        "label2": "City B",
        "color1": "red",
        "color2": "blue",
        "type": "line"
    }
)
```

#### Multiple Datasets Without X-axis (Auto-indexed)
```python
response = requests.post("http://localhost:8000/render",
    json={
        "title": "Sales by Product",
        "y1": [100, 150, 120],
        "y2": [80, 90, 110],
        "y3": [60, 70, 65],
        "label1": "Product A",
        "label2": "Product B",
        "label3": "Product C",
        "color1": "#FF5733",
        "color2": "#33FF57",
        "color3": "#3357FF",
        "type": "bar"
    }
)
# X-axis will be [0, 1, 2]
```

#### Five Datasets (Maximum)
```python
response = requests.post("http://localhost:8000/render",
    json={
        "title": "5-Day Weather Stations",
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
        "type": "line"
    }
)
```

### MCP Protocol Examples

#### Two Datasets via MCP
```python
from mcp import ClientSession
from mcp.client.streamablehttp import streamablehttp_client

async with streamablehttp_client("http://localhost:8001/mcp/") as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        result = await session.call_tool(
            "render_graph",
            arguments={
                "title": "Comparison",
                "x": [1, 2, 3, 4],
                "y1": [10, 20, 15, 25],
                "y2": [8, 18, 13, 23],
                "label1": "Series A",
                "label2": "Series B",
                "color1": "red",
                "color2": "blue",
                "type": "line",
                "token": "your-jwt-token"
            }
        )
```

#### Three Datasets with Bar Chart
```python
result = await session.call_tool(
    "render_graph",
    arguments={
        "title": "Quarterly Sales",
        "y1": [100, 120, 110, 130],
        "y2": [90, 100, 95, 110],
        "y3": [80, 95, 85, 100],
        "label1": "Q1",
        "label2": "Q2",
        "label3": "Q3",
        "type": "bar",
        "token": "your-jwt-token"
    }
)
# X-axis auto-generated: [0, 1, 2, 3]
```

## Chart Type Behavior

### Line Charts
- Each dataset plotted as a separate line
- Legend automatically shown if any labels provided
- Lines share the same X-axis values

### Scatter Plots
- Each dataset plotted as a separate scatter series
- All markers use the same size (`marker_size` parameter)
- Individual colors can be specified per dataset

### Bar Charts
- Single dataset: Standard bar chart
- Multiple datasets: Grouped bars side-by-side
- Bars automatically positioned to avoid overlap
- Width adjusted based on number of datasets

## Validation Rules

1. **At least one dataset required**: Must provide `y1` (or `y` for backward compatibility)
2. **Equal lengths**: All datasets must have the same number of points
3. **X-axis matching**: If `x` is provided, it must match the dataset length
4. **Maximum 5 datasets**: Can provide up to y1, y2, y3, y4, y5
5. **Color format**: Colors must be valid (hex, rgb, rgba, or named colors)

## Backward Compatibility

The service maintains full backward compatibility with the original single-dataset API:

- `y` parameter maps to `y1`
- `color` parameter maps to `color1`
- Existing code continues to work without modification
- `x` is now optional (defaults to indices)

### Migration Examples

**Old API:**
```python
{
    "title": "Sales",
    "x": [1, 2, 3],
    "y": [100, 120, 110],
    "color": "blue"
}
```

**New API (equivalent):**
```python
{
    "title": "Sales",
    "x": [1, 2, 3],
    "y1": [100, 120, 110],
    "color1": "blue"
}
```

**Both work identically!**

## Legend Display

A legend is automatically displayed when:
- Any dataset has a `label` parameter set
- Multiple datasets are provided with labels

Position: Upper right corner (matplotlib default)

## Best Practices

1. **Use meaningful labels**: Provide `label1`, `label2`, etc. when plotting multiple datasets
2. **Choose distinct colors**: Use contrasting colors for better visualization
3. **Keep datasets aligned**: Ensure all y-arrays have the same length
4. **Omit X for simplicity**: If X-axis values are sequential, omit `x` for auto-indexing
5. **Limit datasets**: While 5 datasets are supported, 2-3 is optimal for readability

## Error Handling

Common errors and solutions:

### "At least one dataset (y1) is required"
- **Cause**: Neither `y` nor `y1` provided
- **Solution**: Provide at least `y1` parameter

### "All datasets must have the same length"
- **Cause**: y1, y2, y3, etc. have different numbers of points
- **Solution**: Ensure all y-arrays have equal length

### "X array must match dataset length"
- **Cause**: `x` array length doesn't match y-array lengths
- **Solution**: Make `x` the same length as your y-arrays, or omit `x`

### "Invalid color format"
- **Cause**: Color string not recognized
- **Solution**: Use hex (#FF5733), rgb(255,87,51), or named colors (red, blue, etc.)

## Performance Considerations

- **Multiple datasets**: Rendering time increases linearly with dataset count
- **Large datasets**: Consider limiting data points for better performance
- **Bar charts**: Grouped bars take slightly more time than single-dataset bars
- **Legend**: Minimal impact on performance

## See Also

- [Graph Parameters](./GRAPH_PARAMS.md) - All parameter documentation
- [Axis Controls](./AXIS_CONTROLS.md) - Axis limits and tick customization
- [Themes](./THEMES.md) - Visual theme options
- [MCP Server](./MCP_README.md) - MCP protocol documentation
