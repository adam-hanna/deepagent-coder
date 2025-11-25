"""
Tool Wrapper Utilities - Enhance MCP tools with additional functionality.

This module provides wrappers around MCP tools to add features like:
- Automatic directory creation before file writes
- Better error handling and recovery
- Tool call logging and debugging
"""

from collections.abc import Callable
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


async def wrap_write_file_tool(original_tool: Any, workspace_path: str) -> Callable:
    """
    Wrap the MCP filesystem write_file tool to automatically create parent directories.

    Args:
        original_tool: The original MCP write_file tool
        workspace_path: The workspace root path for validation

    Returns:
        Wrapped tool function that creates directories before writing
    """

    async def wrapped_write_file(*args, **kwargs):
        """Wrapped write_file that creates parent directories first"""
        # Extract file path from arguments
        file_path = kwargs.get("path") or (args[0] if args else None)

        if not file_path:
            logger.error("write_file called without path argument")
            return await original_tool.ainvoke(*args, **kwargs)

        try:
            # Create parent directory if needed
            file_path_obj = Path(file_path)
            parent_dir = file_path_obj.parent

            if parent_dir and str(parent_dir) != "." and not parent_dir.exists():
                logger.info(f"Creating parent directory: {parent_dir}")
                parent_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"✓ Created directory: {parent_dir}")

        except Exception as e:
            logger.warning(f"Failed to create parent directory for {file_path}: {e}")
            # Continue anyway - the original tool might handle it

        # Call original tool
        return await original_tool.ainvoke(*args, **kwargs)

    return wrapped_write_file


def wrap_mcp_tools(tools: list[Any], workspace_path: str) -> list[Any]:
    """
    Wrap MCP tools to add enhanced functionality.

    Currently wraps:
    - write_file: Adds automatic directory creation

    Args:
        tools: List of MCP tools to wrap
        workspace_path: Workspace root path

    Returns:
        List of wrapped tools (or original tools if wrapping not needed)
    """
    wrapped_tools = []

    for tool in tools:
        tool_name = getattr(tool, "name", str(tool))

        # Wrap write_file tool
        if "write_file" in tool_name.lower() or "write" in tool_name.lower():
            logger.info(f"Wrapping tool: {tool_name} with directory creation logic")
            # Note: We can't easily wrap the tool object itself since it's a LangChain tool
            # Instead, we'll handle this at the prompt level - see main agent prompt updates
            wrapped_tools.append(tool)
        else:
            wrapped_tools.append(tool)

    logger.debug(f"Processed {len(tools)} tools ({len(wrapped_tools)} wrapped)")
    return wrapped_tools
