# Axis Limits and Tick Controls

The graph rendering API supports fine-grained control over axis limits and tick positions, allowing you to create precisely formatted charts that match your exact requirements.

## Features

### Axis Limits

Control the minimum and maximum values displayed on each axis:

- `xmin`: Minimum value for x-axis
- `xmax`: Maximum value for x-axis  
- `ymin`: Minimum value for y-axis
- `ymax`: Maximum value for y-axis

All axis limit parameters are optional. You can set:
- Both min and max for an axis
- Only min or only max for an axis
- Different combinations for x and y axes

### Major Ticks

Specify custom positions for major tick marks:

- `x_major_ticks`: List of positions for x-axis major ticks
- `y_major_ticks`: List of positions for y-axis major ticks

Major ticks are the primary tick marks with labels that appear on the axes.

### Minor Ticks

Specify custom positions for minor tick marks:

- `x_minor_ticks`: List of positions for x-axis minor ticks
- `y_minor_ticks`: List of positions for y-axis minor ticks

Minor ticks are smaller tick marks between major ticks, useful for showing finer gradations.

## Examples

### Example 1: Setting Axis Limits

```json
{
  "title": "Sales Data",
  "x": [1, 2, 3, 4, 5],
  "y": [100, 150, 120, 180, 200],
  "xlabel": "Month",
  "ylabel": "Sales ($)",
  "type": "line",
  "xmin": 0,
  "xmax": 6,
  "ymin": 0,
  "ymax": 250
}
```

This ensures the x-axis goes from 0 to 6 and y-axis from 0 to 250, regardless of the data values.

### Example 2: Custom Major Ticks

```json
{
  "title": "Temperature Over Time",
  "x": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24],
  "y": [15, 16, 18, 21, 24, 27, 29, 28, 26, 23, 20, 18, 16],
  "xlabel": "Hour of Day",
  "ylabel": "Temperature (°C)",
  "type": "line",
  "x_major_ticks": [0, 6, 12, 18, 24],
  "y_major_ticks": [10, 15, 20, 25, 30]
}
```

This places major tick marks at specific hours (0, 6, 12, 18, 24) and temperature values.

### Example 3: Major and Minor Ticks

```json
{
  "title": "Precise Measurement",
  "x": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  "y": [0, 5, 12, 18, 22, 24, 23, 20, 15, 8, 0],
  "type": "scatter",
  "xmin": 0,
  "xmax": 10,
  "ymin": 0,
  "ymax": 30,
  "x_major_ticks": [0, 5, 10],
  "x_minor_ticks": [1, 2, 3, 4, 6, 7, 8, 9],
  "y_major_ticks": [0, 10, 20, 30],
  "y_minor_ticks": [5, 15, 25]
}
```

This creates major ticks at intervals of 5 on the x-axis and 10 on the y-axis, with minor ticks filling in between.

### Example 4: Partial Limits

```json
{
  "title": "Revenue Growth",
  "x": [1, 2, 3, 4, 5],
  "y": [100, 150, 120, 180, 200],
  "type": "bar",
  "ymin": 0
}
```

You can set only the limits you need. Here, we ensure the y-axis starts at 0 (common for bar charts) while letting matplotlib determine the maximum automatically.

## MCP Tool Usage

When using the MCP `render_graph` tool, include the axis control parameters:

```python
result = await session.call_tool("render_graph", {
    "title": "Custom Axis Chart",
    "x": [1, 2, 3, 4, 5],
    "y": [10, 20, 15, 25, 30],
    "type": "line",
    "xmin": 0,
    "xmax": 6,
    "ymin": 0,
    "ymax": 35,
    "x_major_ticks": [0, 1, 2, 3, 4, 5, 6],
    "y_major_ticks": [0, 10, 20, 30],
    "token": "your-token-here"
})
```

## Web API Usage

POST to `/render` endpoint:

```bash
curl -X POST http://localhost:8000/render \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Custom Chart",
    "x": [1, 2, 3, 4, 5],
    "y": [2, 4, 6, 8, 10],
    "type": "line",
    "xmin": 0,
    "xmax": 6,
    "ymin": 0,
    "ymax": 12,
    "x_major_ticks": [0, 2, 4, 6],
    "y_major_ticks": [0, 3, 6, 9, 12]
  }'
```

## Best Practices

1. **Start axis at zero for bar charts**: For bar charts showing quantities, set `ymin: 0` to avoid misleading visualizations.

2. **Use consistent tick intervals**: When setting major ticks, use evenly spaced values for better readability.

3. **Don't overuse minor ticks**: Too many minor ticks can clutter the chart. Use them sparingly.

4. **Consider your data range**: Set axis limits that comfortably contain your data with some padding.

5. **Combine with themes**: Axis controls work seamlessly with all themes (light, dark, bizlight, bizdark).

## Backward Compatibility

All axis control parameters are optional. Existing code that doesn't use these features will continue to work exactly as before, with matplotlib automatically determining appropriate axis limits and tick positions.

## Implementation Details

The axis controls are applied in the following order during rendering:

1. Data is plotted
2. Labels and title are set
3. Axis limits are applied (if specified)
4. Major ticks are set (if specified)
5. Minor ticks are set (if specified)

This ensures that custom axis settings override matplotlib's automatic behavior while still respecting the underlying data.
