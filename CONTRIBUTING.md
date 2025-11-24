# Contributing to DeepAgent Coding Assistant

Thank you for your interest in contributing to DeepAgent Coding Assistant! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Quality Standards](#code-quality-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Branch Strategy](#branch-strategy)
- [Commit Guidelines](#commit-guidelines)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a positive environment
- Report unacceptable behavior to project maintainers

## Getting Started

### Prerequisites

- Python 3.11+ installed
- [uv](https://github.com/astral-sh/uv) package manager
- [Ollama](https://ollama.ai/) for local LLM testing
- Node.js/npm for MCP server
- Git

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/deepagent-claude.git
   cd deepagent-claude
   ```

2. **Install dependencies:**
   ```bash
   # Install uv if you don't have it
   pip install uv

   # Install project dependencies including dev tools
   uv sync --all-extras --dev
   ```

3. **Install pre-commit hooks:**
   ```bash
   uv run pre-commit install
   ```

4. **Pull required Ollama models:**
   ```bash
   ollama pull qwen2.5-coder:latest
   ollama pull codellama:13b-code
   ollama pull llama3.1:8b
   ```

5. **Verify setup:**
   ```bash
   # Run tests
   uv run pytest

   # Run linting
   uv run ruff check src/ tests/

   # Check formatting
   uv run black --check src/ tests/
   ```

## Development Workflow

We follow the **Git Flow** branching model:

### Branch Strategy

- `main` - Production-ready code, tagged releases only
- `develop` - Integration branch for features
- `feature/*` - New features (branch from `develop`)
- `bugfix/*` - Bug fixes (branch from `develop`)
- `hotfix/*` - Critical fixes (branch from `main`)
- `release/*` - Release preparation (branch from `develop`)

### Creating a Feature Branch

```bash
# Ensure you're on develop and up to date
git checkout develop
git pull origin develop

# Create your feature branch
git checkout -b feature/your-feature-name

# Make your changes and commit
git add .
git commit -m "feat: add amazing feature"

# Push to your fork
git push origin feature/your-feature-name
```

## Code Quality Standards

### Code Formatting

We use **Black** for code formatting:

```bash
# Format code
uv run black src/ tests/

# Check formatting
uv run black --check src/ tests/
```

**Configuration:**
- Line length: 100 characters
- Python version: 3.11+

### Linting

We use **Ruff** for linting:

```bash
# Run linter
uv run ruff check src/ tests/

# Fix auto-fixable issues
uv run ruff check --fix src/ tests/
```

**Enabled rules:**
- `E/W` - pycodestyle errors and warnings
- `F` - pyflakes
- `I` - isort (import sorting)
- `B` - flake8-bugbear
- `C4` - flake8-comprehensions
- `UP` - pyupgrade
- `ARG` - flake8-unused-arguments
- `SIM` - flake8-simplify

### Type Checking

We use **mypy** for static type checking:

```bash
# Run type checker
uv run mypy src/deepagent_claude
```

### Pre-commit Hooks

All code quality checks run automatically on commit:

- Trailing whitespace removal
- End of file fixer
- YAML/JSON/TOML validation
- Large file check
- Black formatting
- Ruff linting
- Mypy type checking
- pytest test suite

To run pre-commit manually:
```bash
uv run pre-commit run --all-files
```

## Testing Requirements

### Test Coverage

- **Minimum coverage: 80%**
- All new features must include tests
- Bug fixes must include regression tests
- Tests must be meaningful and not just for coverage

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/deepagent_claude --cov-report=html

# Run specific test file
uv run pytest tests/core/test_model_selector.py -v

# Run tests matching pattern
uv run pytest -k "test_model" -v

# Run tests in parallel (faster)
uv run pytest -n auto
```

### Writing Tests

We follow **Test-Driven Development (TDD)**:

1. Write the test first (RED)
2. Write minimal code to pass (GREEN)
3. Refactor and improve (REFACTOR)

**Example:**

```python
import pytest
from deepagent_claude.core.model_selector import ModelSelector

def test_model_selector_initialization():
    """Test that ModelSelector initializes with default models"""
    selector = ModelSelector()
    assert selector.get_model("main_agent") is not None
    assert selector.get_model("main_agent").model_name == "qwen2.5-coder:latest"

@pytest.mark.asyncio
async def test_model_selector_custom_model():
    """Test that custom models can be configured"""
    selector = ModelSelector()
    selector.configure_model("test_agent", "llama3.1:8b", temperature=0.5)
    model = selector.get_model("test_agent")
    assert model.model_name == "llama3.1:8b"
```

### Test Organization

```
tests/
├── core/              # Core component tests
├── middleware/        # Middleware tests
├── utils/             # Utility tests
├── integration/       # Integration tests
└── fixtures/          # Shared test fixtures
```

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass:**
   ```bash
   uv run pytest
   ```

2. **Check code quality:**
   ```bash
   uv run ruff check src/ tests/
   uv run black --check src/ tests/
   uv run mypy src/deepagent_claude
   ```

3. **Verify coverage:**
   ```bash
   uv run pytest --cov=src/deepagent_claude --cov-fail-under=80
   ```

4. **Update documentation:**
   - Update README.md if needed
   - Update CHANGELOG.md with your changes
   - Add docstrings to new functions/classes

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests written and passing (coverage ≥ 80%)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commits follow conventional commit format
- [ ] PR description is clear and complete
- [ ] Linked to related issues (if any)

### PR Title Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat: add new feature`
- `fix: resolve bug in model selector`
- `docs: update contributing guide`
- `test: add tests for session manager`
- `refactor: improve error handling`
- `chore: update dependencies`
- `ci: fix GitHub Actions workflow`

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Tests pass
- [ ] Code formatted
- [ ] Linting clean
- [ ] Coverage ≥ 80%
- [ ] Documentation updated
```

### Review Process

1. Automated CI checks must pass
2. At least one maintainer approval required
3. No unresolved conversations
4. Branch up to date with base branch

## Commit Guidelines

### Conventional Commits

Format: `<type>(<scope>): <subject>`

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Code style (formatting, missing semi-colons, etc.)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks
- `ci` - CI/CD changes
- `perf` - Performance improvements

**Examples:**
```bash
feat(mcp): add support for filesystem tools
fix(agent): resolve path resolution issue on macOS
docs(readme): add installation instructions
test(middleware): add tests for logging middleware
refactor(core): improve error handling
```

### Commit Best Practices

- Keep commits atomic (one logical change per commit)
- Write clear, concise commit messages
- Use present tense ("add feature" not "added feature")
- Reference issues when applicable (`fixes #123`)
- Break large changes into smaller commits

## Development Tips

### Debugging

```bash
# Run with verbose logging
uv run python -m deepagent_claude.main run --verbose "your request"

# Run pytest with output
uv run pytest -v -s

# Use debugger
uv run python -m pdb -m deepagent_claude.main
```

### Local Testing

```bash
# Test agent locally
uv run python -m deepagent_claude.main run --workspace /tmp/test "Create hello.txt"

# Test in interactive mode
uv run python -m deepagent_claude.main chat
```

### Performance Profiling

```bash
# Profile code
uv run python -m cProfile -o profile.stats -m deepagent_claude.main run "request"

# View profile
uv run python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('time').print_stats(20)"
```

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/yourusername/deepagent-claude/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/deepagent-claude/discussions)
- **Documentation:** [Project Wiki](https://github.com/yourusername/deepagent-claude/wiki)

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- GitHub contributors page

Thank you for contributing! 🎉
