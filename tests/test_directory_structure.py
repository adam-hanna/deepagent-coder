# tests/test_directory_structure.py
from pathlib import Path


def test_source_directory_structure():
    """Verify all required directories exist"""
    base = Path("src/deepagent_claude")

    required_dirs = [
        base,
        base / "core",
        base / "mcp_servers",
        base / "middleware",
        base / "subagents",
        base / "cli",
        base / "utils",
    ]

    for dir_path in required_dirs:
        assert dir_path.exists(), f"Missing directory: {dir_path}"
        assert (dir_path / "__init__.py").exists(), f"Missing __init__.py in {dir_path}"


def test_tests_directory_structure():
    """Verify test directory mirrors source structure"""
    base = Path("tests")

    required_dirs = [
        base / "core",
        base / "mcp_servers",
        base / "middleware",
        base / "cli",
    ]

    for dir_path in required_dirs:
        assert dir_path.exists(), f"Missing test directory: {dir_path}"
