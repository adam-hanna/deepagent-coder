#!/bin/bash
# System validation script for DeepAgent Coding Assistant

set -e

echo "🔍 Running system validation..."
echo ""

# Check Python version
echo "✓ Checking Python version..."
python3 --version

# Check uv
echo "✓ Checking uv installation..."
uv --version

# Run test suite
echo "✓ Running test suite..."
uv run pytest --tb=short -q

# Check code formatting
echo "✓ Checking code style..."
uv run ruff check src/ || true

# Check type hints
echo "✓ Checking type hints..."
uv run mypy src/deepagent_claude --ignore-missing-imports || true

# Verify directory structure
echo "✓ Checking directory structure..."
for dir in src/deepagent_claude/{cli,core,middleware,mcp_servers,subagents,utils}; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir"
    else
        echo "  ✗ $dir (missing)"
    fi
done

# Count implementations
echo ""
echo "📊 Implementation Statistics:"
echo "  Python files: $(find src/ -name "*.py" | wc -l)"
echo "  Test files: $(find tests/ -name "*.py" | wc -l)"
echo "  Lines of code: $(find src/ -name "*.py" -exec wc -l {} + | tail -1 | awk '{print $1}')"

echo ""
echo "✅ Validation complete!"
