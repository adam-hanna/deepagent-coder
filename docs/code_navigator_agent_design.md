# Code Search Agent - Simplified Design

## Overview

The Code Search agent is a specialist that uses basic file system tools and grep-like searching to help other agents find code locations. Instead of specialized tools, it relies on reasoning and pattern matching to locate APIs, database calls, function definitions, or any other code artifacts.

## Core Philosophy

- **Simple tools, intelligent usage** - Like a Unix expert who can find anything with grep, find, and ls
- **No framework-specific logic** - The agent learns patterns through its prompt
- **Composable operations** - Chain simple tools to answer complex questions

## Integration with Existing System

### Agent Hierarchy Update

```
┌─────────────────────────────────────────────────┐
│           ORCHESTRATOR AGENT                    │
│  - Routes to code_search when agents need      │
│    to find code locations                       │
└────────────────┬────────────────────────────────┘
                 │
    ┌────────────┼────────────┬─────────────┬──────────────┬──────────────┐
    │            │            │             │              │              │
┌───▼────┐  ┌───▼────┐  ┌───▼────┐   ┌───▼────┐   ┌────▼─────┐   ┌────▼────┐
│  Code  │  │ Debug  │  │Refactor│   │  Test  │   │   Docs   │   │  Code   │
│  Gen   │  │        │  │        │   │        │   │          │   │ Search  │
└────────┘  └────────┘  └────────┘   └────────┘   └──────────┘   └─────────┘
```

## Code Search Agent Implementation

```python
async def create_code_search_agent(llm):
    """Code search specialist with basic filesystem tools"""
    
    # Simple MCP client with generic tools
    client = MultiServerMCPClient({
        "search_tools": {
            "transport": "stdio",
            "command": "python",
            "args": ["./mcp_servers/search_tools_server.py"]
        }
    })
    
    tools = await client.get_tools()
    
    agent = create_react_agent(
        llm,
        tools,
        name="code_search",
        prompt="""You are a code search specialist. You help other agents find code locations using basic search tools.

## Available Tools

- **grep**: Search for patterns in files (supports regex)
- **find**: Find files by name, extension, or path patterns  
- **ls**: List directory contents
- **head/tail**: View start/end of files
- **wc**: Count lines in files

## Search Strategies

### Finding API Endpoints
- Flask: grep for "@app.route" or "@blueprint.route"
- FastAPI: grep for "@app.get", "@app.post", "@router"
- Express: grep for "app.get", "app.post", "router."
- General: search for the API path string, then look nearby for handlers

### Finding Database Calls
- SQL: grep for "SELECT", "INSERT", "UPDATE", "DELETE"
- ORMs: search for ".query", ".filter", ".save()", "objects."
- MongoDB: search for "find(", "insert(", "update("

### Finding Function/Class Definitions
- Python: grep for "def function_name" or "class ClassName"
- JavaScript: grep for "function name" or "const name.*=.*function"
- General: search for the name with word boundaries

### Finding Imports/Dependencies
- Python: grep for "import.*module" or "from.*import"
- JavaScript: grep for "require(" or "import.*from"
- Look at file headers first

## Best Practices

1. Start broad, then narrow:
   - First find relevant files with find
   - Then search within those files with grep
   
2. Use context lines:
   - grep with -B/-A flags to see surrounding code
   
3. Chain operations:
   - find + grep for targeted searches
   - grep + head/tail for specific sections

4. Provide structured results:
   - Always include file path and line numbers
   - Show relevant code context
   - Explain why this location is relevant

## Output Format

Always provide findings as:
```
File: path/to/file.py
Line: 42
Context: [relevant code snippet]
Confidence: High/Medium/Low
Reasoning: Why this is likely the right location
```

Remember: Other agents rely on your accuracy. When uncertain, provide multiple possible locations ranked by confidence."""
    )
    
    return agent
```

## MCP Server: Generic Search Tools

```python
# mcp_servers/search_tools_server.py
from mcp.server.fastmcp import FastMCP
import subprocess
import os
from pathlib import Path
from typing import List, Optional

mcp = FastMCP("Search Tools")

@mcp.tool()
def grep(
    pattern: str,
    path: str = ".",
    file_pattern: Optional[str] = None,
    recursive: bool = True,
    context_before: int = 0,
    context_after: int = 0,
    ignore_case: bool = False,
    regex: bool = False
) -> List[dict]:
    """Search for pattern in files using grep"""
    cmd = ["grep"]
    
    # Build grep flags
    if recursive:
        cmd.append("-r")
    if ignore_case:
        cmd.append("-i")
    if regex:
        cmd.append("-E")
    else:
        cmd.append("-F")  # Fixed string
    
    # Line numbers always
    cmd.append("-n")
    
    # Context lines
    if context_before > 0:
        cmd.extend(["-B", str(context_before)])
    if context_after > 0:
        cmd.extend(["-A", str(context_after)])
    
    # Add pattern and path
    cmd.append(pattern)
    cmd.append(path)
    
    # File pattern filter
    if file_pattern:
        cmd.extend(["--include", file_pattern])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse grep output
        matches = []
        for line in result.stdout.strip().split('\n'):
            if line and ':' in line:
                parts = line.split(':', 2)
                if len(parts) >= 3:
                    matches.append({
                        "file": parts[0],
                        "line": parts[1],
                        "text": parts[2],
                        "pattern": pattern
                    })
        
        return matches
    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
def find(
    path: str = ".",
    name: Optional[str] = None,
    type: Optional[str] = None,  # "f" for file, "d" for directory
    extension: Optional[str] = None,
    max_depth: Optional[int] = None
) -> List[str]:
    """Find files and directories"""
    cmd = ["find", path]
    
    if max_depth:
        cmd.extend(["-maxdepth", str(max_depth)])
    
    if type:
        cmd.extend(["-type", type])
    
    if name:
        cmd.extend(["-name", name])
    elif extension:
        cmd.extend(["-name", f"*.{extension}"])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        files = [f for f in result.stdout.strip().split('\n') if f]
        return files
    except Exception as e:
        return [f"Error: {str(e)}"]

@mcp.tool()
def ls(
    path: str = ".",
    all_files: bool = False,
    long_format: bool = False
) -> List[dict]:
    """List directory contents"""
    cmd = ["ls"]
    
    if all_files:
        cmd.append("-a")
    if long_format:
        cmd.append("-l")
    
    cmd.append(path)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if long_format:
            # Parse ls -l output
            files = []
            for line in result.stdout.strip().split('\n')[1:]:  # Skip total line
                if line:
                    parts = line.split(None, 8)
                    if len(parts) >= 9:
                        files.append({
                            "permissions": parts[0],
                            "size": parts[4],
                            "date": f"{parts[5]} {parts[6]} {parts[7]}",
                            "name": parts[8]
                        })
        else:
            files = result.stdout.strip().split('\n')
            
        return files
    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
def head(
    file_path: str,
    lines: int = 10
) -> str:
    """Show first N lines of a file"""
    try:
        with open(file_path, 'r') as f:
            head_lines = []
            for i, line in enumerate(f):
                if i >= lines:
                    break
                head_lines.append(line.rstrip())
        return '\n'.join(head_lines)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def tail(
    file_path: str,
    lines: int = 10
) -> str:
    """Show last N lines of a file"""
    try:
        with open(file_path, 'r') as f:
            all_lines = f.readlines()
            tail_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        return ''.join(tail_lines)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def wc(
    file_path: str,
    lines: bool = True,
    words: bool = False,
    chars: bool = False
) -> dict:
    """Count lines, words, or characters in file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        result = {}
        if lines:
            result["lines"] = content.count('\n') + (1 if content and not content.endswith('\n') else 0)
        if words:
            result["words"] = len(content.split())
        if chars:
            result["characters"] = len(content)
            
        return result
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def ripgrep(
    pattern: str,
    path: str = ".",
    file_type: Optional[str] = None,
    context: int = 0,
    multiline: bool = False
) -> List[dict]:
    """Fast search using ripgrep (if available)"""
    # Check if ripgrep is available
    if not shutil.which("rg"):
        return grep(pattern, path)  # Fallback to grep
    
    cmd = ["rg", "--json", "-n"]
    
    if file_type:
        cmd.extend(["-t", file_type])
    
    if context > 0:
        cmd.extend(["-C", str(context)])
        
    if multiline:
        cmd.append("--multiline")
    
    cmd.extend([pattern, path])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        matches = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    if data.get('type') == 'match':
                        match_data = data['data']
                        matches.append({
                            "file": match_data['path']['text'],
                            "line": match_data['line_number'],
                            "text": match_data['lines']['text'].strip(),
                            "column": match_data.get('submatches', [{}])[0].get('start', 0)
                        })
                except:
                    pass
                    
        return matches
    except Exception as e:
        return grep(pattern, path)  # Fallback to grep

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

## Usage Examples

### Example 1: Finding an API Endpoint

```python
# User: "Find the foo API endpoint"

# Code search agent reasoning:
# 1. First, find all API-related files
files = await find(path=".", name="*api*", type="f", extension="py")

# 2. Search for "foo" in route definitions
results = await grep(
    pattern="foo",
    path="./api",
    file_pattern="*.py",
    context_after=5,
    context_before=2
)

# 3. Look for route decorators near "foo" mentions
for result in results:
    # Check context for @app.route, @router, etc.
    route_check = await grep(
        pattern="@.*route|@router",
        path=result["file"],
        context_after=10
    )
    
# Returns structured findings:
"""
File: api/routes/foo.py
Line: 45
Context:
    @router.get("/api/foo/{id}")
    async def get_foo(id: str, db: Session):
        \"\"\"Fetch foo by ID\"\"\"
Confidence: High
Reasoning: Found @router.get decorator with /api/foo path
"""
```

### Example 2: Finding Database Calls

```python
# User: "Where are the database calls for user data?"

# Code search agent reasoning:
# 1. Find files with "user" in name
user_files = await find(name="*user*", type="f")

# 2. Search for SQL queries
sql_results = await grep(
    pattern="SELECT.*FROM.*user",
    path=".",
    recursive=True,
    ignore_case=True,
    regex=True
)

# 3. Search for ORM patterns
orm_results = await grep(
    pattern="User.query|User.objects|db.session.query",
    path=".",
    file_pattern="*.py",
    regex=True
)

# 4. Check each result's context
for result in sql_results + orm_results:
    context = await grep(
        pattern=result["text"],
        path=result["file"],
        context_before=5,
        context_after=5
    )
```

## State Management

Simple state updates to pass findings:

```python
class AgentState(TypedDict):
    messages: Annotated[list, add]
    current_file: str
    project_context: dict
    next_agent: str
    search_results: dict  # NEW: Store search findings

# When code_search completes, it adds structured results
search_results = {
    "query": "foo API endpoint",
    "findings": [
        {
            "file": "api/routes/foo.py",
            "line": 45,
            "function": "get_foo",
            "confidence": "high"
        }
    ],
    "search_pattern": "@router.*foo",
    "files_examined": 12
}
```

## Benefits of Simplified Approach

1. **Flexibility** - Can find anything without hardcoded patterns
2. **Transparency** - Other developers understand grep/find commands
3. **Maintainability** - No framework-specific code to update
4. **Composability** - Agent learns to chain simple tools effectively
5. **Portability** - Works with any language or framework

The agent's intelligence comes from its reasoning about how to use simple tools, not from complex pre-programmed patterns. This mirrors how human developers actually search codebases.