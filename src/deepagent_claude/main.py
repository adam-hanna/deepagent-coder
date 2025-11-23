"""Main entry point for DeepAgent coding assistant"""

import asyncio
import click
from pathlib import Path
from typing import Optional

from deepagent_claude.coding_agent import CodingDeepAgent
from deepagent_claude.cli.console import DeepAgentConsole
from deepagent_claude.cli.chat_mode import ChatMode


console = DeepAgentConsole()


async def create_app(model: str = "qwen2.5-coder:latest", workspace: Optional[str] = None) -> CodingDeepAgent:
    """
    Create and initialize the coding agent

    Args:
        model: Ollama model name
        workspace: Workspace directory

    Returns:
        Initialized CodingDeepAgent
    """
    console.print_message("Initializing DeepAgent Coding Assistant...", style="cyan")

    agent = CodingDeepAgent(model=model, workspace=workspace)

    with console.status("Loading models and tools..."):
        await agent.initialize()

    console.print_success("System initialized!")
    console.print_message(f"Workspace: {agent.get_workspace_path()}", style="dim")

    return agent


async def run_single_request(request: str, model: str = "qwen2.5-coder:latest", workspace: Optional[str] = None) -> dict:
    """
    Run a single request and return result

    Args:
        request: User request
        model: Model name
        workspace: Workspace directory

    Returns:
        Processing result
    """
    agent = await create_app(model=model, workspace=workspace)

    try:
        result = await agent.process_request(request)
        return result
    finally:
        await agent.cleanup()


async def run_interactive_chat(model: str = "qwen2.5-coder:latest", workspace: Optional[str] = None):
    """
    Run interactive chat mode

    Args:
        model: Model name
        workspace: Workspace directory
    """
    agent = await create_app(model=model, workspace=workspace)
    chat = ChatMode(agent=agent)

    console.rule("DeepAgent Coding Assistant")
    console.print_message("Type your question or /help for commands", style="dim")
    console.rule()

    try:
        while not chat.should_exit():
            try:
                # Get user input
                user_input = input("\n> ")

                if not user_input.strip():
                    continue

                # Process input
                with console.status("Thinking..."):
                    result = await chat.process_input(user_input)

                # Display result
                if result:
                    if "error" in result:
                        console.print_error(result["error"])
                    elif "help" in result:
                        console.print_message(result["help"])
                    elif "messages" in result:
                        messages = result["messages"]
                        if messages:
                            last_msg = messages[-1]
                            if last_msg.get("role") == "assistant":
                                console.print_markdown(last_msg.get("content", ""))

            except KeyboardInterrupt:
                console.print_warning("\nUse /exit to quit")
                continue
            except EOFError:
                break

    finally:
        await agent.cleanup()
        console.print_message("Goodbye!", style="cyan")


@click.group()
def cli():
    """DeepAgent Coding Assistant - AI-powered coding help"""
    pass


@cli.command()
@click.argument('request')
@click.option('--model', default="qwen2.5-coder:latest", help="Ollama model to use")
@click.option('--workspace', default=None, help="Workspace directory")
def run(request: str, model: str, workspace: Optional[str]):
    """Execute a single request"""
    result = asyncio.run(run_single_request(request, model=model, workspace=workspace))

    # Display result
    if "messages" in result:
        messages = result["messages"]
        if messages:
            last_msg = messages[-1]
            if last_msg.get("role") == "assistant":
                console.print_markdown(last_msg.get("content", ""))


@cli.command()
@click.option('--model', default="qwen2.5-coder:latest", help="Ollama model to use")
@click.option('--workspace', default=None, help="Workspace directory")
def chat(model: str, workspace: Optional[str]):
    """Start interactive chat mode"""
    asyncio.run(run_interactive_chat(model=model, workspace=workspace))


@cli.command()
def version():
    """Show version information"""
    console.print_message("DeepAgent Coding Assistant v0.1.0", style="bold cyan")


if __name__ == "__main__":
    cli()
