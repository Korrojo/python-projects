# mongo-backup-tools: End-to-End Testing Guide

This guide provides comprehensive, repeatable testing procedures for the mongo-backup-tools project. Use this for
validation, training, and understanding the underlying MongoDB backup/restore processes.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Test Data Setup](#test-data-setup)
- [Test Scenarios](#test-scenarios)
  - [Test 1: Basic Dump and Restore](#test-1-basic-dump-and-restore)
  - [Test 2: JSON Export and Import](#test-2-json-export-and-import)
  - [Test 3: CSV Export and Import](#test-3-csv-export-and-import)
  - [Test 4: Import with Upsert Mode](#test-4-import-with-upsert-mode)
  - [Test 5: Centralized Directories](#test-5-centralized-directories)
- [Cleanup](#cleanup)
- [Troubleshooting](#troubleshooting)

______________________________________________________________________

## Prerequisites

### Required Software

1. **Python 3.11+**

   ```bash
   python3 --version  # Should be 3.11 or higher
   ```

1. **MongoDB 4.0+**

   - Local MongoDB instance running on `localhost:27017`
   - Or MongoDB Atlas connection string

1. **MongoDB Database Tools**

   ```bash
   mongodump --version
   mongorestore --version
   mongoexport --version
   mongoimport --version
   ```

   **Installation:**

   - macOS: `brew install mongodb-database-tools`
   - Ubuntu: `sudo apt-get install mongodb-database-tools`
   - Windows: Download from [MongoDB Download Center](https://www.mongodb.com/try/download/database-tools)

### Verify MongoDB is Running

```bash
# Test connection
mongosh --eval "db.version()" mongodb://localhost:27017/test
```

**Expected Output:** MongoDB version number (e.g., `8.2.1`)

______________________________________________________________________

## Environment Setup

### 1. Navigate to Project Directory

```bash
cd /Users/demesewabebe/Projects/python-projects/mongo_backup_tools
```

**Verify you're in the correct directory:**

```bash
pwd
```

**Expected Output:** `/Users/demesewabebe/Projects/python-projects/mongo_backup_tools`

### 2. Install Package

**Note:** This repo uses a shared virtual environment at `../.venv311`

```bash
../.venv311/bin/pip install -e .
```

**Expected Output:**

```
Successfully built mongo-backup-tools
Successfully installed mongo-backup-tools-1.0.0
```

### 3. Verify Installation

```bash
../.venv311/bin/python3 run.py --help
```

**Expected:** CLI help menu with commands: `version`, `dump`, `restore`, `export`, `import`

### 4. Verify Version

```bash
../.venv311/bin/python3 run.py version
```

**Expected Output:**

```
mongo-backup-tools version 1.0.0
```

______________________________________________________________________

## Test Data Setup

### Create Test Database

Run the setup script to create a test database with sample data:

```bash
../.venv311/bin/python3 tests/setup_test_data.py
```

**Expected Output:**

```
✓ Created database: test_backup_demo
✓ Inserted 5 documents into users collection
```

**What it creates:**

- Database: `test_backup_demo`
- Collection: `users`
- 5 documents with fields: `_id`, `name`, `age`, `email`, `city`

**Verify Data:**

```bash
mongosh mongodb://localhost:27017/test_backup_demo --eval "db.users.find().pretty()"
```

______________________________________________________________________

## Test Scenarios

### Test 1: Basic Dump and Restore

**Objective:** Test binary backup and restore functionality.

#### Step 1.1: Perform Dump

```bash
../.venv311/bin/python3 run.py dump \
  --host localhost \
  --port 27017 \
  --database test_backup_demo \
  --out /tmp/test_dump \
  --verbose
```

**Expected Output:**

```
✓ Dump completed successfully in X.XXs
```

**Validation:**

```bash
ls -lh /tmp/test_dump/test_backup_demo/
```

**Expected:** Should see `users.bson` and `users.metadata.json`

#### Step 1.2: Drop Original Database

```bash
mongosh mongodb://localhost:27017/test_backup_demo --eval "db.dropDatabase()"
```

**Expected Output:**

```
{ ok: 1, dropped: 'test_backup_demo' }
```

**Verify Deletion:**

```bash
../.venv311/bin/python3 -c "from pymongo import MongoClient; print('Count:', MongoClient('mongodb://localhost:27017')['test_backup_demo']['users'].count_documents({}))"
```

**Expected Output:** `Count: 0`

#### Step 1.3: Restore Database

```bash
../.venv311/bin/python3 run.py restore \
  --host localhost \
  --port 27017 \
  --dir /tmp/test_dump \
  --verbose
```

**Expected Output:**

```
✓ Restore completed successfully in X.XXs
```

**Validation:**

```bash
../.venv311/bin/python3 -c "from pymongo import MongoClient; print('Restored count:', MongoClient('mongodb://localhost:27017')['test_backup_demo']['users'].count_documents({}))"
```

**Expected Output:** `Restored count: 5`

#### Step 1.4: Verify Data Integrity

```bash
mongosh mongodb://localhost:27017/test_backup_demo --eval "db.users.findOne({_id: 1})"
```

**Expected:** Should see Alice Johnson's complete document with all fields intact.

______________________________________________________________________

### Test 2: JSON Export and Import

**Objective:** Test JSON export and import functionality.

#### Step 2.1: Export to JSON

```bash
../.venv311/bin/python3 run.py export \
  --host localhost \
  --port 27017 \
  --database test_backup_demo \
  --collection users \
  --out /tmp/users_export.json \
  --type json \
  --json-array \
  --pretty \
  --verbose
```

**Expected Output:**

```
✓ Export completed successfully in X.XXs
```

**Validation:**

```bash
cat /tmp/users_export.json | head -20
```

**Expected:** Pretty-printed JSON array with user documents.

#### Step 2.2: Create New Collection

```bash
../.venv311/bin/python3 -c "from pymongo import MongoClient; MongoClient('mongodb://localhost:27017')['test_backup_demo']['users_imported'].delete_many({}); print('✓ Ready for import')"
```

#### Step 2.3: Import JSON

```bash
../.venv311/bin/python3 run.py import \
  --host localhost \
  --port 27017 \
  --database test_backup_demo \
  --collection users_imported \
  --file /tmp/users_export.json \
  --type json \
  --mode insert \
  --verbose
```

**Expected Output:**

```
✓ Import completed successfully in X.XXs
```

**Validation:**

```bash
../.venv311/bin/python3 -c "from pymongo import MongoClient; print('Imported count:', MongoClient('mongodb://localhost:27017')['test_backup_demo']['users_imported'].count_documents({}))"
```

**Expected Output:** `Imported count: 5`

______________________________________________________________________

### Test 3: CSV Export and Import

**Objective:** Test CSV export and import functionality.

#### Step 3.1: Export to CSV

```bash
../.venv311/bin/python3 run.py export \
  --host localhost \
  --port 27017 \
  --database test_backup_demo \
  --collection users \
  --out /tmp/users_export.csv \
  --type csv \
  --field _id \
  --field name \
  --field age \
  --field email \
  --field city \
  --verbose
```

**Expected Output:**

```
✓ Export completed successfully in X.XXs
```

**Validation:**

```bash
cat /tmp/users_export.csv
```

**Expected:** CSV format with header row and 5 data rows.

#### Step 3.2: Import CSV with Headers

```bash
../.venv311/bin/python3 -c "from pymongo import MongoClient; MongoClient('mongodb://localhost:27017')['test_backup_demo']['users_csv'].delete_many({}); print('✓ Ready for import')"
```

```bash
../.venv311/bin/python3 run.py import \
  --host localhost \
  --port 27017 \
  --database test_backup_demo \
  --collection users_csv \
  --file /tmp/users_export.csv \
  --type csv \
  --headerline \
  --mode insert \
  --verbose
```

**Expected Output:**

```
✓ Import completed successfully in X.XXs
```

**Validation:**

```bash
../.venv311/bin/python3 -c "from pymongo import MongoClient; print('CSV imported count:', MongoClient('mongodb://localhost:27017')['test_backup_demo']['users_csv'].count_documents({}))"
```

**Expected Output:** `CSV imported count: 5`

______________________________________________________________________

### Test 4: Import with Upsert Mode

**Objective:** Test upsert functionality (update existing or insert new).

#### Step 4.1: Modify Test Data

Create a file with modified data:

```bash
cat > /tmp/users_update.json << 'EOF'
{"_id": 1, "name": "Alice Johnson", "age": 31, "email": "alice.new@example.com", "city": "New York"}
{"_id": 6, "name": "Frank Miller", "age": 40, "email": "frank@example.com", "city": "Miami"}
EOF
```

#### Step 4.2: Import with Upsert

```bash
../.venv311/bin/python3 run.py import \
  --host localhost \
  --port 27017 \
  --database test_backup_demo \
  --collection users \
  --file /tmp/users_update.json \
  --type json \
  --mode upsert \
  --upsert-fields _id \
  --verbose
```

**Expected Output:**

```
✓ Import completed successfully in X.XXs
```

**Validation:**

Check updated document:

```bash
mongosh mongodb://localhost:27017/test_backup_demo --eval "db.users.findOne({_id: 1})"
```

**Expected:** Alice's age should be 31 and email should be `alice.new@example.com`

Check new document:

```bash
mongosh mongodb://localhost:27017/test_backup_demo --eval "db.users.findOne({_id: 6})"
```

**Expected:** Frank Miller's document should exist.

Total count:

```bash
../.venv311/bin/python3 -c "from pymongo import MongoClient; print('Total after upsert:', MongoClient('mongodb://localhost:27017')['test_backup_demo']['users'].count_documents({}))"
```

**Expected Output:** `Total after upsert: 6` (5 original + 1 new)

______________________________________________________________________

### Test 5: Centralized Directories

**Objective:** Verify that logs and output files are stored in centralized repository directories.

#### Step 5.1: Check Centralized Output Directory

```bash
ls -lh ../../data/output/mongo_backup_tools/
```

**Expected:** Directory exists (created automatically by the tool)

#### Step 5.2: Dump to Centralized Directory

```bash
../.venv311/bin/python3 run.py dump \
  --host localhost \
  --port 27017 \
  --database test_backup_demo \
  --verbose
```

**Note:** No `--out` specified, should use default centralized location.

**Expected Output:**

```
✓ Dump completed successfully in X.XXs
```

#### Step 5.3: Verify Output Location

```bash
ls -lh ../../data/output/mongo_backup_tools/
```

**Expected:** Should see dump files in the centralized output directory.

#### Step 5.4: Check Centralized Logs

```bash
ls -lh ../../logs/mongo_backup_tools/
```

**Expected:** Should see timestamped log files (e.g., `20251113_030000_dump.log`)

#### Step 5.5: Inspect Log File

```bash
tail -20 ../../logs/mongo_backup_tools/*.log
```

**Expected:** Detailed logs of the dump operation with timestamps.

______________________________________________________________________

## Cleanup

### Remove Test Database

```bash
mongosh mongodb://localhost:27017/test_backup_demo --eval "db.dropDatabase()"
```

### Remove Temporary Files

```bash
rm -rf /tmp/test_dump
rm -f /tmp/users_export.json
rm -f /tmp/users_export.csv
rm -f /tmp/users_update.json
```

### Optional: Clear Centralized Directories

```bash
# Clear output directory
rm -rf ../../data/output/mongo_backup_tools/*

# Clear logs directory
rm -rf ../../logs/mongo_backup_tools/*
```

______________________________________________________________________

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'typer'"

**Cause:** Dependencies not installed or wrong Python interpreter.

**Solution:**

```bash
# Ensure venv is activated
source ../.venv311/bin/activate

# Reinstall
pip install -e .
```

### Issue: "Connection refused to localhost:27017"

**Cause:** MongoDB is not running.

**Solution:**

```bash
# macOS (Homebrew)
brew services start mongodb-community

# Linux (systemd)
sudo systemctl start mongod

# Verify
mongosh --eval "db.version()"
```

### Issue: "mongodump: command not found"

**Cause:** MongoDB Database Tools not installed.

**Solution:**

```bash
# macOS
brew install mongodb-database-tools

# Ubuntu/Debian
sudo apt-get install mongodb-database-tools

# Verify
mongodump --version
```

### Issue: Dump/Restore fails with permission errors

**Cause:** Insufficient permissions on output/input directories.

**Solution:**

```bash
# Check permissions
ls -ld /tmp/test_dump

# Fix if needed
chmod 755 /tmp/test_dump
```

### Issue: "Error: File not formatted" when committing

**Cause:** Pre-commit hooks require proper formatting.

**Solution:**

```bash
# Format files
black src/ tests/
ruff check --fix src/ tests/

# Re-commit
git add .
git commit -m "Your message"
```

______________________________________________________________________

## Testing Checklist

After completing all tests, verify:

- [ ] CLI help displays correctly
- [ ] Version command works
- [ ] Dump creates BSON files
- [ ] Restore recovers all data
- [ ] JSON export creates valid JSON
- [ ] JSON import populates collection
- [ ] CSV export creates proper CSV
- [ ] CSV import with headers works
- [ ] Upsert mode updates and inserts correctly
- [ ] Centralized output directory is used
- [ ] Centralized logs directory contains logs
- [ ] All test data cleaned up

______________________________________________________________________

## Training Notes

### Key Learning Points

1. **Binary vs. Text Formats:**

   - `dump/restore`: Binary BSON format (efficient, preserves types)
   - `export/import`: JSON/CSV formats (human-readable, portable)

1. **When to Use Each:**

   - Use `dump/restore` for full backups, migrations, disaster recovery
   - Use `export/import` for data sharing, analytics, partial transfers

1. **Upsert vs. Insert:**

   - `insert`: Adds new documents, fails on duplicates
   - `upsert`: Updates existing or inserts new (idempotent)

1. **Centralized Directories:**

   - Outputs: `../../data/output/mongo_backup_tools/`
   - Logs: `../../logs/mongo_backup_tools/`
   - Automatically created by the tool

1. **Shell Script Integration:**

   - Python CLI delegates to MongoDB shell tools
   - Proper error handling and logging
   - State tracking for resume capability

______________________________________________________________________

## Next Steps

After mastering these tests, explore:

1. **Advanced Features:**

   - Query filters (`--query`)
   - Specific collections (`--collection`)
   - Archive files (`--archive`)
   - Compression (`--gzip`)
   - Parallel jobs (`--num-parallel-collections`)

1. **Production Use Cases:**

   - Scheduled backups (cron jobs)
   - Remote MongoDB (Atlas)
   - Large datasets
   - Point-in-time recovery (`--oplog`)

1. **Integration:**

   - CI/CD pipelines
   - Monitoring and alerting
   - Automated testing

______________________________________________________________________

**Document Version:** 1.0.0 **Last Updated:** 2025-11-13 **Tested With:** MongoDB 8.2.1, Python 3.11
