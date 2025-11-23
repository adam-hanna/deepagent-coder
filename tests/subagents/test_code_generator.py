"""Tests for Code Generator subagent."""

import pytest
from deepagent_claude.subagents.code_generator import (
    create_code_generator_agent,
    get_code_generation_guidelines,
)
from deepagent_claude.core.model_selector import ModelSelector


@pytest.mark.asyncio
async def test_code_generator_creation():
    """Test that code generator agent can be created."""
    selector = ModelSelector()
    agent = await create_code_generator_agent(selector, [])
    assert agent is not None


def test_get_code_generation_guidelines():
    """Test that code generation guidelines are comprehensive."""
    guidelines = get_code_generation_guidelines()
    assert len(guidelines) > 0
    assert "Python Style Guide" in guidelines
