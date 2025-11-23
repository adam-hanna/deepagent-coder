import pytest
from deepagent_claude.utils.session_manager import SessionManager

def test_session_manager_initialization():
    manager = SessionManager()
    assert manager is not None
    assert manager.current_session_id is not None

def test_create_new_session():
    manager = SessionManager()
    session_id = manager.create_session()
    assert session_id is not None
    assert len(session_id) > 0

def test_get_current_session():
    manager = SessionManager()
    session = manager.get_current_session()
    assert session is not None
    assert "session_id" in session
    assert "created_at" in session
