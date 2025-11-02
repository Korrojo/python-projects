#!/bin/bash
#
# Install Git Hooks
#
# This script installs git hooks from scripts/hooks/ to .git/hooks/
# Run this script after cloning the repository to set up workflow enforcement.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_SRC="$REPO_ROOT/scripts/hooks"
HOOKS_DST="$REPO_ROOT/.git/hooks"

echo "Installing git hooks..."
echo ""

# Check if .git directory exists
if [ ! -d "$REPO_ROOT/.git" ]; then
    echo "❌ Error: .git directory not found. Are you in a git repository?"
    exit 1
fi

# Install each hook
INSTALLED_COUNT=0
for hook in "$HOOKS_SRC"/*; do
    if [ -f "$hook" ]; then
        HOOK_NAME=$(basename "$hook")
        echo "  Installing $HOOK_NAME..."
        cp "$hook" "$HOOKS_DST/$HOOK_NAME"
        chmod +x "$HOOKS_DST/$HOOK_NAME"
        INSTALLED_COUNT=$((INSTALLED_COUNT + 1))
    fi
done

echo ""
echo "✅ Successfully installed $INSTALLED_COUNT git hook(s)"
echo ""
echo "Installed hooks:"
echo "  - pre-commit: Prevents commits to main/master branches"
echo ""
echo "Note: Hooks can be bypassed with --no-verify (not recommended)"
echo ""
