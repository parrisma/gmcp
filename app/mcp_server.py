#!/usr/bin/env python3
"""MCP Server for Graph Rendering

This server exposes graph rendering capabilities through the Model Context Protocol.
It provides tools to render line and bar charts using matplotlib.

This server uses Streamable HTTP transport, which is the modern preferred standard
for MCP servers, superseding SSE. It's compatible with n8n's MCP Client Tool and
other modern MCP clients.
"""

import asyncio
import contextlib
import json
import sys
from pathlib import Path
from typing import Any, AsyncIterator
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Add parent directory to path to enable imports when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.render import GraphRenderer
from app.graph_params import GraphParams
from app.validation import GraphDataValidator
from app.storage import get_storage
from app.auth import AuthService
from app.logger import ConsoleLogger
from app.themes import list_themes_with_descriptions
from app.handlers import list_handlers_with_descriptions
import logging as python_logging
from datetime import datetime
import base64
import os


# Initialize the MCP server
app = Server("gplot-renderer")
renderer = GraphRenderer()
validator = GraphDataValidator()
storage = get_storage()
logger = ConsoleLogger(name="mcp_server", level=python_logging.INFO)

# Initialize auth service (will be configured when server starts)
auth_service: AuthService | None = None


@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools for graph rendering."""
    return [
        Tool(
            name="ping",
            description="Health check that returns the current server timestamp to verify the server is running.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="render_graph",
            description=(
                "Render a graph (line or bar chart) and return it as a base64-encoded PNG image or GUID. "
                "Provide data points, labels, and styling options to create the visualization. "
                "If proxy=true, the image is saved to disk and a GUID is returned instead of base64 data."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The title of the graph"},
                    "x": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "X-axis data points (optional, defaults to indices [0, 1, 2, ...]). For backward compatibility, you can also use old 'y' parameter which maps to 'y1'.",
                    },
                    "y": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Y-axis data points (backward compatibility - maps to y1, list of numbers)",
                    },
                    "y1": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "First dataset Y-axis data points (required unless 'y' provided, list of numbers)",
                    },
                    "y2": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Second dataset Y-axis data points (optional)",
                    },
                    "y3": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Third dataset Y-axis data points (optional)",
                    },
                    "y4": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Fourth dataset Y-axis data points (optional)",
                    },
                    "y5": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Fifth dataset Y-axis data points (optional)",
                    },
                    "label1": {
                        "type": "string",
                        "description": "Label for first dataset (optional, for legend)",
                    },
                    "label2": {
                        "type": "string",
                        "description": "Label for second dataset (optional, for legend)",
                    },
                    "label3": {
                        "type": "string",
                        "description": "Label for third dataset (optional, for legend)",
                    },
                    "label4": {
                        "type": "string",
                        "description": "Label for fourth dataset (optional, for legend)",
                    },
                    "label5": {
                        "type": "string",
                        "description": "Label for fifth dataset (optional, for legend)",
                    },
                    "color1": {
                        "type": "string",
                        "description": "Color for first dataset (e.g., 'red', '#FF5733', 'rgb(255,87,51)')",
                    },
                    "color2": {
                        "type": "string",
                        "description": "Color for second dataset",
                    },
                    "color3": {
                        "type": "string",
                        "description": "Color for third dataset",
                    },
                    "color4": {
                        "type": "string",
                        "description": "Color for fourth dataset",
                    },
                    "color5": {
                        "type": "string",
                        "description": "Color for fifth dataset",
                    },
                    "xlabel": {
                        "type": "string",
                        "description": "Label for the X-axis (default: 'X-axis')",
                        "default": "X-axis",
                    },
                    "ylabel": {
                        "type": "string",
                        "description": "Label for the Y-axis (default: 'Y-axis')",
                        "default": "Y-axis",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["line", "scatter", "bar"],
                        "description": "The type of the graph: 'line', 'scatter', or 'bar' (default: 'line')",
                        "default": "line",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["png", "jpg", "svg", "pdf"],
                        "description": "Image format (default: 'png'). Supported: png, jpg, svg, pdf",
                        "default": "png",
                    },
                    "proxy": {
                        "type": "boolean",
                        "description": "If true, save image to disk and return GUID instead of base64 (default: false)",
                        "default": False,
                    },
                    "color": {
                        "type": "string",
                        "description": "Line/marker color (e.g., 'red', '#FF5733', 'rgb(255,87,51)')",
                    },
                    "line_width": {
                        "type": "number",
                        "description": "Line width for line plots (default: 2.0)",
                        "default": 2.0,
                    },
                    "marker_size": {
                        "type": "number",
                        "description": "Marker size for scatter plots (default: 36.0)",
                        "default": 36.0,
                    },
                    "alpha": {
                        "type": "number",
                        "description": "Transparency level from 0.0 (transparent) to 1.0 (opaque) (default: 1.0)",
                        "default": 1.0,
                    },
                    "theme": {
                        "type": "string",
                        "enum": ["light", "dark", "bizlight", "bizdark"],
                        "description": "Visual theme for the graph (default: 'light') if theme is supplied specifying data set colours is optional and will override any theme colours",
                        "default": "light",
                    },
                    "xmin": {
                        "type": "number",
                        "description": "Minimum value for x-axis (optional)",
                    },
                    "xmax": {
                        "type": "number",
                        "description": "Maximum value for x-axis (optional)",
                    },
                    "ymin": {
                        "type": "number",
                        "description": "Minimum value for y-axis (optional)",
                    },
                    "ymax": {
                        "type": "number",
                        "description": "Maximum value for y-axis (optional)",
                    },
                    "x_major_ticks": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Custom positions for x-axis major tick marks (optional)",
                    },
                    "y_major_ticks": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Custom positions for y-axis major tick marks (optional)",
                    },
                    "x_minor_ticks": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Custom positions for x-axis minor tick marks (optional)",
                    },
                    "y_minor_ticks": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Custom positions for y-axis minor tick marks (optional)",
                    },
                    "token": {
                        "type": "string",
                        "description": "JWT authentication token (required for all operations)",
                    },
                },
                "required": ["title", "token"],
            },
        ),
        Tool(
            name="get_image",
            description=(
                "Retrieve a previously rendered image by its GUID. "
                "Returns the image as base64-encoded data."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "guid": {
                        "type": "string",
                        "description": "The GUID of the image to retrieve (returned by render_graph with proxy=true)",
                    },
                    "token": {
                        "type": "string",
                        "description": "JWT authentication token (required for all operations)",
                    },
                },
                "required": ["guid", "token"],
            },
        ),
        Tool(
            name="list_themes",
            description=(
                "List all available themes with their descriptions. "
                "Use this to discover which themes are available for the 'theme' parameter in render_graph."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="list_handlers",
            description=(
                "List all available graph types (handlers) with their descriptions. "
                "Use this to discover which graph types are available for the 'type' parameter in render_graph."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@app.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[TextContent | ImageContent | EmbeddedResource]:
    """
    Handle tool execution requests with comprehensive error handling.

    This function ensures the MCP server never crashes by catching all exceptions
    and returning meaningful error messages to the client.
    """

    if name == "ping":
        logger.info("Ping tool called")
        current_time = datetime.now().isoformat()
        logger.debug("Ping response", timestamp=current_time)
        return [
            TextContent(
                type="text", text=f"Server is running\nTimestamp: {current_time}\nService: gplot"
            )
        ]

    if name == "get_image":
        logger.info("Get image tool called")

        # Validate required arguments
        if "guid" not in arguments:
            logger.warning("Missing required argument: guid")
            return [
                TextContent(
                    type="text",
                    text="Error: Missing required argument 'guid'\n\n"
                    "Provide the GUID of the image to retrieve.",
                )
            ]

        if "token" not in arguments:
            logger.warning("Missing required argument: token")
            return [
                TextContent(
                    type="text",
                    text="Error: Missing required argument 'token'\n\n"
                    "JWT authentication token is required for all operations.",
                )
            ]

        guid = arguments["guid"]
        token = arguments["token"]

        # Verify JWT token
        try:
            if auth_service is None:
                raise RuntimeError("Authentication service not initialized")
            token_info = auth_service.verify_token(token)
            group = token_info.group
            logger.debug("Token verified", group=group)
        except Exception as e:
            logger.error("Token validation failed", error=str(e))
            return [
                TextContent(
                    type="text",
                    text=f"Authentication Error: {str(e)}\n\n"
                    "Provide a valid JWT token to access this resource.",
                )
            ]

        try:
            # Retrieve image from storage with group access control
            image_result = storage.get_image(guid, group=group)

            if image_result is None:
                logger.warning("Image not found", guid=guid)
                return [
                    TextContent(
                        type="text",
                        text=f"Error: Image not found for GUID: {guid}\n\n"
                        "The image may have been deleted or the GUID is invalid.",
                    )
                ]

            image_data, img_format = image_result

            # Encode to base64
            base64_image = base64.b64encode(image_data).decode("utf-8")

            logger.info(
                "Image retrieved successfully", guid=guid, format=img_format, size=len(image_data)
            )

            return [
                ImageContent(type="image", data=base64_image, mimeType=f"image/{img_format}"),
                TextContent(
                    type="text",
                    text=f"Successfully retrieved image: {guid}.{img_format}",
                ),
            ]

        except ValueError as e:
            logger.error("Invalid GUID", guid=guid, error=str(e))
            return [
                TextContent(
                    type="text",
                    text=f"Error: Invalid GUID format: {guid}\n\n{str(e)}",
                )
            ]
        except Exception as e:
            logger.error("Failed to retrieve image", guid=guid, error=str(e))
            return [
                TextContent(
                    type="text",
                    text=f"Error retrieving image: {str(e)}",
                )
            ]

    if name == "list_themes":
        logger.info("List themes tool called")
        try:
            themes = list_themes_with_descriptions()

            # Format the themes as a readable text response
            response_lines = ["Available Themes:\n"]
            for theme_name, description in sorted(themes.items()):
                response_lines.append(f"• {theme_name}: {description}")

            response_text = "\n".join(response_lines)
            logger.debug("Themes listed", count=len(themes))

            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            logger.error("Failed to list themes", error=str(e))
            return [
                TextContent(
                    type="text",
                    text=f"Error listing themes: {str(e)}",
                )
            ]

    if name == "list_handlers":
        logger.info("List handlers tool called")
        try:
            handlers = list_handlers_with_descriptions()

            # Format the handlers as a readable text response
            response_lines = ["Available Graph Types:\n"]
            for handler_name, description in sorted(handlers.items()):
                response_lines.append(f"• {handler_name}: {description}")

            response_text = "\n".join(response_lines)
            logger.debug("Handlers listed", count=len(handlers))

            return [TextContent(type="text", text=response_text)]
        except Exception as e:
            logger.error("Failed to list handlers", error=str(e))
            return [
                TextContent(
                    type="text",
                    text=f"Error listing handlers: {str(e)}",
                )
            ]

    if name != "render_graph":
        logger.warning("Unknown tool requested", tool_name=name)
        return [
            TextContent(
                type="text",
                text=f"Error: Unknown tool '{name}'\n\nAvailable tools:\n- ping\n- render_graph\n- get_image\n- list_themes\n- list_handlers",
            )
        ]

    logger.info("Render tool called")

    try:
        # Validate required arguments - only title and token are required now
        # x is optional (auto-generates indices), y1-y5 are optional (backward compatible with y)
        required_args = ["title", "token"]
        missing_args = [arg for arg in required_args if arg not in arguments]
        if missing_args:
            logger.warning("Missing required arguments", missing=missing_args)
            return [
                TextContent(
                    type="text",
                    text=f"Missing required arguments: {', '.join(missing_args)}\n\n"
                    f"Required: title, token (JWT)\n"
                    f"Data arrays: x (optional, auto-generated if omitted), y (backward compat) or y1-y5 (up to 5 datasets)\n"
                    f"Labels: label1-label5 (optional, for legend)\n"
                    f"Colors: color1-color5 (optional, per-dataset colors)\n"
                    f"Other: xlabel, ylabel, type, format, line_width, marker_size, alpha, theme, "
                    f"xmin, xmax, ymin, ymax, x_major_ticks, y_major_ticks, x_minor_ticks, y_minor_ticks",
                )
            ]

        # Verify JWT token
        token = arguments["token"]
        try:
            if auth_service is None:
                raise RuntimeError("Authentication service not initialized")
            token_info = auth_service.verify_token(token)
            group = token_info.group
            logger.debug("Token verified", group=group)
        except Exception as e:
            logger.error("Token validation failed", error=str(e))
            return [
                TextContent(
                    type="text",
                    text=f"Authentication Error: {str(e)}\n\n"
                    "Provide a valid JWT token to access this service.",
                )
            ]

        # Validate data arrays if provided
        # x is optional (will be auto-generated if omitted)
        # y is backward compat, y1-y5 are the new multi-dataset parameters
        if "x" in arguments and not isinstance(arguments["x"], list):
            logger.warning("Invalid x argument type", type=type(arguments["x"]).__name__)
            return [
                TextContent(
                    type="text",
                    text="Error: 'x' must be an array of numbers\n\nExample: x=[1, 2, 3, 4, 5]",
                )
            ]

        logger.debug(
            "Request validated",
            title=arguments.get("title"),
            data_points=len(arguments.get("x", [])),
            chart_type=arguments.get("type", "line"),
        )

        # Create GraphParams from arguments - pass all optional fields
        try:
            is_proxy = arguments.get("proxy", False)
            graph_data = GraphParams(
                title=arguments["title"],
                x=arguments.get("x"),  # Optional now
                y1=arguments.get("y1"),  # Optional if 'y' is provided
                y2=arguments.get("y2"),
                y3=arguments.get("y3"),
                y4=arguments.get("y4"),
                y5=arguments.get("y5"),
                label1=arguments.get("label1"),
                label2=arguments.get("label2"),
                label3=arguments.get("label3"),
                label4=arguments.get("label4"),
                label5=arguments.get("label5"),
                color1=arguments.get("color1"),
                color2=arguments.get("color2"),
                color3=arguments.get("color3"),
                color4=arguments.get("color4"),
                color5=arguments.get("color5"),
                xlabel=arguments.get("xlabel", "X-axis"),
                ylabel=arguments.get("ylabel", "Y-axis"),
                type=arguments.get("type", "line"),
                format=arguments.get("format", "png"),
                return_base64=not is_proxy,  # If proxy, don't return base64
                proxy=is_proxy,
                line_width=arguments.get("line_width", 2.0),
                marker_size=arguments.get("marker_size", 36.0),
                alpha=arguments.get("alpha", 1.0),
                theme=arguments.get("theme", "light"),
                # Axis limits
                xmin=arguments.get("xmin"),
                xmax=arguments.get("xmax"),
                ymin=arguments.get("ymin"),
                ymax=arguments.get("ymax"),
                # Major and minor ticks
                x_major_ticks=arguments.get("x_major_ticks"),
                y_major_ticks=arguments.get("y_major_ticks"),
                x_minor_ticks=arguments.get("x_minor_ticks"),
                y_minor_ticks=arguments.get("y_minor_ticks"),
                # Backward compatibility
                y=arguments.get("y"),
                color=arguments.get("color"),
            )
            logger.debug("GraphData created successfully")
        except Exception as e:
            logger.error("Failed to create GraphData", error=str(e), error_type=type(e).__name__)
            return [
                TextContent(
                    type="text",
                    text=f"Error creating graph data: {str(e)}\n\n"
                    f"Suggestions:\n"
                    f"- Ensure y1 (required) is an array of numbers\n"
                    f"- If providing x, ensure it's an array of numbers (optional, defaults to indices)\n"
                    f"- For multiple datasets, provide y2, y3, y4, y5 as arrays of numbers\n"
                    f"- Check that all numeric parameters (alpha, line_width, marker_size) are valid numbers\n"
                    f"- For backward compatibility, you can use 'y' which maps to 'y1'",
                )
            ]

        # Validate the input data
        try:
            logger.debug("Validating graph data")
            validation_result = validator.validate(graph_data)

            if not validation_result.is_valid:
                logger.warning(
                    "Validation failed",
                    error_count=len(validation_result.errors),
                    errors=[e.field for e in validation_result.errors],
                )
                # Return validation errors as text
                error_message = validation_result.get_error_summary()
                return [TextContent(type="text", text=f"Validation Error:\n\n{error_message}")]
            logger.debug("Validation passed")
        except Exception as e:
            logger.error("Validation error", error=str(e), error_type=type(e).__name__)
            return [
                TextContent(
                    type="text",
                    text=f"Error during validation: {str(e)}\n\n"
                    f"The validation system encountered an unexpected error.\n"
                    f"Please check your input data format.",
                )
            ]

        # Render the graph (will be base64 string or GUID)
        try:
            logger.debug("Starting render", group=group)
            base64_image = renderer.render(graph_data, group=group)
            logger.info(
                "Render completed successfully",
                chart_type=graph_data.type,
                format=graph_data.format,
                output_size=len(base64_image) if isinstance(base64_image, (str, bytes)) else 0,
                group=group,
            )
        except ValueError as e:
            logger.error("Configuration error", error=str(e), chart_type=graph_data.type)
            # Handle known validation errors from renderer
            return [
                TextContent(
                    type="text",
                    text=f"Configuration Error: {str(e)}\n\n"
                    f"Suggestions:\n"
                    f"- Check that the chart type is valid (line, scatter, bar)\n"
                    f"- Verify the theme name is correct (light, dark)\n"
                    f"- Ensure the format is supported (png, jpg, svg, pdf)",
                )
            ]
        except RuntimeError as e:
            logger.error("Runtime error during render", error=str(e), chart_type=graph_data.type)
            # Handle rendering errors
            return [
                TextContent(
                    type="text",
                    text=f"Rendering Error: {str(e)}\n\n"
                    f"The graph rendering process failed.\n"
                    f"Suggestions:\n"
                    f"- Verify your data values are valid numbers\n"
                    f"- Check that arrays are not empty\n"
                    f"- Try reducing the data size or simplifying the request",
                )
            ]
        except Exception as e:
            logger.error(
                "Unexpected error during render", error=str(e), error_type=type(e).__name__
            )
            return [
                TextContent(
                    type="text",
                    text=f"Unexpected rendering error: {str(e)}\n\n"
                    f"An unexpected error occurred during rendering.\n"
                    f"Please verify your input data and try again.",
                )
            ]

        # Check if result is a GUID (proxy mode) or base64 data
        if is_proxy:
            # Proxy mode: base64_image is actually a GUID string
            guid = str(base64_image)
            logger.info("Returning GUID response (proxy mode)", title=graph_data.title, guid=guid)
            return [
                TextContent(
                    type="text",
                    text=f"Image saved with GUID: {guid}\n\n"
                    f"Chart: {graph_data.type} - '{graph_data.title}'\n"
                    f"Format: {graph_data.format}\n"
                    f"Use get_image tool with guid='{guid}' to retrieve the image.",
                ),
            ]

        # Regular mode: Ensure it's a string for ImageContent
        try:
            if isinstance(base64_image, bytes):
                base64_image = base64_image.decode("utf-8")
            elif isinstance(base64_image, (bytearray, memoryview)):
                base64_image = bytes(base64_image).decode("utf-8")
            logger.debug("Image encoded successfully")
        except Exception as e:
            logger.error("Failed to encode image", error=str(e))
            return [
                TextContent(
                    type="text",
                    text=f"Error encoding image: {str(e)}\n\n"
                    f"Failed to convert the rendered image to base64 format.",
                )
            ]

        # Type assertion for type checker - base64_image is now definitely a str
        base64_str: str = str(base64_image)

        # Return the rendered image
        try:
            logger.info("Returning successful response", title=graph_data.title)
            result: list[TextContent | ImageContent | EmbeddedResource] = [
                ImageContent(type="image", data=base64_str, mimeType=f"image/{graph_data.format}"),
                TextContent(
                    type="text",
                    text=f"Successfully rendered {graph_data.type} chart: '{graph_data.title}'",
                ),
            ]
            return result
        except Exception as e:
            logger.error("Failed to create response", error=str(e))
            return [
                TextContent(
                    type="text",
                    text=f"Error creating response: {str(e)}\n\n"
                    f"The image was rendered but could not be packaged for return.",
                )
            ]

    except KeyboardInterrupt:
        # Handle graceful shutdown
        logger.info("Interrupted by user")
        raise
    except Exception as e:
        # Ultimate fallback - catch any unexpected exceptions
        logger.critical("Critical error in tool handler", error=str(e), error_type=type(e).__name__)
        return [
            TextContent(
                type="text",
                text=f"Critical Error: {str(e)}\n\n"
                f"An unexpected error occurred. This should not happen.\n"
                f"Please report this issue with your input data.\n\n"
                f"Error type: {type(e).__name__}",
            )
        ]


# Create StreamableHTTP session manager
session_manager = StreamableHTTPSessionManager(
    app=app,
    event_store=None,  # No event store for stateless operation
    json_response=False,  # Use SSE streams by default
    stateless=False,  # Maintain session state
)


async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
    """Handle Streamable HTTP requests for MCP protocol."""
    await session_manager.handle_request(scope, receive, send)


@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    """Context manager for managing session manager lifecycle."""
    logger.info("Initializing StreamableHTTP session manager")
    async with session_manager.run():
        logger.info("StreamableHTTP session manager started", status="ready")
        try:
            yield
        finally:
            logger.info("StreamableHTTP session manager shutting down", status="stopping")


# Create Starlette app for Streamable HTTP transport
# Use trailing slash in mount path to avoid redirects
starlette_app = Starlette(
    debug=True,
    routes=[
        Mount("/mcp/", app=handle_streamable_http),
    ],
    lifespan=lifespan,
)

# Add CORS middleware to expose Mcp-Session-Id header
starlette_app = CORSMiddleware(
    starlette_app,
    allow_origins=["*"],  # Allow all origins - adjust for production
    allow_methods=["GET", "POST", "DELETE"],  # MCP streamable HTTP methods
    expose_headers=["Mcp-Session-Id"],
)


async def main(host: str = "0.0.0.0", port: int = 8001):
    """
    Run the MCP server with Streamable HTTP transport and comprehensive error handling.

    Args:
        host: Host address to bind to (default: 0.0.0.0)
        port: Port number to listen on (default: 8001)
    """
    import uvicorn

    logger.info(
        "Starting MCP Streamable HTTP server",
        version="1.0.0",
        host=host,
        port=port,
        transport="Streamable HTTP",
    )
    try:
        config = uvicorn.Config(
            starlette_app,
            host=host,
            port=port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        logger.info(f"Server initialized, listening on http://{host}:{port}/mcp/", endpoint="/mcp/")
        await server.serve()
        logger.info("Server shutdown complete")
    except KeyboardInterrupt:
        # Handle graceful shutdown
        logger.info("Server stopped by user")
    except Exception as e:
        logger.critical("Fatal server error", error=str(e), error_type=type(e).__name__)
        sys.exit(1)
