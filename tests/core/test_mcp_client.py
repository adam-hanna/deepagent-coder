# tests/core/test_mcp_client.py
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
    manager = MCPClientManager()
    await manager.initialize()

    tools = await manager.get_all_tools()

    assert len(tools) > 0
    assert any("python" in str(tool).lower() for tool in tools)

@pytest.mark.asyncio
async def test_mcp_client_by_category():
    """Test getting tools by category"""
    manager = MCPClientManager()
    await manager.initialize()

    python_tools = await manager.get_tools_by_server("python")

    assert len(python_tools) > 0

@pytest.mark.asyncio
async def test_mcp_client_invalid_server():
    """Test error handling for invalid server name"""
    manager = MCPClientManager()
    await manager.initialize()

    with pytest.raises(ValueError, match="Unknown server"):
        await manager.get_tools_by_server("nonexistent")

@pytest.mark.asyncio
async def test_add_custom_server():
    """Test adding custom MCP server"""
    manager = MCPClientManager()

    manager.add_server(
        "custom",
        command="python",
        args=["/path/to/server.py"]
    )

    assert "custom" in manager.server_configs

@pytest.mark.asyncio
async def test_get_tools_before_initialize():
    """Test that getting tools before initialize raises error"""
    manager = MCPClientManager()

    with pytest.raises(RuntimeError, match="not initialized"):
        await manager.get_all_tools()
