# common_config

Shared configuration, logging, database utilities, and a Typer-based scaffolder
to create new sibling projects with consistent repository standards.

## Features

- **Centralized Pydantic settings** with `.env` support (uses `shared_config/.env`)
- **Standard logging** (console + rotating file) with run timestamp utility
- **MongoDB connection wrapper** with health check and retry logic
- **Typer CLI scaffolder** to create new projects following repository standards
- **Black + Ruff** formatting defaults (120 char line length)
- **Python 3.11** baseline

## Repository Standardization

This package enforces the following repository structure:

```
repository-root/
├── .venv311/              # Shared virtual environment for all projects
├── shared_config/
│   └── .env               # Single source of truth for all environment variables
├── data/
│   ├── input/<project>/   # Per-project input data
│   └── output/<project>/  # Per-project output data
├── logs/<project>/        # Per-project log files
├── artifacts/             # Build outputs (pytest cache, coverage reports)
├── archive/               # Historical/archived files
│   ├── projects/<project>/
│   ├── data/
│   └── logs/
├── tests/                 # Repository-level shared test fixtures
│   └── conftest.py        # Shared pytest fixtures for all projects
└── <project>/             # Individual project directories
    ├── src/<package>/
    ├── tests/
    ├── run.py
    └── README.md
```

**Key Principles:**
- ❌ No per-project `config/`, `data/`, `logs/`, `archive/` directories
- ✅ Single `.env` at `shared_config/.env`
- ✅ Centralized data and logs at repository root
- ✅ Shared virtual environment (`.venv311/`)
- ✅ Consistent testing structure with shared fixtures

## Install (editable for local dev)

```bash
# From repository root
.venv311/Scripts/python -m pip install -e ./common_config

# Or if you have venv activated
pip install -e ./common_config
```

## CLI Scaffolder

Create a new project following repository standards:

```bash
# From repository root
python -m common_config init my_new_project

# Or specify directory
python -m common_config init my_new_project --dir /path/to/workspace
```

This creates:

This creates:

**Project Structure:**
```
my_new_project/
├── src/my_new_project/    # Python package
│   └── __init__.py
├── tests/                  # Tests with smoke tests included
│   ├── __init__.py
│   └── test_my_new_project_smoke.py
├── temp/                   # Temporary files (gitignored)
├── run.py                  # Main entry point
├── run.bat                 # Windows batch script (uses shared venv)
├── pyproject.toml          # Black/Ruff config
├── .gitignore
├── README.md
└── .vscode/settings.json
```

**Centralized Directories Created:**
```
data/input/my_new_project/    # At repository root
data/output/my_new_project/   # At repository root
logs/my_new_project/          # At repository root
```

**Note:** No per-project `config/`, `data/`, `logs/`, or `archive/` directories are created.
All environment variables go in `shared_config/.env` at repository root.

## Using in a Project

### Basic Setup

```python
from pathlib import Path
from common_config.utils.logger import setup_logging, get_logger, get_run_timestamp
from common_config.config.settings import get_settings

# Get settings (loads from shared_config/.env)
settings = get_settings()

# Setup logging to centralized logs directory
log_dir = Path(settings.paths.logs) / "my_project"
log_dir.mkdir(parents=True, exist_ok=True)
setup_logging(log_dir=log_dir)

# Get logger
logger = get_logger(__name__)
logger.info(f"Output dir: {settings.paths.data_output}/my_project/")
```

### Database Connection

```python
from common_config.database.mongodb import MongoDBConnection

# Uses MONGODB_URI and DATABASE_NAME from shared_config/.env
with MongoDBConnection() as conn:
    db = conn.get_database()
    collection = db["MyCollection"]
    doc = collection.find_one({"field": "value"})
```

## Configuration

### Shared .env File

**All projects** use `shared_config/.env` at repository root:

```env
# shared_config/.env

# Application
APP_ENV=LOCL

# MongoDB
MONGODB_URI_LOCL=mongodb://localhost:27017
DATABASE_NAME_LOCL=LocalDatabase

MONGODB_URI_PROD=mongodb://prod-server:27017
DATABASE_NAME_PROD=ProductionDatabase

# Paths (optional overrides)
DATA_INPUT_DIR=data/input
DATA_OUTPUT_DIR=data/output
LOG_DIR=logs
```

**Environment Suffix Resolution:**
- Set `APP_ENV=LOCL` → uses `MONGODB_URI_LOCL`, `DATABASE_NAME_LOCL`
- Set `APP_ENV=PROD` → uses `MONGODB_URI_PROD`, `DATABASE_NAME_PROD`

### Settings Object

All settings are accessed via:

```python
from common_config.config.settings import get_settings

settings = get_settings()
print(settings.mongodb_uri)       # Based on APP_ENV
print(settings.database_name)     # Based on APP_ENV  
print(settings.paths.data_input)  # data/input
print(settings.paths.data_output) # data/output
print(settings.paths.logs)        # logs
```

## Testing

All projects should include tests following the repository standard:

```bash
# Run tests for a specific project
pytest my_project/tests/ -v

# Run all repository tests
pytest tests/ -v

# With coverage
pytest my_project/tests/ --cov=my_project

# Coverage reports go to artifacts/coverage/
```

**Shared Fixtures:**
Use fixtures from `tests/conftest.py` at repository root:
- `mock_mongo_connection` - Mock MongoDB for testing
- `mock_settings` - Mock settings
- `temp_data_dir`, `temp_log_dir` - Temporary directories
- `sample_csv_data`, `sample_patient_data` - Test data

See `docs/TESTING_GUIDE.md` for complete testing documentation.

## CI/CD Integration

Projects automatically tested via GitHub Actions:
1. **Lint** - Ruff linting and formatting checks
2. **Type-check** - Pyright static analysis
3. **Tests** - pytest with coverage reports uploaded to artifacts

See `.github/workflows/README.md` for workflow details.

## Migration from Old Structure

If you have projects with old structure (`config/.env`, per-project `data/`, `logs/`):

1. **Move environment variables** to `shared_config/.env`
2. **Move data files**:
   - `my_project/data/input/*` → `data/input/my_project/`
   - `my_project/data/output/*` → `data/output/my_project/`
3. **Move logs**: `my_project/logs/*` → `logs/my_project/`
4. **Archive old files**: `my_project/archive/*` → `archive/projects/my_project/`
5. **Remove** `my_project/config/`, `my_project/data/`, `my_project/logs/`, `my_project/archive/`
6. **Update code** to use centralized paths:
   ```python
   # Old
   log_dir = Path("logs")
   
   # New  
   log_dir = Path(settings.paths.logs) / "my_project"
   log_dir.mkdir(parents=True, exist_ok=True)
   ```

## Documentation

- `REPOSITORY_STANDARDS.md` - Complete repository structure and standards
- `docs/TESTING_GUIDE.md` - Testing guidelines and fixtures
- `.github/workflows/README.md` - CI/CD pipeline documentation  
- `archive/README.md` - Archive directory usage and policies

## CLI Options Reference

```bash
# Create project with custom package name
python -m common_config init my-new-project --package my_pkg

# Force overwrite existing directory
python -m common_config init my_project --force

# Show help
python -m common_config init --help
```
