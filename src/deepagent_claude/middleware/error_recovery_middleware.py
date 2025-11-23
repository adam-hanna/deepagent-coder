"""Error recovery middleware for graceful error handling and retries"""

from typing import Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)


def create_error_recovery_middleware(
    max_retries: int = 3,
    add_recovery_message: bool = True
) -> Callable:
    """
    Create error recovery middleware

    Args:
        max_retries: Maximum number of retry attempts
        add_recovery_message: Whether to add recovery guidance to messages

    Returns:
        Middleware function
    """

    async def error_recovery_middleware(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle errors gracefully with retry logic

        Args:
            state: Agent state dictionary

        Returns:
            Modified state with error handling
        """
        # Check if there's an error in the state
        error = state.get("error")

        if error:
            # Track retry count
            retry_count = state.get("retry_count", 0) + 1
            state["retry_count"] = retry_count

            logger.warning(
                f"Error detected (attempt {retry_count}/{max_retries}): {error}"
            )

            # Check if max retries reached
            if retry_count >= max_retries:
                state["max_retries_reached"] = True
                logger.error(
                    f"Max retries ({max_retries}) reached. "
                    f"Error: {error}"
                )

                if add_recovery_message:
                    state["messages"].append({
                        "role": "system",
                        "content": (
                            f"⚠️  Maximum retry attempts ({max_retries}) reached. "
                            f"Error: {error}. Please try a different approach or "
                            f"check the error details."
                        )
                    })
            else:
                # Add recovery guidance
                if add_recovery_message:
                    state["messages"].append({
                        "role": "system",
                        "content": (
                            f"⚠️  An error occurred: {error}. "
                            f"Attempting recovery (attempt {retry_count}/{max_retries})..."
                        )
                    })

                logger.info(f"Attempting recovery (retry {retry_count})")

        return state

    return error_recovery_middleware
