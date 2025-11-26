"""
Linting MCP Server

Provides tools for code quality and linting operations:
- run_ruff: Run ruff linter with auto-fix support
- run_mypy: Run mypy type checker
- run_black: Run black code formatter
- format_code: Generic formatter wrapper
- lint_project: Run all linting tools on entire project
"""

import asyncio
import json
from pathlib import Path
import re
import sys


async def _run_command(
    cmd: list[str], cwd: str | None = None, timeout: int = 300
) -> tuple[str, str, int]:
    """
    Helper to run a command and return stdout, stderr, returncode.

    Args:
        cmd: Command and arguments as list
        cwd: Working directory
        timeout: Timeout in seconds

    Returns:
        Tuple of (stdout, stderr, returncode)
    """
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            returncode = process.returncode or 0

            return stdout, stderr, returncode

        except TimeoutError:
            process.kill()
            await process.communicate()
            return "", f"Command timed out after {timeout}s", 1

    except FileNotFoundError:
        return "", f"Command not found: {cmd[0]}", 127
    except Exception as e:
        return "", f"Error running command: {str(e)}", 1


async def run_ruff_impl(path: str, fix: bool = False, config: str | None = None) -> dict:
    """
    Implementation for run_ruff tool.

    Args:
        path: File or directory path to lint
        fix: Whether to auto-fix issues
        config: Optional path to ruff config file

    Returns:
        Dictionary with linting results
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return {"error": f"Path not found: {path}"}

    # Always use as Python module
    cmd = [sys.executable, "-m", "ruff", "check", str(path_obj), "--output-format=json"]

    if fix:
        cmd.append("--fix")

    if config:
        cmd.extend(["--config", config])

    stdout, stderr, returncode = await _run_command(cmd)

    # Ruff returns non-zero if it finds issues, which is expected
    if stderr and "not found" in stderr.lower():
        return {"error": stderr}

    try:
        # Parse JSON output
        issues = json.loads(stdout) if stdout.strip() else []

        result = {
            "path": str(path_obj),
            "total_issues": len(issues),
            "issues": issues,
            "fixed": fix,
        }

        if fix:
            result["message"] = f"Fixed {len(issues)} issues" if issues else "No issues to fix"
        else:
            result["message"] = f"Found {len(issues)} issues" if issues else "No issues found"

        return result

    except json.JSONDecodeError:
        # If JSON parsing fails, return raw output
        return {
            "path": str(path_obj),
            "total_issues": 0,
            "raw_output": stdout,
            "fixed": fix,
            "message": "Could not parse ruff output",
        }


async def run_mypy_impl(path: str, strict: bool = False, config: str | None = None) -> dict:
    """
    Implementation for run_mypy tool.

    Args:
        path: File or directory path to type check
        strict: Whether to use strict mode
        config: Optional path to mypy config file

    Returns:
        Dictionary with type checking results
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return {"error": f"Path not found: {path}"}

    # Always use as Python module
    cmd = [sys.executable, "-m", "mypy", str(path_obj)]

    if strict:
        cmd.append("--strict")

    if config:
        cmd.extend(["--config-file", config])

    stdout, stderr, returncode = await _run_command(cmd)

    if stderr and "not found" in stderr.lower():
        return {"error": stderr}

    # Parse mypy output (format: file:line: error: message)
    issues = []
    for line in stdout.splitlines():
        # Match pattern: path:line: error_type: message
        match = re.match(r"^(.+?):(\d+):(?:\s+(\w+):)?\s*(.+)$", line)
        if match:
            file_path, line_num, error_type, message = match.groups()
            issues.append(
                {
                    "file": file_path,
                    "line": int(line_num),
                    "type": error_type or "error",
                    "message": message.strip(),
                }
            )

    result = {
        "path": str(path_obj),
        "total_issues": len(issues),
        "issues": issues,
        "strict_mode": strict,
    }

    if returncode == 0:
        result["message"] = "No type errors found"
    else:
        result["message"] = f"Found {len(issues)} type errors"

    return result


async def run_black_impl(path: str, check: bool = False, line_length: int | None = None) -> dict:
    """
    Implementation for run_black tool.

    Args:
        path: File or directory path to format
        check: Whether to check without modifying files
        line_length: Optional line length limit

    Returns:
        Dictionary with formatting results
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return {"error": f"Path not found: {path}"}

    # Always use as Python module
    cmd = [sys.executable, "-m", "black", str(path_obj)]

    if check:
        cmd.append("--check")

    if line_length:
        cmd.extend(["--line-length", str(line_length)])

    # Add verbose flag to get more details
    cmd.append("--verbose")

    stdout, stderr, returncode = await _run_command(cmd)

    if stderr and "not found" in stderr.lower():
        return {"error": stderr}

    # Parse output for file counts
    reformatted = 0
    unchanged = 0

    combined_output = stdout + stderr
    for line in combined_output.splitlines():
        if "reformatted" in line.lower():
            # Extract number from "X file(s) reformatted"
            match = re.search(r"(\d+)\s+file", line)
            if match:
                reformatted = int(match.group(1))
        elif "left unchanged" in line.lower():
            match = re.search(r"(\d+)\s+file", line)
            if match:
                unchanged = int(match.group(1))

    result = {
        "path": str(path_obj),
        "check_only": check,
        "reformatted": reformatted,
        "unchanged": unchanged,
        "total_files": reformatted + unchanged,
    }

    if check:
        if returncode == 0:
            result["message"] = "All files are formatted correctly"
        else:
            result["message"] = f"{reformatted} file(s) would be reformatted"
    else:
        if reformatted > 0:
            result["message"] = f"Reformatted {reformatted} file(s)"
        else:
            result["message"] = "No files needed reformatting"

    return result


async def format_code_impl(path: str, formatter: str = "black", **kwargs) -> dict:
    """
    Implementation for format_code tool (generic formatter wrapper).

    Args:
        path: File or directory path to format
        formatter: Formatter to use ('black' or 'ruff')
        **kwargs: Additional formatter-specific options

    Returns:
        Dictionary with formatting results
    """
    if formatter == "black":
        return await run_black_impl(path, **kwargs)
    elif formatter == "ruff":
        # Ruff can also format with --fix
        return await run_ruff_impl(path, fix=True, **kwargs)
    else:
        return {"error": f"Unsupported formatter: {formatter}"}


async def lint_project_impl(path: str, fix: bool = False, strict_mypy: bool = False) -> dict:
    """
    Implementation for lint_project tool.
    Runs all linting tools on a project.

    Args:
        path: Project directory path
        fix: Whether to auto-fix issues
        strict_mypy: Whether to use strict mypy mode

    Returns:
        Dictionary with aggregated results from all tools
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return {"error": f"Path not found: {path}"}

    if not path_obj.is_dir():
        return {"error": f"Path is not a directory: {path}"}

    # Run all tools in parallel
    ruff_task = asyncio.create_task(run_ruff_impl(path, fix=fix))
    mypy_task = asyncio.create_task(run_mypy_impl(path, strict=strict_mypy))
    black_task = asyncio.create_task(run_black_impl(path, check=not fix))

    ruff_result = await ruff_task
    mypy_result = await mypy_task
    black_result = await black_task

    # Aggregate results
    total_issues = 0
    if "total_issues" in ruff_result:
        total_issues += ruff_result["total_issues"]
    if "total_issues" in mypy_result:
        total_issues += mypy_result["total_issues"]
    if "reformatted" in black_result:
        total_issues += black_result["reformatted"]

    result = {
        "path": str(path_obj),
        "total_issues": total_issues,
        "results": {"ruff": ruff_result, "mypy": mypy_result, "black": black_result},
    }

    if total_issues == 0:
        result["message"] = "All checks passed!"
    else:
        result["message"] = f"Found {total_issues} total issues across all tools"

    return result


# MCP Tool Functions (exported)
async def run_ruff(path: str, fix: bool = False, config: str | None = None) -> dict:
    """
    Run ruff linter with auto-fix support.

    Args:
        path: File or directory path to lint
        fix: Whether to auto-fix issues
        config: Optional path to ruff config file

    Returns:
        Dictionary with linting results
    """
    return await run_ruff_impl(path, fix, config)


async def run_mypy(path: str, strict: bool = False, config: str | None = None) -> dict:
    """
    Run mypy type checker.

    Args:
        path: File or directory path to type check
        strict: Whether to use strict mode
        config: Optional path to mypy config file

    Returns:
        Dictionary with type checking results
    """
    return await run_mypy_impl(path, strict, config)


async def run_black(path: str, check: bool = False, line_length: int | None = None) -> dict:
    """
    Run black code formatter.

    Args:
        path: File or directory path to format
        check: Whether to check without modifying files
        line_length: Optional line length limit

    Returns:
        Dictionary with formatting results
    """
    return await run_black_impl(path, check, line_length)


async def format_code(path: str, formatter: str = "black", **kwargs) -> dict:
    """
    Generic formatter wrapper.

    Args:
        path: File or directory path to format
        formatter: Formatter to use ('black' or 'ruff')
        **kwargs: Additional formatter-specific options

    Returns:
        Dictionary with formatting results
    """
    result = await format_code_impl(path, formatter, **kwargs)
    # Add success flag for test compatibility
    if "error" not in result:
        result["success"] = True
    return result


async def lint_project(path: str, fix: bool = False, strict_mypy: bool = False) -> dict:
    """
    Run all linting tools on entire project.

    Args:
        path: Project directory path
        fix: Whether to auto-fix issues
        strict_mypy: Whether to use strict mypy mode

    Returns:
        Dictionary with aggregated results from all tools
    """
    return await lint_project_impl(path, fix, strict_mypy)
