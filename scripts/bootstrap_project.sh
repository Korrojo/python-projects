#!/usr/bin/env bash
# ==============================================================================
# Bootstrap Script for New Python Projects
# ==============================================================================
# Automated setup for new projects in the unified repository structure
# Usage: ./scripts/bootstrap_project.sh <project-name> [environment]
#
# Example: ./scripts/bootstrap_project.sh db_collection_stats DEV
# ==============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# ==============================================================================
# Configuration
# ==============================================================================

PROJECT_NAME="${1:-}"
ENVIRONMENT="${2:-DEV}"

if [ -z "$PROJECT_NAME" ]; then
    log_error "Project name is required"
    echo "Usage: $0 <project-name> [environment]"
    echo "Example: $0 db_collection_stats DEV"
    exit 1
fi

# Get script directory and repository root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

log_info "=========================================="
log_info "Project Bootstrap Automation"
log_info "=========================================="
log_info "Project Name: $PROJECT_NAME"
log_info "Environment: $ENVIRONMENT"
log_info "Repository Root: $REPO_ROOT"
log_info "=========================================="
echo ""

cd "$REPO_ROOT"

# ==============================================================================
# Step 1: Check Prerequisites
# ==============================================================================

log_info "Step 1/10: Checking prerequisites..."

check_command python3
check_command pip

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
    log_error "Python 3.11+ required. Found: $PYTHON_VERSION"
    exit 1
fi

log_success "Prerequisites check passed (Python $PYTHON_VERSION)"
echo ""

# ==============================================================================
# Step 2: Setup Virtual Environment
# ==============================================================================

log_info "Step 2/10: Setting up virtual environment..."

VENV_DIR="$REPO_ROOT/.venv311"

if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    log_success "Virtual environment created"
else
    log_success "Virtual environment already exists"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"
log_success "Virtual environment activated"
echo ""

# ==============================================================================
# Step 3: Install/Upgrade pip
# ==============================================================================

log_info "Step 3/10: Upgrading pip..."
pip install --upgrade pip --quiet
log_success "pip upgraded"
echo ""

# ==============================================================================
# Step 4: Install Repository Dependencies
# ==============================================================================

log_info "Step 4/10: Installing repository dependencies..."

if [ -f "$REPO_ROOT/requirements.txt" ]; then
    pip install -r "$REPO_ROOT/requirements.txt" --quiet
    log_success "Repository dependencies installed"
else
    log_warning "requirements.txt not found, skipping..."
fi
echo ""

# ==============================================================================
# Step 5: Install common_config
# ==============================================================================

log_info "Step 5/10: Installing common_config..."

if [ -d "$REPO_ROOT/common_config" ]; then
    pip install -e "$REPO_ROOT/common_config" --quiet
    log_success "common_config installed in editable mode"
else
    log_error "common_config directory not found!"
    exit 1
fi
echo ""

# ==============================================================================
# Step 6: Verify .env Configuration
# ==============================================================================

log_info "Step 6/10: Verifying environment configuration..."

ENV_FILE="$REPO_ROOT/shared_config/.env"

if [ ! -f "$ENV_FILE" ]; then
    log_warning ".env file not found at $ENV_FILE"
    if [ -f "$REPO_ROOT/shared_config/.env.example" ]; then
        log_info "Creating .env from .env.example..."
        cp "$REPO_ROOT/shared_config/.env.example" "$ENV_FILE"
        log_warning "Please edit $ENV_FILE with your actual credentials"
    else
        log_error "No .env.example found. Cannot proceed."
        exit 1
    fi
fi

# Check if environment-specific variables exist
if ! grep -q "MONGODB_URI_$ENVIRONMENT" "$ENV_FILE"; then
    log_warning "MONGODB_URI_$ENVIRONMENT not found in .env"
    log_warning "Please add: MONGODB_URI_$ENVIRONMENT=your_connection_string"
fi

if ! grep -q "DATABASE_NAME_$ENVIRONMENT" "$ENV_FILE"; then
    log_warning "DATABASE_NAME_$ENVIRONMENT not found in .env"
    log_warning "Please add: DATABASE_NAME_$ENVIRONMENT=your_database_name"
fi

log_success "Environment configuration checked"
echo ""

# ==============================================================================
# Step 7: Scaffold New Project
# ==============================================================================

log_info "Step 7/10: Scaffolding project structure..."

PROJECT_DIR="$REPO_ROOT/$PROJECT_NAME"

if [ -d "$PROJECT_DIR" ]; then
    log_error "Project directory already exists: $PROJECT_DIR"
    read -p "Do you want to overwrite it? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
        log_info "Aborting..."
        exit 1
    fi
    FORCE_FLAG="--force"
else
    FORCE_FLAG=""
fi

python -m common_config init "$PROJECT_NAME" $FORCE_FLAG

log_success "Project scaffolded"
echo ""

# ==============================================================================
# Step 8: Run Code Quality Checks
# ==============================================================================

log_info "Step 8/10: Running code quality checks..."

# Format code with Black
log_info "Formatting with Black..."
black "$PROJECT_DIR" --line-length 120 --quiet || log_warning "Black formatting had warnings"

# Lint with Ruff
log_info "Linting with Ruff..."
ruff check "$PROJECT_DIR" --fix --quiet || log_warning "Ruff found issues (auto-fixed where possible)"

log_success "Code quality checks completed"
echo ""

# ==============================================================================
# Step 9: Run Tests
# ==============================================================================

log_info "Step 9/10: Running initial tests..."

if [ -d "$PROJECT_DIR/tests" ]; then
    pytest "$PROJECT_DIR/tests/" -q --disable-warnings || log_warning "Some tests failed (expected for initial scaffold)"
    log_success "Tests executed"
else
    log_warning "No tests directory found, skipping..."
fi
echo ""

# ==============================================================================
# Step 10: Verify Project Setup
# ==============================================================================

log_info "Step 10/10: Verifying project setup..."

# Verify directory structure
CHECKS_PASSED=true

for dir in "src" "tests" "scripts" "temp"; do
    if [ -d "$PROJECT_DIR/$dir" ]; then
        log_success "Directory exists: $dir/"
    else
        log_error "Missing directory: $dir/"
        CHECKS_PASSED=false
    fi
done

# Verify centralized directories
for dir in "data/input/$PROJECT_NAME" "data/output/$PROJECT_NAME" "logs/$PROJECT_NAME"; do
    if [ -d "$REPO_ROOT/$dir" ]; then
        log_success "Centralized directory exists: $dir/"
    else
        log_error "Missing centralized directory: $dir/"
        CHECKS_PASSED=false
    fi
done

# Verify key files
for file in "run.py" "README.md" ".gitignore"; do
    if [ -f "$PROJECT_DIR/$file" ]; then
        log_success "File exists: $file"
    else
        log_error "Missing file: $file"
        CHECKS_PASSED=false
    fi
done

echo ""

# ==============================================================================
# Summary
# ==============================================================================

log_info "=========================================="
log_info "Bootstrap Complete!"
log_info "=========================================="
echo ""

if [ "$CHECKS_PASSED" = true ]; then
    log_success "All verification checks passed ✓"
else
    log_warning "Some verification checks failed"
fi

echo ""
log_info "Project Location: $PROJECT_DIR"
log_info "Data Input: $REPO_ROOT/data/input/$PROJECT_NAME/"
log_info "Data Output: $REPO_ROOT/data/output/$PROJECT_NAME/"
log_info "Logs: $REPO_ROOT/logs/$PROJECT_NAME/"
echo ""

log_info "Next Steps:"
echo "  1. Edit project code: code $PROJECT_DIR/"
echo "  2. Update .env if needed: code $ENV_FILE"
echo "  3. Run project: python $PROJECT_DIR/run.py"
echo "  4. Run tests: pytest $PROJECT_DIR/tests/ -v"
echo "  5. Commit changes: git add $PROJECT_NAME && git commit -m 'feat: Add $PROJECT_NAME project'"
echo ""

log_info "Quick Start Commands:"
echo "  cd $PROJECT_DIR"
echo "  python run.py"
echo ""

log_success "Happy coding! 🚀"
