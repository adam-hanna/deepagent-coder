# tests/mcp_servers/test_git_server.py
import pytest
from pathlib import Path
import subprocess
from deepagent_claude.mcp_servers.git_server import (
    _git_status_impl as git_status,
    _git_diff_impl as git_diff,
    _git_log_impl as git_log,
    _git_commit_impl as git_commit,
    _git_add_impl as git_add,
    _git_branch_impl as git_branch,
    _git_checkout_impl as git_checkout,
    _git_create_branch_impl as git_create_branch
)

@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository"""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    # Initialize repo
    subprocess.run(["git", "init"], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir, check=True
    )

    # Create initial commit
    (repo_dir / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_dir, check=True
    )

    return str(repo_dir)

@pytest.mark.asyncio
async def test_git_status_shows_clean_repo(git_repo):
    """Test git status on clean repo"""
    result = await git_status(git_repo)

    assert "error" not in result
    assert result["branch"]
    assert result["clean"] is True
    assert len(result["untracked"]) == 0

@pytest.mark.asyncio
async def test_git_status_shows_untracked_files(git_repo):
    """Test git status detects untracked files"""
    # Add untracked file
    (Path(git_repo) / "new_file.txt").write_text("content")

    result = await git_status(git_repo)

    assert "error" not in result
    assert result["clean"] is False
    assert "new_file.txt" in result["untracked"]

@pytest.mark.asyncio
async def test_git_add_stages_files(git_repo):
    """Test staging files"""
    # Create file
    (Path(git_repo) / "test.txt").write_text("test")

    result = await git_add(git_repo, ["test.txt"])

    assert "error" not in result
    assert result["success"] is True
    assert "test.txt" in result["staged"]

@pytest.mark.asyncio
async def test_git_commit_creates_commit(git_repo):
    """Test creating commit"""
    # Stage a file
    (Path(git_repo) / "test.txt").write_text("test")
    await git_add(git_repo, ["test.txt"])

    result = await git_commit(git_repo, "Test commit")

    assert "error" not in result
    assert result["success"] is True
    assert result["commit_hash"]

@pytest.mark.asyncio
async def test_git_diff_shows_changes(git_repo):
    """Test viewing unstaged changes"""
    # Modify existing file
    (Path(git_repo) / "README.md").write_text("# Modified")

    result = await git_diff(git_repo)

    assert "error" not in result
    assert result["has_changes"] is True
    assert "Modified" in result["diff"]

@pytest.mark.asyncio
async def test_git_log_returns_commits(git_repo):
    """Test viewing commit history"""
    result = await git_log(git_repo)

    assert "error" not in result
    assert len(result["commits"]) >= 1
    assert result["commits"][0]["subject"] == "Initial commit"

@pytest.mark.asyncio
async def test_git_branch_lists_branches(git_repo):
    """Test listing branches"""
    result = await git_branch(git_repo)

    assert "error" not in result
    assert len(result["branches"]) >= 1
    assert result["current"]

@pytest.mark.asyncio
async def test_git_create_branch_makes_new_branch(git_repo):
    """Test creating new branch"""
    result = await git_create_branch(git_repo, "feature-test", checkout=False)

    assert "error" not in result
    assert result["success"] is True
    assert result["branch"] == "feature-test"

@pytest.mark.asyncio
async def test_git_checkout_switches_branches(git_repo):
    """Test switching branches"""
    # Create and checkout new branch first
    await git_create_branch(git_repo, "test-branch", checkout=False)

    result = await git_checkout(git_repo, "test-branch")

    assert "error" not in result
    assert result["success"] is True
    assert result["branch"] == "test-branch"
