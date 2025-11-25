# tests/middleware/test_git_safety_middleware.py
import pytest

from deepagent_coder.middleware.git_safety_middleware import create_git_safety_middleware


@pytest.mark.asyncio
async def test_git_safety_middleware_creation():
    """Test creating git safety middleware"""
    middleware = create_git_safety_middleware()
    assert middleware is not None


@pytest.mark.asyncio
async def test_git_safety_warns_on_unsafe_operations():
    """Test middleware warns on unsafe git operations"""
    middleware = create_git_safety_middleware()

    state = {"messages": [{"role": "user", "content": "force push to main"}]}

    original_length = len(state["messages"])

    result = await middleware(state)
    # Should add warning message
    assert len(result["messages"]) > original_length
    assert len(result["messages"]) == 2  # Original + warning


@pytest.mark.asyncio
async def test_git_safety_blocks_when_enforced():
    """Test middleware blocks operations when enforce=True"""
    middleware = create_git_safety_middleware(enforce=True)

    state = {"messages": [{"role": "user", "content": "git push --force origin main"}]}

    result = await middleware(state)
    assert "git_operation_blocked" in result
    assert result["git_operation_blocked"] is True


@pytest.mark.asyncio
async def test_git_safety_detects_hard_reset():
    """Test detection of git reset --hard"""
    middleware = create_git_safety_middleware()

    state = {"messages": [{"role": "user", "content": "git reset --hard HEAD~5"}]}

    result = await middleware(state)
    assert len(result["messages"]) > 1
    # Check that warning was added
    assert any("WARNING" in msg.get("content", "") for msg in result["messages"])


@pytest.mark.asyncio
async def test_git_safety_allows_safe_operations():
    """Test that safe git operations pass through"""
    middleware = create_git_safety_middleware()

    state = {"messages": [{"role": "user", "content": "git commit -m 'safe commit'"}]}

    result = await middleware(state)
    # Should not add any warnings for safe operations
    assert len(result["messages"]) == len(state["messages"])


@pytest.mark.asyncio
async def test_git_safety_handles_empty_messages():
    """Test middleware handles empty message list"""
    middleware = create_git_safety_middleware()

    state = {"messages": []}

    result = await middleware(state)
    assert result["messages"] == []
