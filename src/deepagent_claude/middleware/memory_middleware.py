"""Memory compaction middleware for DeepAgent"""

from collections.abc import Callable
import logging
from typing import Any

from deepagent_claude.utils.memory_compactor import MemoryCompactor

logger = logging.getLogger(__name__)


def create_memory_middleware(
    model_selector, threshold: int = 6000, keep_recent: int = 10
) -> Callable:
    """
    Create memory compaction middleware

    Args:
        model_selector: ModelSelector instance
        threshold: Token threshold for compaction
        keep_recent: Number of recent messages to keep

    Returns:
        Middleware function
    """
    compactor = MemoryCompactor(model_selector=model_selector, threshold=threshold)

    async def memory_middleware(state: dict[str, Any]) -> dict[str, Any]:
        """
        Middleware that compacts messages when threshold reached

        Args:
            state: Agent state dictionary

        Returns:
            Modified state with compacted messages
        """
        messages = state.get("messages", [])

        if not messages:
            return state

        # Check if compaction needed
        if compactor.should_compact(messages):
            logger.info("Performing memory compaction...")

            try:
                # Generate summary of old messages
                summary = await compactor.compact_conversation(messages, keep_recent=keep_recent)

                # Replace old messages with summary + recent
                compacted_messages = compactor.compact_with_summary(
                    messages, summary, keep_recent=keep_recent
                )

                original_count = len(messages)
                new_count = len(compacted_messages)

                state["messages"] = compacted_messages
                state["compaction_metadata"] = {
                    "compacted_count": original_count - keep_recent,
                    "kept_count": keep_recent,
                    "original_count": original_count,
                    "new_count": new_count,
                }

                logger.info(
                    f"Compacted {original_count - keep_recent} messages, "
                    f"kept {keep_recent} recent (total: {original_count} -> {new_count})"
                )

            except Exception as e:
                logger.error(f"Memory compaction failed: {e}")
                # Continue without compaction on error

        return state

    return memory_middleware
