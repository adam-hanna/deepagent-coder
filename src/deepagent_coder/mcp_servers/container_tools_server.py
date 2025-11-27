"""Container tools MCP server - Docker, Kubernetes, Terraform, and YAML operations"""

from pathlib import Path
from typing import Any

from fastmcp import FastMCP
import yaml

from .shell_server import run_command

mcp = FastMCP("Container Tools")


async def docker_command(
    command: str,
    cwd: str | None = None,
    timeout: int = 300,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Execute a Docker command

    Args:
        command: Docker command to execute (e.g., "ps", "build -t myimage .")
        cwd: Working directory for command execution (optional)
        timeout: Maximum execution time in seconds (default: 300)
        env: Additional environment variables (optional)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if command succeeded
        - output: Command output (stdout)
        - error: Error message (stderr) if command failed
        - command: The full command that was executed
    """
    full_command = f"docker {command}"

    result = await run_command(full_command, cwd=cwd, timeout=timeout, env=env)

    # Format response based on success/failure
    if result["returncode"] == 0:
        return {
            "success": True,
            "output": result["stdout"],
            "command": full_command,
        }
    else:
        return {
            "success": False,
            "error": result.get("stderr") or result.get("error", "Unknown error"),
            "command": full_command,
        }


async def docker_compose_command(
    command: str,
    cwd: str | None = None,
    timeout: int = 600,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Execute a Docker Compose command

    Args:
        command: Docker Compose command (e.g., "up -d", "down", "logs")
        cwd: Working directory containing docker-compose.yml (optional)
        timeout: Maximum execution time in seconds (default: 600)
        env: Additional environment variables (optional)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if command succeeded
        - output: Command output
        - error: Error message if command failed
        - command: The full command that was executed
    """
    full_command = f"docker-compose {command}"

    result = await run_command(full_command, cwd=cwd, timeout=timeout, env=env)

    if result["returncode"] == 0:
        return {
            "success": True,
            "output": result["stdout"],
            "command": full_command,
        }
    else:
        return {
            "success": False,
            "error": result.get("stderr") or result.get("error", "Unknown error"),
            "command": full_command,
        }


async def kubectl_command(
    command: str,
    cwd: str | None = None,
    timeout: int = 300,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Execute a kubectl command for Kubernetes operations

    Args:
        command: kubectl command (e.g., "get pods", "apply -f deployment.yaml")
        cwd: Working directory for command execution (optional)
        timeout: Maximum execution time in seconds (default: 300)
        env: Additional environment variables (optional)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if command succeeded
        - output: Command output
        - error: Error message if command failed
        - command: The full command that was executed
    """
    full_command = f"kubectl {command}"

    result = await run_command(full_command, cwd=cwd, timeout=timeout, env=env)

    if result["returncode"] == 0:
        return {
            "success": True,
            "output": result["stdout"],
            "command": full_command,
        }
    else:
        return {
            "success": False,
            "error": result.get("stderr") or result.get("error", "Unknown error"),
            "command": full_command,
        }


async def terraform_command(
    command: str,
    cwd: str | None = None,
    timeout: int = 600,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Execute a Terraform command for infrastructure as code

    Args:
        command: Terraform command (e.g., "init", "plan", "apply")
        cwd: Working directory containing Terraform files (optional)
        timeout: Maximum execution time in seconds (default: 600)
        env: Additional environment variables (optional)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if command succeeded
        - output: Command output
        - error: Error message if command failed
        - command: The full command that was executed
    """
    full_command = f"terraform {command}"

    result = await run_command(full_command, cwd=cwd, timeout=timeout, env=env)

    if result["returncode"] == 0:
        return {
            "success": True,
            "output": result["stdout"],
            "command": full_command,
        }
    else:
        return {
            "success": False,
            "error": result.get("stderr") or result.get("error", "Unknown error"),
            "command": full_command,
        }


async def read_yaml_file(file_path: str) -> dict[str, Any]:
    """
    Read and parse a YAML file

    Args:
        file_path: Path to the YAML file to read

    Returns:
        Dictionary containing:
        - success: Boolean indicating if file was read successfully
        - data: Parsed YAML content as a Python dictionary/list
        - error: Error message if reading/parsing failed
        - file: The file path that was read
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file": file_path,
            }

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return {
            "success": True,
            "data": data,
            "file": file_path,
        }

    except yaml.YAMLError as e:
        return {
            "success": False,
            "error": f"YAML parsing error: {str(e)}",
            "file": file_path,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file": file_path,
        }


async def write_yaml_file(file_path: str, data: dict[str, Any]) -> dict[str, Any]:
    """
    Write data to a YAML file

    Args:
        file_path: Path where the YAML file should be written
        data: Python dictionary/list to serialize as YAML

    Returns:
        Dictionary containing:
        - success: Boolean indicating if file was written successfully
        - file: The file path that was written
        - error: Error message if writing failed
    """
    try:
        path = Path(file_path)

        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

        return {
            "success": True,
            "file": file_path,
        }

    except (TypeError, yaml.representer.RepresenterError) as e:
        return {
            "success": False,
            "error": f"Data serialization error: {str(e)}",
            "file": file_path,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file": file_path,
        }


# MCP Tool wrappers
@mcp.tool()
async def run_docker_command(
    command: str,
    cwd: str | None = None,
    timeout: int = 300,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Execute a Docker command

    Use this tool to run Docker commands for container management:
    - Container operations: docker ps, docker run, docker stop
    - Image operations: docker build, docker pull, docker push
    - Network operations: docker network create, docker network ls
    - Volume operations: docker volume create, docker volume ls

    Args:
        command: Docker command to execute (e.g., "ps", "build -t myimage .")
        cwd: Working directory for command execution (optional)
        timeout: Maximum execution time in seconds (default: 300)
        env: Additional environment variables (optional)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if command succeeded
        - output: Command output (stdout)
        - error: Error message (stderr) if command failed
        - command: The full command that was executed
    """
    return await docker_command(command, cwd, timeout, env)


@mcp.tool()
async def run_docker_compose_command(
    command: str,
    cwd: str | None = None,
    timeout: int = 600,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Execute a Docker Compose command

    Use this tool to manage multi-container Docker applications:
    - Start services: docker-compose up -d
    - Stop services: docker-compose down
    - View logs: docker-compose logs
    - Scale services: docker-compose scale web=3

    Args:
        command: Docker Compose command (e.g., "up -d", "down", "logs")
        cwd: Working directory containing docker-compose.yml (optional)
        timeout: Maximum execution time in seconds (default: 600)
        env: Additional environment variables (optional)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if command succeeded
        - output: Command output
        - error: Error message if command failed
        - command: The full command that was executed
    """
    return await docker_compose_command(command, cwd, timeout, env)


@mcp.tool()
async def run_kubectl_command(
    command: str,
    cwd: str | None = None,
    timeout: int = 300,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Execute a kubectl command for Kubernetes operations

    Use this tool to interact with Kubernetes clusters:
    - Get resources: kubectl get pods, kubectl get services
    - Apply configurations: kubectl apply -f deployment.yaml
    - Describe resources: kubectl describe pod mypod
    - Delete resources: kubectl delete deployment myapp

    Args:
        command: kubectl command (e.g., "get pods", "apply -f deployment.yaml")
        cwd: Working directory for command execution (optional)
        timeout: Maximum execution time in seconds (default: 300)
        env: Additional environment variables (optional)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if command succeeded
        - output: Command output
        - error: Error message if command failed
        - command: The full command that was executed
    """
    return await kubectl_command(command, cwd, timeout, env)


@mcp.tool()
async def run_terraform_command(
    command: str,
    cwd: str | None = None,
    timeout: int = 600,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Execute a Terraform command for infrastructure as code

    Use this tool to manage infrastructure with Terraform:
    - Initialize: terraform init
    - Plan changes: terraform plan
    - Apply changes: terraform apply
    - Destroy resources: terraform destroy

    Args:
        command: Terraform command (e.g., "init", "plan", "apply")
        cwd: Working directory containing Terraform files (optional)
        timeout: Maximum execution time in seconds (default: 600)
        env: Additional environment variables (optional)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if command succeeded
        - output: Command output
        - error: Error message if command failed
        - command: The full command that was executed
    """
    return await terraform_command(command, cwd, timeout, env)


@mcp.tool()
async def read_yaml(file_path: str) -> dict[str, Any]:
    """
    Read and parse a YAML file

    Use this tool to read YAML configuration files:
    - Docker Compose files (docker-compose.yml)
    - Kubernetes manifests (deployment.yaml, service.yaml)
    - CI/CD configurations (.gitlab-ci.yml, .github/workflows/*.yml)
    - Application configurations

    Args:
        file_path: Path to the YAML file to read

    Returns:
        Dictionary containing:
        - success: Boolean indicating if file was read successfully
        - data: Parsed YAML content as a Python dictionary/list
        - error: Error message if reading/parsing failed
        - file: The file path that was read
    """
    return await read_yaml_file(file_path)


@mcp.tool()
async def write_yaml(file_path: str, data: dict[str, Any]) -> dict[str, Any]:
    """
    Write data to a YAML file

    Use this tool to create or update YAML configuration files:
    - Generate Docker Compose configurations
    - Create Kubernetes manifests
    - Write CI/CD pipeline definitions
    - Update application configuration files

    Args:
        file_path: Path where the YAML file should be written
        data: Python dictionary/list to serialize as YAML

    Returns:
        Dictionary containing:
        - success: Boolean indicating if file was written successfully
        - file: The file path that was written
        - error: Error message if writing failed
    """
    return await write_yaml_file(file_path, data)


if __name__ == "__main__":
    mcp.run(show_banner=False, log_level="ERROR")
