"""Main CodingDeepAgent orchestration class"""

import logging
from pathlib import Path
import sys
from typing import Any, TypedDict

from deepagent_coder.core.config import Config
from deepagent_coder.core.mcp_client import MCPClientManager
from deepagent_coder.core.model_selector import ModelSelector
from deepagent_coder.middleware.audit_middleware import create_audit_middleware
from deepagent_coder.middleware.error_recovery_middleware import create_error_recovery_middleware
from deepagent_coder.middleware.git_safety_middleware import create_git_safety_middleware
from deepagent_coder.middleware.logging_middleware import create_logging_middleware
from deepagent_coder.middleware.memory_middleware import create_memory_middleware
from deepagent_coder.subagents.code_generator import create_code_generator_agent
from deepagent_coder.subagents.code_navigator import create_code_navigator
from deepagent_coder.subagents.code_reviewer import create_code_review_agent
from deepagent_coder.subagents.debugger import create_debugger_agent
from deepagent_coder.subagents.devops import create_devops_agent
from deepagent_coder.subagents.refactorer import create_refactorer_agent
from deepagent_coder.subagents.test_writer import create_test_writer_agent
from deepagent_coder.utils.file_organizer import FileOrganizer
from deepagent_coder.utils.session_manager import SessionManager

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State passed between agents in the graph"""

    messages: list[Any]
    current_file: str
    project_context: dict[str, Any]
    next_agent: str
    search_results: dict[str, Any]  # Store search findings from code navigator
    deployment_state: dict[str, Any]  # Track deployment status
    test_results: dict[str, Any]  # Test results from tester agent
    review_results: dict[str, Any]  # Code review results from reviewer agent
    quality_score: float  # Overall quality score from review (0-10)
    quality_gate_passed: bool  # Whether code meets quality threshold


class CodingDeepAgent:
    """
    Production-ready coding assistant using DeepAgent architecture

    Integrates all components: models, MCP tools, subagents, middleware,
    and file organization for a complete AI coding assistant.
    """

    def __init__(
        self,
        model: str | None = None,
        workspace: str | None = None,
        config: Config | None = None,
    ):
        """
        Initialize coding agent

        Args:
            model: Ollama model name (overrides config)
            workspace: Workspace directory path (overrides config)
            config: Configuration instance. If not provided, uses defaults.
        """
        # Use provided config or create new one
        self.config = config or Config()

        # CLI args override config
        if model:
            self.config.set("agent.model", model)
        if workspace:
            self.config.set("workspace.path", workspace)

        # Get effective values from config
        self.model_name = self.config.get("agent.model", "qwen2.5-coder:latest")
        workspace_path = self.config.get("workspace.path", "~/.deepagents/workspace")
        self.workspace = Path(workspace_path).expanduser()
        self.workspace.mkdir(parents=True, exist_ok=True)

        # Core components
        self.model_selector = ModelSelector(config=self.config)
        self.mcp_client: MCPClientManager | None = None
        self.file_organizer = FileOrganizer(str(self.workspace))

        # Get sessions directory from config
        sessions_dir = self.config.get("workspace.sessions_dir", "sessions")
        self.session_manager = SessionManager(str(self.workspace / sessions_dir))

        # Agent and subagents
        self.agent = None
        self.subagents: dict[str, Any] = {}

        # Middleware
        self.middleware: list[Any] = []

        # State
        self.initialized = False

        logger.info(f"CodingDeepAgent created with model {self.model_name}")
        logger.info(f"Workspace: {self.workspace}")

    async def initialize(self) -> None:
        """Initialize MCP tools, subagents, and agent"""
        if self.initialized:
            logger.warning("Agent already initialized")
            return

        logger.info("Initializing CodingDeepAgent...")

        try:
            # Setup MCP tools
            await self._setup_mcp_tools()

            # Create subagents
            await self._create_subagents()

            # Setup middleware stack
            self._setup_middleware()

            # Create main agent (placeholder for now - would use DeepAgent)
            self._create_main_agent()

            self.initialized = True
            logger.info("CodingDeepAgent initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise

    async def _setup_mcp_tools(self) -> None:
        """Setup MCP client and tools"""
        # Resolve workspace path to handle symlinks (e.g., /tmp -> /private/tmp on macOS)
        resolved_workspace = self.workspace.resolve()

        # Get path to Python filesystem server
        project_root = Path(__file__).parent.parent.parent
        filesystem_server_path = (
            project_root / "src" / "deepagent_coder" / "mcp_servers" / "filesystem_server.py"
        )

        # Use Python-based filesystem server (no Node.js required!)
        custom_config = {
            "filesystem": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(filesystem_server_path)],
                "env": {"WORKSPACE_PATH": str(resolved_workspace)},
            }
        }

        # Only use custom config, no defaults (to avoid loading broken custom servers)
        self.mcp_client = MCPClientManager(custom_configs=custom_config, use_defaults=False)
        await self.mcp_client.initialize()
        logger.info(f"MCP tools initialized for workspace: {resolved_workspace}")

    async def _create_subagents(self) -> None:
        """Create specialized subagents"""
        logger.info("Creating subagents...")

        # Get tools for subagents (if MCP client is set up)
        tools = []
        if self.mcp_client:
            try:
                tools = await self.mcp_client.get_all_tools()
            except Exception as e:
                logger.warning(f"Could not get MCP tools for subagents: {e}")

        # Create all subagents
        # Note: code_navigator takes just llm, others need model_selector + tools
        self.subagents = {
            "code_generator": await create_code_generator_agent(self.model_selector, tools=tools),
            "debugger": await create_debugger_agent(self.model_selector, tools=tools),
            "test_writer": await create_test_writer_agent(self.model_selector, tools=tools),
            "refactorer": await create_refactorer_agent(self.model_selector, tools=tools),
            "devops": await create_devops_agent(self.model_selector, tools=tools),
            "code_review": await create_code_review_agent(self.model_selector, tools=tools),
            "code_navigator": await create_code_navigator(
                self.model_selector.get_model("code_generator")
            ),
        }

        logger.info(f"Created {len(self.subagents)} subagents")

    def _setup_middleware(self) -> None:
        """Setup middleware stack from configuration"""
        self.middleware = []

        # Logging middleware
        if self.config.get("agent.logging.file"):
            log_file = str(self.workspace / self.config.get("agent.logging.file"))
            self.middleware.append(create_logging_middleware(log_file=log_file))

        # Memory middleware
        if self.config.get("middleware.memory.enabled", True):
            threshold = self.config.get("middleware.memory.threshold", 6000)
            self.middleware.append(
                create_memory_middleware(self.model_selector, threshold=threshold)
            )

        # Git safety middleware
        if self.config.get("middleware.git_safety.enabled", True):
            enforce = self.config.get("middleware.git_safety.enforce", False)
            self.middleware.append(create_git_safety_middleware(enforce=enforce))

        # Error recovery middleware
        if self.config.get("middleware.error_recovery.enabled", True):
            max_retries = self.config.get("middleware.error_recovery.max_retries", 3)
            self.middleware.append(create_error_recovery_middleware(max_retries=max_retries))

        # Audit middleware
        if self.config.get("middleware.audit.enabled", True):
            audit_file = str(
                self.workspace / self.config.get("middleware.audit.file", "audit.jsonl")
            )
            self.middleware.append(create_audit_middleware(audit_file=audit_file))

        logger.info(f"Middleware stack configured with {len(self.middleware)} components")

    def _create_main_agent(self) -> None:
        """Create main agent with all components"""
        # Get the main agent model
        self.main_model = self.model_selector.get_model("main_agent")

        # Store tools reference (will be populated after MCP init)
        self.tools: list[Any] = []

        # Create agent structure
        self.agent = type("Agent", (), {"ainvoke": self._agent_invoke})()
        logger.info("Main agent created with model")

    async def _get_tools(self) -> list[Any]:
        """Get tools from MCP client"""
        if not self.tools and self.mcp_client:
            try:
                self.tools = await self.mcp_client.get_all_tools()
                logger.info(f"Retrieved {len(self.tools)} MCP tools")
            except Exception as e:
                logger.warning(f"Failed to get MCP tools: {e}")
                self.tools = []
        return self.tools

    async def _ensure_parent_directory_exists(self, file_path: str, tools: list[Any]) -> None:
        """
        Automatically create parent directory for a file if it doesn't exist.

        Args:
            file_path: Path to the file (may be relative like "./src/server.ts")
            tools: List of available tools (to find create_directory tool)
        """
        # Extract parent directory from ORIGINAL relative path
        original_path_obj = Path(file_path)
        parent_dir = original_path_obj.parent

        # Only create if parent is not current directory
        if str(parent_dir) != "." and parent_dir != Path("."):
            # Convert to workspace-relative path (remove ./ prefix if present)
            parent_str = str(parent_dir)
            if parent_str.startswith("./"):
                parent_str = parent_str[2:]

            logger.info(f"[auto-mkdir] Creating parent directory: ./{parent_str}")
            # Find and call create_directory tool with ABSOLUTE workspace path
            for mkdir_tool in tools:
                if "create_directory" in mkdir_tool.name.lower():
                    try:
                        # Convert to absolute workspace path (same as path-fixing logic)
                        abs_parent_path = (self.workspace / parent_str).resolve()
                        await mkdir_tool.ainvoke({"path": str(abs_parent_path)})
                        logger.info(f"[auto-mkdir] ✓ Created: {abs_parent_path}")
                    except Exception as e:
                        logger.debug(f"[auto-mkdir] Note: {e}")
                    break

    async def _agent_invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        """Agent invocation with LLM and tool calling"""
        import json

        # Apply middleware
        for middleware in self.middleware:
            state = await middleware(state)

        # Get messages
        messages = state.get("messages", [])

        # Convert to LangChain format
        from langchain_core.messages import (
            AIMessage,
            BaseMessage,
            HumanMessage,
            SystemMessage,
            ToolMessage,
        )

        # Add system prompt
        system_prompt = f"""You are an orchestrator agent coordinating specialized subagents for coding tasks.

🚨 **CRITICAL FILE CREATION RULE - READ THIS FIRST** 🚨
BEFORE writing ANY file to a subdirectory, you MUST create the parent directory first!
Example: To create "src/server.ts", you MUST first call create_directory with path="./src"
This is NOT optional. The write_file tool will FAIL if the parent directory doesn't exist.

Your workspace directory is: {self.workspace}

**CRITICAL WORKSPACE RULES:**
1. ALL file operations MUST be within the workspace directory
2. NEVER use absolute paths outside the workspace (e.g., /Users/..., /home/...)
3. NEVER try to access files in the project source code directory
4. Use RELATIVE paths starting with "./" (e.g., "./src/app.js", "./package.json")
5. The MCP filesystem server restricts access to the workspace only - any attempts to access files outside will fail

If you see errors like "Access denied - path outside allowed directories", it means you tried to access a file outside the workspace. Always use relative paths within the workspace.

Available subagents:
- code_generator: Writes new code and creates files
- debugger: Finds and fixes bugs
- test_writer: Creates test cases
- refactorer: Improves existing code
- devops: Handles deployment, containerization (Docker, K8s), and infrastructure (Terraform)
- code_review: Performs automated code quality reviews with metrics and scoring
- code_navigator: Searches codebase to find files, functions, APIs, database calls, etc.

When to use code_navigator:
- User asks "where is X?" or "find X" or "locate X"
- Need to find API endpoints, functions, classes, or database queries
- Before modifying code, to find the right file location
- When other agents need to know where code is located
- To understand project structure and organization

Workflow with code_navigator:
1. Route to code_navigator with search query (e.g., "find the user login endpoint")
2. Code navigator returns findings in search_results with file paths and line numbers
3. Use search_results to guide other agents (e.g., debugger knows which file to fix)

Example workflow for "Fix the login bug":
1. Route to code_navigator: "Find the login endpoint and authentication logic"
2. Review search_results with file locations
3. Route to debugger with specific file paths from search_results
4. Debugger fixes the issue in the identified files

When to use devops:
- User requests containerization (Docker, docker-compose)
- Need to create Kubernetes deployment manifests
- Infrastructure as code tasks (Terraform)
- CI/CD pipeline setup (GitHub Actions, GitLab CI)
- Deployment configurations and YAML management
- Any task involving "deploy", "containerize", "kubernetes", "docker", "terraform"

Workflow with devops:
1. After code changes, route to tester first to ensure tests pass
2. Then route to devops with deployment requirements
3. DevOps creates/updates deployment configurations
4. DevOps handles containerization and infrastructure setup

Example workflow for "Deploy this application":
1. Route to tester: "Run all tests for this application"
2. Review test_results to ensure all pass
3. Route to devops: "Create Docker configuration and Kubernetes manifests"
4. DevOps generates Dockerfile, docker-compose.yml, and K8s manifests
5. DevOps updates deployment_state with configuration details

When to use code_review:
- After code generation to ensure quality standards
- Before deployment to check if code meets quality gates
- User requests "review", "check quality", or "assess code"
- To identify issues in existing code (complexity, security, coverage)
- To ensure test coverage is adequate
- To verify maintainability and best practices

Workflow with code_review:
1. Route to code_review with file paths or code to review
2. Code reviewer analyzes metrics (complexity, coverage, security)
3. Reviewer updates review_results with findings and issues
4. Reviewer sets quality_score (0-10) and quality_gate_passed (true/false)
5. If quality_gate_passed is false, route back to appropriate agent for fixes

Example workflow for "Generate and review authentication module":
1. Route to code_generator: "Create authentication module with login/logout"
2. Code generator creates auth.py
3. Route to code_review: "Review the newly created auth.py"
4. Reviewer analyzes and sets review_results with score 7.5 (below threshold)
5. Route back to code_generator with review feedback to address issues
6. Route to code_review again to verify improvements
7. Once quality_gate_passed is true, proceed to next step

## QUALITY GATE ENFORCEMENT (CRITICAL)

Before routing to devops for deployment, you MUST enforce the quality gate:

**Quality Gate Rules:**
1. IF deploying AND quality_gate_passed is not true:
   - BLOCK deployment
   - Route to code_review first
   - Wait for quality_gate_passed to be set to true

2. IF quality_gate_passed is false:
   - DO NOT proceed to deployment
   - Inform user that code needs improvement
   - Route to appropriate agent to fix issues

3. IF quality_gate_passed is true:
   - Allow deployment to proceed
   - Route to devops

**Example - Deployment with Quality Gate:**
User: "Deploy this application"

Step 1: Check quality_gate_passed in state
- If true: Route to devops
- If false or not set: Route to code_review first

Step 2: After code_review completes
- Check quality_gate_passed again
- If true: Route to devops
- If false: Inform user of issues, suggest fixes

**Example - Failed Quality Gate:**
User: "Deploy the new feature"
State: quality_gate_passed = false, quality_score = 6.5

Response: "Quality gate failed (score: 6.5/10). Cannot deploy. Issues found:
- Test coverage only 65% (need 80%)
- 2 security vulnerabilities detected
Please address these issues before deployment."

Route to code_generator or debugger to fix issues.

When creating files (via code_generator or directly):
1. **IMPORTANT**: If a file is in a subdirectory (e.g., "src/server.ts"), you MUST create the directory FIRST using create_directory
2. Use the write_file tool to save code to disk
3. Output ALL tool calls at once as a JSON array (multiple files in ONE response)
4. File paths must be relative to workspace root (e.g., "./file.txt", "./src/app.js")
5. Create ALL necessary files (package.json, source files, README, etc.) in a SINGLE response

CRITICAL FORMAT: Output a JSON array of tool calls (one per line):
[
{{"name": "create_directory", "arguments": {{"path": "./src"}}}},
{{"name": "write_file", "arguments": {{"path": "./package.json", "content": "..."}}}},
{{"name": "write_file", "arguments": {{"path": "./src/server.js", "content": "..."}}}},
{{"name": "write_file", "arguments": {{"path": "./README.md", "content": "..."}}}}
]

IMPORTANT:
- **ALWAYS create directories before files in subdirectories** (create_directory BEFORE write_file)
- Use \\n for newlines in content, NOT actual newlines
- All JSON must be valid (escape quotes, etc.)
- Output ALL files the user requested in ONE response
- All paths must be within the workspace (no absolute paths outside workspace)

Example for "Create src/server.ts and package.json":
[
{{"name": "create_directory", "arguments": {{"path": "./src"}}}},
{{"name": "write_file", "arguments": {{"path": "./package.json", "content": "{{\\"name\\":\\"my-app\\",\\"version\\":\\"1.0.0\\"}}"}}}}
{{"name": "write_file", "arguments": {{"path": "./src/server.ts", "content": "import express from 'express';\\nconst app = express();\\napp.listen(3000);"}}}}
]

🚨 **CRITICAL EDITING RULE - READ THIS BEFORE MODIFYING FILES** 🚨
When EDITING existing files, you MUST use the edit_file tool, NOT write_file!
- write_file: Use ONLY for creating NEW files or completely replacing a file
- edit_file: Use for modifying EXISTING files (fixes bugs, updates code, changes specific lines)

HOW TO USE edit_file:
The edit_file tool requires:
1. path: The file to edit (relative path like "./src/server.ts")
2. edits: An array of edit objects, where each edit has:
   - oldText: The EXACT text to find and replace (must match exactly, including whitespace)
   - newText: The replacement text

Example: Fix a bug in existing code:
{{"name": "edit_file", "arguments": {{
  "path": "./src/server.ts",
  "edits": [
    {{
      "oldText": "res.status(201).json({{ id: newTodo.id, description: newTodo.text, completed: newTodo.completed }})",
      "newText": "res.status(201).json({{ id: newTodo.id, text: newTodo.text, completed: newTodo.completed }})"
    }}
  ]
}}}}

Example: Change multiple parts of a file:
{{"name": "edit_file", "arguments": {{
  "path": "./config.json",
  "edits": [
    {{
      "oldText": "\\"port\\": 3000",
      "newText": "\\"port\\": 8080"
    }},
    {{
      "oldText": "\\"debug\\": false",
      "newText": "\\"debug\\": true"
    }}
  ]
}}}}

CRITICAL edit_file RULES:
1. oldText must match EXACTLY - every character, space, and newline
2. Read the file first with read_file to see the exact text you need to match
3. Copy the EXACT text from the file output (preserve indentation, quotes, etc.)
4. If oldText doesn't match exactly, the edit will FAIL
5. You can make multiple edits in one call by adding more objects to the edits array

Example workflow for fixing a bug:
1. Read the file: {{"name": "read_file", "arguments": {{"path": "./src/server.ts"}}}}
2. Find the buggy line in the output (e.g., line 21)
3. Copy the EXACT text of that line
4. Create edit_file call with exact oldText and corrected newText

Available tools:
- create_directory: Create a directory (use BEFORE writing files to subdirectories)
- write_file: Create or overwrite a file (ONLY for NEW files, not editing)
- edit_file: Edit existing files by replacing exact text matches
- read_file: Read a file (ALWAYS read before editing to get exact text)
- list_directory: List directory contents
- move_file: Move or rename files and directories
- delete_file: Delete a single file
- delete_directory: Delete a directory (use recursive=true for non-empty directories)
- run_shell_command: Execute shell commands for operations not covered by other tools (e.g., npm install, git commands, grep, etc.)

🚨 **FILE DELETION** 🚨
Use the delete_file and delete_directory tools for file operations:
- Delete a file: Use delete_file with path='./path/to/file.txt'
- Delete a directory: Use delete_directory with path='./path/to/directory' and recursive=true
- Be CAREFUL with deletion - it's permanent!

Example: Delete old test file
{{"name": "delete_file", "arguments": {{"path": "./old-test.js"}}}}

Example: Run shell command
{{"name": "run_shell_command", "arguments": {{"command": "npm install"}}}}

Be proactive and efficient - create directories AND files in ONE response!"""

        lc_messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))

        # Get tools and bind to model
        tools = await self._get_tools()
        logger.info(f"Retrieved {len(tools) if tools else 0} tools from MCP")
        if tools:
            logger.info(f"Available tool names: {[t.name for t in tools[:5]]}")  # Show first 5
            model_with_tools = self.main_model.bind_tools(tools)
            logger.info(f"✓ Successfully bound {len(tools)} tools to model")
        else:
            model_with_tools = self.main_model
            logger.warning("⚠ No tools available, using model without tools")

        # Agent loop - handle tool calling
        max_iterations = self.config.get("agent.max_iterations", 10)
        for iteration in range(max_iterations):
            logger.info(f"═══ Agent iteration {iteration + 1}/{max_iterations} ═══")

            # Call LLM
            logger.info("Calling LLM...")
            response = await model_with_tools.ainvoke(lc_messages)
            logger.info(f"LLM response type: {type(response)}")
            logger.info(f"LLM response has tool_calls: {hasattr(response, 'tool_calls')}")

            # Check if there are structured tool calls (OpenAI-style)
            has_tool_calls = hasattr(response, "tool_calls") and response.tool_calls

            if has_tool_calls:
                logger.info(f"Number of tool calls: {len(response.tool_calls)}")
                lc_messages.append(response)

                logger.info(f"🔧 Processing {len(response.tool_calls)} tool call(s)")

                # Execute tool calls
                for tool_call in response.tool_calls:
                    tool_name = tool_call.get("name")
                    tool_args = tool_call.get("args", {})
                    tool_id = tool_call.get("id")

                    logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

                    try:
                        # AUTO-MKDIR: Create parent directory before write_file
                        if tool_name and "write_file" in tool_name.lower():
                            file_path = tool_args.get("path") or tool_args.get("file_path")
                            if file_path:
                                await self._ensure_parent_directory_exists(file_path, tools)

                        # Find and execute the tool
                        tool_result = None
                        for tool in tools:
                            if tool.name == tool_name:
                                tool_result = await tool.ainvoke(tool_args)
                                break

                        if tool_result is None:
                            tool_result = f"Error: Tool {tool_name} not found"

                        logger.info(f"Tool result: {str(tool_result)[:200]}")

                        # Add tool result to messages
                        lc_messages.append(
                            ToolMessage(content=str(tool_result), tool_call_id=tool_id)
                        )

                    except Exception as e:
                        logger.error(f"Tool execution error: {e}")
                        lc_messages.append(
                            ToolMessage(
                                content=f"Error executing tool: {str(e)}", tool_call_id=tool_id
                            )
                        )
            else:
                # Ollama models don't support tool_calls, parse JSON from content
                print("DEBUG: No structured tool_calls, parsing JSON from content")
                lc_messages.append(response)

                # Try to extract JSON tool calls from content
                raw_content = response.content if hasattr(response, "content") else ""
                # Convert content to string if it's a list
                content = str(raw_content)
                print(f"DEBUG: Content length: {len(content)}")
                print(f"DEBUG: Content preview: {content[:500]}")

                tool_calls = []

                # Strategy 1: Try to parse entire content as JSON array
                try:
                    parsed = json.loads(content.strip())
                    if isinstance(parsed, list):
                        # It's an array of tool calls
                        for item in parsed:
                            if isinstance(item, dict) and "name" in item:
                                # Normalize: accept both "arguments" and "parameters"
                                if "parameters" in item and "arguments" not in item:
                                    item["arguments"] = item["parameters"]
                                if "arguments" in item:
                                    tool_calls.append(item)
                                    print(f"DEBUG: Found tool call from array: {item.get('name')}")
                    elif isinstance(parsed, dict) and "name" in parsed:
                        # It's a single tool call object
                        # Normalize: accept both "arguments" and "parameters"
                        if "parameters" in parsed and "arguments" not in parsed:
                            parsed["arguments"] = parsed["parameters"]
                        if "arguments" in parsed:
                            tool_calls.append(parsed)
                            print(f"DEBUG: Found single tool call: {parsed.get('name')}")
                except json.JSONDecodeError:
                    print("DEBUG: Content is not valid JSON, trying individual object extraction")
                    pass

                # Strategy 2: If Strategy 1 failed, find individual JSON objects with balanced braces
                if not tool_calls:
                    i = 0
                    while i < len(content):
                        # Find start of JSON object
                        if content[i] == "{":
                            # Try to extract a complete JSON object
                            brace_count = 0
                            start = i
                            in_string = False
                            escape_next = False

                            for j in range(i, len(content)):
                                char = content[j]

                                if escape_next:
                                    escape_next = False
                                    continue

                                if char == "\\":
                                    escape_next = True
                                    continue

                                if char == '"' and not escape_next:
                                    in_string = not in_string

                                if not in_string:
                                    if char == "{":
                                        brace_count += 1
                                    elif char == "}":
                                        brace_count -= 1

                                        if brace_count == 0:
                                            # Found complete JSON object
                                            json_str = content[start : j + 1]
                                            try:
                                                obj = json.loads(json_str)
                                                if "name" in obj:
                                                    # Normalize: accept both "arguments" and "parameters"
                                                    if (
                                                        "parameters" in obj
                                                        and "arguments" not in obj
                                                    ):
                                                        obj["arguments"] = obj["parameters"]
                                                    if "arguments" in obj:
                                                        tool_calls.append(obj)
                                                        print(
                                                            f"DEBUG: Found tool call: {obj.get('name')}"
                                                        )
                                            except:
                                                pass
                                            i = j
                                            break
                        i += 1

                if not tool_calls:
                    # No tool calls found, we're done
                    print("DEBUG: No tool calls found in content, agent finished")
                    break

                print(f"DEBUG: Found {len(tool_calls)} tool call(s)")

                # Execute each tool call
                tool_results = []
                for tool_call_dict in tool_calls:
                    tool_name = tool_call_dict.get("name")
                    tool_args = tool_call_dict.get("arguments", {})

                    print(f"DEBUG: Executing tool: {tool_name}")
                    print(f"DEBUG: Args: {tool_args}")

                    try:
                        # AUTO-MKDIR: Create parent directory before write_file
                        # MUST happen BEFORE path fixing, using the original relative path
                        if tool_name and "write_file" in tool_name.lower():
                            file_path = tool_args.get("path") or tool_args.get("file_path")
                            if file_path:
                                await self._ensure_parent_directory_exists(file_path, tools)

                        # Fix paths for filesystem operations - convert to absolute workspace paths
                        if (
                            tool_name in ["write_file", "read_file", "read_text_file", "edit_file"]
                            and "path" in tool_args
                        ):
                            original_path = tool_args["path"]

                            # Convert to absolute path within workspace
                            if not Path(original_path).is_absolute():
                                # Remove ./ prefix if present
                                if original_path.startswith("./"):
                                    original_path = original_path[2:]
                                # Join with workspace and resolve to absolute path
                                abs_path = (self.workspace / original_path).resolve()
                                tool_args["path"] = str(abs_path)
                                print(
                                    f"DEBUG: Fixed path: '{tool_args['path']}'  (was: '{original_path}')"
                                )

                        # Find and execute the tool
                        tool_result = None
                        for tool in tools:
                            if tool.name == tool_name:
                                tool_result = await tool.ainvoke(tool_args)
                                break

                        if tool_result is None:
                            tool_result = f"Error: Tool {tool_name} not found"
                            print(f"DEBUG: Tool not found: {tool_name}")
                            print(f"DEBUG: Available tools: {[t.name for t in tools]}")

                        print(f"DEBUG: Tool result: {str(tool_result)[:200]}")
                        tool_results.append(f"{tool_name}: {tool_result}")

                    except Exception as e:
                        print(f"DEBUG: Tool execution error: {e}")
                        import traceback

                        traceback.print_exc()
                        tool_results.append(f"Error: {e}")

                # Add tool results as a human message
                if tool_results:
                    results_msg = "Tool execution results:\n" + "\n".join(tool_results)
                    lc_messages.append(HumanMessage(content=results_msg))
                    print(f"DEBUG: Added {len(tool_results)} tool results to conversation")

        # Convert final response back to dict format
        final_response = lc_messages[-1]
        if hasattr(final_response, "content"):
            messages.append({"role": "assistant", "content": final_response.content})

        state["messages"] = messages
        return state

    async def process_request(self, request: str) -> dict[str, Any]:
        """
        Process user request

        Args:
            request: User request string

        Returns:
            Processing result
        """
        if not self.initialized:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        logger.info(f"Processing request: {request[:100]}...")

        # Create state
        state = {
            "messages": [{"role": "user", "content": request}],
            "session_id": self.session_manager.current_session_id,
        }

        # Process through agent
        if self.agent is None:
            raise RuntimeError("Agent not initialized properly")
        result = await self.agent.ainvoke(state)

        # Store in session
        self.session_manager.store_session_data(
            "last_request", {"request": request, "response": result}
        )

        return result

    def get_workspace_path(self) -> Path:
        """Get workspace path"""
        return self.workspace

    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self.mcp_client:
            await self.mcp_client.close()

        self.session_manager.close_session()
        logger.info("Agent cleanup complete")
