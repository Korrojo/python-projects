# db_collection_stats - Architecture Guide

**How to add new functionality to a multi-command CLI project**

______________________________________________________________________

## Overview

This project uses a **CLI with subcommands** architecture, allowing multiple related use cases to coexist in a single
project.

**Current commands:**

- `coll-stats` - Gather collection statistics (original feature)
- `index-stats` - Analyze index usage (example of adding new functionality)

______________________________________________________________________

## Architecture Pattern

### Structure

```
db_collection_stats/
├── src/db_collection_stats/
│   ├── __init__.py
│   ├── cli.py              # CLI with subcommands (entry point)
│   ├── collector.py        # Collection stats module
│   ├── exporter.py         # Export utilities (shared)
│   └── (future modules)    # Add new functionality here
├── tests/
│   ├── test_collector.py
│   ├── test_exporter.py
│   └── (test new modules)
├── run.py                  # Thin wrapper that calls cli.py
└── README.md
```

### Key Components

**1. cli.py** - Command definitions

- Uses Typer for CLI framework
- Each command is a function decorated with `@app.command()`
- Handles argument parsing, logging setup, error handling

**2. Feature modules** - Business logic

- `collector.py` - Collection statistics gathering
- `exporter.py` - Export and display utilities
- (Add new modules for new features)

**3. run.py** - Entry point

- Minimal wrapper that imports and runs the CLI app
- All logic lives in `cli.py` and feature modules

______________________________________________________________________

## Usage Examples

### Collection Statistics

```bash
# Basic usage (default options)
python db_collection_stats/run.py coll-stats

# Use PROD environment
python db_collection_stats/run.py coll-stats --env PROD

# Include system collections
python db_collection_stats/run.py coll-stats --include-system

# Skip CSV export
python db_collection_stats/run.py coll-stats --no-csv
```

### Index Statistics

```bash
# Analyze all collections
python db_collection_stats/run.py index-stats

# Analyze specific collection
python db_collection_stats/run.py index-stats --collection Patients

# Highlight unused indexes
python db_collection_stats/run.py index-stats --show-unused

# Include system collections
python db_collection_stats/run.py index-stats --include-system
```

### Help

```bash
# Show all commands
python db_collection_stats/run.py --help

# Show help for specific command
python db_collection_stats/run.py coll-stats --help
python db_collection_stats/run.py index-stats --help
```

______________________________________________________________________

## How to Add New Functionality

### Step 1: Create the Feature Module

**Example:** Add schema validation analysis

```python
# src/db_collection_stats/schema_analyzer.py

def analyze_schema(db, collection_name):
    """Analyze document schema patterns."""
    coll = db[collection_name]

    # Sample documents
    sample = list(coll.aggregate([{"$sample": {"size": 1000}}]))

    # Analyze field presence, types, etc.
    field_stats = {}
    # ... your analysis logic

    return field_stats
```

### Step 2: Add Command to CLI

**File:** `src/db_collection_stats/cli.py`

```python
from db_collection_stats.schema_analyzer import analyze_schema

@app.command("schema-analysis")
def schema_analysis(
    collection: str = typer.Argument(..., help="Collection to analyze"),
    sample_size: int = typer.Option(1000, "--sample-size", help="Number of documents to sample"),
):
    """Analyze document schema patterns in a collection.

    Samples documents and identifies common fields, data types,
    and schema inconsistencies.
    """
    settings = get_settings()
    log_dir = Path(settings.paths.logs) / "db_collection_stats"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir)
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info("db_collection_stats - Schema Analysis")
    logger.info("=" * 60)

    try:
        with get_mongo_client(
            mongodb_uri=settings.mongodb_uri,
            database_name=settings.database_name
        ) as client:
            db = client[settings.database_name]
            logger.info(f"Analyzing schema for: {collection}")

            # Your analysis logic
            schema_stats = analyze_schema(db, collection)

            # Display results
            print(f"\n📊 Schema Analysis for {collection}")
            # ... format and print results

            logger.info("Completed successfully")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise typer.Exit(code=1)
```

### Step 3: Write Tests

**File:** `tests/test_schema_analyzer.py`

```python
import pytest
from unittest.mock import MagicMock

from db_collection_stats.schema_analyzer import analyze_schema

def test_analyze_schema():
    """Test schema analysis logic."""
    mock_db = MagicMock()
    # ... setup mocks

    result = analyze_schema(mock_db, "test_collection")

    assert result is not None
    # ... assertions
```

### Step 4: Update Documentation

Update `README.md`:

- Add new command to usage examples
- Document what the command does
- Show example output

______________________________________________________________________

## Design Principles

### 1. Separation of Concerns

- **CLI layer** (`cli.py`) - Argument parsing, user interaction, error handling
- **Business logic** (feature modules) - Core functionality, reusable
- **Shared utilities** (`exporter.py`) - Cross-cutting concerns

### 2. Testability

Each feature module should:

- Have minimal dependencies
- Be testable with mocked MongoDB connections
- Not depend on CLI framework (pure Python functions)

### 3. Consistency

All commands should:

- Use the same logging setup
- Follow the same error handling pattern
- Use consistent naming conventions
- Have comprehensive help text

### 4. Discoverability

- Commands are self-documenting (`--help`)
- Help text explains what command does and why you'd use it
- Options have clear descriptions

______________________________________________________________________

## Command Template

**Copy this template when adding new commands:**

```python
@app.command("command-name")
def command_name(
    env: str = typer.Option(
        None,
        "--env",
        help="Environment to use (DEV, PROD, STG, etc.) - overrides APP_ENV",
    ),
    required_arg: str = typer.Argument(..., help="Description"),
    optional_flag: bool = typer.Option(False, "--flag", help="Description"),
):
    """One-line command description.

    Detailed description explaining:
    - What the command does
    - When you'd use it
    - What output it produces
    """
    # 1. Set environment and get configuration
    if env:
        os.environ["APP_ENV"] = env.upper()

    settings = get_settings()
    log_dir = Path(settings.paths.logs) / "db_collection_stats"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir)
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info(f"db_collection_stats - Command Name")
    logger.info("=" * 60)

    # 2. Connect to MongoDB
    try:
        with get_mongo_client(
            mongodb_uri=settings.mongodb_uri,
            database_name=settings.database_name
        ) as client:
            db = client[settings.database_name]
            logger.info(f"Environment: {env.upper() if env else os.environ.get('APP_ENV', 'default')}")
            logger.info(f"MongoDB URI: {settings.mongodb_uri}")
            logger.info(f"Database: {settings.database_name}")

            # 3. Execute core logic
            logger.info("Executing command...")
            # Your code here

            # 4. Display results
            print("\\n Results:")
            # Your output here

            logger.info("Completed successfully")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\\n❌ Error: {e}\\n")
        raise typer.Exit(code=1)
```

______________________________________________________________________

## Advanced Patterns

### Shared Options

For options used across multiple commands:

```python
# Define once
def common_options(exclude_system: bool = typer.Option(True, "--exclude-system")):
    return exclude_system

# Use in commands
@app.command()
def cmd1(exclude_system: bool = common_options()):
    pass

@app.command()
def cmd2(exclude_system: bool = common_options()):
    pass
```

### Command Groups

For many commands, organize into groups:

```python
# Stats commands
stats_app = typer.Typer(help="Statistics commands")
app.add_typer(stats_app, name="stats")

@stats_app.command("collections")
def stats_collections():
    """Collection statistics."""
    pass

@stats_app.command("indexes")
def stats_indexes():
    """Index statistics."""
    pass

# Usage: python run.py stats collections
#        python run.py stats indexes
```

### Config Files

For complex configurations:

```python
import typer
from pathlib import Path
import tomli

@app.command()
def analyze(
    config: Path = typer.Option(None, "--config", help="Config file path")
):
    """Analyze with configuration file."""
    if config:
        with open(config, "rb") as f:
            cfg = tomli.load(f)
        # Use cfg["option_name"]
```

______________________________________________________________________

## Migration from Single-Purpose Script

### Before (Single Purpose)

```python
# run.py - Only does collection stats
def main():
    # ... collection stats logic
    pass
```

### After (Multi-Purpose)

```python
# cli.py - Multiple commands
@app.command("coll-stats")
def coll_stats():
    # ... collection stats logic
    pass

@app.command("index-stats")
def index_stats():
    # ... index stats logic
    pass

# run.py - Thin wrapper
from cli import app
if __name__ == "__main__":
    app()
```

**Benefits:**

- ✅ Easy to add new functionality
- ✅ Each feature is self-contained
- ✅ Consistent interface
- ✅ Better help documentation
- ✅ Each command can have unique options

______________________________________________________________________

## Why Typer?

**Typer advantages:**

- ✅ Type hints for argument validation
- ✅ Automatic help generation
- ✅ Rich formatting (colors, tables)
- ✅ Consistent with `common_config` CLI
- ✅ Easy to test
- ✅ Subcommands support

**Alternative: argparse**

- More verbose
- Manual help text
- Less type-safe
- More boilerplate

______________________________________________________________________

## Testing Strategy

### Unit Tests

Test feature modules independently:

```python
def test_collector():
    mock_db = MagicMock()
    result = gather_collection_stats(mock_db, "test")
    assert result.collection_name == "test"
```

### Integration Tests

Test CLI commands (optional):

```python
from typer.testing import CliRunner
from db_collection_stats.cli import app

def test_coll_stats_command():
    runner = CliRunner()
    result = runner.invoke(app, ["coll-stats", "--help"])
    assert result.exit_code == 0
    assert "Gather statistics" in result.stdout
```

______________________________________________________________________

## Real-World Example: Index Statistics

### Why This Feature?

**Problem:** Unused indexes waste storage and slow down writes.

**Solution:** `index-stats` command shows index usage, helping identify unused indexes.

### Implementation

**1. Core Logic:**

```python
# In cli.py - Uses MongoDB's $indexStats aggregation
index_stats = list(coll.aggregate([{"$indexStats": {}}]))
usage_lookup = {stat["name"]: stat.get("accesses", {}).get("ops", 0)
                for stat in index_stats}
```

**2. User Interface:**

```python
# Options for flexibility
--collection <name>     # Analyze specific collection
--show-unused           # Highlight unused indexes
--exclude-system        # Skip system collections
```

**3. Output:**

```
📊 Collection: Patients (5 indexes)
  • _id_           | Keys: _id: 1              | Usage:  1,234,567
  • hcmId_1        | Keys: HcmId: 1            | Usage:    456,789
  • name_dob_1     | Keys: name: 1, dob: 1     | Usage:          0 ⚠️  UNUSED
```

______________________________________________________________________

## Summary

**To add new functionality:**

1. Create feature module with core logic
1. Add command to `cli.py`
1. Write tests
1. Update documentation

**Benefits of this architecture:**

- ✅ Scalable (easy to add commands)
- ✅ Maintainable (separation of concerns)
- ✅ Discoverable (--help shows all features)
- ✅ Testable (modular design)
- ✅ Professional (standard CLI patterns)

______________________________________________________________________

**Questions?** See the implementation in `src/db_collection_stats/cli.py` for complete working examples.
