"""Logging middleware for comprehensive agent activity tracking"""

from typing import Dict, Any, Callable, Optional
import logging
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)


def create_logging_middleware(
    log_file: Optional[str] = None,
    log_level: int = logging.INFO,
    include_state: bool = False
) -> Callable:
    """
    Create logging middleware for agent activity tracking

    Args:
        log_file: Optional file path for persistent logging
        log_level: Logging level (default: INFO)
        include_state: Whether to log full state (can be verbose)

    Returns:
        Middleware function
    """
    # Configure file handler if log_file specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
        logger.addHandler(file_handler)
        logger.setLevel(log_level)

    async def logging_middleware(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log agent state and activity

        Args:
            state: Agent state dictionary

        Returns:
            Unmodified state (logging is observational)
        """
        try:
            messages = state.get("messages", [])
            message_count = len(messages)

            # Log message activity
            if messages:
                last_message = messages[-1]
                role = last_message.get("role", "unknown")
                content_preview = str(last_message.get("content", ""))[:100]

                logger.info(
                    f"Agent activity - Messages: {message_count}, "
                    f"Last: {role} - {content_preview}..."
                )

            # Log state changes (if enabled)
            if include_state:
                # Log non-message keys
                other_keys = {k: v for k, v in state.items() if k != "messages"}
                if other_keys:
                    logger.debug(f"State keys: {list(other_keys.keys())}")

            # Log special flags
            if state.get("git_operation_blocked"):
                logger.warning("Git operation was blocked by safety middleware")

            if state.get("compaction_metadata"):
                metadata = state["compaction_metadata"]
                logger.info(
                    f"Memory compaction: {metadata.get('compacted_count')} "
                    f"messages compacted"
                )

            # Write structured log to file if configured
            if log_file:
                _write_structured_log(log_file, state)

        except Exception as e:
            # Logging should never break the agent
            logger.error(f"Error in logging middleware: {e}", exc_info=True)

        return state

    return logging_middleware


def _write_structured_log(log_file: str, state: Dict[str, Any]) -> None:
    """
    Write structured JSON log entry

    Args:
        log_file: Path to log file
        state: Agent state to log
    """
    try:
        log_path = Path(log_file).parent / f"{Path(log_file).stem}_structured.jsonl"

        entry = {
            "timestamp": datetime.now().isoformat(),
            "message_count": len(state.get("messages", [])),
            "state_keys": list(state.keys()),
            "flags": {
                k: v for k, v in state.items()
                if k not in ["messages"] and isinstance(v, (bool, str, int, float))
            }
        }

        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')

    except Exception as e:
        logger.debug(f"Could not write structured log: {e}")
