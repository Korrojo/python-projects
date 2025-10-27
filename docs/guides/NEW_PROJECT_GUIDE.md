# Creating a New Project - Complete Bootstrap Guide

**Purpose:** Step-by-step guide to create any new project in this repository with full validation at each phase.

**Supports:** macOS, Linux, and Windows (PowerShell, CMD, Git Bash)

---

## 🖥️ Cross-Platform Guide

This guide supports **all major platforms**:
- ✅ **macOS** (primary)
- ✅ **Linux**
- ✅ **Windows** (PowerShell, CMD, Git Bash)

**Platform-specific commands are clearly marked:**
- 🍎 macOS/Linux/Git Bash → Use `bash` syntax
- 🪟 Windows PowerShell → Use `powershell` syntax
- 🪟 Windows CMD → Use `cmd` syntax

**Most commands are identical across platforms** (Python, pip, etc.)

---

## Prerequisites Checklist

Before starting, ensure you have:
- [ ] Terminal/command line access
  - macOS: Terminal or iTerm2
  - Windows: PowerShell, CMD, or Git Bash
  - Linux: Any terminal emulator
- [ ] Git repository cloned
- [ ] Write permissions in the repository directory

---

## PHASE 1: Environment Setup

### Step 1.1: Make Scripts Executable

**⚠️ IMPORTANT: Run this first!**

#### macOS / Linux / Git Bash

```bash
# Make setup scripts executable
chmod +x scripts/install_venv.sh
chmod +x scripts/lint.sh
chmod +x scripts/bootstrap_project.sh
```

**What this does:**
- Grants execute permissions to all setup scripts
- Prevents "Permission denied" errors

**Verify:**
```bash
ls -la *.sh scripts/*.sh | grep "rwx"
```
You should see `-rwxr-xr-x` in the output.

#### Windows (PowerShell / CMD)

**Not needed on Windows** - `.ps1` and `.bat` files are executable by default.

**However, PowerShell execution policy may need to be enabled:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Step 1.2: Install Virtual Environment

#### macOS / Linux / Git Bash

**Run this command:**
```bash
./scripts/install_venv.sh
```

#### Windows PowerShell

**Run this command:**
```powershell
.\scripts\install_venv.ps1
```

**What will happen:**
1. Script detects your OS
2. Searches for all Python installations on your system
3. Shows you a numbered list like:
   ```
   Found 2 Python installation(s):

     1) Python 3.11.9 (RECOMMENDED) - /usr/local/bin/python3.11
     2) Python 3.12.2 - /opt/homebrew/bin/python3

   Select Python version (1-2) [default: 1]:
   ```
4. **You type a number** (recommend: choose Python 3.11 if available)
5. If Python 3.11 not found, script offers to install it via Homebrew

**Interactive Prompts:**
- **"Select Python version"** → Type `1` for Python 3.11 (recommended)
- **"Install Python 3.11 using Homebrew? (y/N)"** → Type `y` if you want auto-install

**Expected Output:**
```
✓ Virtual environment created successfully!
✓ Virtual environment Python version: 3.11.9
✓ Version verified!

=== Installation Complete! ===

Virtual environment created at: .venv311
```

**Verify:**
```bash
# Check venv was created
ls -d .venv*

# Should show: .venv311 or .venv312 (depending on Python version chosen)
```

---

### Step 1.3: Activate Virtual Environment

**⚠️ IMPORTANT: Activate the venv created in Step 1.2**

The venv directory name depends on which Python version you selected:
- Python 3.11 → `.venv311`
- Python 3.12 → `.venv312`

#### macOS / Linux / Git Bash (Windows)

**If you have Python 3.11:**
```bash
source .venv311/bin/activate
```

**If you have Python 3.12:**
```bash
source .venv312/bin/activate
```

**⚠️ CRITICAL: Must use `source`**
- `source .venv311/bin/activate` ✅ Correct
- `./.venv311/bin/activate` ❌ Won't work (creates subshell)

#### Windows PowerShell

**If you have Python 3.11:**
```powershell
.\.venv311\Scripts\Activate.ps1
```

**If you have Python 3.12:**
```powershell
.\.venv312\Scripts\Activate.ps1
```

**Note:** If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Windows Command Prompt (CMD)

**If you have Python 3.11:**
```cmd
.venv311\Scripts\activate.bat
```

**If you have Python 3.12:**
```cmd
.venv312\Scripts\activate.bat
```

---

**Expected Result (All Platforms):**
- Your prompt will change to show `(.venv311)` or `(.venv312)` at the beginning
- Example: `(.venv311) ➜ python git:(main) ✗`

**Verify (All Platforms):**

**macOS/Linux/Git Bash:**
```bash
# Check Python is from venv
which python
# Should show: /Users/.../python/.venv311/bin/python

# Check Python version
python --version
# Should show: Python 3.11.9

# Check pip is from venv
which pip
# Should show: /Users/.../python/.venv311/bin/pip
```

**Windows (PowerShell/CMD):**
```powershell
# Check Python is from venv
where python
# Should show: C:\...\python\.venv311\Scripts\python.exe

# Check Python version
python --version
# Should show: Python 3.11.9

# Check pip is from venv
where pip
# Should show: C:\...\python\.venv311\Scripts\pip.exe
```

**✅ Success Criteria (All Platforms):**
- `(.venv311)` or `(.venv312)` appears in your terminal prompt
- Python path shows `.venv*` directory
- `python --version` shows the version you selected
- No error messages

**To deactivate later (All Platforms):**
```bash
deactivate
```

---

### Step 1.4: Upgrade pip

**Run this command:**
```bash
pip install --upgrade pip
```

**Expected Output:**
```
Successfully installed pip-24.x.x
```

**Verify:**
```bash
pip --version
# Should show latest version (24.x or higher)
```

---

### Step 1.5: Install Repository Dependencies

**Run this command:**
```bash
pip install -r requirements.txt
```

**What this installs:**
- pydantic (settings management)
- pymongo (MongoDB driver)
- pandas (data processing)
- pytest (testing)
- ruff (linting/formatting)
- All other shared dependencies

**Expected Output:**
```
Collecting pydantic>=2.6.0
...
Successfully installed pydantic-2.x.x pymongo-4.x.x pandas-2.x.x ...
```

**⏱️ Time:** ~1-2 minutes

**Verify:**
```bash
pip list | grep -E "pydantic|pymongo|pandas|pytest|ruff"
```

You should see all packages listed with version numbers.

---

### Step 1.6: Install common_config

**Run this command:**
```bash
pip install -e ./common_config
```

**What this does:**
- Installs `common_config` in **editable mode** (`-e`)
- Editable = changes to code take effect immediately (no reinstall needed)
- Makes `common_config` available as a package in all projects

**Expected Output:**
```
Successfully installed common-config-0.1.0
```

**Verify:**
```bash
pip show common-config

# Should show:
# Name: common-config
# Version: 0.1.0
# Location: /Users/demesewabebe/Projects/python/common_config/src
# Editable project location: /Users/demesewabebe/Projects/python/common_config
```

---

### Step 1.7: Verify Configuration

**Run this command:**
```bash
python -c "from common_config.config import get_settings; import os; s=get_settings(); print(f'APP_ENV={os.environ.get(\"APP_ENV\", \"(not set)\")}\nURI={s.mongodb_uri}\nDB={s.database_name}')"
```

**Expected Output:**
```
APP_ENV=DEV (or "(not set)" - both are fine)
URI=mongodb+srv://<username>:<password>@<hostname>.mongodb.net/?retryWrites=true&w=majority
DB=sample_mflix
```

**If this works, you're ready to proceed!**

**If you get errors:**
- `ModuleNotFoundError: No module named 'common_config'` → Re-run step 1.6
- `ValueError: MongoDB URI not found` → Check `shared_config/.env` has `MONGODB_URI_DEV`

---

## ✅ PHASE 1 COMPLETE!

**What we accomplished:**
- ✅ Virtual environment created
- ✅ Virtual environment activated
- ✅ All dependencies installed
- ✅ `common_config` library installed
- ✅ Configuration verified (can connect to DEV MongoDB)

**Verification Checklist:**
- [ ] `(.venv311)` or `(.venv312)` shows in terminal prompt
- [ ] `which python` shows venv path
- [ ] `pip list` shows all required packages
- [ ] `pip show common-config` shows installed
- [ ] Configuration test prints DEV environment variables

**Time taken:** ~5-10 minutes

---

## PHASE 2: Project Scaffolding

### Step 2.1: Create Project Structure

**Choose your project name** - use lowercase with underscores (e.g., `user_validator`, `data_reporter`, `collection_stats`).

**Run this command:**
```bash
common <your-project-name>
```

**Example:**
```bash
common user_validator
```

**What this does:**
- Creates `<your-project-name>/` directory
- Generates standard project structure
- Creates centralized directories in `data/` and `logs/`
- Generates template files (run.py, README.md, tests, etc.)

**Expected Output:**
```
✅ Project created at: ./<your-project-name>

📁 Structure:
   <your-project-name>/
   ├── src/
   ├── tests/
   ├── scripts/
   ├── temp/
   ├── run.py
   ├── run.bat
   ├── .gitignore
   └── README.md

📁 Centralized directories created:
   data/input/<your-project-name>/
   data/output/<your-project-name>/
   logs/<your-project-name>/

Next steps:
  1) Verify common_config is installed (only needed once):
     pip show common-config

  2) Run code quality checks (lint, format, type check):
     ./scripts/lint.sh <your-project-name>/

  3) Run tests:
     pytest <your-project-name>/tests/ -v

  4) Run project:
     python <your-project-name>/run.py
```

> **📝 Note:** The CLI suggests these next steps, but **don't run them yet!** Phase 3 will walk through each step with proper validation and explanations.

**Verify:**
```bash
# Check project directory was created
ls -la <your-project-name>/

# Should show:
# src/  tests/  scripts/  temp/  run.py  run.bat  .gitignore  README.md

# Check centralized directories
ls -la data/input/<your-project-name>/
ls -la data/output/<your-project-name>/
ls -la logs/<your-project-name>/
```

---

### Step 2.2: Inspect Generated Files

**View the template run.py:**
```bash
cat <your-project-name>/run.py
```

**What you'll see:**
- Logging setup using `common_config`
- Settings loader for environment config
- Template main() function with TODOs
- Standard log directory resolution

**View project README:**
```bash
cat <your-project-name>/README.md
```

**View test structure:**
```bash
ls -la <your-project-name>/tests/
```

---

## ✅ PHASE 2 COMPLETE!

**What we accomplished:**
- ✅ Project structure created
- ✅ Template files generated
- ✅ Centralized directories set up
- ✅ Ready for code implementation

**Verification Checklist:**
- [ ] `<your-project-name>/` directory exists
- [ ] `<your-project-name>/run.py` exists
- [ ] `<your-project-name>/tests/` exists
- [ ] `data/input/<your-project-name>/` exists
- [ ] `data/output/<your-project-name>/` exists
- [ ] `logs/<your-project-name>/` exists

**Time taken:** ~1 minute

---

## PHASE 3: Code Quality Baseline

> **🎯 Goal:** Execute the suggested "Next steps" from Phase 2 with proper validation. We'll verify the generated project works correctly by running linting, tests, and the project itself.

### Step 3.1: Run Linting and Formatting

**This implements:** "Next steps" item #2 from Phase 2

**Run this command:**
```bash
./scripts/lint.sh <your-project-name>/
```

**What this does:**
1. **Ruff format** - Formats all Python code
2. **Ruff check** - Checks for code issues
3. **Ruff fix** - Auto-fixes issues where possible
4. **Pyright** - Type checking (optional, may not be installed)

**Expected Output:**
```
=== Python Code Quality Tools ===

Target: <your-project-name>/

1. Running Ruff (formatter)...
4 files already formatted

2. Running Ruff (linter - check)...
All checks passed!

3. Running Ruff (linter - auto-fix)...
Fixed 0 errors

4. Pyright not available - skipping type checking
   Type checking is still available in VS Code via Pylance

=== Done! ===
```

**⏱️ Time:** ~5-10 seconds

---

### Step 3.2: Run Initial Tests

**This implements:** "Next steps" item #3 from Phase 2

**Run this command:**
```bash
pytest <your-project-name>/tests/ -v
```

**What this tests:**
- Smoke tests (can import modules)
- Dependency availability
- Project structure integrity

**Expected Output:**
```
========================= test session starts =========================
collected 5 items

<your-project-name>/tests/test_<project>_smoke.py::TestImports::test_import_run_module PASSED
<your-project-name>/tests/test_<project>_smoke.py::TestDependencies::test_common_config_available PASSED
<your-project-name>/tests/test_<project>_smoke.py::TestProjectStructure::test_readme_exists PASSED
<your-project-name>/tests/test_<project>_smoke.py::TestProjectStructure::test_run_script_exists PASSED
<your-project-name>/tests/test_<project>_smoke.py::TestProjectStructure::test_src_directory_exists PASSED

========================= 5 passed in 0.12s =========================
```

**Verify:**
```bash
# Run with more verbose output
pytest <your-project-name>/tests/ -vv

# Run with coverage
pytest <your-project-name>/tests/ --cov=<your-project-name>
```

---

## ✅ PHASE 3 COMPLETE!

**What we accomplished:**
- ✅ Code formatted to standards (item #2 from "Next steps")
- ✅ All linting checks passed
- ✅ Initial smoke tests passed (item #3 from "Next steps")
- ✅ Clean baseline established

**Verification Checklist:**
- [ ] No linting errors
- [ ] All tests pass
- [ ] No import errors

**Time taken:** ~1 minute

---

## Optional: Test Run the Project Template

**This implements:** "Next steps" item #4 from Phase 2 (optional at this stage)

You can run the generated project template to see the basic structure in action:

```bash
python <your-project-name>/run.py
```

**What to expect:**
- Logging initialization
- Settings loaded from `common_config`
- TODO placeholders for implementation
- No actual business logic yet

This is optional now since the template doesn't do much yet. The real work begins in Phase 4.

---

## PHASE 4: Database Configuration (If Needed)

If your project needs database access, add credentials to `shared_config/.env`:

```bash
# Open the shared environment file
code shared_config/.env
```

Add your connection string (if not already present):
```env
MONGODB_URI_DEV=mongodb://username:password@host:port/database?authSource=admin
MONGODB_URI_PROD=mongodb://username:password@host:port/database?authSource=admin
DATABASE_NAME_DEV=your_database
DATABASE_NAME_PROD=your_database
```

**Note:** All projects share this `.env` file - no per-project config files.

**Test the connection:**
```bash
python -c "from common_config.config import get_settings; s=get_settings(); print(f'Connected to: {s.database_name}')"
```

---

## PHASE 5: Implement Your Logic

### Project Structure Reference

Your project has the following structure:

```
<your-project-name>/
├── src/
│   └── <your_project_name>/      # Your Python package
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_<project>_smoke.py
├── scripts/                       # Maintenance scripts (indexes, migrations, etc.)
│   └── README.md
├── temp/                          # Temporary files (gitignored)
│   └── .gitkeep
├── run.py                        # Main entry point
├── run.bat                       # Windows launcher
├── .gitignore                    # Project-specific ignores
├── pyproject.toml                # Python tooling config
└── README.md                     # Project documentation
```

**Centralized directories at repository root:**
```
data/
├── input/<your-project-name>/    # Input files
└── output/<your-project-name>/   # Output files

logs/<your-project-name>/         # Log files

artifacts/                        # Build outputs (shared)
├── .pytest_cache/
├── .ruff_cache/
├── coverage/
└── test-reports/
```

### Main Entry Point: `run.py`

The scaffolder creates a template `run.py` with:
- Logging setup (outputs to `logs/<project>/`)
- Settings loading from `shared_config/.env`
- Basic structure

**Edit it:**
```bash
code <your-project-name>/run.py
```

### Create Modules in `src/`

Add your business logic:
```bash
# Create a module
code <your-project-name>/src/<your_project_name>/processor.py
```

**Example module structure:**
```python
from common_config.config import get_settings

def process_data():
    """Your business logic here."""
    settings = get_settings()
    # ... implementation ...
    pass
```

### Utility Scripts in `scripts/`

For maintenance tasks (index creation, migrations):
```bash
code <your-project-name>/scripts/create_indexes.py
```

---

## PHASE 6: Managing Dependencies

**IMPORTANT:** This repository uses a **shared virtual environment** with a **root-level `requirements.txt`**.

### Check if dependency already exists:
```bash
pip list | grep <package-name>
```

### If dependency is already installed:
✅ **No action needed!** Just use it in your project.

### If you need a NEW dependency:

**Option 1: Shared dependency (used by multiple projects)**
1. **Add to ROOT `requirements.txt`:**
   ```bash
   echo "pandas==2.1.0" >> requirements.txt
   ```

2. **Install in shared venv:**
   ```bash
   pip install -r requirements.txt
   ```

**Option 2: Project-specific dependency (ONLY this project needs it)**
1. **Create project requirements.txt:**
   ```bash
   echo "special-library==1.0.0" > <your-project-name>/requirements.txt
   ```

2. **Install it:**
   ```bash
   pip install -r <your-project-name>/requirements.txt
   ```

**Best Practice:** Prefer Option 1 (root-level) to avoid version conflicts and duplication.

---

## PHASE 7: Write Tests

The scaffolder creates initial smoke tests in `tests/test_<package>_smoke.py`.

**Add more tests:**
```bash
code <your-project-name>/tests/test_processor.py
```

**Example test:**
```python
import pytest
from <your_project_name>.processor import process_data

def test_process_data():
    """Test your business logic."""
    result = process_data()
    assert result is not None
```

**Run tests:**
```bash
pytest <your-project-name>/tests/ -v
```

**With coverage:**
```bash
pytest <your-project-name>/tests/ --cov=<your-project-name> --cov-report=term-missing
```

---

## PHASE 8: Run Your Project

### Option 1: Direct Python
```bash
python <your-project-name>/run.py
```

### Option 2: Windows Batch File
```bash
<your-project-name>\run.bat
```

The batch file automatically activates the shared venv and runs `run.py`.

---

## PHASE 9: Git Commit and Documentation

### Update Project README

Edit your project's README to document:
- Purpose and functionality
- Usage instructions
- Configuration requirements
- Example outputs

```bash
code <your-project-name>/README.md
```

### Create a Git Commit

**Check status:**
```bash
git status
```

**Add your new project:**
```bash
git add <your-project-name>/
git add data/input/<your-project-name>/
git add data/output/<your-project-name>/
git add logs/<your-project-name>/
```

**Commit with descriptive message:**
```bash
git commit -m "feat: Add <your-project-name> project

- Implements [brief description of functionality]
- Includes comprehensive tests
- Follows repository standards

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Integration with CI/CD

Your project is automatically included in the GitHub Actions pipeline:

1. **Linting**: Ruff checks code quality
2. **Type Checking**: Pyright validates types
3. **Testing**: Pytest runs all tests with coverage

No additional setup needed - just push your code!

---

## Common Tasks Quick Reference

**Phase 1: Environment Setup**
```bash
# Activate venv (manual)
source .venv311/bin/activate

# Deactivate venv
deactivate

# Check environment config
python -c "from common_config.config import get_settings; print(get_settings())"
```

**Phase 2: Project Scaffolding**
```bash
# Create new project
common <your-project-name>
```

**Phase 3: Code Quality Baseline**
```bash
# Run linting (implements "Next steps" item #2)
./scripts/lint.sh <your-project-name>/

# Run tests (implements "Next steps" item #3)
pytest <your-project-name>/tests/ -v

# Run project template (implements "Next steps" item #4)
python <your-project-name>/run.py
```

**Development Workflow**
```bash
# Format code
ruff format <your-project-name>/

# Lint code
ruff check <your-project-name>/

# Type check
pyright <your-project-name>/

# Run tests with coverage
pytest <your-project-name>/tests/ --cov=<your-project-name>
```

---

## Troubleshooting

### "Permission denied" error
**Solution:** Run `chmod +x scripts/install_venv.sh scripts/lint.sh scripts/bootstrap_project.sh`

### "No Python installations found"
**Solution:** Let the script install Python 3.11 via Homebrew, or install manually

### "ModuleNotFoundError: No module named 'common_config'"
**Solution:**
```bash
# Ensure venv is activated
source .venv311/bin/activate

# Reinstall common_config
pip install -e ./common_config
```

### "grep: invalid option -- P"
**Solution:** This issue has been fixed in the updated scripts (using `sed` instead of `grep -P`)

### Tests fail with import errors
**Solution:**
```bash
# Ensure pytest is installed
pip install pytest pytest-cov

# Ensure you're in repository root
pwd  # Should show: /Users/demesewabebe/Projects/python
```

### "Permission denied" on run.bat
**Solution:**
- Run from Command Prompt or Git Bash, not PowerShell
- Or use: `python <your-project-name>/run.py`

### Database connection issues
**Solution:**
- Verify `shared_config/.env` has correct `MONGODB_URI_DEV`
- Check network access to database
- Verify credentials are correct

---

## End-to-End Validation Checklist

- [ ] Virtual environment exists and is Python 3.11
- [ ] Virtual environment activated for your shell
- [ ] `common_config` installed in editable mode
- [ ] Dependencies installed
- [ ] Project scaffolded successfully
- [ ] Linting and formatting pass
- [ ] All smoke tests pass
- [ ] Database configuration complete (if needed)
- [ ] Business logic implemented
- [ ] Comprehensive tests written
- [ ] All tests pass with >80% coverage
- [ ] Project runs successfully
- [ ] README documentation complete
- [ ] Code committed to Git

---

## Related Documentation

- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing best practices
- [LINTING.md](LINTING.md) - Code quality tools setup
- [REPOSITORY_STANDARDS.md](REPOSITORY_STANDARDS.md) - Directory structure conventions
- [VENV_SETUP.md](VENV_SETUP.md) - Virtual environment details

---

**Ready to start? Begin with Phase 1, Step 1.1!** 🚀

**Last Updated:** 2025-10-27
