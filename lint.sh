#!/bin/bash
# Linting and formatting script for Python projects
# Uses Ruff (formatter + linter) and Pyright (type checker)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Python Code Quality Tools ===${NC}"
echo ""

# Check if ruff is installed
command -v ruff >/dev/null 2>&1 || { echo -e "${RED}Error: ruff is not installed. Run: pip install ruff${NC}"; exit 1; }

# Check if pyright is available (optional)
PYRIGHT_AVAILABLE=false
command -v pyright >/dev/null 2>&1 && PYRIGHT_AVAILABLE=true

# Determine target (default: all Python files)
TARGET="${1:-.}"

echo -e "${YELLOW}Target: $TARGET${NC}"
echo ""

# Run Ruff (formatter)
echo -e "${GREEN}1. Running Ruff (formatter)...${NC}"
ruff format "$TARGET"
echo ""

# Run Ruff (linter) - check only
echo -e "${GREEN}2. Running Ruff (linter - check)...${NC}"
ruff check "$TARGET"
echo ""

# Run Ruff (linter) - fix
echo -e "${GREEN}3. Running Ruff (linter - auto-fix)...${NC}"
ruff check "$TARGET" --fix
echo ""

# Run Pyright (type checker) - optional
if [ "$PYRIGHT_AVAILABLE" = true ]; then
    echo -e "${GREEN}4. Running Pyright (type checker)...${NC}"
    if pyright "$TARGET" 2>/dev/null; then
        echo -e "${GREEN}✓ Type checking passed${NC}"
    else
        echo -e "${YELLOW}⚠ Type checking found issues (see above)${NC}"
        echo -e "${YELLOW}Note: Pyright may have package detection issues. VS Code Pylance is more reliable.${NC}"
    fi
    echo ""
else
    echo -e "${YELLOW}4. Pyright not available - skipping type checking${NC}"
    echo -e "${YELLOW}   Type checking is still available in VS Code via Pylance${NC}"
    echo ""
fi

echo -e "${GREEN}=== Done! ===${NC}"
echo ""
echo "To check without fixing:"
echo "  ruff check $TARGET"
echo ""
echo "To format without linting:"
echo "  ruff format $TARGET"
echo ""
if [ "$PYRIGHT_AVAILABLE" = true ]; then
    echo "To run type checking only:"
    echo "  pyright $TARGET"
    echo ""
fi
echo "Note: Type checking is integrated in VS Code via Pylance"
