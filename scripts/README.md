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

---

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

---

### `activate_venv.ps1` (Windows PowerShell)
**Purpose:** Simplified virtual environment activation for Windows

**Usage:**
```powershell
.\scripts\activate_venv.ps1
```

**Note:** For manual activation, use:
- Windows: `.\.venv311\Scripts\Activate.ps1`
- macOS/Linux: `source .venv311/bin/activate`

---

## Code Quality Scripts

### `lint.sh` (Cross-platform)
**Purpose:** Comprehensive code quality checking with auto-fix

**Usage:**
```bash
./scripts/lint.sh [target_directory]
```

**What it does:**
1. **Ruff Format** - Formats Python code to Black-compatible style
2. **Ruff Check** - Lints code for issues
3. **Ruff Auto-fix** - Automatically fixes issues where possible
4. **Pyright** - Type checking (IDE-agnostic)

**Examples:**
```bash
# Lint entire repository
./scripts/lint.sh .

# Lint specific project
./scripts/lint.sh db_collection_stats/

# Lint common_config
./scripts/lint.sh common_config/
```

**Exit codes:**
- `0` - All checks passed
- `1` - Unfixable issues remain

---

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
2. Dependency installation
3. common_config installation
4. Environment verification
5. Project scaffolding
6. Code quality checks
7. Initial tests
8. Structure verification

---

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

---

## Making Scripts Executable (macOS/Linux)

Before first use, grant execute permissions:

```bash
chmod +x scripts/install_venv.sh
chmod +x scripts/lint.sh
chmod +x scripts/bootstrap_project.sh
```

**Windows:** Scripts are executable by default (.ps1 files)

---

## Cross-Platform Support

All scripts support:
- ✅ **macOS** (primary development platform)
- ✅ **Linux** (Ubuntu, Debian, RHEL, etc.)
- ✅ **Windows** (PowerShell, Git Bash, CMD)

Platform detection is automatic where applicable.

---

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

---

## Related Documentation

- **BOOTSTRAP_GUIDE.md** - Step-by-step manual setup guide
- **VENV_SETUP.md** - Virtual environment details
- **LINTING.md** - Code quality standards
- **CONTRIBUTING.md** - Contribution guidelines
