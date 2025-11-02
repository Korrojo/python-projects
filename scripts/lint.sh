#!/bin/bash
# Linting and formatting script for Python projects
# Uses mdformat (markdown formatter), Black (Python formatter), Ruff (linter), and Pyright (type checker)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Code Quality Tools (Markdown + Python) ===${NC}"
echo ""

# Check if mdformat is installed
command -v mdformat >/dev/null 2>&1 || { echo -e "${RED}Error: mdformat is not installed. Run: pip install -r requirements.txt${NC}"; exit 1; }

# Check if black is installed
command -v black >/dev/null 2>&1 || { echo -e "${RED}Error: black is not installed. Run: pip install black${NC}"; exit 1; }

# Check if ruff is installed
command -v ruff >/dev/null 2>&1 || { echo -e "${RED}Error: ruff is not installed. Run: pip install ruff${NC}"; exit 1; }

# Check if pyright is available (optional)
PYRIGHT_AVAILABLE=false
command -v pyright >/dev/null 2>&1 && PYRIGHT_AVAILABLE=true

# Determine target (default: all files)
TARGET="${1:-.}"

echo -e "${YELLOW}Target: $TARGET${NC}"
echo ""

# Detect if target is markdown-only
IS_MARKDOWN_ONLY=false
if [[ "$TARGET" == *.md ]]; then
    IS_MARKDOWN_ONLY=true
fi

# Run mdformat (markdown formatter)
echo -e "${GREEN}1. Running mdformat (markdown formatter)...${NC}"
if [ "$IS_MARKDOWN_ONLY" = true ]; then
    # Direct markdown file
    if mdformat --check --wrap 120 "$TARGET" 2>/dev/null; then
        echo -e "${GREEN}✓ Markdown file properly formatted${NC}"
    else
        echo ""
        echo -e "${YELLOW}⚠ Markdown formatting issues found. Auto-fixing...${NC}"
        mdformat --wrap 120 "$TARGET"
        echo -e "${GREEN}✓ Markdown file formatted${NC}"
    fi
else
    # Directory or multiple files
    if find "$TARGET" -name "*.md" \
        ! -path "*/.venv*/*" \
        ! -path "*/node_modules/*" \
        ! -path "*/temp/*" \
        ! -path "*/artifacts/*" \
        ! -path "*/build/*" \
        ! -path "*/dist/*" \
        -exec mdformat --check --wrap 120 {} + 2>/dev/null; then
        echo -e "${GREEN}✓ All markdown files properly formatted${NC}"
    else
        echo ""
        echo -e "${YELLOW}⚠ Markdown formatting issues found. Auto-fixing...${NC}"
        find "$TARGET" -name "*.md" \
            ! -path "*/.venv*/*" \
            ! -path "*/node_modules/*" \
            ! -path "*/temp/*" \
            ! -path "*/artifacts/*" \
            ! -path "*/build/*" \
            ! -path "*/dist/*" \
            -exec mdformat --wrap 120 {} +
        echo -e "${GREEN}✓ Markdown files formatted${NC}"
    fi
fi
echo ""

# Skip Python tools if target is markdown-only
if [ "$IS_MARKDOWN_ONLY" = true ]; then
    echo -e "${YELLOW}Target is markdown file - skipping Python tools${NC}"
    echo ""
    echo -e "${GREEN}=== Done! ===${NC}"
    exit 0
fi

# Run Black (formatter)
echo -e "${GREEN}2. Running Black (Python formatter)...${NC}"
black "$TARGET"
echo ""

# Run Ruff (linter) - check only
echo -e "${GREEN}3. Running Ruff (Python linter - check)...${NC}"
if ! ruff check "$TARGET"; then
    echo ""
    echo -e "${YELLOW}⚠ Ruff found issues. Attempting auto-fix...${NC}"
    echo ""
    # Run Ruff (linter) - fix
    echo -e "${GREEN}4. Running Ruff (Python linter - auto-fix)...${NC}"
    if ruff check "$TARGET" --fix; then
        echo -e "${GREEN}✓ All fixable issues resolved!${NC}"
    else
        echo ""
        echo -e "${RED}✗ Some issues remain after auto-fix${NC}"
        echo -e "${YELLOW}To see remaining issues, run:${NC}"
        echo -e "  ${YELLOW}ruff check $TARGET${NC}"
        echo ""
        echo -e "${YELLOW}To manually fix, run:${NC}"
        echo -e "  ${YELLOW}ruff check $TARGET --fix${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ All checks passed!${NC}"
fi
echo ""

# Run Pyright (type checker)
if [ "$PYRIGHT_AVAILABLE" = true ]; then
    echo -e "${GREEN}5. Running Pyright (type checker)...${NC}"
    if pyright "$TARGET" 2>/dev/null; then
        echo -e "${GREEN}✓ Type checking passed${NC}"
    else
        echo -e "${YELLOW}⚠ Type checking found issues (see above)${NC}"
    fi
    echo ""
else
    echo -e "${RED}5. Pyright not found - skipping type checking${NC}"
    echo -e "${YELLOW}   To install: ${NC}pip install -r requirements.txt"
    echo -e "${YELLOW}   This ensures IDE-agnostic type checking on any platform${NC}"
    echo ""
fi

echo -e "${GREEN}=== Done! ===${NC}"
echo ""
echo "Individual tool usage:"
echo ""
echo "Markdown formatting:"
echo "  mdformat --check --wrap 120 *.md  (check only)"
echo "  mdformat --wrap 120 *.md          (auto-fix)"
echo ""
echo "Python formatting:"
echo "  black --check --diff $TARGET      (check only)"
echo "  black $TARGET                     (auto-fix)"
echo ""
echo "Python linting:"
echo "  ruff check $TARGET                (check only)"
echo "  ruff check $TARGET --fix          (auto-fix)"
echo ""
if [ "$PYRIGHT_AVAILABLE" = true ]; then
    echo "Type checking:"
    echo "  pyright $TARGET"
    echo ""
fi
echo "Note:"
echo "- This script auto-formats markdown AND Python code"
echo "- Also runs automatically via pre-push hook"
echo "- Type checking is integrated in VS Code via Pylance"
