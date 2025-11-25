"""
File Organizer - Manages file system organization for DeepAgent Claude.

This module provides structured file and directory management for storing
agent sessions, decisions, summaries, and generated content. It creates
and maintains a standard directory structure with organized data persistence.

Key features:
- Standard directory structure creation
- Session data persistence (JSON)
- Decision log storage
- Summary archiving
- Generated content organization

Example:
    organizer = FileOrganizer()
    organizer.create_standard_structure()

    # Save session
    path = organizer.save_session_data("session_123", session_data)

    # Load session
    data = organizer.load_session_data("session_123")
"""

from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class FileOrganizer:
    """
    Manages file system organization for DeepAgent Claude.

    Creates and maintains a structured directory hierarchy for storing
    various types of agent data. Provides convenient methods for saving
    and loading structured data in JSON format.

    Attributes:
        base_path: Base directory for all organized files
    """

    def __init__(self, base_path: str | None = None):
        """
        Initialize FileOrganizer with base directory.

        Args:
            base_path: Base directory path. If None, uses ~/.deepagent_coder
        """
        if base_path is None:
            base_path = str(Path.home() / ".deepagent_coder")

        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"FileOrganizer initialized with base_path: {self.base_path}")

    def create_standard_structure(self) -> None:
        """
        Create standard directory structure for organized file storage.

        Creates the following directories:
        - sessions/: Session data and conversation history
        - decisions/: Decision logs and reasoning traces
        - summaries/: Conversation summaries and compactions
        - generated/: Generated code, documents, and artifacts
        - logs/: Application and agent logs
        """
        dirs = ["sessions", "decisions", "summaries", "generated", "logs"]

        for dir_name in dirs:
            dir_path = self.base_path / dir_name
            dir_path.mkdir(exist_ok=True)
            logger.debug(f"Created directory: {dir_path}")

        logger.info("Standard directory structure created")

    def save_session_data(self, session_id: str, data: dict[str, Any]) -> Path:
        """
        Save session data to JSON file.

        Args:
            session_id: Unique identifier for the session
            data: Session data dictionary to save

        Returns:
            Path: Path to saved file

        Example:
            path = organizer.save_session_data("sess_123", {
                "user": "alice",
                "created_at": "2024-01-15",
                "messages": [...]
            })
        """
        path = self.base_path / "sessions" / f"{session_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved session data to: {path}")
        return path

    def load_session_data(self, session_id: str) -> dict[str, Any] | None:
        """
        Load session data from JSON file.

        Args:
            session_id: Unique identifier for the session

        Returns:
            Optional[Dict[str, Any]]: Session data if found, None otherwise

        Example:
            data = organizer.load_session_data("sess_123")
            if data:
                print(f"Session created at: {data['created_at']}")
        """
        path = self.base_path / "sessions" / f"{session_id}.json"

        if not path.exists():
            logger.warning(f"Session data not found: {session_id}")
            return None

        with open(path) as f:
            data = json.load(f)

        logger.info(f"Loaded session data from: {path}")
        return data

    def save_decision_log(self, decision_id: str, decision_data: dict[str, Any]) -> Path:
        """
        Save decision log to JSON file.

        Args:
            decision_id: Unique identifier for the decision
            decision_data: Decision data to save

        Returns:
            Path: Path to saved file
        """
        path = self.base_path / "decisions" / f"{decision_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        # Add timestamp if not present
        if "timestamp" not in decision_data:
            decision_data["timestamp"] = datetime.now().isoformat()

        with open(path, "w") as f:
            json.dump(decision_data, f, indent=2)

        logger.info(f"Saved decision log to: {path}")
        return path

    def load_decision_log(self, decision_id: str) -> dict[str, Any] | None:
        """
        Load decision log from JSON file.

        Args:
            decision_id: Unique identifier for the decision

        Returns:
            Optional[Dict[str, Any]]: Decision data if found, None otherwise
        """
        path = self.base_path / "decisions" / f"{decision_id}.json"

        if not path.exists():
            logger.warning(f"Decision log not found: {decision_id}")
            return None

        with open(path) as f:
            data = json.load(f)

        logger.info(f"Loaded decision log from: {path}")
        return data

    def save_summary(
        self, summary_id: str, summary_text: str, metadata: dict[str, Any] | None = None
    ) -> Path:
        """
        Save conversation summary to file.

        Args:
            summary_id: Unique identifier for the summary
            summary_text: Summary text content
            metadata: Optional metadata about the summary

        Returns:
            Path: Path to saved file
        """
        path = self.base_path / "summaries" / f"{summary_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        summary_data = {
            "summary_id": summary_id,
            "text": summary_text,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        with open(path, "w") as f:
            json.dump(summary_data, f, indent=2)

        logger.info(f"Saved summary to: {path}")
        return path

    def load_summary(self, summary_id: str) -> dict[str, Any] | None:
        """
        Load conversation summary from file.

        Args:
            summary_id: Unique identifier for the summary

        Returns:
            Optional[Dict[str, Any]]: Summary data if found, None otherwise
        """
        path = self.base_path / "summaries" / f"{summary_id}.json"

        if not path.exists():
            logger.warning(f"Summary not found: {summary_id}")
            return None

        with open(path) as f:
            data = json.load(f)

        logger.info(f"Loaded summary from: {path}")
        return data

    def save_generated_file(
        self, filename: str, content: str, subdirectory: str | None = None
    ) -> Path:
        """
        Save generated content to file.

        Args:
            filename: Name of the file to save
            content: File content
            subdirectory: Optional subdirectory within generated/

        Returns:
            Path: Path to saved file
        """
        if subdirectory:
            path = self.base_path / "generated" / subdirectory / filename
        else:
            path = self.base_path / "generated" / filename

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(content)

        logger.info(f"Saved generated file to: {path}")
        return path

    def list_sessions(self) -> list[str]:
        """
        List all saved session IDs.

        Returns:
            List[str]: List of session IDs
        """
        sessions_dir = self.base_path / "sessions"
        if not sessions_dir.exists():
            return []

        session_files = sessions_dir.glob("*.json")
        session_ids = [f.stem for f in session_files]

        logger.debug(f"Found {len(session_ids)} sessions")
        return sorted(session_ids)

    def list_decisions(self) -> list[str]:
        """
        List all saved decision IDs.

        Returns:
            List[str]: List of decision IDs
        """
        decisions_dir = self.base_path / "decisions"
        if not decisions_dir.exists():
            return []

        decision_files = decisions_dir.glob("*.json")
        decision_ids = [f.stem for f in decision_files]

        logger.debug(f"Found {len(decision_ids)} decisions")
        return sorted(decision_ids)

    def cleanup_old_files(self, days: int = 30) -> int:
        """
        Clean up files older than specified number of days.

        Args:
            days: Number of days to keep files (default: 30)

        Returns:
            int: Number of files deleted
        """
        from time import time

        cutoff_time = time() - (days * 24 * 60 * 60)
        deleted_count = 0

        for dir_name in ["sessions", "decisions", "summaries", "generated"]:
            dir_path = self.base_path / dir_name
            if not dir_path.exists():
                continue

            for file_path in dir_path.rglob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old file: {file_path}")

        logger.info(f"Cleaned up {deleted_count} files older than {days} days")
        return deleted_count

    def get_storage_stats(self) -> dict[str, Any]:
        """
        Get storage statistics for organized files.

        Returns:
            Dict[str, Any]: Statistics including file counts and sizes
        """
        stats = {"base_path": str(self.base_path), "directories": {}}

        for dir_name in ["sessions", "decisions", "summaries", "generated", "logs"]:
            dir_path = self.base_path / dir_name
            if not dir_path.exists():
                stats["directories"][dir_name] = {"count": 0, "size_bytes": 0}
                continue

            files = list(dir_path.rglob("*"))
            file_count = sum(1 for f in files if f.is_file())
            total_size = sum(f.stat().st_size for f in files if f.is_file())

            stats["directories"][dir_name] = {"count": file_count, "size_bytes": total_size}

        logger.debug(f"Storage stats: {stats}")
        return stats
