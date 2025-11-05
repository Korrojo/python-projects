# Repository-Level Lessons Learned

**Repository**: ubiquityMongo_phiMasking\
**Scope**: Multi-project Python workspace organization\
**Date**: October 2025\
**Focus**: Project structure, shared configuration, and common pitfalls

______________________________________________________________________

## Table of Contents

1. [Project Structure Evolution](#1-project-structure-evolution)
1. [Shared Configuration Challenges](#2-shared-configuration-challenges)
1. [Path Management Issues](#3-path-management-issues)
1. [Logging Standardization](#4-logging-standardization)
1. [Environment Management](#5-environment-management)
1. [Common Pitfalls & Solutions](#6-common-pitfalls--solutions)
1. [Migration Guide](#7-migration-guide)
1. [Best Practices for New Projects](#8-best-practices-for-new-projects)

______________________________________________________________________

## 1. Project Structure Evolution

### Problem: Inconsistent Directory Structures

**Initial State** (Legacy projects):

```
project_name/
├── data/              # ❌ Project-level data dir
│   ├── input/
│   └── output/
├── logs/              # ❌ Project-level logs
├── env/               # ❌ Project-level virtual env
├── config/
│   └── .env           # ❌ Project-level secrets
└── src/
```

**Issues**:

- Every project created its own `data/`, `logs/`, `env/` directories
- Secrets scattered across multiple `.env` files
- Data files hard to find (which project has what?)
- Log files fragmented across project directories
- Disk space wasted with multiple virtual environments
- Confusion about where files are actually stored

**Root Cause**: No central convention when projects were created independently

______________________________________________________________________

### Solution: Unified Repository Structure

**Current Standard** (New projects):

```
repository/
├── shared_config/
│   └── .env                          # ✅ ONE source of truth for all projects
├── common_config/                     # ✅ Shared library (settings, logging, DB)
├── data/                             # ✅ Repo-level data root
│   ├── input/
│   │   ├── project_a/
│   │   ├── project_b/
│   │   └── appointment_comparison/
│   └── output/
│       ├── project_a/
│       ├── project_b/
│       └── appointment_comparison/
├── logs/                             # ✅ Repo-level logs root
│   ├── project_a/
│   ├── project_b/
│   └── appointment_comparison/
├── temp/                             # ✅ Repo-level temp root
│   └── project_name/
├── archive/                          # ✅ Repo-level archive root
│   └── project_name/
├── .venv/                            # ✅ ONE shared virtual environment
├── project_a/                        # ✅ Source code only
│   ├── src/
│   ├── tests/
│   ├── README.md
│   └── requirements.txt
└── project_b/
    ├── src/
    ├── tests/
    └── README.md
```

**Benefits**:

- ✅ All data in one place (`data/input/`, `data/output/`)
- ✅ All logs in one place (`logs/`)
- ✅ Easy to find any project's files
- ✅ One virtual environment for all projects
- ✅ One configuration file for all secrets
- ✅ Clear separation: projects = code, repo root = data/logs/config

______________________________________________________________________

### Lesson 1: Directory Structure Convention

**✅ DO**:

- Create project subdirectories under shared roots (`data/input/project_name/`)
- Use `common_config` for path resolution
- Keep only source code in project directories
- Calculate absolute paths from repo root

**❌ DON'T**:

- Create `data/` or `logs/` directories at project level
- Hard-code paths like `./data/input/`
- Store secrets in project-level `.env` files
- Create per-project virtual environments

**Code Pattern**:

```python
from common_config.config import get_settings

settings = get_settings()

# ✅ GOOD: Use shared paths
input_dir = settings.paths.data_input / "appointment_comparison"
output_dir = settings.paths.data_output / "appointment_comparison"
log_dir = settings.paths.logs / "appointment_comparison"

# ❌ BAD: Hard-coded project-level paths
input_dir = Path("./data/input")  # Wrong! Creates project-level data/
log_dir = Path("./logs")          # Wrong! Creates project-level logs/
```

______________________________________________________________________

## 2. Shared Configuration Challenges

### Problem: Configuration Fragmentation

**Issues We Faced**:

1. **Multiple `.env` Files**: Each project had its own `.env` with duplicate MongoDB URIs
1. **Environment Confusion**: Some used `ENV`, others `ENVIRONMENT`, others `APP_ENV`
1. **Missing Variables**: Forgot to copy all required vars when creating new projects
1. **Secret Management**: Production credentials in multiple files (security risk)
1. **Inconsistent Naming**: `MONGO_URI` vs `MONGODB_CONNECTION_STRING` vs `DB_URI`

**Example Chaos**:

```bash
# Project A's .env
MONGO_URI=mongodb://localhost:27017
DATABASE=UbiquityProduction

# Project B's .env
MONGODB_CONNECTION_STRING=mongodb://localhost:27017
DB_NAME=UbiquityProduction

# Project C's .env (forgot to create)
# Uses hard-coded values in code ❌
```

______________________________________________________________________

### Solution: Single Source of Truth

**Implementation**: `shared_config/.env`

```bash
# One file for ALL projects

# Current environment selector
APP_ENV=PROD  # Options: LOCL, DEV, STG, TRNG, PERF, PRPRD, PROD

# Environment-suffixed connection strings (one per environment)
MONGODB_URI_LOCL=mongodb://localhost:27017
MONGODB_URI_DEV=mongodb://dev-server:27017
MONGODB_URI_PROD=mongodb://prod-cluster:27017

# Database names per environment
DATABASE_NAME_LOCL=UbiquityLOCAL
DATABASE_NAME_DEV=UbiquityDevelopment
DATABASE_NAME_PROD=UbiquityProduction

# Backup directories per environment
BACKUP_DIR_LOCL=~/Backups/local/export
BACKUP_DIR_PROD=F:/mongodrive/backups/prod

# Optional log directory override per environment
LOG_DIR_PROD=F:/logs/prod
```

**Usage in Code**:

```python
from common_config.config import get_settings

settings = get_settings()

# Automatically resolves based on APP_ENV
connection_string = settings.mongodb_uri      # Gets MONGODB_URI_PROD if APP_ENV=PROD
database_name = settings.database_name        # Gets DATABASE_NAME_PROD
backup_dir = settings.backup_dir              # Gets BACKUP_DIR_PROD

# Standard paths (repo-level)
input_dir = settings.paths.data_input / "my_project"
output_dir = settings.paths.data_output / "my_project"
log_dir = settings.paths.logs / "my_project"
```

______________________________________________________________________

### Lesson 2: Environment-Suffixed Variables

**Pattern**: Use environment suffixes for per-environment values

**✅ DO**:

```bash
# shared_config/.env
APP_ENV=PROD

# Suffixed variables (one per environment)
MONGODB_URI_LOCL=...
MONGODB_URI_DEV=...
MONGODB_URI_PROD=...

DATABASE_NAME_LOCL=...
DATABASE_NAME_DEV=...
DATABASE_NAME_PROD=...
```

**❌ DON'T**:

```bash
# ❌ Multiple .env files
project_a/.env
project_b/.env
project_c/.env

# ❌ Hard-coded environment selection
if environment == "production":
    uri = "mongodb://prod..."
```

**Benefits**:

- Switch environments by changing ONE variable (`APP_ENV`)
- All environment configs in one place
- No need to edit code to change environments
- Easier to audit credentials (one file to secure)

______________________________________________________________________

### Lesson 3: Configuration Precedence

**Order** (last wins):

1. `shared_config/.env` (base configuration)
1. Project-level `.env` (rare; for project-specific non-secrets)
1. OS environment variables (runtime overrides)

**Example**:

```bash
# shared_config/.env
APP_ENV=LOCL
MONGODB_URI_LOCL=mongodb://localhost:27017

# Runtime override (for testing)
APP_ENV=DEV python -m my_project --input file.csv

# Or OS environment variable
export APP_ENV=DEV
python -m my_project --input file.csv
```

**Use Cases**:

- Development: Use `APP_ENV=LOCL` in `shared_config/.env`
- CI/CD: Set `APP_ENV=STG` as environment variable
- Production: Set `APP_ENV=PROD` as environment variable
- Quick testing: Override at runtime with `APP_ENV=DEV python ...`

______________________________________________________________________

## 3. Path Management Issues

### Problem: Log Files in Wrong Locations

**Real Issue from appointment_comparison**:

**Initial Code** (WRONG):

```python
# In __main__.py
log_dir = Path("logs") / "appointment_comparison"  # ❌ Relative path!
log_dir.mkdir(parents=True, exist_ok=True)
```

**Result**:

```
appointment_comparison/
└── logs/                           # ❌ Created in project directory!
    └── appointment_comparison/
        └── 20251023_224543_app.log
```

**Expected**:

```
repository/
└── logs/                           # ✅ Should be in repo root!
    └── appointment_comparison/
        └── 20251023_224543_app.log
```

**Why This Happened**:

- Used relative path `Path("logs")` instead of absolute
- Created directory relative to current working directory
- Working directory was project directory (not repo root)

______________________________________________________________________

### Solution: Always Use Absolute Paths

**Fixed Code**:

```python
from pathlib import Path
from common_config.config import get_settings

settings = get_settings()

# ✅ CORRECT: Use absolute path from settings
log_dir = settings.paths.logs / "appointment_comparison"
log_dir.mkdir(parents=True, exist_ok=True)

# Or calculate from python_root
python_root = Path(__file__).resolve().parent.parent  # Go up to repo root
log_dir = python_root / "logs" / "appointment_comparison"
```

**How `common_config` Calculates Paths**:

```python
# In common_config/src/common_config/config/settings.py
class PathConfig:
    def __init__(self):
        # Find repo root (where shared_config/.env lives)
        self.repo_root = self._find_repo_root()
        
        # All paths calculated from repo root (absolute)
        self.data_input = self.repo_root / "data" / "input"
        self.data_output = self.repo_root / "data" / "output"
        self.logs = self.repo_root / "logs"
        self.temp = self.repo_root / "temp"
        self.archive = self.repo_root / "archive"
    
    def _find_repo_root(self) -> Path:
        """Find repository root by looking for shared_config/.env"""
        current = Path(__file__).resolve()
        while current != current.parent:
            if (current / "shared_config" / ".env").exists():
                return current
            current = current.parent
        raise RuntimeError("Cannot find repo root (shared_config/.env)")
```

______________________________________________________________________

### Lesson 4: Path Resolution Rules

**✅ DO**:

```python
from common_config.config import get_settings

settings = get_settings()

# For shared directories (data, logs, temp, archive)
input_dir = settings.paths.data_input / "my_project"
output_dir = settings.paths.data_output / "my_project"
log_dir = settings.paths.logs / "my_project"

# Create project subdirectories
input_dir.mkdir(parents=True, exist_ok=True)
output_dir.mkdir(parents=True, exist_ok=True)
log_dir.mkdir(parents=True, exist_ok=True)

# Use absolute paths for file operations
input_file = input_dir / "data.csv"
output_file = output_dir / f"{timestamp}_output.csv"
log_file = log_dir / f"{timestamp}_app.log"
```

**❌ DON'T**:

```python
# ❌ Relative paths (creates dirs in current working directory)
log_dir = Path("logs")
data_dir = Path("./data/input")

# ❌ Hard-coded absolute paths (not portable)
log_dir = Path("F:/ubiquityMongo_phiMasking/python/logs")

# ❌ Project-level data/logs directories
log_dir = Path(__file__).parent / "logs"  # In project dir!
```

______________________________________________________________________

### Lesson 5: Current Working Directory Issues

**Problem**: Scripts behave differently depending on where you run them from

**Example**:

```bash
# Running from repo root
cd /repo
python project_a/run.py
# Relative path "logs/" creates /repo/logs/ ✅

# Running from project directory
cd /repo/project_a
python run.py
# Relative path "logs/" creates /repo/project_a/logs/ ❌
```

**Solution**: Always use absolute paths (no dependency on CWD)

```python
from common_config.config import get_settings

settings = get_settings()
log_dir = settings.paths.logs / "project_a"  # Always /repo/logs/project_a
```

**Benefits**:

- Works regardless of where script is run from
- Consistent behavior in dev vs CI/CD
- No "works on my machine" issues

______________________________________________________________________

## 4. Logging Standardization

### Problem: Inconsistent Logging Practices

**Issues We Faced**:

1. **Different log formats**: Some projects used JSON, others plain text
1. **Different log locations**: `logs/`, `./logs/`, `<project>/logs/`
1. **No timestamps in filenames**: Hard to find specific run logs
1. **Missing log rotation**: Logs grew indefinitely
1. **Inconsistent log levels**: Some DEBUG, some INFO, no standard

**Example Chaos**:

```
project_a/logs/app.log                    # No timestamp
project_b/application.log                 # Different name
logs/project_c/2025-10-23.log            # Only date, no time
/tmp/project_d.log                        # In system temp!
```

______________________________________________________________________

### Solution: Standardized Logging Pattern

**Implemented in `common_config`**:

```python
from common_config.utils.logger import get_logger, get_run_timestamp

# Get logger with standard format
logger = get_logger(__name__)

# Generate timestamp for filenames
timestamp = get_run_timestamp()  # Returns: "20251023_224543"

# Standard log file path
log_file = settings.paths.logs / "project_name" / f"{timestamp}_app.log"

# Configure logging
setup_logging(log_file, level=logging.INFO)

# Log with context
logger.info("Starting validation")
logger.info(f"Input file: {input_path}")
logger.info(f"Processing 2127 rows...")
logger.info("Validation complete!")
```

**Standard Format**:

```
2025-10-23 22:45:43 | INFO | module.name | Message here
2025-10-23 22:45:44 | WARNING | module.name | Warning message
2025-10-23 22:45:45 | ERROR | module.name | Error message with context
```

______________________________________________________________________

### Lesson 6: Logging Best Practices

**Standard Pattern**:

```python
from pathlib import Path
from common_config.config import get_settings
from common_config.utils.logger import get_logger, get_run_timestamp

# 1. Get settings and timestamp
settings = get_settings()
timestamp = get_run_timestamp()

# 2. Create log directory
log_dir = settings.paths.logs / "my_project"
log_dir.mkdir(parents=True, exist_ok=True)

# 3. Create log file with timestamp
log_file = log_dir / f"{timestamp}_app.log"

# 4. Get logger
logger = get_logger(__name__)

# 5. Log startup info
logger.info("=" * 80)
logger.info("Starting my_project")
logger.info(f"Input file: {input_path}")
logger.info(f"Environment: {settings.app_env}")
logger.info(f"Database: {settings.database_name}")
logger.info("=" * 80)

# 6. Log progress
for i in range(0, total, 100):
    logger.info(f"Processed {i}/{total} rows")

# 7. Log completion
logger.info("=" * 80)
logger.info("Processing complete!")
logger.info(f"Output file: {output_path}")
logger.info("=" * 80)
```

**File Naming Convention**:

```
logs/
└── project_name/
    ├── 20251023_224543_app.log       # Main application log
    ├── 20251023_225612_export.log    # Specific operation log
    └── 20251024_093015_import.log    # Another operation
```

**Benefits**:

- Easy to find logs for specific runs (timestamp in filename)
- Consistent format across all projects
- Clear separation by project (subdirectories)
- Standard log levels and structure

______________________________________________________________________

## 5. Environment Management

### Problem: Virtual Environment Duplication

**Initial State**:

```
project_a/
└── env/                    # ❌ 500MB virtual environment
    └── ...

project_b/
└── venv/                   # ❌ Another 500MB
    └── ...

project_c/
└── .venv/                  # ❌ Another 500MB
    └── ...

# Total: 1.5GB+ for 3 projects with same dependencies!
```

**Issues**:

- Disk space waste (multiple copies of same packages)
- Dependency conflicts (different versions across projects)
- Setup overhead (create venv for each project)
- Maintenance burden (update packages in multiple places)

______________________________________________________________________

### Solution: Single Shared Virtual Environment

**Current Standard**:

```
repository/
├── .venv/                          # ✅ ONE virtual environment
│   └── ...                         # Contains all dependencies
├── common_config/
│   └── (installed editable)
├── project_a/
├── project_b/
└── project_c/
```

**Setup Process**:

```bash
# 1. Create ONE virtual environment at repo root
cd /repository
python -m venv .venv

# 2. Activate (do once per terminal session)
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Git Bash / macOS / Linux:
source ./.venv/bin/activate

# 3. Install shared library (editable)
pip install -e ./common_config

# 4. Install project-specific dependencies as needed
pip install -r project_a/requirements.txt
pip install -r project_b/requirements.txt

# 5. Run any project from repo root
python -m project_a --input data.csv
python -m project_b --input data.csv
```

______________________________________________________________________

### Lesson 7: Shared Virtual Environment

**✅ DO**:

- Create ONE `.venv/` at repository root
- Install `common_config` editable: `pip install -e ./common_config`
- Install project dependencies: `pip install -r project_name/requirements.txt`
- Activate venv before running any project
- Add `.venv/` to `.gitignore`

**❌ DON'T**:

- Create `env/`, `venv/`, or `.venv/` in project directories
- Install packages system-wide (use venv)
- Commit virtual environment to git
- Mix Python versions across projects

**Benefits**:

- Disk space savings (one copy of packages)
- Consistent dependencies across projects
- Easier maintenance (update once)
- Faster project setup (venv already exists)

______________________________________________________________________

## 6. Common Pitfalls & Solutions

### Pitfall 1: "Module Not Found" Errors

**Symptom**:

```bash
python project_a/run.py
ModuleNotFoundError: No module named 'common_config'
```

**Cause**: `common_config` not installed or venv not activated

**Solution**:

```bash
# Ensure venv is activated
source ./.venv/bin/activate  # or .\.venv\Scripts\Activate.ps1

# Install common_config editable
pip install -e ./common_config

# Verify installation
python -c "from common_config.config import get_settings; print('OK')"
```

______________________________________________________________________

### Pitfall 2: "Cannot Find .env File" Errors

**Symptom**:

```bash
RuntimeError: Cannot find shared_config/.env file
```

**Cause**: `shared_config/.env` doesn't exist or is in wrong location

**Solution**:

```bash
# Check if file exists
ls shared_config/.env

# If missing, create it
cp shared_config/.env.example shared_config/.env  # If example exists
# Or create manually with required variables

# Required variables:
# APP_ENV=LOCL
# MONGODB_URI_LOCL=mongodb://localhost:27017
# DATABASE_NAME_LOCL=UbiquityLOCAL
```

______________________________________________________________________

### Pitfall 3: Files Created in Wrong Directories

**Symptom**: Files appear in project directories instead of shared `data/` or `logs/`

**Example**:

```
project_a/
├── data/          # ❌ Wrong! Should be in /repository/data/
└── logs/          # ❌ Wrong! Should be in /repository/logs/
```

**Cause**: Using relative paths like `Path("data")` or `Path("./logs")`

**Solution**:

```python
# ❌ BAD: Relative paths
data_dir = Path("data/input")
log_dir = Path("logs")

# ✅ GOOD: Use common_config paths
from common_config.config import get_settings
settings = get_settings()
data_dir = settings.paths.data_input / "project_name"
log_dir = settings.paths.logs / "project_name"

# Always create project subdirectories
data_dir.mkdir(parents=True, exist_ok=True)
log_dir.mkdir(parents=True, exist_ok=True)
```

______________________________________________________________________

### Pitfall 4: Environment Variable Not Found

**Symptom**:

```bash
KeyError: 'MONGODB_URI_PROD'
```

**Cause**: Variable not defined for current environment

**Solution**:

```bash
# Check current environment
python -c "from common_config.config import get_settings; print(get_settings().app_env)"

# Ensure variable exists for that environment
# In shared_config/.env:
MONGODB_URI_PROD=mongodb://...
DATABASE_NAME_PROD=UbiquityProduction
```

______________________________________________________________________

### Pitfall 5: Import Errors from Project Modules

**Symptom**:

```bash
ModuleNotFoundError: No module named 'project_a.module'
```

**Cause**: Project not installed or wrong import path

**Solution**:

**Option 1**: Install project editable (if it has `pyproject.toml` or `setup.py`)

```bash
pip install -e ./project_a
python -c "from project_a.module import func; print('OK')"
```

**Option 2**: Run as module from repo root

```bash
cd /repository
python -m project_a.run --input data.csv
```

**Option 3**: Add repo root to PYTHONPATH

```bash
export PYTHONPATH=/repository:$PYTHONPATH
python project_a/run.py
```

______________________________________________________________________

## 7. Migration Guide

### Migrating Legacy Projects to Unified Structure

**Step 1: Assess Current State**

```bash
# Check if project has local data/logs directories
ls -la project_name/
# Look for: data/, logs/, env/, venv/, .venv/, config/.env
```

**Step 2: Move Data Files**

```bash
# Create shared directory structure
mkdir -p data/input/project_name
mkdir -p data/output/project_name
mkdir -p logs/project_name

# Move existing data
mv project_name/data/input/* data/input/project_name/
mv project_name/data/output/* data/output/project_name/

# Move existing logs
mv project_name/logs/* logs/project_name/

# Remove project-level directories
rm -rf project_name/data
rm -rf project_name/logs
```

**Step 3: Update Configuration**

```bash
# Remove project-level .env
rm project_name/.env
rm project_name/config/.env

# Ensure variables exist in shared_config/.env
# Add any project-specific variables
```

**Step 4: Update Code**

```python
# Replace hard-coded paths
# ❌ OLD:
data_dir = Path("data/input")
log_dir = Path("logs")

# ✅ NEW:
from common_config.config import get_settings
settings = get_settings()
data_dir = settings.paths.data_input / "project_name"
log_dir = settings.paths.logs / "project_name"
```

**Step 5: Update Documentation**

````markdown
# Update project README.md

## Setup

1. Activate shared virtual environment:
   ```bash
   source ./.venv/bin/activate
````

2. Install dependencies (if not already installed):

   ```bash
   pip install -r project_name/requirements.txt
   ```

1. Run project:

   ```bash
   python -m project_name --input file.csv --env PROD
   ```

## Paths

- Input files: `data/input/project_name/`
- Output files: `data/output/project_name/`
- Logs: `logs/project_name/`
- Configuration: `shared_config/.env`

````

**Step 6: Test Migration**
```bash
# Test with small dataset
python -m project_name --input test_data.csv --limit 10

# Verify files created in correct locations
ls data/output/project_name/
ls logs/project_name/

# Check no files created in project directory
ls -la project_name/  # Should NOT have data/ or logs/
````

______________________________________________________________________

## 8. Best Practices for New Projects

### Checklist for Starting a New Project

**Before Writing Code**:

- [ ] Read `docs/MONGODB_VALIDATION_BEST_PRACTICES.md`
- [ ] Review existing project structure (`appointment_comparison`, `patients_hcmid_validator`)
- [ ] Plan your statistics output format
- [ ] Identify required MongoDB indexes

**Project Setup**:

- [ ] Create project directory (code only): `mkdir my_project`

- [ ] Create standard structure:

  ```bash
  mkdir -p my_project/src/my_project
  mkdir -p my_project/tests
  mkdir -p my_project/docs
  ```

- [ ] Create shared directories (if not exist):

  ```bash
  mkdir -p data/input/my_project
  mkdir -p data/output/my_project
  mkdir -p logs/my_project
  ```

- [ ] Add required variables to `shared_config/.env`:

  ```bash
  # If project needs specific variables
  MY_PROJECT_SETTING_LOCL=value
  MY_PROJECT_SETTING_PROD=value
  ```

**Code Setup**:

- [ ] Use `common_config` for settings:

  ```python
  from common_config.config import get_settings
  settings = get_settings()
  ```

- [ ] Use shared paths:

  ```python
  input_dir = settings.paths.data_input / "my_project"
  output_dir = settings.paths.data_output / "my_project"
  log_dir = settings.paths.logs / "my_project"
  ```

- [ ] Implement batch processing from start

- [ ] Add `--limit` flag for testing

- [ ] Add progress logging (every 100 rows)

- [ ] Implement statistics with math verification

- [ ] Handle missing data gracefully

**Documentation**:

- [ ] Create `my_project/README.md` with:
  - Project overview
  - Setup instructions
  - Usage examples
  - Configuration details
  - Paths (using shared directories)
- [ ] Document MongoDB queries (if applicable)
- [ ] Document required indexes
- [ ] Add examples to main repository README

**Testing**:

- [ ] Test with `--limit 10` (smoke test)
- [ ] Test with `--limit 100` (validation test)
- [ ] Verify output files in correct locations
- [ ] Verify log files in correct locations
- [ ] Test from different working directories
- [ ] Test environment switching (`APP_ENV=DEV`, `APP_ENV=PROD`)

**After Completion**:

- [ ] Create `my_project/LESSONS_LEARNED.md`
- [ ] Update `docs/MONGODB_VALIDATION_BEST_PRACTICES.md` if new patterns
- [ ] Add to main README's project list
- [ ] Document performance metrics

______________________________________________________________________

### Standard Project Template

```
my_project/
├── README.md                       # Project overview and usage
├── requirements.txt                # Project-specific dependencies
├── run.py                          # Optional: convenience entry point
├── src/
│   └── my_project/
│       ├── __init__.py
│       ├── __main__.py            # CLI entry point
│       ├── validator.py           # Main orchestration
│       ├── db_matcher.py          # Database queries
│       ├── comparator.py          # Comparison logic
│       ├── file_handler.py        # File I/O
│       └── models.py              # Data models
├── tests/
│   ├── __init__.py
│   ├── test_validator.py
│   ├── test_comparator.py
│   └── fixtures/
│       └── sample_data.py
└── docs/
    ├── AGGREGATION_QUERIES.md     # MongoDB queries
    ├── INDEX_CREATION.md          # Index documentation
    └── LESSONS_LEARNED.md         # Post-project insights
```

**Files NOT in project directory** (use shared locations):

- ❌ `data/` - Use `repository/data/input/my_project/` and `repository/data/output/my_project/`
- ❌ `logs/` - Use `repository/logs/my_project/`
- ❌ `env/`, `venv/`, `.venv/` - Use `repository/.venv/`
- ❌ `config/.env` - Use `repository/shared_config/.env`

______________________________________________________________________

## Summary of Key Lessons

### Top 10 Organizational Lessons

1. **Centralize Configuration**: Use `shared_config/.env` for all projects
1. **Centralize Data & Logs**: Use repo-level `data/`, `logs/` directories
1. **Use Absolute Paths**: Never use relative paths for data/logs
1. **Environment Suffixes**: Use `_LOCL`, `_DEV`, `_PROD` suffixes for variables
1. **Shared Virtual Environment**: One `.venv/` at repo root for all projects
1. **Standard Directory Structure**: Keep only source code in project directories
1. **Common Config Library**: Use `common_config` for settings, logging, DB
1. **Project Subdirectories**: Create `data/input/project_name/` subdirectories
1. **Consistent Logging**: Use `common_config.utils.logger` for standard format
1. **Document Everything**: README + LESSONS_LEARNED for every project

______________________________________________________________________

### Quick Reference Commands

**Verify Configuration**:

```bash
python -c "from common_config.config import get_settings; s=get_settings(); print(f'ENV={s.app_env}\nDB={s.database_name}\nData In={s.paths.data_input}\nData Out={s.paths.data_output}\nLogs={s.paths.logs}')"
```

**Check Where Files Will Be Created**:

```python
from common_config.config import get_settings
settings = get_settings()
print(f"Input:  {settings.paths.data_input / 'my_project'}")
print(f"Output: {settings.paths.data_output / 'my_project'}")
print(f"Logs:   {settings.paths.logs / 'my_project'}")
```

**Test Environment Switching**:

```bash
APP_ENV=LOCL python -c "from common_config.config import get_settings; print(get_settings().database_name)"
APP_ENV=PROD python -c "from common_config.config import get_settings; print(get_settings().database_name)"
```

______________________________________________________________________

**Document Version**: 1.0\
**Last Updated**: October 24, 2025\
**Repository**: ubiquityMongo_phiMasking\
**Maintainer**: Development Team
