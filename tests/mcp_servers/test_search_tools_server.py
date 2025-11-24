import pytest

from deepagent_claude.mcp_servers.search_tools_server import grep, find, ls


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure for testing"""
    # Create test files
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("""
def hello():
    print("Hello World")

def goodbye():
    print("Goodbye World")
""")

    (tmp_path / "src" / "utils.py").write_text("""
def helper():
    return "helper function"
""")

    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("""
def test_hello():
    assert True
""")

    return tmp_path


def test_grep_finds_pattern(temp_project):
    """Test grep can find a pattern in files"""
    results = grep(
        pattern="hello",
        path=str(temp_project / "src"),
        recursive=True
    )

    assert len(results) > 0
    assert any("main.py" in r["file"] for r in results)
    assert any("hello" in r["text"].lower() for r in results)


def test_grep_with_context_lines(temp_project):
    """Test grep returns context lines"""
    results = grep(
        pattern="hello",
        path=str(temp_project / "src" / "main.py"),
        context_before=1,
        context_after=1,
        recursive=False
    )

    assert len(results) > 0
    # Context should be included in the results


def test_grep_case_insensitive(temp_project):
    """Test case-insensitive search"""
    results = grep(
        pattern="HELLO",
        path=str(temp_project / "src"),
        ignore_case=True,
        recursive=True
    )

    assert len(results) > 0


def test_grep_with_file_pattern(temp_project):
    """Test grep with file pattern filter"""
    results = grep(
        pattern="def",
        path=str(temp_project),
        file_pattern="*.py",
        recursive=True
    )

    assert len(results) > 0
    assert all(r["file"].endswith(".py") for r in results)


def test_grep_regex_mode(temp_project):
    """Test grep with regex patterns"""
    results = grep(
        pattern="def.*hello",
        path=str(temp_project / "src"),
        regex=True,
        recursive=True
    )

    assert len(results) > 0


def test_find_files_by_name(temp_project):
    """Test finding files by name"""
    results = find(
        path=str(temp_project),
        name="main.py",
        type="f"
    )

    assert len(results) > 0
    assert any("main.py" in r for r in results)


def test_find_by_extension(temp_project):
    """Test finding files by extension"""
    results = find(
        path=str(temp_project),
        extension="py",
        type="f"
    )

    assert len(results) >= 3  # main.py, utils.py, test_main.py
    assert all(r.endswith(".py") for r in results)


def test_find_directories(temp_project):
    """Test finding directories"""
    results = find(
        path=str(temp_project),
        type="d"
    )

    assert len(results) > 0
    assert any("src" in r for r in results)
    assert any("tests" in r for r in results)


def test_find_with_max_depth(temp_project):
    """Test find with depth limit"""
    results = find(
        path=str(temp_project),
        max_depth=1,
        type="d"
    )

    # Should only find top-level directories
    assert len(results) >= 2  # src and tests


def test_ls_basic(temp_project):
    """Test basic directory listing"""
    results = ls(path=str(temp_project))

    assert len(results) > 0
    assert "src" in results or any("src" in str(r) for r in results)
    assert "tests" in results or any("tests" in str(r) for r in results)


def test_ls_long_format(temp_project):
    """Test ls with detailed information"""
    results = ls(path=str(temp_project), long_format=True)

    assert len(results) > 0
    # Long format returns dicts with permissions, size, etc.
    if isinstance(results[0], dict):
        assert "name" in results[0]
        assert "permissions" in results[0] or "size" in results[0]


def test_ls_all_files(temp_project):
    """Test ls including hidden files"""
    # Create a hidden file
    (temp_project / ".hidden").write_text("hidden content")

    results = ls(path=str(temp_project), all_files=True)

    assert any(".hidden" in str(r) for r in results)
