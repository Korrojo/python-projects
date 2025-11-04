#!/bin/bash
# Pre-push validation script
# Run this before pushing to main or creating PRs

set -e  # Exit on any error

echo "=== Pre-Push Validation ==="
echo ""

# 1. Check if venv is activated, activate if not
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "📦 Virtual environment not activated, activating..."
    # Try to find and activate venv
    if [ -d ".venv311" ]; then
        source .venv311/bin/activate
        echo "✅ Virtual environment activated: .venv311"
    elif [ -d ".venv312" ]; then
        source .venv312/bin/activate
        echo "✅ Virtual environment activated: .venv312"
    else
        echo "❌ No virtual environment found (.venv311 or .venv312)"
        echo "   Run: ./scripts/install_venv.sh"
        exit 1
    fi
else
    echo "✅ Virtual environment: $VIRTUAL_ENV"
fi

# 2. Run markdown linting
echo ""
echo "Running markdown linting..."
./scripts/markdown-lint.sh check
if [ $? -ne 0 ]; then
    echo "❌ Markdown linting failed! Fix issues before pushing."
    exit 1
fi
echo "✅ Markdown linting passed"

# 3. Run code linting (catches N999 and formatting issues)
echo ""
echo "Running code quality checks..."
./scripts/lint.sh
if [ $? -ne 0 ]; then
    echo "❌ Code linting failed! Fix issues before pushing."
    exit 1
fi
echo "✅ Code quality checks passed"

# 4. Run tests
echo ""
echo "Running tests..."
# Capture both stdout and exit code
test_output=$(pytest -q --maxfail=1 --disable-warnings -m "not integration" 2>&1)
test_exit_code=$?

# Print the output
echo "$test_output"

# Check if tests failed
if [ $test_exit_code -ne 0 ]; then
    echo "❌ Tests failed! Fix tests before pushing."
    exit 1
fi

# Check if any tests were actually selected and run
if echo "$test_output" | grep -qE "(0 passed|collected 0 items|0 selected, 0 deselected)"; then
    echo "❌ No tests were selected/run! Check your test markers."
    echo "   Tests need proper markers like @pytest.mark.unit"
    exit 1
fi

# Check if tests were deselected without any being selected
if echo "$test_output" | grep -qE "deselected" && ! echo "$test_output" | grep -qE "[1-9][0-9]* passed"; then
    echo "❌ All tests were deselected! Check your test markers."
    echo "   Tests need proper markers like @pytest.mark.unit"
    exit 1
fi

echo "✅ Tests passed"

# 5. Check for common cross-platform issues
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
