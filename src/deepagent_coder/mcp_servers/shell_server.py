"""Shell command execution MCP server - run arbitrary shell commands"""

import asyncio
import os
import platform
import shutil
import sys
from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("Shell Tools")


async def run_command(
    command: str,
    cwd: str | None = None,
    timeout: int = 300,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Execute a shell command with proper safety controls

    Args:
        command: Shell command to execute
        cwd: Working directory (optional, defaults to current directory)
        timeout: Maximum execution time in seconds (default: 300/5 minutes)
        env: Environment variables to set (optional, merges with current env)

    Returns:
        Dictionary with stdout, stderr, returncode, and optional error

    Example:
        >>> await run_command("echo 'Hello World'")
        {'stdout': 'Hello World\\n', 'stderr': '', 'returncode': 0}

        >>> await run_command("npm install", cwd="/path/to/project")
        {'stdout': '...', 'stderr': '', 'returncode': 0}
    """
    try:
        # Prepare environment
        command_env = os.environ.copy()
        if env:
            command_env.update(env)

        # Determine shell based on platform
        if platform.system() == "Windows":
            shell_cmd = ["cmd", "/c", command]
        else:
            shell_cmd = ["/bin/sh", "-c", command]

        # Execute command
        process = await asyncio.create_subprocess_exec(
            *shell_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=command_env,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

            return {
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "returncode": process.returncode,
            }

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return {
                "error": f"Command timed out after {timeout} seconds",
                "returncode": -1,
                "stdout": "",
                "stderr": "",
            }

    except FileNotFoundError as e:
        return {
            "error": f"Command not found: {e}",
            "returncode": 127,
            "stdout": "",
            "stderr": str(e),
        }
    except PermissionError as e:
        return {
            "error": f"Permission denied: {e}",
            "returncode": 126,
            "stdout": "",
            "stderr": str(e),
        }
    except Exception as e:
        return {
            "error": f"Command execution failed: {str(e)}",
            "returncode": 1,
            "stdout": "",
            "stderr": str(e),
        }


@mcp.tool()
async def run_shell_command(
    command: str,
    cwd: str | None = None,
    timeout: int = 300,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Execute a shell command

    Use this tool to run any command-line tool or script:
    - Package managers: npm install, pip install, cargo build
    - Build tools: make, cmake, gradle, maven
    - Development servers: npm start, python manage.py runserver
    - Docker commands: docker build, docker run, docker-compose up
    - Any other CLI tool available on the system

    Args:
        command: Shell command to execute (e.g., "npm install", "docker ps")
        cwd: Working directory for command execution (optional)
        timeout: Maximum execution time in seconds (default: 300)
        env: Additional environment variables (optional)

    Returns:
        Dictionary containing:
        - stdout: Command standard output
        - stderr: Command standard error
        - returncode: Exit code (0 for success)
        - error: Error message if command failed
    """
    return await run_command(command, cwd, timeout, env)


async def get_shell_info() -> dict[str, Any]:
    """
    Get information about the current shell environment

    Returns:
        Dictionary with shell type, version, and platform information
    """
    system = platform.system()

    # Determine shell
    if system == "Windows":
        shell = "cmd" if "COMSPEC" in os.environ else "powershell"
        shell_path = os.environ.get("COMSPEC", "powershell")
    else:
        shell = os.environ.get("SHELL", "/bin/sh")
        shell_path = shell

    # Get shell version
    try:
        if system == "Windows":
            version_result = await run_command("ver")
        else:
            version_result = await run_command(f"{shell} --version 2>&1 | head -1")

        version = version_result.get("stdout", "").strip() or "Unknown"
    except Exception:
        version = "Unknown"

    return {
        "shell": shell,
        "shell_path": shell_path,
        "version": version,
        "platform": sys.platform,
        "system": system,
        "python_version": sys.version,
    }


@mcp.tool()
async def get_system_info() -> dict[str, Any]:
    """
    Get information about the system and shell environment

    Returns:
        Dictionary with shell, platform, and system information
    """
    return await get_shell_info()


async def check_command_exists(command: str) -> dict[str, Any]:
    """
    Check if a command is available on the system

    Args:
        command: Command name to check (e.g., "npm", "docker", "python")

    Returns:
        Dictionary with:
        - exists: Boolean indicating if command is available
        - path: Full path to command (if exists)
    """
    command_path = shutil.which(command)

    return {
        "exists": command_path is not None,
        "path": command_path if command_path else None,
        "command": command,
    }


@mcp.tool()
async def check_command_available(command: str) -> dict[str, Any]:
    """
    Check if a command-line tool is available

    Useful before running commands to verify tools are installed.

    Args:
        command: Command name (e.g., "npm", "docker", "git")

    Returns:
        Dictionary with:
        - exists: True if command is available
        - path: Full path to the command executable
        - command: The command name that was checked
    """
    return await check_command_exists(command)


if __name__ == "__main__":
    mcp.run()
