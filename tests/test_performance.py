# tests/test_performance.py
import time
from unittest.mock import AsyncMock, patch

import pytest

from deepagent_coder.coding_agent import CodingDeepAgent
from deepagent_coder.core.model_selector import ModelSelector
from deepagent_coder.utils.memory_compactor import MemoryCompactor


@pytest.mark.asyncio
async def test_initialization_time(tmp_path):
    """Test agent initialization completes within time limit"""
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

        start = time.time()
        await agent.initialize()
        elapsed = time.time() - start

        # Should initialize quickly (mock version)
        assert elapsed < 5.0
        assert agent.initialized


@pytest.mark.asyncio
async def test_memory_compaction_performance():
    """Test memory compaction performance"""
    selector = ModelSelector()
    compactor = MemoryCompactor(selector, threshold=1000)

    # Create large message list
    messages = [{"role": "user", "content": "Message " * 100} for _ in range(100)]

    # Test that compaction doesn't take too long
    start = time.time()
    should_compact = compactor.should_compact(messages)
    elapsed = time.time() - start

    assert elapsed < 1.0  # Should be fast
    assert should_compact  # Should trigger


def test_session_manager_performance(tmp_path):
    """Test session manager operations are fast"""
    from deepagent_coder.utils.session_manager import SessionManager

    manager = SessionManager(str(tmp_path))

    # Create session
    start = time.time()
    session_id = manager.create_session()
    elapsed = time.time() - start

    assert elapsed < 0.1  # Should be very fast
    assert session_id is not None

    # Store data
    start = time.time()
    for i in range(100):
        manager.store_session_data(f"key_{i}", {"value": i})
    elapsed = time.time() - start

    assert elapsed < 1.0  # 100 writes should be fast


def test_file_organizer_performance(tmp_path):
    """Test file organizer operations are fast"""
    from deepagent_coder.utils.file_organizer import FileOrganizer

    organizer = FileOrganizer(str(tmp_path))

    # Create standard structure
    start = time.time()
    organizer.create_standard_structure()
    elapsed = time.time() - start

    assert elapsed < 0.1  # Should be very fast

    # Save generated files
    start = time.time()
    for i in range(50):
        organizer.save_generated_file(f"test_{i}.txt", f"Content {i}")
    elapsed = time.time() - start

    assert elapsed < 2.0  # 50 file writes should complete quickly
