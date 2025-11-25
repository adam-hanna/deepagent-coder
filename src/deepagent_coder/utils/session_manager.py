"""Session management for persistent state"""

from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any
import uuid

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages agent sessions with persistent state.

    Each session has:
    - Unique identifier
    - Creation timestamp
    - Session data store
    - File organization
    - Message history

    Auto-creates a session on initialization if none provided.
    """

    def __init__(self, base_path: str | None = None):
        """
        Initialize session manager

        Args:
            base_path: Root directory for sessions (default: ~/.deepagents/sessions)
        """
        if base_path is None:
            base_path = str(Path.home() / ".deepagents" / "sessions")

        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.current_session_id: str | None = None
        self._current_session_path: Path | None = None

        # Auto-create initial session
        self.create_session()

        logger.info(f"Session manager initialized at {self.base_path}")

    def create_session(self, session_id: str | None = None) -> str:
        """
        Create new session

        Args:
            session_id: Optional custom session ID (generated if not provided)

        Returns:
            Session identifier
        """
        if session_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            session_id = f"session_{timestamp}_{unique_id}"

        session_path = self.base_path / session_id
        session_path.mkdir(parents=True, exist_ok=True)

        # Create session metadata
        metadata = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
        }

        metadata_path = session_path / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        self.current_session_id = session_id
        self._current_session_path = session_path

        logger.info(f"Created session: {session_id}")

        return session_id

    def get_current_session(self) -> dict[str, Any]:
        """
        Get current session metadata

        Returns:
            Dictionary with session metadata

        Raises:
            RuntimeError: If no active session
        """
        if not self._current_session_path:
            raise RuntimeError("No active session")

        metadata_path = self._current_session_path / "metadata.json"

        if not metadata_path.exists():
            raise RuntimeError("Session metadata not found")

        with open(metadata_path, encoding="utf-8") as f:
            return json.load(f)

    def load_session(self, session_id: str) -> bool:
        """
        Load existing session

        Args:
            session_id: Session identifier to load

        Returns:
            True if session loaded successfully
        """
        session_path = self.base_path / session_id

        if not session_path.exists():
            logger.error(f"Session not found: {session_id}")
            return False

        metadata_path = session_path / "metadata.json"

        if not metadata_path.exists():
            logger.error(f"Session metadata not found: {session_id}")
            return False

        self.current_session_id = session_id
        self._current_session_path = session_path

        logger.info(f"Loaded session: {session_id}")

        return True

    def store_session_data(self, key: str, data: Any) -> None:
        """
        Store data in current session

        Args:
            key: Data key
            data: Data to store (must be JSON serializable)

        Raises:
            RuntimeError: If no active session
        """
        if not self._current_session_path:
            raise RuntimeError("No active session")

        data_path = self._current_session_path / f"{key}.json"

        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Stored session data: {key}")

    def get_session_data(self, key: str) -> Any | None:
        """
        Retrieve data from current session

        Args:
            key: Data key

        Returns:
            Stored data or None if not found

        Raises:
            RuntimeError: If no active session
        """
        if not self._current_session_path:
            raise RuntimeError("No active session")

        data_path = self._current_session_path / f"{key}.json"

        if not data_path.exists():
            return None

        with open(data_path, encoding="utf-8") as f:
            return json.load(f)

    def list_sessions(self) -> list[dict[str, Any]]:
        """
        List all sessions

        Returns:
            List of session metadata dictionaries
        """
        sessions = []

        for session_dir in sorted(self.base_path.iterdir()):
            if not session_dir.is_dir():
                continue

            metadata_path = session_dir / "metadata.json"

            if not metadata_path.exists():
                continue

            try:
                with open(metadata_path, encoding="utf-8") as f:
                    metadata = json.load(f)
                    sessions.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to read session metadata: {e}")

        return sessions

    def close_session(self) -> None:
        """Close current session and update metadata"""
        if not self._current_session_path:
            return

        metadata_path = self._current_session_path / "metadata.json"

        if metadata_path.exists():
            with open(metadata_path, encoding="utf-8") as f:
                metadata = json.load(f)

            metadata["status"] = "closed"
            metadata["closed_at"] = datetime.now().isoformat()

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

        logger.info(f"Closed session: {self.current_session_id}")

        self.current_session_id = None
        self._current_session_path = None

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its data

        Args:
            session_id: Session identifier to delete

        Returns:
            True if session was deleted
        """
        session_path = self.base_path / session_id

        if not session_path.exists():
            return False

        # Delete all files in session
        import shutil

        shutil.rmtree(session_path)

        logger.info(f"Deleted session: {session_id}")

        return True

    def get_session_path(self, subdir: str | None = None) -> Path | None:
        """
        Get path to current session directory or subdirectory

        Args:
            subdir: Optional subdirectory name

        Returns:
            Path to session directory
        """
        if not self._current_session_path:
            return None

        if subdir:
            path = self._current_session_path / subdir
            path.mkdir(parents=True, exist_ok=True)
            return path

        return self._current_session_path
