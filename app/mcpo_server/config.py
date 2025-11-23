"""MCPO configuration management

Handles generation of mcpo config files for multiple server configurations.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class MCPOConfig:
    """MCPO configuration builder"""

    def __init__(self):
        self.servers: Dict[str, dict] = {}

    def add_server(
        self,
        name: str,
        url: str,
        auth_token: Optional[str] = None,
        disabled_tools: Optional[List[str]] = None,
    ) -> None:
        """
        Add an MCP server to the configuration

        Args:
            name: Unique name for this server instance
            url: URL of the MCP server endpoint
            auth_token: Optional JWT bearer token for authentication
            disabled_tools: Optional list of tool names to disable
        """
        server_config = {
            "type": "streamable-http",
            "url": url,
        }

        if auth_token:
            server_config["headers"] = {"Authorization": f"Bearer {auth_token}"}  # type: ignore[assignment]

        if disabled_tools:
            server_config["disabledTools"] = disabled_tools  # type: ignore[assignment]

        self.servers[name] = server_config

    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        return {"mcpServers": self.servers}

    def to_json(self, indent: int = 2) -> str:
        """Convert configuration to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: Path) -> None:
        """Save configuration to file"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: Path) -> "MCPOConfig":
        """Load configuration from file"""
        with open(path, "r") as f:
            data = json.load(f)

        config = cls()
        config.servers = data.get("mcpServers", {})
        return config


def create_default_config(
    auth_token: Optional[str] = None,
    mcp_auth_port: int = 8001,
) -> MCPOConfig:
    """
    Create default MCPO configuration for gplot MCP server

    Args:
        auth_token: JWT token for authenticated server
        mcp_auth_port: Port for MCP server (default: 8001)

    Returns:
        MCPOConfig instance
    """
    config = MCPOConfig()

    # Add gplot MCP server
    config.add_server(
        name="gplot",
        url=f"http://localhost:{mcp_auth_port}/mcp",
        auth_token=auth_token,
    )

    return config


def create_public_only_config(mcp_port: int = 8001) -> MCPOConfig:
    """
    Create MCPO configuration for public (no auth) server only

    Args:
        mcp_port: Port for MCP server (default: 8001)

    Returns:
        MCPOConfig instance
    """
    config = MCPOConfig()
    config.add_server(
        name="gplot",
        url=f"http://localhost:{mcp_port}/mcp",
    )
    return config
