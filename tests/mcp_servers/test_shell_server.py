# tests/mcp_servers/test_shell_server.py
"""Tests for shell command MCP server"""

import pytest

from deepagent_coder.mcp_servers.shell_server import (
    run_command,
    get_shell_info,
    check_command_exists,
)


@pytest.mark.asyncio
async def test_run_command_simple():
    """Test running a simple echo command"""
    result = await run_command("echo 'Hello World'")

    assert result["returncode"] == 0
    assert "Hello World" in result["stdout"]
    assert result["stderr"] == ""
    assert "error" not in result


@pytest.mark.asyncio
async def test_run_command_with_cwd(tmp_path):
    """Test running command with custom working directory"""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    result = await run_command("ls", cwd=str(tmp_path))

    assert result["returncode"] == 0
    assert "test.txt" in result["stdout"]


@pytest.mark.asyncio
async def test_run_command_with_env():
    """Test running command with custom environment variables"""
    result = await run_command(
        "echo $MY_VAR",
        env={"MY_VAR": "custom_value"}
    )

    assert result["returncode"] == 0
    assert "custom_value" in result["stdout"]


@pytest.mark.asyncio
async def test_run_command_timeout():
    """Test command timeout"""
    result = await run_command("sleep 10", timeout=1)

    assert "error" in result
    assert "timed out" in result["error"].lower()
    assert result["returncode"] != 0


@pytest.mark.asyncio
async def test_run_command_stderr():
    """Test command that outputs to stderr"""
    result = await run_command(">&2 echo 'error message'")

    assert result["returncode"] == 0
    assert "error message" in result["stderr"]


@pytest.mark.asyncio
async def test_run_command_failure():
    """Test command that fails"""
    result = await run_command("exit 1")

    assert result["returncode"] == 1


@pytest.mark.asyncio
async def test_run_command_nonexistent():
    """Test running a non-existent command"""
    result = await run_command("nonexistent_command_12345")

    assert result["returncode"] != 0
    assert "error" in result or result["stderr"] != ""


@pytest.mark.asyncio
async def test_get_shell_info():
    """Test getting shell information"""
    result = await get_shell_info()

    assert "shell" in result
    assert "version" in result
    assert "platform" in result
    assert result["platform"] in ["linux", "darwin", "win32"]


@pytest.mark.asyncio
async def test_check_command_exists():
    """Test checking if command exists"""
    # Test with a command that should exist
    result = await check_command_exists("echo")
    assert result["exists"] is True
    assert "path" in result

    # Test with a command that doesn't exist
    result = await check_command_exists("nonexistent_command_12345")
    assert result["exists"] is False


@pytest.mark.asyncio
async def test_run_command_multiline():
    """Test running multi-line command"""
    result = await run_command(
        """
        echo "line 1"
        echo "line 2"
        echo "line 3"
        """
    )

    assert result["returncode"] == 0
    assert "line 1" in result["stdout"]
    assert "line 2" in result["stdout"]
    assert "line 3" in result["stdout"]


@pytest.mark.asyncio
async def test_run_command_with_pipes():
    """Test running command with pipes"""
    result = await run_command("echo 'hello world' | grep hello")

    assert result["returncode"] == 0
    assert "hello" in result["stdout"]


@pytest.mark.asyncio
async def test_run_command_captures_output():
    """Test that command output is captured correctly"""
    result = await run_command("python -c 'print(\"test\")'")

    assert result["returncode"] == 0
    assert "test" in result["stdout"]
