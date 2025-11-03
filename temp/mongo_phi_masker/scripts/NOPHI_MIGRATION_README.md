# No-PHI Collections Migration Tool

This tool facilitates the migration of MongoDB collections that do not contain Protected Health Information (PHI) from a source database to a destination database. Since these collections don't contain PHI, they can be directly copied without any masking or transformation.

## Overview

The `migrate_no_phi_collections.py` script provides a streamlined way to:

1. Read a list of collections from a text file or command line
2. Connect to source and destination MongoDB instances
3. Copy the specified collections in batches
4. Track migration progress and generate logs

## Prerequisites

- Python 3.10+
- MongoDB 4.4+
- PyMongo
- Environment variables set for MongoDB connections

## Configuration

### Environment Variables

Create a `.env.prod` file (or specify a different env file with `--env`) with the following variables:

```
# Source MongoDB
MONGO_SOURCE_HOST=source.mongodb.com

MONGO_SOURCE_USERNAME=username
MONGO_SOURCE_PASSWORD=password
MONGO_SOURCE_DB=sourcedb
MONGO_SOURCE_AUTH_DB=admin
MONGO_SOURCE_USE_SRV=false
MONGO_SOURCE_USE_SSL=true

# Destination MongoDB
MONGO_DEST_HOST=dest.mongodb.com

MONGO_DEST_USERNAME=username
MONGO_DEST_PASSWORD=password
MONGO_DEST_DB=destdb
MONGO_DEST_AUTH_DB=admin
MONGO_DEST_USE_SRV=false
MONGO_DEST_USE_SSL=true
```

### Collections List

Create a text file at `docs/no-phi_collections.txt` with one collection name per line. Lines starting with `#` are treated as comments and will be ignored:

```
Collection1
Collection2
# Collection3 - skipped because it's commented out
Collection4
```

## Usage

### Basic Usage

```bash
# Migrate all collections from no-phi_collections.txt
python scripts/migrate_no_phi_collections.py --use-all-no-phi

# Migrate specific collections (comma-separated)
python scripts/migrate_no_phi_collections.py --collections "Collection1,Collection2,Collection4"

# Migrate collections from a specific file
python scripts/migrate_no_phi_collections.py --collections-file path/to/my_collections.txt

# Use a different environment file
python scripts/migrate_no_phi_collections.py --use-all-no-phi --env .env.dev

# Specify batch size for processing
python scripts/migrate_no_phi_collections.py --use-all-no-phi --batch-size 500
```

### Advanced Options

```bash
# Drop and recreate collections that already exist in the destination database
python scripts/migrate_no_phi_collections.py --use-all-no-phi --drop-existing

# Control parallel processing with specific number of worker threads
python scripts/migrate_no_phi_collections.py --use-all-no-phi --max-workers 8

# Reduce log verbosity (log progress every 10,000 documents instead of default 5,000)
python scripts/migrate_no_phi_collections.py --use-all-no-phi --log-frequency 10000

# Enable console output (by default, logs only go to the log file)
python scripts/migrate_no_phi_collections.py --use-all-no-phi --console-output

# Skip index creation (useful when indexes have invalid specifications)
python scripts/migrate_no_phi_collections.py --use-all-no-phi --skip-indexes

# Combine options for optimized performance
python scripts/migrate_no_phi_collections.py --use-all-no-phi --batch-size 1000 --max-workers 16 --drop-existing

# Use a custom configuration file
python scripts/migrate_no_phi_collections.py --use-all-no-phi --config path/to/config.json
```

### Running in Background (nohup)

For long-running migrations, you can use `nohup` to run the script in the background:

```bash
# Run in background, log to file only (default behavior)
nohup python scripts/migrate_no_phi_collections.py --use-all-no-phi --batch-size 2500 > /dev/null 2>&1 &

# Check the detailed log file for progress
tail -f logs/no_phi_migration_*.log

# Check the process status
ps aux | grep migrate_no_phi_collections
```

## Parallel Processing

The script uses parallel processing to significantly improve performance:

1. **Collection-Level Parallelism**: Multiple collections are processed simultaneously using a thread pool.
2. **Batch Inserts**: Documents are inserted in batches using `insert_many()` for better performance.
3. **Worker Thread Control**: The number of parallel workers can be controlled via:
   - Command line: `--max-workers 16`
   - Environment variable: `PROCESSING_MAX_WORKERS` (defaults to 32 in .env.prod)
   - Default fallback: 4 workers if neither is specified

For optimal performance with large collections:
- Increase batch size for collections with simple documents (e.g., `--batch-size 2500`)
- Use more workers for many small collections (e.g., `--max-workers 32`)
- Use fewer workers for a few very large collections (e.g., `--max-workers 8`)

## Migration Log

After migration, a log file is generated at `docs/migration_log.json` with details about each collection's migration status, document count, and any errors encountered.

## Troubleshooting

### Common Issues

1. **Connection Errors**: Verify MongoDB connection details in your environment file
2. **Permission Issues**: Ensure the MongoDB user has read access to source and write access to destination
3. **Collection Already Exists**: By default, collections that already exist in the destination are skipped

### Log Levels

Use the standard Python logging levels to control verbosity:

```bash
# Set log level to DEBUG for more detailed information
export LOGLEVEL=DEBUG
python scripts/migrate_no_phi_collections.py --use-all-no-phi
```

## Project Integration

This script is part of the MongoPHIMasker project, which handles PHI data masking for MongoDB databases to ensure HIPAA compliance. While the main project focuses on masking PHI data, this script provides a faster path for non-PHI collections that don't require masking.

For collections containing PHI data, use the main masking process with appropriate rule groups based on the collection category.

Example:
```bash
python scripts/migrate_no_phi_collections.py --env .env.prod --drop-existing --collections-file docs/no-phi_collections_2.txt --log-frequency 10000
```