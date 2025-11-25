#!/bin/bash
# Setup script for DeepAgent Coding Assistant

set -e

echo "🚀 Setting up DeepAgent Coding Assistant..."

# Check for Python 3.11+
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.11+ is required but not found"
    exit 1
fi

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Check for Ollama
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not found. Install from https://ollama.ai/"
    echo "   After installing, run: ollama pull qwen2.5-coder:7b"
else
    echo "✅ Ollama found"

    # Pull default model
    echo "📥 Pulling qwen2.5-coder:7b model..."
    ollama pull qwen2.5-coder:7b
fi

# Create workspace directory
mkdir -p ~/.deepagents/workspace

echo "✅ Setup complete!"
echo ""
echo "To start DeepAgent:"
echo "  uv run python -m deepagent_coder.main chat"
echo ""
echo "For help:"
echo "  uv run python -m deepagent_coder.main --help"
