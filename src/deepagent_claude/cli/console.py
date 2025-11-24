"""Rich-based console interface for DeepAgent"""

from contextlib import contextmanager

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax


class DeepAgentConsole:
    """
    Console interface using Rich for beautiful CLI output

    Provides formatted output methods for different message types
    and code highlighting.
    """

    def __init__(self, width: int | None = None):
        """
        Initialize console

        Args:
            width: Optional fixed width for console output
        """
        self.console = Console(width=width)

    def print_message(self, message: str, style: str = "white") -> None:
        """
        Print a styled message

        Args:
            message: Message to print
            style: Rich style (e.g., "info", "bold", "dim")
        """
        self.console.print(message, style=style)

    def print_error(self, message: str) -> None:
        """
        Print error message in red

        Args:
            message: Error message
        """
        self.console.print(f"❌ {message}", style="bold red")

    def print_success(self, message: str) -> None:
        """
        Print success message in green

        Args:
            message: Success message
        """
        self.console.print(f"✅ {message}", style="bold green")

    def print_warning(self, message: str) -> None:
        """
        Print warning message in yellow

        Args:
            message: Warning message
        """
        self.console.print(f"⚠️  {message}", style="bold yellow")

    def print_code(self, code: str, language: str = "python") -> None:
        """
        Print syntax-highlighted code

        Args:
            code: Code to display
            language: Programming language for syntax highlighting
        """
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)

    def print_markdown(self, markdown: str) -> None:
        """
        Print formatted markdown

        Args:
            markdown: Markdown text to render
        """
        md = Markdown(markdown)
        self.console.print(md)

    def print_panel(self, content: str, title: str | None = None) -> None:
        """
        Print content in a panel

        Args:
            content: Content to display
            title: Optional panel title
        """
        panel = Panel(content, title=title, expand=False)
        self.console.print(panel)

    @contextmanager
    def status(self, message: str):
        """
        Context manager for status spinner

        Args:
            message: Status message to display

        Yields:
            Status object
        """
        with self.console.status(message) as status:
            yield status

    def clear(self) -> None:
        """Clear the console"""
        self.console.clear()

    def rule(self, title: str | None = None) -> None:
        """
        Print a horizontal rule

        Args:
            title: Optional title for the rule
        """
        self.console.rule(title)
