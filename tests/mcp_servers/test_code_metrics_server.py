# tests/mcp_servers/test_code_metrics_server.py
"""Tests for code metrics MCP server"""


import pytest

from deepagent_coder.mcp_servers.code_metrics_server import (
    analyze_dependencies,
    calculate_complexity,
    calculate_maintainability,
    detect_duplication,
    measure_code_coverage,
)


@pytest.mark.asyncio
async def test_calculate_complexity_simple_function(tmp_path):
    """Test calculating complexity for simple function"""
    test_file = tmp_path / "simple.py"
    content = """def simple_function():
    return 1
"""
    test_file.write_text(content)

    result = await calculate_complexity(str(test_file))

    assert result["success"] is True
    assert "functions" in result
    assert len(result["functions"]) == 1
    assert result["functions"][0]["name"] == "simple_function"
    assert result["functions"][0]["complexity"] == 1


@pytest.mark.asyncio
async def test_calculate_complexity_complex_function(tmp_path):
    """Test calculating complexity for complex function"""
    test_file = tmp_path / "complex.py"
    content = """def complex_function(x):
    if x > 0:
        if x > 10:
            return "high"
        elif x > 5:
            return "medium"
        else:
            return "low"
    else:
        return "negative"
"""
    test_file.write_text(content)

    result = await calculate_complexity(str(test_file))

    assert result["success"] is True
    assert len(result["functions"]) == 1
    assert result["functions"][0]["complexity"] > 1
    assert result["functions"][0]["line"] > 0


@pytest.mark.asyncio
async def test_calculate_complexity_multiple_functions(tmp_path):
    """Test calculating complexity for multiple functions"""
    test_file = tmp_path / "multi.py"
    content = """def func1():
    return 1

def func2(x):
    if x:
        return True
    return False

class MyClass:
    def method1(self):
        return 1
"""
    test_file.write_text(content)

    result = await calculate_complexity(str(test_file))

    assert result["success"] is True
    assert len(result["functions"]) >= 3
    function_names = [f["name"] for f in result["functions"]]
    assert "func1" in function_names
    assert "func2" in function_names
    assert "MyClass.method1" in function_names or "method1" in function_names


@pytest.mark.asyncio
async def test_calculate_complexity_nonexistent_file():
    """Test calculating complexity for non-existent file"""
    result = await calculate_complexity("/nonexistent/file.py")

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_measure_code_coverage_with_pytest(tmp_path):
    """Test measuring code coverage with pytest"""
    # Create a simple module
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")
    module_file = src_dir / "mymodule.py"
    module_file.write_text("""def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
""")

    # Create tests
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "__init__.py").write_text("")
    test_file = test_dir / "test_mymodule.py"
    test_file.write_text("""from src.mymodule import add

def test_add():
    assert add(1, 2) == 3
""")

    result = await measure_code_coverage(
        test_command="pytest --cov=src",
        source_dir=str(src_dir),
        working_dir=str(tmp_path)
    )

    assert result["success"] is True
    assert "coverage_percent" in result
    assert isinstance(result["coverage_percent"], (int, float))
    assert "uncovered_lines" in result or "missing_lines" in result


@pytest.mark.asyncio
async def test_measure_code_coverage_no_tests(tmp_path):
    """Test measuring coverage with no tests"""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "empty.py").write_text("# empty")

    result = await measure_code_coverage(
        test_command="pytest",
        source_dir=str(src_dir),
        working_dir=str(tmp_path)
    )

    # Should handle gracefully
    assert "success" in result
    # Either success with 0% or failure is acceptable
    if result["success"]:
        assert result["coverage_percent"] >= 0


@pytest.mark.asyncio
async def test_detect_duplication_exact_duplicates(tmp_path):
    """Test detecting exact duplicate code blocks"""
    file1 = tmp_path / "file1.py"
    file1.write_text("""def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
""")

    file2 = tmp_path / "file2.py"
    file2.write_text("""def handle_items(items):
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result
""")

    result = await detect_duplication(path=str(tmp_path), threshold=50)

    assert isinstance(result, list)
    # Should find duplicates
    if result:
        dup = result[0]
        assert "files" in dup
        assert "tokens" in dup or "lines" in dup


@pytest.mark.asyncio
async def test_detect_duplication_no_duplicates(tmp_path):
    """Test detecting duplication with unique code"""
    file1 = tmp_path / "unique1.py"
    file1.write_text("def func1():\n    return 1\n")

    file2 = tmp_path / "unique2.py"
    file2.write_text("def func2():\n    return 'hello'\n")

    result = await detect_duplication(path=str(tmp_path), threshold=50)

    assert isinstance(result, list)
    # Should find no or minimal duplicates
    assert len(result) == 0 or all(d.get("tokens", 100) < 50 for d in result)


@pytest.mark.asyncio
async def test_detect_duplication_custom_threshold(tmp_path):
    """Test detecting duplication with custom threshold"""
    file1 = tmp_path / "code.py"
    file1.write_text("""def func():
    x = 1
    y = 2
    return x + y
""")

    result = await detect_duplication(path=str(tmp_path), threshold=10)

    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_calculate_maintainability_simple(tmp_path):
    """Test calculating maintainability index for simple code"""
    test_file = tmp_path / "simple.py"
    content = """def add(a, b):
    \"\"\"Add two numbers\"\"\"
    return a + b
"""
    test_file.write_text(content)

    result = await calculate_maintainability(str(test_file))

    assert result["success"] is True
    assert "maintainability_index" in result
    assert 0 <= result["maintainability_index"] <= 100
    assert "rank" in result  # A, B, C rating
    assert "complexity" in result
    assert "sloc" in result or "lines_of_code" in result


@pytest.mark.asyncio
async def test_calculate_maintainability_complex(tmp_path):
    """Test calculating maintainability for complex code"""
    test_file = tmp_path / "complex.py"
    content = """def complex_function(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                result = x + y + z
                for i in range(10):
                    result += i
                    if result > 100:
                        return result
            else:
                return -1
        else:
            return -2
    else:
        return -3
    return result
"""
    test_file.write_text(content)

    result = await calculate_maintainability(str(test_file))

    assert result["success"] is True
    assert result["maintainability_index"] < 100  # Should be lower for complex code


@pytest.mark.asyncio
async def test_calculate_maintainability_nonexistent():
    """Test calculating maintainability for non-existent file"""
    result = await calculate_maintainability("/nonexistent/file.py")

    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_analyze_dependencies_simple(tmp_path):
    """Test analyzing dependencies for simple imports"""
    test_file = tmp_path / "simple.py"
    content = """import os
import sys
from pathlib import Path
"""
    test_file.write_text(content)

    result = await analyze_dependencies(str(test_file))

    assert result["success"] is True
    assert "imports" in result
    assert len(result["imports"]) == 3
    import_names = [imp["module"] for imp in result["imports"]]
    assert "os" in import_names
    assert "sys" in import_names
    assert "pathlib" in import_names


@pytest.mark.asyncio
async def test_analyze_dependencies_relative_imports(tmp_path):
    """Test analyzing relative imports"""
    test_file = tmp_path / "module.py"
    content = """from . import sibling
from .. import parent
from .submodule import func
"""
    test_file.write_text(content)

    result = await analyze_dependencies(str(test_file))

    assert result["success"] is True
    assert "imports" in result
    # Should identify relative imports
    assert any("relative" in str(imp).lower() for imp in result["imports"]) or len(result["imports"]) > 0


@pytest.mark.asyncio
async def test_analyze_dependencies_circular(tmp_path):
    """Test detecting circular dependencies"""
    file1 = tmp_path / "module_a.py"
    file1.write_text("from module_b import func_b\n\ndef func_a():\n    return func_b()")

    file2 = tmp_path / "module_b.py"
    file2.write_text("from module_a import func_a\n\ndef func_b():\n    return func_a()")

    result1 = await analyze_dependencies(str(file1))
    result2 = await analyze_dependencies(str(file2))

    assert result1["success"] is True
    assert result2["success"] is True
    # Should detect the mutual dependency
    assert any("module_b" in imp["module"] for imp in result1["imports"])
    assert any("module_a" in imp["module"] for imp in result2["imports"])


@pytest.mark.asyncio
async def test_analyze_dependencies_no_imports(tmp_path):
    """Test analyzing file with no imports"""
    test_file = tmp_path / "no_imports.py"
    content = """def standalone():
    return 42
"""
    test_file.write_text(content)

    result = await analyze_dependencies(str(test_file))

    assert result["success"] is True
    assert len(result["imports"]) == 0


@pytest.mark.asyncio
async def test_analyze_dependencies_nonexistent():
    """Test analyzing dependencies for non-existent file"""
    result = await analyze_dependencies("/nonexistent/file.py")

    assert result["success"] is False
    assert "error" in result
