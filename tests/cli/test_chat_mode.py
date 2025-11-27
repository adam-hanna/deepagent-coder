# tests/cli/test_chat_mode.py
from unittest.mock import AsyncMock

import pytest

from deepagent_coder.cli.chat_mode import ChatMode


@pytest.mark.asyncio
async def test_chat_mode_creation():
    """Test creating chat mode"""
    chat = ChatMode()
    assert chat is not None


@pytest.mark.asyncio
async def test_chat_mode_process_command():
    """Test processing user command"""
    chat = ChatMode()
    result = await chat.process_input("/help")
    assert result is not None


@pytest.mark.asyncio
async def test_chat_mode_exit_command():
    """Test exit command"""
    chat = ChatMode()
    result = await chat.process_input("/exit")
    assert chat.should_exit()


@pytest.mark.asyncio
async def test_chat_mode_handles_regular_input():
    """Test handling regular user input"""
    mock_agent = AsyncMock()
    mock_agent.process_request.return_value = {
        "messages": [{"role": "assistant", "content": "Response"}]
    }

    chat = ChatMode(agent=mock_agent)
    result = await chat.process_input("Hello")
    assert result is not None
    mock_agent.process_request.assert_called_once_with("Hello")
