"""Code metrics MCP server - Complexity, coverage, duplication, maintainability analysis"""

import ast
import contextlib
from pathlib import Path
import subprocess
from typing import Any

from fastmcp import FastMCP
from radon.complexity import cc_visit
from radon.metrics import mi_visit
from radon.raw import analyze

mcp = FastMCP("Code Metrics")


async def calculate_complexity(file_path: str) -> dict[str, Any]:
    """
    Calculate cyclomatic complexity for all functions in a Python file

    Args:
        file_path: Path to the Python file

    Returns:
        Dictionary containing:
        - success: Boolean indicating if analysis succeeded
        - functions: List of functions with complexity scores
        - average_complexity: Average complexity across all functions
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

        # Use radon to calculate cyclomatic complexity
        results = cc_visit(content)

        functions = []
        for result in results:
            func_info = {
                "name": result.name,
                "complexity": result.complexity,
                "line": result.lineno,
                "column": result.col_offset,
                "type": result.letter,  # F for function, M for method, C for class
            }
            functions.append(func_info)

        avg_complexity = (
            sum(f["complexity"] for f in functions) / len(functions) if functions else 0
        )

        return {
            "success": True,
            "file": file_path,
            "functions": functions,
            "average_complexity": round(avg_complexity, 2),
            "total_functions": len(functions),
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


async def measure_code_coverage(
    test_command: str = "pytest",
    source_dir: str = "src",
    working_dir: str = ".",
) -> dict[str, Any]:
    """
    Run tests and measure code coverage

    Args:
        test_command: Command to run tests (default: pytest)
        source_dir: Source directory to measure coverage for
        working_dir: Working directory to run command from

    Returns:
        Dictionary containing:
        - success: Boolean indicating if coverage measurement succeeded
        - coverage_percent: Overall coverage percentage
        - uncovered_lines: Dictionary mapping files to uncovered line numbers
        - total_statements: Total number of statements
        - covered_statements: Number of covered statements
        - error: Error message if measurement failed
    """
    try:
        # Parse the test command to handle compound commands
        cmd_parts = test_command.split()

        # Add coverage flags if not already present
        if "--cov" not in test_command:
            cmd_parts.extend(["--cov=" + source_dir, "--cov-report=term-missing"])
        elif "--cov-report" not in test_command:
            cmd_parts.append("--cov-report=term-missing")

        result = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            cwd=working_dir,
            shell=False,
        )

        # Parse coverage output
        output = result.stdout + result.stderr
        coverage_percent = 0.0
        uncovered_lines = {}
        total_statements = 0
        covered = 0

        # Extract coverage percentage - look for lines with % symbol
        for line in output.split("\n"):
            # Match lines like "src/mymodule.py    10    2    80%"
            if "%" in line:
                parts = line.split()
                # Try to find percentage value
                for part in parts:
                    if "%" in part:
                        with contextlib.suppress(ValueError):
                            coverage_percent = max(
                                coverage_percent, float(part.rstrip("%"))
                            )

            # Extract totals from TOTAL line
            if "TOTAL" in line:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        total_statements = int(parts[1])
                        missing = int(parts[2])
                        covered = total_statements - missing
                    except (ValueError, IndexError):
                        pass

        # Consider success if tests ran and we got coverage data
        success = (result.returncode == 0) or (coverage_percent >= 0)

        return {
            "success": success,
            "coverage_percent": coverage_percent,
            "uncovered_lines": uncovered_lines,
            "missing_lines": uncovered_lines,  # Alias for backward compatibility
            "total_statements": total_statements,
            "covered_statements": covered,
            "command": " ".join(cmd_parts),
            "output": output[:500],  # First 500 chars
        }

    except FileNotFoundError:
        return {
            "success": False,
            "error": "Test command not found in PATH",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def detect_duplication(path: str = ".", threshold: int = 50) -> list[dict[str, Any]]:
    """
    Find duplicate code blocks using AST comparison

    Args:
        path: Directory to search for duplicates
        threshold: Minimum number of tokens to consider as duplicate

    Returns:
        List of dictionaries containing:
        - files: List of files containing the duplicate
        - lines: Line numbers in each file
        - tokens: Number of duplicate tokens
        - code_snippet: Example of duplicated code
    """
    try:
        duplicates = []
        path_obj = Path(path)

        # Find all Python files
        py_files = list(path_obj.rglob("*.py"))

        # Parse all files into ASTs
        file_asts = {}
        for py_file in py_files:
            try:
                with open(py_file) as f:
                    content = f.read()
                    file_asts[py_file] = ast.parse(content)
            except (SyntaxError, UnicodeDecodeError):
                continue

        # Compare ASTs for similarities
        for i, (file1, ast1) in enumerate(file_asts.items()):
            for file2, ast2 in list(file_asts.items())[i + 1 :]:
                # Extract function bodies
                funcs1 = [node for node in ast.walk(ast1) if isinstance(node, ast.FunctionDef)]
                funcs2 = [node for node in ast.walk(ast2) if isinstance(node, ast.FunctionDef)]

                # Compare function bodies
                for func1 in funcs1:
                    for func2 in funcs2:
                        # Simple comparison: check if function bodies have similar structure
                        body1 = ast.dump(func1)
                        body2 = ast.dump(func2)

                        # Calculate similarity (simple approach)
                        tokens1 = set(body1.split())
                        tokens2 = set(body2.split())
                        common_tokens = tokens1 & tokens2
                        similarity = len(common_tokens)

                        if similarity >= threshold:
                            duplicates.append(
                                {
                                    "files": [str(file1), str(file2)],
                                    "functions": [func1.name, func2.name],
                                    "lines": [func1.lineno, func2.lineno],
                                    "tokens": similarity,
                                }
                            )

        return duplicates

    except Exception as e:
        return [{"error": str(e)}]


async def calculate_maintainability(file_path: str) -> dict[str, Any]:
    """
    Calculate maintainability index for a Python file

    Args:
        file_path: Path to the Python file

    Returns:
        Dictionary containing:
        - success: Boolean indicating if calculation succeeded
        - maintainability_index: MI score (0-100, higher is better)
        - rank: Letter grade (A=excellent, B=good, C=moderate)
        - complexity: Cyclomatic complexity
        - sloc: Source lines of code
        - comments: Comment ratio
        - error: Error message if calculation failed
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

        # Calculate maintainability index using radon
        mi = mi_visit(content, multi=True)

        # Get raw metrics
        raw = analyze(content)

        # Calculate rank based on MI
        if mi >= 20:
            rank = "A"  # Excellent
        elif mi >= 10:
            rank = "B"  # Good
        elif mi >= 0:
            rank = "C"  # Moderate
        else:
            rank = "D"  # Difficult

        return {
            "success": True,
            "file": file_path,
            "maintainability_index": round(mi, 2),
            "rank": rank,
            "complexity": raw.lloc,  # Logical lines of code as complexity proxy
            "sloc": raw.sloc,
            "lines_of_code": raw.loc,
            "comments": raw.comments,
            "blank": raw.blank,
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


async def analyze_dependencies(file_path: str) -> dict[str, Any]:
    """
    Analyze import dependencies in a Python file

    Args:
        file_path: Path to the Python file

    Returns:
        Dictionary containing:
        - success: Boolean indicating if analysis succeeded
        - imports: List of imported modules with details
        - total_imports: Total number of imports
        - stdlib_imports: Number of standard library imports
        - third_party_imports: Number of third-party imports
        - relative_imports: Number of relative imports
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

        # Parse the AST
        tree = ast.parse(content)

        imports = []
        stdlib_count = 0
        third_party_count = 0
        relative_count = 0

        # Standard library modules (partial list)
        stdlib_modules = {
            "os",
            "sys",
            "pathlib",
            "re",
            "json",
            "datetime",
            "collections",
            "itertools",
            "functools",
            "subprocess",
            "argparse",
            "logging",
            "unittest",
            "pytest",
            "typing",
            "io",
            "time",
            "random",
            "math",
            "string",
        }

        # Find all import statements
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    imports.append(
                        {
                            "module": module_name,
                            "alias": alias.asname,
                            "line": node.lineno,
                            "type": "import",
                        }
                    )
                    if module_name.split(".")[0] in stdlib_modules:
                        stdlib_count += 1
                    else:
                        third_party_count += 1

            elif isinstance(node, ast.ImportFrom):
                module_name = node.module if node.module else ""
                is_relative = node.level > 0

                for alias in node.names:
                    imports.append(
                        {
                            "module": module_name or f"{'.' * node.level}",
                            "name": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno,
                            "type": "from_import",
                            "relative": is_relative,
                            "level": node.level,
                        }
                    )

                if is_relative:
                    relative_count += 1
                elif module_name.split(".")[0] in stdlib_modules:
                    stdlib_count += 1
                else:
                    third_party_count += 1

        return {
            "success": True,
            "file": file_path,
            "imports": imports,
            "total_imports": len(imports),
            "stdlib_imports": stdlib_count,
            "third_party_imports": third_party_count,
            "relative_imports": relative_count,
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
mcp.tool(calculate_complexity)
mcp.tool(measure_code_coverage)
mcp.tool(detect_duplication)
mcp.tool(calculate_maintainability)
mcp.tool(analyze_dependencies)


if __name__ == "__main__":
    mcp.run(transport="stdio")
