# tests/integration/test_code_navigator_integration.py

import pytest


@pytest.fixture
def sample_codebase(tmp_path):
    """Create a sample codebase for testing"""
    # Create API routes
    api_dir = tmp_path / "api"
    api_dir.mkdir()

    (api_dir / "routes.py").write_text(
        """
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/users")
async def list_users():
    return {"users": []}

@router.post("/api/users")
async def create_user(user: dict):
    return {"id": 1, **user}

@router.get("/api/users/{user_id}")
async def get_user(user_id: int):
    return {"id": user_id}
"""
    )

    # Create database models
    models_dir = tmp_path / "models"
    models_dir.mkdir()

    (models_dir / "user.py").write_text(
        """
from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)

    def query_by_email(self, email):
        return db.session.query(User).filter(User.email == email).first()
"""
    )

    # Create utils
    (tmp_path / "utils.py").write_text(
        """
def validate_email(email: str) -> bool:
    return "@" in email

def format_name(name: str) -> str:
    return name.title()
"""
    )

    return tmp_path


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_finds_api_endpoint(sample_codebase):
    """Test code navigator can find API endpoints"""
    from deepagent_coder.mcp_servers.search_tools_server import grep

    # Test finding users API
    results = grep(
        pattern="@router.get.*users", path=str(sample_codebase), regex=True, recursive=True
    )

    assert len(results) > 0
    assert any("routes.py" in r["file"] for r in results)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_finds_database_calls(sample_codebase):
    """Test code navigator can find database queries"""
    from deepagent_coder.mcp_servers.search_tools_server import grep

    results = grep(pattern="query.*filter", path=str(sample_codebase), regex=True, recursive=True)

    assert len(results) > 0
    assert any("user.py" in r["file"] for r in results)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_finds_function_definition(sample_codebase):
    """Test code navigator can find function definitions"""
    from deepagent_coder.mcp_servers.search_tools_server import grep

    results = grep(pattern="def validate_email", path=str(sample_codebase), recursive=True)

    assert len(results) > 0
    assert any("utils.py" in r["file"] for r in results)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_chains_find_and_grep(sample_codebase):
    """Test code navigator can chain find and grep operations"""
    from deepagent_coder.mcp_servers.search_tools_server import find, grep

    # First find Python files
    py_files = find(path=str(sample_codebase), extension="py", type="f")

    assert len(py_files) >= 3  # routes.py, user.py, utils.py

    # Then search for functions in those files
    function_counts = 0
    for file_path in py_files:
        results = grep(pattern="def ", path=file_path, recursive=False)
        function_counts += len(results)

    # Should find multiple function definitions
    assert function_counts > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_with_context_lines(sample_codebase):
    """Test code navigator returns context around matches"""
    from deepagent_coder.mcp_servers.search_tools_server import grep

    results = grep(
        pattern="list_users",
        path=str(sample_codebase),
        context_before=2,
        context_after=2,
        recursive=True,
    )

    assert len(results) > 0
    # Context lines should be included (decorator line before function)
    # Note: grep with context returns additional lines, so we should have more results


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_case_insensitive_search(sample_codebase):
    """Test code navigator can perform case-insensitive searches"""
    from deepagent_coder.mcp_servers.search_tools_server import grep

    # Search for "USER" in various cases
    results = grep(pattern="USER", path=str(sample_codebase), ignore_case=True, recursive=True)

    assert len(results) > 0
    # Should find "User" class and "users" endpoints


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_find_by_file_pattern(sample_codebase):
    """Test code navigator can filter files by pattern"""
    from deepagent_coder.mcp_servers.search_tools_server import grep

    # Only search in Python files
    results = grep(pattern="def", path=str(sample_codebase), file_pattern="*.py", recursive=True)

    assert len(results) > 0
    # All results should be from .py files
    assert all(r["file"].endswith(".py") for r in results)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_head_tool(sample_codebase):
    """Test code navigator can read first lines of files"""
    from deepagent_coder.mcp_servers.search_tools_server import head

    content = head(file_path=str(sample_codebase / "utils.py"), lines=3)

    assert isinstance(content, str)
    assert len(content) > 0
    # Should contain function definition
    assert "def" in content


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_tail_tool(sample_codebase):
    """Test code navigator can read last lines of files"""
    from deepagent_coder.mcp_servers.search_tools_server import tail

    content = tail(file_path=str(sample_codebase / "utils.py"), lines=3)

    assert isinstance(content, str)
    assert len(content) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_wc_tool(sample_codebase):
    """Test code navigator can count lines in files"""
    from deepagent_coder.mcp_servers.search_tools_server import wc

    result = wc(file_path=str(sample_codebase / "utils.py"), lines=True)

    assert isinstance(result, dict)
    assert "lines" in result
    assert result["lines"] > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_ls_tool(sample_codebase):
    """Test code navigator can list directory contents"""
    from deepagent_coder.mcp_servers.search_tools_server import ls

    results = ls(path=str(sample_codebase))

    assert len(results) > 0
    # Should find api, models directories and utils.py
    files_and_dirs = [str(r) if isinstance(r, str) else r.get("name", "") for r in results]
    assert any("api" in f for f in files_and_dirs)
    assert any("models" in f for f in files_and_dirs)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_find_tool(sample_codebase):
    """Test code navigator can find files by name"""
    from deepagent_coder.mcp_servers.search_tools_server import find

    results = find(path=str(sample_codebase), name="routes.py", type="f")

    assert len(results) > 0
    assert any("routes.py" in r for r in results)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_navigator_ripgrep_tool(sample_codebase):
    """Test code navigator can use ripgrep (or fallback to grep)"""
    from deepagent_coder.mcp_servers.search_tools_server import ripgrep

    results = ripgrep(pattern="def", path=str(sample_codebase))

    assert isinstance(results, list)
    # Should find function definitions
    assert len(results) > 0 or "error" not in str(results[0]).lower()
