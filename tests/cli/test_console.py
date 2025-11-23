# tests/cli/test_console.py
import pytest
from deepagent_claude.cli.console import DeepAgentConsole
from io import StringIO

def test_console_creation():
    """Test creating console instance"""
    console = DeepAgentConsole()
    assert console is not None

def test_console_print_message():
    """Test printing message to console"""
    console = DeepAgentConsole()
    # Should not raise exception
    console.print_message("Test message", style="cyan")

def test_console_print_error():
    """Test printing error message"""
    console = DeepAgentConsole()
    console.print_error("Error message")

def test_console_print_success():
    """Test printing success message"""
    console = DeepAgentConsole()
    console.print_success("Success message")

def test_console_print_warning():
    """Test printing warning message"""
    console = DeepAgentConsole()
    console.print_warning("Warning message")

def test_console_print_code():
    """Test printing code block"""
    console = DeepAgentConsole()
    code = "def hello():\n    print('Hello')"
    console.print_code(code, language="python")

def test_console_status_context():
    """Test status context manager"""
    console = DeepAgentConsole()
    with console.status("Processing..."):
        pass  # Should complete without error
