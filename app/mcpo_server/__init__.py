"""MCPO wrapper for gofr-plot MCP server

This module provides MCPO (MCP-to-OpenAPI) proxy functionality
to expose the gofr-plot MCP server as OpenAPI-compatible endpoints.
"""

from app.mcpo_server.wrapper import start_mcpo_wrapper

__all__ = ["start_mcpo_wrapper"]
