# tests/mcp_servers/test_python_server.py
from pathlib import Path

import pytest

from deepagent_claude.mcp_servers.python_server import _analyze_code_impl as analyze_code
from deepagent_claude.mcp_servers.python_server import _profile_code_impl as profile_code
from deepagent_claude.mcp_servers.python_server import _run_python_impl as run_python


@pytest.mark.asyncio
async def test_run_python_executes_simple_code():
    """Test executing simple Python code"""
    code = "print('hello world')"
    result = await run_python(code)

    assert result["returncode"] == 0
    assert "hello world" in result["stdout"]
    assert result["stderr"] == ""


@pytest.mark.asyncio
async def test_run_python_handles_syntax_errors():
    """Test handling of syntax errors"""
    code = "print('unclosed string"
    result = await run_python(code)

    assert "error" in result
    assert "SyntaxError" in result["error"] or "unterminated" in result["error"].lower()


@pytest.mark.asyncio
async def test_run_python_respects_timeout():
    """Test timeout enforcement"""
    code = "import time; time.sleep(10)"
    result = await run_python(code, timeout=1)

    assert "error" in result or result["returncode"] != 0


@pytest.mark.asyncio
async def test_analyze_code_extracts_functions():
    """Test function extraction from Python file"""
    # Create test file
    test_file = Path("test_temp_analysis.py")
    test_file.write_text(
        """
def hello(name: str) -> str:
    '''Say hello'''
    return f"Hello {name}"

async def async_hello(name: str) -> str:
    '''Async hello'''
    return f"Async Hello {name}"
"""
    )

    try:
        result = await analyze_code(str(test_file))

        assert "error" not in result
        assert len(result["functions"]) == 2
        assert result["functions"][0]["name"] == "hello"
        assert result["functions"][0]["args"] == ["name"]
        assert result["functions"][0]["docstring"] == "Say hello"
        assert result["functions"][1]["is_async"] is True
    finally:
        test_file.unlink()


@pytest.mark.asyncio
async def test_analyze_code_extracts_classes():
    """Test class extraction from Python file"""
    test_file = Path("test_temp_class.py")
    test_file.write_text(
        """
class MyClass:
    '''A test class'''

    def method_one(self, x: int) -> int:
        return x * 2

    def method_two(self) -> str:
        return "test"
"""
    )

    try:
        result = await analyze_code(str(test_file))

        assert "error" not in result
        assert len(result["classes"]) == 1
        assert result["classes"][0]["name"] == "MyClass"
        assert len(result["classes"][0]["methods"]) == 2
    finally:
        test_file.unlink()


@pytest.mark.asyncio
async def test_analyze_code_extracts_imports():
    """Test import extraction"""
    test_file = Path("test_temp_imports.py")
    test_file.write_text(
        """
import os
import sys as system
from pathlib import Path
from typing import Dict, List
"""
    )

    try:
        result = await analyze_code(str(test_file))

        assert "error" not in result
        assert len(result["imports"]) >= 4

        # Check regular import
        os_import = next(i for i in result["imports"] if i["module"] == "os")
        assert os_import["type"] == "import"

        # Check aliased import
        sys_import = next(i for i in result["imports"] if i["module"] == "sys")
        assert sys_import["alias"] == "system"

        # Check from import
        path_import = next(i for i in result["imports"] if "Path" in i["module"])
        assert path_import["type"] == "from_import"
    finally:
        test_file.unlink()


@pytest.mark.asyncio
async def test_profile_code_measures_performance():
    """Test code profiling"""
    test_file = Path("test_temp_profile.py")
    test_file.write_text(
        """
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    return fibonacci(10)
"""
    )

    try:
        result = await profile_code(str(test_file), "main")

        assert "error" not in result
        assert result["function"] == "main"
        assert result["total_calls"] > 0
        assert result["total_time"] > 0
        assert "profile_output" in result
    finally:
        test_file.unlink()
