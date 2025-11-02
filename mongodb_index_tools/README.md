# MongoDB Index Tools

Unified MongoDB index management and analysis toolkit. Consolidates functionality from 6 independent JavaScript projects into a single Python tool with standardized CLI.

## Features

- **Index Inventory**: List all indexes with detailed information (keys, attributes, uniqueness, etc.) ✅
- **Index Utilization**: Analyze index usage statistics to identify unused or heavily-used indexes ✅
- **Query Analyzer**: Analyze query execution plans (coming soon)
- **Index Advisor**: Get index recommendations (coming soon)
- **Index Manager**: Create and drop indexes safely (coming soon)

## Installation

This project uses the repository-wide shared virtual environment. See the root README.md for setup instructions.

## Configuration

Configure MongoDB connection in `shared_config/.env`:

```bash
# Default environment
APP_ENV=DEV

# DEV Environment
MONGODB_URI_DEV=mongodb://localhost:27017
DATABASE_NAME_DEV=UbiquityDevelopment

# PROD Environment
MONGODB_URI_PROD=mongodb+srv://user:password@cluster.mongodb.net
DATABASE_NAME_PROD=UbiquityProduction
```

## Usage

### Index Inventory

List all indexes in the database with detailed information:

```bash
# List all indexes (DEV environment by default)
python mongodb_index_tools/run.py inventory

# List indexes for PROD environment
python mongodb_index_tools/run.py inventory --env PROD

# List indexes for specific collection
python mongodb_index_tools/run.py inventory -c Patients --env PROD

# Include system collections
python mongodb_index_tools/run.py inventory --include-system --env PROD

# Skip CSV export
python mongodb_index_tools/run.py inventory --no-csv
```

**Output:**
- Console display with collection-grouped indexes
- CSV export to `data/output/mongodb_index_tools/index_inventory_<database>_<timestamp>.csv`
- Logs in `logs/mongodb_index_tools/`

**CSV Columns:**
- Collection Name
- Index Name
- Index Keys
- Unique (Yes/No)
- Sparse (Yes/No)
- Attributes (unique, sparse, TTL, etc.)

### Index Utilization

Analyze how often each index is used to identify optimization opportunities:

```bash
# Analyze index usage for a specific collection
python mongodb_index_tools/run.py utilization -c Patients

# Analyze for PROD environment
python mongodb_index_tools/run.py utilization -c Patients --env PROD

# Skip CSV export
python mongodb_index_tools/run.py utilization -c Users --no-csv --env PROD
```

**Output:**
- Console display with usage statistics (operations count, size, last reset date)
- Highlights unused indexes (0 operations) with ⚠️  warning
- CSV export to `data/output/mongodb_index_tools/index_utilization_<database>_<collection>_<timestamp>.csv`
- Logs in `logs/mongodb_index_tools/`

**CSV Columns:**
- No (row number)
- Index Name
- Operations (total index uses since last MongoDB restart)
- Size (MB)
- Since (date when statistics tracking started)
- Key1, Key2, Key3, ... (index key fields)

**Note:** Index usage statistics are reset when MongoDB restarts. Run this command after MongoDB has been running for a representative period.

## Testing

```bash
# Run all tests
pytest mongodb_index_tools/tests/ -v

# Run with coverage
pytest mongodb_index_tools/tests/ --cov=mongodb_index_tools --cov-report=term-missing
```

## Development

```bash
# Format and lint
./scripts/lint.sh mongodb_index_tools/

# Type check
pyright mongodb_index_tools/
```

## Project Structure

```
mongodb_index_tools/
├── src/
│   └── mongodb_index_tools/
│       ├── cli.py              # Multi-command CLI interface
│       ├── inventory.py        # Index inventory module ✅
│       ├── utilization.py      # Index utilization analysis ✅
│       ├── analyzer.py         # Query plan analyzer (coming soon)
│       ├── advisor.py          # Index recommendations (coming soon)
│       └── manager.py          # Index create/drop (coming soon)
├── tests/
│   ├── test_inventory.py       # Inventory tests ✅
│   ├── test_utilization.py     # Utilization tests ✅
│   └── conftest.py
└── run.py                      # Entry point
```

## Related Documentation

- [CLI Patterns](../docs/best-practices/CLI_PATTERNS.md) - Standard CLI usage
- [Common Config API](../docs/guides/COMMON_CONFIG_API_REFERENCE.md) - Import paths and patterns

## License

See repository root for license information.
