# Users Provider Update System

## Overview

A Python utility for updating MongoDB Users collection with Athena provider information from CSV files. The system
creates a backup collection, matches users by name, and updates provider-specific fields with comprehensive logging and
validation.

**Key Features:**

- ✅ Automated backup creation before updates
- ✅ Case-insensitive name matching (FirstName/LastName)
- ✅ Strict duplicate handling (skips all duplicates)
- ✅ Comprehensive logging with timestamps
- ✅ Post-update validation
- ✅ Support for multiple environments (dev/staging/production)

Unified configuration only

This project now uses the workspace-wide unified configuration via `common_config` and `shared_config/.env` exclusively.

- Set `APP_ENV` and environment-suffixed variables in `../shared_config/.env` (e.g., `MONGODB_URI_TRNG`,
  `DATABASE_NAME_TRNG`).
- Logs are written under `logs/users-provider-update/` and directories are auto-created at startup.
- Place inputs under `data/input/users-provider-update/` and outputs under `data/output/users-provider-update/`.

______________________________________________________________________

## Table of Contents

1. [Quick Start](#quick-start)
1. [Project Structure](#project-structure)
1. [Prerequisites](#prerequisites)
1. [Installation](#installation)
1. [Configuration](#configuration)
1. [Usage](#usage)
1. [Validation](#validation)
1. [Processing Rules](#processing-rules)
1. [Troubleshooting](#troubleshooting)

______________________________________________________________________

## Quick Start

### Quick Start (Unified Setup)

```bash
# From repo root
python -m venv .venv
source .venv/bin/activate  # Windows Git Bash/macOS/Linux
# or PowerShell: .\.venv\Scripts\Activate.ps1

pip install -e ./common_config
pip install -r users-provider-update/requirements.txt

# Configure shared environment once
# Edit shared_config/.env and set APP_ENV, MONGODB_URI_<ENV>, DATABASE_NAME_<ENV>

# Run update using unified settings
cd users-provider-update
python src/core/update_users_from_csv.py --csv "data/input/users-provider-update/provider_20250910.csv"

# Validate results
python validate_users_update.py --csv "data/input/users-provider-update/provider_20250910.csv" --sample 10
```

> Note: Project-local `env/` files and `--env` flags are no longer supported.

______________________________________________________________________

## Project Structure

```
users-provider-update/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git ignore rules
│
├── src/                               # Source code
│   ├── core/
│   │   └── update_users_from_csv.py   # Main update script
│   └── connectors/
│       └── mongodb_connector.py       # MongoDB connection handler
│
├── data/                              # Data files (shared root recommended)
│   ├── input/users-provider-update/   # Raw CSV files (place here)
│   └── output/users-provider-update/  # Processing results
│
├── logs/users-provider-update/        # Process logs (auto-generated via common_config)
│
├── artifacts/                         # Documentation and schemas
│
├── archive/                           # Archived files
│   └── nodejs_original/               # Original Node.js implementation
│
└── validate_users_update.py          # Validation script
```

______________________________________________________________________

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **MongoDB Access**: Credentials for target database
- **Network**: Access to MongoDB servers

### Required Python Packages

```txt
pandas==2.0.3
pymongo==4.5.0
```

______________________________________________________________________

## Installation

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Verify Installation

```bash
python -c "import pandas, pymongo; print('All packages installed successfully!')"
```

______________________________________________________________________

## Configuration

This project uses the shared `shared_config/.env` only. Set:

- `APP_ENV` and suffixed variables like `MONGODB_URI_PROD`, `DATABASE_NAME_PROD` (and TRNG/STG as needed)
- Optional per-project overrides via common_config settings (e.g., collection names) if supported

______________________________________________________________________

## Usage

### CSV File Format

Place your CSV file in `data/input/users-provider-update/`. Required columns:

| Column      | Purpose              | Example      | Notes                                |
| ----------- | -------------------- | ------------ | ------------------------------------ |
| `ID`        | Athena Provider ID   | `34`         | Maps to `AthenaProviderId` (integer) |
| `First`     | First Name           | `MANDY`      | Used for matching (case-insensitive) |
| `Last`      | Last Name            | `HEATON`     | Used for matching (case-insensitive) |
| `User Name` | Athena Username      | `mheaton12`  | Maps to `AthenaUserName`             |
| `NPI`       | National Provider ID | `1114382157` | Maps to `NPI` field                  |

### Running the Update

```bash
python src/core/update_users_from_csv.py \
  --csv "data/input/users-provider-update/provider_20250910.csv"
```

**What This Does:**

1. ✅ Connects to MongoDB using credentials from `shared_config/.env` (via common_config)
1. ✅ Creates backup collection (`Users` → `AD_Users_20250910`)
1. ✅ Reads and validates CSV data
1. ✅ Matches users by FirstName/LastName (case-insensitive, IsActive: true)
1. ✅ Updates matched users with Athena information
1. ✅ Logs all operations to `logs/` directory

**Output**:

- Updated MongoDB collection
- Log file: `logs/users-provider-update/YYYYMMDD_HHMMSS_update_users_from_csv.log`

______________________________________________________________________

## Validation

### Running Validation

```bash
# Validate all records
python validate_users_update.py \
  --csv "data/input/users-provider-update/provider_20250910.csv"

# Validate first 10 records only
python validate_users_update.py \
  --csv "data/input/users-provider-update/provider_20250910.csv" \
  --sample 10
```

**What Gets Validated:**

- ✅ User exists in MongoDB
- ✅ `AthenaProviderId` matches CSV ID
- ✅ `AthenaUserName` matches CSV User Name
- ✅ `NPI` matches CSV NPI

**Output Example:**

```
================================================================================
VALIDATION RESULTS
================================================================================

✅ MATCH: MANDY HEATON (AthenaProviderId: 34)
✅ MATCH: AMBER ARNOLD (AthenaProviderId: 56)
❌ NOT FOUND: JOHN SMITH
⚠️  DUPLICATE: JANE DOE (2 users found)

================================================================================
VALIDATION SUMMARY
================================================================================
Total records checked   : 67
Matched (✅)            : 60
Not found (❌)          : 5
Mismatched (⚠️)         : 2
Match rate              : 89.6%
================================================================================
```

## Git Bash Commands (Windows)

### Activate venv

```bash
source .venv/Scripts/activate
```

### Run update

- From repo root (adds package path so `src` is found):

```bash
PYTHONPATH=users-provider-update \
python users-provider-update/src/core/update_users_from_csv.py --csv "data/input/users-provider-update/Athena release preview Provider info.csv"
```

- Optional inline env overrides:

```bash
APP_ENV=STG3 COLLECTION_BEFORE=Users COLLECTION_AFTER=Users_bkp_20251110 \
PYTHONPATH=users-provider-update \
python users-provider-update/src/core/update_users_from_csv.py --csv "data/input/users-provider-update/Athena release preview Provider info.csv"
```

- From inside the project directory:

```bash
cd users-provider-update
python src/core/update_users_from_csv.py --csv "../data/input/users-provider-update/Athena release preview Provider info.csv"
```

### Run validation

- From repo root:

```bash
PYTHONPATH=users-provider-update \
python users-provider-update/validate_users_update.py --csv "data/input/users-provider-update/Athena release preview Provider info.csv" --sample 20
```

- From inside the project directory:

```bash
cd users-provider-update
python validate_users_update.py --csv "../data/input/users-provider-update/Athena release preview Provider info.csv" --sample 20
```

### Run tests

```bash
pytest -q users-provider-update/tests
```

## PowerShell Commands (Windows)

### Activate venv

```powershell
./.venv/Scripts/Activate.ps1
```

### Run update

- From repo root (set env and path so `src` is found):

```powershell
$env:PYTHONPATH = "users-provider-update"
python users-provider-update/src/core/update_users_from_csv.py --csv "data/input/users-provider-update/Athena release preview Provider info.csv"
```

- Optional env overrides before running:

```powershell
$env:APP_ENV = "STG3"
$env:COLLECTION_BEFORE = "Users"
$env:COLLECTION_AFTER = "Users_bkp_20251110"
$env:PYTHONPATH = "users-provider-update"
python users-provider-update/src/core/update_users_from_csv.py --csv "data/input/users-provider-update/Athena release preview Provider info.csv"
```

- From inside the project directory:

```powershell
cd users-provider-update
python src/core/update_users_from_csv.py --csv "../data/input/users-provider-update/Athena release preview Provider info.csv"
```

### Run validation

- From repo root:

```powershell
$env:PYTHONPATH = "users-provider-update"
python users-provider-update/validate_users_update.py --csv "data/input/users-provider-update/Athena release preview Provider info.csv" --sample 20
```

- From inside the project directory:

```powershell
cd users-provider-update
python validate_users_update.py --csv "../data/input/users-provider-update/Athena release preview Provider info.csv" --sample 20
```

### Run tests

```powershell
pytest -q users-provider-update/tests
```

______________________________________________________________________

## Processing Rules

### Matching & Update Logic

1. **Active Users Only**: Only users with `IsActive: true` are considered
1. **Case-Insensitive Matching**: Users matched by FirstName/LastName (case-insensitive, trimmed)
1. **Strict Duplicate Handling**: If multiple active users found, **ALL are skipped** (no updates)
1. **AthenaProviderId Check**: If user already has `AthenaProviderId`, update is skipped
1. **Three Field Update**: Updates `AthenaProviderId`, `AthenaUserName`, `NPI`
1. **Continue on Error**: Errors logged, processing continues for all records

### Order of Checks

1. Validate CSV row (required fields, correct types)
1. Find active users by name (case-insensitive)
1. If no users found → Log and skip
1. If multiple users found → Log all user IDs and skip (strict duplicate rule)
1. If single user found:
   - If `AthenaProviderId` exists → Log and skip
   - Else → Update user with Athena fields

### Example Log Messages

```
2025-10-02T14:15:36.123Z - Found duplicate users for JANE DOE. Skipping update for ALL matching records. User IDs: [507f1f77bcf86cd799439011, 507f191e810c19729de860ea]
2025-10-02T14:15:36.456Z - User JOHN SMITH (ID: 507f1f77bcf86cd799439011) already has an AthenaProviderId (34). Skipping.
2025-10-02T14:15:36.789Z - Successfully updated user AMBER ARNOLD (ID: 507f1f77bcf86cd799439011).
```

______________________________________________________________________

## Troubleshooting

### Common Issues

#### 1. Connection Failures

**Error**: `Failed to connect to MongoDB`

**Solution**:

- Check `env/env.dev` credentials are correct
- Verify network access to MongoDB host
- Confirm SSL/SRV settings match your MongoDB setup

#### 2. CSV Not Found

**Error**: `CSV file not found: data/input/provider_20250910.csv`

**Solution**:

- Verify CSV file is in `data/input/` directory
- Check file name matches exactly (case-sensitive)

#### 3. No Updates Occurring

**Cause**: Users not active or names don't match

**Solution**:

- Verify users have `IsActive: true` in MongoDB
- Check name spelling matches exactly
- Use validation script to identify mismatches

#### 4. Import Errors

**Error**: `ModuleNotFoundError: No module named 'pandas'`

**Solution**:

```bash
pip install -r requirements.txt
```

### Log Analysis

**Update Logs** (`logs/*_update_users_from_csv.log`):

- Check summary statistics
- Review successful updates
- Identify skipped records and reasons
- Look for error messages

**Validation Logs** (`logs/*_validation_users_update.log`):

- Review match rate
- Check for mismatches
- Identify missing users

______________________________________________________________________

## Workflow Steps

### 1. Preparation

- ✅ Verify MongoDB credentials in `env/env.dev`
- ✅ Confirm target database and collection
- ✅ Place CSV file in `data/input/`

### 2. Test with Sample (Recommended)

```bash
# Create a 3-row sample CSV for testing
head -4 data/input/users-provider-update/provider_20250910.csv > data/input/users-provider-update/provider_sample.csv

# Run update on sample
python src/core/update_users_from_csv.py \
  --csv "data/input/users-provider-update/provider_sample.csv"

# Validate sample
python validate_users_update.py \
  --csv "data/input/users-provider-update/provider_sample.csv"
```

### 3. Run Full Update

```bash
python src/core/update_users_from_csv.py \
  --csv "data/input/users-provider-update/provider_20250910.csv"
```

### 4. Validate Results

```bash
python validate_users_update.py \
  --csv "data/input/users-provider-update/provider_20250910.csv"
```

### 5. Review Logs

```bash
# View latest update log
ls -lt logs/users-provider-update/*_update_users_from_csv.log | head -1

# View latest validation log
ls -lt logs/users-provider-update/*_validation_users_update.log | head -1
```

### 6. Final Steps (After Validation)

- Rename original `Users` to `Users_bkp_{timestamp}`
- Rename backup collection (`AD_Users_20250910`) to `Users`

______________________________________________________________________

## Dependencies

```txt
pandas==2.0.3          # CSV processing and data manipulation
pymongo==4.5.0         # MongoDB driver
```

______________________________________________________________________

## Security & Best Practices

### Security

- ✅ Unified environment in shared_config/.env (never hardcoded)
- ✅ `.gitignore` prevents committing sensitive files
- ✅ Separate environments for Development/Staging/Production via suffixes
- ✅ Comprehensive logging for audit trails under shared logs directory

### Best Practices

- ✅ Always test on Development environment first
- ✅ Use sample CSV for initial testing
- ✅ Run validation after every update
- ✅ Review logs before and after updates
- ✅ Keep backups of important collections

______________________________________________________________________

## Version History

**Current Version**: 2.0 (Python)\
**Last Updated**: October 2, 2025\
**Status**: Production-Ready

### Changelog

- **v2.0** (Oct 2025): Complete Python rewrite from Node.js
- **v1.0** (Sep 2025): Initial Node.js implementation

______________________________________________________________________

## Support

### Log Files Location

All logs are stored in `logs/` directory with timestamps:

- `YYYYMMDD_HHMMSS_update_users_from_csv.log`
- `YYYYMMDD_HHMMSS_validation_users_update.log`

### Getting Help

1. Check logs in `logs/` directory for detailed error information
1. Review sample data in `artifacts/samples/` for expected formats
1. Test with small dataset first
1. Verify MongoDB permissions and connection settings

______________________________________________________________________

## License

Internal use only. Proprietary software.

______________________________________________________________________

## Contact

For questions or issues, contact: <demesew.abebe@optum.com>

______________________________________________________________________

**Last Updated**: October 2, 2025\
**Version**: 2.0 (Python)\
**Environment**: UbiquitySTG3 Database
