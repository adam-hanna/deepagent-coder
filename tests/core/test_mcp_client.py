# tests/core/test_mcp_client.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from deepagent_claude.core.mcp_client import MCPClientManager


@pytest.mark.asyncio
async def test_mcp_client_initialization():
    """Test MCP client manager initialization"""
    manager = MCPClientManager()

    assert manager is not None
    assert len(manager.server_configs) > 0


@pytest.mark.asyncio
async def test_mcp_client_gets_tools():
    """Test fetching tools from MCP servers"""
    with patch("deepagent_claude.core.mcp_client.MultiServerMCPClient") as MockClient:
        # Create mock tools
        mock_tool1 = MagicMock()
        mock_tool1.name = "python_exec"
        mock_tool1.__str__ = lambda self: "python_exec"

        mock_tool2 = MagicMock()
        mock_tool2.name = "bash_run"
        mock_tool2.__str__ = lambda self: "bash_run"

        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.get_tools = AsyncMock(return_value=[mock_tool1, mock_tool2])
        MockClient.return_value = mock_client_instance

        manager = MCPClientManager()
        await manager.initialize()

        tools = await manager.get_all_tools()

        assert len(tools) > 0
        assert any("python" in str(tool).lower() for tool in tools)


@pytest.mark.asyncio
async def test_mcp_client_by_category():
    """Test getting tools by category"""
    with patch("deepagent_claude.core.mcp_client.MultiServerMCPClient") as MockClient:
        # Create mock tools for python server
        mock_tool = MagicMock()
        mock_tool.name = "python_exec"
        mock_tool.server = "python"
        mock_tool.__str__ = lambda self: "python_exec"

        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.get_tools = AsyncMock(return_value=[mock_tool])
        MockClient.return_value = mock_client_instance

        manager = MCPClientManager()
        await manager.initialize()

        python_tools = await manager.get_tools_by_server("python")

        assert len(python_tools) > 0


@pytest.mark.asyncio
async def test_mcp_client_invalid_server():
    """Test error handling for invalid server name"""
    with patch("deepagent_claude.core.mcp_client.MultiServerMCPClient"):
        manager = MCPClientManager()
        await manager.initialize()

        with pytest.raises(ValueError, match="Unknown server"):
            await manager.get_tools_by_server("nonexistent")


@pytest.mark.asyncio
async def test_add_custom_server():
    """Test adding custom MCP server"""
    manager = MCPClientManager()

    manager.add_server("custom", command="python", args=["/path/to/server.py"])

    assert "custom" in manager.server_configs


@pytest.mark.asyncio
async def test_get_tools_before_initialize():
    """Test that getting tools before initialize raises error"""
    manager = MCPClientManager()

    with pytest.raises(RuntimeError, match="not initialized"):
        await manager.get_all_tools()
