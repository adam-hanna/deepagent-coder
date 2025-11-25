# tests/test_coding_agent.py
from unittest.mock import AsyncMock, patch

import pytest

from deepagent_claude.coding_agent import CodingDeepAgent


@pytest.mark.asyncio
async def test_coding_agent_creation():
    """Test creating coding agent"""
    with patch("langchain_ollama.ChatOllama"):
        agent = CodingDeepAgent()
        assert agent is not None


@pytest.mark.asyncio
async def test_coding_agent_initialization():
    """Test agent initialization"""
    with (
        patch("langchain_ollama.ChatOllama"),
        patch(
            "deepagent_claude.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_claude.coding_agent.CodingDeepAgent._create_subagents",
            new_callable=AsyncMock,
        ),
    ):
        agent = CodingDeepAgent()
        await agent.initialize()
        assert agent.initialized


@pytest.mark.asyncio
async def test_coding_agent_process_request():
    """Test processing user request"""
    with (
        patch("langchain_ollama.ChatOllama"),
        patch(
            "deepagent_claude.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_claude.coding_agent.CodingDeepAgent._create_subagents",
            new_callable=AsyncMock,
        ),
    ):
        agent = CodingDeepAgent()
        agent.initialized = True
        agent.agent = AsyncMock()
        agent.agent.ainvoke.return_value = {
            "messages": [{"role": "assistant", "content": "Response"}]
        }

        result = await agent.process_request("Test request")
        assert result is not None


def test_agent_state_includes_search_results():
    """Test AgentState has search_results field"""
    from deepagent_claude.coding_agent import AgentState

    # AgentState should have search_results in its annotations
    assert "search_results" in AgentState.__annotations__


@pytest.mark.asyncio
async def test_coding_agent_creates_code_navigator():
    """Test CodingDeepAgent creates code navigator subagent"""
    with (
        patch("langchain_ollama.ChatOllama"),
        patch("deepagent_claude.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock),
        patch("deepagent_claude.coding_agent.create_code_navigator", new_callable=AsyncMock) as mock_nav,
        patch("deepagent_claude.coding_agent.create_code_generator_agent", new_callable=AsyncMock),
        patch("deepagent_claude.coding_agent.create_debugger_agent", new_callable=AsyncMock),
        patch("deepagent_claude.coding_agent.create_test_writer_agent", new_callable=AsyncMock),
        patch("deepagent_claude.coding_agent.create_refactorer_agent", new_callable=AsyncMock),
    ):
        agent = CodingDeepAgent()
        await agent.initialize()

        # Code navigator should be created
        mock_nav.assert_called_once()

        # Verify code_navigator is in subagents dict
        assert "code_navigator" in agent.subagents
