# tests/core/test_session_manager.py
from deepagent_coder.utils.session_manager import SessionManager


def test_session_manager_creates_session(tmp_path):
    """Test creating new session"""
    manager = SessionManager(str(tmp_path))
    session_id = manager.create_session()

    assert session_id is not None
    assert len(session_id) > 0
    assert manager.current_session_id == session_id


def test_session_manager_stores_session_data(tmp_path):
    """Test storing session data"""
    manager = SessionManager(str(tmp_path))
    session_id = manager.create_session()

    manager.store_session_data("test_key", {"value": "test"})

    data = manager.get_session_data("test_key")
    assert data == {"value": "test"}


def test_session_manager_lists_sessions(tmp_path):
    """Test listing all sessions"""
    manager = SessionManager(str(tmp_path))

    session1 = manager.create_session()
    session2 = manager.create_session()

    sessions = manager.list_sessions()
    assert len(sessions) >= 2
