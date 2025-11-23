"""Audit middleware for compliance and activity tracking"""

from typing import Dict, Any, Callable, Optional
import logging
from pathlib import Path
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)

# Patterns for sensitive data to redact
SENSITIVE_PATTERNS = [
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
    (r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[CARD]'),
    (r'password\s*[:=]\s*\S+', 'password=[REDACTED]'),
    (r'api[_-]?key\s*[:=]\s*\S+', 'api_key=[REDACTED]'),
    (r'token\s*[:=]\s*\S+', 'token=[REDACTED]'),
]


def create_audit_middleware(
    audit_file: Optional[str] = None,
    redact_sensitive: bool = True,
    include_message_content: bool = False
) -> Callable:
    """
    Create audit middleware for compliance logging

    Args:
        audit_file: Path to audit log file (JSONL format)
        redact_sensitive: Whether to redact sensitive data
        include_message_content: Whether to include full message content (can be verbose)

    Returns:
        Middleware function
    """
    # Setup audit file
    if audit_file:
        try:
            audit_path = Path(audit_file)
            audit_path.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not create audit directory: {e}")
            # Continue anyway - will fail gracefully during write

    async def audit_middleware(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log agent actions for audit trail

        Args:
            state: Agent state dictionary

        Returns:
            Unmodified state (auditing is observational)
        """
        try:
            # Build audit entry
            entry = {
                "timestamp": datetime.now().isoformat(),
                "message_count": len(state.get("messages", [])),
            }

            # Add user/session context if present
            if "user_id" in state:
                entry["user_id"] = state["user_id"]
            if "session_id" in state:
                entry["session_id"] = state["session_id"]
            if "action" in state:
                entry["action"] = state["action"]

            # Add message info
            messages = state.get("messages", [])
            if messages:
                last_message = messages[-1]
                entry["last_message_role"] = last_message.get("role", "unknown")

                if include_message_content:
                    content = str(last_message.get("content", ""))
                    if redact_sensitive:
                        content = _redact_sensitive_data(content)
                    entry["last_message_content"] = content[:200]  # Limit length

            # Add special flags
            if state.get("git_operation_blocked"):
                entry["git_operation_blocked"] = True
            if state.get("max_retries_reached"):
                entry["max_retries_reached"] = True
            if state.get("compaction_metadata"):
                entry["memory_compacted"] = True

            # Add state keys (not values)
            entry["state_keys"] = list(state.keys())

            # Write to audit log
            if audit_file:
                _write_audit_entry(audit_file, entry)

            # Also log to standard logger
            logger.info(f"Audit: {entry.get('action', 'activity')} - User: {entry.get('user_id', 'unknown')}")

        except Exception as e:
            # Auditing should never break the agent
            logger.error(f"Error in audit middleware: {e}", exc_info=True)

        return state

    return audit_middleware


def _redact_sensitive_data(text: str) -> str:
    """
    Redact sensitive data from text

    Args:
        text: Text to redact

    Returns:
        Redacted text
    """
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _write_audit_entry(audit_file: str, entry: Dict[str, Any]) -> None:
    """
    Write audit entry to file

    Args:
        audit_file: Path to audit file
        entry: Audit entry dictionary
    """
    try:
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception as e:
        logger.error(f"Failed to write audit entry: {e}")
