#!/usr/bin/env python3
"""Debug script to test if Ollama models support tool calling"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from deepagent_claude.core.mcp_client import MCPClientManager


async def test_tool_calling():
    """Test if Ollama model supports tool calling"""

    print("=" * 80)
    print("Testing Ollama Tool Calling Support")
    print("=" * 80)

    # Setup MCP client
    test_dir = Path("/tmp/test-tools").resolve()
    test_dir.mkdir(exist_ok=True)

    config = {
        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", str(test_dir)]
        }
    }

    print("\n1. Initializing MCP client...")
    manager = MCPClientManager(custom_configs=config, use_defaults=False)
    await manager.initialize()

    print("2. Getting tools...")
    tools = await manager.get_all_tools()
    print(f"   Retrieved {len(tools)} tools")
    if tools:
        print(f"   Tool names: {[t.name for t in tools[:5]]}")

    # Create model
    print("\n3. Creating Ollama model (qwen2.5-coder:latest)...")
    model = ChatOllama(
        model="qwen2.5-coder:latest",
        temperature=0.3,
        num_ctx=8192
    )

    # Bind tools
    print("4. Binding tools to model...")
    model_with_tools = model.bind_tools(tools)
    print("   ✓ Tools bound")

    # Test invocation
    print("\n5. Invoking model with tool calling request...")
    messages = [
        SystemMessage(content="You are a helpful assistant with access to filesystem tools. When asked to create files, use the write_file tool."),
        HumanMessage(content="Create a file called test.txt with content 'Hello World'")
    ]

    response = await model_with_tools.ainvoke(messages)

    print("\n6. Analyzing response...")
    print(f"   Response type: {type(response)}")
    print(f"   Has 'content' attr: {hasattr(response, 'content')}")
    print(f"   Has 'tool_calls' attr: {hasattr(response, 'tool_calls')}")

    if hasattr(response, 'content'):
        print(f"\n   Content (first 500 chars):")
        print(f"   {response.content[:500]}")

    if hasattr(response, 'tool_calls'):
        print(f"\n   Tool calls: {response.tool_calls}")
        if response.tool_calls:
            print(f"   ✓ Model DOES support tool calling!")
            print(f"   Number of tool calls: {len(response.tool_calls)}")
            for tc in response.tool_calls:
                print(f"   - {tc}")
        else:
            print(f"   ✗ Model does NOT support tool calling (tool_calls is empty)")
            print(f"   The model generated JSON as text instead of using tool_calls")

    # Cleanup
    print("\n7. Cleaning up...")
    await manager.close()

    print("\n" + "=" * 80)
    print("CONCLUSION:")
    if hasattr(response, 'tool_calls') and response.tool_calls:
        print("✓ Ollama model SUPPORTS tool calling - investigate why agent doesn't work")
    else:
        print("✗ Ollama model DOES NOT support tool calling")
        print("  Solution: Need to parse JSON from content and execute tools manually")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_tool_calling())
