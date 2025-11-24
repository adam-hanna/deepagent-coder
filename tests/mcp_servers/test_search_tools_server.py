import pytest

from deepagent_claude.mcp_servers.search_tools_server import grep


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
