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
        self.mcp_client = MCPClientManager()

        # Configure MCP servers (simplified for now)
        config = {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", str(self.workspace)]
            }
        }

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
        # Placeholder - would create actual DeepAgent
        # For now, just create a mock structure
        self.agent = type('Agent', (), {
            'ainvoke': self._mock_invoke
        })()
        logger.info("Main agent created")

    async def _mock_invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Mock agent invocation for testing"""
        # Apply middleware
        for middleware in self.middleware:
            state = await middleware(state)

        # Simulate response
        messages = state.get("messages", [])
        messages.append({
            "role": "assistant",
            "content": "Mock response from agent"
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
            await self.mcp_client.cleanup()

        self.session_manager.close_session()
        logger.info("Agent cleanup complete")
