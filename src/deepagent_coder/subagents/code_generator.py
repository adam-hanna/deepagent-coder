"""
Code Generator Subagent - Specialist for code generation tasks.

This module provides a specialized subagent focused on generating high-quality,
production-ready code following best practices and style guidelines.

The Code Generator specializes in:
- Implementing features from specifications
- Writing clean, maintainable, well-documented code
- Following language-specific best practices and style guides
- Creating comprehensive docstrings and comments
- Considering edge cases and error handling
- Writing code that integrates well with existing codebases

Example:
    from deepagent_coder.core.model_selector import ModelSelector
    from deepagent_coder.subagents.code_generator import create_code_generator_agent

    selector = ModelSelector()
    agent = await create_code_generator_agent(selector, tools=[])

    response = await agent.invoke("Implement a binary search function")
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Code Generation Specialist, an expert software engineer focused on producing high-quality, production-ready code.

Your core responsibilities:

1. **Code Generation Excellence**
   - Write clean, readable, maintainable code that follows established patterns
   - Implement features correctly and completely from specifications
   - Consider edge cases, error handling, and performance implications
   - Follow language-specific idioms and best practices
   - Write self-documenting code with clear variable and function names

2. **Documentation Standards**
   - Provide comprehensive docstrings for all public functions, classes, and modules
   - Include parameter types, return types, and descriptions
   - Document exceptions that may be raised
   - Add inline comments for complex logic or non-obvious decisions
   - Follow documentation standards (e.g., Google, NumPy, Sphinx styles)

3. **Code Quality Principles**
   - Write DRY (Don't Repeat Yourself) code
   - Keep functions focused and single-purpose
   - Use appropriate design patterns when beneficial
   - Ensure code is testable and loosely coupled
   - Consider SOLID principles in design

4. **Language-Specific Best Practices**
   - Follow PEP 8 for Python (or equivalent style guides for other languages)
   - Use type hints in Python for better code clarity
   - Implement proper error handling (try/except, Result types, etc.)
   - Use language features appropriately (list comprehensions, context managers, etc.)
   - Follow security best practices (input validation, safe API usage)

5. **Integration Awareness**
   - Write code that integrates smoothly with existing codebases
   - Respect existing patterns and architectural decisions
   - Minimize dependencies and coupling
   - Consider backward compatibility when modifying existing code
   - Ensure new code follows the project's conventions

6. **Quality Assurance**
   - Write code that is easy to test
   - Consider how the code will be used and maintained
   - Think about error messages and debugging experience
   - Validate inputs and handle edge cases gracefully
   - Write defensive code that fails fast with clear error messages

7. **CRITICAL: File Creation Workflow**
   - **ALWAYS create parent directories BEFORE writing files to subdirectories**
   - When asked to create files in subdirectories (e.g., "src/server.ts"):
     1. FIRST: Use create_directory tool to create the parent directory (e.g., "./src")
     2. THEN: Use write_file tool to create the file (e.g., "./src/server.ts")
   - Example correct sequence:
     ```
     create_directory(path="./src")
     write_file(path="./src/server.ts", content="...")
     ```
   - WRONG (will fail): write_file(path="./src/server.ts") without creating "./src" first
   - This applies to ANY nested path: always create parent directories first
   - Use relative paths starting with "./" (e.g., "./src/app.js", "./package.json")

When generating code:
1. Start by understanding the requirements completely
2. Consider the broader context and how the code fits into the system
3. Plan the structure and approach before implementing
4. Implement incrementally, focusing on correctness
5. Add comprehensive documentation as you go
6. Review your code for clarity, correctness, and completeness

Remember: You are producing code that other developers will read, maintain, and extend.
Code quality, clarity, and maintainability are just as important as functionality."""


def get_code_generation_guidelines() -> str:
    """
    Get comprehensive Python code generation guidelines.

    Returns:
        str: Detailed guidelines for Python code generation including style,
             documentation, error handling, and best practices.

    Example:
        guidelines = get_code_generation_guidelines()
        # Use guidelines in prompts or documentation
    """
    return """
## Python Style Guide and Best Practices

### Code Style (PEP 8)
- Use 4 spaces for indentation (never tabs)
- Limit lines to 100 characters (configurable)
- Use blank lines to separate logical sections
- Use snake_case for functions and variables
- Use PascalCase for class names
- Use UPPER_CASE for constants

### Type Hints
- Always use type hints for function parameters and return values
- Use `Optional[T]` for nullable types
- Use `List`, `Dict`, `Set`, `Tuple` from typing module
- Use `Any` sparingly and only when truly needed
- Example:
  ```python
  def process_data(items: List[str], count: Optional[int] = None) -> Dict[str, Any]:
      pass
  ```

### Documentation
- Use docstrings for all public modules, functions, classes, and methods
- Follow Google or NumPy docstring format
- Include:
  - Brief description (one line)
  - Detailed explanation (if needed)
  - Args: Parameter descriptions with types
  - Returns: Return value description with type
  - Raises: Exceptions that may be raised
  - Example usage (when helpful)

Example docstring:
```python
def calculate_average(numbers: List[float]) -> float:
    \"\"\"
    Calculate the arithmetic mean of a list of numbers.

    Args:
        numbers: A list of numeric values to average

    Returns:
        The arithmetic mean as a float

    Raises:
        ValueError: If the list is empty

    Example:
        >>> calculate_average([1.0, 2.0, 3.0])
        2.0
    \"\"\"
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)
```

### Error Handling
- Use specific exception types (ValueError, TypeError, etc.)
- Provide clear, actionable error messages
- Use try/except blocks appropriately
- Don't catch exceptions unless you can handle them meaningfully
- Consider using custom exception classes for domain-specific errors
- Always clean up resources (use context managers)

### Best Practices
- **Single Responsibility**: Each function should do one thing well
- **DRY**: Don't Repeat Yourself - extract common logic
- **KISS**: Keep It Simple, Stupid - avoid over-engineering
- **Composition over Inheritance**: Prefer composition when possible
- **Fail Fast**: Validate inputs early and raise clear errors
- **Use Built-ins**: Leverage Python's rich standard library
- **List Comprehensions**: Use for simple transformations
- **Context Managers**: Use `with` statements for resource management
- **Generators**: Use for memory-efficient iteration over large datasets

### Code Structure
```python
# Standard library imports
import os
import sys
from typing import List, Dict, Optional

# Third-party imports
import requests
import numpy as np

# Local application imports
from myapp.utils import helper_function

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Classes and functions
class MyClass:
    \"\"\"Brief description.\"\"\"

    def __init__(self, param: str):
        \"\"\"Initialize MyClass.\"\"\"
        self.param = param

    def method(self) -> str:
        \"\"\"Do something.\"\"\"
        return self.param

def my_function(arg: int) -> bool:
    \"\"\"Do something else.\"\"\"
    return arg > 0
```

### Common Patterns
- Use `pathlib.Path` instead of `os.path` for file operations
- Use `f-strings` for string formatting
- Use `enumerate()` instead of range(len())
- Use `zip()` for parallel iteration
- Use `defaultdict` from collections for grouping
- Use `dataclasses` for simple data containers
- Use `functools.lru_cache` for memoization
- Use `logging` module instead of print statements

### Testing Considerations
- Write code that's easy to test
- Avoid global state and side effects
- Use dependency injection for external dependencies
- Keep functions pure when possible
- Make I/O operations mockable
"""


async def create_code_generator_agent(
    model_selector,
    tools: list[Any],
    backend: Any | None = None,
    workspace_path: str | None = None,
) -> Any:
    """
    Create a code generator specialist subagent.

    This agent specializes in generating high-quality code following best practices,
    with comprehensive documentation and proper error handling.

    Args:
        model_selector: ModelSelector instance for obtaining the appropriate model
        tools: List of tools available to the agent (e.g., file operations, search)
        backend: Optional backend for agent state persistence. If None, creates a
                FilesystemBackend in the default workspace.
        workspace_path: Optional custom workspace path. If None, uses
                       ~/.deepagents/code_generator

    Returns:
        A configured DeepAgent instance specialized for code generation

    Example:
        from deepagent_coder.core.model_selector import ModelSelector

        selector = ModelSelector()
        agent = await create_code_generator_agent(selector, tools=[])

        response = await agent.invoke(
            "Generate a function to validate email addresses"
        )
    """
    # Use LangChain ReAct agent instead of deepagents (temporary workaround for langchain 1.x compatibility)
    from langgraph.prebuilt import create_react_agent

    logger.info("Creating code generator subagent...")

    # Get the appropriate model for code generation
    model = model_selector.get_model("code_generator")

    # Create the agent with specialized system prompt using ReAct pattern
    # Note: 'prompt' parameter changed from 'state_modifier' in langgraph 0.2+
    agent = create_react_agent(model, tools, prompt=SYSTEM_PROMPT)

    logger.info("✓ Code generator subagent created successfully")
    return agent
