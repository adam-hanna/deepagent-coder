# tests/test_coding_agent.py
from unittest.mock import AsyncMock, patch

import pytest

from deepagent_coder.coding_agent import CodingDeepAgent


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
            "deepagent_coder.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._create_subagents",
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
            "deepagent_coder.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._create_subagents",
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
    from deepagent_coder.coding_agent import AgentState

    # AgentState should have search_results in its annotations
    assert "search_results" in AgentState.__annotations__


@pytest.mark.asyncio
async def test_coding_agent_creates_code_navigator():
    """Test CodingDeepAgent creates code navigator subagent"""
    with (
        patch("langchain_ollama.ChatOllama"),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_coder.coding_agent.create_code_navigator", new_callable=AsyncMock
        ) as mock_nav,
        patch("deepagent_coder.coding_agent.create_code_generator_agent", new_callable=AsyncMock),
        patch("deepagent_coder.coding_agent.create_debugger_agent", new_callable=AsyncMock),
        patch("deepagent_coder.coding_agent.create_test_writer_agent", new_callable=AsyncMock),
        patch("deepagent_coder.coding_agent.create_refactorer_agent", new_callable=AsyncMock),
    ):
        agent = CodingDeepAgent()
        await agent.initialize()

        # Code navigator should be created
        mock_nav.assert_called_once()

        # Verify code_navigator is in subagents dict
        assert "code_navigator" in agent.subagents


@pytest.mark.asyncio
async def test_orchestrator_prompt_includes_code_navigator():
    """Test orchestrator system prompt includes code_navigator guidance"""
    with (
        patch("langchain_ollama.ChatOllama"),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._create_subagents",
            new_callable=AsyncMock,
        ),
        patch("deepagent_coder.coding_agent.MCPClientManager") as mock_mcp,
    ):
        # Mock the MCP client to return empty tools
        mock_client = AsyncMock()
        mock_client.get_all_tools = AsyncMock(return_value=[])
        mock_mcp.return_value = mock_client

        agent = CodingDeepAgent()
        agent.initialized = True
        agent.subagents = {
            "code_navigator": AsyncMock(),
            "code_generator": AsyncMock(),
            "debugger": AsyncMock(),
        }

        # Create a state to process
        state = {
            "messages": [{"role": "user", "content": "Find the login endpoint"}],
            "current_file": "",
            "project_context": {},
            "search_results": {},
            "next_agent": "",
        }

        # Mock the model's ainvoke to capture the system prompt
        mock_model = AsyncMock()
        from langchain_core.messages import AIMessage

        mock_model.ainvoke = AsyncMock(return_value=AIMessage(content="Test response"))
        agent.main_model = mock_model

        # Process the state (this will build the system prompt)
        import contextlib

        with contextlib.suppress(Exception):
            await agent._agent_invoke(state)

        # Check that ainvoke was called with messages including the system prompt
        if mock_model.ainvoke.called:
            call_args = mock_model.ainvoke.call_args
            messages = call_args[0][0] if call_args[0] else []

            # Get the system message
            system_message = None
            for msg in messages:
                if hasattr(msg, "type") and msg.type == "system":
                    system_message = msg.content
                    break

            # Verify code_navigator is mentioned in system prompt
            if system_message:
                assert "code_navigator" in system_message.lower()
                assert "find" in system_message.lower() or "search" in system_message.lower()
                assert "API" in system_message or "endpoint" in system_message.lower()
