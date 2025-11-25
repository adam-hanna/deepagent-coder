"""Search Tools MCP Server - filesystem search and navigation tools"""

import json
import shutil
import subprocess
from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("Search Tools")


def grep(
    pattern: str,
    path: str = ".",
    file_pattern: str | None = None,
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

                    matches.append(
                        {
                            "file": file_path,
                            "line": line_num,
                            "text": text,
                            "pattern": pattern,
                        }
                    )

        return matches
    except subprocess.TimeoutExpired:
        return [{"error": "Search timed out after 60 seconds"}]
    except Exception as e:
        return [{"error": f"Grep failed: {str(e)}"}]


# Register the function as an MCP tool
mcp.tool()(grep)


def find(
    path: str = ".",
    name: str | None = None,
    type: str | None = None,  # "f" for file, "d" for directory
    extension: str | None = None,
    max_depth: int | None = None,
) -> list[str]:
    """
    Find files and directories by name, type, or extension.

    Args:
        path: Starting directory for search
        name: Exact filename to match
        type: "f" for files only, "d" for directories only
        extension: File extension to match (without dot)
        max_depth: Maximum depth to search

    Returns:
        List of file/directory paths
    """
    cmd = ["find", path]

    if max_depth is not None:
        cmd.extend(["-maxdepth", str(max_depth)])

    if type:
        cmd.extend(["-type", type])

    if name:
        cmd.extend(["-name", name])
    elif extension:
        cmd.extend(["-name", f"*.{extension}"])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        files = [f for f in result.stdout.strip().split("\n") if f]
        return files
    except subprocess.TimeoutExpired:
        return ["Error: Find timed out after 30 seconds"]
    except Exception as e:
        return [f"Error: {str(e)}"]


# Register the find function as an MCP tool
mcp.tool()(find)


def ls(
    path: str = ".",
    all_files: bool = False,
    long_format: bool = False,
) -> list[dict[str, Any]] | list[str]:
    """
    List directory contents.

    Args:
        path: Directory to list
        all_files: Include hidden files (starting with .)
        long_format: Show detailed information (permissions, size, date)

    Returns:
        List of files/directories (strings or dicts if long_format)
    """
    cmd = ["ls"]

    if all_files:
        cmd.append("-a")
    if long_format:
        cmd.append("-l")

    cmd.append(path)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if long_format:
            # Parse ls -l output
            files = []
            lines = result.stdout.strip().split("\n")

            # Skip first line if it's "total XXX"
            start_idx = 1 if lines and lines[0].startswith("total") else 0

            for line in lines[start_idx:]:
                if line:
                    parts = line.split(None, 8)
                    if len(parts) >= 9:
                        files.append(
                            {
                                "permissions": parts[0],
                                "links": parts[1],
                                "owner": parts[2],
                                "group": parts[3],
                                "size": parts[4],
                                "date": f"{parts[5]} {parts[6]} {parts[7]}",
                                "name": parts[8],
                            }
                        )
                    elif len(parts) >= 1:
                        # Simpler format for some systems
                        files.append({"name": " ".join(parts)})
            return files
        else:
            files = result.stdout.strip().split("\n")
            return [f for f in files if f]

    except Exception as e:
        return [{"error": str(e)}]


# Register the ls function as an MCP tool
mcp.tool()(ls)


def head(file_path: str, lines: int = 10) -> str:
    """
    Show first N lines of a file.

    Args:
        file_path: Path to file
        lines: Number of lines to show (default: 10)

    Returns:
        First N lines of file as string
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            head_lines = []
            for i, line in enumerate(f):
                if i >= lines:
                    break
                head_lines.append(line.rstrip())
        return "\n".join(head_lines)
    except Exception as e:
        return f"Error: {str(e)}"


# Register the head function as an MCP tool
mcp.tool()(head)


def tail(file_path: str, lines: int = 10) -> str:
    """
    Show last N lines of a file.

    Args:
        file_path: Path to file
        lines: Number of lines to show (default: 10)

    Returns:
        Last N lines of file as string
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            all_lines = f.readlines()
            tail_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        return "".join(tail_lines).rstrip()
    except Exception as e:
        return f"Error: {str(e)}"


# Register the tail function as an MCP tool
mcp.tool()(tail)


def wc(
    file_path: str,
    lines: bool = True,
    words: bool = False,
    chars: bool = False,
) -> dict[str, Any]:
    """
    Count lines, words, or characters in file.

    Args:
        file_path: Path to file
        lines: Count lines (default: True)
        words: Count words
        chars: Count characters

    Returns:
        Dictionary with requested counts
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        result = {}
        if lines:
            result["lines"] = content.count("\n") + (
                1 if content and not content.endswith("\n") else 0
            )
        if words:
            result["words"] = len(content.split())
        if chars:
            result["characters"] = len(content)

        return result
    except Exception as e:
        return {"error": str(e)}


# Register the wc function as an MCP tool
mcp.tool()(wc)


def ripgrep(
    pattern: str,
    path: str = ".",
    file_type: str | None = None,
    context: int = 0,
    multiline: bool = False,
) -> list[dict[str, Any]]:
    """
    Fast search using ripgrep (if available), falls back to grep.

    Args:
        pattern: Pattern to search for
        path: Directory or file path to search
        file_type: Language/file type to filter (e.g., "py", "js")
        context: Number of context lines before and after match
        multiline: Enable multiline search

    Returns:
        List of matches with file, line number, and text
    """
    # Check if ripgrep is available
    if not shutil.which("rg"):
        # Fallback to grep
        return grep(pattern=pattern, path=path, recursive=True, regex=True)

    cmd = ["rg", "--json", "-n"]

    if file_type:
        cmd.extend(["-t", file_type])

    if context > 0:
        cmd.extend(["-C", str(context)])

    if multiline:
        cmd.append("--multiline")

    cmd.extend([pattern, path])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        matches = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    data = json.loads(line)
                    if data.get("type") == "match":
                        match_data = data["data"]
                        matches.append(
                            {
                                "file": match_data["path"]["text"],
                                "line": match_data["line_number"],
                                "text": match_data["lines"]["text"].strip(),
                                "column": match_data.get("submatches", [{}])[0].get("start", 0),
                            }
                        )
                except json.JSONDecodeError:
                    # Skip malformed JSON lines
                    pass

        return matches if matches else []
    except subprocess.TimeoutExpired:
        return [{"error": "Ripgrep timed out after 60 seconds"}]
    except Exception:
        # Fallback to grep on any error
        return grep(pattern=pattern, path=path, recursive=True, regex=True)


# Register the ripgrep function as an MCP tool
mcp.tool()(ripgrep)


def run_server():
    """Run the Search Tools MCP server"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
