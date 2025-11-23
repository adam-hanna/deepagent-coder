"""Git safety middleware to prevent dangerous operations"""

from typing import Dict, Any, Callable
import re
import logging

logger = logging.getLogger(__name__)

DANGEROUS_PATTERNS = [
    (r"git\s+push\s+.*--force", "Force push detected"),
    (r"force\s+push", "Force push detected"),
    (r"git\s+reset\s+--hard", "Hard reset detected"),
    (r"git\s+clean\s+-[fFdDxX]", "Git clean detected"),
    (r"git\s+push\s+.*\b(main|master)\b", "Push to main/master branch"),
    (r"push.*\b(main|master)\b", "Push to main/master branch"),
]


def create_git_safety_middleware(
    enforce: bool = False
) -> Callable:
    """
    Create git safety middleware

    Args:
        enforce: If True, block dangerous operations. If False, warn only.

    Returns:
        Middleware function
    """

    async def git_safety_middleware(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for dangerous git operations and warn/block

        Args:
            state: Agent state

        Returns:
            Modified state with warnings if needed
        """
        messages = state.get("messages", [])

        if not messages:
            return state

        last_message = messages[-1]
        content = last_message.get("content", "").lower()

        # Check for dangerous patterns
        for pattern, description in DANGEROUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                warning_msg = f"⚠️  WARNING: {description}. "

                if enforce:
                    warning_msg += "This operation is blocked for safety."
                    logger.warning(f"Blocked dangerous operation: {description}")

                    # Add blocking message
                    state["messages"].append({
                        "role": "system",
                        "content": warning_msg
                    })

                    # Set flag to prevent execution
                    state["git_operation_blocked"] = True

                else:
                    warning_msg += "Please confirm this is intentional."
                    logger.info(f"Warning about operation: {description}")

                    state["messages"].append({
                        "role": "system",
                        "content": warning_msg
                    })

                break

        return state

    return git_safety_middleware
