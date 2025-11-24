"""Main CodingDeepAgent orchestration class"""

import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from langchain_ollama import ChatOllama

from deepagent_claude.core.model_selector import ModelSelector
from deepagent_claude.core.mcp_client import MCPClientManager
from deepagent_claude.utils.file_organizer import FileOrganizer
from deepagent_claude.utils.session_manager import SessionManager
from deepagent_claude.middleware.memory_middleware import create_memory_middleware
from deepagent_claude.middleware.git_safety_middleware import create_git_safety_middleware
from deepagent_claude.middleware.logging_middleware import create_logging_middleware
from deepagent_claude.middleware.error_recovery_middleware import create_error_recovery_middleware
from deepagent_claude.middleware.audit_middleware import create_audit_middleware

logger = logging.getLogger(__name__)


class CodingDeepAgent:
    """
    Production-ready coding assistant using DeepAgent architecture

    Integrates all components: models, MCP tools, subagents, middleware,
    and file organization for a complete AI coding assistant.
    """

    def __init__(self, model: str = "qwen2.5-coder:7b", workspace: Optional[str] = None):
        """
        Initialize coding agent

        Args:
            model: Ollama model name
            workspace: Workspace directory path
        """
        self.model_name = model
        self.workspace = Path(workspace) if workspace else Path.home() / ".deepagents" / "workspace"
        self.workspace.mkdir(parents=True, exist_ok=True)

        # Core components
        self.model_selector = ModelSelector()
        self.mcp_client = None
        self.file_organizer = FileOrganizer(str(self.workspace))
        self.session_manager = SessionManager(str(self.workspace / "sessions"))

        # Agent and subagents
        self.agent = None
        self.subagents: Dict[str, Any] = {}

        # Middleware
        self.middleware = []

        # State
        self.initialized = False

        logger.info(f"CodingDeepAgent created with model {model}")

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
        # Use standard MCP servers that work reliably
        custom_config = {
            "filesystem": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", str(self.workspace)]
            }
        }

        self.mcp_client = MCPClientManager(custom_configs=custom_config)
        await self.mcp_client.initialize()
        logger.info("MCP tools initialized")

    async def _create_subagents(self) -> None:
        """Create specialized subagents"""
        # Placeholder - would create actual DeepAgent subagents
        self.subagents = {
            "code_generator": None,
            "debugger": None,
            "test_writer": None,
            "refactorer": None
        }
        logger.info("Subagents created")

    def _setup_middleware(self) -> None:
        """Setup middleware stack"""
        self.middleware = [
            create_logging_middleware(
                log_file=str(self.workspace / "agent.log")
            ),
            create_memory_middleware(
                self.model_selector,
                threshold=6000
            ),
            create_git_safety_middleware(enforce=False),
            create_error_recovery_middleware(max_retries=3),
            create_audit_middleware(
                audit_file=str(self.workspace / "audit.jsonl")
            ),
        ]
        logger.info(f"Middleware stack configured with {len(self.middleware)} components")

    def _create_main_agent(self) -> None:
        """Create main agent with all components"""
        # Get the main agent model
        self.main_model = self.model_selector.get_model("main_agent")

        # Store tools reference (will be populated after MCP init)
        self.tools = []

        # Create agent structure
        self.agent = type('Agent', (), {
            'ainvoke': self._agent_invoke
        })()
        logger.info("Main agent created with model")

    async def _get_tools(self):
        """Get tools from MCP client"""
        if not self.tools and self.mcp_client:
            try:
                self.tools = await self.mcp_client.get_all_tools()
                logger.info(f"Retrieved {len(self.tools)} MCP tools")
            except Exception as e:
                logger.warning(f"Failed to get MCP tools: {e}")
                self.tools = []
        return self.tools

    async def _agent_invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Agent invocation with LLM and tool calling"""
        # Apply middleware
        for middleware in self.middleware:
            state = await middleware(state)

        # Get messages
        messages = state.get("messages", [])

        # Convert to LangChain format
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

        # Add system prompt
        system_prompt = """You are a coding assistant with access to filesystem and command-line tools.

When creating code:
1. ALWAYS use the write_file or create_file tool to save code to disk
2. Create all necessary files (package.json, source files, README, etc.)
3. Use proper file paths relative to the workspace
4. After creating files, you can run commands using bash/shell tools

Available tools allow you to:
- Create, read, update, and delete files
- Run shell commands (npm install, npm test, git, etc.)
- List directory contents

Be proactive - create the files the user requests!"""

        lc_messages = [SystemMessage(content=system_prompt)]

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
        if tools:
            model_with_tools = self.main_model.bind_tools(tools)
            logger.info(f"Bound {len(tools)} tools to model")
        else:
            model_with_tools = self.main_model
            logger.warning("No tools available, using model without tools")

        # Agent loop - handle tool calling
        max_iterations = 10
        for iteration in range(max_iterations):
            logger.info(f"Agent iteration {iteration + 1}/{max_iterations}")

            # Call LLM
            response = await model_with_tools.ainvoke(lc_messages)
            lc_messages.append(response)

            # Check if there are tool calls
            if not response.tool_calls:
                # No more tool calls, we're done
                logger.info("No tool calls, agent finished")
                break

            # Execute tool calls
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id")

                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

                try:
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
                    lc_messages.append(ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_id
                    ))

                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    lc_messages.append(ToolMessage(
                        content=f"Error executing tool: {str(e)}",
                        tool_call_id=tool_id
                    ))

        # Convert final response back to dict format
        final_response = lc_messages[-1]
        if hasattr(final_response, 'content'):
            messages.append({
                "role": "assistant",
                "content": final_response.content
            })

        state["messages"] = messages
        return state

    async def process_request(self, request: str) -> Dict[str, Any]:
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
            "messages": [
                {"role": "user", "content": request}
            ],
            "session_id": self.session_manager.current_session_id
        }

        # Process through agent
        result = await self.agent.ainvoke(state)

        # Store in session
        self.session_manager.store_session_data("last_request", {
            "request": request,
            "response": result
        })

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
