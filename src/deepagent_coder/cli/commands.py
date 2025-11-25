"""Command handlers for CLI"""

from collections.abc import Callable
import logging
from typing import Any

logger = logging.getLogger(__name__)


class CommandHandler:
    """
    Handles CLI commands like /help, /exit, /workspace, etc.

    Commands are prefixed with / and provide special functionality
    separate from agent processing.
    """

    def __init__(self):
        """Initialize command handler"""
        self.commands: dict[str, Callable] = {
            "/help": self._help,
            "/exit": self._exit,
            "/quit": self._exit,
            "/workspace": self._workspace,
            "/clear": self._clear,
            "/history": self._history,
        }

    async def execute(self, command: str) -> dict[str, Any]:
        """
        Execute a command

        Args:
            command: Command string (e.g., "/help")

        Returns:
            Command result dictionary
        """
        # Parse command and args
        parts = command.split()
        cmd = parts[0] if parts else ""
        args = parts[1:] if len(parts) > 1 else []

        # Get handler
        handler = self.commands.get(cmd)

        if handler:
            try:
                return await handler(args)
            except Exception as e:
                logger.error(f"Error executing command {cmd}: {e}")
                return {"success": False, "error": str(e)}
        else:
            return {
                "success": False,
                "error": f"Unknown command: {cmd}",
                "help": "Type /help for available commands",
            }

    async def _help(self, args: list) -> dict[str, Any]:
        """Show help information"""
        help_text = """
Available Commands:

/help       - Show this help message
/exit       - Exit the assistant
/quit       - Exit the assistant
/workspace  - Show current workspace path
/clear      - Clear conversation history
/history    - Show conversation history

Usage Tips:
- Type your question or request to interact with the agent
- Use commands for special operations
- Press Ctrl+C to exit
"""
        return {"success": True, "help": help_text}

    async def _exit(self, args: list) -> dict[str, Any]:
        """Exit command"""
        return {"success": True, "exit": True, "message": "Goodbye!"}

    async def _workspace(self, args: list) -> dict[str, Any]:
        """Show workspace path"""
        # This would get the actual workspace path from configuration
        return {"success": True, "workspace": "~/.deepagents/workspace"}

    async def _clear(self, args: list) -> dict[str, Any]:
        """Clear conversation history"""
        return {"success": True, "cleared": True, "message": "Conversation history cleared"}

    async def _history(self, args: list) -> dict[str, Any]:
        """Show conversation history"""
        return {"success": True, "history": []}
