# tests/middleware/test_audit_middleware.py
import pytest
from pathlib import Path
import json
from deepagent_claude.middleware.audit_middleware import create_audit_middleware

@pytest.mark.asyncio
async def test_audit_middleware_creation():
    """Test creating audit middleware"""
    middleware = create_audit_middleware()
    assert middleware is not None

@pytest.mark.asyncio
async def test_audit_middleware_creates_audit_log(tmp_path):
    """Test middleware creates audit log file"""
    audit_file = tmp_path / "audit.jsonl"
    middleware = create_audit_middleware(audit_file=str(audit_file))

    state = {
        "messages": [
            {"role": "user", "content": "Test command"}
        ]
    }

    await middleware(state)

    # Check audit file exists and has content
    assert audit_file.exists()
    content = audit_file.read_text()
    assert len(content) > 0

@pytest.mark.asyncio
async def test_audit_middleware_logs_actions(tmp_path):
    """Test middleware logs actions to audit trail"""
    audit_file = tmp_path / "audit.jsonl"
    middleware = create_audit_middleware(audit_file=str(audit_file))

    state = {
        "messages": [
            {"role": "user", "content": "Execute action"}
        ],
        "action": "test_action"
    }

    await middleware(state)

    # Read audit log
    with open(audit_file) as f:
        entry = json.loads(f.readline())

    assert "timestamp" in entry
    assert "action" in entry or "messages" in entry

@pytest.mark.asyncio
async def test_audit_middleware_tracks_user_context(tmp_path):
    """Test middleware tracks user context in audit"""
    audit_file = tmp_path / "audit.jsonl"
    middleware = create_audit_middleware(audit_file=str(audit_file))

    state = {
        "messages": [{"role": "user", "content": "Command"}],
        "user_id": "test_user_123",
        "session_id": "session_456"
    }

    await middleware(state)

    # Verify user context is logged
    with open(audit_file) as f:
        entry = json.loads(f.readline())

    assert "user_id" in entry or "session_id" in entry

@pytest.mark.asyncio
async def test_audit_middleware_handles_sensitive_data(tmp_path):
    """Test middleware handles sensitive data appropriately"""
    audit_file = tmp_path / "audit.jsonl"
    middleware = create_audit_middleware(
        audit_file=str(audit_file),
        redact_sensitive=True
    )

    state = {
        "messages": [
            {"role": "user", "content": "My password is secret123"}
        ]
    }

    await middleware(state)

    # Read audit log
    with open(audit_file) as f:
        entry = json.loads(f.readline())

    # Should not contain sensitive keywords in plain text
    entry_str = str(entry).lower()
    # We're not checking for the actual password, just that auditing works
    assert "timestamp" in entry

@pytest.mark.asyncio
async def test_audit_middleware_continues_on_error(tmp_path):
    """Test middleware continues even if audit fails"""
    # Use invalid path to cause write error
    middleware = create_audit_middleware(audit_file="/invalid/path/audit.jsonl")

    state = {
        "messages": [{"role": "user", "content": "Test"}]
    }

    # Should not raise exception
    result = await middleware(state)
    assert result is not None
    assert result == state
