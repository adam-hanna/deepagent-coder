# DeepAgent Coding Assistant

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/adam-hanna/deepagent-coder/releases/tag/v1.0.0)
[![Python](https://img.shields.io/badge/python-3.13+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-315%20passing-brightgreen.svg)](tests/)

An AI coding assistant built with 100% Python. Features DeepAgent architecture, Ollama local LLMs, and Model Context Protocol (MCP) for filesystem operations - no Node.js dependencies required.

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- [Ollama](https://ollama.ai/) running locally

### Installation

```bash
# Clone the repository
git clone git@github.com:adam-hanna/deepagent-coder.git
cd deepagent-coder

# Install dependencies using uv
pip install uv
uv sync

# Pull required Ollama models
ollama pull qwen2.5:14b          # Main agent (orchestration & conversation)
ollama pull codellama:13b-code   # Code generation specialist
ollama pull llama3.1:8b          # Summarization specialist
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

**With custom configuration:**
```bash
uv run python -m deepagent_coder.main run --config ./my-config.yaml "Your request"
```

### Docker Setup (Alternative)

**Quick start with Docker Compose:**
```bash
# Clone the repository
git clone git@github.com:adam-hanna/deepagent-coder.git
cd deepagent-coder

# Start services (automatically pulls required models)
docker-compose up -d

# Run commands
docker-compose run deepagent run --workspace /workspace "Your request"

# Interactive chat mode
docker-compose run deepagent chat
```

**What happens on startup:**
1. Ollama service starts with GPU support
2. Required models are automatically pulled:
   - `qwen2.5:14b` (main agent)
   - `codellama:13b-code` (code generator)
   - `llama3.1:8b` (summarizer)
3. DeepAgent starts with models ready to use

**Requirements:**
- Docker and Docker Compose
- NVIDIA GPU with drivers (for GPU acceleration)
- Docker NVIDIA runtime configured

**Note**: First startup may take 10-15 minutes to download models (~20GB total).

## ⚙️ Configuration

DeepAgent uses a flexible YAML-based configuration system with hierarchical priority:

**Priority Order (highest to lowest):**
1. CLI flags (`--model`, `--workspace`, `--config`)
2. Environment variables (`DEEPAGENT_*`)
3. Project config (`.deepagent.yaml` in current directory)
4. User config (`~/.config/deepagent/config.yaml`)
5. Built-in defaults

### Quick Start with Configuration

**Create a project-specific config:**
```bash
cp config.example.yaml .deepagent.yaml
# Edit .deepagent.yaml with your preferences
```

**Create a user-level config:**
```bash
mkdir -p ~/.config/deepagent
cp config.example.yaml ~/.config/deepagent/config.yaml
# Edit ~/.config/deepagent/config.yaml
```

### Key Configuration Options

**Models** - Configure all 8 agent roles:
```yaml
models:
  # Main agent uses generalist model for better orchestration
  main_agent:
    model: "qwen2.5:14b"
    temperature: 0.3
    num_ctx: 32768
  # Subagents use specialized coding models
  code_generator:
    model: "codellama:13b-code"
    temperature: 0.2
  # ... 6 more roles
```

**Middleware** - Control system behavior:
```yaml
middleware:
  memory:
    threshold: 6000  # Token threshold for memory management
  git_safety:
    enforce: false   # Warn or block unsafe git operations
  error_recovery:
    max_retries: 3   # Automatic retry attempts
```

**Quality Gates** - Enforce code quality:
```yaml
quality:
  min_quality_score: 7.5           # 0-10 scale
  test_coverage:
    minimum_percentage: 80
    enforce: true
  complexity:
    max_cyclomatic_complexity: 10
```

**Environment Variables:**
```bash
export DEEPAGENT_MODEL="your-model:latest"
export DEEPAGENT_WORKSPACE="/custom/workspace"
export DEEPAGENT_LOG_LEVEL="DEBUG"
export DEEPAGENT_MAX_RETRIES=5
```

### Full Configuration Reference

See [config.example.yaml](config.example.yaml) for a complete annotated configuration file with all available options including:

- Workspace settings
- Model configurations (8 agent roles)
- Middleware stack settings
- MCP server configuration
- Code quality thresholds
- Performance tuning
- Chat mode settings
- Feature flags

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
├── tests/                         # 315 passing tests
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

**Test Coverage**: 315+ passing tests (73% coverage) covering:
- Core components (model selector, MCP client, session manager, configuration)
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

**Cause**: Python MCP filesystem server failed to start

**Fix**:
```bash
# Verify Python is available
python --version

# Test filesystem server manually
python src/deepagent_coder/mcp_servers/filesystem_server.py
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
- `fastmcp`: Python MCP server framework for filesystem operations

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`uv run pytest`)
5. **Format and fix code** (see below for auto-fix options)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Quality & Auto-Fix

**Pre-commit hooks are already configured with auto-fix enabled!** When you commit, the following tools will automatically fix issues:
- **Black**: Auto-formats Python code
- **isort**: Auto-sorts imports
- **Ruff**: Auto-fixes linting issues

**Manual formatting before commit:**
```bash
# Run all formatters and fixers
./scripts/format.sh

# Or run individually:
uv run black src/ tests/ --line-length=100
uv run isort src/ tests/ --profile=black --line-length=100
uv run ruff check src/ tests/ --fix
```

**Verify everything passes:**
```bash
uv run pre-commit run --all-files
```

**Install pre-commit hooks** (if not already installed):
```bash
uv run pre-commit install
```

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
