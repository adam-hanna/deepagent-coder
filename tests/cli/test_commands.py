# tests/cli/test_commands.py
import pytest
from deepagent_claude.cli.commands import CommandHandler

@pytest.mark.asyncio
async def test_command_handler_creation():
    """Test creating command handler"""
    handler = CommandHandler()
    assert handler is not None

@pytest.mark.asyncio
async def test_command_handler_help():
    """Test help command"""
    handler = CommandHandler()
    result = await handler.execute("/help")
    assert result is not None
    assert "commands" in str(result).lower() or result.get("help")

@pytest.mark.asyncio
async def test_command_handler_exit():
    """Test exit command"""
    handler = CommandHandler()
    result = await handler.execute("/exit")
    assert result is not None

@pytest.mark.asyncio
async def test_command_handler_unknown_command():
    """Test unknown command handling"""
    handler = CommandHandler()
    result = await handler.execute("/unknown")
    assert result is not None
