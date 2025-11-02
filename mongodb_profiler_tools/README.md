# MongoDB Profiler Tools

MongoDB profiler analysis toolkit for identifying slow queries and monitoring database performance. Consolidates functionality from 3 independent JavaScript profiler projects into a single Python tool with standardized CLI.

## Features

- **Slow Queries Analyzer**: Find and analyze slow operations from system.profile ✅
- **Profiler Statistics**: Get profiling collection statistics and health metrics ✅

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

### Slow Queries Analyzer

Find and analyze slow operations from MongoDB profiler data:

```bash
# Find slow queries (default: >= 100ms)
python mongodb_profiler_tools/run.py slow-queries

# Set custom threshold
python mongodb_profiler_tools/run.py slow-queries --threshold 250

# Filter by collection
python mongodb_profiler_tools/run.py slow-queries --collection UbiquityProduction.Patients

# Filter by operation type
python mongodb_profiler_tools/run.py slow-queries --operation query

# Limit results
python mongodb_profiler_tools/run.py slow-queries --limit 50

# Skip CSV export
python mongodb_profiler_tools/run.py slow-queries --no-csv

# Analyze PROD environment
python mongodb_profiler_tools/run.py slow-queries --env PROD --threshold 500
```

**Output:**
- Console display with top slow operations
- Operation details: timestamp, duration, examined vs returned docs, plan summary
- Summary statistics: total time, average time, operation breakdown
- CSV export to `data/output/mongodb_profiler_tools/slow_queries_<database>_<timestamp>.csv`
- Logs in `logs/mongodb_profiler_tools/`

**CSV Columns:**
- Timestamp
- Operation (query, update, delete, command, etc.)
- Namespace (database.collection)
- Duration (ms)
- Docs Examined
- Keys Examined
- Returned (documents)
- Plan Summary (COLLSCAN, IXSCAN, etc.)
- Client (IP address)
- User
- Command (query/update details)

**Prerequisites:**
Profiling must be enabled in MongoDB:
```javascript
// Check profiling level
db.getProfilingLevel()

// Enable profiling for slow queries only (recommended)
db.setProfilingLevel(1, { slowms: 100 })

// Enable profiling for all operations (impacts performance)
db.setProfilingLevel(2)
```

**Use Cases:**
- Identify performance bottlenecks
- Find queries doing collection scans (COLLSCAN)
- Track slow operations over time
- Prioritize index creation based on slow query patterns
- Monitor query performance after index changes
- Audit database access patterns

### Profiler Statistics

Get MongoDB profiler collection statistics and health metrics:

```bash
# Get profiler stats for default environment
python mongodb_profiler_tools/run.py profiler-stats

# Get profiler stats for PROD
python mongodb_profiler_tools/run.py profiler-stats --env PROD
```

**Output:**
- Profiling status (enabled/disabled, level, slow threshold)
- Collection size (documents, MB, storage)
- Time range covered (oldest/newest entries, duration)
- Recommendations for optimal profiling setup

**Profiling Levels:**
- **Level 0**: Off - no data collected
- **Level 1**: Slow operations only (recommended for production)
- **Level 2**: All operations (use with caution - performance impact)

**Use Cases:**
- Verify profiling is enabled before analyzing slow queries
- Monitor profiler collection growth
- Determine if profiler data covers sufficient time period
- Check if system.profile is capped (recommended)
- Assess profiling overhead

## Testing

```bash
# Run all tests
PYTHONPATH=mongodb_profiler_tools/src:$PYTHONPATH pytest mongodb_profiler_tools/tests/ -v

# Run with coverage
PYTHONPATH=mongodb_profiler_tools/src:$PYTHONPATH pytest mongodb_profiler_tools/tests/ --cov=mongodb_profiler_tools --cov-report=term-missing
```

## Development

```bash
# Format and lint
./scripts/lint.sh mongodb_profiler_tools/

# Type check
pyright mongodb_profiler_tools/
```

## Project Structure

```
mongodb_profiler_tools/
├── src/
│   └── mongodb_profiler_tools/
│       ├── cli.py              # Multi-command CLI interface
│       ├── slow_queries.py     # Slow queries analyzer ✅
│       ├── profiler_stats.py   # Profiler statistics ✅
│       └── run.py              # Module entry point
├── tests/
│   ├── test_slow_queries.py    # Slow queries tests ✅
│   ├── test_profiler_stats.py  # Profiler stats tests ✅
│   ├── test_mongodb_profiler_tools_smoke.py  # Smoke tests ✅
│   └── conftest.py
└── run.py                       # CLI entry point
```

## Related Documentation

- [CLI Patterns](../docs/best-practices/CLI_PATTERNS.md) - Standard CLI usage
- [Common Config API](../docs/guides/COMMON_CONFIG_API_REFERENCE.md) - Import paths and patterns

## Best Practices

### Profiling in Production

1. **Use Level 1** (slow operations only) to minimize overhead
2. **Set appropriate slowms** threshold (100-500ms depending on workload)
3. **Use capped collection** to limit system.profile size:
   ```javascript
   db.setProfilingLevel(0)
   db.system.profile.drop()
   db.createCollection("system.profile", { capped: true, size: 104857600 })  // 100MB
   db.setProfilingLevel(1, { slowms: 100 })
   ```
4. **Monitor collection size** regularly with `profiler-stats` command
5. **Analyze periodically** to identify new slow queries

### Analyzing Slow Queries

1. **Start with high threshold** (500ms+) to find critical issues
2. **Look for COLLSCAN** operations - candidates for indexing
3. **High examined:returned ratio** indicates inefficient queries
4. **Check plan summary** to verify indexes are being used
5. **Cross-reference** with index advisor recommendations

## License

See repository root for license information.
