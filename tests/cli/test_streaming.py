# tests/cli/test_streaming.py
import pytest
import asyncio
from deepagent_claude.cli.streaming import StreamingHandler

@pytest.mark.asyncio
async def test_streaming_handler_creation():
    """Test creating streaming handler"""
    handler = StreamingHandler()
    assert handler is not None

@pytest.mark.asyncio
async def test_streaming_handler_processes_tokens():
    """Test handler processes streaming tokens"""
    handler = StreamingHandler()

    tokens = ["Hello", " ", "World"]
    for token in tokens:
        await handler.on_token(token)

    result = handler.get_accumulated()
    assert result == "Hello World"

@pytest.mark.asyncio
async def test_streaming_handler_with_callback():
    """Test handler with callback function"""
    received = []

    def callback(token):
        received.append(token)

    handler = StreamingHandler(callback=callback)

    await handler.on_token("Test")
    assert "Test" in received

@pytest.mark.asyncio
async def test_streaming_handler_reset():
    """Test resetting handler state"""
    handler = StreamingHandler()

    await handler.on_token("Test")
    handler.reset()

    assert handler.get_accumulated() == ""

@pytest.mark.asyncio
async def test_streaming_handler_with_rate_limit():
    """Test handler respects rate limiting"""
    handler = StreamingHandler(rate_limit=0.01)

    start = asyncio.get_event_loop().time()
    await handler.on_token("Token1")
    await handler.on_token("Token2")
    elapsed = asyncio.get_event_loop().time() - start

    # Should have some delay due to rate limiting
    assert elapsed >= 0.01
