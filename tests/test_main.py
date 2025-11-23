# tests/test_main.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from deepagent_claude.main import create_app, run_single_request

@pytest.mark.asyncio
async def test_create_app():
    """Test creating app instance"""
    with patch('deepagent_claude.main.CodingDeepAgent') as MockAgent:
        mock_agent = AsyncMock()
        mock_agent.initialize = AsyncMock()
        mock_agent.get_workspace_path.return_value = "/tmp/workspace"
        MockAgent.return_value = mock_agent

        app = await create_app()
        assert app is not None

@pytest.mark.asyncio
async def test_run_single_request():
    """Test running single request"""
    with patch('deepagent_claude.main.CodingDeepAgent') as MockAgent:
        mock_agent = AsyncMock()
        mock_agent.process_request.return_value = {"messages": [{"role": "assistant", "content": "Response"}]}
        MockAgent.return_value = mock_agent

        result = await run_single_request("Test request")
        assert result is not None
