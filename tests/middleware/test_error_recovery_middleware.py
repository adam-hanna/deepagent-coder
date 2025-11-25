# tests/middleware/test_error_recovery_middleware.py
import pytest

from deepagent_coder.middleware.error_recovery_middleware import create_error_recovery_middleware


@pytest.mark.asyncio
async def test_error_recovery_middleware_creation():
    """Test creating error recovery middleware"""
    middleware = create_error_recovery_middleware()
    assert middleware is not None


@pytest.mark.asyncio
async def test_error_recovery_passes_through_normal_state():
    """Test middleware passes through normal state"""
    middleware = create_error_recovery_middleware()

    state = {"messages": [{"role": "user", "content": "Hello"}]}

    result = await middleware(state)
    assert result == state
    assert "error_count" not in result


@pytest.mark.asyncio
async def test_error_recovery_tracks_retry_count():
    """Test middleware tracks retry attempts"""
    middleware = create_error_recovery_middleware(max_retries=3)

    state = {"messages": [{"role": "user", "content": "Test"}], "error": "Something went wrong"}

    result = await middleware(state)
    assert "retry_count" in result
    assert result["retry_count"] == 1


@pytest.mark.asyncio
async def test_error_recovery_adds_recovery_message():
    """Test middleware adds recovery message on error"""
    middleware = create_error_recovery_middleware()

    state = {"messages": [{"role": "user", "content": "Test"}], "error": "Connection failed"}

    result = await middleware(state)
    # Should add recovery guidance
    messages = result.get("messages", [])
    assert len(messages) > 1
    assert any("error" in msg.get("content", "").lower() for msg in messages)


@pytest.mark.asyncio
async def test_error_recovery_respects_max_retries():
    """Test middleware respects maximum retry limit"""
    middleware = create_error_recovery_middleware(max_retries=2)

    state = {
        "messages": [{"role": "user", "content": "Test"}],
        "error": "Persistent error",
        "retry_count": 2,
    }

    result = await middleware(state)
    # Should indicate max retries reached
    assert result.get("max_retries_reached") is True


@pytest.mark.asyncio
async def test_error_recovery_clears_error_on_success():
    """Test middleware clears error state on success"""
    middleware = create_error_recovery_middleware()

    # First call with error
    state = {
        "messages": [{"role": "user", "content": "Test"}],
        "error": "Temporary error",
        "retry_count": 1,
    }

    result = await middleware(state)
    assert "retry_count" in result

    # Second call without error (success)
    state2 = {"messages": [{"role": "user", "content": "Success"}], "retry_count": 1}

    result2 = await middleware(state2)
    # Retry count should not increase without error
    assert result2.get("retry_count", 0) <= 1
