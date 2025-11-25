# tests/mcp_servers/test_build_tools_server.py
"""Tests for build tools MCP server"""

import pytest
from pathlib import Path

from deepagent_coder.mcp_servers.build_tools_server import (
    find_files_by_pattern,
    analyze_file_stats,
    count_pattern_occurrences,
    extract_structure,
)


@pytest.mark.asyncio
async def test_find_files_by_pattern_simple(tmp_path):
    """Test finding files with simple pattern"""
    # Create test files
    (tmp_path / "test1.py").write_text("# test file")
    (tmp_path / "test2.py").write_text("# test file")
    (tmp_path / "test.txt").write_text("text file")

    result = await find_files_by_pattern(pattern="*.py", path=str(tmp_path), recursive=False)

    assert len(result) == 2
    assert all(str(f).endswith(".py") for f in result)


@pytest.mark.asyncio
async def test_find_files_by_pattern_recursive(tmp_path):
    """Test finding files recursively"""
    # Create nested structure
    (tmp_path / "file1.js").write_text("// file")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file2.js").write_text("// file")

    result = await find_files_by_pattern(pattern="*.js", path=str(tmp_path), recursive=True)

    assert len(result) >= 2
    assert any("file1.js" in str(f) for f in result)
    assert any("file2.js" in str(f) for f in result)


@pytest.mark.asyncio
async def test_find_files_by_pattern_file_type_filter(tmp_path):
    """Test filtering by file type (files only)"""
    (tmp_path / "test.py").write_text("# test")
    (tmp_path / "dir").mkdir()

    result = await find_files_by_pattern(pattern="*", path=str(tmp_path), recursive=False, file_type="f")

    # Should only include files, not directories
    assert all(Path(f).is_file() for f in result)
    assert not any(Path(f).is_dir() for f in result)


@pytest.mark.asyncio
async def test_find_files_by_pattern_directories_only(tmp_path):
    """Test filtering by type (directories only)"""
    (tmp_path / "file.txt").write_text("text")
    (tmp_path / "testdir").mkdir()

    result = await find_files_by_pattern(pattern="*", path=str(tmp_path), recursive=False, file_type="d")

    # Should only include directories
    assert all(Path(f).is_dir() for f in result)


@pytest.mark.asyncio
async def test_analyze_file_stats_basic(tmp_path):
    """Test basic file statistics"""
    test_file = tmp_path / "test.txt"
    content = "Line 1\nLine 2\nLine 3\n"
    test_file.write_text(content)

    result = await analyze_file_stats(str(test_file))

    assert result["success"] is True
    assert result["size_bytes"] == len(content)
    assert result["lines"] == 3  # splitlines() returns 3 for this content
    assert result["is_file"] is True
    assert result["is_dir"] is False


@pytest.mark.asyncio
async def test_analyze_file_stats_with_code_metrics(tmp_path):
    """Test file statistics with code metrics"""
    test_file = tmp_path / "test.py"
    content = """# This is a comment
import os
import sys

def hello():
    print("Hello")

def world():
    print("World")
"""
    test_file.write_text(content)

    result = await analyze_file_stats(str(test_file))

    assert result["success"] is True
    assert "code_metrics" in result
    assert result["code_metrics"]["import_lines"] == 2
    assert result["code_metrics"]["function_definitions"] == 2
    assert result["code_metrics"]["comment_lines"] >= 1


@pytest.mark.asyncio
async def test_analyze_file_stats_nonexistent():
    """Test analyzing non-existent file"""
    result = await analyze_file_stats("/nonexistent/file.txt")

    assert result["success"] is False
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_analyze_file_stats_directory(tmp_path):
    """Test analyzing a directory"""
    test_dir = tmp_path / "testdir"
    test_dir.mkdir()

    result = await analyze_file_stats(str(test_dir))

    assert result["success"] is True
    assert result["is_dir"] is True
    assert result["is_file"] is False


@pytest.mark.asyncio
async def test_count_pattern_occurrences_simple(tmp_path):
    """Test counting simple string pattern"""
    file1 = tmp_path / "test1.txt"
    file1.write_text("hello world\nhello again")

    file2 = tmp_path / "test2.txt"
    file2.write_text("goodbye world")

    result = await count_pattern_occurrences(
        pattern="hello",
        path=str(tmp_path),
        is_regex=False
    )

    assert result["total_matches"] == 2
    assert result["files_with_matches"] == 1
    assert str(file1) in result["matches_by_file"]


@pytest.mark.asyncio
async def test_count_pattern_occurrences_regex(tmp_path):
    """Test counting with regex pattern"""
    file1 = tmp_path / "test.py"
    file1.write_text("def func1():\n    pass\n\ndef func2():\n    pass")

    result = await count_pattern_occurrences(
        pattern=r"def\s+\w+",
        path=str(tmp_path),
        is_regex=True
    )

    assert result["total_matches"] == 2
    assert result["files_with_matches"] == 1


@pytest.mark.asyncio
async def test_count_pattern_occurrences_case_insensitive(tmp_path):
    """Test case-insensitive pattern matching"""
    file1 = tmp_path / "test.txt"
    file1.write_text("Hello HELLO hello")

    result = await count_pattern_occurrences(
        pattern="hello",
        path=str(tmp_path),
        is_regex=False,
        ignore_case=True
    )

    assert result["total_matches"] == 3


@pytest.mark.asyncio
async def test_count_pattern_occurrences_file_extensions(tmp_path):
    """Test filtering by file extensions"""
    (tmp_path / "test.py").write_text("import os")
    (tmp_path / "test.txt").write_text("import os")

    result = await count_pattern_occurrences(
        pattern="import",
        path=str(tmp_path),
        file_extensions=["py"],
        is_regex=False
    )

    # Should only match in .py file
    assert result["files_with_matches"] == 1
    assert any(".py" in str(f) for f in result["matches_by_file"].keys())


@pytest.mark.asyncio
async def test_extract_structure_python(tmp_path):
    """Test extracting structure from Python file"""
    py_file = tmp_path / "test.py"
    content = """# Module docstring
import os

class MyClass:
    def method1(self):
        pass

    def method2(self):
        pass

def standalone_function():
    pass
"""
    py_file.write_text(content)

    result = await extract_structure(str(py_file))

    assert result["success"] is True
    assert len(result["sections"]) > 0
    # Should find class and function definitions
    section_types = [s["type"] for s in result["sections"]]
    assert any("class" in t for t in section_types)
    assert any("function" in t for t in section_types)


@pytest.mark.asyncio
async def test_extract_structure_markdown(tmp_path):
    """Test extracting structure from Markdown file"""
    md_file = tmp_path / "test.md"
    content = """# Main Header

Some content

## Section 1

Content here

## Section 2

More content
"""
    md_file.write_text(content)

    result = await extract_structure(str(md_file))

    assert result["success"] is True
    assert len(result["sections"]) >= 3
    # Should find markdown headers
    assert any("Main Header" in s["name"] for s in result["sections"])


@pytest.mark.asyncio
async def test_extract_structure_with_max_depth(tmp_path):
    """Test structure extraction with depth limit"""
    py_file = tmp_path / "test.py"
    content = """class Outer:
    class Inner:
        class DeepNested:
            def deep_method(self):
                pass
"""
    py_file.write_text(content)

    result = await extract_structure(str(py_file), max_depth=2)

    assert result["success"] is True
    # Should respect max_depth in outline
    assert len(result["outline"]) > 0


@pytest.mark.asyncio
async def test_extract_structure_nonexistent():
    """Test extracting structure from non-existent file"""
    result = await extract_structure("/nonexistent/file.py")

    assert result["success"] is False
    assert "error" in result
