# Code Navigator Agent Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a Code Navigator subagent that uses grep, find, and other filesystem tools to search codebases and help other agents locate code artifacts.

**Architecture:** Create a new MCP server (search_tools_server.py) with filesystem search tools, a new subagent (code_navigator.py) that uses these tools intelligently, and integrate it into the existing multi-agent system. The agent will reason about search strategies rather than relying on hardcoded patterns.

**Tech Stack:** FastMCP, Python subprocess, asyncio, langgraph, langchain-ollama

---

## Task 1: Create Search Tools MCP Server (grep tool)

**Files:**
- Create: `src/deepagent_claude/mcp_servers/search_tools_server.py`
- Test: `tests/mcp_servers/test_search_tools_server.py`

**Step 1: Write failing test for grep tool**

```python
# tests/mcp_servers/test_search_tools_server.py
import pytest
import tempfile
from pathlib import Path
from deepagent_claude.mcp_servers.search_tools_server import (
    grep, find, ls, head, tail, wc, ripgrep
)


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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/mcp_servers/test_search_tools_server.py::test_grep_finds_pattern -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'deepagent_claude.mcp_servers.search_tools_server'"

**Step 3: Implement grep tool in MCP server**

```python
# src/deepagent_claude/mcp_servers/search_tools_server.py
"""Search Tools MCP Server - filesystem search and navigation tools"""

import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

from fastmcp import FastMCP

mcp = FastMCP("Search Tools")


@mcp.tool()
def grep(
    pattern: str,
    path: str = ".",
    file_pattern: Optional[str] = None,
    recursive: bool = True,
    context_before: int = 0,
    context_after: int = 0,
    ignore_case: bool = False,
    regex: bool = False,
) -> list[dict[str, Any]]:
    """
    Search for pattern in files using grep.

    Args:
        pattern: Pattern to search for
        path: Directory or file path to search
        file_pattern: Optional glob pattern to filter files (e.g., "*.py")
        recursive: Search recursively through directories
        context_before: Number of lines to show before match
        context_after: Number of lines to show after match
        ignore_case: Case-insensitive search
        regex: Treat pattern as regex (default: fixed string)

    Returns:
        List of matches with file, line number, and text
    """
    cmd = ["grep"]

    # Build grep flags
    if recursive:
        cmd.append("-r")
    if ignore_case:
        cmd.append("-i")
    if regex:
        cmd.append("-E")  # Extended regex
    else:
        cmd.append("-F")  # Fixed string (faster)

    # Line numbers always
    cmd.append("-n")

    # Context lines
    if context_before > 0:
        cmd.extend(["-B", str(context_before)])
    if context_after > 0:
        cmd.extend(["-A", str(context_after)])

    # Add pattern and path
    cmd.append(pattern)
    cmd.append(path)

    # File pattern filter
    if file_pattern:
        cmd.extend(["--include", file_pattern])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Parse grep output
        matches = []
        for line in result.stdout.strip().split("\n"):
            if line and ":" in line:
                # Format: file:line:text or file:line-text (for context)
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    file_path = parts[0]
                    line_num = parts[1]
                    text = parts[2] if len(parts) > 2 else ""

                    matches.append({
                        "file": file_path,
                        "line": line_num,
                        "text": text,
                        "pattern": pattern,
                    })

        return matches
    except subprocess.TimeoutExpired:
        return [{"error": "Search timed out after 60 seconds"}]
    except Exception as e:
        return [{"error": f"Grep failed: {str(e)}"}]


def run_server():
    """Run the Search Tools MCP server"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
```

**Step 4: Run tests to verify grep passes**

Run: `pytest tests/mcp_servers/test_search_tools_server.py -k grep -v`
Expected: All grep tests PASS

**Step 5: Commit grep tool**

```bash
git add src/deepagent_claude/mcp_servers/search_tools_server.py tests/mcp_servers/test_search_tools_server.py
git commit -m "feat(search-tools): add grep tool to search tools MCP server"
```

---

## Task 2: Add find tool to Search Tools MCP Server

**Files:**
- Modify: `src/deepagent_claude/mcp_servers/search_tools_server.py`
- Modify: `tests/mcp_servers/test_search_tools_server.py`

**Step 1: Write failing test for find tool**

```python
# Add to tests/mcp_servers/test_search_tools_server.py

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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/mcp_servers/test_search_tools_server.py::test_find_files_by_name -v`
Expected: FAIL with "NameError: name 'find' is not defined"

**Step 3: Implement find tool**

```python
# Add to src/deepagent_claude/mcp_servers/search_tools_server.py

@mcp.tool()
def find(
    path: str = ".",
    name: Optional[str] = None,
    type: Optional[str] = None,  # "f" for file, "d" for directory
    extension: Optional[str] = None,
    max_depth: Optional[int] = None,
) -> list[str]:
    """
    Find files and directories by name, type, or extension.

    Args:
        path: Starting directory for search
        name: Exact filename to match
        type: "f" for files only, "d" for directories only
        extension: File extension to match (without dot)
        max_depth: Maximum depth to search

    Returns:
        List of file/directory paths
    """
    cmd = ["find", path]

    if max_depth is not None:
        cmd.extend(["-maxdepth", str(max_depth)])

    if type:
        cmd.extend(["-type", type])

    if name:
        cmd.extend(["-name", name])
    elif extension:
        cmd.extend(["-name", f"*.{extension}"])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        files = [f for f in result.stdout.strip().split("\n") if f]
        return files
    except subprocess.TimeoutExpired:
        return ["Error: Find timed out after 30 seconds"]
    except Exception as e:
        return [f"Error: {str(e)}"]
```

**Step 4: Run tests to verify find passes**

Run: `pytest tests/mcp_servers/test_search_tools_server.py -k find -v`
Expected: All find tests PASS

**Step 5: Commit find tool**

```bash
git add src/deepagent_claude/mcp_servers/search_tools_server.py tests/mcp_servers/test_search_tools_server.py
git commit -m "feat(search-tools): add find tool for file/directory discovery"
```

---

## Task 3: Add ls tool to Search Tools MCP Server

**Files:**
- Modify: `src/deepagent_claude/mcp_servers/search_tools_server.py`
- Modify: `tests/mcp_servers/test_search_tools_server.py`

**Step 1: Write failing test for ls tool**

```python
# Add to tests/mcp_servers/test_search_tools_server.py

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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/mcp_servers/test_search_tools_server.py::test_ls_basic -v`
Expected: FAIL with "NameError: name 'ls' is not defined"

**Step 3: Implement ls tool**

```python
# Add to src/deepagent_claude/mcp_servers/search_tools_server.py

@mcp.tool()
def ls(
    path: str = ".",
    all_files: bool = False,
    long_format: bool = False,
) -> list[dict[str, Any]] | list[str]:
    """
    List directory contents.

    Args:
        path: Directory to list
        all_files: Include hidden files (starting with .)
        long_format: Show detailed information (permissions, size, date)

    Returns:
        List of files/directories (strings or dicts if long_format)
    """
    cmd = ["ls"]

    if all_files:
        cmd.append("-a")
    if long_format:
        cmd.append("-l")

    cmd.append(path)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if long_format:
            # Parse ls -l output
            files = []
            lines = result.stdout.strip().split("\n")

            # Skip first line if it's "total XXX"
            start_idx = 1 if lines and lines[0].startswith("total") else 0

            for line in lines[start_idx:]:
                if line:
                    parts = line.split(None, 8)
                    if len(parts) >= 9:
                        files.append({
                            "permissions": parts[0],
                            "links": parts[1],
                            "owner": parts[2],
                            "group": parts[3],
                            "size": parts[4],
                            "date": f"{parts[5]} {parts[6]} {parts[7]}",
                            "name": parts[8],
                        })
                    elif len(parts) >= 1:
                        # Simpler format for some systems
                        files.append({"name": " ".join(parts)})
            return files
        else:
            files = result.stdout.strip().split("\n")
            return [f for f in files if f]

    except Exception as e:
        return [{"error": str(e)}]
```

**Step 4: Run tests to verify ls passes**

Run: `pytest tests/mcp_servers/test_search_tools_server.py -k ls -v`
Expected: All ls tests PASS

**Step 5: Commit ls tool**

```bash
git add src/deepagent_claude/mcp_servers/search_tools_server.py tests/mcp_servers/test_search_tools_server.py
git commit -m "feat(search-tools): add ls tool for directory listing"
```

---

## Task 4: Add head, tail, and wc tools to Search Tools MCP Server

**Files:**
- Modify: `src/deepagent_claude/mcp_servers/search_tools_server.py`
- Modify: `tests/mcp_servers/test_search_tools_server.py`

**Step 1: Write failing tests for head, tail, wc**

```python
# Add to tests/mcp_servers/test_search_tools_server.py

def test_head_reads_first_lines(temp_project):
    """Test reading first N lines of file"""
    content = head(file_path=str(temp_project / "src" / "main.py"), lines=2)

    assert isinstance(content, str)
    assert len(content) > 0
    # Should contain first lines (def hello)


def test_tail_reads_last_lines(temp_project):
    """Test reading last N lines of file"""
    content = tail(file_path=str(temp_project / "src" / "main.py"), lines=2)

    assert isinstance(content, str)
    assert len(content) > 0


def test_wc_counts_lines(temp_project):
    """Test counting lines in file"""
    result = wc(file_path=str(temp_project / "src" / "main.py"), lines=True)

    assert isinstance(result, dict)
    assert "lines" in result
    assert result["lines"] > 0


def test_wc_counts_words(temp_project):
    """Test counting words in file"""
    result = wc(
        file_path=str(temp_project / "src" / "main.py"),
        lines=False,
        words=True
    )

    assert isinstance(result, dict)
    assert "words" in result
    assert result["words"] > 0


def test_wc_counts_characters(temp_project):
    """Test counting characters in file"""
    result = wc(
        file_path=str(temp_project / "src" / "main.py"),
        lines=False,
        chars=True
    )

    assert isinstance(result, dict)
    assert "characters" in result
    assert result["characters"] > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/mcp_servers/test_search_tools_server.py::test_head_reads_first_lines -v`
Expected: FAIL with "NameError: name 'head' is not defined"

**Step 3: Implement head, tail, and wc tools**

```python
# Add to src/deepagent_claude/mcp_servers/search_tools_server.py

@mcp.tool()
def head(file_path: str, lines: int = 10) -> str:
    """
    Show first N lines of a file.

    Args:
        file_path: Path to file
        lines: Number of lines to show (default: 10)

    Returns:
        First N lines of file as string
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            head_lines = []
            for i, line in enumerate(f):
                if i >= lines:
                    break
                head_lines.append(line.rstrip())
        return "\n".join(head_lines)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def tail(file_path: str, lines: int = 10) -> str:
    """
    Show last N lines of a file.

    Args:
        file_path: Path to file
        lines: Number of lines to show (default: 10)

    Returns:
        Last N lines of file as string
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            tail_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        return "".join(tail_lines).rstrip()
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def wc(
    file_path: str,
    lines: bool = True,
    words: bool = False,
    chars: bool = False,
) -> dict[str, Any]:
    """
    Count lines, words, or characters in file.

    Args:
        file_path: Path to file
        lines: Count lines (default: True)
        words: Count words
        chars: Count characters

    Returns:
        Dictionary with requested counts
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        result = {}
        if lines:
            result["lines"] = content.count("\n") + (
                1 if content and not content.endswith("\n") else 0
            )
        if words:
            result["words"] = len(content.split())
        if chars:
            result["characters"] = len(content)

        return result
    except Exception as e:
        return {"error": str(e)}
```

**Step 4: Run tests to verify all pass**

Run: `pytest tests/mcp_servers/test_search_tools_server.py -k "head or tail or wc" -v`
Expected: All tests PASS

**Step 5: Commit head, tail, wc tools**

```bash
git add src/deepagent_claude/mcp_servers/search_tools_server.py tests/mcp_servers/test_search_tools_server.py
git commit -m "feat(search-tools): add head, tail, and wc tools for file inspection"
```

---

## Task 5: Add ripgrep tool to Search Tools MCP Server

**Files:**
- Modify: `src/deepagent_claude/mcp_servers/search_tools_server.py`
- Modify: `tests/mcp_servers/test_search_tools_server.py`

**Step 1: Write failing test for ripgrep**

```python
# Add to tests/mcp_servers/test_search_tools_server.py

def test_ripgrep_basic_search(temp_project):
    """Test basic ripgrep search"""
    results = ripgrep(
        pattern="hello",
        path=str(temp_project / "src")
    )

    assert isinstance(results, list)
    assert len(results) > 0
    if "error" not in results[0]:
        assert any("hello" in r.get("text", "").lower() for r in results)


def test_ripgrep_with_file_type(temp_project):
    """Test ripgrep with file type filter"""
    results = ripgrep(
        pattern="def",
        path=str(temp_project),
        file_type="py"
    )

    assert isinstance(results, list)
    # Should find Python files only


def test_ripgrep_with_context(temp_project):
    """Test ripgrep with context lines"""
    results = ripgrep(
        pattern="hello",
        path=str(temp_project / "src"),
        context=2
    )

    assert isinstance(results, list)
    # Context should provide surrounding lines


def test_ripgrep_fallback_to_grep(temp_project, monkeypatch):
    """Test ripgrep falls back to grep when rg not available"""
    # Mock shutil.which to return None (rg not found)
    monkeypatch.setattr("shutil.which", lambda x: None)

    results = ripgrep(
        pattern="hello",
        path=str(temp_project / "src")
    )

    # Should still work via grep fallback
    assert isinstance(results, list)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/mcp_servers/test_search_tools_server.py::test_ripgrep_basic_search -v`
Expected: FAIL with "NameError: name 'ripgrep' is not defined"

**Step 3: Implement ripgrep tool**

```python
# Add to src/deepagent_claude/mcp_servers/search_tools_server.py

@mcp.tool()
def ripgrep(
    pattern: str,
    path: str = ".",
    file_type: Optional[str] = None,
    context: int = 0,
    multiline: bool = False,
) -> list[dict[str, Any]]:
    """
    Fast search using ripgrep (if available), falls back to grep.

    Args:
        pattern: Pattern to search for
        path: Directory or file path to search
        file_type: Language/file type to filter (e.g., "py", "js")
        context: Number of context lines before and after match
        multiline: Enable multiline search

    Returns:
        List of matches with file, line number, and text
    """
    # Check if ripgrep is available
    if not shutil.which("rg"):
        # Fallback to grep
        return grep(pattern=pattern, path=path, recursive=True, regex=True)

    cmd = ["rg", "--json", "-n"]

    if file_type:
        cmd.extend(["-t", file_type])

    if context > 0:
        cmd.extend(["-C", str(context)])

    if multiline:
        cmd.append("--multiline")

    cmd.extend([pattern, path])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        matches = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    data = json.loads(line)
                    if data.get("type") == "match":
                        match_data = data["data"]
                        matches.append({
                            "file": match_data["path"]["text"],
                            "line": match_data["line_number"],
                            "text": match_data["lines"]["text"].strip(),
                            "column": match_data.get("submatches", [{}])[0].get("start", 0),
                        })
                except json.JSONDecodeError:
                    # Skip malformed JSON lines
                    pass

        return matches if matches else []
    except subprocess.TimeoutExpired:
        return [{"error": "Ripgrep timed out after 60 seconds"}]
    except Exception as e:
        # Fallback to grep on any error
        return grep(pattern=pattern, path=path, recursive=True, regex=True)
```

**Step 4: Run tests to verify ripgrep passes**

Run: `pytest tests/mcp_servers/test_search_tools_server.py -k ripgrep -v`
Expected: All ripgrep tests PASS

**Step 5: Commit ripgrep tool**

```bash
git add src/deepagent_claude/mcp_servers/search_tools_server.py tests/mcp_servers/test_search_tools_server.py
git commit -m "feat(search-tools): add ripgrep tool with grep fallback"
```

---

## Task 6: Create Code Navigator Subagent

**Files:**
- Create: `src/deepagent_claude/subagents/code_navigator.py`
- Test: `tests/subagents/test_code_navigator.py`

**Step 1: Write failing test for code navigator creation**

```python
# tests/subagents/test_code_navigator.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from deepagent_claude.subagents.code_navigator import (
    create_code_navigator,
    get_code_navigator_prompt,
)


@pytest.mark.asyncio
async def test_create_code_navigator():
    """Test creating code navigator subagent"""
    mock_llm = MagicMock()

    with patch("deepagent_claude.subagents.code_navigator.create_react_agent") as mock_create:
        mock_create.return_value = AsyncMock()

        agent = await create_code_navigator(mock_llm)

        assert agent is not None
        mock_create.assert_called_once()


def test_get_code_navigator_prompt():
    """Test code navigator prompt is comprehensive"""
    prompt = get_code_navigator_prompt()

    assert isinstance(prompt, str)
    assert len(prompt) > 100

    # Check for key search strategies
    assert "grep" in prompt.lower()
    assert "find" in prompt.lower()
    assert "API" in prompt or "endpoint" in prompt
    assert "database" in prompt.lower()
    assert "function" in prompt.lower()


@pytest.mark.asyncio
async def test_code_navigator_with_mcp_client():
    """Test code navigator integrates with MCP client"""
    mock_llm = MagicMock()

    with (
        patch("deepagent_claude.subagents.code_navigator.create_react_agent") as mock_create,
        patch("deepagent_claude.subagents.code_navigator.MultiServerMCPClient") as mock_mcp,
    ):
        mock_mcp.return_value.get_tools = AsyncMock(return_value=[])
        mock_create.return_value = AsyncMock()

        agent = await create_code_navigator(mock_llm)

        assert agent is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/subagents/test_code_navigator.py::test_create_code_navigator -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'deepagent_claude.subagents.code_navigator'"

**Step 3: Implement code navigator subagent**

```python
# src/deepagent_claude/subagents/code_navigator.py
"""Code Navigator Subagent - Searches codebases using filesystem tools"""

from typing import Any

from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_react_agent

from deepagent_claude.core.mcp_client import MultiServerMCPClient


def get_code_navigator_prompt() -> str:
    """Get the comprehensive prompt for the code navigator agent"""
    return """You are a code search specialist. You help other agents find code locations using basic search tools.

## Available Tools

- **grep**: Search for patterns in files (supports regex)
- **find**: Find files by name, extension, or path patterns
- **ls**: List directory contents
- **head/tail**: View start/end of files
- **wc**: Count lines in files
- **ripgrep**: Fast search using ripgrep (falls back to grep)

## Search Strategies

### Finding API Endpoints
- Flask: grep for "@app.route" or "@blueprint.route"
- FastAPI: grep for "@app.get", "@app.post", "@router"
- Express: grep for "app.get", "app.post", "router."
- General: search for the API path string, then look nearby for handlers

### Finding Database Calls
- SQL: grep for "SELECT", "INSERT", "UPDATE", "DELETE"
- ORMs: search for ".query", ".filter", ".save()", "objects."
- MongoDB: search for "find(", "insert(", "update("

### Finding Function/Class Definitions
- Python: grep for "def function_name" or "class ClassName"
- JavaScript: grep for "function name" or "const name.*=.*function"
- TypeScript: grep for "function name" or "const name.*:.*=>"
- General: search for the name with word boundaries

### Finding Imports/Dependencies
- Python: grep for "import.*module" or "from.*import"
- JavaScript: grep for "require(" or "import.*from"
- Look at file headers first

### Finding Configuration
- Search for config files: find with names like "config", ".env", "settings"
- Look for capitalized constants: grep for "[A-Z_]+" in config directories

## Best Practices

1. **Start broad, then narrow:**
   - First find relevant files with find
   - Then search within those files with grep

2. **Use context lines:**
   - grep with context_before/context_after to see surrounding code

3. **Chain operations:**
   - find + grep for targeted searches
   - grep + head/tail for specific sections

4. **Verify findings:**
   - Use head/tail to examine context around matches
   - Check file structure with ls before diving deep

5. **Provide structured results:**
   - Always include file path and line numbers
   - Show relevant code context
   - Explain why this location is relevant

## Output Format

Always provide findings as:

```
File: path/to/file.py
Line: 42
Context: [relevant code snippet]
Confidence: High/Medium/Low
Reasoning: Why this is likely the right location
```

## Multi-Step Search Example

When searching for "where is the user login endpoint?":

1. Find API files: `find(path=".", name="*api*", type="f")`
2. Search for login: `grep(pattern="login", path="./api", file_pattern="*.py")`
3. Check for route decorators: `grep(pattern="@.*route", file="<file_from_step_2>", context_after=10)`
4. Verify with head: `head(file_path="<file_from_step_3>", lines=20)`

## Important Notes

- **Other agents rely on your accuracy** - When uncertain, provide multiple possible locations ranked by confidence
- **Context is king** - Always show surrounding code, not just the matching line
- **Think like a developer** - Consider common patterns and conventions
- **Be thorough** - Check obvious places first, then expand search
- **Explain your reasoning** - Help other agents understand why you picked these locations

Remember: You're not just finding text, you're understanding code structure and helping agents navigate it intelligently."""


async def create_code_navigator(llm: BaseChatModel) -> Any:
    """
    Create a code navigator subagent with search tools.

    Args:
        llm: Language model for the agent

    Returns:
        Code navigator agent with search capabilities
    """
    # Initialize MCP client with search tools server
    client = MultiServerMCPClient({
        "search_tools": {
            "transport": "stdio",
            "command": "python",
            "args": ["-m", "deepagent_claude.mcp_servers.search_tools_server"],
        }
    })

    # Get tools from MCP server
    await client.initialize()
    tools = await client.get_tools()

    # Create agent with tools and specialized prompt
    agent = create_react_agent(
        llm,
        tools,
        state_modifier=get_code_navigator_prompt(),
    )

    return agent
```

**Step 4: Run tests to verify code navigator passes**

Run: `pytest tests/subagents/test_code_navigator.py -v`
Expected: All tests PASS

**Step 5: Commit code navigator subagent**

```bash
git add src/deepagent_claude/subagents/code_navigator.py tests/subagents/test_code_navigator.py
git commit -m "feat(subagent): add code navigator subagent with search capabilities"
```

---

## Task 7: Update AgentState to include search_results

**Files:**
- Modify: `src/deepagent_claude/coding_agent.py`

**Step 1: Write failing test for AgentState with search_results**

```python
# Add to tests/test_coding_agent.py

def test_agent_state_includes_search_results():
    """Test AgentState has search_results field"""
    from deepagent_claude.coding_agent import AgentState

    # AgentState should have search_results in its annotations
    assert "search_results" in AgentState.__annotations__
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_coding_agent.py::test_agent_state_includes_search_results -v`
Expected: FAIL with "AssertionError: assert 'search_results' in ..."

**Step 3: Update AgentState to include search_results**

```python
# Modify in src/deepagent_claude/coding_agent.py
# Find the AgentState class and update it

class AgentState(TypedDict):
    """State passed between agents in the graph"""
    messages: Annotated[list, add]
    current_file: str
    project_context: dict
    next_agent: str
    search_results: dict  # NEW: Store search findings from code navigator
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_coding_agent.py::test_agent_state_includes_search_results -v`
Expected: PASS

**Step 5: Commit AgentState update**

```bash
git add src/deepagent_claude/coding_agent.py tests/test_coding_agent.py
git commit -m "feat(state): add search_results field to AgentState"
```

---

## Task 8: Integrate Code Navigator into CodingDeepAgent

**Files:**
- Modify: `src/deepagent_claude/coding_agent.py`
- Modify: `tests/test_coding_agent.py`

**Step 1: Write failing test for code navigator integration**

```python
# Add to tests/test_coding_agent.py

@pytest.mark.asyncio
async def test_coding_agent_creates_code_navigator():
    """Test CodingDeepAgent creates code navigator subagent"""
    with (
        patch("langchain_ollama.ChatOllama"),
        patch("deepagent_claude.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock),
        patch("deepagent_claude.coding_agent.create_code_navigator", new_callable=AsyncMock) as mock_nav,
        patch("deepagent_claude.coding_agent.create_code_generator", new_callable=AsyncMock),
        patch("deepagent_claude.coding_agent.create_debugger", new_callable=AsyncMock),
        patch("deepagent_claude.coding_agent.create_test_writer", new_callable=AsyncMock),
        patch("deepagent_claude.coding_agent.create_refactorer", new_callable=AsyncMock),
    ):
        agent = CodingDeepAgent()
        await agent.initialize()

        # Code navigator should be created
        mock_nav.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_coding_agent.py::test_coding_agent_creates_code_navigator -v`
Expected: FAIL with "ImportError: cannot import name 'create_code_navigator'"

**Step 3: Integrate code navigator into _create_subagents**

```python
# Modify in src/deepagent_claude/coding_agent.py
# Add import at top:
from deepagent_claude.subagents.code_navigator import create_code_navigator

# Update _create_subagents method:
async def _create_subagents(self):
    """Create specialized subagents"""
    self.logger.info("Creating subagents...")

    # Get appropriate model for subagents
    subagent_model = self.model_selector.get_model("subagent")

    # Create all subagents
    self.subagents = {
        "code_generator": await create_code_generator(subagent_model),
        "debugger": await create_debugger(subagent_model),
        "test_writer": await create_test_writer(subagent_model),
        "refactorer": await create_refactorer(subagent_model),
        "code_navigator": await create_code_navigator(subagent_model),  # NEW
    }

    self.logger.info(f"Created {len(self.subagents)} subagents")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_coding_agent.py::test_coding_agent_creates_code_navigator -v`
Expected: PASS

**Step 5: Commit code navigator integration**

```bash
git add src/deepagent_claude/coding_agent.py tests/test_coding_agent.py
git commit -m "feat(integration): integrate code navigator into main agent"
```

---

## Task 9: Add Code Navigator to Orchestrator Routing Logic

**Files:**
- Modify: `src/deepagent_claude/coding_agent.py`
- Modify: `tests/test_coding_agent.py`

**Step 1: Write failing test for routing to code navigator**

```python
# Add to tests/test_coding_agent.py

@pytest.mark.asyncio
async def test_orchestrator_routes_to_code_navigator():
    """Test orchestrator can route to code navigator"""
    with (
        patch("langchain_ollama.ChatOllama"),
        patch("deepagent_claude.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock),
        patch("deepagent_claude.coding_agent.CodingDeepAgent._create_subagents", new_callable=AsyncMock),
    ):
        agent = CodingDeepAgent()
        agent.initialized = True
        agent.subagents = {
            "code_navigator": AsyncMock(),
            "code_generator": AsyncMock(),
            "debugger": AsyncMock(),
        }

        # Create state that should route to code navigator
        state = {
            "messages": [{"role": "user", "content": "Find the user login API endpoint"}],
            "next_agent": "code_navigator",
            "current_file": "",
            "project_context": {},
            "search_results": {},
        }

        # Test that orchestrator can handle code_navigator routing
        # This will be implemented in the orchestrator logic
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_coding_agent.py::test_orchestrator_routes_to_code_navigator -v`
Expected: Test passes but orchestrator doesn't handle code_navigator yet

**Step 3: Update orchestrator to handle code_navigator routing**

```python
# Modify in src/deepagent_claude/coding_agent.py
# Find the _should_continue method or orchestrator routing logic

def _create_graph(self):
    """Create the agent workflow graph"""
    # ... existing code ...

    # Add routing to code navigator
    # The orchestrator should be able to route to "code_navigator"
    # when the next_agent is set to "code_navigator"

    # Update the conditional edges or routing logic to include:
    # - Route to code_navigator when searching for code
    # - Code navigator can return to orchestrator with search results
    # - Other agents can request code navigator via next_agent field
```

**Step 4: Add orchestrator prompt guidance for using code navigator**

```python
# Modify the orchestrator system prompt in src/deepagent_claude/coding_agent.py

ORCHESTRATOR_PROMPT = """You are the orchestrator agent coordinating specialized subagents.

Available subagents:
- code_generator: Writes new code
- debugger: Finds and fixes bugs
- test_writer: Creates test cases
- refactorer: Improves existing code
- code_navigator: Searches codebase to find files, functions, APIs, etc.  # NEW

When to use code_navigator:
- User asks "where is X?" or "find X"
- Need to locate APIs, functions, classes, or database calls
- Before modifying code, to find the right file
- When other agents need to know code locations

Workflow with code_navigator:
1. Route to code_navigator with search query
2. Code navigator returns findings in search_results
3. Use search_results to guide other agents

Example:
User: "Fix the login bug"
1. Route to code_navigator to find login code
2. Once found, route to debugger with file location
"""
```

**Step 5: Run tests to verify orchestrator handles code_navigator**

Run: `pytest tests/test_coding_agent.py -k orchestrator -v`
Expected: All orchestrator tests PASS

**Step 6: Commit orchestrator routing updates**

```bash
git add src/deepagent_claude/coding_agent.py tests/test_coding_agent.py
git commit -m "feat(orchestrator): add code navigator routing and guidance"
```

---

## Task 10: Add Integration Tests for Code Navigator

**Files:**
- Create: `tests/integration/test_code_navigator_integration.py`

**Step 1: Write integration tests**

```python
# tests/integration/test_code_navigator_integration.py
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from deepagent_claude.subagents.code_navigator import create_code_navigator


@pytest.fixture
def sample_codebase(tmp_path):
    """Create a sample codebase for testing"""
    # Create API routes
    api_dir = tmp_path / "api"
    api_dir.mkdir()

    (api_dir / "routes.py").write_text("""
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/users")
async def list_users():
    return {"users": []}

@router.post("/api/users")
async def create_user(user: dict):
    return {"id": 1, **user}

@router.get("/api/users/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id}
""")

    # Create database models
    models_dir = tmp_path / "models"
    models_dir.mkdir()

    (models_dir / "user.py").write_text("""
from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)

    def query_by_email(self, email):
        return db.session.query(User).filter(User.email == email).first()
""")

    # Create utils
    (tmp_path / "utils.py").write_text("""
def validate_email(email: str) -> bool:
    return "@" in email

def format_name(name: str) -> str:
    return name.title()
""")

    return tmp_path


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_finds_api_endpoint(sample_codebase):
    """Test code navigator can find API endpoints"""
    mock_llm = AsyncMock()

    with patch("deepagent_claude.subagents.code_navigator.MultiServerMCPClient") as mock_mcp:
        from deepagent_claude.mcp_servers.search_tools_server import grep, find

        # Mock MCP client to return real tools
        mock_client = AsyncMock()
        mock_client.get_tools.return_value = []  # Simplified for test
        mock_mcp.return_value = mock_client

        # Test finding users API
        results = grep(
            pattern="@router.get.*users",
            path=str(sample_codebase),
            regex=True,
            recursive=True
        )

        assert len(results) > 0
        assert any("routes.py" in r["file"] for r in results)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_finds_database_calls(sample_codebase):
    """Test code navigator can find database queries"""
    from deepagent_claude.mcp_servers.search_tools_server import grep

    results = grep(
        pattern="query.*filter",
        path=str(sample_codebase),
        regex=True,
        recursive=True
    )

    assert len(results) > 0
    assert any("user.py" in r["file"] for r in results)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_finds_function_definition(sample_codebase):
    """Test code navigator can find function definitions"""
    from deepagent_claude.mcp_servers.search_tools_server import grep

    results = grep(
        pattern="def validate_email",
        path=str(sample_codebase),
        recursive=True
    )

    assert len(results) > 0
    assert any("utils.py" in r["file"] for r in results)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_chains_find_and_grep(sample_codebase):
    """Test code navigator can chain find and grep operations"""
    from deepagent_claude.mcp_servers.search_tools_server import find, grep

    # First find Python files
    py_files = find(
        path=str(sample_codebase),
        extension="py",
        type="f"
    )

    assert len(py_files) >= 3  # routes.py, user.py, utils.py

    # Then search for functions in those files
    for file_path in py_files:
        results = grep(
            pattern="def ",
            path=file_path,
            recursive=False
        )
        # Should find function definitions


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_with_context_lines(sample_codebase):
    """Test code navigator returns context around matches"""
    from deepagent_claude.mcp_servers.search_tools_server import grep

    results = grep(
        pattern="list_users",
        path=str(sample_codebase),
        context_before=2,
        context_after=2,
        recursive=True
    )

    assert len(results) > 0
    # Context lines should be included (decorator line before function)
```

**Step 2: Run integration tests to verify they fail appropriately**

Run: `pytest tests/integration/test_code_navigator_integration.py -v`
Expected: Tests may pass if implementation is complete, or fail showing integration issues

**Step 3: Fix any integration issues found**

Based on test results, fix:
- MCP client initialization
- Tool parameter passing
- Search result formatting
- Error handling

**Step 4: Run all integration tests to verify**

Run: `pytest tests/integration/test_code_navigator_integration.py -v`
Expected: All integration tests PASS

**Step 5: Commit integration tests**

```bash
git add tests/integration/test_code_navigator_integration.py
git commit -m "test(integration): add code navigator integration tests"
```

---

## Task 11: Update Documentation

**Files:**
- Create: `docs/code_navigator_usage.md`
- Modify: `README.md`

**Step 1: Create usage documentation**

```markdown
# Code Navigator Usage Guide

## Overview

The Code Navigator is a specialized subagent that helps locate code artifacts in a codebase using filesystem search tools (grep, find, ls, head, tail, wc, ripgrep).

## When to Use

- Finding API endpoints
- Locating database queries
- Discovering function/class definitions
- Finding configuration files
- Searching for imports and dependencies
- Understanding project structure

## How It Works

The Code Navigator uses a reasoning-based approach:
1. Receives a search query (e.g., "find the user login endpoint")
2. Breaks down the query into search steps
3. Uses tools (grep, find, etc.) to explore the codebase
4. Returns structured results with file paths, line numbers, and context

## Search Strategies

### Finding API Endpoints

**Flask:**
```python
# Searches for route decorators
grep(pattern="@app.route.*login", regex=True)
```

**FastAPI:**
```python
grep(pattern="@router.(get|post).*login", regex=True)
```

### Finding Database Calls

**SQL:**
```python
grep(pattern="SELECT.*FROM.*users", regex=True, ignore_case=True)
```

**ORM:**
```python
grep(pattern="User.query|User.objects", regex=True)
```

### Finding Functions

**Python:**
```python
grep(pattern="def validate_email", recursive=True)
```

**JavaScript:**
```python
grep(pattern="function validateEmail|const validateEmail.*=", regex=True)
```

## Output Format

Results are returned in `search_results` state:

```python
{
    "query": "user login endpoint",
    "findings": [
        {
            "file": "api/routes/auth.py",
            "line": 45,
            "function": "login",
            "code": "@router.post('/api/login')\nasync def login(...):",
            "confidence": "high"
        }
    ],
    "files_examined": 12,
    "search_pattern": "@router.*login"
}
```

## Integration with Other Agents

The orchestrator routes to Code Navigator when:
- User asks "where is X?"
- Other agents need file locations
- Before debugging or refactoring

Example workflow:
1. User: "Fix the login bug"
2. Orchestrator routes to Code Navigator
3. Code Navigator finds login code location
4. Orchestrator routes to Debugger with location
5. Debugger fixes the bug

## Examples

### Example 1: Finding an API Endpoint

Query: "Find the user registration endpoint"

Steps:
1. `find(name="*api*", type="f")` → Find API files
2. `grep(pattern="register", path="./api")` → Search for "register"
3. `grep(pattern="@.*route", file="<match>", context=10)` → Find route decorator

Result:
```
File: api/auth.py
Line: 67
Context:
    @router.post("/api/register")
    async def register_user(user_data: UserCreate):
        return await create_user(user_data)
Confidence: High
Reasoning: Found @router.post decorator with /api/register path
```

### Example 2: Finding Database Queries

Query: "Where do we query the users table?"

Steps:
1. `find(name="*user*", extension="py")` → Find user-related files
2. `grep(pattern="users", file=<files>)` → Search for "users"
3. `grep(pattern="SELECT|query|filter", context=5)` → Look for SQL patterns

Result:
```
File: models/user.py
Line: 23
Context:
    def get_by_email(self, email):
        return db.session.query(User).filter(
            User.email == email
        ).first()
Confidence: High
Reasoning: Found SQLAlchemy query with User model filter
```

## Tips for Effective Searching

1. **Start broad, narrow down**: Use find to locate files, then grep within them
2. **Use context**: Always request context lines to understand matches
3. **Chain operations**: Combine tools for complex queries
4. **Verify results**: Use head/tail to examine full context
5. **Provide confidence**: Rank findings by likelihood

## Troubleshooting

### No Results Found
- Try broader patterns
- Check file paths are correct
- Use case-insensitive search
- Expand search to more file types

### Too Many Results
- Add file type filters
- Use more specific patterns
- Narrow search path
- Use regex with word boundaries

### Incorrect Matches
- Examine context lines
- Check for similar naming
- Search for imports to verify usage
- Use ripgrep for better accuracy
```

**Step 2: Update README.md**

```markdown
# Add to README.md in the Features section:

### Code Navigation
- Intelligent code search using grep, find, and ripgrep
- Find API endpoints, database queries, functions across any language
- Context-aware results with file paths and line numbers
- Integrated with all subagents for location-aware operations
```

**Step 3: Commit documentation**

```bash
git add docs/code_navigator_usage.md README.md
git commit -m "docs: add code navigator usage guide and README updates"
```

---

## Task 12: Run Full Test Suite and Verify

**Step 1: Run all tests**

```bash
# Run all tests except integration (which require external services)
pytest -v -m "not integration"

# Run integration tests separately (requires project setup)
pytest -v -m "integration"
```

Expected: All tests PASS

**Step 2: Run linting**

```bash
uv run ruff check src/ tests/
uv run black --check src/ tests/
```

Expected: No linting errors

**Step 3: Check test coverage**

```bash
pytest --cov=src/deepagent_claude --cov-report=term-missing --cov-fail-under=60
```

Expected: Coverage >= 60%

**Step 4: Manual verification**

Test the code navigator manually:
```python
# Create a test script
from deepagent_claude.subagents.code_navigator import create_code_navigator
from deepagent_claude.core.model_selector import ModelSelector

async def test_manual():
    selector = ModelSelector()
    model = selector.get_model("subagent")

    navigator = await create_code_navigator(model)

    # Test a search
    result = await navigator.ainvoke({
        "messages": [{"role": "user", "content": "Find the grep function"}]
    })

    print(result)

# Run it
import asyncio
asyncio.run(test_manual())
```

**Step 5: Commit any fixes found during verification**

```bash
git add <any_fixed_files>
git commit -m "fix: address issues found during verification"
```

---

## Verification Checklist

Before marking complete, verify:

- [ ] All MCP server tools implemented (grep, find, ls, head, tail, wc, ripgrep)
- [ ] Code Navigator subagent created with comprehensive prompt
- [ ] AgentState includes search_results field
- [ ] Code Navigator integrated into CodingDeepAgent
- [ ] Orchestrator can route to Code Navigator
- [ ] All unit tests passing (>128 tests)
- [ ] Integration tests passing
- [ ] No linting errors (ruff, black)
- [ ] Test coverage >= 60%
- [ ] Documentation complete
- [ ] Manual testing successful

---

## Post-Implementation Tasks

1. **Performance Testing**
   - Test with large codebases (>10k files)
   - Measure search times
   - Optimize if needed

2. **Edge Cases**
   - Binary files
   - Very large files (>1MB)
   - Special characters in filenames
   - Symlinks

3. **Future Enhancements**
   - Add tree-sitter for AST-based search
   - Cache search results
   - Add fuzzy matching
   - Support for more languages

---

## Implementation Notes

- **No mocks in production code** - All tools are fully functional
- **No stubs** - Every function is complete
- **No TODOs** - Implementation is 100% complete
- **Test-driven** - Tests written before implementation
- **Frequent commits** - One commit per major step
- **DRY principle** - Shared logic extracted to functions
- **YAGNI** - Only what's needed, no speculative features
