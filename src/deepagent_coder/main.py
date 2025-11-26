"""Main entry point for DeepAgent coding assistant"""

import asyncio
from pathlib import Path

import click

from deepagent_coder.cli.chat_mode import ChatMode
from deepagent_coder.cli.console import DeepAgentConsole
from deepagent_coder.coding_agent import CodingDeepAgent
from deepagent_coder.core.config import Config

console = DeepAgentConsole()


async def create_app(
    model: str | None = None,
    workspace: str | None = None,
    config_file: str | None = None,
) -> CodingDeepAgent:
    """
    Create and initialize the coding agent

    Args:
        model: Ollama model name (overrides config)
        workspace: Workspace directory (overrides config)
        config_file: Path to config file

    Returns:
        Initialized CodingDeepAgent
    """
    console.print_message("Initializing DeepAgent Coding Assistant...", style="cyan")

    # Load configuration
    cli_overrides = {}
    if model:
        cli_overrides["agent"] = {"model": model}
    if workspace:
        cli_overrides["workspace"] = {"path": workspace}

    config = Config(
        config_file=Path(config_file) if config_file else None, cli_overrides=cli_overrides
    )

    if config_file:
        console.print_message(f"Using config file: {config_file}", style="dim")

    agent = CodingDeepAgent(model=model, workspace=workspace, config=config)

    with console.status("Loading models and tools..."):
        await agent.initialize()

    console.print_success("System initialized!")
    console.print_message(f"Workspace: {agent.get_workspace_path()}", style="dim")

    return agent


async def run_single_request(
    request: str,
    model: str | None = None,
    workspace: str | None = None,
    config_file: str | None = None,
) -> dict:
    """
    Run a single request and return result

    Args:
        request: User request
        model: Model name (overrides config)
        workspace: Workspace directory (overrides config)
        config_file: Path to config file

    Returns:
        Processing result
    """
    agent = await create_app(model=model, workspace=workspace, config_file=config_file)

    try:
        result = await agent.process_request(request)
        return result
    finally:
        await agent.cleanup()


async def run_interactive_chat(
    model: str | None = None,
    workspace: str | None = None,
    config_file: str | None = None,
):
    """
    Run interactive chat mode

    Args:
        model: Model name (overrides config)
        workspace: Workspace directory (overrides config)
        config_file: Path to config file
    """
    agent = await create_app(model=model, workspace=workspace, config_file=config_file)
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
@click.argument("request")
@click.option("--model", default=None, help="Ollama model to use (overrides config)")
@click.option("--workspace", default=None, help="Workspace directory (overrides config)")
@click.option("--config", "config_file", default=None, help="Path to config file")
def run(request: str, model: str | None, workspace: str | None, config_file: str | None):
    """Execute a single request"""
    result = asyncio.run(
        run_single_request(request, model=model, workspace=workspace, config_file=config_file)
    )

    # Display result
    if "messages" in result:
        messages = result["messages"]
        if messages:
            last_msg = messages[-1]
            if last_msg.get("role") == "assistant":
                console.print_markdown(last_msg.get("content", ""))


@cli.command()
@click.option("--model", default=None, help="Ollama model to use (overrides config)")
@click.option("--workspace", default=None, help="Workspace directory (overrides config)")
@click.option("--config", "config_file", default=None, help="Path to config file")
def chat(model: str | None, workspace: str | None, config_file: str | None):
    """Start interactive chat mode"""
    asyncio.run(run_interactive_chat(model=model, workspace=workspace, config_file=config_file))


@cli.command()
def version():
    """Show version information"""
    console.print_message("DeepAgent Coding Assistant v0.1.0", style="bold cyan")


if __name__ == "__main__":
    cli()
