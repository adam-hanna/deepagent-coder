#!/usr/bin/env python3
"""Test MCP client in isolation to verify it's working"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from deepagent_claude.core.mcp_client import MCPClientManager

async def test_mcp_client():
    """Test MCP client can retrieve and execute tools"""

    # Create test directory (resolve symlinks on macOS)
    test_dir = Path("/tmp/test-mcp").resolve()
    test_dir.mkdir(exist_ok=True)

    print("=" * 80)
    print("Testing MCP Client in Isolation")
    print("=" * 80)

    # Configure MCP client with only filesystem server
    config = {
        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", str(test_dir)]
        }
    }

    print(f"\n1. Creating MCPClientManager with config:")
    print(f"   Workspace: {test_dir}")

    manager = MCPClientManager(custom_configs=config, use_defaults=False)

    print("\n2. Initializing MCP client...")
    try:
        await manager.initialize()
        print("   ✓ Initialization successful")
    except Exception as e:
        print(f"   ✗ Initialization failed: {e}")
        return

    print("\n3. Retrieving tools...")
    try:
        tools = await manager.get_all_tools()
        print(f"   ✓ Retrieved {len(tools)} tools")

        if tools:
            print("\n   Available tools:")
            for i, tool in enumerate(tools[:10], 1):  # Show first 10
                print(f"   {i}. {tool.name}: {tool.description[:80] if hasattr(tool, 'description') else 'No description'}")
            if len(tools) > 10:
                print(f"   ... and {len(tools) - 10} more tools")
        else:
            print("   ✗ No tools retrieved!")
            return

    except Exception as e:
        print(f"   ✗ Failed to get tools: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test tool execution
    print("\n4. Testing tool execution...")

    # Try to find write_file or create_file tool
    write_tool = None
    for tool in tools:
        if tool.name in ['write_file', 'create_file', 'write']:
            write_tool = tool
            break

    if not write_tool:
        print("   ✗ Could not find write_file or create_file tool")
        print(f"   Available tool names: {[t.name for t in tools]}")
        return

    print(f"   Found tool: {write_tool.name}")

    # Try to execute the tool
    test_file = test_dir / "test.txt"
    test_content = "Hello from MCP test!"

    try:
        print(f"   Attempting to write to: {test_file}")
        result = await write_tool.ainvoke({
            "path": str(test_file),
            "content": test_content
        })
        print(f"   ✓ Tool executed successfully")
        print(f"   Result: {result}")

        # Verify file was created
        if test_file.exists():
            print(f"   ✓ File created successfully!")
            content = test_file.read_text()
            print(f"   Content: {content}")
        else:
            print(f"   ✗ File was not created")

    except Exception as e:
        print(f"   ✗ Tool execution failed: {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    print("\n5. Cleaning up...")
    await manager.close()
    print("   ✓ MCP client closed")

    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_mcp_client())
