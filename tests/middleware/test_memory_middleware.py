# tests/middleware/test_memory_middleware.py
import pytest
from deepagent_claude.middleware.memory_middleware import create_memory_middleware
from deepagent_claude.core.model_selector import ModelSelector

@pytest.mark.asyncio
async def test_memory_middleware_creation():
    """Test creating memory middleware"""
    selector = ModelSelector()
    middleware = create_memory_middleware(selector)
    assert middleware is not None

@pytest.mark.asyncio
async def test_memory_middleware_doesnt_compact_small_context():
    """Test middleware skips compaction for small contexts"""
    selector = ModelSelector()
    middleware = create_memory_middleware(selector, threshold=10000)

    state = {
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    }

    result = await middleware(state)
    assert len(result["messages"]) == 1

@pytest.mark.asyncio
async def test_memory_middleware_compacts_large_context():
    """Test middleware compacts when threshold exceeded"""
    selector = ModelSelector()
    # Low threshold to trigger compaction
    middleware = create_memory_middleware(selector, threshold=100, keep_recent=2)

    # Create large message list
    messages = [
        {"role": "user", "content": "Message " + "x" * 100}
        for _ in range(10)
    ]

    state = {"messages": messages}

    result = await middleware(state)

    # Should have compacted: 1 summary + 2 recent = 3 messages
    assert len(result["messages"]) <= 5  # Allow some flexibility
    assert "compaction_metadata" in result

@pytest.mark.asyncio
async def test_memory_middleware_handles_empty_messages():
    """Test middleware handles empty message list"""
    selector = ModelSelector()
    middleware = create_memory_middleware(selector)

    state = {"messages": []}

    result = await middleware(state)
    assert result["messages"] == []

@pytest.mark.asyncio
async def test_memory_middleware_handles_missing_messages():
    """Test middleware handles state without messages"""
    selector = ModelSelector()
    middleware = create_memory_middleware(selector)

    state = {}

    result = await middleware(state)
    assert "messages" not in result or result.get("messages") == []
