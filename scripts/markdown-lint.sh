#!/bin/bash
# Markdown formatting script using mdformat (pure Python solution)
# Works like Black but for markdown files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Markdown Formatting (mdformat) ===${NC}"
echo ""

# Check if mdformat is installed
if ! command -v mdformat >/dev/null 2>&1; then
    echo -e "${RED}Error: mdformat is not installed${NC}"
    echo "Install with: pip install mdformat mdformat-gfm mdformat-tables mdformat-frontmatter"
    echo "Or: pip install -r requirements.txt"
    exit 1
fi

# Determine mode (check or fix)
MODE="${1:-check}"
TARGET="${2:-.}"

# Build exclude patterns
EXCLUDE_PATTERNS=(
    --exclude ".venv*"
    --exclude "node_modules"
    --exclude "temp"
    --exclude "artifacts"
    --exclude "build"
    --exclude "dist"
)

if [ "$MODE" = "fix" ]; then
    echo -e "${GREEN}Running mdformat with auto-fix...${NC}"
    echo ""

    # Format markdown files
    find "$TARGET" -name "*.md" \
        ! -path "*/.venv*/*" \
        ! -path "*/node_modules/*" \
        ! -path "*/temp/*" \
        ! -path "*/artifacts/*" \
        ! -path "*/build/*" \
        ! -path "*/dist/*" \
        ! -path "*/archive/*" \
        -exec mdformat --wrap 120 {} +

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ All markdown files formatted!${NC}"
    else
        echo ""
        echo -e "${YELLOW}⚠ Some issues could not be auto-fixed${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Running mdformat (check mode)...${NC}"
    echo ""

    # Check markdown files without modifying
    find "$TARGET" -name "*.md" \
        ! -path "*/.venv*/*" \
        ! -path "*/node_modules/*" \
        ! -path "*/temp/*" \
        ! -path "*/artifacts/*" \
        ! -path "*/build/*" \
        ! -path "*/dist/*" \
        ! -path "*/archive/*" \
        -exec mdformat --check --wrap 120 {} +

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ All markdown files are properly formatted!${NC}"
    else
        echo ""
        echo -e "${RED}✗ Markdown formatting issues found${NC}"
        echo ""
        echo -e "${YELLOW}To auto-fix issues, run:${NC}"
        echo -e "  ${YELLOW}./scripts/markdown-lint.sh fix${NC}"
        echo ""
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}=== Done! ===${NC}"
echo ""
echo "Available commands:"
echo "  ./scripts/markdown-lint.sh check  - Check markdown formatting"
echo "  ./scripts/markdown-lint.sh fix    - Auto-fix markdown formatting"
echo ""
echo "mdformat is a pure Python solution (like Black for markdown)"
echo "Configuration: Line wrap at 120 characters"
echo ""
