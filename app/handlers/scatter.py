from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from app.graph_params import GraphParams

from app.handlers.base import GraphHandler


class ScatterGraphHandler(GraphHandler):
    """Handler for scatter plots with support for multiple datasets"""

    def plot(self, ax: "Axes", data: "GraphParams") -> None:
        """
        Plot scatter plot with error handling, supporting multiple datasets

        Each dataset (y1-y5) will be plotted as a separate scatter series with optional
        custom color and label for legend support.

        Raises:
            ValueError: If data cannot be plotted
        """
        try:
            datasets = data.get_datasets()

            if not datasets:
                raise ValueError("No datasets provided (y1 is required)")

            # Get x values (shared across all datasets)
            x_values = data.get_x_values(len(datasets[0][0]))

            # Plot each dataset
            for i, (y_data, label, color) in enumerate(datasets):
                kwargs: dict[str, Any] = {"s": data.marker_size, "alpha": data.alpha}

                if color:
                    kwargs["c"] = color

                if label:
                    kwargs["label"] = label

                ax.scatter(x_values, y_data, **kwargs)

            # Add legend if any dataset has a label
            if any(label for _, label, _ in datasets):
                ax.legend()

        except Exception as e:
            raise ValueError(f"Failed to plot scatter chart: {str(e)}")

    def get_description(self) -> str:
        """Get a human-readable description of the handler"""
        return "Scatter plot for showing relationships between variables and identifying patterns or correlations in data points, supports multiple datasets"
