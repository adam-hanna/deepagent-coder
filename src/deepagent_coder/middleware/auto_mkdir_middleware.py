"""Auto-mkdir middleware - automatically creates parent directories before file writes"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def create_auto_mkdir_middleware(mcp_client: Any = None) -> callable:
    """
    Create middleware that automatically creates parent directories before file writes.

    This middleware intercepts write_file tool calls and ensures parent directories
    exist before the file is written, preventing "parent directory does not exist" errors.

    Args:
        mcp_client: MCP client instance for calling create_directory tool

    Returns:
        Middleware function that processes tool calls
    """

    async def auto_mkdir_middleware(state: dict[str, Any]) -> dict[str, Any]:
        """
        Intercept write_file calls and auto-create parent directories.

        Args:
            state: Agent state dictionary

        Returns:
            Modified state with auto-created directories
        """
        # Get the last message to check if it's a tool call
        messages = state.get("messages", [])
        if not messages:
            return state

        last_message = messages[-1]

        # Check if this is an AI message with tool calls
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return state

        # Process each tool call
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get("name", "")

            # Check if this is a write_file call
            if "write_file" in tool_name.lower() or tool_name == "write_file":
                args = tool_call.get("args", {})
                file_path = args.get("path") or args.get("file_path")

                if file_path and mcp_client:
                    # Extract parent directory
                    path_obj = Path(file_path)
                    parent_dir = path_obj.parent

                    # Only create if parent is not current directory
                    if str(parent_dir) != "." and parent_dir != Path("."):
                        try:
                            logger.info(f"[auto-mkdir] Creating parent directory: {parent_dir}")

                            # Call create_directory tool via MCP
                            await mcp_client.call_tool(
                                "create_directory", {"path": str(parent_dir)}
                            )

                            logger.info(f"[auto-mkdir] ✓ Successfully created: {parent_dir}")

                        except Exception as e:
                            # Log but don't fail - directory might already exist
                            logger.debug(f"[auto-mkdir] Directory creation note: {e}")

        return state

    return auto_mkdir_middleware
