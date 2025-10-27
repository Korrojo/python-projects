#!/bin/bash
# Pre-push validation script
# Run this before pushing to main or creating PRs

set -e  # Exit on any error

echo "=== Pre-Push Validation ==="
echo ""

# 1. Check if venv is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "❌ Virtual environment not activated!"
    echo "   Run: source .venv311/bin/activate"
    exit 1
fi
echo "✅ Virtual environment: $VIRTUAL_ENV"

# 2. Run linting (catches N999 and formatting issues)
echo ""
echo "Running code quality checks..."
./scripts/lint.sh
if [ $? -ne 0 ]; then
    echo "❌ Linting failed! Fix issues before pushing."
    exit 1
fi
echo "✅ Code quality checks passed"

# 3. Run tests
echo ""
echo "Running tests..."
pytest -q --maxfail=1 --disable-warnings -m "not integration"
if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Fix tests before pushing."
    exit 1
fi
echo "✅ Tests passed"

# 4. Check for common cross-platform issues
echo ""
echo "Checking for cross-platform issues..."

# Check for bash-specific commands in workflows
if grep -r "mkdir -p" .github/workflows/ 2>/dev/null; then
    echo "⚠️  Warning: Found 'mkdir -p' in workflows (use Python os.makedirs instead)"
fi

# Check for multiline commands with backslashes in workflows
if grep -A 5 "run: |" .github/workflows/ | grep -E "\\\\$" 2>/dev/null; then
    echo "⚠️  Warning: Found multiline commands with backslashes (may break on Windows)"
fi

echo ""
echo "=== ✅ All pre-push checks passed! ==="
echo "Safe to push to remote."
