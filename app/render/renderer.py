"""Graph renderer implementation

Main renderer class that coordinates the rendering pipeline.
"""

import matplotlib.pyplot as plt
import io
import base64
from typing import Optional
from app.graph_params import GraphParams
from app.handlers import get_handler, list_handlers
from app.themes import get_theme
from app.storage import get_storage
from app.logger import ConsoleLogger
import logging


class GraphRenderer:
    """Main renderer that delegates to specific graph handlers via registry"""

    def __init__(self):
        self.logger = ConsoleLogger(name="renderer", level=logging.INFO)
        self.logger.debug("GraphRenderer initialized", handlers=list_handlers())

    def render(self, data: GraphParams, group: Optional[str] = None) -> str | bytes:
        """
        Render a graph based on the provided data

        Args:
            data: GraphParams containing all parameters for rendering
            group: Optional group name for storage access control

        Returns:
            Base64-encoded string, raw bytes, or GUID string (proxy mode)

        Raises:
            ValueError: If graph type is not supported or theme is invalid
            RuntimeError: If rendering fails
        """
        fig = None
        buf = None

        datasets = data.get_datasets()
        data_points = len(datasets[0][0]) if datasets else 0

        self.logger.info(
            "Starting render",
            chart_type=data.type,
            format=data.format,
            theme=data.theme,
            num_datasets=len(datasets),
            data_points=data_points,
        )

        try:
            # Get the appropriate handler from registry
            try:
                handler = get_handler(data.type)
                self.logger.debug("Handler selected", handler=type(handler).__name__)
            except ValueError as e:
                self.logger.error("Unsupported graph type", chart_type=data.type, error=str(e))
                raise

            # Get and apply theme
            try:
                self.logger.debug("Loading theme", theme_name=data.theme)
                theme = get_theme(data.theme)
            except ValueError as e:
                self.logger.error("Theme error", theme_name=data.theme, error=str(e))
                raise ValueError(f"Theme error: {str(e)}")

            # Create figure and plot
            try:
                self.logger.debug("Creating matplotlib figure")
                fig, ax = plt.subplots()
            except Exception as e:
                self.logger.error("Failed to create figure", error=str(e))
                raise RuntimeError(f"Failed to create matplotlib figure: {str(e)}")

            # Apply theme before plotting
            try:
                self.logger.debug("Applying theme to figure")
                theme.apply(fig, ax)
            except Exception as e:
                self.logger.error("Failed to apply theme", error=str(e))
                raise RuntimeError(f"Failed to apply theme: {str(e)}")

            # Use theme's default color if no color specified
            if data.color is None:
                try:
                    data.color = theme.get_default_color()
                    self.logger.debug("Using theme default color", color=data.color)
                except Exception as e:
                    # Fallback to a safe default if theme fails
                    self.logger.warning("Failed to get theme color, using fallback", error=str(e))
                    data.color = "blue"

            # Plot data
            try:
                self.logger.debug("Plotting data", handler=type(handler).__name__)
                handler.plot(ax, data)
            except Exception as e:
                self.logger.error(
                    "Failed to plot data", error=str(e), handler=type(handler).__name__
                )
                raise RuntimeError(f"Failed to plot data: {str(e)}")

            # Set labels and title
            try:
                self.logger.debug("Setting labels and title")
                ax.set_title(data.title)
                ax.set_xlabel(data.xlabel)
                ax.set_ylabel(data.ylabel)
            except Exception as e:
                self.logger.error("Failed to set labels", error=str(e))
                raise RuntimeError(f"Failed to set labels: {str(e)}")

            # Apply axis limits if specified
            try:
                if data.xmin is not None or data.xmax is not None:
                    self.logger.debug("Setting x-axis limits", xmin=data.xmin, xmax=data.xmax)
                    ax.set_xlim(left=data.xmin, right=data.xmax)
                if data.ymin is not None or data.ymax is not None:
                    self.logger.debug("Setting y-axis limits", ymin=data.ymin, ymax=data.ymax)
                    ax.set_ylim(bottom=data.ymin, top=data.ymax)
            except Exception as e:
                self.logger.error("Failed to set axis limits", error=str(e))
                raise RuntimeError(f"Failed to set axis limits: {str(e)}")

            # Apply major ticks if specified
            try:
                if data.x_major_ticks is not None:
                    self.logger.debug("Setting x-axis major ticks", count=len(data.x_major_ticks))
                    ax.set_xticks(data.x_major_ticks)
                if data.y_major_ticks is not None:
                    self.logger.debug("Setting y-axis major ticks", count=len(data.y_major_ticks))
                    ax.set_yticks(data.y_major_ticks)
            except Exception as e:
                self.logger.error("Failed to set major ticks", error=str(e))
                raise RuntimeError(f"Failed to set major ticks: {str(e)}")

            # Apply minor ticks if specified
            try:
                if data.x_minor_ticks is not None:
                    self.logger.debug("Setting x-axis minor ticks", count=len(data.x_minor_ticks))
                    ax.set_xticks(data.x_minor_ticks, minor=True)
                if data.y_minor_ticks is not None:
                    self.logger.debug("Setting y-axis minor ticks", count=len(data.y_minor_ticks))
                    ax.set_yticks(data.y_minor_ticks, minor=True)
            except Exception as e:
                self.logger.error("Failed to set minor ticks", error=str(e))
                raise RuntimeError(f"Failed to set minor ticks: {str(e)}")

            # Save to buffer
            try:
                self.logger.debug("Saving to buffer", format=data.format)
                buf = io.BytesIO()
                plt.savefig(buf, format=data.format, facecolor=fig.get_facecolor())
                buf.seek(0)
            except Exception as e:
                self.logger.error("Failed to save to buffer", error=str(e), format=data.format)
                raise RuntimeError(f"Failed to save image to buffer: {str(e)}")

            # Return as GUID (proxy mode), base64, or raw bytes
            try:
                image_data = buf.read()
                image_size = len(image_data)

                # Proxy mode: save to disk and return GUID
                if data.proxy:
                    self.logger.debug(
                        "Proxy mode: saving to storage", size_bytes=image_size, group=group
                    )
                    storage = get_storage()
                    guid = storage.save_image(image_data, data.format, group=group)
                    self.logger.info(
                        "Render completed (proxy mode)",
                        chart_type=data.type,
                        format=data.format,
                        output_size_bytes=image_size,
                        guid=guid,
                        group=group,
                    )
                    return guid

                if data.return_base64:
                    self.logger.debug("Encoding as base64", size_bytes=image_size)
                    encoded = base64.b64encode(image_data).decode("utf-8")
                    self.logger.info(
                        "Render completed successfully",
                        chart_type=data.type,
                        format=data.format,
                        output_size_bytes=image_size,
                        base64_length=len(encoded),
                    )
                    return encoded

                self.logger.info(
                    "Render completed successfully",
                    chart_type=data.type,
                    format=data.format,
                    output_size_bytes=image_size,
                )
                return image_data
            except Exception as e:
                self.logger.error("Failed to encode image data", error=str(e))
                raise RuntimeError(f"Failed to encode image data: {str(e)}")

        except (ValueError, RuntimeError):
            # Re-raise known exceptions
            raise
        except Exception as e:
            # Catch any unexpected exceptions
            self.logger.error(
                "Unexpected error during rendering", error=str(e), error_type=type(e).__name__
            )
            raise RuntimeError(f"Unexpected error during rendering: {str(e)}")
        finally:
            # Always close the figure to free memory
            if fig is not None:
                try:
                    self.logger.debug("Cleaning up matplotlib figure")
                    plt.close(fig)
                except Exception as e:
                    self.logger.warning("Error closing figure", error=str(e))
                    pass  # Ignore errors during cleanup

            # Close buffer if it exists
            if buf is not None:
                try:
                    buf.close()
                except Exception:
                    pass  # Ignore errors during cleanup
