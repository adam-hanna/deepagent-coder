# tests/mcp_servers/test_container_tools_server.py
"""Tests for container tools MCP server"""

from unittest.mock import patch

import pytest

from deepagent_coder.mcp_servers.container_tools_server import (
    docker_command,
    docker_compose_command,
    kubectl_command,
    read_yaml_file,
    terraform_command,
    write_yaml_file,
)


@pytest.mark.asyncio
async def test_docker_command_success():
    """Test successful docker command execution"""
    with patch('deepagent_coder.mcp_servers.container_tools_server.run_command') as mock_run:
        mock_run.return_value = {
            "stdout": "docker ps output",
            "stderr": "",
            "returncode": 0
        }

        result = await docker_command("ps")

        assert result["success"] is True
        assert "docker ps output" in result["output"]
        mock_run.assert_called_once_with("docker ps", cwd=None, timeout=300, env=None)


@pytest.mark.asyncio
async def test_docker_command_with_cwd():
    """Test docker command with custom working directory"""
    with patch('deepagent_coder.mcp_servers.container_tools_server.run_command') as mock_run:
        mock_run.return_value = {
            "stdout": "build output",
            "stderr": "",
            "returncode": 0
        }

        result = await docker_command("build -t myimage .", cwd="/app")

        assert result["success"] is True
        mock_run.assert_called_once_with("docker build -t myimage .", cwd="/app", timeout=300, env=None)


@pytest.mark.asyncio
async def test_docker_command_failure():
    """Test docker command failure"""
    with patch('deepagent_coder.mcp_servers.container_tools_server.run_command') as mock_run:
        mock_run.return_value = {
            "stdout": "",
            "stderr": "Error: No such container",
            "returncode": 1
        }

        result = await docker_command("stop nonexistent")

        assert result["success"] is False
        assert "Error: No such container" in result["error"]


@pytest.mark.asyncio
async def test_docker_compose_command_up():
    """Test docker-compose up command"""
    with patch('deepagent_coder.mcp_servers.container_tools_server.run_command') as mock_run:
        mock_run.return_value = {
            "stdout": "Creating network... Creating container...",
            "stderr": "",
            "returncode": 0
        }

        result = await docker_compose_command("up -d", cwd="/project")

        assert result["success"] is True
        assert "Creating" in result["output"]
        mock_run.assert_called_once_with("docker-compose up -d", cwd="/project", timeout=600, env=None)


@pytest.mark.asyncio
async def test_kubectl_command_get_pods():
    """Test kubectl get pods command"""
    with patch('deepagent_coder.mcp_servers.container_tools_server.run_command') as mock_run:
        mock_run.return_value = {
            "stdout": "NAME                     READY   STATUS",
            "stderr": "",
            "returncode": 0
        }

        result = await kubectl_command("get pods")

        assert result["success"] is True
        assert "NAME" in result["output"]


@pytest.mark.asyncio
async def test_terraform_command_init():
    """Test terraform init command"""
    with patch('deepagent_coder.mcp_servers.container_tools_server.run_command') as mock_run:
        mock_run.return_value = {
            "stdout": "Initializing provider plugins...",
            "stderr": "",
            "returncode": 0
        }

        result = await terraform_command("init", cwd="/terraform")

        assert result["success"] is True
        assert "Initializing" in result["output"]


@pytest.mark.asyncio
async def test_read_yaml_file_success(tmp_path):
    """Test reading valid YAML file"""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text("""
version: "3.8"
services:
  web:
    image: nginx
    ports:
      - "80:80"
""")

    result = await read_yaml_file(str(yaml_file))

    assert result["success"] is True
    assert result["data"]["version"] == "3.8"
    assert "web" in result["data"]["services"]


@pytest.mark.asyncio
async def test_read_yaml_file_not_found():
    """Test reading non-existent YAML file"""
    result = await read_yaml_file("/nonexistent/file.yaml")

    assert result["success"] is False
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_write_yaml_file_success(tmp_path):
    """Test writing YAML file"""
    yaml_file = tmp_path / "output.yaml"

    data = {
        "version": "3.8",
        "services": {
            "app": {
                "image": "python:3.11",
                "ports": ["5000:5000"]
            }
        }
    }

    result = await write_yaml_file(str(yaml_file), data)

    assert result["success"] is True
    assert yaml_file.exists()

    # Verify written content
    content = yaml_file.read_text()
    assert "version" in content
    assert "python:3.11" in content


@pytest.mark.asyncio
async def test_write_yaml_file_invalid_data(tmp_path):
    """Test writing invalid YAML data"""
    yaml_file = tmp_path / "output.yaml"

    # Objects are not JSON serializable
    data = {"key": object()}

    result = await write_yaml_file(str(yaml_file), data)

    assert result["success"] is False
    assert "error" in result
