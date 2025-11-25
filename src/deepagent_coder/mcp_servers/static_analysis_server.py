"""Static analysis MCP server - Linting, security scanning, type/doc coverage"""

import ast
import subprocess
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("Static Analysis")


async def run_linter(
    file_path: str,
    linter: str | None = None,
    config_file: str | None = None,
) -> dict[str, Any]:
    """
    Run appropriate linter on a file

    Args:
        file_path: Path to file to lint
        linter: Linter to use (pylint, ruff, flake8, etc.) - auto-detects if None
        config_file: Path to config file for linter

    Returns:
        Dictionary containing:
        - success: Boolean indicating if linting succeeded
        - issues: List of linting issues found
        - linter_used: Name of linter that was used
        - error: Error message if linting failed
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
            }

        # Auto-detect linter based on file type
        if linter is None:
            if path.suffix == ".py":
                # Try pylint first as it's most comprehensive
                linter = "pylint"
            else:
                return {
                    "success": False,
                    "error": f"No default linter for {path.suffix} files",
                }

        # Build command
        cmd = [linter]

        # Add config file if provided
        if config_file and linter == "pylint":
            cmd.extend(["--rcfile", config_file])

        # Add output format
        if linter == "pylint":
            cmd.extend(["--output-format=json", str(file_path)])
        elif linter == "ruff":
            cmd.extend(["check", "--output-format=json", str(file_path)])
        elif linter == "flake8":
            cmd.extend(["--format=json", str(file_path)])
        else:
            cmd.append(str(file_path))

        # Run linter
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        # Parse output
        issues = []
        output = result.stdout

        # Parse pylint JSON output
        if linter == "pylint":
            try:
                import json

                if output.strip():
                    pylint_issues = json.loads(output)
                    for issue in pylint_issues:
                        issues.append(
                            {
                                "line": issue.get("line", 0),
                                "column": issue.get("column", 0),
                                "type": issue.get("type", "unknown"),
                                "message": issue.get("message", ""),
                                "symbol": issue.get("symbol", ""),
                                "message_id": issue.get("message-id", ""),
                            }
                        )
            except json.JSONDecodeError:
                # If JSON parsing fails, treat output as text
                for line in output.split("\n"):
                    if line.strip():
                        issues.append({"message": line})

        # Parse ruff JSON output
        elif linter == "ruff":
            try:
                import json

                if output.strip():
                    ruff_issues = json.loads(output)
                    for issue in ruff_issues:
                        issues.append(
                            {
                                "line": issue.get("location", {}).get("row", 0),
                                "column": issue.get("location", {}).get("column", 0),
                                "type": issue.get("code", "unknown"),
                                "message": issue.get("message", ""),
                            }
                        )
            except json.JSONDecodeError:
                pass

        # For other linters, parse text output
        else:
            for line in output.split("\n"):
                if line.strip():
                    issues.append({"message": line})

        return {
            "success": True,
            "file": file_path,
            "linter_used": linter,
            "issues": issues,
            "total_issues": len(issues),
        }

    except FileNotFoundError:
        return {
            "success": False,
            "error": f"Linter '{linter}' not found in PATH",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def security_scan(
    path: str,
    language: str | None = None,
) -> dict[str, Any]:
    """
    Scan for security issues using appropriate tool

    Args:
        path: Path to file or directory to scan
        language: Programming language (auto-detects if None)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if scan succeeded
        - vulnerabilities: List of security issues found
        - language_detected: Language that was detected
        - error: Error message if scan failed
    """
    try:
        path_obj = Path(path)

        if not path_obj.exists():
            return {
                "success": False,
                "error": f"Path not found: {path}",
            }

        # Auto-detect language
        if language is None:
            if path_obj.is_file():
                suffix = path_obj.suffix
                if suffix == ".py":
                    language = "python"
                else:
                    language = "unknown"
            else:
                # For directories, assume Python if .py files exist
                if list(path_obj.rglob("*.py")):
                    language = "python"
                else:
                    language = "unknown"

        vulnerabilities = []

        # Use appropriate security scanner
        if language == "python":
            # Use bandit for Python
            cmd = ["bandit", "-f", "json", "-r", str(path)]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            # Parse bandit JSON output
            try:
                import json

                output = result.stdout
                if output.strip():
                    bandit_data = json.loads(output)
                    for issue in bandit_data.get("results", []):
                        vulnerabilities.append(
                            {
                                "file": issue.get("filename", ""),
                                "line": issue.get("line_number", 0),
                                "severity": issue.get("issue_severity", "UNKNOWN"),
                                "confidence": issue.get("issue_confidence", "UNKNOWN"),
                                "issue": issue.get("issue_text", ""),
                                "test_id": issue.get("test_id", ""),
                                "code": issue.get("code", ""),
                            }
                        )
            except (json.JSONDecodeError, KeyError):
                # If parsing fails, return empty list
                pass

        else:
            return {
                "success": False,
                "error": f"No security scanner available for {language}",
            }

        return {
            "success": True,
            "path": path,
            "language_detected": language,
            "vulnerabilities": vulnerabilities,
            "total_vulnerabilities": len(vulnerabilities),
        }

    except FileNotFoundError:
        return {
            "success": False,
            "error": "Security scanner not found in PATH",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def check_type_coverage(file_path: str) -> dict[str, Any]:
    """
    Analyze type annotation coverage

    Args:
        file_path: Path to Python file

    Returns:
        Dictionary containing:
        - success: Boolean indicating if analysis succeeded
        - type_coverage_percent: Percentage of functions with type annotations
        - total_functions: Total number of functions
        - typed_functions: Number of functions with type annotations
        - untyped_functions: List of functions without annotations
        - error: Error message if analysis failed
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
            }

        with open(path) as f:
            content = f.read()

        # Parse AST
        tree = ast.parse(content)

        total_functions = 0
        typed_functions = 0
        untyped_functions = []

        # Find all function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_functions += 1

                # Check if function has type annotations
                has_return_type = node.returns is not None

                # Check if parameters have type annotations
                has_param_types = all(
                    arg.annotation is not None for arg in node.args.args if arg.arg != "self"
                )

                # Consider function typed if it has return type and all params are typed
                if has_return_type and has_param_types:
                    typed_functions += 1
                else:
                    untyped_functions.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "has_return_type": has_return_type,
                            "has_param_types": has_param_types,
                        }
                    )

        # Calculate coverage
        type_coverage_percent = (
            (typed_functions / total_functions * 100) if total_functions > 0 else 0
        )

        return {
            "success": True,
            "file": file_path,
            "type_coverage_percent": round(type_coverage_percent, 2),
            "total_functions": total_functions,
            "typed_functions": typed_functions,
            "untyped_functions": untyped_functions,
        }

    except SyntaxError as e:
        return {
            "success": False,
            "error": f"Syntax error in file: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def documentation_coverage(file_path: str) -> dict[str, Any]:
    """
    Check documentation completeness

    Args:
        file_path: Path to Python file

    Returns:
        Dictionary containing:
        - success: Boolean indicating if analysis succeeded
        - doc_coverage_percent: Percentage of items with docstrings
        - total_items: Total number of documentable items
        - documented_items: Number of items with docstrings
        - undocumented_items: List of items without docstrings
        - module_docstring: Whether module has docstring
        - error: Error message if analysis failed
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
            }

        with open(path) as f:
            content = f.read()

        # Parse AST
        tree = ast.parse(content)

        total_items = 0
        documented_items = 0
        undocumented_items = []

        # Check module docstring
        module_docstring = ast.get_docstring(tree) is not None

        # Find all documentable items
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                total_items += 1

                docstring = ast.get_docstring(node)
                if docstring:
                    documented_items += 1
                else:
                    item_type = "function" if isinstance(node, ast.FunctionDef) else "class"
                    undocumented_items.append(
                        {
                            "name": node.name,
                            "type": item_type,
                            "line": node.lineno,
                        }
                    )

        # Calculate coverage
        doc_coverage_percent = (
            (documented_items / total_items * 100) if total_items > 0 else 0
        )

        return {
            "success": True,
            "file": file_path,
            "doc_coverage_percent": round(doc_coverage_percent, 2),
            "total_items": total_items,
            "documented_items": documented_items,
            "undocumented_items": undocumented_items,
            "module_docstring": module_docstring,
        }

    except SyntaxError as e:
        return {
            "success": False,
            "error": f"Syntax error in file: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


# Register tools with MCP
mcp.tool(run_linter)
mcp.tool(security_scan)
mcp.tool(check_type_coverage)
mcp.tool(documentation_coverage)


if __name__ == "__main__":
    mcp.run(transport="stdio")
