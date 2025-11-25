# tests/subagents/test_code_navigator.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from deepagent_claude.subagents.code_navigator import (
    create_code_navigator,
    get_code_navigator_prompt,
)


@pytest.mark.asyncio
async def test_create_code_navigator():
    """Test creating code navigator subagent"""
    mock_llm = MagicMock()

    with (
        patch("deepagent_claude.subagents.code_navigator.create_react_agent") as mock_create,
        patch("deepagent_claude.subagents.code_navigator.MultiServerMCPClient") as mock_mcp_class,
    ):
        # Setup mock client instance
        mock_client_instance = MagicMock()
        mock_client_instance.initialize = AsyncMock()
        mock_client_instance.get_tools = AsyncMock(return_value=[])
        mock_mcp_class.return_value = mock_client_instance

        mock_create.return_value = AsyncMock()

        agent = await create_code_navigator(mock_llm)

        assert agent is not None
        mock_create.assert_called_once()


def test_get_code_navigator_prompt():
    """Test code navigator prompt is comprehensive"""
    prompt = get_code_navigator_prompt()

    assert isinstance(prompt, str)
    assert len(prompt) > 100

    # Check for key search strategies
    assert "grep" in prompt.lower()
    assert "find" in prompt.lower()
    assert "API" in prompt or "endpoint" in prompt
    assert "database" in prompt.lower()
    assert "function" in prompt.lower()


@pytest.mark.asyncio
async def test_code_navigator_with_mcp_client():
    """Test code navigator integrates with MCP client"""
    mock_llm = MagicMock()

    with (
        patch("deepagent_claude.subagents.code_navigator.create_react_agent") as mock_create,
        patch("deepagent_claude.subagents.code_navigator.MultiServerMCPClient") as mock_mcp_class,
    ):
        # Setup mock client instance
        mock_client_instance = MagicMock()
        mock_client_instance.initialize = AsyncMock()
        mock_client_instance.get_tools = AsyncMock(return_value=[])
        mock_mcp_class.return_value = mock_client_instance

        mock_create.return_value = AsyncMock()

        agent = await create_code_navigator(mock_llm)

        assert agent is not None
