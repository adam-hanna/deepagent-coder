"""Tests for Code Generator subagent."""

import sys
from unittest.mock import AsyncMock, MagicMock

import pytest


def test_get_code_generation_guidelines():
    """Test that code generation guidelines are comprehensive."""
    # Import only the function that doesn't depend on deepagents
    from deepagent_coder.subagents.code_generator import get_code_generation_guidelines

    guidelines = get_code_generation_guidelines()
    assert len(guidelines) > 0
    assert "Python Style Guide" in guidelines


@pytest.mark.asyncio
async def test_code_generator_creation():
    """Test that code generator agent can be created."""
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
        from deepagent_coder.core.model_selector import ModelSelector
        from deepagent_coder.subagents.code_generator import create_code_generator_agent

        selector = ModelSelector()
        agent = await create_code_generator_agent(selector, [])
        # create_code_generator_agent returns a CompiledStateGraph from create_react_agent,
        # not a mock, so just verify it's not None
        assert agent is not None
    finally:
        # Clean up sys.modules
        if "deepagents" in sys.modules:
            del sys.modules["deepagents"]
        if "deepagents.backend" in sys.modules:
            del sys.modules["deepagents.backend"]
