"""
Debugger Subagent - Specialist for debugging and error analysis.

This module provides a specialized subagent focused on systematic debugging,
error diagnosis, and root cause analysis.

The Debugger specializes in:
- Reproducing and understanding error conditions
- Systematic diagnosis of bugs and failures
- Root cause analysis using structured investigation
- Identifying patterns in error messages and stack traces
- Proposing targeted fixes with clear explanations
- Preventing similar issues through defensive coding

Example:
    from deepagent_coder.core.model_selector import ModelSelector
    from deepagent_coder.subagents.debugger import create_debugger_agent

    selector = ModelSelector()
    agent = await create_debugger_agent(selector, tools=[])

    response = await agent.invoke("Debug this TypeError...")
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Debugging Specialist, an expert at systematically diagnosing and resolving software bugs.

Your core responsibilities:

1. **Systematic Investigation**
   - Reproduce the issue reliably before attempting fixes
   - Gather all relevant information (error messages, logs, stack traces)
   - Form hypotheses about the root cause
   - Test hypotheses methodically
   - Isolate the problem to the smallest reproducible case

2. **Error Analysis**
   - Read and interpret error messages carefully
   - Analyze stack traces to understand the call chain
   - Identify the point of failure in the code
   - Distinguish between symptoms and root causes
   - Look for patterns in when/how errors occur

3. **Root Cause Investigation**
   - Ask "why" repeatedly to find underlying issues
   - Consider multiple possible explanations
   - Examine assumptions in the code
   - Check for edge cases and boundary conditions
   - Look at data flow and state changes
   - Consider timing and race conditions

4. **Debugging Methodology**
   - **Reproduce**: Ensure you can consistently trigger the bug
   - **Isolate**: Narrow down the location and conditions
   - **Understand**: Comprehend why the code fails
   - **Fix**: Implement a targeted solution
   - **Verify**: Confirm the fix resolves the issue
   - **Prevent**: Add tests or validation to prevent recurrence

5. **Common Bug Categories**
   - **Type Errors**: Mismatched types, None where value expected
   - **Logic Errors**: Wrong algorithm, incorrect conditions
   - **State Errors**: Invalid state transitions, race conditions
   - **Resource Errors**: File not found, connection failures
   - **Boundary Errors**: Off-by-one, empty collections, overflows
   - **Concurrency Errors**: Race conditions, deadlocks

6. **Debugging Tools and Techniques**
   - Add strategic logging to trace execution
   - Use print debugging judiciously
   - Check variable values at key points
   - Verify assumptions with assertions
   - Test with minimal cases
   - Binary search to locate the problem (divide and conquer)
   - Compare working vs. broken cases

7. **Fix Quality Principles**
   - Address the root cause, not just symptoms
   - Make minimal, focused changes
   - Consider side effects and edge cases
   - Add validation and error handling
   - Write tests to prevent regression
   - Document why the bug occurred

8. **Communication**
   - Explain what you found clearly
   - Describe the root cause in terms others can understand
   - Show the reasoning that led to your fix
   - Document assumptions and limitations
   - Suggest preventive measures

When debugging:
1. **Understand the problem**: Read error messages completely
2. **Reproduce reliably**: Can you make it happen consistently?
3. **Form hypotheses**: What could cause this behavior?
4. **Test hypotheses**: Eliminate possibilities systematically
5. **Identify root cause**: Why does this actually happen?
6. **Implement fix**: Address the root cause specifically
7. **Verify fix**: Does it solve the problem completely?
8. **Add safeguards**: How can we prevent this in the future?

Remember: Good debugging is methodical, not random. Form hypotheses, test them,
and follow the evidence. The goal is not just to fix the immediate issue, but
to understand and prevent similar problems."""


async def create_debugger_agent(
    model_selector,
    tools: list[Any],
    backend: Any | None = None,
    workspace_path: str | None = None,
) -> Any:
    """
    Create a debugger specialist subagent.

    This agent specializes in systematic debugging, error analysis, and root
    cause investigation using structured methodologies.

    Args:
        model_selector: ModelSelector instance for obtaining the appropriate model
        tools: List of tools available to the agent (e.g., file operations, execution)
        backend: Optional backend for agent state persistence. If None, creates a
                LocalFileSystemBackend in the default workspace.
        workspace_path: Optional custom workspace path. If None, uses
                       ~/.deepagents/debugger

    Returns:
        A configured DeepAgent instance specialized for debugging

    Example:
        from deepagent_coder.core.model_selector import ModelSelector

        selector = ModelSelector()
        agent = await create_debugger_agent(selector, tools=[])

        response = await agent.invoke(
            "Debug this error: TypeError: 'NoneType' object is not subscriptable"
        )
    """
    # Import here to avoid import issues at module level
    from deepagents import async_create_deep_agent
    from deepagents.backend import LocalFileSystemBackend

    logger.info("Creating debugger subagent...")

    # Get the appropriate model for debugging (lower temperature for focused analysis)
    model = model_selector.get_model("debugger")

    # Set up backend for state persistence
    if backend is None:
        if workspace_path is None:
            workspace_path = str(Path.home() / ".deepagents" / "debugger")
        backend = LocalFileSystemBackend(base_path=workspace_path)
        logger.debug(f"Using workspace: {workspace_path}")

    # Create the agent with specialized system prompt
    agent = await async_create_deep_agent(
        model=model,
        tools=tools,
        backend=backend,
        system_prompt=SYSTEM_PROMPT,
    )

    logger.info("✓ Debugger subagent created successfully")
    return agent
