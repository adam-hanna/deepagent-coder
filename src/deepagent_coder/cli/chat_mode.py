"""Interactive chat mode for DeepAgent"""

import logging
from typing import Any

from deepagent_coder.cli.commands import CommandHandler
from deepagent_coder.cli.console import DeepAgentConsole

logger = logging.getLogger(__name__)


class ChatMode:
    """
    Interactive REPL chat mode for agent interaction

    Provides command-line interface with command handling and
    conversation management.
    """

    def __init__(self, agent: Any | None = None):
        """
        Initialize chat mode

        Args:
            agent: Optional agent instance for processing requests
        """
        self.agent = agent
        self.console = DeepAgentConsole()
        self.command_handler = CommandHandler(agent=agent)
        self._exit = False
        self.conversation_history: list[dict[str, str]] = []

    async def process_input(self, user_input: str) -> dict[str, Any] | None:
        """
        Process user input (command or message)

        Args:
            user_input: User input string

        Returns:
            Processing result or None
        """
        # Check if it's a command
        if user_input.startswith("/"):
            return await self._process_command(user_input)
        else:
            return await self._process_message(user_input)

    async def _process_command(self, command: str) -> dict[str, Any] | None:
        """
        Process a command

        Args:
            command: Command string

        Returns:
            Command result
        """
        result = await self.command_handler.execute(command)

        # Handle special commands
        if command in ["/exit", "/quit"]:
            self._exit = True

        return result

    async def _process_message(self, message: str) -> dict[str, Any] | None:
        """
        Process a regular message

        Args:
            message: User message

        Returns:
            Agent response
        """
        if not self.agent:
            self.console.print_warning("No agent configured")
            return None

        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": message})

        try:
            # Invoke agent using process_request
            result = await self.agent.process_request(message)

            # Extract response
            if "messages" in result:
                messages = result["messages"]
                if messages:
                    last_message = messages[-1]
                    self.conversation_history.append(last_message)

            return result

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.console.print_error(f"Error: {e}")
            return None

    def should_exit(self) -> bool:
        """
        Check if chat should exit

        Returns:
            True if exit requested
        """
        return self._exit

    def reset(self) -> None:
        """Reset conversation history"""
        self.conversation_history = []
        self._exit = False
