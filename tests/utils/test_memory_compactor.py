import pytest
from deepagent_claude.utils.memory_compactor import MemoryCompactor
from deepagent_claude.core.model_selector import ModelSelector

def test_memory_compactor_initialization():
    selector = ModelSelector()
    compactor = MemoryCompactor(selector)
    assert compactor is not None
    assert compactor.threshold == 6000

@pytest.mark.asyncio
async def test_compact_conversation():
    selector = ModelSelector()
    compactor = MemoryCompactor(selector)
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "I'm doing well, thanks!"},
        {"role": "user", "content": "What can you help me with?"},
        {"role": "assistant", "content": "I can help with many things"},
        {"role": "user", "content": "That's great"},
        {"role": "assistant", "content": "Let me know how I can assist"},
    ]
    summary = await compactor.compact_conversation(messages, keep_recent=2)
    assert isinstance(summary, str)
    assert len(summary) > 0

def test_should_compact_returns_false_below_threshold():
    selector = ModelSelector()
    compactor = MemoryCompactor(selector, threshold=1000)
    messages = [{"role": "user", "content": "Short"}]
    assert not compactor.should_compact(messages)

def test_should_compact_returns_true_above_threshold():
    selector = ModelSelector()
    compactor = MemoryCompactor(selector, threshold=10)
    messages = [{"role": "user", "content": "Long " * 100}]
    assert compactor.should_compact(messages)
