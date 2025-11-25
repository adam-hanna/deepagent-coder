# DevOps & Code Review Agents - Integration Plan

## 1. DevOps Agent + Container/Build Tools

### Overview
The DevOps Agent automates the entire deployment pipeline, from code changes to production. It works closely with existing agents to ensure deployable code and manages infrastructure as code.

### Integration Points

#### With Existing Agents:
- **After Code Generator**: Automatically containerize new services
- **After Debugger**: Update deployment configs for bug fixes requiring env changes
- **After Refactorer**: Adjust build configs for structural changes
- **With Navigator**: Find existing deployment configurations and infrastructure code
- **After Tester**: Ensure all tests pass before deployment

#### Enhanced Orchestrator Logic:
```python
# Additional routing logic for orchestrator
routing_guidelines = """
- After code changes: Route to tester → devops for deployment
- For "deploy" requests: navigator (find configs) → devops
- For "scale" requests: devops directly
- For "rollback" requests: devops with urgency flag
"""
```

### DevOps Agent Implementation

```python
async def create_devops_agent(llm):
    """DevOps specialist for deployment automation"""
    
    client = MultiServerMCPClient({
        "container_tools": {
            "transport": "stdio",
            "command": "python",
            "args": ["./mcp_servers/container_tools_server.py"]
        },
        "build_tools": {
            "transport": "stdio",
            "command": "python",
            "args": ["./mcp_servers/build_tools_server.py"]
        },
        "k8s_tools": {
            "transport": "stdio",
            "command": "python",
            "args": ["./mcp_servers/k8s_tools_server.py"]
        }
    })
    
    tools = await client.get_tools()
    
    agent = create_react_agent(
        llm,
        tools,
        name="devops",
        prompt="""You are a DevOps automation specialist.

## Integration with Team

1. **From Navigator**: Receive deployment config locations
   - Use navigator's findings to update the right files
   - Example: "deployment configs at k8s/app/deployment.yaml"

2. **From Tester**: Receive test results before deployment
   - Only proceed if all tests pass
   - Create rollback plan if deploying despite failures

3. **To Code Generator**: Provide deployment templates
   - When new services are created, generate matching configs

## Workflow Patterns

### Containerization Flow
1. Analyze application (use navigator findings)
2. Generate appropriate Dockerfile
3. Create docker-compose for local dev
4. Build and test container
5. Push to registry

### Kubernetes Deployment
1. Generate/update manifests
2. Handle ConfigMaps/Secrets
3. Set resource limits
4. Configure health checks
5. Apply progressive rollout

### CI/CD Pipeline
1. Generate GitHub Actions/GitLab CI
2. Set up build stages
3. Configure test automation
4. Add security scanning
5. Deploy to environments

## State Management

Store deployment state in DeepAgent's filesystem:
- /deployments/current/[service].yaml
- /deployments/history/[timestamp].yaml
- /infrastructure/terraform/
- /ci-cd/pipelines/

## Safety Protocols

1. Always create rollback plans
2. Test in staging first
3. Use canary deployments
4. Monitor after deployment
5. Alert on failures"""
    )
    
    return agent
```

### Container Tools MCP Server

```python
# mcp_servers/container_tools_server.py
from mcp.server.fastmcp import FastMCP
import subprocess
import json
import os
from typing import Optional, Dict, List

mcp = FastMCP("Container Tools")

@mcp.tool()
def docker_command(
    args: List[str],
    capture_output: bool = True,
    input_text: Optional[str] = None
) -> dict:
    """Execute any docker command - generic interface"""
    cmd = ["docker"] + args
    
    try:
        if capture_output:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                input=input_text
            )
            return {
                "command": " ".join(cmd),
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        else:
            # For interactive commands
            result = subprocess.run(cmd)
            return {
                "command": " ".join(cmd),
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
    except Exception as e:
        return {
            "command": " ".join(cmd),
            "error": str(e),
            "success": False
        }

@mcp.tool()
def docker_compose_command(
    args: List[str],
    file: Optional[str] = None,
    project_name: Optional[str] = None,
    capture_output: bool = True
) -> dict:
    """Execute any docker-compose command"""
    cmd = ["docker-compose"]
    
    if file:
        cmd.extend(["-f", file])
    if project_name:
        cmd.extend(["-p", project_name])
    
    cmd.extend(args)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True
        )
        
        return {
            "command": " ".join(cmd),
            "stdout": result.stdout if capture_output else "",
            "stderr": result.stderr if capture_output else "",
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {
            "command": " ".join(cmd),
            "error": str(e),
            "success": False
        }

@mcp.tool()
def kubectl_command(
    args: List[str],
    namespace: Optional[str] = None,
    context: Optional[str] = None,
    output_format: Optional[str] = None
) -> dict:
    """Execute any kubectl command"""
    cmd = ["kubectl"]
    
    if namespace:
        cmd.extend(["-n", namespace])
    if context:
        cmd.extend(["--context", context])
    if output_format:
        cmd.extend(["-o", output_format])
    
    cmd.extend(args)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        # Try to parse JSON output if requested
        output = result.stdout
        if output_format == "json" and output:
            try:
                output = json.loads(output)
            except:
                pass  # Keep as string if parsing fails
        
        return {
            "command": " ".join(cmd),
            "output": output,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {
            "command": " ".join(cmd),
            "error": str(e),
            "success": False
        }

@mcp.tool()
def terraform_command(
    args: List[str],
    working_dir: str = ".",
    auto_approve: bool = False,
    var_file: Optional[str] = None
) -> dict:
    """Execute any terraform command"""
    cmd = ["terraform"]
    cmd.extend(args)
    
    # Add common flags
    if auto_approve and args[0] in ["apply", "destroy"]:
        cmd.append("-auto-approve")
    if var_file:
        cmd.extend(["-var-file", var_file])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=working_dir
        )
        
        return {
            "command": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0,
            "working_dir": working_dir
        }
    except Exception as e:
        return {
            "command": " ".join(cmd),
            "error": str(e),
            "success": False
        }

@mcp.tool()
def read_yaml(file_path: str) -> dict:
    """Read and parse YAML file (for k8s manifests, docker-compose, etc)"""
    try:
        import yaml
        with open(file_path, 'r') as f:
            content = yaml.safe_load(f)
        return {
            "content": content,
            "success": True,
            "file": file_path
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False,
            "file": file_path
        }

@mcp.tool()
def write_yaml(file_path: str, content: dict) -> dict:
    """Write dictionary as YAML file"""
    try:
        import yaml
        with open(file_path, 'w') as f:
            yaml.dump(content, f, default_flow_style=False)
        return {
            "success": True,
            "file": file_path
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Generic Build/Analysis Tools MCP Server

```python
# mcp_servers/generic_build_tools_server.py
from mcp.server.fastmcp import FastMCP
import subprocess
import os
import json
import re
from pathlib import Path
from typing import Optional, List, Dict

mcp = FastMCP("Generic Build Tools")

@mcp.tool()
def run_command(
    command: List[str],
    working_dir: str = ".",
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    shell: bool = False
) -> dict:
    """Run any shell command - ultimate generic tool"""
    try:
        # Merge with existing env if provided
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)
        
        result = subprocess.run(
            command if not shell else " ".join(command),
            capture_output=True,
            text=True,
            cwd=working_dir,
            env=cmd_env,
            timeout=timeout,
            shell=shell
        )
        
        return {
            "command": command if not shell else " ".join(command),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0,
            "working_dir": working_dir
        }
    except subprocess.TimeoutExpired:
        return {
            "command": command if not shell else " ".join(command),
            "error": f"Command timed out after {timeout} seconds",
            "success": False
        }
    except Exception as e:
        return {
            "command": command if not shell else " ".join(command),
            "error": str(e),
            "success": False
        }

@mcp.tool()
def find_files_by_pattern(
    pattern: str,
    path: str = ".",
    recursive: bool = True,
    file_type: Optional[str] = None
) -> List[str]:
    """Find files matching pattern - works like find command"""
    matches = []
    path_obj = Path(path)
    
    if recursive:
        if file_type == "f":  # Files only
            matches = [str(f) for f in path_obj.rglob(pattern) if f.is_file()]
        elif file_type == "d":  # Directories only  
            matches = [str(f) for f in path_obj.rglob(pattern) if f.is_dir()]
        else:  # Both
            matches = [str(f) for f in path_obj.rglob(pattern)]
    else:
        if file_type == "f":
            matches = [str(f) for f in path_obj.glob(pattern) if f.is_file()]
        elif file_type == "d":
            matches = [str(f) for f in path_obj.glob(pattern) if f.is_dir()]
        else:
            matches = [str(f) for f in path_obj.glob(pattern)]
    
    return sorted(matches)

@mcp.tool()
def analyze_file_stats(file_path: str) -> dict:
    """Get detailed file statistics"""
    try:
        path = Path(file_path)
        
        if not path.exists():
            return {"error": f"File not found: {file_path}"}
        
        stats = path.stat()
        
        # Basic stats
        result = {
            "file": file_path,
            "size_bytes": stats.st_size,
            "size_human": format_bytes(stats.st_size),
            "modified": stats.st_mtime,
            "created": stats.st_ctime,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "permissions": oct(stats.st_mode)[-3:]
        }
        
        # For text files, add line counts and basic analysis
        if path.is_file() and stats.st_size < 10_000_000:  # Don't read huge files
            try:
                content = path.read_text()
                lines = content.splitlines()
                
                result.update({
                    "lines": len(lines),
                    "characters": len(content),
                    "non_empty_lines": len([l for l in lines if l.strip()]),
                    "avg_line_length": sum(len(l) for l in lines) / len(lines) if lines else 0
                })
                
                # Language-agnostic code metrics
                result["code_metrics"] = {
                    "comment_lines": count_comment_lines(content, file_path),
                    "import_lines": count_import_lines(content, file_path),
                    "function_definitions": count_function_definitions(content, file_path)
                }
                
            except UnicodeDecodeError:
                result["binary_file"] = True
        
        return result
        
    except Exception as e:
        return {"error": str(e), "file": file_path}

@mcp.tool()
def count_pattern_occurrences(
    pattern: str,
    path: str = ".",
    file_extensions: Optional[List[str]] = None,
    ignore_case: bool = False,
    is_regex: bool = True
) -> dict:
    """Count occurrences of pattern in files"""
    results = {
        "pattern": pattern,
        "total_matches": 0,
        "files_with_matches": 0,
        "matches_by_file": {}
    }
    
    # Build file list
    files = []
    if file_extensions:
        for ext in file_extensions:
            files.extend(find_files_by_pattern(f"*.{ext}", path))
    else:
        # All text files
        all_files = find_files_by_pattern("*", path, file_type="f")
        files = [f for f in all_files if is_text_file(f)]
    
    # Compile pattern
    flags = re.IGNORECASE if ignore_case else 0
    if is_regex:
        pattern_re = re.compile(pattern, flags)
    
    # Search files
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            if is_regex:
                matches = pattern_re.findall(content)
            else:
                # Simple string search
                if ignore_case:
                    matches = content.lower().count(pattern.lower())
                else:
                    matches = content.count(pattern)
                matches = [pattern] * matches if matches else []
            
            if matches:
                results["files_with_matches"] += 1
                results["total_matches"] += len(matches)
                results["matches_by_file"][file_path] = len(matches)
                
        except Exception as e:
            results["matches_by_file"][file_path] = f"Error: {str(e)}"
    
    return results

@mcp.tool()
def extract_structure(
    file_path: str,
    max_depth: int = 3
) -> dict:
    """Extract structure from any text file using indentation and patterns"""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        structure = {
            "file": file_path,
            "sections": [],
            "outline": []
        }
        
        # Detect structure based on patterns
        section_patterns = [
            (r'^#{1,6}\s+(.+)', 'markdown_header'),
            (r'^(class|interface|struct)\s+(\w+)', 'class_definition'),
            (r'^(def|function|fn|func)\s+(\w+)', 'function_definition'),
            (r'^(public|private|protected)?\s*(static)?\s*\w+\s+(\w+)\s*\(', 'method_definition'),
            (r'^(\w+):\s*

### Integration with Existing State

```python
# Enhanced AgentState for DevOps
class AgentState(TypedDict):
    messages: Annotated[list, add]
    current_file: str
    project_context: dict
    next_agent: str
    code_analysis: dict
    search_results: dict
    deployment_state: dict  # NEW: Track deployment status
    test_results: dict      # NEW: From tester agent

# DevOps agent reads from other agents' outputs
deployment_state = {
    "last_deployment": "2024-01-15T10:00:00Z",
    "environment": "staging",
    "version": "v1.2.3",
    "rollback_version": "v1.2.2",
    "config_changes": [],
    "infrastructure_changes": []
}
```

## 2. Code Review Agent + Code Metrics Tools

### Overview
The Code Review Agent provides automated, objective code reviews by combining static analysis, metrics calculation, and learned patterns from the codebase. It acts as a senior developer reviewing PRs.

### Integration Points

#### With Existing Agents:
- **After Code Generator**: Review generated code for quality
- **With Navigator**: Understand code context and patterns
- **Before Refactorer**: Identify what needs refactoring
- **With Tester**: Ensure test coverage meets standards
- **Feeds back to all agents**: Provides quality guidelines

#### Memory Integration:
```python
# Code Review agent writes learned patterns
write_file("/knowledge/code_standards.md", """
## Project Code Standards (Learned)
- Average function length: 15 lines
- Naming convention: snake_case for functions
- Test coverage target: 80%
- Max cyclomatic complexity: 10
""")

# Other agents read and follow these standards
```

### Code Review Agent Implementation

```python
async def create_code_review_agent(llm):
    """Code review specialist with metrics analysis"""
    
    client = MultiServerMCPClient({
        "metrics_tools": {
            "transport": "stdio",
            "command": "python",
            "args": ["./mcp_servers/code_metrics_server.py"]
        },
        "static_analysis": {
            "transport": "stdio",
            "command": "python",
            "args": ["./mcp_servers/static_analysis_server.py"]
        }
    })
    
    tools = await client.get_tools()
    
    # Also inherits search tools from navigator
    tools.extend(navigator_tools)
    
    agent = create_react_agent(
        llm,
        tools,
        name="code_review",
        prompt="""You are a senior code reviewer providing objective, metrics-based reviews.

## Integration with Team

1. **Use Navigator**: Find related code for context
   - Check similar implementations
   - Understand project patterns
   
2. **Inform Other Agents**: Document standards
   - Write findings to /knowledge/code_standards.md
   - Update /review/checklist.md

3. **Work with Tester**: Ensure adequate testing
   - Check test coverage
   - Verify edge cases

## Review Process

### 1. Contextual Analysis
- Use navigator to find similar code
- Check project conventions
- Review recent changes in area

### 2. Metrics Collection
- Cyclomatic complexity
- Code duplication
- Test coverage
- Documentation coverage
- Security vulnerabilities

### 3. Pattern Analysis
- Naming consistency
- Error handling patterns
- API consistency
- Design pattern usage

### 4. Constructive Feedback
Rate each aspect:
- **Correctness**: Does it work?
- **Performance**: Is it efficient?
- **Maintainability**: Is it clear?
- **Security**: Is it safe?
- **Testing**: Is it tested?

## Output Format

```markdown
## Code Review Summary

**Overall Score**: 8.5/10

### Strengths
- Clean function separation
- Good error handling
- Comprehensive tests

### Issues Found
1. **High Complexity** (Line 45-67)
   - Cyclomatic complexity: 12
   - Suggestion: Extract method
   
2. **Missing Tests** (Line 89)
   - Uncovered edge case
   - Suggestion: Add test for null input

### Metrics
- Test Coverage: 85%
- Duplication: 2%
- Complexity Average: 4.5
- Documentation: 90%
```

Remember: Be constructive and educational. Explain WHY something should change."""
    )
    
    return agent
```

### Code Metrics MCP Server

```python
# mcp_servers/code_metrics_server.py
from mcp.server.fastmcp import FastMCP
import ast
import radon.complexity
import radon.metrics

mcp = FastMCP("Code Metrics")

@mcp.tool()
def calculate_complexity(file_path: str) -> dict:
    """Calculate cyclomatic complexity"""
    # Returns per-function complexity scores
    # Identifies complex areas needing refactoring

@mcp.tool()
def measure_code_coverage(
    test_command: str = "pytest",
    source_dir: str = "src"
) -> dict:
    """Run tests and measure coverage"""
    # Integrates with pytest-cov, jest coverage, etc.
    # Returns uncovered lines

@mcp.tool()
def detect_duplication(
    path: str = ".",
    threshold: int = 50  # tokens
) -> list:
    """Find duplicate code blocks"""
    # Uses AST comparison
    # Returns similar code segments

@mcp.tool()
def calculate_maintainability(file_path: str) -> dict:
    """Calculate maintainability index"""
    # Combines complexity, lines of code, comments
    # Returns MI score and breakdown

@mcp.tool()
def analyze_dependencies(file_path: str) -> dict:
    """Analyze import dependencies"""
    # Checks coupling
    # Identifies circular dependencies
```

### Static Analysis MCP Server

```python
# mcp_servers/static_analysis_server.py

@mcp.tool()
def run_linter(
    file_path: str,
    linter: str = None,  # auto-detect
    config_file: str = None
) -> list:
    """Run appropriate linter"""
    # pylint, eslint, rubocop, etc.
    # Returns issues with severity

@mcp.tool()
def security_scan(
    path: str,
    language: str = None
) -> list:
    """Scan for security issues"""
    # Bandit for Python, npm audit, etc.
    # Returns vulnerabilities

@mcp.tool()
def check_type_coverage(file_path: str) -> dict:
    """Analyze type annotation coverage"""
    # For Python: mypy coverage
    # For TS/JS: TypeScript coverage

@mcp.tool()
def documentation_coverage(file_path: str) -> dict:
    """Check documentation completeness"""
    # Docstring coverage
    # Public API documentation
    # README completeness
```

### Enhanced Orchestrator Integration

```python
# Additional state for code review workflow
class ReviewState(TypedDict):
    review_requested: bool
    review_results: dict
    quality_threshold: float
    auto_fix_issues: bool

# Orchestrator routing update
def enhanced_supervisor_logic(state):
    """Route based on quality gates"""
    
    if state.get("review_requested"):
        return "code_review"
    
    # Auto-review after code generation
    if state.get("last_agent") == "code_gen" and AUTO_REVIEW_ENABLED:
        return "code_review"
    
    # Check quality before deployment
    if state.get("next_agent") == "devops" and not state.get("review_passed"):
        return "code_review"
```

### Workflow Integration Examples

#### Example 1: Code Generation → Review → Deployment
```python
# User: "Create a new user authentication API"

# 1. Code Generator creates the API
# 2. Code Review automatically triggered
review_results = {
    "score": 7.5,
    "issues": ["missing input validation", "no rate limiting"],
    "coverage": 65
}

# 3. If score < 8, route back to Code Generator with feedback
# 4. Once score >= 8, route to DevOps for deployment
```

#### Example 2: Bug Fix → Review → Test → Deploy
```python
# User: "Fix the memory leak in data processor"

# 1. Navigator finds the code
# 2. Debugger fixes the issue
# 3. Code Review checks the fix
# 4. Tester runs regression tests
# 5. DevOps deploys if all pass
```

### Continuous Learning

Both agents contribute to the system's knowledge:

```python
# Code Review learns patterns
write_file("/knowledge/review_history.json", {
    "common_issues": {
        "missing_error_handling": 45,
        "no_input_validation": 38,
        "hardcoded_values": 22
    },
    "average_scores_by_agent": {
        "code_gen": 8.2,
        "debugger": 8.7,
        "human": 7.9
    }
})

# DevOps learns deployment patterns  
write_file("/knowledge/deployment_patterns.json", {
    "successful_rollouts": 156,
    "rollback_triggers": ["high_error_rate", "memory_spike"],
    "optimal_canary_percentage": 10
})
```

## Benefits of Integration

1. **Quality Gates**: Code Review prevents bad code from reaching production
2. **Automated Deployment**: DevOps removes manual deployment friction
3. **Learning System**: Both agents improve other agents over time
4. **Objective Standards**: Metrics-based reviews remove subjectivity
5. **Fast Feedback**: Immediate reviews accelerate development

These agents transform the system from a coding assistant into a complete software delivery platform., 'yaml_section'),
            (r'^\[(\w+)\]', 'ini_section'),
            (r'^---+\s*(.+)?\s*---+

### Integration with Existing State

```python
# Enhanced AgentState for DevOps
class AgentState(TypedDict):
    messages: Annotated[list, add]
    current_file: str
    project_context: dict
    next_agent: str
    code_analysis: dict
    search_results: dict
    deployment_state: dict  # NEW: Track deployment status
    test_results: dict      # NEW: From tester agent

# DevOps agent reads from other agents' outputs
deployment_state = {
    "last_deployment": "2024-01-15T10:00:00Z",
    "environment": "staging",
    "version": "v1.2.3",
    "rollback_version": "v1.2.2",
    "config_changes": [],
    "infrastructure_changes": []
}
```

## 2. Code Review Agent + Code Metrics Tools

### Overview
The Code Review Agent provides automated, objective code reviews by combining static analysis, metrics calculation, and learned patterns from the codebase. It acts as a senior developer reviewing PRs.

### Integration Points

#### With Existing Agents:
- **After Code Generator**: Review generated code for quality
- **With Navigator**: Understand code context and patterns
- **Before Refactorer**: Identify what needs refactoring
- **With Tester**: Ensure test coverage meets standards
- **Feeds back to all agents**: Provides quality guidelines

#### Memory Integration:
```python
# Code Review agent writes learned patterns
write_file("/knowledge/code_standards.md", """
## Project Code Standards (Learned)
- Average function length: 15 lines
- Naming convention: snake_case for functions
- Test coverage target: 80%
- Max cyclomatic complexity: 10
""")

# Other agents read and follow these standards
```

### Code Review Agent Implementation

```python
async def create_code_review_agent(llm):
    """Code review specialist with metrics analysis"""
    
    client = MultiServerMCPClient({
        "metrics_tools": {
            "transport": "stdio",
            "command": "python",
            "args": ["./mcp_servers/code_metrics_server.py"]
        },
        "static_analysis": {
            "transport": "stdio",
            "command": "python",
            "args": ["./mcp_servers/static_analysis_server.py"]
        }
    })
    
    tools = await client.get_tools()
    
    # Also inherits search tools from navigator
    tools.extend(navigator_tools)
    
    agent = create_react_agent(
        llm,
        tools,
        name="code_review",
        prompt="""You are a senior code reviewer providing objective, metrics-based reviews.

## Integration with Team

1. **Use Navigator**: Find related code for context
   - Check similar implementations
   - Understand project patterns
   
2. **Inform Other Agents**: Document standards
   - Write findings to /knowledge/code_standards.md
   - Update /review/checklist.md

3. **Work with Tester**: Ensure adequate testing
   - Check test coverage
   - Verify edge cases

## Review Process

### 1. Contextual Analysis
- Use navigator to find similar code
- Check project conventions
- Review recent changes in area

### 2. Metrics Collection
- Cyclomatic complexity
- Code duplication
- Test coverage
- Documentation coverage
- Security vulnerabilities

### 3. Pattern Analysis
- Naming consistency
- Error handling patterns
- API consistency
- Design pattern usage

### 4. Constructive Feedback
Rate each aspect:
- **Correctness**: Does it work?
- **Performance**: Is it efficient?
- **Maintainability**: Is it clear?
- **Security**: Is it safe?
- **Testing**: Is it tested?

## Output Format

```markdown
## Code Review Summary

**Overall Score**: 8.5/10

### Strengths
- Clean function separation
- Good error handling
- Comprehensive tests

### Issues Found
1. **High Complexity** (Line 45-67)
   - Cyclomatic complexity: 12
   - Suggestion: Extract method
   
2. **Missing Tests** (Line 89)
   - Uncovered edge case
   - Suggestion: Add test for null input

### Metrics
- Test Coverage: 85%
- Duplication: 2%
- Complexity Average: 4.5
- Documentation: 90%
```

Remember: Be constructive and educational. Explain WHY something should change."""
    )
    
    return agent
```

### Code Metrics MCP Server

```python
# mcp_servers/code_metrics_server.py
from mcp.server.fastmcp import FastMCP
import ast
import radon.complexity
import radon.metrics

mcp = FastMCP("Code Metrics")

@mcp.tool()
def calculate_complexity(file_path: str) -> dict:
    """Calculate cyclomatic complexity"""
    # Returns per-function complexity scores
    # Identifies complex areas needing refactoring

@mcp.tool()
def measure_code_coverage(
    test_command: str = "pytest",
    source_dir: str = "src"
) -> dict:
    """Run tests and measure coverage"""
    # Integrates with pytest-cov, jest coverage, etc.
    # Returns uncovered lines

@mcp.tool()
def detect_duplication(
    path: str = ".",
    threshold: int = 50  # tokens
) -> list:
    """Find duplicate code blocks"""
    # Uses AST comparison
    # Returns similar code segments

@mcp.tool()
def calculate_maintainability(file_path: str) -> dict:
    """Calculate maintainability index"""
    # Combines complexity, lines of code, comments
    # Returns MI score and breakdown

@mcp.tool()
def analyze_dependencies(file_path: str) -> dict:
    """Analyze import dependencies"""
    # Checks coupling
    # Identifies circular dependencies
```

### Static Analysis MCP Server

```python
# mcp_servers/static_analysis_server.py

@mcp.tool()
def run_linter(
    file_path: str,
    linter: str = None,  # auto-detect
    config_file: str = None
) -> list:
    """Run appropriate linter"""
    # pylint, eslint, rubocop, etc.
    # Returns issues with severity

@mcp.tool()
def security_scan(
    path: str,
    language: str = None
) -> list:
    """Scan for security issues"""
    # Bandit for Python, npm audit, etc.
    # Returns vulnerabilities

@mcp.tool()
def check_type_coverage(file_path: str) -> dict:
    """Analyze type annotation coverage"""
    # For Python: mypy coverage
    # For TS/JS: TypeScript coverage

@mcp.tool()
def documentation_coverage(file_path: str) -> dict:
    """Check documentation completeness"""
    # Docstring coverage
    # Public API documentation
    # README completeness
```

### Enhanced Orchestrator Integration

```python
# Additional state for code review workflow
class ReviewState(TypedDict):
    review_requested: bool
    review_results: dict
    quality_threshold: float
    auto_fix_issues: bool

# Orchestrator routing update
def enhanced_supervisor_logic(state):
    """Route based on quality gates"""
    
    if state.get("review_requested"):
        return "code_review"
    
    # Auto-review after code generation
    if state.get("last_agent") == "code_gen" and AUTO_REVIEW_ENABLED:
        return "code_review"
    
    # Check quality before deployment
    if state.get("next_agent") == "devops" and not state.get("review_passed"):
        return "code_review"
```

### Workflow Integration Examples

#### Example 1: Code Generation → Review → Deployment
```python
# User: "Create a new user authentication API"

# 1. Code Generator creates the API
# 2. Code Review automatically triggered
review_results = {
    "score": 7.5,
    "issues": ["missing input validation", "no rate limiting"],
    "coverage": 65
}

# 3. If score < 8, route back to Code Generator with feedback
# 4. Once score >= 8, route to DevOps for deployment
```

#### Example 2: Bug Fix → Review → Test → Deploy
```python
# User: "Fix the memory leak in data processor"

# 1. Navigator finds the code
# 2. Debugger fixes the issue
# 3. Code Review checks the fix
# 4. Tester runs regression tests
# 5. DevOps deploys if all pass
```

### Continuous Learning

Both agents contribute to the system's knowledge:

```python
# Code Review learns patterns
write_file("/knowledge/review_history.json", {
    "common_issues": {
        "missing_error_handling": 45,
        "no_input_validation": 38,
        "hardcoded_values": 22
    },
    "average_scores_by_agent": {
        "code_gen": 8.2,
        "debugger": 8.7,
        "human": 7.9
    }
})

# DevOps learns deployment patterns  
write_file("/knowledge/deployment_patterns.json", {
    "successful_rollouts": 156,
    "rollback_triggers": ["high_error_rate", "memory_spike"],
    "optimal_canary_percentage": 10
})
```

## Benefits of Integration

1. **Quality Gates**: Code Review prevents bad code from reaching production
2. **Automated Deployment**: DevOps removes manual deployment friction
3. **Learning System**: Both agents improve other agents over time
4. **Objective Standards**: Metrics-based reviews remove subjectivity
5. **Fast Feedback**: Immediate reviews accelerate development

These agents transform the system from a coding assistant into a complete software delivery platform., 'separator_section')
        ]
        
        current_indent_stack = []
        
        for i, line in enumerate(lines):
            # Calculate indentation
            indent = len(line) - len(line.lstrip())
            stripped = line.strip()
            
            if not stripped:
                continue
            
            # Check patterns
            for pattern, pattern_type in section_patterns:
                match = re.match(pattern, stripped)
                if match:
                    name = match.group(1) if pattern_type != 'class_definition' else match.group(2)
                    
                    section = {
                        "line": i + 1,
                        "type": pattern_type,
                        "name": name,
                        "indent": indent,
                        "text": stripped
                    }
                    
                    structure["sections"].append(section)
                    
                    # Build outline based on indentation
                    while current_indent_stack and current_indent_stack[-1][1] >= indent:
                        current_indent_stack.pop()
                    
                    level = len(current_indent_stack)
                    if level < max_depth:
                        outline_entry = "  " * level + f"- {name} ({pattern_type})"
                        structure["outline"].append(outline_entry)
                        current_indent_stack.append((name, indent))
                    
                    break
        
        return structure
        
    except Exception as e:
        return {"error": str(e), "file": file_path}

# Helper functions
def format_bytes(size: int) -> str:
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

def is_text_file(file_path: str) -> bool:
    """Check if file is likely text"""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(512)
        return not bool(chunk.translate(None, bytes(range(32, 127))))
    except:
        return False

def count_comment_lines(content: str, file_path: str) -> int:
    """Count comment lines based on file extension"""
    ext = Path(file_path).suffix.lower()
    count = 0
    
    # Common comment patterns
    if ext in ['.py', '.sh', '.yml', '.yaml']:
        count = len([l for l in content.splitlines() if l.strip().startswith('#')])
    elif ext in ['.js', '.java', '.c', '.cpp', '.go', '.rs']:
        count = len([l for l in content.splitlines() if l.strip().startswith('//')])
        # Also count /* */ blocks
        count += content.count('/*')
    elif ext in ['.html', '.xml']:
        count += content.count('<!--')
    
    return count

def count_import_lines(content: str, file_path: str) -> int:
    """Count import statements"""
    ext = Path(file_path).suffix.lower()
    lines = content.splitlines()
    count = 0
    
    if ext == '.py':
        count = len([l for l in lines if l.strip().startswith(('import ', 'from '))])
    elif ext in ['.js', '.ts']:
        count = len([l for l in lines if re.match(r'^\s*(import|require)', l)])
    elif ext == '.java':
        count = len([l for l in lines if l.strip().startswith('import ')])
    elif ext == '.go':
        in_import = False
        for line in lines:
            if line.strip() == 'import (':
                in_import = True
            elif in_import and line.strip() == ')':
                in_import = False
            elif line.strip().startswith('import '):
                count += 1
            elif in_import:
                count += 1
    
    return count

def count_function_definitions(content: str, file_path: str) -> int:
    """Count function definitions"""
    ext = Path(file_path).suffix.lower()
    
    if ext == '.py':
        return len(re.findall(r'^\s*def\s+\w+', content, re.MULTILINE))
    elif ext in ['.js', '.ts']:
        # Various JS function patterns
        patterns = [
            r'^\s*function\s+\w+',
            r'^\s*const\s+\w+\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=]+)\s*=>',
            r'^\s*(?:export\s+)?(?:async\s+)?function\s+\w+'
        ]
        return sum(len(re.findall(p, content, re.MULTILINE)) for p in patterns)
    elif ext == '.java':
        return len(re.findall(r'^\s*(?:public|private|protected)?\s*(?:static)?\s*\w+\s+\w+\s*\(', content, re.MULTILINE))
    elif ext == '.go':
        return len(re.findall(r'^\s*func\s+', content, re.MULTILINE))
    
    return 0

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Integration with Existing State

```python
# Enhanced AgentState for DevOps
class AgentState(TypedDict):
    messages: Annotated[list, add]
    current_file: str
    project_context: dict
    next_agent: str
    code_analysis: dict
    search_results: dict
    deployment_state: dict  # NEW: Track deployment status
    test_results: dict      # NEW: From tester agent

# DevOps agent reads from other agents' outputs
deployment_state = {
    "last_deployment": "2024-01-15T10:00:00Z",
    "environment": "staging",
    "version": "v1.2.3",
    "rollback_version": "v1.2.2",
    "config_changes": [],
    "infrastructure_changes": []
}
```

## 2. Code Review Agent + Code Metrics Tools

### Overview
The Code Review Agent provides automated, objective code reviews by combining static analysis, metrics calculation, and learned patterns from the codebase. It acts as a senior developer reviewing PRs.

### Integration Points

#### With Existing Agents:
- **After Code Generator**: Review generated code for quality
- **With Navigator**: Understand code context and patterns
- **Before Refactorer**: Identify what needs refactoring
- **With Tester**: Ensure test coverage meets standards
- **Feeds back to all agents**: Provides quality guidelines

#### Memory Integration:
```python
# Code Review agent writes learned patterns
write_file("/knowledge/code_standards.md", """
## Project Code Standards (Learned)
- Average function length: 15 lines
- Naming convention: snake_case for functions
- Test coverage target: 80%
- Max cyclomatic complexity: 10
""")

# Other agents read and follow these standards
```

### Code Review Agent Implementation

```python
async def create_code_review_agent(llm):
    """Code review specialist with metrics analysis"""
    
    client = MultiServerMCPClient({
        "metrics_tools": {
            "transport": "stdio",
            "command": "python",
            "args": ["./mcp_servers/code_metrics_server.py"]
        },
        "static_analysis": {
            "transport": "stdio",
            "command": "python",
            "args": ["./mcp_servers/static_analysis_server.py"]
        }
    })
    
    tools = await client.get_tools()
    
    # Also inherits search tools from navigator
    tools.extend(navigator_tools)
    
    agent = create_react_agent(
        llm,
        tools,
        name="code_review",
        prompt="""You are a senior code reviewer providing objective, metrics-based reviews.

## Integration with Team

1. **Use Navigator**: Find related code for context
   - Check similar implementations
   - Understand project patterns
   
2. **Inform Other Agents**: Document standards
   - Write findings to /knowledge/code_standards.md
   - Update /review/checklist.md

3. **Work with Tester**: Ensure adequate testing
   - Check test coverage
   - Verify edge cases

## Review Process

### 1. Contextual Analysis
- Use navigator to find similar code
- Check project conventions
- Review recent changes in area

### 2. Metrics Collection
- Cyclomatic complexity
- Code duplication
- Test coverage
- Documentation coverage
- Security vulnerabilities

### 3. Pattern Analysis
- Naming consistency
- Error handling patterns
- API consistency
- Design pattern usage

### 4. Constructive Feedback
Rate each aspect:
- **Correctness**: Does it work?
- **Performance**: Is it efficient?
- **Maintainability**: Is it clear?
- **Security**: Is it safe?
- **Testing**: Is it tested?

## Output Format

```markdown
## Code Review Summary

**Overall Score**: 8.5/10

### Strengths
- Clean function separation
- Good error handling
- Comprehensive tests

### Issues Found
1. **High Complexity** (Line 45-67)
   - Cyclomatic complexity: 12
   - Suggestion: Extract method
   
2. **Missing Tests** (Line 89)
   - Uncovered edge case
   - Suggestion: Add test for null input

### Metrics
- Test Coverage: 85%
- Duplication: 2%
- Complexity Average: 4.5
- Documentation: 90%
```

Remember: Be constructive and educational. Explain WHY something should change."""
    )
    
    return agent
```

### Code Metrics MCP Server

```python
# mcp_servers/code_metrics_server.py
from mcp.server.fastmcp import FastMCP
import ast
import radon.complexity
import radon.metrics

mcp = FastMCP("Code Metrics")

@mcp.tool()
def calculate_complexity(file_path: str) -> dict:
    """Calculate cyclomatic complexity"""
    # Returns per-function complexity scores
    # Identifies complex areas needing refactoring

@mcp.tool()
def measure_code_coverage(
    test_command: str = "pytest",
    source_dir: str = "src"
) -> dict:
    """Run tests and measure coverage"""
    # Integrates with pytest-cov, jest coverage, etc.
    # Returns uncovered lines

@mcp.tool()
def detect_duplication(
    path: str = ".",
    threshold: int = 50  # tokens
) -> list:
    """Find duplicate code blocks"""
    # Uses AST comparison
    # Returns similar code segments

@mcp.tool()
def calculate_maintainability(file_path: str) -> dict:
    """Calculate maintainability index"""
    # Combines complexity, lines of code, comments
    # Returns MI score and breakdown

@mcp.tool()
def analyze_dependencies(file_path: str) -> dict:
    """Analyze import dependencies"""
    # Checks coupling
    # Identifies circular dependencies
```

### Static Analysis MCP Server

```python
# mcp_servers/static_analysis_server.py

@mcp.tool()
def run_linter(
    file_path: str,
    linter: str = None,  # auto-detect
    config_file: str = None
) -> list:
    """Run appropriate linter"""
    # pylint, eslint, rubocop, etc.
    # Returns issues with severity

@mcp.tool()
def security_scan(
    path: str,
    language: str = None
) -> list:
    """Scan for security issues"""
    # Bandit for Python, npm audit, etc.
    # Returns vulnerabilities

@mcp.tool()
def check_type_coverage(file_path: str) -> dict:
    """Analyze type annotation coverage"""
    # For Python: mypy coverage
    # For TS/JS: TypeScript coverage

@mcp.tool()
def documentation_coverage(file_path: str) -> dict:
    """Check documentation completeness"""
    # Docstring coverage
    # Public API documentation
    # README completeness
```

### Enhanced Orchestrator Integration

```python
# Additional state for code review workflow
class ReviewState(TypedDict):
    review_requested: bool
    review_results: dict
    quality_threshold: float
    auto_fix_issues: bool

# Orchestrator routing update
def enhanced_supervisor_logic(state):
    """Route based on quality gates"""
    
    if state.get("review_requested"):
        return "code_review"
    
    # Auto-review after code generation
    if state.get("last_agent") == "code_gen" and AUTO_REVIEW_ENABLED:
        return "code_review"
    
    # Check quality before deployment
    if state.get("next_agent") == "devops" and not state.get("review_passed"):
        return "code_review"
```

### Workflow Integration Examples

#### Example 1: Code Generation → Review → Deployment
```python
# User: "Create a new user authentication API"

# 1. Code Generator creates the API
# 2. Code Review automatically triggered
review_results = {
    "score": 7.5,
    "issues": ["missing input validation", "no rate limiting"],
    "coverage": 65
}

# 3. If score < 8, route back to Code Generator with feedback
# 4. Once score >= 8, route to DevOps for deployment
```

#### Example 2: Bug Fix → Review → Test → Deploy
```python
# User: "Fix the memory leak in data processor"

# 1. Navigator finds the code
# 2. Debugger fixes the issue
# 3. Code Review checks the fix
# 4. Tester runs regression tests
# 5. DevOps deploys if all pass
```

### Continuous Learning

Both agents contribute to the system's knowledge:

```python
# Code Review learns patterns
write_file("/knowledge/review_history.json", {
    "common_issues": {
        "missing_error_handling": 45,
        "no_input_validation": 38,
        "hardcoded_values": 22
    },
    "average_scores_by_agent": {
        "code_gen": 8.2,
        "debugger": 8.7,
        "human": 7.9
    }
})

# DevOps learns deployment patterns  
write_file("/knowledge/deployment_patterns.json", {
    "successful_rollouts": 156,
    "rollback_triggers": ["high_error_rate", "memory_spike"],
    "optimal_canary_percentage": 10
})
```

## Benefits of Integration

1. **Quality Gates**: Code Review prevents bad code from reaching production
2. **Automated Deployment**: DevOps removes manual deployment friction
3. **Learning System**: Both agents improve other agents over time
4. **Objective Standards**: Metrics-based reviews remove subjectivity
5. **Fast Feedback**: Immediate reviews accelerate development

These agents transform the system from a coding assistant into a complete software delivery platform.