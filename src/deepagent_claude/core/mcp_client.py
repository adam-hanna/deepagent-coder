# src/deepagent_claude/core/mcp_client.py
"""MCP Client management for tool integration"""

import logging
from pathlib import Path
import sys
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)


class MCPClientManager:
    """
    Manages MCP server connections and tool access.

    Provides centralized management of multiple MCP servers
    for filesystem, git, python, testing, and linting operations.
    """

    def __init__(
        self, custom_configs: dict[str, dict[str, Any]] | None = None, use_defaults: bool = True
    ):
        """
        Initialize MCP client manager

        Args:
            custom_configs: Optional custom server configurations
            use_defaults: Whether to load default server configs (default: True)
        """
        if custom_configs and not use_defaults:
            # Only use custom configs, no defaults
            self.server_configs = custom_configs
        elif custom_configs:
            # Merge custom with defaults
            self.server_configs = self._get_default_configs()
            self.server_configs.update(custom_configs)
        else:
            # Use defaults only
            self.server_configs = self._get_default_configs()

        self.client: MultiServerMCPClient | None = None
        self._tools_cache: list[Any] | None = None

        logger.info(f"Initialized MCPClientManager with {len(self.server_configs)} servers")

    def _get_default_configs(self) -> dict[str, dict[str, Any]]:
        """Get default MCP server configurations"""
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent.parent

        return {
            "python": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [
                    str(
                        project_root
                        / "src"
                        / "deepagent_claude"
                        / "mcp_servers"
                        / "python_server.py"
                    )
                ],
            },
            "git": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [
                    str(project_root / "src" / "deepagent_claude" / "mcp_servers" / "git_server.py")
                ],
            },
            "testing": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [
                    str(
                        project_root
                        / "src"
                        / "deepagent_claude"
                        / "mcp_servers"
                        / "testing_server.py"
                    )
                ],
            },
            "linting": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [
                    str(
                        project_root
                        / "src"
                        / "deepagent_claude"
                        / "mcp_servers"
                        / "linting_server.py"
                    )
                ],
            },
        }

    async def initialize(self) -> None:
        """
        Initialize MCP client and connect to all servers

        Raises:
            RuntimeError: If client initialization fails
        """
        try:
            logger.info("Initializing MCP client...")

            self.client = MultiServerMCPClient(self.server_configs)

            logger.info("✓ MCP client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            raise RuntimeError(f"MCP client initialization failed: {e}")

    async def get_all_tools(self, use_cache: bool = True) -> list[Any]:
        """
        Get all tools from all MCP servers

        Args:
            use_cache: Use cached tools if available

        Returns:
            List of all available tools

        Raises:
            RuntimeError: If client not initialized
        """
        if self.client is None:
            raise RuntimeError("Client not initialized. Call initialize() first.")

        if use_cache and self._tools_cache is not None:
            return self._tools_cache

        try:
            logger.debug("Fetching tools from MCP servers...")

            tools = await self.client.get_tools()

            self._tools_cache = tools

            logger.info(f"Retrieved {len(tools)} tools from MCP servers")

            return tools

        except Exception as e:
            logger.error(f"Failed to get tools: {e}")
            raise RuntimeError(f"Failed to get MCP tools: {e}")

    async def get_tools_by_server(self, server_name: str) -> list[Any]:
        """
        Get tools from specific MCP server

        Args:
            server_name: Name of the server (python, git, testing, linting)

        Returns:
            List of tools from specified server

        Raises:
            ValueError: If server name not found
        """
        if server_name not in self.server_configs:
            available = ", ".join(self.server_configs.keys())
            raise ValueError(f"Unknown server '{server_name}'. Available: {available}")

        all_tools = await self.get_all_tools()

        # Filter tools by server name (tools include server metadata)
        server_tools = [
            tool for tool in all_tools if hasattr(tool, "server") and tool.server == server_name
        ]

        return server_tools

    def add_server(
        self, name: str, command: str, args: list[str], transport: str = "stdio"
    ) -> None:
        """
        Add a custom MCP server

        Args:
            name: Server name
            command: Command to start server
            args: Command arguments
            transport: Transport type (default: stdio)
        """
        self.server_configs[name] = {"transport": transport, "command": command, "args": args}

        # Clear cache as configuration changed
        self._tools_cache = None

        logger.info(f"Added custom MCP server '{name}'")

    async def close(self) -> None:
        """Close MCP client and cleanup resources"""
        if self.client:
            try:
                # MultiServerMCPClient doesn't have explicit close in current version
                # but we set it to None to allow garbage collection
                self.client = None
                self._tools_cache = None

                logger.info("MCP client closed")

            except Exception as e:
                logger.warning(f"Error closing MCP client: {e}")


# Global default instance
_default_manager = None


async def get_default_manager() -> MCPClientManager:
    """Get or create the default MCPClientManager instance"""
    global _default_manager

    if _default_manager is None:
        _default_manager = MCPClientManager()
        await _default_manager.initialize()

    return _default_manager
