# db_collection_stats

**MongoDB collection statistics gathering and export tool**

Gathers comprehensive statistics for all collections in a MongoDB database and exports them to CSV format with a console
summary.

______________________________________________________________________

## What It Does

This tool connects to a MongoDB database, gathers statistics for all collections (excluding system collections by
default), and provides:

- **CSV Export** - Timestamped CSV file with detailed collection statistics
- **Console Summary** - Human-readable summary with totals and top 5 largest collections
- **Comprehensive Logging** - Full execution logs with timestamps

### Statistics Collected

For each collection:

- Collection name
- Document count
- Collection size (bytes)
- Average document size (bytes)
- Storage size (bytes)
- Number of indexes
- Total index size (bytes)

______________________________________________________________________

## Prerequisites

- Python 3.11+
- MongoDB database access
- Virtual environment activated (`.venv311/`)
- `common_config` installed (`pip install -e ./common_config`)

______________________________________________________________________

## Configuration

### 1. MongoDB Connection

Add to `shared_config/.env` or `config/.env`:

```bash
# MongoDB connection
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=your_database_name

# Optional: Specify environment
APP_ENV=DEV
```

### 2. Verify Configuration

```bash
python -c "from common_config.config.settings import get_settings; s=get_settings(); print(f'DB: {s.database_name}\nURI: {s.mongodb_uri}')"
```

### 3. Multi-Environment Configuration

You can configure multiple environments (DEV, PROD, STG, etc.) in your `.env` file and switch between them using the
`--env` option:

**Setup in `.env`:**

```bash
# Default environment
APP_ENV=DEV

# DEV environment
MONGODB_URI_DEV=mongodb://localhost:27017
DATABASE_NAME_DEV=dev_database

# PROD environment
MONGODB_URI_PROD=mongodb://prod-server:27017
DATABASE_NAME_PROD=production_database

# STG environment
MONGODB_URI_STG=mongodb://staging-server:27017
DATABASE_NAME_STG=staging_database
```

**Switch environments from CLI:**

```bash
# Use DEV environment (default from .env)
python db_collection_stats/run.py coll-stats

# Use PROD environment
python db_collection_stats/run.py coll-stats --env PROD

# Use STG environment
python db_collection_stats/run.py index-stats --env STG
```

**Priority order:**

1. `--env` CLI option (highest priority)
1. `APP_ENV` environment variable
1. Default configuration in `.env`

**Use cases:**

- Quick analysis of different environments without changing `.env`
- CI/CD pipelines with dynamic environment selection
- Testing against multiple databases

______________________________________________________________________

## Usage

This project supports multiple commands. Run `--help` to see all available options.

### Command: `coll-stats`

Gather statistics for all collections in the database.

```bash
# Basic usage (uses default environment from .env)
python db_collection_stats/run.py coll-stats

# Use PROD environment
python db_collection_stats/run.py coll-stats --env PROD

# Use STG environment
python db_collection_stats/run.py coll-stats --env STG

# Include system collections
python db_collection_stats/run.py coll-stats --include-system

# Skip CSV export (console output only)
python db_collection_stats/run.py coll-stats --no-csv

# Combine options: PROD environment without CSV export
python db_collection_stats/run.py coll-stats --env PROD --no-csv

# Show help
python db_collection_stats/run.py coll-stats --help
```

**What this does:**

1. Connects to MongoDB
1. Lists all collections (excludes system collections by default)
1. Gathers statistics for each collection
1. Prints summary to console
1. Exports to timestamped CSV file (unless --no-csv)

### Command: `index-stats`

Analyze index usage statistics for collections.

```bash
# Analyze all collections (uses default environment from .env)
python db_collection_stats/run.py index-stats

# Use PROD environment
python db_collection_stats/run.py index-stats --env PROD

# Analyze specific collection in PROD
python db_collection_stats/run.py index-stats --collection Patients --env PROD

# Highlight unused indexes in STG environment
python db_collection_stats/run.py index-stats --show-unused --env STG

# Analyze specific collection
python db_collection_stats/run.py index-stats --collection Patients

# Include system collections
python db_collection_stats/run.py index-stats --include-system

# Skip CSV export (console output only)
python db_collection_stats/run.py index-stats --no-csv

# Combine options: specific collection in PROD, show unused, no CSV
python db_collection_stats/run.py index-stats \
  --collection Patients \
  --env PROD \
  --show-unused \
  --no-csv

# Show help
python db_collection_stats/run.py index-stats --help
```

**What this does:**

1. Connects to MongoDB
1. For each collection, lists all indexes
1. Shows index names, key patterns, and usage statistics
1. Highlights unused indexes (when --show-unused is used)
1. Exports to timestamped CSV file (unless --no-csv)
1. Helps identify indexes that could be removed

**Output:**

- **Console:** Formatted display with index details
- **CSV:** `YYYYMMDD_HHMMSS_index_stats_<database>.csv`
- **Logs:** `YYYYMMDD_HHMMSS_app.log`

**CSV Format:**

```csv
collection_name,index_name,index_keys,usage_count,is_unused
Patients,_id_,"_id: 1",1234567,No
Patients,hcmId_1,"HcmId: 1",456789,No
Patients,name_dob_1,"name: 1, dob: 1",0,Yes
```

**Note:** Index usage statistics reset when MongoDB restarts.

### Show All Commands

```bash
# List all available commands
python db_collection_stats/run.py --help
```

### Output

**Console Summary:**

```
================================================================================
Collection Statistics Summary for Database: UbiquityProduction
================================================================================

Total Collections: 25
Total Documents: 1,234,567
Total Data Size: 5.23 GB
Total Storage Size: 6.45 GB
Total Indexes: 87
Total Index Size: 1.12 GB

--------------------------------------------------------------------------------
Top 5 Largest Collections (by data size):
--------------------------------------------------------------------------------
Collection                     Documents     Data Size      Indexes
--------------------------------------------------------------------------------
Patients                          500,000      2.15 GB            5
Appointments                      300,000      1.84 GB            4
Users                              50,000    512.45 MB            3
...
```

**CSV File:**

```
data/output/db_collection_stats/20250127_143022_collection_stats_UbiquityProduction.csv
```

**Note:** Timestamp comes first for chronological sorting.

**CSV Format:**

```csv
collection_name,document_count,collection_size_bytes,avg_document_size_bytes,storage_size_bytes,num_indexes,total_index_size_bytes
Patients,500000,2150000000,430.00,2580000000,5,52000000
Appointments,300000,1840000000,613.33,2210000000,4,48000000
...
```

**Logs:**

```
logs/db_collection_stats/20250127_143022_app.log
```

______________________________________________________________________

## Project Structure

```
db_collection_stats/
├── src/db_collection_stats/
│   ├── __init__.py
│   ├── cli.py                # CLI with subcommands (entry point)
│   ├── collector.py          # Statistics gathering logic
│   └── exporter.py           # CSV export and console display
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Test configuration
│   ├── test_collector.py    # Tests for statistics gathering
│   ├── test_exporter.py     # Tests for export/display
│   └── test_db_collection_stats_smoke.py  # Smoke tests
├── scripts/                  # Utility scripts (if needed)
├── temp/                     # Temporary files
├── run.py                    # Main entry point (calls cli.py)
├── run.bat                   # Windows convenience script
├── README.md                 # This file
└── ARCHITECTURE.md           # How to add new functionality
```

### Architecture

This project uses a **CLI with subcommands** pattern, allowing multiple related use cases to coexist:

- **cli.py** - Defines all commands using Typer framework
- **Feature modules** (collector.py, exporter.py, etc.) - Business logic
- **run.py** - Thin wrapper that launches the CLI

**Want to add new functionality?** See [ARCHITECTURE.md](ARCHITECTURE.md) for a complete guide.

### Module Details

#### `cli.py`

**CLI Framework:** Entry point for all commands

**Commands:**

- `coll-stats` - Gather collection statistics
- `index-stats` - Analyze index usage

**Framework:** Uses Typer for argument parsing and help generation

**Adding new commands:** See [ARCHITECTURE.md](ARCHITECTURE.md)

#### `collector.py`

**CollectionStats Dataclass:**

- Type-safe storage for collection statistics
- Provides `to_dict()` method for CSV export

**Functions:**

- `gather_collection_stats(db, collection_name)` - Gets stats for single collection
- `gather_all_collections_stats(client, database_name, exclude_system=True)` - Gets stats for all collections

**Usage Example:**

```python
from common_config.connectors.mongodb import get_mongo_client
from db_collection_stats.collector import gather_all_collections_stats

with get_mongo_client(mongodb_uri="...", database_name="...") as client:
    stats_list = gather_all_collections_stats(client, "UbiquityProduction")
    for stats in stats_list:
        print(f"{stats.collection_name}: {stats.document_count} docs")
```

#### `exporter.py`

**Functions:**

- `export_to_csv(stats_list, output_dir, database_name)` - Exports collection stats to timestamped CSV
- `export_index_stats_to_csv(index_data, output_dir, database_name)` - Exports index stats to timestamped CSV
- `format_bytes(bytes_value)` - Human-readable byte formatting (KB, MB, GB, TB)
- `print_summary(stats_list, database_name)` - Console summary with totals and top 5

**Usage Example (Collection Stats):**

```python
from pathlib import Path
from db_collection_stats.exporter import export_to_csv, print_summary

# Print summary
print_summary(stats_list, "UbiquityProduction")

# Export to CSV
output_dir = Path("data/output/db_collection_stats")
csv_path = export_to_csv(stats_list, output_dir, "UbiquityProduction")
print(f"Exported to: {csv_path}")
```

**Usage Example (Index Stats):**

```python
from pathlib import Path
from db_collection_stats.exporter import export_index_stats_to_csv

# Prepare index data
index_data = [
    {
        "collection_name": "Patients",
        "index_name": "hcmId_1",
        "index_keys": "HcmId: 1",
        "usage_count": 456789,
        "is_unused": "No",
    },
    # ... more indexes
]

# Export to CSV
output_dir = Path("data/output/db_collection_stats")
csv_path = export_index_stats_to_csv(index_data, output_dir, "UbiquityProduction")
print(f"Exported to: {csv_path}")
```

______________________________________________________________________

## Testing

### Run All Tests

```bash
# From repository root
pytest db_collection_stats/tests/ -v
```

**Expected output:**

```
db_collection_stats/tests/test_collector.py::TestCollectionStats::test_to_dict PASSED
db_collection_stats/tests/test_collector.py::TestCollectionStats::test_to_dict_rounds_avg_size PASSED
...
================================ 35 passed in 0.07s ================================
```

### Test Coverage

Tests cover:

- ✅ CollectionStats dataclass (to_dict, rounding)
- ✅ Single collection statistics gathering
- ✅ All collections statistics gathering
- ✅ System collection filtering
- ✅ Error handling for individual collections
- ✅ CSV export (file creation, content, headers)
- ✅ Byte formatting (B, KB, MB, GB, TB, PB)
- ✅ Console summary display
- ✅ Empty collections and databases
- ✅ Missing fields handling

### Run Specific Test Module

```bash
# Test collector only
pytest db_collection_stats/tests/test_collector.py -v

# Test exporter only
pytest db_collection_stats/tests/test_exporter.py -v

# Test with coverage
pytest db_collection_stats/tests/ --cov=db_collection_stats --cov-report=term-missing
```

______________________________________________________________________

## Features

### System Collection Filtering

By default, excludes collections starting with `system.` (e.g., `system.indexes`, `system.profile`).

**To include system collections:**

```python
# In collector.py
stats_list = gather_all_collections_stats(client, database_name, exclude_system=False)
```

### Error Handling

- Gracefully handles errors for individual collections
- Prints warning but continues with other collections
- Full stack traces in logs for debugging

### Timestamped Outputs

All outputs include timestamps (timestamp first for chronological sorting):

- CSV: `YYYYMMDD_HHMMSS_collection_stats_<database>.csv`
- Logs: `YYYYMMDD_HHMMSS_app.log`

**Pattern:** `YYYYMMDD_HHMMSS_<description>.<ext>`

### Human-Readable Formatting

Console output uses:

- Thousand separators for document counts (1,234,567)
- Byte formatting (5.23 GB instead of 5230000000 bytes)
- Sorted collections (alphabetically)
- Top 5 largest collections highlighted

______________________________________________________________________

## Common Use Cases

### 1. Database Health Check

Quickly assess database size and distribution:

```bash
python db_collection_stats/run.py coll-stats
# Review console output for totals and top collections
```

### 2. Capacity Planning

Export historical statistics for trend analysis:

```bash
# Run weekly/monthly, keep CSV files
python db_collection_stats/run.py coll-stats
# CSV files are timestamped and never overwrite
```

### 3. Index Optimization

Identify unused indexes that can be removed:

```bash
# Find all unused indexes
python db_collection_stats/run.py index-stats --show-unused

# Export to CSV for analysis
python db_collection_stats/run.py index-stats
# Review CSV: indexes with usage_count=0 are candidates for removal
```

**Why this matters:**

- Unused indexes waste storage space
- Every index slows down write operations
- Removing unused indexes improves performance

### 4. Collection Index Overview

Check total index count and size per collection:

```bash
python db_collection_stats/run.py coll-stats
# Check "Total Index Size" in console output
# Review CSV for per-collection index counts
```

### 5. Development Monitoring

Track collection growth during development:

```bash
# Before making changes
python db_collection_stats/run.py coll-stats

# After making changes
python db_collection_stats/run.py coll-stats

# Compare CSV files
```

______________________________________________________________________

## Development Notes

### Adding New Statistics

To collect additional statistics:

1. **Update CollectionStats dataclass** (collector.py):

```python
@dataclass
class CollectionStats:
    # Existing fields...
    new_field: int  # Add your new field
```

2. **Update gather_collection_stats()** (collector.py):

```python
return CollectionStats(
    # Existing fields...
    new_field=stats.get("newField", 0),
)
```

3. **Update to_dict()** (collector.py):

```python
def to_dict(self) -> dict:
    return {
        # Existing fields...
        "new_field": self.new_field,
    }
```

4. **Update CSV headers** (exporter.py):

```python
headers = [
    # Existing headers...
    "new_field",
]
```

5. **Add tests** for the new field

### MongoDB collStats Command

This tool uses MongoDB's `collStats` command:

```javascript
db.runCommand({ collStats: "collectionName" })
```

**Available fields:**

- `count` - Document count
- `size` - Collection size in bytes
- `avgObjSize` - Average document size
- `storageSize` - Storage size including padding
- `nindexes` - Number of indexes
- `totalIndexSize` - Total size of all indexes
- `totalSize` - Total size (data + indexes)
- `scaleFactor` - Scale factor for size values

See [MongoDB collStats documentation](https://www.mongodb.com/docs/manual/reference/command/collStats/) for more fields.

______________________________________________________________________

## Troubleshooting

### "ModuleNotFoundError: No module named 'common_config'"

**Solution:**

```bash
pip install -e ./common_config
```

### "ModuleNotFoundError: No module named 'db_collection_stats'"

**Solution:** Run from repository root, not from project directory:

```bash
# ❌ Wrong
cd db_collection_stats
python run.py

# ✅ Correct
python db_collection_stats/run.py
```

### "MongoDB URI not found"

**Solution:** Configure `shared_config/.env`:

```bash
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=your_database
```

### Permission Denied for Some Collections

**Behavior:** Tool prints warning and continues with other collections:

```
Warning: Failed to gather stats for restricted_collection: Permission denied
```

**Solution:** This is expected. Only collections with read permission are included.

______________________________________________________________________

## Configuration Reference

### Environment Variables

| Variable        | Required | Description               | Example                     |
| --------------- | -------- | ------------------------- | --------------------------- |
| `MONGODB_URI`   | Yes      | MongoDB connection string | `mongodb://localhost:27017` |
| `DATABASE_NAME` | Yes      | Database name to analyze  | `UbiquityProduction`        |
| `APP_ENV`       | No       | Environment selector      | `DEV`, `PROD`, etc.         |

### Paths

All paths are relative to repository root:

| Type       | Path                               | Description                 |
| ---------- | ---------------------------------- | --------------------------- |
| **Input**  | `data/input/db_collection_stats/`  | (Not used by this tool)     |
| **Output** | `data/output/db_collection_stats/` | CSV files saved here        |
| **Logs**   | `logs/db_collection_stats/`        | Log files saved here        |
| **Temp**   | `temp/`                            | Temporary files (if needed) |

______________________________________________________________________

## Related Documentation

- **[Master README](../README.md)** - Repository overview
- **[COMMON_CONFIG_API_REFERENCE](../docs/guides/COMMON_CONFIG_API_REFERENCE.md)** - Import paths and patterns
- **[NEW_PROJECT_GUIDE](../docs/guides/NEW_PROJECT_GUIDE.md)** - How this project was created
- **[TESTING_GUIDE](../docs/guides/TESTING_GUIDE.md)** - Testing strategies

______________________________________________________________________

## Changelog

### 2025-01-27 - Multi-Command Architecture + CSV Export

**Added:**

- CLI with subcommands architecture (cli.py)
- New command: `index-stats` - Analyze index usage statistics with CSV export
- CSV export for index statistics (`export_index_stats_to_csv()`)
- Architecture documentation (ARCHITECTURE.md)
- Support for multiple use cases in single project

**Changed:**

- run.py now a thin wrapper calling cli.py
- Original functionality moved to `coll-stats` command
- Filename pattern: Timestamp first (YYYYMMDD_HHMMSS_description.ext)
- Replaced `--mongodb-uri` and `--database` options with `--env` for environment switching

**CSV Outputs:**

- Collection stats: `YYYYMMDD_HHMMSS_collection_stats_<database>.csv`
- Index stats: `YYYYMMDD_HHMMSS_index_stats_<database>.csv`

**Migration:**

- Old: `python run.py`
- New: `python run.py coll-stats`

### 2025-01-27 - Initial Implementation

**Created:**

- Statistics gathering module (collector.py)
- CSV export and console display (exporter.py)
- Main entry point (run.py)
- Comprehensive test suite (35 tests, 100% pass rate)

**Features:**

- Gathers 7 statistics per collection
- CSV export with timestamps
- Console summary with human-readable formatting
- System collection filtering
- Error handling for restricted collections

______________________________________________________________________

## License

See repository root for license information.

______________________________________________________________________

**Last Updated:** 2025-01-27
