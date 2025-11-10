# common_config API Reference

**Purpose:** Quick reference for correct import paths and usage patterns when developing with common_config.

**Why this document exists:** To prevent import errors and ensure developers use the correct API patterns consistently
across all projects.

______________________________________________________________________

<details open>
<summary><strong>📖 Table of Contents</strong> (click to expand/collapse)</summary>

- [Configuration & Settings](#configuration--settings)
  - [Import Path](#import-path)
  - [Usage](#usage)
  - [Configuration Precedence](#configuration-precedence)
  - [Environment-Specific Variables](#environment-specific-variables)
    - [Setup in `.env`](#setup-in-env)
    - [How It Works](#how-it-works)
    - [CLI Integration Pattern](#cli-integration-pattern)
- [Database Connectors](#database-connectors)
  - [MongoDB Connection](#mongodb-connection)
    - [Import Path](#import-path-1)
    - [Usage Pattern 1: Context Manager (Recommended)](#usage-pattern-1-context-manager-recommended)
    - [Usage Pattern 2: MongoDBConnector Class](#usage-pattern-2-mongodbconnector-class)
    - [Testing Connection](#testing-connection)
  - [Alternative: Simple MongoConnection Wrapper](#alternative-simple-mongoconnection-wrapper)
    - [Import Path](#import-path-2)
    - [Usage](#usage-1)
- [Logging](#logging)
  - [Import Path](#import-path-3)
  - [Usage](#usage-2)
- [Security Utilities](#security-utilities) ⭐
  - [Import Path](#import-path-4)
  - [Credential Redaction](#credential-redaction)
    - [`redact_uri(uri, mask="***")`](#redact_uriuri-mask)
    - [`redact_password(text, mask="***")`](#redact_passwordtext-mask)
    - [`get_safe_connection_info(uri, database)`](#get_safe_connection_infouri-database)
  - [Security Checklist](#security-checklist)
- [File Operations](#file-operations)
  - [Import Path](#import-path-5)
  - [Usage](#usage-3)
- [Common Patterns](#common-patterns)
  - [Pattern 1: Basic Project Setup (No Database)](#pattern-1-basic-project-setup-no-database)
  - [Pattern 2: MongoDB Project](#pattern-2-mongodb-project)
  - [Pattern 3: Data Processing with CSV Export](#pattern-3-data-processing-with-csv-export)
- [Quick Troubleshooting](#quick-troubleshooting)
  - [Import Error: `No module named 'common_config'`](#import-error-no-module-named-common_config)
  - [Import Error: `No module named 'common_config.db.mongo_client'`](#import-error-no-module-named-common_configdbmongo_client)
  - [Error: `MongoDB URI not found`](#error-mongodb-uri-not-found)
- [Version Information](#version-information)
- [See Also](#see-also)

</details>

______________________________________________________________________

## Configuration & Settings

### Import Path

```python
from common_config.config.settings import get_settings, AppSettings
```

### Usage

```python
settings = get_settings()

# Access common settings
mongodb_uri = settings.mongodb_uri
database_name = settings.database_name
log_level = settings.log_level

# Access paths
input_dir = settings.paths.data_input
output_dir = settings.paths.data_output
logs_dir = settings.paths.logs
temp_dir = settings.paths.temp

# Ensure directories exist
settings.ensure_dirs()
```

### Configuration Precedence

1. OS environment variables (highest priority)
1. `.env` in project root
1. `config/.env` in project directory
1. `shared_config/.env` (lowest priority)

### Environment-Specific Variables

**⭐ RECOMMENDED PATTERN:** Use environment suffixes for multi-environment support.

#### Setup in `.env`

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

#### How It Works

When `APP_ENV` is set, `common_config` automatically resolves environment-specific variables:

1. **`APP_ENV=DEV`** → uses `MONGODB_URI_DEV` → sets `MONGODB_URI`
1. **`APP_ENV=PROD`** → uses `MONGODB_URI_PROD` → sets `MONGODB_URI`
1. **`APP_ENV=STG`** → uses `MONGODB_URI_STG` → sets `MONGODB_URI`

Your code always uses the base variable names (`settings.mongodb_uri`), and the environment resolution happens
automatically.

#### CLI Integration Pattern

```python
import os
from common_config.config.settings import get_settings

# Allow CLI to override environment
if env:  # env comes from --env CLI option
    os.environ["APP_ENV"] = env.upper()

# Now get_settings() will use the environment-specific variables
settings = get_settings()
print(settings.mongodb_uri)  # Uses MONGODB_URI_PROD if env="PROD"
```

**Complete example:**

```python
import os
import typer

app = typer.Typer()


@app.command()
def my_command(
    env: str = typer.Option(
        None,
        "--env",
        help="Environment (DEV, PROD, STG) - overrides APP_ENV",
    ),
):
    """Process data in specified environment."""
    # Set environment before loading settings
    if env:
        os.environ["APP_ENV"] = env.upper()

    settings = get_settings()
    # settings.mongodb_uri now uses the environment-specific value
```

**Supported Variables with Environment Suffixes:**

- `MONGODB_URI_{ENV}`
- `DATABASE_NAME_{ENV}`
- `COLLECTION_NAME_{ENV}`
- `COLLECTION_BEFORE_{ENV}`
- `COLLECTION_AFTER_{ENV}`
- `AZ_SAS_DIR_URL_{ENV}`
- `BACKUP_DIR_{ENV}`
- `LOG_DIR_{ENV}`

**See also:** [Standard CLI Patterns](../best-practices/CLI_PATTERNS.md)

______________________________________________________________________

## Database Connectors

### MongoDB Connection

#### Import Path

```python
from common_config.connectors.mongodb import get_mongo_client, MongoDBConnector
```

#### Usage Pattern 1: Context Manager (Recommended)

```python
from common_config.connectors.mongodb import get_mongo_client

# Using settings
settings = get_settings()
with get_mongo_client(
    mongodb_uri=settings.mongodb_uri, database_name=settings.database_name
) as client:
    db = client[settings.database_name]
    collections = db.list_collection_names()
    # Connection auto-closes when exiting context
```

#### Usage Pattern 2: MongoDBConnector Class

```python
from common_config.connectors.mongodb import MongoDBConnector

# Environment-based (reads MONGODB_URI_DEV, DATABASE_NAME_DEV from .env)
connector = MongoDBConnector(env="DEV")

with connector.connect() as client:
    db = client[connector.database_name]
    # Use database
```

#### Testing Connection

```python
connector = MongoDBConnector(env="DEV")
if connector.test_connection():
    print("Connection successful")
```

### Alternative: Simple MongoConnection Wrapper

#### Import Path

```python
from common_config.db.mongo import MongoConnection, ConnectionInfo
```

#### Usage

```python
conn = MongoConnection(uri="mongodb://localhost:27017", database_name="mydb")
with conn as c:
    db = c.db
    # Use database

# Test connection
info = conn.test_connection()
print(f"Connected: {info.connected}, Server: {info.server_version}")
```

______________________________________________________________________

## Logging

### Import Path

```python
from common_config.utils.logger import get_logger, setup_logging, get_run_timestamp
```

### Usage

```python
from pathlib import Path
from common_config.utils.logger import setup_logging, get_logger

# Setup logging (do this once at app start)
log_dir = Path("logs/my_project")
log_dir.mkdir(parents=True, exist_ok=True)
setup_logging(log_dir=log_dir, log_level="INFO")

# Get logger for your module
logger = get_logger(__name__)

# Use logger
logger.info("Application started")
logger.debug("Debug information")
logger.error("Error occurred", exc_info=True)
logger.warning("Warning message")

# Get timestamped run identifier
run_id = get_run_timestamp()  # Returns: "20240115_143022"
```

______________________________________________________________________

## Security Utilities

**⚠️ CRITICAL:** Use these utilities to prevent credential exposure in logs.

### Import Path

```python
from common_config.utils.security import (
    redact_uri,
    redact_password,
    get_safe_connection_info,
)
```

### Credential Redaction

#### `redact_uri(uri, mask="***")`

Redact credentials from URIs for safe logging.

```python
from common_config.utils.security import redact_uri

# MongoDB URIs
uri = "mongodb+srv://<username>:<password>@cluster.mongodb.net/?options"
safe_uri = redact_uri(uri)
# Returns: "mongodb+srv://***:***@cluster.mongodb.net/?options"

# Standard MongoDB
uri = "mongodb://<username>:<password>@localhost:27017/mydb"
safe_uri = redact_uri(uri)
# Returns: "mongodb://***:***@localhost:27017/mydb"

# Safe for logging
logger.info(f"Connecting to: {redact_uri(settings.mongodb_uri)}")
```

**Why this is critical:**

- Prevents credentials in log files
- Prevents credentials in CI/CD logs
- Prevents credentials in error tracking systems
- Compliance requirement (SOC2, GDPR, etc.)

#### `redact_password(text, mask="***")`

Redact passwords from text using common patterns.

```python
from common_config.utils.security import redact_password

text = "Connecting with password=secret123"
safe_text = redact_password(text)
# Returns: "Connecting with password=***"
```

#### `get_safe_connection_info(uri, database)`

Get safe connection information dictionary for logging.

```python
from common_config.utils.security import get_safe_connection_info

info = get_safe_connection_info(
    "mongodb+srv://<username>:<password>@cluster.mongodb.net/?options", "mydb"
)

# Returns: {
#     'database': 'mydb',
#     'uri': 'mongodb+srv://***:***@cluster.mongodb.net/?options',
#     'host': 'cluster.mongodb.net',
#     'port': None,
#     'scheme': 'mongodb+srv'
# }

logger.info(f"Connection info: {info}")  # Safe to log
```

### Security Checklist

**Before logging any connection information:**

- [ ] Import `redact_uri` from `common_config.utils.security`
- [ ] Use `redact_uri()` for ALL URI logging
- [ ] Never log raw `settings.mongodb_uri`
- [ ] Never log passwords or API keys
- [ ] Review log files for accidental credential exposure

**Examples of correct usage:**

```python
# ✅ CORRECT
from common_config.utils.security import redact_uri

logger.info(f"MongoDB URI: {redact_uri(settings.mongodb_uri)}")
logger.info(f"Connecting to: {redact_uri(uri)}")

# ❌ WRONG - NEVER DO THIS
logger.info(f"MongoDB URI: {settings.mongodb_uri}")  # Exposes credentials!
logger.info(f"Connecting to: {uri}")  # Exposes credentials!
```

______________________________________________________________________

## File Operations

### Import Path

```python
from common_config.utils.file_ops import ensure_dir, archive_file, clean_old_files
```

### Usage

```python
from pathlib import Path
from common_config.utils.file_ops import ensure_dir, archive_file

# Ensure directory exists
output_dir = ensure_dir(Path("data/output/my_project"))

# Archive old file before overwriting
archive_file(Path("data/output/report.csv"), archive_dir=Path("archive"))
```

______________________________________________________________________

## Common Patterns

### Pattern 1: Basic Project Setup (No Database)

```python
"""Main entry point for project."""

import sys
from pathlib import Path

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from common_config.config.settings import get_settings
from common_config.utils.logger import setup_logging, get_logger


def main():
    """Main execution function."""
    settings = get_settings()

    # Setup logging
    log_dir = Path(settings.paths.logs) / "my_project"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir)
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info("my_project - Starting")
    logger.info("=" * 60)

    # Your logic here

    logger.info("Completed successfully")


if __name__ == "__main__":
    main()
```

### Pattern 2: MongoDB Project

```python
"""Main entry point for MongoDB project."""

import sys
from pathlib import Path

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from common_config.config.settings import get_settings
from common_config.connectors.mongodb import get_mongo_client
from common_config.utils.logger import setup_logging, get_logger


def main():
    """Main execution function."""
    settings = get_settings()

    # Setup logging
    log_dir = Path(settings.paths.logs) / "my_project"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir)
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info("my_project - Starting")
    logger.info("=" * 60)

    try:
        # MongoDB connection
        with get_mongo_client(
            mongodb_uri=settings.mongodb_uri, database_name=settings.database_name
        ) as client:
            db = client[settings.database_name]

            # Your MongoDB operations here
            collections = db.list_collection_names()
            logger.info(f"Found {len(collections)} collections")

            logger.info("Completed successfully")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
```

### Pattern 3: Data Processing with CSV Export

```python
"""Main entry point for data processing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from common_config.config.settings import get_settings
from common_config.utils.logger import setup_logging, get_logger


def main():
    """Main execution function."""
    settings = get_settings()

    # Setup logging
    log_dir = Path(settings.paths.logs) / "my_project"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir)
    logger = get_logger(__name__)

    # Define I/O paths
    input_dir = Path(settings.paths.data_input) / "my_project"
    output_dir = Path(settings.paths.data_output) / "my_project"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Input:  {input_dir}")
    logger.info(f"Output: {output_dir}")

    # Process data
    # ...

    # Export results
    output_file = output_dir / "results.csv"
    logger.info(f"Results saved to: {output_file}")


if __name__ == "__main__":
    main()
```

______________________________________________________________________

## Quick Troubleshooting

### Import Error: `No module named 'common_config'`

**Problem:** Python can't find the common_config package.

**Solutions:**

1. Ensure common_config is installed: `pip show common-config`
1. If not installed: `pip install -e common_config`
1. Check virtual environment is activated: `which python` (should show .venv311)

### Import Error: `No module named 'common_config.db.mongo_client'`

**Problem:** Using old/incorrect import path.

**Solution:** Use correct path:

```python
# WRONG
from common_config.db.mongo_client import get_mongo_client

# CORRECT
from common_config.connectors.mongodb import get_mongo_client
```

### Error: `MongoDB URI not found`

**Problem:** MongoDB configuration missing from .env files.

**Solution:** Add to `shared_config/.env`:

```bash
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=your_database_name
```

Or use environment-specific variables:

```bash
MONGODB_URI_DEV=mongodb://localhost:27017
DATABASE_NAME_DEV=dev_database

MONGODB_URI_PROD=mongodb://production-server:27017
DATABASE_NAME_PROD=prod_database
```

______________________________________________________________________

## Version Information

This reference is valid for common_config as of January 2025.

If you encounter import errors:

1. Check this reference first
1. Inspect the actual common_config source code
1. Update this document if you find discrepancies

______________________________________________________________________

## See Also

- [NEW_PROJECT_GUIDE.md](NEW_PROJECT_GUIDE.md) - Step-by-step guide for creating new projects
- [TESTING_GUIDE.md](../TESTING_GUIDE.md) - Testing patterns and best practices
- [CI_CD_LESSONS_LEARNED.md](../best-practices/CI_CD_LESSONS_LEARNED.md) - CI/CD best practices
