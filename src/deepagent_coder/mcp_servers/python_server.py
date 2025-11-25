"""Python tools MCP server - code execution, analysis, profiling"""

import ast
import asyncio
import json
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

mcp = FastMCP("Python Tools")


async def _run_python_impl(code: str, timeout: int = 30) -> dict[str, Any]:
    """
    Execute Python code safely with timeout

    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds

    Returns:
        Dictionary with stdout, stderr, returncode, or error
    """
    try:
        # Validate syntax first
        ast.parse(code)

        # Execute with timeout
        process = await asyncio.create_subprocess_exec(
            "python",
            "-c",
            code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

            return {
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8"),
                "returncode": process.returncode,
            }
        except TimeoutError:
            process.kill()
            await process.wait()
            return {"error": f"Execution timed out after {timeout} seconds", "returncode": -1}

    except SyntaxError as e:
        return {"error": f"SyntaxError: {e.msg} at line {e.lineno}", "returncode": 1}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "returncode": 1}


@mcp.tool()
async def run_python(code: str, timeout: int = 30) -> dict[str, Any]:
    """MCP tool wrapper for run_python"""
    return await _run_python_impl(code, timeout)


async def _analyze_code_impl(file_path: str) -> dict[str, Any]:
    """
    Perform static analysis on Python file using AST

    Args:
        file_path: Path to Python file to analyze

    Returns:
        Dictionary with functions, classes, imports, and complexity metrics
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}"}

        if path.suffix != ".py":
            return {"error": f"Not a Python file: {file_path}"}

        with open(path, encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=file_path)
        analyzer = CodeAnalyzer()
        analyzer.visit(tree)

        return {
            "file": file_path,
            "functions": analyzer.functions,
            "classes": analyzer.classes,
            "imports": analyzer.imports,
            "complexity_score": analyzer.calculate_complexity(),
            "lines_of_code": len(source.splitlines()),
        }

    except SyntaxError as e:
        return {"error": f"SyntaxError in {file_path}: {e.msg} at line {e.lineno}"}
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}


@mcp.tool()
async def analyze_code(file_path: str) -> dict[str, Any]:
    """MCP tool wrapper for analyze_code"""
    return await _analyze_code_impl(file_path)


class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor for comprehensive code analysis"""

    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = []
        self.complexity = 0
        self._current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Extract function information"""
        func_info = {
            "name": node.name,
            "args": [a.arg for a in node.args.args],
            "lineno": node.lineno,
            "col_offset": node.col_offset,
            "docstring": ast.get_docstring(node),
            "is_async": False,
            "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
        }

        if self._current_class:
            self.classes[-1]["methods"].append(func_info)
        else:
            self.functions.append(func_info)

        # Count decision points for complexity
        self.complexity += self._count_decision_points(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Extract async function information"""
        func_info = {
            "name": node.name,
            "args": [a.arg for a in node.args.args],
            "lineno": node.lineno,
            "col_offset": node.col_offset,
            "docstring": ast.get_docstring(node),
            "is_async": True,
            "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
        }

        if self._current_class:
            self.classes[-1]["methods"].append(func_info)
        else:
            self.functions.append(func_info)

        self.complexity += self._count_decision_points(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Extract class information"""
        self._current_class = node.name

        class_info = {
            "name": node.name,
            "bases": [self._get_base_name(b) for b in node.bases],
            "lineno": node.lineno,
            "col_offset": node.col_offset,
            "docstring": ast.get_docstring(node),
            "methods": [],
            "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
        }

        self.classes.append(class_info)
        self.generic_visit(node)
        self._current_class = None

    def visit_Import(self, node: ast.Import):
        """Extract import statements"""
        for alias in node.names:
            self.imports.append(
                {
                    "module": alias.name,
                    "alias": alias.asname,
                    "type": "import",
                    "lineno": node.lineno,
                }
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Extract from...import statements"""
        module = node.module or ""
        for alias in node.names:
            self.imports.append(
                {
                    "module": f"{module}.{alias.name}" if module else alias.name,
                    "alias": alias.asname,
                    "type": "from_import",
                    "from_module": module,
                    "lineno": node.lineno,
                }
            )
        self.generic_visit(node)

    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Extract decorator name"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return "unknown"

    def _get_base_name(self, base: ast.expr) -> str:
        """Extract base class name"""
        return self._get_name(base)

    def _get_name(self, node: ast.expr) -> str:
        """Extract name from various node types"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return "unknown"

    def _count_decision_points(self, node: ast.AST) -> int:
        """Count cyclomatic complexity decision points"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(
                child,
                (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.And, ast.Or),
            ):
                complexity += 1

        return complexity

    def calculate_complexity(self) -> int:
        """Calculate total cyclomatic complexity"""
        return self.complexity


async def _profile_code_impl(
    file_path: str, function_name: str = "main", args: str | None = None
) -> dict[str, Any]:
    """
    Profile Python code performance

    Args:
        file_path: Path to Python file
        function_name: Name of function to profile
        args: Optional JSON string of arguments to pass

    Returns:
        Profiling statistics including execution time and call counts
    """
    try:
        import cProfile
        import importlib.util
        from io import StringIO
        import pstats

        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}"}

        # Import the module
        spec = importlib.util.spec_from_file_location("_profile_module", path)
        if spec is None or spec.loader is None:
            return {"error": f"Could not load module from {file_path}"}

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get the function
        if not hasattr(module, function_name):
            return {"error": f"Function '{function_name}' not found in {file_path}"}

        func = getattr(module, function_name)

        # Parse arguments if provided
        func_args = []
        func_kwargs = {}
        if args:
            parsed_args = json.loads(args)
            if isinstance(parsed_args, list):
                func_args = parsed_args
            elif isinstance(parsed_args, dict):
                func_kwargs = parsed_args

        # Profile execution
        profiler = cProfile.Profile()
        profiler.enable()

        try:
            result = func(*func_args, **func_kwargs)
        except Exception as e:
            profiler.disable()
            return {"error": f"Function execution failed: {str(e)}"}

        profiler.disable()

        # Get statistics
        stream = StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats("cumulative")
        stats.print_stats(20)

        return {
            "file": file_path,
            "function": function_name,
            "profile_output": stream.getvalue(),
            "total_calls": stats.total_calls,
            "total_time": stats.total_tt,
            "result": str(result) if result is not None else None,
        }

    except Exception as e:
        return {"error": f"Profiling failed: {str(e)}"}


@mcp.tool()
async def profile_code(
    file_path: str, function_name: str = "main", args: str | None = None
) -> dict[str, Any]:
    """MCP tool wrapper for profile_code"""
    return await _profile_code_impl(file_path, function_name, args)


def run_server():
    """Run the Python MCP server"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
