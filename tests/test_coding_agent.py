# tests/test_coding_agent.py
import pytest
from deepagent_claude.coding_agent import CodingDeepAgent
from unittest.mock import MagicMock, AsyncMock, patch

@pytest.mark.asyncio
async def test_coding_agent_creation():
    """Test creating coding agent"""
    with patch('deepagent_claude.coding_agent.ChatOllama'):
        agent = CodingDeepAgent()
        assert agent is not None

@pytest.mark.asyncio
async def test_coding_agent_initialization():
    """Test agent initialization"""
    with patch('deepagent_claude.coding_agent.ChatOllama'), \
         patch('deepagent_claude.coding_agent.CodingDeepAgent._setup_mcp_tools', new_callable=AsyncMock), \
         patch('deepagent_claude.coding_agent.CodingDeepAgent._create_subagents', new_callable=AsyncMock):
        agent = CodingDeepAgent()
        await agent.initialize()
        assert agent.initialized

@pytest.mark.asyncio
async def test_coding_agent_process_request():
    """Test processing user request"""
    with patch('deepagent_claude.coding_agent.ChatOllama'), \
         patch('deepagent_claude.coding_agent.CodingDeepAgent._setup_mcp_tools', new_callable=AsyncMock), \
         patch('deepagent_claude.coding_agent.CodingDeepAgent._create_subagents', new_callable=AsyncMock):
        agent = CodingDeepAgent()
        agent.initialized = True
        agent.agent = AsyncMock()
        agent.agent.ainvoke.return_value = {"messages": [{"role": "assistant", "content": "Response"}]}

        result = await agent.process_request("Test request")
        assert result is not None
