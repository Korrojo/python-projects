# End-to-End PHI Masking Workflow

Complete guide for running the end-to-end PHI masking workflow with test data generation, backup, masking, and
validation.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Workflow Overview](#workflow-overview)
- [Step-by-Step Setup](#step-by-step-setup)
- [Running the Workflow](#running-the-workflow)
- [Validation](#validation)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### 1. Python Environment

- Python 3.11+
- Virtual environment activated

```bash
# Verify Python version
python --version  # Should be 3.11+

# Verify virtual environment
which python  # Should point to .venv311/bin/python
```

### 2. MongoDB

- MongoDB 4.4+ running locally (or remote)
- Access to create databases and collections
- mongodump and mongorestore tools installed

```bash
# Verify MongoDB is running
mongosh --eval "db.adminCommand('ping')"

# Verify mongodump/mongorestore
which mongodump mongorestore
```

### 3. Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Key dependencies for workflow:
# - Faker==24.0.0  (test data generation)
# - tqdm==4.66.1   (progress bars)
# - pymongo==4.6.3 (MongoDB driver)
```

### 4. Environment Configuration

The workflow uses `shared_config/.env` for environment presets.

**Ensure `shared_config/.env` is configured:**

```bash
# Check if shared_config/.env exists
ls -la ../shared_config/.env

# Minimum required configuration in shared_config/.env:
# LOCL Environment
MONGODB_URI_LOCL=mongodb://localhost:27017
DATABASE_NAME_LOCL=UbiquityLOCAL

# DEV Environment
MONGODB_URI_DEV=mongodb://localhost:27017
DATABASE_NAME_DEV=UbiquityDEV
```

## Quick Start

**Run the complete workflow with one command:**

```bash
# Interactive mode (recommended for first run)
./scripts/workflow_orchestrator.sh --collection Patients --size 10000 --interactive

# Automated mode (no prompts)
./scripts/workflow_orchestrator.sh --collection Patients --size 10000 --automated
```

That's it! The orchestrator handles all 6 steps automatically.

## Workflow Overview

The complete workflow consists of 6 steps:

```
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 1: Generate Test Data                   │
│  Environment: LOCL                                              │
│  Database: localdb-unmasked (or DATABASE_NAME_LOCL)             │
│  Action: Generate 10K realistic patient documents              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 2: Backup from LOCL                     │
│  Source: LOCL / localdb-unmasked                                │
│  Destination: backup/YYYYMMDD_HHMMSS_localdb-unmasked_Patients │
│  Action: mongodump with timestamp                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     STEP 3: Restore to DEV                      │
│  Source: backup/YYYYMMDD_HHMMSS_localdb-unmasked_Patients      │
│  Destination: DEV / devdb                                       │
│  Action: mongorestore                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 4: Mask Data (In-Situ)                  │
│  Environment: DEV / devdb                                       │
│  Action: Mask PHI fields in-place                              │
│  Fields: FirstName, LastName, Email, Phone, SSN, Address, etc. │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  STEP 5: Backup Masked Data                     │
│  Source: DEV / devdb                                            │
│  Destination: backup/YYYYMMDD_HHMMSS_devdb_Patients           │
│  Action: mongodump with timestamp                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  STEP 6: Restore to LOCL-Masked                 │
│  Source: backup/YYYYMMDD_HHMMSS_devdb_Patients                 │
│  Destination: LOCL / localdb-masked                             │
│  Action: mongorestore                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                     ✓ Workflow Complete!
```

## Step-by-Step Setup

### 1. Clone and Navigate

```bash
cd /path/to/mongo_phi_masker
```

### 2. Activate Virtual Environment

```bash
source .venv311/bin/activate  # macOS/Linux
# or
.venv311\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example if needed
cp ../shared_config/.env.example ../shared_config/.env

# Edit with your MongoDB connection details
nano ../shared_config/.env
```

**Minimum configuration:**

```bash
# LOCL Environment (simulates production)
MONGODB_URI_LOCL=mongodb://localhost:27017
DATABASE_NAME_LOCL=UbiquityLOCAL

# DEV Environment (where masking happens)
MONGODB_URI_DEV=mongodb://localhost:27017
DATABASE_NAME_DEV=UbiquityDEV
```

### 5. Verify Configuration

```bash
# Run pre-flight checks
python scripts/preflight_check.py --collection Patients --src-env LOCL --dst-env DEV --verbose
```

Expected output:

```
✓ Shared Config File
✓ Source Environment: LOCL
✓ Destination Environment: DEV
✓ All pre-flight checks passed!
```

### 6. Create Required Directories

```bash
mkdir -p backup logs reports checkpoints
```

## Running the Workflow

### Option 1: Complete Workflow (Recommended)

Use the orchestrator for the full 6-step workflow:

```bash
# Interactive mode - prompts before each step
./scripts/workflow_orchestrator.sh --collection Patients --size 10000 --interactive

# Automated mode - runs all steps without prompts
./scripts/workflow_orchestrator.sh --collection Patients --size 10000 --automated
```

**Expected duration for 10K documents:**

- Step 1 (Generate): ~30-60 seconds
- Step 2 (Backup): ~5-10 seconds
- Step 3 (Restore): ~5-10 seconds
- Step 4 (Mask): ~60-120 seconds
- Step 5 (Backup): ~5-10 seconds
- Step 6 (Restore): ~5-10 seconds
- **Total: ~2-4 minutes**

### Option 2: Individual Scripts

Run each step separately for more control:

#### Step 1: Generate Test Data

```bash
python scripts/generate_test_data.py \
  --collection Patients \
  --size 10000 \
  --env LOCL \
  --db UbiquityLOCAL
```

#### Step 2: Backup from LOCL

```bash
./scripts/backup_collection.sh \
  --env LOCL \
  --db UbiquityLOCAL \
  --collection Patients \
  --compress
```

#### Step 3: Restore to DEV

```bash
# Find the backup directory (most recent)
BACKUP_DIR=$(ls -td backup/*_UbiquityLOCAL_Patients | head -n 1)

./scripts/restore_collection.sh \
  --env DEV \
  --db UbiquityDEV \
  --backup-dir "$BACKUP_DIR" \
  --drop
```

#### Step 4: Mask Data

```bash
python masking.py \
  --config config/config_rules/config_Patients.json \
  --src-env DEV \
  --dst-env DEV \
  --src-db UbiquityDEV \
  --dst-db UbiquityDEV \
  --collection Patients \
  --in-situ
```

#### Step 5: Backup Masked Data

```bash
./scripts/backup_collection.sh \
  --env DEV \
  --db UbiquityDEV \
  --collection Patients \
  --compress
```

#### Step 6: Restore to LOCL-Masked

```bash
# Find the masked backup (most recent from DEV)
MASKED_BACKUP=$(ls -td backup/*_UbiquityDEV_Patients | head -n 1)

./scripts/restore_collection.sh \
  --env LOCL \
  --db UbiquityLOCAL-masked \
  --backup-dir "$MASKED_BACKUP" \
  --drop
```

## Validation

### 1. Document Count Validation

The orchestrator automatically validates document counts at each step. You can also verify manually:

```bash
# Count in LOCL unmasked
mongosh mongodb://localhost:27017/UbiquityLOCAL --eval "db.Patients.countDocuments({})"

# Count in DEV (masked)
mongosh mongodb://localhost:27017/UbiquityDEV --eval "db.Patients.countDocuments({})"

# Count in LOCL masked
mongosh mongodb://localhost:27017/UbiquityLOCAL-masked --eval "db.Patients.countDocuments({})"
```

All counts should match (e.g., 10,000 documents).

### 2. PHI Masking Validation

Compare original vs masked data:

```bash
python scripts/compare_masking.py \
  --src-env LOCL \
  --src-db UbiquityLOCAL \
  --dst-env LOCL \
  --dst-db UbiquityLOCAL-masked \
  --collection Patients \
  --sample-size 100
```

Expected output:

```
✓ FirstName: 100% masked (100/100 documents)
✓ LastName: 100% masked (100/100 documents)
✓ Email: 100% masked (100/100 documents)
✓ Phone: 100% masked (100/100 documents)
✓ SSN: 100% masked (100/100 documents)
✓ Non-PHI fields preserved
```

### 3. Sample Document Comparison

```bash
# View original document
mongosh mongodb://localhost:27017/UbiquityLOCAL --eval "db.Patients.findOne()"

# View masked document (same _id)
mongosh mongodb://localhost:27017/UbiquityLOCAL-masked --eval "db.Patients.findOne()"
```

Verify:

- PHI fields are different
- Non-PHI fields are identical
- Document structure is preserved

## Troubleshooting

### Issue: "shared_config/.env not found"

**Solution:**

```bash
# Copy example and configure
cp ../shared_config/.env.example ../shared_config/.env
nano ../shared_config/.env
```

### Issue: "Module 'faker' not found" or "Module 'tqdm' not found"

**Solution:**

```bash
pip install -r requirements.txt
# Or specifically:
pip install Faker==24.0.0 tqdm==4.66.1
```

### Issue: "MongoDB connection failed"

**Solution:**

```bash
# Check if MongoDB is running
mongosh --eval "db.adminCommand('ping')"

# If not running:
# macOS:
brew services start mongodb-community

# Linux:
sudo systemctl start mongod

# Docker:
docker start mongodb
```

### Issue: "Collection not found in COLLECTION_RULE_MAPPING"

**Solution:**

Ensure the collection is defined in `config/collection_rule_mapping.py`:

```python
COLLECTION_RULE_MAPPING = {
    # ... existing collections ...
    "Patients": "rule_group_1",  # Add if missing
}
```

### Issue: "Config file not found"

**Solution:**

Create configuration file for your collection:

```bash
# Copy from existing
cp config/config_rules/config_Container.json config/config_rules/config_Patients.json

# Edit for your collection
nano config/config_rules/config_Patients.json
```

### Issue: Pre-flight checks fail

**Solution:**

Run verbose pre-flight checks to see specific issues:

```bash
python scripts/preflight_check.py \
  --collection Patients \
  --src-env LOCL \
  --dst-env DEV \
  --verbose
```

Fix any reported errors before running the workflow.

## Performance Benchmarks

### Expected Performance (10K Documents)

| Step        | Duration    | Throughput          |
| ----------- | ----------- | ------------------- |
| 1. Generate | 30-60s      | ~200-300 docs/sec   |
| 2. Backup   | 5-10s       | N/A                 |
| 3. Restore  | 5-10s       | N/A                 |
| 4. Mask     | 60-120s     | ~80-150 docs/sec    |
| 5. Backup   | 5-10s       | N/A                 |
| 6. Restore  | 5-10s       | N/A                 |
| **Total**   | **2-4 min** | **~40-80 docs/sec** |

### Scaling to Larger Datasets

| Size | Estimated Duration |
| ---- | ------------------ |
| 10K  | 2-4 minutes        |
| 50K  | 10-20 minutes      |
| 100K | 20-40 minutes      |
| 500K | 1.5-3 hours        |

*Note: Performance varies based on hardware, network, and complexity of masking rules.*

## Next Steps

After successful workflow completion:

1. **Review masked data** - Verify PHI is properly masked
1. **Test application compatibility** - Ensure masked data works with your application
1. **Scale up** - Try larger datasets (50K, 100K)
1. **Automate** - Schedule regular masking workflows
1. **Monitor** - Track performance metrics and optimization opportunities

## Related Documentation

- [Pre-Flight Checks](PREFLIGHT_CHECKS.md) - Configuration validation
- [Test Data Export](TEST_DATA_EXPORT.md) - Exporting PHI-rich test data
- [Masking Validation](MASKING_VALIDATION.md) - Validating masking results
- [Performance Tracking](PERFORMANCE_TRACKING.md) - Monitoring pipeline performance

______________________________________________________________________

**Questions or Issues?**

Check the [Troubleshooting](#troubleshooting) section or review the logs in `logs/` directory.
