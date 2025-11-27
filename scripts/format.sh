#!/bin/bash
# Format and fix all Python files in the project

set -e

echo "🔧 Running auto-formatters and fixers..."
echo ""

echo "1️⃣  Running Black (code formatter)..."
uv run black src/ tests/ --line-length=100

echo ""
echo "2️⃣  Running isort (import sorter)..."
uv run isort src/ tests/ --profile=black --line-length=100

echo ""
echo "3️⃣  Running Ruff (linter with auto-fix)..."
uv run ruff check src/ tests/ --fix

echo ""
echo "✅ All formatting and fixes complete!"
echo ""
echo "💡 Tip: Run 'uv run pre-commit run --all-files' to verify everything passes"
