# Changelog

All notable changes to the DeepAgent Coding Assistant project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-24

### Added
- **Full Ollama Integration**: Native support for Ollama models (qwen2.5-coder, codellama, llama3.1)
- **MCP Tool Execution**: Complete Model Context Protocol integration with filesystem tools
- **JSON Tool Call Parsing**: Custom parser for Ollama models that output JSON as text
- **Multi-File Creation**: Agent can create multiple files in a single request via iterative loop
- **Path Normalization**: Automatic conversion of relative paths to absolute workspace paths
- **Model Selector**: Configure different models for different agent roles
- **Middleware Stack**: Logging, memory management, git safety, error recovery, and audit middleware
- **File Organization**: Automatic workspace and session management
- **Session Manager**: Track and manage agent sessions with persistent storage
- **Complete Test Suite**: 132 passing tests with 100% TDD methodology

### Features
- Create complete projects (package.json, source files, README) in one command
- Support for Node.js, Python, and general coding tasks
- Workspace isolation with resolved symlink handling (macOS compatible)
- Comprehensive error handling and recovery
- Audit trail for all agent actions
- Memory compaction when context limits approached

### Technical Details
- **Architecture**: DeepAgent pattern with specialized subagents
- **Tool Integration**: MCP filesystem server with write_file, read_file, list_directory
- **LLM Support**: Works with Ollama models that don't support native tool calling
- **Path Resolution**: Handles /tmp → /private/tmp symlinks on macOS
- **JSON Parsing**: Dual-strategy parsing for both array and individual object formats

### Verified Working Examples
- ✅ Simple file creation (hello.txt)
- ✅ Complete Node.js REST API with Express
  - package.json with dependencies
  - server.js with CRUD endpoints
  - README.md with documentation
- ✅ Multi-file projects with proper organization

### Known Limitations
- Requires Ollama running locally
- Limited to filesystem operations (no command execution yet)
- Agent loop limited to 10 iterations per request
- Models must generate valid JSON for tool calls

### Dependencies
- Python 3.13+
- Ollama with qwen2.5-coder:latest (or compatible model)
- Node.js/npm (for MCP filesystem server)
- langchain-ollama
- langchain-mcp-adapters

[1.0.0]: https://github.com/yourusername/deepagent-claude/releases/tag/v1.0.0
