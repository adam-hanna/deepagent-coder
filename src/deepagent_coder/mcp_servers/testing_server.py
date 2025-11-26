# src/deepagent_coder/mcp_servers/testing_server.py
"""Testing tools MCP server - test execution and coverage"""

import asyncio
from pathlib import Path
import re
import sys
from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("Testing Tools")


@mcp.tool()
async def run_pytest(
    project_path: str,
    test_path: str | None = None,
    markers: str | None = None,
    verbose: bool = True,
    timeout: int = 120,
) -> dict[str, Any]:
    """
    Run pytest on project or specific tests

    Args:
        project_path: Path to project root
        test_path: Optional specific test file or directory
        markers: Optional pytest markers to filter tests
        verbose: Use verbose output
        timeout: Maximum execution time in seconds

    Returns:
        Test results including passed, failed, skipped counts and output
    """
    return await _run_pytest_impl(project_path, test_path, markers, verbose, timeout)


async def _run_pytest_impl(
    project_path: str,
    test_path: str | None = None,
    markers: str | None = None,
    verbose: bool = True,
    timeout: int = 120,
) -> dict[str, Any]:
    """Implementation of run_pytest"""
    try:
        path = Path(project_path)
        if not path.exists():
            return {"error": f"Project path not found: {project_path}"}

        # Build pytest command - always use as Python module
        cmd = [sys.executable, "-m", "pytest"]

        if test_path:
            test_full_path = Path(test_path)
            if test_full_path.is_absolute():
                cmd.append(str(test_full_path))
            else:
                cmd.append(str(path / test_path))

        if markers:
            cmd.extend(["-m", markers])

        if verbose:
            cmd.append("-v")

        # Add output for parsing
        cmd.extend(["--tb=short", "-q"])

        # Execute pytest
        result = await _run_command(cmd, cwd=path, timeout=timeout)

        if result["returncode"] not in [0, 1] and (
            "ERROR" in result["stderr"] or "error" in result["stderr"].lower()
        ):  # 0=pass, 1=some failed
            return {"error": result["stderr"] or result["stdout"]}

        # Parse output
        output = result["stdout"] + result["stderr"]

        # Extract test counts
        passed = 0
        failed = 0
        skipped = 0
        total = 0

        # Look for summary line like "3 passed, 1 failed in 0.05s"
        summary_pattern = r"(\d+)\s+passed|(\d+)\s+failed|(\d+)\s+skipped"
        for match in re.finditer(summary_pattern, output):
            if match.group(1):
                passed = int(match.group(1))
            elif match.group(2):
                failed = int(match.group(2))
            elif match.group(3):
                skipped = int(match.group(3))

        total = passed + failed + skipped

        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "output": output,
            "success": failed == 0,
        }

    except Exception as e:
        return {"error": f"Pytest execution failed: {str(e)}"}


@mcp.tool()
async def run_unittest(
    project_path: str,
    test_path: str | None = None,
    pattern: str = "test*.py",
    verbose: bool = True,
    timeout: int = 120,
) -> dict[str, Any]:
    """
    Run unittest on project

    Args:
        project_path: Path to project root
        test_path: Optional test directory
        pattern: Test file pattern
        verbose: Use verbose output
        timeout: Maximum execution time in seconds

    Returns:
        Test results including passed, failed counts and output
    """
    return await _run_unittest_impl(project_path, test_path, pattern, verbose, timeout)


async def _run_unittest_impl(
    project_path: str,
    test_path: str | None = None,
    pattern: str = "test*.py",
    verbose: bool = True,
    timeout: int = 120,
) -> dict[str, Any]:
    """Implementation of run_unittest"""
    try:
        path = Path(project_path)
        if not path.exists():
            return {"error": f"Project path not found: {project_path}"}

        # Build unittest command
        cmd = ["python", "-m", "unittest"]

        if test_path:
            cmd.append(test_path)
        else:
            cmd.extend(["discover", "-s", str(path), "-p", pattern])

        if verbose:
            cmd.append("-v")

        # Execute unittest
        result = await _run_command(cmd, cwd=path, timeout=timeout)

        # Parse output
        output = result["stdout"] + result["stderr"]

        # Extract test counts from output like "Ran 5 tests in 0.001s"
        ran_match = re.search(r"Ran (\d+) test", output)
        total = int(ran_match.group(1)) if ran_match else 0

        # Check for failures/errors
        failed_match = re.search(r"FAILED.*failures=(\d+)", output)
        error_match = re.search(r"errors=(\d+)", output)

        failed = int(failed_match.group(1)) if failed_match else 0
        errors = int(error_match.group(1)) if error_match else 0
        passed = total - failed - errors

        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "output": output,
            "success": result["returncode"] == 0,
        }

    except Exception as e:
        return {"error": f"Unittest execution failed: {str(e)}"}


@mcp.tool()
async def get_coverage(
    project_path: str,
    source_dirs: list[str] | None = None,
    test_path: str | None = None,
    timeout: int = 180,
) -> dict[str, Any]:
    """
    Run tests with coverage reporting

    Args:
        project_path: Path to project root
        source_dirs: List of source directories to measure coverage
        test_path: Optional specific test path
        timeout: Maximum execution time in seconds

    Returns:
        Coverage report including percentage and detailed file coverage
    """
    return await _get_coverage_impl(project_path, source_dirs, test_path, timeout)


async def _get_coverage_impl(
    project_path: str,
    source_dirs: list[str] | None = None,
    test_path: str | None = None,
    timeout: int = 180,
) -> dict[str, Any]:
    """Implementation of get_coverage"""
    try:
        path = Path(project_path)
        if not path.exists():
            return {"error": f"Project path not found: {project_path}"}

        # Build coverage command - always use as Python module
        cmd = [sys.executable, "-m", "coverage", "run", "-m", "pytest"]

        if test_path:
            cmd.append(test_path)

        if source_dirs:
            for src_dir in source_dirs:
                cmd.extend(["--source", src_dir])

        # Run tests with coverage
        await _run_command(cmd, cwd=path, timeout=timeout)

        # Generate report
        report_cmd = [sys.executable, "-m", "coverage", "report"]
        report_result = await _run_command(report_cmd, cwd=path, timeout=30)

        # Parse coverage percentage
        output = report_result["stdout"]

        # Look for "TOTAL ... XX%"
        total_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
        coverage_percent = int(total_match.group(1)) if total_match else 0

        # Parse individual file coverage
        files = []
        for line in output.splitlines():
            # Match lines like "src/calculator.py    10    2    80%"
            file_match = re.match(r"(.+?)\s+(\d+)\s+(\d+)\s+(\d+)%", line)
            if file_match and not line.startswith("TOTAL"):
                files.append(
                    {
                        "file": file_match.group(1).strip(),
                        "statements": int(file_match.group(2)),
                        "missing": int(file_match.group(3)),
                        "coverage": int(file_match.group(4)),
                    }
                )

        return {
            "coverage_percent": coverage_percent,
            "files": files,
            "report": output,
            "success": True,
        }

    except Exception as e:
        return {"error": f"Coverage execution failed: {str(e)}"}


async def _run_command(cmd: list[str], cwd: Path, timeout: int = 120) -> dict[str, Any]:
    """Execute command and return result"""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

        return {
            "stdout": stdout.decode("utf-8"),
            "stderr": stderr.decode("utf-8"),
            "returncode": process.returncode,
        }

    except TimeoutError:
        process.kill()
        await process.wait()
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "returncode": -1,
        }


def run_server():
    """Run the Testing MCP server"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
