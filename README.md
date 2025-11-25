# DeepAgent Coding Assistant

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/adam-hanna/deepagent-coder/releases/tag/v1.0.0)
[![Python](https://img.shields.io/badge/python-3.13+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-266%20passing-brightgreen.svg)](tests/)

A production-ready AI coding assistant. Built with DeepAgent architecture, Ollama local LLMs, and Model Context Protocol (MCP) for filesystem operations.

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- [Ollama](https://ollama.ai/) running locally
- Node.js/npm (for MCP filesystem server)

### Installation

```bash
# Clone the repository
git clone git@github.com:adam-hanna/deepagent-coder.git
cd deepagent-coder

# Install dependencies using uv
pip install uv
uv sync

# Pull required Ollama models
ollama pull qwen2.5-coder:latest
ollama pull codellama:13b-code
ollama pull llama3.1:8b
ollama serve
```

### Usage

**Interactive chat mode:**
```bash
uv run python -m deepagent_coder.main chat
```

**Single command with workspace:**
```bash
uv run python -m deepagent_coder.main run --workspace /tmp/my-api "Create a Node.js TODO REST API with Express. Include package.json, server.js with CRUD endpoints, and README.md"
```

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│         CLI Interface               │
│  • Interactive chat mode            │
│  • Single request execution         │
│  • Progress tracking                │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│      CodingDeepAgent Core           │
│  • Task orchestration               │
│  • LLM + MCP tool integration       │
│  • JSON tool call parsing           │
│  • Multi-file creation loop         │
└─────────────┬───────────────────────┘
              │
        ┌─────┴─────┬─────────┬───────┬────────┬────────┬──────────┐
        ▼           ▼         ▼       ▼        ▼        ▼          ▼
    ┌───────┐  ┌────────┐ ┌─────┐ ┌────────┐ ┌──────┐ ┌──────┐ ┌────────┐
    │CodeGen│  │Debugger│ │Test │ │Refactor│ │DevOps│ │Review│ │CodeNav │
    │       │  │        │ │Writer│ │        │ │      │ │      │ │        │
    └───────┘  └────────┘ └─────┘ └────────┘ └──────┘ └──────┘ └────────┘
        │           │         │       │          │        │          │
        └───────────┴─────────┴───────┴──────────┴────────┴──────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   Middleware Stack    │
        │  • Memory compaction  │
        │  • Git safety         │
        │  • Error recovery     │
        │  • Logging & audit    │
        └───────────┬───────────┘
                    │
              ┌─────┴─────┐
              ▼           ▼
     ┌──────────────┐  ┌───────────────┐
     │MCP Filesystem│  │  MCP Servers  │
     │• write_file  │  │• Container    │
     │• read_file   │  │• Build Tools  │
     │• directory   │  │• Code Metrics │
     └──────────────┘  └───────────────┘
```

## 🔧 Technical Details

### How It Works

1. **Ollama Model Integration**: Uses local LLMs that don't natively support tool calling
2. **Custom JSON Parser**: Extracts tool calls from LLM text output using dual-strategy parsing
3. **Path Resolution**: Converts relative paths (`./file.txt`) to absolute workspace paths
4. **Symlink Handling**: Resolves macOS symlinks (`/tmp` → `/private/tmp`) automatically
5. **Agent Loop**: Iterates up to 10 times to complete multi-file creation tasks
6. **MCP Tools**: Executes filesystem operations through standardized protocol

### JSON Parsing Strategies

The agent uses two strategies to extract tool calls from Ollama model output:

**Strategy 1**: Parse entire response as JSON array
```json
[
  {"name": "write_file", "arguments": {"path": "./file1.txt", "content": "..."}},
  {"name": "write_file", "arguments": {"path": "./file2.txt", "content": "..."}}
]
```

**Strategy 2**: Extract individual JSON objects with balanced brace matching
```
{"name": "write_file", "arguments": {...}}
{"name": "write_file", "arguments": {...}}
```

### Project Structure

```
deepagent-coder/
├── src/deepagent_coder/
│   ├── core/
│   │   ├── model_selector.py      # Model configuration
│   │   ├── mcp_client.py          # MCP client manager
│   │   └── session_manager.py     # Session persistence
│   ├── middleware/
│   │   ├── logging_middleware.py
│   │   ├── memory_middleware.py
│   │   ├── git_safety_middleware.py
│   │   ├── error_recovery_middleware.py
│   │   └── audit_middleware.py
│   ├── utils/
│   │   └── file_organizer.py      # Workspace organization
│   ├── coding_agent.py            # Main agent orchestration
│   └── main.py                    # CLI entry point
├── tests/                         # 266 passing tests
│   ├── core/
│   ├── middleware/
│   ├── subagents/
│   └── utils/
├── CHANGELOG.md                   # Version history
├── pyproject.toml                 # Dependencies
└── README.md
```

## ⚙️ Configuration

### Model Configuration

Edit `src/deepagent_coder/core/model_selector.py`:

```python
self.model_configs = {
    "main_agent": {
        "model": "qwen2.5-coder:latest",  # Main coding model
        "temperature": 0.3,
        "num_ctx": 32768,
    },
    "code_generator": {
        "model": "codellama:13b-code",    # Code generation
        "temperature": 0.2,
        "num_ctx": 16384,
    },
    "summarizer": {
        "model": "llama3.1:8b",           # Memory compaction
        "temperature": 0.4,
        "num_ctx": 8192,
    }
}
```

### Workspace Configuration

**Default workspace**: `~/.deepagents/workspace`

**Custom workspace**:
```bash
uv run python -m deepagent_coder.main run \
  --workspace /path/to/workspace \
  "Your request"
```

**Important**: Workspace paths are automatically resolved to handle symlinks on macOS.

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/deepagent_coder --cov-report=html

# Run specific test file
uv run pytest tests/core/test_session_manager.py -v

# Run tests matching pattern
uv run pytest -k "test_write_file"
```

**Test Coverage**: 266+ passing tests (73% coverage) covering:
- Core components (model selector, MCP client, session manager)
- Middleware stack (logging, memory, git safety, error recovery, audit)
- MCP servers (container tools, code metrics, static analysis, build tools)
- Subagents (code generation, debugging, testing, refactoring, DevOps, code review, navigation)
- Utilities (file organizer, memory compactor, session manager)
- Integration tests (full agent workflows, DevOps and code review integration)

## 🐛 Troubleshooting

### Issue: "Access denied - path outside allowed directories"

**Cause**: Path resolution issue or MCP server not configured for workspace

**Fix**: Ensure workspace path is resolved correctly. The agent automatically handles this.

### Issue: "Failed to get MCP tools"

**Cause**: MCP filesystem server not running or npx not available

**Fix**:
```bash
# Install Node.js and npm
# Verify npx is available
npx --version

# Test MCP server manually
npx -y @modelcontextprotocol/server-filesystem /tmp/test
```

### Issue: "No tool calls found in content"

**Cause**: Ollama model not generating valid JSON or different output format

**Fix**: Try a different model or check Ollama logs:
```bash
ollama list  # Check available models
ollama pull qwen2.5-coder:latest  # Pull recommended model
```

### Issue: Agent creates only one file at a time

**Cause**: Model not following multi-file format instructions

**Fix**: Be explicit in your request:
```bash
"Create THREE files: package.json, server.js, and README.md"
```

## 📊 Performance

- **Startup Time**: ~5-10 seconds (MCP server initialization)
- **Simple File Creation**: ~2-5 seconds
- **Multi-File Project**: ~10-30 seconds (3-5 files)
- **Memory Usage**: ~2GB (Ollama + Python + MCP server)
- **Agent Loop Limit**: 10 iterations per request

## 🔒 Known Limitations

- Filesystem operations only (no command execution yet)
- Agent loop limited to 10 iterations
- Requires Ollama running locally
- Models must generate valid JSON for tool calls
- macOS symlink handling required for `/tmp` directory

## 📦 Dependencies

**Core:**
- `langchain-ollama`: LLM integration
- `langchain-mcp-adapters`: MCP protocol support
- `pydantic`: Data validation

**Development:**
- `pytest`: Testing framework
- `pytest-asyncio`: Async test support
- `pytest-mock`: Mocking utilities
- `pytest-cov`: Coverage reporting

**MCP Server:**
- `@modelcontextprotocol/server-filesystem`: File operations via npx

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`uv run pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) - Local LLM inference
- [Model Context Protocol](https://modelcontextprotocol.io/) - Standardized tool access
- [LangChain](https://www.langchain.com/) - LLM framework
- [DeepAgent](https://github.com/deepagents/deepagents) - Multi-agent architecture pattern

## 📞 Support

- 🐛 [Report a bug](https://github.com/adam-hanna/deepagent-coder/issues/new?labels=bug)
- 💡 [Request a feature](https://github.com/adam-hanna/deepagent-coder/issues/new?labels=enhancement)
- 📖 [Read the docs](https://github.com/adam-hanna/deepagent-coder/wiki)
- 💬 [Join discussions](https://github.com/adam-hanna/deepagent-coder/discussions)

---

**Built with ❤️ using Ollama, MCP, and the DeepAgent architecture pattern**
