# tests/integration/test_e2e.py
from unittest.mock import AsyncMock, patch

import pytest

from deepagent_coder.cli.chat_mode import ChatMode
from deepagent_coder.coding_agent import CodingDeepAgent


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow(tmp_path):
    """Test complete workflow from initialization to request processing"""
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

        # Create agent
        agent = CodingDeepAgent(workspace=str(tmp_path))

        # Initialize
        await agent.initialize()
        assert agent.initialized

        # Process request
        result = await agent.process_request("Write a hello world function")
        assert result is not None
        assert "messages" in result

        # Verify workspace files
        assert agent.get_workspace_path().exists()

        # Cleanup
        await agent.cleanup()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_middleware_integration(tmp_path):
    """Test middleware stack integration"""
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

        agent = CodingDeepAgent(workspace=str(tmp_path))
        await agent.initialize()

        # Process request that should trigger middleware
        result = await agent.process_request("git push --force origin main")

        # Should have warning from git safety middleware
        messages = result.get("messages", [])
        assert any("WARNING" in str(msg.get("content", "")) for msg in messages)

        await agent.cleanup()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_persistence(tmp_path):
    """Test session data persistence"""
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

        agent = CodingDeepAgent(workspace=str(tmp_path))
        await agent.initialize()

        # Process request
        await agent.process_request("Test request")

        # Verify session data was stored
        session_data = agent.session_manager.get_session_data("last_request")
        assert session_data is not None

        await agent.cleanup()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_chat_mode_integration():
    """Test chat mode with agent integration"""
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

        mock_agent = AsyncMock()
        mock_agent.ainvoke.return_value = {
            "messages": [{"role": "assistant", "content": "Response"}]
        }

        chat = ChatMode(agent=mock_agent)

        # Process regular message
        result = await chat.process_input("Hello")
        assert result is not None

        # Process command
        result = await chat.process_input("/help")
        assert result is not None

        # Exit
        await chat.process_input("/exit")
        assert chat.should_exit()
