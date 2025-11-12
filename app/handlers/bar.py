from typing import TYPE_CHECKING, Any
import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from app.graph_params import GraphParams

from app.handlers.base import GraphHandler


class BarGraphHandler(GraphHandler):
    """Handler for bar charts with support for multiple datasets"""

    def get_description(self) -> str:
        """Return a description of this graph type"""
        return "Bar chart for comparing discrete categories or groups, supports single dataset bars or grouped bars for multiple datasets with automatic positioning"

    def plot(self, ax: "Axes", data: "GraphParams") -> None:
        """
        Plot bar chart with error handling, supporting multiple datasets

        Multiple datasets (y1-y5) will be plotted as grouped bars side-by-side.
        Each dataset can have optional custom color and label for legend support.

        Raises:
            ValueError: If data cannot be plotted
        """
        try:
            datasets = data.get_datasets()

            if not datasets:
                raise ValueError("No datasets provided (y1 is required)")

            # Get x values (shared across all datasets)
            x_values = data.get_x_values(len(datasets[0][0]))

            num_datasets = len(datasets)

            if num_datasets == 1:
                # Single dataset - simple bar chart
                y_data, label, color = datasets[0]
                kwargs: dict[str, Any] = {"alpha": data.alpha}

                if color:
                    kwargs["color"] = color
                if label:
                    kwargs["label"] = label

                ax.bar(x_values, y_data, **kwargs)
            else:
                # Multiple datasets - grouped bars
                bar_width = 0.8 / num_datasets  # Divide space among datasets
                x_array = np.array(x_values)

                for i, (y_data, label, color) in enumerate(datasets):
                    # Offset each dataset's bars
                    offset = (i - num_datasets / 2 + 0.5) * bar_width
                    x_positions = x_array + offset

                    kwargs: dict[str, Any] = {"width": bar_width, "alpha": data.alpha}

                    if color:
                        kwargs["color"] = color
                    if label:
                        kwargs["label"] = label

                    ax.bar(x_positions, y_data, **kwargs)

            # Add legend if any dataset has a label
            if any(label for _, label, _ in datasets):
                ax.legend()

        except Exception as e:
            raise ValueError(f"Failed to plot bar chart: {str(e)}")
