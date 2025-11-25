# tests/mcp_servers/test_static_analysis_server.py
"""Tests for static analysis MCP server"""


import pytest

from deepagent_coder.mcp_servers.static_analysis_server import (
    check_type_coverage,
    documentation_coverage,
    run_linter,
    security_scan,
)


@pytest.mark.asyncio
async def test_run_linter_pylint_clean_code(tmp_path):
    """Test running pylint on clean Python code"""
    test_file = tmp_path / "clean.py"
    content = """\"\"\"Module docstring.\"\"\"


def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b
"""
    test_file.write_text(content)

    result = await run_linter(str(test_file), linter="pylint")

    assert result["success"] is True
    assert "issues" in result
    assert isinstance(result["issues"], list)
    # Clean code should have few or no issues
    assert len(result["issues"]) <= 2  # Allow for minor style issues


@pytest.mark.asyncio
async def test_run_linter_pylint_with_issues(tmp_path):
    """Test running pylint on code with issues"""
    test_file = tmp_path / "issues.py"
    content = """import os
import sys

def badFunction(x,y):
    z = x + y
    return z
"""
    test_file.write_text(content)

    result = await run_linter(str(test_file), linter="pylint")

    assert result["success"] is True
    assert len(result["issues"]) > 0
    # Should detect various issues
    issue_types = [issue.get("type") for issue in result["issues"]]
    # Check for severity levels
    assert any(
        "warning" in str(issue).lower() or "convention" in str(issue).lower()
        for issue in result["issues"]
    )


@pytest.mark.asyncio
async def test_run_linter_auto_detect(tmp_path):
    """Test auto-detecting linter based on file type"""
    test_file = tmp_path / "test.py"
    content = """def func():
    x = 1
    return x
"""
    test_file.write_text(content)

    result = await run_linter(str(test_file))  # No linter specified

    assert result["success"] is True
    assert "linter_used" in result
    assert result["linter_used"] in ["pylint", "ruff", "flake8"]


@pytest.mark.asyncio
async def test_run_linter_with_config(tmp_path):
    """Test running linter with custom config file"""
    test_file = tmp_path / "test.py"
    test_file.write_text("def func():\n    pass\n")

    config_file = tmp_path / ".pylintrc"
    config_file.write_text("[MESSAGES CONTROL]\ndisable=missing-docstring\n")

    result = await run_linter(str(test_file), linter="pylint", config_file=str(config_file))

    assert result["success"] is True


@pytest.mark.asyncio
async def test_run_linter_nonexistent_file():
    """Test linting non-existent file"""
    result = await run_linter("/nonexistent/file.py")

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_security_scan_bandit_clean(tmp_path):
    """Test security scan on clean code"""
    test_file = tmp_path / "clean.py"
    content = """\"\"\"Safe module.\"\"\"


def process_data(data):
    \"\"\"Process data safely.\"\"\"
    return [x * 2 for x in data if x > 0]
"""
    test_file.write_text(content)

    result = await security_scan(str(test_file), language="python")

    assert result["success"] is True
    assert "vulnerabilities" in result
    assert isinstance(result["vulnerabilities"], list)


@pytest.mark.asyncio
async def test_security_scan_bandit_with_issues(tmp_path):
    """Test security scan finding vulnerabilities"""
    test_file = tmp_path / "insecure.py"
    content = """import pickle
import subprocess
import os

def load_data(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)  # Security issue: arbitrary code execution

def run_command(user_input):
    os.system(user_input)  # Security issue: shell injection

def execute(cmd):
    subprocess.call(cmd, shell=True)  # Security issue: shell=True
"""
    test_file.write_text(content)

    result = await security_scan(str(test_file), language="python")

    assert result["success"] is True
    assert len(result["vulnerabilities"]) > 0
    # Should detect security issues
    assert any(
        "pickle" in str(v).lower() or "subprocess" in str(v).lower() or "shell" in str(v).lower()
        for v in result["vulnerabilities"]
    )


@pytest.mark.asyncio
async def test_security_scan_directory(tmp_path):
    """Test security scan on entire directory"""
    # Create multiple files
    (tmp_path / "file1.py").write_text("import os\nos.system('ls')")
    (tmp_path / "file2.py").write_text("def safe(): pass")

    result = await security_scan(str(tmp_path), language="python")

    assert result["success"] is True
    assert "vulnerabilities" in result


@pytest.mark.asyncio
async def test_security_scan_auto_detect_language(tmp_path):
    """Test auto-detecting language for security scan"""
    test_file = tmp_path / "test.py"
    test_file.write_text("def func():\n    pass\n")

    result = await security_scan(str(test_file))  # No language specified

    assert result["success"] is True
    assert "language_detected" in result or "vulnerabilities" in result


@pytest.mark.asyncio
async def test_security_scan_nonexistent_path():
    """Test security scan on non-existent path"""
    result = await security_scan("/nonexistent/path")

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_check_type_coverage_full(tmp_path):
    """Test type coverage on fully typed code"""
    test_file = tmp_path / "typed.py"
    content = """\"\"\"Fully typed module.\"\"\"


def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b


def multiply(x: float, y: float) -> float:
    \"\"\"Multiply two numbers.\"\"\"
    return x * y


class Calculator:
    \"\"\"A simple calculator.\"\"\"

    def __init__(self, initial: int = 0) -> None:
        self.value: int = initial

    def add(self, x: int) -> None:
        \"\"\"Add to value.\"\"\"
        self.value += x
"""
    test_file.write_text(content)

    result = await check_type_coverage(str(test_file))

    assert result["success"] is True
    assert "type_coverage_percent" in result
    assert result["type_coverage_percent"] >= 90  # Should be high for fully typed code
    assert "total_functions" in result
    assert "typed_functions" in result


@pytest.mark.asyncio
async def test_check_type_coverage_partial(tmp_path):
    """Test type coverage on partially typed code"""
    test_file = tmp_path / "partial.py"
    content = """def typed_func(x: int) -> int:
    return x * 2

def untyped_func(x):
    return x + 1

def mixed_func(a: int, b):
    return a + b
"""
    test_file.write_text(content)

    result = await check_type_coverage(str(test_file))

    assert result["success"] is True
    assert result["type_coverage_percent"] < 100
    assert result["type_coverage_percent"] > 0


@pytest.mark.asyncio
async def test_check_type_coverage_none(tmp_path):
    """Test type coverage on untyped code"""
    test_file = tmp_path / "untyped.py"
    content = """def func1(x):
    return x

def func2(a, b):
    return a + b
"""
    test_file.write_text(content)

    result = await check_type_coverage(str(test_file))

    assert result["success"] is True
    assert result["type_coverage_percent"] == 0


@pytest.mark.asyncio
async def test_check_type_coverage_nonexistent():
    """Test type coverage on non-existent file"""
    result = await check_type_coverage("/nonexistent/file.py")

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_documentation_coverage_full(tmp_path):
    """Test documentation coverage on fully documented code"""
    test_file = tmp_path / "documented.py"
    content = """\"\"\"Module for calculations.\"\"\"


def add(a, b):
    \"\"\"Add two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    \"\"\"
    return a + b


class Calculator:
    \"\"\"A calculator class.\"\"\"

    def multiply(self, x, y):
        \"\"\"Multiply two numbers.\"\"\"
        return x * y
"""
    test_file.write_text(content)

    result = await documentation_coverage(str(test_file))

    assert result["success"] is True
    assert "doc_coverage_percent" in result
    assert result["doc_coverage_percent"] >= 90  # Should be high
    assert "total_items" in result
    assert "documented_items" in result


@pytest.mark.asyncio
async def test_documentation_coverage_partial(tmp_path):
    """Test documentation coverage on partially documented code"""
    test_file = tmp_path / "partial_docs.py"
    content = """def documented():
    \"\"\"This function has a docstring.\"\"\"
    pass

def undocumented():
    pass

class MyClass:
    def method1(self):
        \"\"\"Documented method.\"\"\"
        pass

    def method2(self):
        pass
"""
    test_file.write_text(content)

    result = await documentation_coverage(str(test_file))

    assert result["success"] is True
    assert 0 < result["doc_coverage_percent"] < 100


@pytest.mark.asyncio
async def test_documentation_coverage_none(tmp_path):
    """Test documentation coverage on undocumented code"""
    test_file = tmp_path / "no_docs.py"
    content = """def func1():
    pass

def func2():
    return 1
"""
    test_file.write_text(content)

    result = await documentation_coverage(str(test_file))

    assert result["success"] is True
    assert result["doc_coverage_percent"] == 0


@pytest.mark.asyncio
async def test_documentation_coverage_module_only(tmp_path):
    """Test documentation with only module docstring"""
    test_file = tmp_path / "module_doc.py"
    content = """\"\"\"This module has documentation.\"\"\"

def func():
    pass
"""
    test_file.write_text(content)

    result = await documentation_coverage(str(test_file))

    assert result["success"] is True
    assert "module_docstring" in result
    assert result["module_docstring"] is True


@pytest.mark.asyncio
async def test_documentation_coverage_nonexistent():
    """Test documentation coverage on non-existent file"""
    result = await documentation_coverage("/nonexistent/file.py")

    assert result["success"] is False
    assert "error" in result
