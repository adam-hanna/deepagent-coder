# tests/test_project_config.py
import tomli
from pathlib import Path

def test_pyproject_has_required_metadata():
    """Verify pyproject.toml contains all required fields"""
    with open("pyproject.toml", "rb") as f:
        config = tomli.load(f)

    assert config["project"]["name"] == "deepagent-claude"
    assert config["project"]["version"]
    assert config["project"]["requires-python"]  # Just verify it exists and is not empty
    assert len(config["project"]["dependencies"]) > 0

def test_all_required_dependencies_present():
    """Verify all required dependencies are declared"""
    with open("pyproject.toml", "rb") as f:
        config = tomli.load(f)

    required = {
        "deepagents", "langchain", "langchain-ollama",
        "langchain-mcp-adapters", "rich", "click", "fastmcp"
    }
    deps = {dep.split("[")[0].split(">=")[0].split("==")[0]
            for dep in config["project"]["dependencies"]}

    assert required.issubset(deps)
