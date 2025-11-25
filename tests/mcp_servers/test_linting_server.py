# tests/mcp_servers/test_linting_server.py

import pytest

from deepagent_claude.mcp_servers.linting_server import (
    format_code,
    lint_project,
    run_black,
    run_mypy,
    run_ruff,
)


@pytest.fixture
def python_file(tmp_path):
    """Create a temporary Python file with issues"""
    file_path = tmp_path / "test_file.py"
    file_path.write_text(
        """
import os
import sys


def  badly_formatted(x,y):
    unused_var = 123
    return x+y


class  BadClass:
    pass
"""
    )
    return str(file_path)


@pytest.mark.asyncio
async def test_run_ruff_detects_issues(python_file):
    """Test ruff linting"""
    result = await run_ruff(python_file)

    assert "error" not in result
    assert result["total_issues"] > 0


@pytest.mark.asyncio
async def test_run_ruff_with_fix(python_file):
    """Test ruff with auto-fix"""
    result = await run_ruff(python_file, fix=True)

    assert "error" not in result
    assert result["fixed"] is True


@pytest.mark.asyncio
async def test_run_mypy_type_checks(python_file):
    """Test mypy type checking"""
    result = await run_mypy(python_file)

    assert "error" not in result
    # Mypy may or may not find issues in this simple file


@pytest.mark.asyncio
async def test_run_black_formats(python_file):
    """Test black formatting"""
    result = await run_black(python_file)

    assert "error" not in result
    # Black should reformat the file


@pytest.mark.asyncio
async def test_format_code_with_black(python_file):
    """Test generic format_code function"""
    result = await format_code(python_file, formatter="black")

    assert "error" not in result
    assert result.get("success") is not None


@pytest.mark.asyncio
async def test_run_ruff_handles_nonexistent_file():
    """Test ruff with non-existent file"""
    result = await run_ruff("/nonexistent/file.py")

    assert "error" in result
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_lint_project_runs_all_tools(tmp_path):
    """Test comprehensive project linting"""
    # Create simple project structure
    (tmp_path / "test.py").write_text("x = 1")

    result = await lint_project(str(tmp_path))

    assert "error" not in result
    assert "results" in result
    assert "ruff" in result["results"]
    assert "mypy" in result["results"]
    assert "black" in result["results"]
