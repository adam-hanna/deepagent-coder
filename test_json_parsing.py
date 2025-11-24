#!/usr/bin/env python3
"""Test JSON parsing from Ollama response content"""

import json
import re

# Simulate Ollama response content
content = """{ "name": "write_file", "arguments": { "path": "./todo-api/package.json", "content": "{\n  \\"name\\": \\"todo-api\\",\n  \\"version\\": \\"1.0.0\\"\n}" } }

{ "name": "write_file", "arguments": { "path": "./server.js", "content": "console.log('hello');" } }"""

print("=" * 80)
print("Testing JSON Parsing Logic")
print("=" * 80)
print(f"\nInput content:\n{content}\n")
print("=" * 80)

# Try to find JSON blocks with balanced braces
tool_calls = []
i = 0
while i < len(content):
    # Find start of JSON object
    if content[i] == '{':
        # Try to extract a complete JSON object
        brace_count = 0
        start = i
        in_string = False
        escape_next = False

        for j in range(i, len(content)):
            char = content[j]

            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string

            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1

                    if brace_count == 0:
                        # Found complete JSON object
                        json_str = content[start:j+1]
                        try:
                            obj = json.loads(json_str)
                            if "name" in obj and "arguments" in obj:
                                tool_calls.append(obj)
                                print(f"✓ Found tool call: {obj.get('name')}")
                                print(f"  Arguments keys: {list(obj.get('arguments', {}).keys())}")
                        except Exception as e:
                            print(f"✗ Failed to parse: {e}")
                            print(f"  JSON string: {json_str[:100]}")
                        i = j
                        break
    i += 1

print(f"\n{'='*80}")
print(f"Result: Found {len(tool_calls)} tool call(s)")
for tc in tool_calls:
    print(f"  - {tc['name']}: {list(tc['arguments'].keys())}")
print("=" * 80)
