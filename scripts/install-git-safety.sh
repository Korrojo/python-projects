#!/bin/bash
# Install Git Safety Wrapper
# This script sets up protection against --no-verify bypass

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔒 Installing Git Safety Protection..."
echo ""

# Make git-safe executable
chmod +x "$SCRIPT_DIR/git-safe"

# Create git alias that uses our wrapper
echo "📝 Configuring git aliases..."
git config --local alias.safe-commit '!bash scripts/git-safe commit'
git config --local alias.safe-push '!bash scripts/git-safe push'

# Create a reminder in git config
git config --local core.hooksPath ".git/hooks"

# Add to shell profile (optional, user choice)
echo ""
echo "✅ Git safety wrapper installed!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 IMPORTANT: Update Your Workflow"
echo ""
echo "  Old (BLOCKED):        New (REQUIRED):"
echo "  ──────────────        ───────────────"
echo "  git push              git safe-push"
echo "  git commit            git safe-commit"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔧 Optional: Add to your shell profile for convenience"
echo ""
echo "  # Add this to ~/.bashrc or ~/.zshrc:"
echo "  alias git='$REPO_ROOT/scripts/git-safe'"
echo ""
echo "  Then 'git push --no-verify' will be automatically blocked!"
echo ""

# Create security violations log
touch "$REPO_ROOT/.git/security-violations.log"

echo "✅ Installation complete!"
