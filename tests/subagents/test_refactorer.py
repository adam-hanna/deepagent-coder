"""Tests for Refactorer subagent."""

import pytest
import sys
from unittest.mock import AsyncMock, MagicMock


def test_refactorer_module_exists():
    """Test that refactorer module can be imported."""
    from deepagent_claude.subagents import refactorer

    assert refactorer is not None


@pytest.mark.asyncio
async def test_refactorer_creation():
    """Test that refactorer agent can be created."""
    # Mock deepagents modules to avoid import issues
    mock_agent = MagicMock()
    mock_async_create = AsyncMock(return_value=mock_agent)
    mock_backend = MagicMock()

    # Create mock modules for deepagents
    mock_deepagents = MagicMock()
    mock_deepagents.async_create_deep_agent = mock_async_create

    mock_deepagents_backend = MagicMock()
    mock_deepagents_backend.LocalFileSystemBackend = mock_backend

    # Inject mocks into sys.modules before import
    sys.modules["deepagents"] = mock_deepagents
    sys.modules["deepagents.backend"] = mock_deepagents_backend

    try:
        from deepagent_claude.subagents.refactorer import create_refactorer_agent
        from deepagent_claude.core.model_selector import ModelSelector

        selector = ModelSelector()
        agent = await create_refactorer_agent(selector, [])
        assert agent is not None
        assert agent == mock_agent
    finally:
        # Clean up sys.modules
        if "deepagents" in sys.modules:
            del sys.modules["deepagents"]
        if "deepagents.backend" in sys.modules:
            del sys.modules["deepagents.backend"]
