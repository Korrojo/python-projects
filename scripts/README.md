# Repository Setup Scripts

This directory contains scripts for setting up and managing the Python repository environment.

## Environment Setup Scripts

### `install_venv.sh` (macOS/Linux/Git Bash)

**Purpose:** Automated virtual environment creation with Python version detection

**Usage:**

```bash
./scripts/install_venv.sh
```

**Features:**

- Detects OS automatically
- Finds all Python installations on system
- Interactive Python version selection
- Auto-install Python 3.11 via Homebrew (optional)
- Creates `.venv311` or `.venv312` based on selection

______________________________________________________________________

### `install_venv.ps1` (Windows PowerShell)

**Purpose:** Windows version of virtual environment installer

**Usage:**

```powershell
.\scripts\install_venv.ps1
```

**Features:**

- Same functionality as .sh version for Windows
- Uses py launcher when available
- Chocolatey auto-install support

______________________________________________________________________

### `activate_venv.ps1` (Windows PowerShell)

**Purpose:** Simplified virtual environment activation for Windows

**Usage:**

```powershell
.\scripts\activate_venv.ps1
```

**Note:** For manual activation, use:

- Windows: `.\.venv311\Scripts\Activate.ps1`
- macOS/Linux: `source .venv311/bin/activate`

______________________________________________________________________

## Code Quality Scripts

### `lint.sh` (Cross-platform)

**Purpose:** Comprehensive code quality checking with auto-fix for both **Markdown** and **Python**

**Usage:**

```bash
./scripts/lint.sh [target_directory_or_file]
```

**What it does:**

1. **mdformat** - Formats markdown files (pure Python, like Black for markdown)
1. **Black** - Formats Python code to Black-compatible style
1. **Ruff Check** - Lints Python code for issues
1. **Ruff Auto-fix** - Automatically fixes Python issues where possible
1. **Pyright** - Type checking (IDE-agnostic)

**Examples:**

```bash
# Lint entire repository (markdown + Python)
./scripts/lint.sh .

# Lint specific project
./scripts/lint.sh db_collection_stats/

# Lint common_config
./scripts/lint.sh common_config/

# Lint single markdown file
./scripts/lint.sh README.md
```

**Smart behavior:**

- **Markdown file** → Only runs mdformat (skips Python tools)
- **Directory** → Runs all tools (markdown + Python)

**Exit codes:**

- `0` - All checks passed
- `1` - Unfixable issues remain

______________________________________________________________________

### `markdown-lint.sh` (Cross-platform)

**Purpose:** Markdown file formatting using mdformat (pure Python solution)

**Usage:**

```bash
./scripts/markdown-lint.sh [check|fix]
```

**What it does:**

1. **mdformat** - Formats markdown files (like Black for markdown)
1. **Auto-fix** - Fixes formatting issues automatically (in fix mode)

**Examples:**

```bash
# Check markdown files
./scripts/markdown-lint.sh check

# Auto-fix markdown files
./scripts/markdown-lint.sh fix
```

**Note:** Markdown formatting is **automatically integrated** into:

- **Manual workflow:** `./scripts/lint.sh` (runs markdown + Python tools)
- **Automatic workflow:** Pre-push hook (validates before every push)

You only need to run `markdown-lint.sh` directly if you want to format markdown files separately.

**Why mdformat?**

- ✅ Pure Python (no Node.js required)
- ✅ Works like Black for markdown
- ✅ Installed via pip
- ✅ Uses `pyproject.toml` for configuration

**Configuration:**

- `pyproject.toml` - mdformat configuration (same as Black/Ruff)
- Line wrap: 120 characters (matches Black)

**Exit codes:**

- `0` - All checks passed
- `1` - Formatting issues found

______________________________________________________________________

### `pre-push-check.sh` (Pre-push hook)

**Purpose:** Comprehensive validation before pushing to remote

**Usage:**

```bash
./scripts/pre-push-check.sh
```

**What it does:**

1. Activates virtual environment
1. Runs markdown linting
1. Runs code linting (Black, Ruff, Pyright)
1. Runs tests
1. Checks for cross-platform issues

**Note:** This runs automatically via `.git/hooks/pre-push` hook.

**⚠️ CRITICAL:** `--no-verify` is **BLOCKED** by `git-safe` wrapper. See [Git Safety](#git-safety--enforcement-) section
below.

______________________________________________________________________

## Git Safety & Enforcement 🔒

### `git-safe` ⭐ NEW

**Purpose:** Prevents bypassing git hooks with `--no-verify` flag

**Installation:**

```bash
./scripts/install-git-safety.sh
```

**What it does:**

Intercepts `git push`, `git commit`, and `git am` commands and **blocks** the `--no-verify` flag.

**Example blocking:**

```bash
$ git push --no-verify
╔════════════════════════════════════════════════════════════════╗
║                    🚫 SECURITY VIOLATION 🚫                     ║
╠════════════════════════════════════════════════════════════════╣
║  The --no-verify flag is BLOCKED in this repository           ║
║                                                                ║
║  Why: Bypassing hooks leads to CI failures and broken builds  ║
╚════════════════════════════════════════════════════════════════╝

📋 Proper Workflow:
  1. Fix the validation errors shown in the hook output
  2. Run: ./scripts/pre-push-check.sh to verify fixes
  3. Commit the fixes: git add . && git commit --amend
  4. Push without --no-verify: git push
```

**Violation logging:** All `--no-verify` attempts are logged to `.git/security-violations.log`

**See:** [CODE_QUALITY_ENFORCEMENT.md](../docs/CODE_QUALITY_ENFORCEMENT.md) for full policy

______________________________________________________________________

### `install-git-safety.sh`

**Purpose:** Install git-safe wrapper and configure repository

**Usage:**

```bash
./scripts/install-git-safety.sh
```

**Run this:** Once per repository clone (included in setup instructions)

______________________________________________________________________

## Project Scaffolding Scripts

### `bootstrap_project.sh` (macOS/Linux/Git Bash)

**Purpose:** Fully automated new project setup

**Usage:**

```bash
./scripts/bootstrap_project.sh <project-name> [environment]
```

**Example:**

```bash
./scripts/bootstrap_project.sh my_new_project DEV
```

**What it automates:**

1. Virtual environment setup
1. Dependency installation
1. common_config installation
1. Environment verification
1. Project scaffolding
1. Code quality checks
1. Initial tests
1. Structure verification

______________________________________________________________________

### `bootstrap_project.ps1` (Windows PowerShell)

**Purpose:** Windows version of project bootstrap script

**Usage:**

```powershell
.\scripts\bootstrap_project.ps1 <project-name> [environment]
```

**Example:**

```powershell
.\scripts\bootstrap_project.ps1 my_new_project DEV
```

______________________________________________________________________

## Making Scripts Executable (macOS/Linux)

Before first use, grant execute permissions:

```bash
chmod +x scripts/install_venv.sh
chmod +x scripts/lint.sh
chmod +x scripts/bootstrap_project.sh
```

**Windows:** Scripts are executable by default (.ps1 files)

______________________________________________________________________

## Cross-Platform Support

All scripts support:

- ✅ **macOS** (primary development platform)
- ✅ **Linux** (Ubuntu, Debian, RHEL, etc.)
- ✅ **Windows** (PowerShell, Git Bash, CMD)

Platform detection is automatic where applicable.

______________________________________________________________________

## Troubleshooting

### Permission Denied (macOS/Linux)

```bash
chmod +x scripts/*.sh
```

### PowerShell Execution Policy (Windows)

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Script Not Found

Ensure you're in the repository root:

```bash
pwd  # Should show: /Users/demesewabebe/Projects/python
```

______________________________________________________________________

## Related Documentation

- **BOOTSTRAP_GUIDE.md** - Step-by-step manual setup guide
- **VENV_SETUP.md** - Virtual environment details
- **LINTING.md** - Code quality standards
- **CONTRIBUTING.md** - Contribution guidelines
