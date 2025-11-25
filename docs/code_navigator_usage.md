# Code Navigator Usage Guide

## Overview

The Code Navigator is a specialized subagent that helps locate code artifacts in a codebase using filesystem search tools (grep, find, ls, head, tail, wc, ripgrep).

## When to Use

- Finding API endpoints
- Locating database queries
- Discovering function/class definitions
- Finding configuration files
- Searching for imports and dependencies
- Understanding project structure

## How It Works

The Code Navigator uses a reasoning-based approach:
1. Receives a search query (e.g., "find the user login endpoint")
2. Breaks down the query into search steps
3. Uses tools (grep, find, etc.) to explore the codebase
4. Returns structured results with file paths, line numbers, and context

## Search Strategies

### Finding API Endpoints

**Flask:**
```python
# Searches for route decorators
grep(pattern="@app.route.*login", regex=True)
```

**FastAPI:**
```python
grep(pattern="@router.(get|post).*login", regex=True)
```

**Express (JavaScript):**
```python
grep(pattern="app.(get|post).*login", regex=True)
```

### Finding Database Calls

**SQL:**
```python
grep(pattern="SELECT.*FROM.*users", regex=True, ignore_case=True)
```

**ORM (SQLAlchemy):**
```python
grep(pattern="User.query|session.query", regex=True)
```

**MongoDB:**
```python
grep(pattern="db.collection.find|Model.find", regex=True)
```

### Finding Functions

**Python:**
```python
grep(pattern="def validate_email", recursive=True)
```

**JavaScript:**
```python
grep(pattern="function validateEmail|const validateEmail.*=", regex=True)
```

**TypeScript:**
```python
grep(pattern="function validateEmail|const validateEmail.*:.*=>", regex=True)
```

### Finding Class Definitions

**Python:**
```python
grep(pattern="class User.*:", regex=True)
```

**JavaScript/TypeScript:**
```python
grep(pattern="class User", recursive=True)
```

### Finding Imports

**Python:**
```python
grep(pattern="import.*User|from.*import.*User", regex=True)
```

**JavaScript:**
```python
grep(pattern="import.*User|require.*User", regex=True)
```

## Output Format

Results are returned in `search_results` state:

```python
{
    "query": "user login endpoint",
    "findings": [
        {
            "file": "api/routes/auth.py",
            "line": 45,
            "function": "login",
            "code": "@router.post('/api/login')\nasync def login(...):",
            "confidence": "high"
        }
    ],
    "files_examined": 12,
    "search_pattern": "@router.*login"
}
```

## Integration with Other Agents

The orchestrator routes to Code Navigator when:
- User asks "where is X?"
- Other agents need file locations
- Before debugging or refactoring

Example workflow:
1. User: "Fix the login bug"
2. Orchestrator routes to Code Navigator
3. Code Navigator finds login code location
4. Orchestrator routes to Debugger with location
5. Debugger fixes the bug

## Available Tools

### grep
Search for patterns in files with regex support.

**Parameters:**
- `pattern`: Pattern to search for
- `path`: Directory or file path to search
- `file_pattern`: Optional glob pattern to filter files (e.g., "*.py")
- `recursive`: Search recursively through directories (default: True)
- `context_before`: Number of lines to show before match
- `context_after`: Number of lines to show after match
- `ignore_case`: Case-insensitive search
- `regex`: Treat pattern as regex (default: False)

**Example:**
```python
grep(
    pattern="@router.get",
    path="./api",
    file_pattern="*.py",
    recursive=True,
    context_after=5
)
```

### find
Find files and directories by name, type, or extension.

**Parameters:**
- `path`: Starting directory for search
- `name`: Exact filename to match
- `type`: "f" for files only, "d" for directories only
- `extension`: File extension to match (without dot)
- `max_depth`: Maximum depth to search

**Example:**
```python
find(
    path="./src",
    extension="py",
    type="f"
)
```

### ls
List directory contents.

**Parameters:**
- `path`: Directory to list
- `all_files`: Include hidden files (starting with .)
- `long_format`: Show detailed information (permissions, size, date)

**Example:**
```python
ls(path="./src", all_files=True)
```

### head
Show first N lines of a file.

**Parameters:**
- `file_path`: Path to file
- `lines`: Number of lines to show (default: 10)

**Example:**
```python
head(file_path="./main.py", lines=20)
```

### tail
Show last N lines of a file.

**Parameters:**
- `file_path`: Path to file
- `lines`: Number of lines to show (default: 10)

**Example:**
```python
tail(file_path="./log.txt", lines=50)
```

### wc
Count lines, words, or characters in file.

**Parameters:**
- `file_path`: Path to file
- `lines`: Count lines (default: True)
- `words`: Count words
- `chars`: Count characters

**Example:**
```python
wc(file_path="./main.py", lines=True, words=True)
```

### ripgrep
Fast search using ripgrep (falls back to grep if not available).

**Parameters:**
- `pattern`: Pattern to search for
- `path`: Directory or file path to search
- `file_type`: Language/file type to filter (e.g., "py", "js")
- `context`: Number of context lines before and after match
- `multiline`: Enable multiline search

**Example:**
```python
ripgrep(
    pattern="async def.*login",
    path="./api",
    file_type="py",
    context=3
)
```

## Examples

### Example 1: Finding an API Endpoint

**Query:** "Find the user registration endpoint"

**Steps:**
1. `find(name="*api*", type="f")` → Find API files
2. `grep(pattern="register", path="./api")` → Search for "register"
3. `grep(pattern="@.*route", file="<match>", context=10)` → Find route decorator

**Result:**
```
File: api/auth.py
Line: 67
Context:
    @router.post("/api/register")
    async def register_user(user_data: UserCreate):
        return await create_user(user_data)
Confidence: High
Reasoning: Found @router.post decorator with /api/register path
```

### Example 2: Finding Database Queries

**Query:** "Where do we query the users table?"

**Steps:**
1. `find(name="*user*", extension="py")` → Find user-related files
2. `grep(pattern="users", file=<files>)` → Search for "users"
3. `grep(pattern="SELECT|query|filter", context=5)` → Look for SQL patterns

**Result:**
```
File: models/user.py
Line: 23
Context:
    def get_by_email(self, email):
        return db.session.query(User).filter(
            User.email == email
        ).first()
Confidence: High
Reasoning: Found SQLAlchemy query with User model filter
```

### Example 3: Finding Function Definition

**Query:** "Find the validate_email function"

**Steps:**
1. `grep(pattern="def validate_email", recursive=True)` → Search for function
2. `head(file_path="<match>", lines=30)` → View function implementation

**Result:**
```
File: utils/validators.py
Line: 15
Context:
    def validate_email(email: str) -> bool:
        """Validate email format using regex"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
Confidence: High
Reasoning: Found function definition with complete implementation
```

### Example 4: Chaining Operations

**Query:** "Find all API endpoints in the project"

**Steps:**
```python
# Step 1: Find all Python files
py_files = find(path="./", extension="py", type="f")

# Step 2: Search for route decorators in each file
endpoints = []
for file_path in py_files:
    results = grep(
        pattern="@(router|app)\.(get|post|put|delete)",
        path=file_path,
        regex=True,
        context_after=2
    )
    endpoints.extend(results)

# Step 3: Filter to only API-related files
api_endpoints = [e for e in endpoints if "api" in e["file"]]
```

## Tips for Effective Searching

1. **Start broad, narrow down**: Use find to locate files, then grep within them
2. **Use context**: Always request context lines to understand matches
3. **Chain operations**: Combine tools for complex queries
4. **Verify results**: Use head/tail to examine full context
5. **Provide confidence**: Rank findings by likelihood

## Troubleshooting

### No Results Found
- Try broader patterns
- Check file paths are correct
- Use case-insensitive search
- Expand search to more file types

### Too Many Results
- Add file type filters
- Use more specific patterns
- Narrow search path
- Use regex with word boundaries

### Incorrect Matches
- Examine context lines
- Check for similar naming
- Search for imports to verify usage
- Use ripgrep for better accuracy

## Performance Considerations

- **Large codebases**: Use file_pattern to filter by extension
- **Deep directories**: Set max_depth to limit search scope
- **Regex patterns**: Use fixed string search (regex=False) when possible
- **Context lines**: Request only needed context to reduce output

## Integration with Other Subagents

### Code Generator
Code Navigator finds existing similar code to guide generation:
```
Navigator: Find existing API endpoint patterns
Generator: Create new endpoint following discovered patterns
```

### Debugger
Code Navigator locates bugs before debugging:
```
Navigator: Find all usages of deprecated function
Debugger: Fix each usage identified
```

### Test Writer
Code Navigator finds code to test:
```
Navigator: Find all public functions in module
Test Writer: Create tests for discovered functions
```

### Refactorer
Code Navigator identifies refactoring targets:
```
Navigator: Find all database queries without error handling
Refactorer: Add error handling to discovered queries
```

## Best Practices

1. **Be specific**: Provide clear search queries with expected file types
2. **Use context**: Always show surrounding code for verification
3. **Verify findings**: Cross-reference with imports and usages
4. **Document confidence**: Explain why a match is likely correct
5. **Chain wisely**: Combine tools efficiently to minimize searches
6. **Handle errors**: Gracefully handle missing files or invalid patterns
7. **Return structured data**: Always include file path, line number, and code snippet

## Common Patterns

### Finding API Routes by Path
```python
# Find endpoint by URL path
grep(pattern='/api/users.*', path='./api', regex=True)
```

### Finding Database Models
```python
# Find SQLAlchemy models
grep(pattern='class.*\(Base\):', path='./models', regex=True)
```

### Finding Configuration Files
```python
# Find config files
find(path='./', name='config.*', type='f')
find(path='./', name='.env*', type='f')
```

### Finding Imports of Module
```python
# Find all imports of a module
grep(pattern='import.*mymodule|from mymodule', regex=True, recursive=True)
```

### Finding TODO Comments
```python
# Find all TODO/FIXME comments
grep(pattern='TODO|FIXME', ignore_case=True, recursive=True)
```

## Limitations

- Cannot parse or understand code semantics (use AST parsers for that)
- Limited to text-based search (no binary file support)
- No fuzzy matching (must specify exact patterns or regex)
- Cannot follow symbolic links (uses resolved paths)
- Limited by filesystem search tool capabilities

## Future Enhancements

Potential improvements to Code Navigator:
- AST-based code search for semantic understanding
- Fuzzy matching for approximate searches
- Caching of search results for repeated queries
- Integration with language servers (LSP) for precise definitions
- Cross-reference analysis (find all callers of function)
- Dependency graph navigation
