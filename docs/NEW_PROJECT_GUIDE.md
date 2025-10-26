# Creating a New Project - Step-by-Step Guide
# This guide walks you through starting a new project in this repository, ensuring your environment is correct and all setup steps are validated end-to-end.

## 0. Check for Existing Virtual Environment

Before starting, check if a shared virtual environment exists and is using Python 3.11:

```bash
ls -d .venv*  # Should show .venv311
```

Verify Python version:

```bash
# Bash/macOS/Linux
source .venv311/bin/activate
python --version  # Should show Python 3.11.x

# PowerShell (Windows)
./.venv311/Scripts/Activate.ps1
python --version  # Should show Python 3.11.x
```

If the venv is missing or not Python 3.11, create it using the automated scripts:

```bash
# Bash/Git Bash/macOS/Linux
./install_venv.sh

# PowerShell (Windows)
./install_venv.ps1
```

Follow the printed instructions to activate the venv for your shell.

## 1. Activate the Virtual Environment

Always activate the shared venv before running any setup or project commands:

```bash
# Bash/macOS/Linux
source activate_venv.sh
# PowerShell (Windows)
./activate_venv.ps1
# CMD (Windows)
.venv311/Scripts/activate.bat
```

Verify activation:
```bash
which python  # Should show path to .venv311
python --version  # Should show Python 3.11.x
```

This guide walks you through creating a new project in this repository using the standardized scaffolder.

## Prerequisites


2. **common_config package installed:**
   ```bash
   pip install -e ./common_config
   ```

3. **You are in the repository root:**
   ```bash
   cd /path/to/ubiquityMongo_phiMasking/python
   ```

---

## Step 1: Create the Project
> **Note:** Always activate your venv before running the scaffolder or any install commands.

Run the scaffolder with your project name:

```bash
python -m common_config <project-name>
```

**Example:**
```bash
python -m common_config db_collection_reporter
```

**Options available:**
- `--dir` / `-d`: Create in a specific directory (default: current directory)
- `--package` / `-p`: Override Python package name (default: derived from project name)
- `--force`: Overwrite if folder exists

**Expected output:**
```
✅ Project created at: ./db_collection_reporter

📁 Structure:
   db_collection_reporter/
   ├── src/
   ├── tests/
   ├── scripts/     (index creation, migrations, etc.)
   ├── temp/
   ├── run.py
   ├── run.bat
   ├── .gitignore
   └── README.md

📁 Centralized directories created:
   data/input/db_collection_reporter/
   data/output/db_collection_reporter/
   logs/db_collection_reporter/

ℹ️  Uses repository-level settings:
   - .vscode/settings.json (at repo root)
   - shared_config/.env
   - .venv311/ (shared virtual environment)

Next steps:
  1) Add to shared_config/.env if new database connection needed
  2) Install in shared venv: cd .. && .venv311/Scripts/python -m pip install -e common_config
  3) Run tests: pytest db_collection_reporter/tests/ -v
  4) Run project: python db_collection_reporter/run.py
```

---

## Step 2: Configure Database Connection (if needed)

If your project needs database access, add credentials to `shared_config/.env`:

```bash
# Open the shared environment file
code shared_config/.env
```

Add your connection string (if not already present):
```env
MONGODB_URI=mongodb://username:password@host:port/database?authSource=admin
```

**Note:** All projects share this `.env` file - no per-project config files.

---

## Step 3: Install Project Dependencies
> **Tip:** Always activate your venv before installing dependencies.

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
   echo "special-library==1.0.0" > db_collection_reporter/requirements.txt
   ```

2. **Install it:**
   ```bash
   pip install -r db_collection_reporter/requirements.txt
   ```

**Best Practice:** Prefer Option 1 (root-level) to avoid version conflicts and duplication.

---

## Step 4: Implement Your Logic
> **Tip:** Activate your venv before editing, running, or testing code.

### Main Entry Point: `run.py`

The scaffolder creates a template `run.py` with:
- Logging setup (outputs to `logs/<project>/`)
- Settings loading from `shared_config/.env`
- Basic structure

**Edit it:**
```bash
code db_collection_reporter/run.py
```

### Create Modules in `src/`

Add your business logic:
```bash
# Create a module
code db_collection_reporter/src/db_collection_reporter/collector.py
```

### Utility Scripts in `scripts/`

For maintenance tasks (index creation, migrations):
```bash
code db_collection_reporter/scripts/create_indexes.py
```

---

## Step 5: Write Tests
> **Tip:** Activate your venv before running tests.

The scaffolder creates initial smoke tests in `tests/test_<package>_smoke.py`.

**Add more tests:**
```bash
code db_collection_reporter/tests/test_collector.py
```

**Run tests:**
```bash
pytest db_collection_reporter/tests/ -v
```

**With coverage:**
```bash
pytest db_collection_reporter/tests/ --cov=db_collection_reporter --cov-report=term-missing
```

---

## Step 6: Run Your Project
> **Tip:** Activate your venv before running the project.

### Option 1: Direct Python
```bash
python db_collection_reporter/run.py
```

### Option 2: Windows Batch File
```bash
db_collection_reporter\run.bat
```

The batch file automatically activates the shared venv and runs `run.py`.

---

## Project Structure Reference

After scaffolding, your project has:

```
db_collection_reporter/
├── src/
│   └── db_collection_reporter/      # Your Python package
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_db_collection_reporter_smoke.py
├── scripts/                          # Maintenance scripts
│   └── README.md
├── temp/                             # Temporary files (gitignored)
│   └── .gitkeep
├── run.py                           # Main entry point
├── run.bat                          # Windows launcher
├── .gitignore                       # Project-specific ignores
├── pyproject.toml                   # Python tooling config
└── README.md                        # Project documentation
```

**Centralized directories at repository root:**
```
data/
├── input/db_collection_reporter/    # Input files
└── output/db_collection_reporter/   # Output files

logs/db_collection_reporter/         # Log files

artifacts/                           # Build outputs (shared)
├── .pytest_cache/
├── .ruff_cache/
├── coverage/
└── test-reports/
```

---

## What's NOT Created (Centralized at Repo Root)

The scaffolder **does NOT** create:
- ❌ `config/` - Use `shared_config/.env` instead
- ❌ `data/` - Uses centralized `data/input/<project>/` and `data/output/<project>/`
- ❌ `logs/` - Uses centralized `logs/<project>/`
- ❌ `archive/` - Uses centralized `archive/projects/<project>/`
- ❌ `.vscode/settings.json` - Uses repository root settings
- ❌ Per-project `.env` - Uses `shared_config/.env`

---

## Integration with CI/CD

Your project is automatically included in the GitHub Actions pipeline:

1. **Linting**: Ruff checks code quality
2. **Type Checking**: Pyright validates types
3. **Testing**: Pytest runs all tests with coverage

No additional setup needed - just push your code!

---

## Common Tasks Quick Reference

| Task | Command |
|------|---------|
| Check/Create venv | `./install_venv.sh` or `./install_venv.ps1` |
| Activate venv | `source activate_venv.sh` or `./activate_venv.ps1` |
| Create project | `python -m common_config <name>` |
| Install dependencies | `pip install -r requirements.txt` |
| Run project | `python <project>/run.py` |
| Run tests | `pytest <project>/tests/ -v` |
| Check coverage | `pytest <project>/tests/ --cov=<package>` |
| Lint code | `ruff check <project>/` |
| Format code | `ruff format <project>/` |
| Type check | `pyright <project>/` |

---

## Troubleshooting

### "Module not found" errors
- Ensure `common_config` is installed: `pip install -e common_config`
- Ensure you're in the shared venv: `.venv311\Scripts\activate`

### "Permission denied" on run.bat
- Run from Command Prompt or Git Bash, not PowerShell
- Or use: `python <project>/run.py`

### Tests not discovered
- Ensure test files start with `test_`
- Ensure test functions start with `test_`
- Check `pytest.ini` settings in root `pyproject.toml`

### Database connection issues
- Verify `shared_config/.env` has correct `MONGODB_URI`
- Check network access to database
- Verify credentials are correct

---

## Next Steps


## End-to-End Validation Checklist

1. **Virtual environment exists and is Python 3.11**
2. **Virtual environment activated for your shell**
3. **common_config installed in editable mode**
4. **Dependencies installed**
5. **Project scaffolded and code implemented**
6. **Linting, formatting, and type checking pass**
   - `ruff check .`
   - `ruff format --check .`
   - `pyright .`
7. **Tests pass**
   - `pytest -q --maxfail=1 --disable-warnings`
8. **Project runs successfully**

---

Review `TESTING_GUIDE.md` for testing best practices
Check `.github/workflows/README.md` for CI/CD details
See `REPOSITORY_STANDARDS.md` for overall architecture

**Happy coding!** 🚀
