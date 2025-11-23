# tests/middleware/test_logging_middleware.py
import pytest
import logging
from pathlib import Path
from deepagent_claude.middleware.logging_middleware import create_logging_middleware

@pytest.mark.asyncio
async def test_logging_middleware_creation():
    """Test creating logging middleware"""
    middleware = create_logging_middleware()
    assert middleware is not None

@pytest.mark.asyncio
async def test_logging_middleware_logs_messages(caplog):
    """Test middleware logs agent messages"""
    with caplog.at_level(logging.INFO):
        middleware = create_logging_middleware()

        state = {
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        }

        result = await middleware(state)
        assert result is not None
        # Check that something was logged
        assert len(caplog.records) > 0

@pytest.mark.asyncio
async def test_logging_middleware_with_file(tmp_path):
    """Test middleware logs to file"""
    log_file = tmp_path / "agent.log"
    middleware = create_logging_middleware(log_file=str(log_file))

    state = {
        "messages": [
            {"role": "user", "content": "Test message"},
            {"role": "assistant", "content": "Response"}
        ]
    }

    await middleware(state)

    # Check file was created and has content
    assert log_file.exists()
    content = log_file.read_text()
    assert len(content) > 0

@pytest.mark.asyncio
async def test_logging_middleware_tracks_state_changes():
    """Test middleware tracks state changes"""
    middleware = create_logging_middleware()

    state = {
        "messages": [{"role": "user", "content": "Hi"}],
        "custom_key": "custom_value"
    }

    result = await middleware(state)
    # Should preserve all state
    assert "messages" in result
    assert "custom_key" in result
    assert result["custom_key"] == "custom_value"

@pytest.mark.asyncio
async def test_logging_middleware_handles_errors_gracefully(caplog):
    """Test middleware continues on logging errors"""
    with caplog.at_level(logging.ERROR):
        middleware = create_logging_middleware()

        # State with problematic data that might cause logging issues
        state = {
            "messages": [
                {"role": "user", "content": None}  # None content
            ]
        }

        # Should not raise exception
        result = await middleware(state)
        assert result is not None
