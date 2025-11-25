"""Error recovery middleware for graceful error handling and retries"""

from collections.abc import Callable
import logging
from typing import Any

logger = logging.getLogger(__name__)


def create_error_recovery_middleware(
    max_retries: int = 3, add_recovery_message: bool = True
) -> Callable:
    """
    Create error recovery middleware

    Args:
        max_retries: Maximum number of retry attempts
        add_recovery_message: Whether to add recovery guidance to messages

    Returns:
        Middleware function
    """

    async def error_recovery_middleware(state: dict[str, Any]) -> dict[str, Any]:
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

            logger.warning(f"Error detected (attempt {retry_count}/{max_retries}): {error}")

            # Check if max retries reached
            if retry_count >= max_retries:
                state["max_retries_reached"] = True
                logger.error(f"Max retries ({max_retries}) reached. " f"Error: {error}")

                if add_recovery_message:
                    state["messages"].append(
                        {
                            "role": "system",
                            "content": (
                                f"⚠️  Maximum retry attempts ({max_retries}) reached. "
                                f"Error: {error}. Please try a different approach or "
                                f"check the error details."
                            ),
                        }
                    )
            else:
                # Add recovery guidance with specific suggestions
                recovery_message = f"⚠️  An error occurred: {error}. "

                # Detect specific error patterns and provide targeted guidance
                error_str = str(error).lower()

                if (
                    "parent directory does not exist" in error_str
                    or "no such file or directory" in error_str
                ):
                    # Extract directory path from error if possible
                    import re

                    path_match = re.search(r"/[\w/\-\.]+", str(error))
                    if path_match:
                        failed_path = path_match.group(0)
                        import os

                        parent_dir = os.path.dirname(failed_path)
                        recovery_message += (
                            f"\n\n💡 TIP: The parent directory '{parent_dir}' doesn't exist. "
                            f"Use the create_directory or mkdir tool to create it first, then retry writing the file."
                        )
                    else:
                        recovery_message += (
                            "\n\n💡 TIP: Create the parent directory first using create_directory or mkdir, "
                            "then retry writing the file."
                        )

                elif "access denied" in error_str or "permission denied" in error_str:
                    recovery_message += "\n\n💡 TIP: Check file permissions or verify the path is within the allowed workspace."

                elif "outside allowed directories" in error_str:
                    recovery_message += (
                        "\n\n💡 TIP: The path is outside the workspace. All file operations must be within the workspace directory. "
                        "Use relative paths or paths starting with the workspace root."
                    )

                else:
                    recovery_message += (
                        f"Attempting recovery (attempt {retry_count}/{max_retries})..."
                    )

                if add_recovery_message:
                    state["messages"].append(
                        {
                            "role": "system",
                            "content": recovery_message,
                        }
                    )

                logger.info(f"Attempting recovery (retry {retry_count})")

        return state

    return error_recovery_middleware
