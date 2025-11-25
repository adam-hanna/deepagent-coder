"""Build tools MCP server - File analysis and code metrics"""

from pathlib import Path
import re
from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("Build Tools")


async def find_files_by_pattern(
    pattern: str,
    path: str = ".",
    recursive: bool = True,
    file_type: str | None = None,
) -> list[str]:
    """
    Find files matching a pattern

    Args:
        pattern: Glob pattern to match (e.g., "*.py", "test_*.js")
        path: Directory to search in (default: current directory)
        recursive: Whether to search recursively (default: True)
        file_type: Filter by type - "f" for files, "d" for directories, None for both

    Returns:
        List of matching file paths (sorted)
    """
    matches = []
    path_obj = Path(path)

    if not path_obj.exists():
        return []

    if recursive:
        if file_type == "f":  # Files only
            matches = [str(f) for f in path_obj.rglob(pattern) if f.is_file()]
        elif file_type == "d":  # Directories only
            matches = [str(f) for f in path_obj.rglob(pattern) if f.is_dir()]
        else:  # Both
            matches = [str(f) for f in path_obj.rglob(pattern)]
    else:
        if file_type == "f":
            matches = [str(f) for f in path_obj.glob(pattern) if f.is_file()]
        elif file_type == "d":
            matches = [str(f) for f in path_obj.glob(pattern) if f.is_dir()]
        else:
            matches = [str(f) for f in path_obj.glob(pattern)]

    return sorted(matches)


async def analyze_file_stats(file_path: str) -> dict[str, Any]:
    """
    Get detailed file statistics and metrics

    Args:
        file_path: Path to the file to analyze

    Returns:
        Dictionary containing:
        - success: Boolean indicating if analysis succeeded
        - size_bytes: File size in bytes
        - size_human: Human-readable file size
        - is_file: Whether path is a file
        - is_dir: Whether path is a directory
        - lines: Number of lines (for text files)
        - characters: Number of characters (for text files)
        - non_empty_lines: Lines with content
        - code_metrics: Dictionary with import/function/comment counts
        - error: Error message if analysis failed
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
            }

        stats = path.stat()

        # Basic stats
        result = {
            "success": True,
            "file": file_path,
            "size_bytes": stats.st_size,
            "size_human": _format_bytes(stats.st_size),
            "modified": stats.st_mtime,
            "created": stats.st_ctime,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "permissions": oct(stats.st_mode)[-3:],
        }

        # For text files, add line counts and basic analysis
        if path.is_file() and stats.st_size < 10_000_000:  # Don't read huge files
            try:
                content = path.read_text(encoding="utf-8")
                lines = content.splitlines()

                result.update(
                    {
                        "lines": len(lines),
                        "characters": len(content),
                        "non_empty_lines": len([line for line in lines if line.strip()]),
                        "avg_line_length": (
                            sum(len(line) for line in lines) / len(lines) if lines else 0
                        ),
                    }
                )

                # Language-agnostic code metrics
                result["code_metrics"] = {
                    "comment_lines": _count_comment_lines(content, file_path),
                    "import_lines": _count_import_lines(content, file_path),
                    "function_definitions": _count_function_definitions(content, file_path),
                }

            except (UnicodeDecodeError, Exception):
                result["binary_file"] = True

        return result

    except Exception as e:
        return {"success": False, "error": str(e), "file": file_path}


async def count_pattern_occurrences(
    pattern: str,
    path: str = ".",
    file_extensions: list[str] | None = None,
    ignore_case: bool = False,
    is_regex: bool = True,
) -> dict[str, Any]:
    """
    Count occurrences of a pattern in files

    Args:
        pattern: Pattern to search for (regex or string)
        path: Directory to search in
        file_extensions: List of file extensions to search (e.g., ["py", "js"])
        ignore_case: Whether to ignore case in matching
        is_regex: Whether pattern is a regex (True) or plain string (False)

    Returns:
        Dictionary containing:
        - pattern: The search pattern
        - total_matches: Total number of matches across all files
        - files_with_matches: Number of files containing matches
        - matches_by_file: Dictionary mapping file paths to match counts
    """
    results = {
        "pattern": pattern,
        "total_matches": 0,
        "files_with_matches": 0,
        "matches_by_file": {},
    }

    # Build file list
    files = []
    if file_extensions:
        for ext in file_extensions:
            files.extend(await find_files_by_pattern(f"*.{ext}", path))
    else:
        # All text files
        all_files = await find_files_by_pattern("*", path, file_type="f")
        files = [f for f in all_files if _is_text_file(f)]

    # Compile pattern
    flags = re.IGNORECASE if ignore_case else 0
    if is_regex:
        try:
            pattern_re = re.compile(pattern, flags)
        except re.error as e:
            return {
                "pattern": pattern,
                "error": f"Invalid regex pattern: {e}",
                "total_matches": 0,
                "files_with_matches": 0,
                "matches_by_file": {},
            }

    # Search files
    for file_path in files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            if is_regex:
                matches = pattern_re.findall(content)
            else:
                # Simple string search
                if ignore_case:
                    matches_count = content.lower().count(pattern.lower())
                else:
                    matches_count = content.count(pattern)
                matches = [pattern] * matches_count if matches_count else []

            if matches:
                results["files_with_matches"] += 1
                results["total_matches"] += len(matches)
                results["matches_by_file"][file_path] = len(matches)

        except Exception as e:
            results["matches_by_file"][file_path] = f"Error: {str(e)}"

    return results


async def extract_structure(file_path: str, max_depth: int = 3) -> dict[str, Any]:
    """
    Extract structure from a text file using patterns and indentation

    Args:
        file_path: Path to the file to analyze
        max_depth: Maximum nesting depth to include in outline

    Returns:
        Dictionary containing:
        - success: Boolean indicating if extraction succeeded
        - file: The file path analyzed
        - sections: List of detected sections/structures
        - outline: Hierarchical outline of the file
        - error: Error message if extraction failed
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        structure = {"success": True, "file": file_path, "sections": [], "outline": []}

        # Detect structure based on patterns
        section_patterns = [
            (r"^#{1,6}\s+(.+)", "markdown_header"),
            (r"^(class|interface|struct)\s+(\w+)", "class_definition"),
            (r"^(def|function|fn|func)\s+(\w+)", "function_definition"),
            (
                r"^(public|private|protected)?\s*(static)?\s*\w+\s+(\w+)\s*\(",
                "method_definition",
            ),
            (r"^(\w+):\s*$", "yaml_section"),
            (r"^\[(\w+)\]", "ini_section"),
        ]

        current_indent_stack = []

        for i, line in enumerate(lines):
            # Calculate indentation
            indent = len(line) - len(line.lstrip())
            stripped = line.strip()

            if not stripped:
                continue

            # Check patterns
            for pattern, pattern_type in section_patterns:
                match = re.match(pattern, stripped)
                if match:
                    # Extract name based on pattern type
                    if pattern_type == "class_definition":
                        name = match.group(2)
                    elif pattern_type == "method_definition":
                        name = match.group(3) if match.lastindex >= 3 else match.group(1)
                    else:
                        name = match.group(1)

                    section = {
                        "line": i + 1,
                        "type": pattern_type,
                        "name": name,
                        "indent": indent,
                        "text": stripped,
                    }

                    structure["sections"].append(section)

                    # Build outline based on indentation
                    while current_indent_stack and current_indent_stack[-1][1] >= indent:
                        current_indent_stack.pop()

                    level = len(current_indent_stack)
                    if level < max_depth:
                        outline_entry = "  " * level + f"- {name} ({pattern_type})"
                        structure["outline"].append(outline_entry)
                        current_indent_stack.append((name, indent))

                    break

        return structure

    except FileNotFoundError:
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "file": file_path,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "file": file_path}


# Helper functions
def _format_bytes(size: int) -> str:
    """Format bytes to human readable"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def _is_text_file(file_path: str) -> bool:
    """Check if file is likely text"""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(512)
        # Check for null bytes (common in binary files)
        return b"\x00" not in chunk
    except Exception:
        return False


def _count_comment_lines(content: str, file_path: str) -> int:
    """Count comment lines based on file extension"""
    ext = Path(file_path).suffix.lower()
    count = 0

    # Common comment patterns
    if ext in [".py", ".sh", ".yml", ".yaml", ".rb"]:
        count = len([line for line in content.splitlines() if line.strip().startswith("#")])
    elif ext in [".js", ".java", ".c", ".cpp", ".go", ".rs", ".ts", ".jsx", ".tsx"]:
        count = len([line for line in content.splitlines() if line.strip().startswith("//")])
        # Also count /* */ blocks
        count += content.count("/*")
    elif ext in [".html", ".xml"]:
        count += content.count("<!--")

    return count


def _count_import_lines(content: str, file_path: str) -> int:
    """Count import statements"""
    ext = Path(file_path).suffix.lower()
    lines = content.splitlines()
    count = 0

    if ext == ".py":
        count = len([line for line in lines if line.strip().startswith(("import ", "from "))])
    elif ext in [".js", ".ts", ".jsx", ".tsx"]:
        count = len([line for line in lines if re.match(r"^\s*(import|require)", line)])
    elif ext == ".java":
        count = len([line for line in lines if line.strip().startswith("import ")])
    elif ext == ".go":
        in_import = False
        for line in lines:
            if line.strip() == "import (":
                in_import = True
            elif in_import and line.strip() == ")":
                in_import = False
            elif line.strip().startswith("import ") or in_import and line.strip():
                count += 1

    return count


def _count_function_definitions(content: str, file_path: str) -> int:
    """Count function definitions"""
    ext = Path(file_path).suffix.lower()

    if ext == ".py":
        return len(re.findall(r"^\s*def\s+\w+", content, re.MULTILINE))
    elif ext in [".js", ".ts", ".jsx", ".tsx"]:
        # Various JS function patterns
        patterns = [
            r"^\s*function\s+\w+",
            r"^\s*const\s+\w+\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=]+)\s*=>",
            r"^\s*(?:export\s+)?(?:async\s+)?function\s+\w+",
        ]
        return sum(len(re.findall(p, content, re.MULTILINE)) for p in patterns)
    elif ext == ".java":
        return len(
            re.findall(
                r"^\s*(?:public|private|protected)?\s*(?:static)?\s*\w+\s+\w+\s*\(",
                content,
                re.MULTILINE,
            )
        )
    elif ext == ".go":
        return len(re.findall(r"^\s*func\s+", content, re.MULTILINE))

    return 0


# MCP Tool wrappers
@mcp.tool()
async def find_files(
    pattern: str,
    path: str = ".",
    recursive: bool = True,
    file_type: str | None = None,
) -> list[str]:
    """
    Find files matching a glob pattern

    Use this tool to search for files by name or pattern:
    - Find all Python files: pattern="*.py"
    - Find test files: pattern="test_*.py"
    - Find in subdirectories: recursive=True
    - Filter by type: file_type="f" (files) or "d" (directories)

    Args:
        pattern: Glob pattern to match (e.g., "*.py", "test_*.js")
        path: Directory to search in (default: current directory)
        recursive: Whether to search recursively (default: True)
        file_type: Filter by type - "f" for files, "d" for directories, None for both

    Returns:
        List of matching file paths (sorted)
    """
    return await find_files_by_pattern(pattern, path, recursive, file_type)


@mcp.tool()
async def analyze_file(file_path: str) -> dict[str, Any]:
    """
    Get detailed statistics and metrics for a file

    Use this tool to analyze file properties:
    - File size and metadata
    - Line counts for text files
    - Code metrics (imports, functions, comments)
    - Character and line statistics

    Args:
        file_path: Path to the file to analyze

    Returns:
        Dictionary containing:
        - success: Boolean indicating if analysis succeeded
        - size_bytes: File size in bytes
        - size_human: Human-readable file size
        - is_file/is_dir: File type information
        - lines, characters, non_empty_lines: Text file metrics
        - code_metrics: Import/function/comment counts
        - error: Error message if analysis failed
    """
    return await analyze_file_stats(file_path)


@mcp.tool()
async def count_pattern(
    pattern: str,
    path: str = ".",
    file_extensions: list[str] | None = None,
    ignore_case: bool = False,
    is_regex: bool = True,
) -> dict[str, Any]:
    """
    Count occurrences of a pattern across files

    Use this tool to search for patterns in code:
    - Count function calls: pattern=r"my_function\\("
    - Find TODO comments: pattern="TODO"
    - Search in specific files: file_extensions=["py", "js"]
    - Case-insensitive search: ignore_case=True

    Args:
        pattern: Pattern to search for (regex or string)
        path: Directory to search in (default: current directory)
        file_extensions: List of extensions to search (e.g., ["py", "js"])
        ignore_case: Whether to ignore case in matching
        is_regex: Whether pattern is regex (True) or plain string (False)

    Returns:
        Dictionary containing:
        - pattern: The search pattern
        - total_matches: Total number of matches
        - files_with_matches: Number of files with matches
        - matches_by_file: Dictionary of file paths to match counts
    """
    return await count_pattern_occurrences(pattern, path, file_extensions, ignore_case, is_regex)


@mcp.tool()
async def extract_file_structure(file_path: str, max_depth: int = 3) -> dict[str, Any]:
    """
    Extract structure from a source code or text file

    Use this tool to understand file organization:
    - Find classes and functions in code files
    - Extract headers from Markdown files
    - Build hierarchical outline of file structure
    - Get overview of code organization

    Args:
        file_path: Path to the file to analyze
        max_depth: Maximum nesting depth for outline (default: 3)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if extraction succeeded
        - file: The file path analyzed
        - sections: List of detected sections with line numbers
        - outline: Hierarchical outline of the structure
        - error: Error message if extraction failed
    """
    return await extract_structure(file_path, max_depth)


if __name__ == "__main__":
    mcp.run()
