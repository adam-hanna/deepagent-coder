# tests/mcp_servers/test_testing_server.py
from pathlib import Path

import pytest

from deepagent_claude.mcp_servers.testing_server import _get_coverage_impl as get_coverage
from deepagent_claude.mcp_servers.testing_server import _run_pytest_impl as run_pytest


@pytest.fixture
def test_project(tmp_path):
    """Create a temporary test project"""
    # Create source file
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").touch()
    (src_dir / "calculator.py").write_text(
        """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
"""
    )

    # Create test file
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").touch()
    (tests_dir / "test_calculator.py").write_text(
        """
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.calculator import add, subtract, multiply

def test_add():
    assert add(2, 3) == 5

def test_subtract():
    assert subtract(5, 3) == 2

def test_multiply():
    assert multiply(3, 4) == 12

def test_failing():
    assert add(1, 1) == 3  # This will fail
"""
    )

    return str(tmp_path)


@pytest.mark.asyncio
async def test_run_pytest_executes_tests(test_project):
    """Test running pytest on project"""
    result = await run_pytest(test_project)

    assert "error" not in result
    assert result["total_tests"] >= 3
    assert result["passed"] >= 2
    assert result["failed"] >= 1


@pytest.mark.asyncio
async def test_run_pytest_with_specific_file(test_project):
    """Test running pytest on specific file"""
    test_file = str(Path(test_project) / "tests" / "test_calculator.py")
    result = await run_pytest(test_project, test_path=test_file)

    assert "error" not in result
    assert result["total_tests"] >= 3


@pytest.mark.asyncio
async def test_run_pytest_with_markers(test_project):
    """Test running pytest with markers"""
    # Add marked test
    test_file = Path(test_project) / "tests" / "test_marked.py"
    test_file.write_text(
        """
import pytest

@pytest.mark.slow
def test_slow_operation():
    assert True

@pytest.mark.fast
def test_fast_operation():
    assert True
"""
    )

    result = await run_pytest(test_project, markers="fast")

    assert "error" not in result
    # Should only run fast tests


@pytest.mark.asyncio
async def test_get_coverage_reports_coverage(test_project):
    """Test coverage reporting"""
    result = await get_coverage(test_project, source_dirs=["src"])

    assert "error" not in result
    assert "coverage_percent" in result
    assert result["coverage_percent"] >= 0
    assert result["coverage_percent"] <= 100


@pytest.mark.asyncio
async def test_run_pytest_handles_nonexistent_path():
    """Test pytest with non-existent path"""
    result = await run_pytest("/nonexistent/path")

    assert "error" in result
    assert "not found" in result["error"].lower()
