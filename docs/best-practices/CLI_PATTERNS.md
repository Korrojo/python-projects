# Standard CLI Patterns

**Version:** 1.0
**Last Updated:** 2025-01-27

This document defines the standard CLI patterns used across all Python projects in this repository.

---

<details open>
<summary><strong>📖 Table of Contents</strong> (click to expand/collapse)</summary>

- [Overview](#overview)
- [Standard CLI Options](#standard-cli-options)
  - [1. Environment Selection (`--env`)](#1-environment-selection---env)
  - [2. Collection Name (`--collection` / `-c`)](#2-collection-name---collection----c)
  - [3. What Goes in `.env` vs CLI](#3-what-goes-in-env-vs-cli)
- [Standard Command Template](#standard-command-template)
- [🔒 Security Requirements](#-security-requirements)
  - [Credential Redaction in Logs](#credential-redaction-in-logs)
  - [Available Security Utilities](#available-security-utilities)
  - [Security Checklist](#security-checklist)
- [Standard Option Naming Conventions](#standard-option-naming-conventions)
- [Examples](#examples)
  - [Example 1: Single Collection Processing](#example-1-single-collection-processing)
  - [Example 2: All Collections Processing](#example-2-all-collections-processing)
  - [Example 3: Flexible Collection Selection](#example-3-flexible-collection-selection)
- [Migration Guide](#migration-guide)
  - [Before (Non-Standard)](#before-non-standard)
  - [After (Standard)](#after-standard)
- [Checklist for New Projects](#checklist-for-new-projects)
- [Benefits of This Pattern](#benefits-of-this-pattern)
- [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
- [Related Documentation](#related-documentation)

</details>

---

## Overview

All projects that use CLI commands should follow these standardized patterns for consistency, maintainability, and ease of use.

---

## Standard CLI Options

### 1. Environment Selection (`--env`)

**Purpose:** Switch between environments (DEV, PROD, STG, etc.) without modifying `.env` files

**Pattern:**
```python
env: str = typer.Option(
    None,
    "--env",
    help="Environment to use (DEV, PROD, STG, etc.) - overrides APP_ENV",
)
```

**Implementation:**
```python
if env:
    os.environ["APP_ENV"] = env.upper()

settings = get_settings()  # Will now use environment-specific variables
```

**Usage:**
```bash
# Use default environment from .env
python my_project/run.py command

# Use PROD environment
python my_project/run.py command --env PROD

# Use STG environment
python my_project/run.py command --env STG
```

**Environment Configuration in `.env`:**
```bash
# Default environment
APP_ENV=DEV

# DEV environment variables
MONGODB_URI_DEV=mongodb://localhost:27017
DATABASE_NAME_DEV=dev_database

# PROD environment variables
MONGODB_URI_PROD=mongodb://prod-server:27017
DATABASE_NAME_PROD=production_database

# STG environment variables
MONGODB_URI_STG=mongodb://staging-server:27017
DATABASE_NAME_STG=staging_database
```

**Priority Order:**
1. `--env` CLI option (highest priority)
2. `APP_ENV` environment variable
3. Default in `.env` file

---

### 2. Collection Name (`--collection` / `-c`)

**Purpose:** Specify MongoDB collection name(s) to operate on

**Pattern:**
```python
collection: str = typer.Option(
    None,
    "--collection",
    "-c",
    help="Collection name to process",
)
```

**❌ DO NOT put collection names in `.env` files**
**✅ ALWAYS pass collection names via CLI**

**Reason:** Collection names are:
- Specific to each command execution
- Not environment-wide configuration
- May vary per operation
- Should be explicit, not hidden in config

**Usage:**
```bash
# Process specific collection
python my_project/run.py command --collection Patients

# Short form
python my_project/run.py command -c Patients

# Combine with environment
python my_project/run.py command --collection Patients --env PROD
```

---

### 3. What Goes in `.env` vs CLI

**❌ DO NOT put in `.env`:**
- Collection names
- Specific IDs or filters
- Operation-specific parameters
- Temporary/one-time values

**✅ DO put in `.env`:**
- MongoDB connection URIs
- Database names
- API keys
- Credentials
- Environment-wide settings
- Log/data directory paths

**Rule of Thumb:**
- `.env` = Configuration that rarely changes per environment
- CLI = Parameters that change per execution

---

## Standard Command Template

Use this template when creating new CLI commands:

```python
import os
from pathlib import Path
import typer

from common_config.config.settings import get_settings
from common_config.connectors.mongodb import get_mongo_client
from common_config.utils.logger import get_logger, setup_logging
from common_config.utils.security import redact_uri  # ⭐ REQUIRED for credential safety

app = typer.Typer(
    help="Project description",
    no_args_is_help=True,
)

@app.command("command-name")
def command_name(
    env: str = typer.Option(
        None,
        "--env",
        help="Environment to use (DEV, PROD, STG, etc.) - overrides APP_ENV",
    ),
    collection: str = typer.Option(
        None,
        "--collection",
        "-c",
        help="Collection name to process",
    ),
    # Add other command-specific options here
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview changes without executing",
    ),
):
    """Command description.

    Detailed explanation of what this command does.
    """
    # 1. Set environment if provided
    if env:
        os.environ["APP_ENV"] = env.upper()

    # 2. Get settings (will use environment-specific variables)
    settings = get_settings()
    log_dir = Path(settings.paths.logs) / "project_name"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir)
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info(f"Project Name - Command Name")
    logger.info("=" * 60)

    # 3. Connect to MongoDB
    try:
        with get_mongo_client(
            mongodb_uri=settings.mongodb_uri,
            database_name=settings.database_name
        ) as client:
            db = client[settings.database_name]

            logger.info(f"Environment: {env.upper() if env else os.environ.get('APP_ENV', 'default')}")
            logger.info(f"MongoDB URI: {redact_uri(settings.mongodb_uri)}")  # ⚠️ ALWAYS redact URIs
            logger.info(f"Database: {settings.database_name}")

            # 4. Validate collection parameter if required
            if not collection:
                logger.error("Collection name is required")
                print("❌ Error: --collection is required")
                raise typer.Exit(code=1)

            logger.info(f"Collection: {collection}")

            # 5. Execute core logic
            logger.info("Executing command...")
            # Your code here

            # 6. Display results
            print("\nResults:")
            # Your output here

            logger.info("Completed successfully")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
```

---

## 🔒 Security Requirements

### Credential Redaction in Logs

**⚠️ CRITICAL:** Never log credentials or sensitive information.

**❌ NEVER do this:**
```python
logger.info(f"MongoDB URI: {settings.mongodb_uri}")
# Logs: mongodb+srv://<username>:<password>@host/...  ← EXPOSES CREDENTIALS!
```

**✅ ALWAYS do this:**
```python
from common_config.utils.security import redact_uri

logger.info(f"MongoDB URI: {redact_uri(settings.mongodb_uri)}")
# Logs: mongodb+srv://***:***@host/...  ← Safe for logs
```

### Available Security Utilities

```python
from common_config.utils.security import (
    redact_uri,           # Redact credentials from URIs
    redact_password,      # Redact passwords from text
    get_safe_connection_info,  # Get safe connection info dict
)

# Redact MongoDB URIs
safe_uri = redact_uri("mongodb://<username>:<password>@host:27017/db")
# Returns: "mongodb://***:***@host:27017/db"

# Redact passwords from any text
safe_text = redact_password("password=secret123")
# Returns: "password=***"

# Get safe connection info for logging
info = get_safe_connection_info(uri, database)
# Returns: {'database': 'mydb', 'uri': 'mongodb://***:***@host:27017', 'host': 'host', ...}
```

### Security Checklist

When implementing CLI commands:

- [ ] Import `redact_uri` from `common_config.utils.security`
- [ ] Use `redact_uri()` for ALL URI logging
- [ ] Never log passwords or API keys
- [ ] Never print sensitive data to console
- [ ] Review log files for accidental credential exposure
- [ ] Use environment variables (not hardcoded) for credentials

**Consequences of logging credentials:**
- Security vulnerability
- Credentials exposed in log files
- Credentials exposed in CI/CD logs
- Credentials exposed in error tracking systems
- Compliance violations (SOC2, GDPR, etc.)

---

## Standard Option Naming Conventions

**Environment Selection:**
- Long: `--env`
- No short form
- Values: DEV, PROD, STG (uppercase)

**Collection Name:**
- Long: `--collection`
- Short: `-c`
- Value: Collection name as it appears in MongoDB

**Database Override (rare, avoid if possible):**
- Long: `--database`
- Short: `-d`
- Only use when truly needed (prefer --env)

**Dry Run:**
- Long: `--dry-run`
- No short form
- Boolean flag

**CSV Export:**
- Long: `--output-csv` / `--no-csv`
- Default: True (always export unless explicitly disabled)

**System Collections:**
- Long: `--exclude-system` / `--include-system`
- Default: exclude-system

---

## Examples

### Example 1: Single Collection Processing

```python
@app.command("process-collection")
def process_collection(
    env: str = typer.Option(None, "--env", help="Environment (DEV, PROD, STG)"),
    collection: str = typer.Option(None, "--collection", "-c", help="Collection to process"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview only"),
):
    """Process a specific collection."""
    if env:
        os.environ["APP_ENV"] = env.upper()

    settings = get_settings()
    # ... rest of implementation
```

**Usage:**
```bash
# DEV environment
python my_project/run.py process-collection -c Patients --dry-run

# PROD environment
python my_project/run.py process-collection -c Patients --env PROD

# STG environment with dry run
python my_project/run.py process-collection -c Users --env STG --dry-run
```

### Example 2: All Collections Processing

```python
@app.command("process-all")
def process_all(
    env: str = typer.Option(None, "--env", help="Environment (DEV, PROD, STG)"),
    exclude_system: bool = typer.Option(True, "--exclude-system/--include-system"),
    output_csv: bool = typer.Option(True, "--output-csv/--no-csv"),
):
    """Process all collections in database."""
    if env:
        os.environ["APP_ENV"] = env.upper()

    settings = get_settings()
    # ... rest of implementation
```

**Usage:**
```bash
# DEV environment (default)
python my_project/run.py process-all

# PROD environment
python my_project/run.py process-all --env PROD

# Include system collections
python my_project/run.py process-all --include-system --env PROD

# No CSV export
python my_project/run.py process-all --no-csv --env STG
```

### Example 3: Flexible Collection Selection

```python
@app.command("analyze")
def analyze(
    env: str = typer.Option(None, "--env", help="Environment (DEV, PROD, STG)"),
    collection: str = typer.Option(None, "--collection", "-c", help="Specific collection (optional)"),
    exclude_system: bool = typer.Option(True, "--exclude-system/--include-system"),
):
    """Analyze collections - specific or all."""
    if env:
        os.environ["APP_ENV"] = env.upper()

    settings = get_settings()

    with get_mongo_client(
        mongodb_uri=settings.mongodb_uri,
        database_name=settings.database_name
    ) as client:
        db = client[settings.database_name]

        # Determine collections to process
        if collection:
            collections = [collection]
        else:
            collections = db.list_collection_names()
            if exclude_system:
                collections = [c for c in collections if not c.startswith("system.")]

        # Process collections...
```

**Usage:**
```bash
# Analyze all collections
python my_project/run.py analyze --env PROD

# Analyze specific collection
python my_project/run.py analyze -c Patients --env PROD

# Analyze all including system collections
python my_project/run.py analyze --include-system --env DEV
```

---

## Migration Guide

If you have an existing project using `--mongodb-uri` and `--database` options:

### Before (Non-Standard):
```python
@app.command("command")
def command(
    mongodb_uri: str = typer.Option(None, "--mongodb-uri"),
    database: str = typer.Option(None, "--database", "-d"),
    collection: str = typer.Option(None, "--collection", "-c"),
):
    settings = get_settings()
    mongo_uri = mongodb_uri or settings.mongodb_uri
    db_name = database or settings.database_name
    # ...
```

**Usage:**
```bash
python project/run.py command \
  --mongodb-uri mongodb://prod:27017 \
  --database prod_db \
  --collection Patients
```

### After (Standard):
```python
@app.command("command")
def command(
    env: str = typer.Option(None, "--env"),
    collection: str = typer.Option(None, "--collection", "-c"),
):
    if env:
        os.environ["APP_ENV"] = env.upper()

    settings = get_settings()
    # MongoDB URI and database come from environment-specific settings
    # ...
```

**Usage:**
```bash
python project/run.py command --env PROD --collection Patients
```

**Setup `.env`:**
```bash
MONGODB_URI_PROD=mongodb://prod:27017
DATABASE_NAME_PROD=prod_db
```

---

## Checklist for New Projects

When creating a new CLI-based project:

- [ ] Use `--env` option for environment switching
- [ ] Use `--collection` / `-c` for collection names (never in `.env`)
- [ ] Configure environment-specific variables in `.env` with suffixes (e.g., `_DEV`, `_PROD`)
- [ ] Follow standard command template
- [ ] Add `import os` for environment variable manipulation
- [ ] Set `APP_ENV` before calling `get_settings()`
- [ ] Log the active environment, URI, and database
- [ ] Use consistent option naming (--dry-run, --output-csv, --exclude-system)
- [ ] Add `no_args_is_help=True` to Typer app
- [ ] Document all commands with clear help text

---

## Benefits of This Pattern

**Consistency:**
- All projects use the same CLI interface
- Easy to learn once, use everywhere
- Predictable behavior across projects

**Safety:**
- Environment switching is explicit and visible
- No accidental production operations
- Dry-run support encourages testing

**Flexibility:**
- Quick environment switching without file changes
- CI/CD friendly (can set APP_ENV dynamically)
- Collection-specific operations are clear and explicit

**Maintainability:**
- Single source of truth for environment config (`.env`)
- Easy to add new environments
- Clear separation: configuration vs. parameters

---

## Anti-Patterns to Avoid

**❌ Don't hardcode environment values:**
```python
# BAD
mongodb_uri = "mongodb://prod-server:27017"
```

**❌ Don't put collection names in .env:**
```bash
# BAD - in .env
COLLECTION_NAME=Patients
```

**❌ Don't use positional arguments for environment/collection:**
```python
# BAD
@app.command()
def command(env: str, collection: str):  # Positional
    pass
```

**❌ Don't mix environment config sources:**
```python
# BAD - confusing priority
mongo_uri = mongodb_uri or os.environ.get("MONGO_URI") or settings.mongodb_uri
```

**✅ Do use standard pattern:**
```python
# GOOD
if env:
    os.environ["APP_ENV"] = env.upper()

settings = get_settings()  # Single source, clear priority
```

---

## Related Documentation

- [Common Config API Reference](../guides/COMMON_CONFIG_API_REFERENCE.md) - Import paths and settings usage
- [New Project Guide](../guides/NEW_PROJECT_GUIDE.md) - Creating projects with this pattern
- [Environment Configuration](../guides/ENVIRONMENT_CONFIGURATION.md) - Detailed .env setup

---

**Questions or Issues?** Update this document and share with the team.
