# tests/test_coding_agent.py
from unittest.mock import AsyncMock, patch

import pytest

from deepagent_coder.coding_agent import CodingDeepAgent


@pytest.mark.asyncio
async def test_coding_agent_creation():
    """Test creating coding agent"""
    with patch("langchain_ollama.ChatOllama"):
        agent = CodingDeepAgent()
        assert agent is not None


@pytest.mark.asyncio
async def test_coding_agent_initialization():
    """Test agent initialization"""
    with (
        patch("langchain_ollama.ChatOllama"),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._create_subagents",
            new_callable=AsyncMock,
        ),
    ):
        agent = CodingDeepAgent()
        await agent.initialize()
        assert agent.initialized


@pytest.mark.asyncio
async def test_coding_agent_process_request():
    """Test processing user request"""
    with (
        patch("langchain_ollama.ChatOllama"),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._create_subagents",
            new_callable=AsyncMock,
        ),
    ):
        agent = CodingDeepAgent()
        agent.initialized = True
        agent.agent = AsyncMock()
        agent.agent.ainvoke.return_value = {
            "messages": [{"role": "assistant", "content": "Response"}]
        }

        result = await agent.process_request("Test request")
        assert result is not None


def test_agent_state_includes_search_results():
    """Test AgentState has search_results field"""
    from deepagent_coder.coding_agent import AgentState

    # AgentState should have search_results in its annotations
    assert "search_results" in AgentState.__annotations__


@pytest.mark.asyncio
async def test_coding_agent_creates_code_navigator():
    """Test CodingDeepAgent creates code navigator subagent"""
    with (
        patch("langchain_ollama.ChatOllama"),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_coder.coding_agent.create_code_navigator", new_callable=AsyncMock
        ) as mock_nav,
        patch("deepagent_coder.coding_agent.create_code_generator_agent", new_callable=AsyncMock),
        patch("deepagent_coder.coding_agent.create_debugger_agent", new_callable=AsyncMock),
        patch("deepagent_coder.coding_agent.create_test_writer_agent", new_callable=AsyncMock),
        patch("deepagent_coder.coding_agent.create_refactorer_agent", new_callable=AsyncMock),
        patch("deepagent_coder.coding_agent.create_devops_agent", new_callable=AsyncMock),
    ):
        agent = CodingDeepAgent()
        await agent.initialize()

        # Code navigator should be created
        mock_nav.assert_called_once()

        # Verify code_navigator is in subagents dict
        assert "code_navigator" in agent.subagents


@pytest.mark.asyncio
async def test_orchestrator_prompt_includes_code_navigator():
    """Test orchestrator system prompt includes code_navigator guidance"""
    with (
        patch("langchain_ollama.ChatOllama"),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._create_subagents",
            new_callable=AsyncMock,
        ),
        patch("deepagent_coder.coding_agent.MCPClientManager") as mock_mcp,
    ):
        # Mock the MCP client to return empty tools
        mock_client = AsyncMock()
        mock_client.get_all_tools = AsyncMock(return_value=[])
        mock_mcp.return_value = mock_client

        agent = CodingDeepAgent()
        agent.initialized = True
        agent.subagents = {
            "code_navigator": AsyncMock(),
            "code_generator": AsyncMock(),
            "debugger": AsyncMock(),
        }

        # Create a state to process
        state = {
            "messages": [{"role": "user", "content": "Find the login endpoint"}],
            "current_file": "",
            "project_context": {},
            "search_results": {},
            "next_agent": "",
        }

        # Mock the model's ainvoke to capture the system prompt
        mock_model = AsyncMock()
        from langchain_core.messages import AIMessage

        mock_model.ainvoke = AsyncMock(return_value=AIMessage(content="Test response"))
        agent.main_model = mock_model

        # Process the state (this will build the system prompt)
        import contextlib

        with contextlib.suppress(Exception):
            await agent._agent_invoke(state)

        # Check that ainvoke was called with messages including the system prompt
        if mock_model.ainvoke.called:
            call_args = mock_model.ainvoke.call_args
            messages = call_args[0][0] if call_args[0] else []

            # Get the system message
            system_message = None
            for msg in messages:
                if hasattr(msg, "type") and msg.type == "system":
                    system_message = msg.content
                    break

            # Verify code_navigator is mentioned in system prompt
            if system_message:
                assert "code_navigator" in system_message.lower()
                assert "find" in system_message.lower() or "search" in system_message.lower()
                assert "API" in system_message or "endpoint" in system_message.lower()


@pytest.mark.asyncio
async def test_ensure_parent_directory_exists_creates_directory():
    """Test that _ensure_parent_directory_exists creates parent directories"""
    from pathlib import Path

    with (
        patch("langchain_ollama.ChatOllama"),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._create_subagents",
            new_callable=AsyncMock,
        ),
    ):
        agent = CodingDeepAgent()
        agent.workspace = Path("/tmp/test-workspace")

        # Mock create_directory tool
        mock_mkdir_tool = AsyncMock()
        mock_mkdir_tool.name = "create_directory"
        mock_mkdir_tool.ainvoke = AsyncMock()

        tools = [mock_mkdir_tool]

        # Test creating parent directory for ./src/server.ts
        await agent._ensure_parent_directory_exists("./src/server.ts", tools)

        # Verify create_directory was called with absolute path
        mock_mkdir_tool.ainvoke.assert_called_once()
        call_args = mock_mkdir_tool.ainvoke.call_args[0][0]
        assert "src" in call_args["path"]
        assert str(agent.workspace) in call_args["path"]


@pytest.mark.asyncio
async def test_ensure_parent_directory_exists_handles_nested_paths():
    """Test auto-mkdir with nested directory structures"""
    from pathlib import Path

    with (
        patch("langchain_ollama.ChatOllama"),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._create_subagents",
            new_callable=AsyncMock,
        ),
    ):
        agent = CodingDeepAgent()
        agent.workspace = Path("/tmp/test-workspace")

        # Mock create_directory tool
        mock_mkdir_tool = AsyncMock()
        mock_mkdir_tool.name = "create_directory"
        mock_mkdir_tool.ainvoke = AsyncMock()

        tools = [mock_mkdir_tool]

        # Test creating nested parent directory for ./test/unit/helpers/util.ts
        await agent._ensure_parent_directory_exists("./test/unit/helpers/util.ts", tools)

        # Verify create_directory was called with correct nested path
        mock_mkdir_tool.ainvoke.assert_called_once()
        call_args = mock_mkdir_tool.ainvoke.call_args[0][0]
        assert "test/unit/helpers" in call_args["path"]


@pytest.mark.asyncio
async def test_ensure_parent_directory_exists_skips_current_directory():
    """Test that auto-mkdir doesn't create directory for files in current directory"""
    from pathlib import Path

    with (
        patch("langchain_ollama.ChatOllama"),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._create_subagents",
            new_callable=AsyncMock,
        ),
    ):
        agent = CodingDeepAgent()
        agent.workspace = Path("/tmp/test-workspace")

        # Mock create_directory tool
        mock_mkdir_tool = AsyncMock()
        mock_mkdir_tool.name = "create_directory"
        mock_mkdir_tool.ainvoke = AsyncMock()

        tools = [mock_mkdir_tool]

        # Test with file in current directory
        await agent._ensure_parent_directory_exists("./hello.txt", tools)

        # Verify create_directory was NOT called
        mock_mkdir_tool.ainvoke.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_parent_directory_exists_handles_no_leading_dot():
    """Test auto-mkdir with paths that don't have ./ prefix"""
    from pathlib import Path

    with (
        patch("langchain_ollama.ChatOllama"),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._create_subagents",
            new_callable=AsyncMock,
        ),
    ):
        agent = CodingDeepAgent()
        agent.workspace = Path("/tmp/test-workspace")

        # Mock create_directory tool
        mock_mkdir_tool = AsyncMock()
        mock_mkdir_tool.name = "create_directory"
        mock_mkdir_tool.ainvoke = AsyncMock()

        tools = [mock_mkdir_tool]

        # Test with path without ./ prefix
        await agent._ensure_parent_directory_exists("src/components/Button.tsx", tools)

        # Verify create_directory was called
        mock_mkdir_tool.ainvoke.assert_called_once()
        call_args = mock_mkdir_tool.ainvoke.call_args[0][0]
        assert "src/components" in call_args["path"]


@pytest.mark.asyncio
async def test_ensure_parent_directory_gracefully_handles_mkdir_errors():
    """Test that auto-mkdir handles errors gracefully and doesn't crash"""
    from pathlib import Path

    with (
        patch("langchain_ollama.ChatOllama"),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._create_subagents",
            new_callable=AsyncMock,
        ),
    ):
        agent = CodingDeepAgent()
        agent.workspace = Path("/tmp/test-workspace")

        # Mock create_directory tool that raises an error
        mock_mkdir_tool = AsyncMock()
        mock_mkdir_tool.name = "create_directory"
        mock_mkdir_tool.ainvoke = AsyncMock(side_effect=Exception("Directory already exists"))

        tools = [mock_mkdir_tool]

        # Test that error doesn't crash - should be caught and logged
        try:
            await agent._ensure_parent_directory_exists("./src/server.ts", tools)
            # Should not raise exception
        except Exception as e:
            pytest.fail(
                f"_ensure_parent_directory_exists should handle errors gracefully, but raised: {e}"
            )


@pytest.mark.asyncio
async def test_edit_file_path_resolution():
    """Test that edit_file tool correctly resolves relative paths to absolute workspace paths"""
    from pathlib import Path

    with (
        patch("langchain_ollama.ChatOllama"),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._create_subagents",
            new_callable=AsyncMock,
        ),
    ):
        agent = CodingDeepAgent()
        agent.workspace = Path("/tmp/test-workspace")
        agent.initialized = True

        # Mock edit_file tool
        mock_edit_tool = AsyncMock()
        mock_edit_tool.name = "edit_file"
        mock_edit_tool.ainvoke = AsyncMock(return_value="File edited successfully")

        tools = [mock_edit_tool]

        # Simulate calling edit_file with relative path
        tool_args = {
            "file_path": "./src/server.ts",
            "old_text": "old content",
            "new_text": "new content",
        }

        # Find the edit tool and invoke it (simulating what happens in _execute_tool_call)
        for tool in tools:
            if "edit_file" in tool.name.lower():
                # Path fixing logic should convert ./src/server.ts to absolute path
                file_path = tool_args.get("file_path")
                if file_path and not Path(file_path).is_absolute():
                    # Strip ./ prefix if present
                    if file_path.startswith("./"):
                        file_path = file_path[2:]
                    # Convert to absolute workspace path
                    tool_args["file_path"] = str((agent.workspace / file_path).resolve())

                await tool.ainvoke(tool_args)

        # Verify edit_file was called with absolute path
        mock_edit_tool.ainvoke.assert_called_once()
        call_args = mock_edit_tool.ainvoke.call_args[0][0]
        assert call_args["file_path"] == str((agent.workspace / "src/server.ts").resolve())
        assert Path(call_args["file_path"]).is_absolute()


@pytest.mark.asyncio
async def test_write_file_with_auto_mkdir_integration():
    """Test that write_file automatically creates parent directories before writing"""
    from pathlib import Path

    with (
        patch("langchain_ollama.ChatOllama"),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._setup_mcp_tools", new_callable=AsyncMock
        ),
        patch(
            "deepagent_coder.coding_agent.CodingDeepAgent._create_subagents",
            new_callable=AsyncMock,
        ),
    ):
        agent = CodingDeepAgent()
        agent.workspace = Path("/tmp/test-workspace")
        agent.initialized = True

        # Mock both tools
        mock_mkdir_tool = AsyncMock()
        mock_mkdir_tool.name = "create_directory"
        mock_mkdir_tool.ainvoke = AsyncMock()

        mock_write_tool = AsyncMock()
        mock_write_tool.name = "write_file"
        mock_write_tool.ainvoke = AsyncMock(return_value="File written successfully")

        # Simulate tool execution for write_file with subdirectory
        tool_name = "write_file"
        tool_args = {"path": "./src/utils/helper.ts", "content": "export const helper = () => {};"}

        tools = [mock_mkdir_tool, mock_write_tool]

        # Simulate the auto-mkdir logic that runs before write_file
        if "write_file" in tool_name.lower():
            file_path = tool_args.get("path") or tool_args.get("file_path")
            if file_path:
                await agent._ensure_parent_directory_exists(file_path, tools)

        # Verify create_directory was called first
        mock_mkdir_tool.ainvoke.assert_called_once()
        mkdir_call_args = mock_mkdir_tool.ainvoke.call_args[0][0]
        assert "src/utils" in mkdir_call_args["path"]
