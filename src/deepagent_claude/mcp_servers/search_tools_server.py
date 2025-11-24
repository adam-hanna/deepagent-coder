"""Search Tools MCP Server - filesystem search and navigation tools"""

import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

from fastmcp import FastMCP

mcp = FastMCP("Search Tools")


def grep(
    pattern: str,
    path: str = ".",
    file_pattern: Optional[str] = None,
    recursive: bool = True,
    context_before: int = 0,
    context_after: int = 0,
    ignore_case: bool = False,
    regex: bool = False,
) -> list[dict[str, Any]]:
    """
    Search for pattern in files using grep.

    Args:
        pattern: Pattern to search for
        path: Directory or file path to search
        file_pattern: Optional glob pattern to filter files (e.g., "*.py")
        recursive: Search recursively through directories
        context_before: Number of lines to show before match
        context_after: Number of lines to show after match
        ignore_case: Case-insensitive search
        regex: Treat pattern as regex (default: fixed string)

    Returns:
        List of matches with file, line number, and text
    """
    cmd = ["grep"]

    # Build grep flags
    if recursive:
        cmd.append("-r")
    if ignore_case:
        cmd.append("-i")
    if regex:
        cmd.append("-E")  # Extended regex
    else:
        cmd.append("-F")  # Fixed string (faster)

    # Line numbers always
    cmd.append("-n")

    # Context lines
    if context_before > 0:
        cmd.extend(["-B", str(context_before)])
    if context_after > 0:
        cmd.extend(["-A", str(context_after)])

    # Add pattern and path
    cmd.append(pattern)
    cmd.append(path)

    # File pattern filter
    if file_pattern:
        cmd.extend(["--include", file_pattern])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Parse grep output
        matches = []
        for line in result.stdout.strip().split("\n"):
            if line and ":" in line:
                # Format: file:line:text or file:line-text (for context)
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    file_path = parts[0]
                    line_num = parts[1]
                    text = parts[2] if len(parts) > 2 else ""

                    matches.append({
                        "file": file_path,
                        "line": line_num,
                        "text": text,
                        "pattern": pattern,
                    })

        return matches
    except subprocess.TimeoutExpired:
        return [{"error": "Search timed out after 60 seconds"}]
    except Exception as e:
        return [{"error": f"Grep failed: {str(e)}"}]


# Register the function as an MCP tool
mcp.tool()(grep)


# Placeholder functions for other tools (to satisfy imports in tests)
def find(*args, **kwargs):
    """Placeholder for find tool"""
    raise NotImplementedError("find tool not yet implemented")


def ls(*args, **kwargs):
    """Placeholder for ls tool"""
    raise NotImplementedError("ls tool not yet implemented")


def head(*args, **kwargs):
    """Placeholder for head tool"""
    raise NotImplementedError("head tool not yet implemented")


def tail(*args, **kwargs):
    """Placeholder for tail tool"""
    raise NotImplementedError("tail tool not yet implemented")


def wc(*args, **kwargs):
    """Placeholder for wc tool"""
    raise NotImplementedError("wc tool not yet implemented")


def ripgrep(*args, **kwargs):
    """Placeholder for ripgrep tool"""
    raise NotImplementedError("ripgrep tool not yet implemented")


def run_server():
    """Run the Search Tools MCP server"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
