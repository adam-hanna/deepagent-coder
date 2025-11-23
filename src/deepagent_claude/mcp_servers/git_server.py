# src/deepagent_claude/mcp_servers/git_server.py
"""Git operations MCP server - version control tools"""

from fastmcp import FastMCP
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

mcp = FastMCP("Git Tools")


async def _git_status_impl(repo_path: str) -> Dict[str, Any]:
    """
    Get git repository status

    Args:
        repo_path: Path to git repository

    Returns:
        Status information including branch, staged, unstaged, and untracked files
    """
    try:
        path = Path(repo_path)
        if not path.exists():
            return {"error": f"Repository not found: {repo_path}"}

        # Get current branch
        branch_result = await _run_git_command(
            ["git", "branch", "--show-current"],
            cwd=path
        )
        branch = branch_result["stdout"].strip() or "HEAD"

        # Get status
        status_result = await _run_git_command(
            ["git", "status", "--porcelain"],
            cwd=path
        )

        if status_result["returncode"] != 0:
            return {"error": status_result["stderr"]}

        staged = []
        unstaged = []
        untracked = []

        for line in status_result["stdout"].splitlines():
            if not line.strip():
                continue

            status_code = line[:2]
            file_path = line[3:].strip()

            if status_code[0] in ['M', 'A', 'D', 'R', 'C']:
                staged.append({"file": file_path, "status": status_code[0]})

            if status_code[1] in ['M', 'D']:
                unstaged.append({"file": file_path, "status": status_code[1]})

            if status_code == '??':
                untracked.append(file_path)

        return {
            "repo": repo_path,
            "branch": branch,
            "clean": len(staged) == 0 and len(unstaged) == 0 and len(untracked) == 0,
            "staged": staged,
            "unstaged": unstaged,
            "untracked": untracked,
        }

    except Exception as e:
        return {"error": f"Git status failed: {str(e)}"}


@mcp.tool()
async def git_status(repo_path: str) -> Dict[str, Any]:
    """MCP tool wrapper for git_status"""
    return await _git_status_impl(repo_path)


async def _git_add_impl(repo_path: str, files: List[str]) -> Dict[str, Any]:
    """
    Stage files for commit

    Args:
        repo_path: Path to git repository
        files: List of file paths to stage

    Returns:
        Success status and staged files
    """
    try:
        path = Path(repo_path)
        result = await _run_git_command(
            ["git", "add"] + files,
            cwd=path
        )

        if result["returncode"] != 0:
            return {"error": result["stderr"]}

        return {
            "success": True,
            "staged": files,
            "message": f"Staged {len(files)} file(s)"
        }

    except Exception as e:
        return {"error": f"Git add failed: {str(e)}"}


@mcp.tool()
async def git_add(repo_path: str, files: List[str]) -> Dict[str, Any]:
    """MCP tool wrapper for git_add"""
    return await _git_add_impl(repo_path, files)


async def _git_commit_impl(
    repo_path: str,
    message: str,
    allow_empty: bool = False
) -> Dict[str, Any]:
    """
    Create a git commit

    Args:
        repo_path: Path to git repository
        message: Commit message
        allow_empty: Allow empty commits

    Returns:
        Commit information including hash
    """
    try:
        path = Path(repo_path)

        cmd = ["git", "commit", "-m", message]
        if allow_empty:
            cmd.append("--allow-empty")

        result = await _run_git_command(cmd, cwd=path)

        if result["returncode"] != 0:
            # Check if it's because nothing to commit
            if "nothing to commit" in result["stdout"].lower():
                return {
                    "success": False,
                    "message": "Nothing to commit",
                    "output": result["stdout"]
                }
            return {"error": result["stderr"] or result["stdout"]}

        # Extract commit hash
        hash_result = await _run_git_command(
            ["git", "rev-parse", "HEAD"],
            cwd=path
        )
        commit_hash = hash_result["stdout"].strip()

        return {
            "success": True,
            "commit_hash": commit_hash,
            "message": message,
            "output": result["stdout"]
        }

    except Exception as e:
        return {"error": f"Git commit failed: {str(e)}"}


@mcp.tool()
async def git_commit(
    repo_path: str,
    message: str,
    allow_empty: bool = False
) -> Dict[str, Any]:
    """MCP tool wrapper for git_commit"""
    return await _git_commit_impl(repo_path, message, allow_empty)


async def _git_diff_impl(
    repo_path: str,
    staged: bool = False,
    file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get git diff

    Args:
        repo_path: Path to git repository
        staged: Show staged changes instead of unstaged
        file_path: Optional specific file to diff

    Returns:
        Diff output
    """
    try:
        path = Path(repo_path)

        cmd = ["git", "diff"]
        if staged:
            cmd.append("--staged")
        if file_path:
            cmd.append(file_path)

        result = await _run_git_command(cmd, cwd=path)

        if result["returncode"] != 0:
            return {"error": result["stderr"]}

        return {
            "diff": result["stdout"],
            "staged": staged,
            "file": file_path,
            "has_changes": bool(result["stdout"].strip())
        }

    except Exception as e:
        return {"error": f"Git diff failed: {str(e)}"}


@mcp.tool()
async def git_diff(
    repo_path: str,
    staged: bool = False,
    file_path: Optional[str] = None
) -> Dict[str, Any]:
    """MCP tool wrapper for git_diff"""
    return await _git_diff_impl(repo_path, staged, file_path)


async def _git_log_impl(
    repo_path: str,
    max_count: int = 10,
    format: str = "oneline"
) -> Dict[str, Any]:
    """
    Get git commit history

    Args:
        repo_path: Path to git repository
        max_count: Maximum number of commits to return
        format: Log format (oneline, short, full)

    Returns:
        List of commits
    """
    try:
        path = Path(repo_path)

        # Use custom format for parsing
        result = await _run_git_command(
            [
                "git", "log",
                f"-{max_count}",
                "--pretty=format:%H%n%an%n%ae%n%at%n%s%n%b%n---END---"
            ],
            cwd=path
        )

        if result["returncode"] != 0:
            return {"error": result["stderr"]}

        commits = []
        if result["stdout"].strip():
            commit_texts = result["stdout"].split("---END---\n")

            for commit_text in commit_texts:
                if not commit_text.strip():
                    continue

                lines = commit_text.strip().split("\n")
                if len(lines) >= 5:
                    commits.append({
                        "hash": lines[0],
                        "author": lines[1],
                        "email": lines[2],
                        "timestamp": int(lines[3]),
                        "subject": lines[4],
                        "body": "\n".join(lines[5:]).strip() if len(lines) > 5 else ""
                    })

        return {
            "commits": commits,
            "count": len(commits)
        }

    except Exception as e:
        return {"error": f"Git log failed: {str(e)}"}


@mcp.tool()
async def git_log(
    repo_path: str,
    max_count: int = 10,
    format: str = "oneline"
) -> Dict[str, Any]:
    """MCP tool wrapper for git_log"""
    return await _git_log_impl(repo_path, max_count, format)


async def _git_branch_impl(
    repo_path: str,
    list_all: bool = False
) -> Dict[str, Any]:
    """
    List git branches

    Args:
        repo_path: Path to git repository
        list_all: Include remote branches

    Returns:
        List of branches with current branch indicated
    """
    try:
        path = Path(repo_path)

        cmd = ["git", "branch"]
        if list_all:
            cmd.append("-a")

        result = await _run_git_command(cmd, cwd=path)

        if result["returncode"] != 0:
            return {"error": result["stderr"]}

        branches = []
        current_branch = None

        for line in result["stdout"].splitlines():
            line = line.strip()
            if line.startswith("* "):
                current_branch = line[2:]
                branches.append({"name": line[2:], "current": True})
            elif line:
                branches.append({"name": line, "current": False})

        return {
            "branches": branches,
            "current": current_branch,
            "count": len(branches)
        }

    except Exception as e:
        return {"error": f"Git branch failed: {str(e)}"}


@mcp.tool()
async def git_branch(
    repo_path: str,
    list_all: bool = False
) -> Dict[str, Any]:
    """MCP tool wrapper for git_branch"""
    return await _git_branch_impl(repo_path, list_all)


async def _git_create_branch_impl(
    repo_path: str,
    branch_name: str,
    checkout: bool = True
) -> Dict[str, Any]:
    """
    Create a new branch

    Args:
        repo_path: Path to git repository
        branch_name: Name for new branch
        checkout: Switch to new branch after creating

    Returns:
        Success status
    """
    try:
        path = Path(repo_path)

        # Create branch
        result = await _run_git_command(
            ["git", "branch", branch_name],
            cwd=path
        )

        if result["returncode"] != 0:
            return {"error": result["stderr"]}

        # Checkout if requested
        if checkout:
            checkout_result = await _run_git_command(
                ["git", "checkout", branch_name],
                cwd=path
            )

            if checkout_result["returncode"] != 0:
                return {"error": checkout_result["stderr"]}

        return {
            "success": True,
            "branch": branch_name,
            "checked_out": checkout
        }

    except Exception as e:
        return {"error": f"Git create branch failed: {str(e)}"}


@mcp.tool()
async def git_create_branch(
    repo_path: str,
    branch_name: str,
    checkout: bool = True
) -> Dict[str, Any]:
    """MCP tool wrapper for git_create_branch"""
    return await _git_create_branch_impl(repo_path, branch_name, checkout)


async def _git_checkout_impl(
    repo_path: str,
    branch_name: str
) -> Dict[str, Any]:
    """
    Switch to a different branch

    Args:
        repo_path: Path to git repository
        branch_name: Branch to switch to

    Returns:
        Success status
    """
    try:
        path = Path(repo_path)

        result = await _run_git_command(
            ["git", "checkout", branch_name],
            cwd=path
        )

        if result["returncode"] != 0:
            return {"error": result["stderr"]}

        return {
            "success": True,
            "branch": branch_name,
            "output": result["stdout"]
        }

    except Exception as e:
        return {"error": f"Git checkout failed: {str(e)}"}


@mcp.tool()
async def git_checkout(
    repo_path: str,
    branch_name: str
) -> Dict[str, Any]:
    """MCP tool wrapper for git_checkout"""
    return await _git_checkout_impl(repo_path, branch_name)


async def _run_git_command(
    cmd: List[str],
    cwd: Path,
    timeout: int = 30
) -> Dict[str, Any]:
    """Execute git command and return result"""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )

        return {
            "stdout": stdout.decode("utf-8"),
            "stderr": stderr.decode("utf-8"),
            "returncode": process.returncode
        }

    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "returncode": -1
        }


def run_server():
    """Run the Git MCP server"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
