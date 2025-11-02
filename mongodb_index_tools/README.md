# MongoDB Index Tools

Unified MongoDB index management and analysis toolkit. Consolidates functionality from 6 independent JavaScript projects into a single Python tool with standardized CLI.

## Features

- **Index Inventory**: List all indexes with detailed information (keys, attributes, uniqueness, etc.) ✅
- **Index Utilization**: Analyze index usage statistics to identify unused or heavily-used indexes ✅
- **Query Analyzer**: Analyze query execution plans using MongoDB's explain command ✅
- **Index Advisor**: Get index recommendations based on usage and redundancy analysis ✅
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

### Query Analyzer

Analyze how MongoDB executes a specific query using the explain command:

```bash
# Create a query file (query.json)
{
  "filter": {"age": {"$gt": 25}},
  "sort": {"name": 1},
  "limit": 100
}

# Analyze the query
python mongodb_index_tools/run.py analyzer -c Users -f query.json --env PROD

# Save full explain output to JSON
python mongodb_index_tools/run.py analyzer -c Users -f query.json --save-json
```

**Supported Query Types:**
- `find` (default): Regular find queries with filter, projection, sort, limit
- `aggregate`: Aggregation pipeline queries
- `update`: Update queries
- `delete`: Delete queries

**Example Query Files:**

Find query (`query_find.json`):
```json
{
  "filter": {"status": "active", "age": {"$gte": 18}},
  "projection": {"name": 1, "email": 1},
  "sort": {"createdAt": -1},
  "limit": 50
}
```

Aggregate query (`query_agg.json`):
```json
{
  "pipeline": [
    {"$match": {"status": "active"}},
    {"$group": {"_id": "$city", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
  ]
}
```

**Output:**
- Console display with execution metrics
- Scan type (COLLSCAN, IXSCAN, etc.)
- Index used (if any)
- Performance metrics (execution time, documents examined vs returned)
- Performance assessment with warnings for inefficient queries
- Optional JSON export of full explain output

**Use Cases:**
- Understand how MongoDB executes specific queries
- Identify queries doing collection scans that need indexes
- Find queries with high examined:returned ratios
- Validate that new indexes are being used

### Index Advisor

Get intelligent index recommendations based on usage statistics and redundancy analysis:

```bash
# Get recommendations for a specific collection
python mongodb_index_tools/run.py advisor -c Patients

# Analyze for PROD environment
python mongodb_index_tools/run.py advisor -c Patients --env PROD

# Skip CSV export
python mongodb_index_tools/run.py advisor -c Users --no-csv --env PROD
```

**Output:**
- Console display with categorized indexes (unused, redundant, useful)
- Actionable recommendations with severity levels (HIGH, MEDIUM, INFO)
- Drop commands for each recommendation
- Impact assessment for each action
- CSV export to `data/output/mongodb_index_tools/index_recommendations_<database>_<collection>_<timestamp>.csv`
- Logs in `logs/mongodb_index_tools/`

**Recommendation Types:**

1. **DROP - HIGH Severity**: Unused indexes (0 operations)
   - Impact: Saves storage and improves write performance
   - Safe to drop: No queries are using these indexes

2. **DROP - MEDIUM Severity**: Redundant indexes
   - Covered by compound indexes with matching prefix
   - Example: Index on `{a: 1}` is redundant if `{a: 1, b: 1}` exists
   - Impact: Saves storage, minimal impact on reads (covered by compound index)

3. **INFO**: Useful indexes
   - Actively used indexes that should be kept
   - Recommendation to monitor usage over time

**CSV Columns:**
- Type (DROP, INFO)
- Severity (HIGH, MEDIUM, INFO)
- Index Name
- Keys (comma-separated field names)
- Usage Count (number of operations)
- Size (MB)
- Reason (why this recommendation was made)
- Action (MongoDB command to execute)
- Impact (expected outcome)

**Use Cases:**
- Identify unused indexes consuming storage and slowing writes
- Find redundant indexes that can be safely removed
- Optimize database performance by reducing index overhead
- Clean up indexes after schema or query pattern changes
- Prepare for database migration or optimization initiatives

**Note:** This command combines data from `$indexStats` (usage) and index structure analysis. Run after MongoDB has been active for a representative period to get accurate usage statistics.

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
│       ├── analyzer.py         # Query plan analyzer ✅
│       ├── advisor.py          # Index recommendations ✅
│       └── manager.py          # Index create/drop (coming soon)
├── tests/
│   ├── test_inventory.py       # Inventory tests ✅
│   ├── test_utilization.py     # Utilization tests ✅
│   ├── test_analyzer.py        # Analyzer tests ✅
│   ├── test_advisor.py         # Advisor tests ✅
│   └── conftest.py
└── run.py                      # Entry point
```

## Related Documentation

- [CLI Patterns](../docs/best-practices/CLI_PATTERNS.md) - Standard CLI usage
- [Common Config API](../docs/guides/COMMON_CONFIG_API_REFERENCE.md) - Import paths and patterns

## License

See repository root for license information.
