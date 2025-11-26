# src/deepagent_coder/mcp_servers/filesystem_server.py
"""Filesystem operations MCP server - file and directory management tools"""

import os
from pathlib import Path
import shutil
from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("Filesystem Tools")


async def _write_file_impl(path: str, content: str) -> dict[str, Any]:
    """
    Write content to a file

    Args:
        path: Path to the file
        content: Content to write

    Returns:
        Success status and file info
    """
    try:
        file_path = Path(path)

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content to file
        file_path.write_text(content, encoding="utf-8")

        return {
            "success": True,
            "path": str(file_path),
            "size": len(content),
            "message": f"Successfully wrote {len(content)} bytes to {path}",
        }

    except PermissionError:
        return {"error": f"Permission denied: {path}"}
    except Exception as e:
        return {"error": f"Failed to write file: {str(e)}"}


@mcp.tool()
async def write_file(path: str, content: str) -> dict[str, Any]:
    """Write content to a file, creating directories if needed"""
    return await _write_file_impl(path, content)


async def _read_file_impl(path: str) -> dict[str, Any]:
    """
    Read content from a file

    Args:
        path: Path to the file

    Returns:
        File content and metadata
    """
    try:
        file_path = Path(path)

        if not file_path.exists():
            return {"error": f"File not found: {path}"}

        if not file_path.is_file():
            return {"error": f"Not a file: {path}"}

        content = file_path.read_text(encoding="utf-8")
        stat = file_path.stat()

        return {
            "success": True,
            "path": str(file_path),
            "content": content,
            "size": stat.st_size,
            "modified": stat.st_mtime,
        }

    except PermissionError:
        return {"error": f"Permission denied: {path}"}
    except UnicodeDecodeError:
        return {"error": f"File is not a text file: {path}"}
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}


@mcp.tool()
async def read_file(path: str) -> dict[str, Any]:
    """Read content from a file"""
    return await _read_file_impl(path)


async def _list_directory_impl(path: str) -> dict[str, Any]:
    """
    List contents of a directory

    Args:
        path: Path to the directory

    Returns:
        List of files and directories with metadata
    """
    try:
        dir_path = Path(path)

        if not dir_path.exists():
            return {"error": f"Directory not found: {path}"}

        if not dir_path.is_dir():
            return {"error": f"Not a directory: {path}"}

        entries = []
        for entry in dir_path.iterdir():
            stat = entry.stat()
            entries.append(
                {
                    "name": entry.name,
                    "path": str(entry),
                    "type": "directory" if entry.is_dir() else "file",
                    "size": stat.st_size if entry.is_file() else None,
                    "modified": stat.st_mtime,
                }
            )

        # Sort: directories first, then files, alphabetically
        entries.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))

        return {"success": True, "path": str(dir_path), "entries": entries, "count": len(entries)}

    except PermissionError:
        return {"error": f"Permission denied: {path}"}
    except Exception as e:
        return {"error": f"Failed to list directory: {str(e)}"}


@mcp.tool()
async def list_directory(path: str) -> dict[str, Any]:
    """List contents of a directory"""
    return await _list_directory_impl(path)


async def _create_directory_impl(path: str) -> dict[str, Any]:
    """
    Create a directory (and parent directories if needed)

    Args:
        path: Path to the directory

    Returns:
        Success status
    """
    try:
        dir_path = Path(path)

        if dir_path.exists():
            if dir_path.is_dir():
                return {
                    "success": True,
                    "path": str(dir_path),
                    "message": f"Directory already exists: {path}",
                }
            else:
                return {"error": f"Path exists but is not a directory: {path}"}

        dir_path.mkdir(parents=True, exist_ok=True)

        return {
            "success": True,
            "path": str(dir_path),
            "message": f"Successfully created directory: {path}",
        }

    except PermissionError:
        return {"error": f"Permission denied: {path}"}
    except Exception as e:
        return {"error": f"Failed to create directory: {str(e)}"}


@mcp.tool()
async def create_directory(path: str) -> dict[str, Any]:
    """Create a directory, including parent directories if needed"""
    return await _create_directory_impl(path)


async def _move_file_impl(source: str, destination: str) -> dict[str, Any]:
    """
    Move or rename a file or directory

    Args:
        source: Source path
        destination: Destination path

    Returns:
        Success status
    """
    try:
        src_path = Path(source)
        dst_path = Path(destination)

        if not src_path.exists():
            return {"error": f"Source not found: {source}"}

        if dst_path.exists():
            return {"error": f"Destination already exists: {destination}"}

        # Create parent directory if needed
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(src_path), str(dst_path))

        return {
            "success": True,
            "source": str(src_path),
            "destination": str(dst_path),
            "message": f"Successfully moved {source} to {destination}",
        }

    except PermissionError:
        return {"error": "Permission denied"}
    except Exception as e:
        return {"error": f"Failed to move file: {str(e)}"}


@mcp.tool()
async def move_file(source: str, destination: str) -> dict[str, Any]:
    """Move or rename a file or directory"""
    return await _move_file_impl(source, destination)


async def _delete_file_impl(path: str) -> dict[str, Any]:
    """
    Delete a file

    Args:
        path: Path to the file

    Returns:
        Success status
    """
    try:
        file_path = Path(path)

        if not file_path.exists():
            return {"error": f"File not found: {path}"}

        if not file_path.is_file():
            return {"error": f"Not a file (use delete_directory for directories): {path}"}

        file_path.unlink()

        return {
            "success": True,
            "path": str(file_path),
            "message": f"Successfully deleted file: {path}",
        }

    except PermissionError:
        return {"error": f"Permission denied: {path}"}
    except Exception as e:
        return {"error": f"Failed to delete file: {str(e)}"}


@mcp.tool()
async def delete_file(path: str) -> dict[str, Any]:
    """Delete a file"""
    return await _delete_file_impl(path)


async def _delete_directory_impl(path: str, recursive: bool = False) -> dict[str, Any]:
    """
    Delete a directory

    Args:
        path: Path to the directory
        recursive: If True, delete non-empty directories

    Returns:
        Success status
    """
    try:
        dir_path = Path(path)

        if not dir_path.exists():
            return {"error": f"Directory not found: {path}"}

        if not dir_path.is_dir():
            return {"error": f"Not a directory: {path}"}

        if recursive:
            shutil.rmtree(dir_path)
        else:
            dir_path.rmdir()  # Only works for empty directories

        return {
            "success": True,
            "path": str(dir_path),
            "message": f"Successfully deleted directory: {path}",
        }

    except OSError as e:
        if "not empty" in str(e).lower():
            return {"error": f"Directory not empty (use recursive=True to force): {path}"}
        return {"error": f"Failed to delete directory: {str(e)}"}
    except PermissionError:
        return {"error": f"Permission denied: {path}"}
    except Exception as e:
        return {"error": f"Failed to delete directory: {str(e)}"}


@mcp.tool()
async def delete_directory(path: str, recursive: bool = False) -> dict[str, Any]:
    """Delete a directory (optionally recursive for non-empty directories)"""
    return await _delete_directory_impl(path, recursive)


async def _get_file_info_impl(path: str) -> dict[str, Any]:
    """
    Get file or directory metadata

    Args:
        path: Path to the file or directory

    Returns:
        File metadata
    """
    try:
        file_path = Path(path)

        if not file_path.exists():
            return {"error": f"Path not found: {path}"}

        stat = file_path.stat()

        info = {
            "success": True,
            "path": str(file_path),
            "name": file_path.name,
            "type": "directory" if file_path.is_dir() else "file",
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "permissions": oct(stat.st_mode)[-3:],
        }

        if file_path.is_file():
            info["extension"] = file_path.suffix

        return info

    except PermissionError:
        return {"error": f"Permission denied: {path}"}
    except Exception as e:
        return {"error": f"Failed to get file info: {str(e)}"}


@mcp.tool()
async def get_file_info(path: str) -> dict[str, Any]:
    """Get metadata for a file or directory"""
    return await _get_file_info_impl(path)


def run_server():
    """Run the Filesystem MCP server"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
