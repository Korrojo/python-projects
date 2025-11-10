#!/bin/bash
# One-time script to format all markdown files to match CI configuration
#
# Usage: ./scripts/format-all-markdown.sh
#
# This is needed when:
# - Legacy markdown files need to be brought into compliance
# - CI mdformat check fails on files that weren't recently modified
#
# Pre-commit hooks only run on CHANGED files, but CI checks ALL files.
# This script ensures all markdown in the repo matches CI expectations.

set -e

echo "🔍 Finding all markdown files..."

# Find all markdown files excluding common ignore directories
MARKDOWN_FILES=$(find . -name "*.md" \
    ! -path "*/.venv*" \
    ! -path "*/node_modules/*" \
    ! -path "*/temp/*" \
    ! -path "*/artifacts/*" \
    ! -path "*/archive/*" \
    ! -path "*/.git/*")

FILE_COUNT=$(echo "$MARKDOWN_FILES" | wc -l | tr -d ' ')

echo "📝 Found $FILE_COUNT markdown file(s)"
echo ""
echo "Formatting with: mdformat --wrap 120"
echo ""

# Format all files with the same settings as CI
echo "$MARKDOWN_FILES" | xargs -r mdformat --wrap 120

echo ""
echo "✅ Done! All markdown files formatted to match CI."
echo ""
echo "Run 'git status' to see what changed."
