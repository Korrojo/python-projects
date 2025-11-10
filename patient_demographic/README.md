# Patient Demographics Update System

## Overview

A production-ready Python system for updating patient demographic data in MongoDB from CSV files. The system handles CSV
transformation, database updates, and cross-environment validation with comprehensive logging.

**Key Features:**

- ✅ CSV-to-MongoDB transformation with automatic data type conversion
- ✅ Safe database updates with metadata management
- ✅ Cross-environment validation (Production vs Training)
- ✅ Comprehensive logging and audit trails
- ✅ Support for multiple environments (Production, Training, Staging)

> Unified configuration (new)
>
> This project now supports the workspace-wide unified configuration via `common_config` and `shared_config/.env`.
>
> - Prefer setting your Mongo URI and database in `../shared_config/.env` and selecting the environment using `APP_ENV`
>   (e.g., `stg`, `prod`).
> - Logging and data paths will use the shared folders from the repository root.
> - The legacy `env/` files still work as a fallback during migration.

______________________________________________________________________

## Table of Contents

1. [Quick Start](#quick-start)
1. [Project Structure](#project-structure)
1. [Prerequisites](#prerequisites)
1. [Installation](#installation)
1. [Configuration](#configuration)
1. [Usage](#usage)
1. [Validation](#validation)
1. [Troubleshooting](#troubleshooting)
1. [Technical Details](#technical-details)

______________________________________________________________________

## Quick Start

### For First-Time Users (Unified Setup)

```bash
# From repo root (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows Git Bash/macOS/Linux
# or PowerShell: .\.venv\Scripts\Activate.ps1

pip install -e ./common_config
# optional: project deps
pip install -r patient_demographic/requirements.txt

# Configure shared environment
# Edit shared_config/.env and set APP_ENV and suffixed vars: MONGODB_URI_<ENV>, DATABASE_NAME_<ENV>

# Run transformation and update using unified settings
cd patient_demographic
python src/transformers/transform_csv_data.py --input data/input/your_file.csv --output data/output/your_file_transformed.csv
python src/core/update_mongodb_from_csv.py --csv data/output/your_file_transformed.csv
```

### Legacy Setup (Fallback)

```bash
# 1. Clone/navigate to project directory
cd patient_demographic

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure shared environment once
# Edit shared_config/.env and set APP_ENV, MONGODB_URI_<ENV>, DATABASE_NAME_<ENV>

# 4. Place your CSV file in shared input
cp your_file.csv data/input/patient_demographic/

# 5. Run transformation (shared paths)
python src/transformers/transform_csv_data.py \
  --input "data/input/patient_demographic/your_file.csv" \
  --output "data/output/patient_demographic/your_file_transformed.csv"

# 6. Run database update (unified-only)
python src/core/update_mongodb_from_csv.py \
  --csv "data/output/patient_demographic/your_file_transformed.csv"

# 7. Run validation (read-only)
python validate_prod_vs_training.py
```

> Unified-only: This project now uses `shared_config/.env` via `common_config` exclusively; no per-project `env/` files
> or `--env` flags.

______________________________________________________________________

## Project Structure

```
patient_demographic/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git ignore rules
│
├── src/                               # Source code
│   ├── transformers/
│   │   └── transform_csv_data.py      # CSV transformation script
│   ├── core/
│   │   └── update_mongodb_from_csv.py # MongoDB update script
│   └── connectors/
│       └── mongodb_connector.py       # MongoDB connection handler
│
├── env/                               # Environment configurations
│   ├── env.prod                       # Production environment
│   ├── env.trng                       # Training environment
│   └── env.stg                        # Staging environment
│
├── data/                              # Data files
│   ├── input/                         # Raw CSV files (place here)
│   └── output/                        # Transformed CSV files
│
├── logs/                              # Process logs (auto-generated)
│
├── schema/                            # MongoDB schema reference
│   └── patients_schema.js
│
├── archive/                           # Archived/unused files
│
└── validate_prod_vs_training.py      # Validation script
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
python-dateutil
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

This project now uses the unified configuration in `shared_config/.env` via `common_config`.

- Set `APP_ENV` and provide suffixed keys like `MONGODB_URI_TRNG`, `DATABASE_NAME_TRNG`, `MONGODB_URI_PROD`,
  `DATABASE_NAME_PROD`, etc.
- Directories are auto-created at startup: `logs/`, `data/input/`, `data/output/`, `archive/` under the repo’s shared
  root with a per-project subfolder (e.g., `logs/patient_demographic`).
- No per-project `.env` files are used anymore. See the root `README.md` for detailed examples.

______________________________________________________________________

## Usage

### Step 1: Prepare Your CSV File

Place your raw CSV file in `data/input/patient_demographic/`. The CSV should have these columns:

**Required Columns:**

- `patientid` - Patient ID (will become AthenaPatientId)
- `ptnt bqty lgcy ptnt d` - Legacy Patient ID (will become PatientId)
- `patient name` - Full name (will be split into FirstName/LastName)
- `patientdob` - Date of birth (MM/DD/YY or MM/DD/YYYY)
- `patientsex` - Gender (F/M)

**Optional Columns:**

- `patient email` - Email address
- `patient address1` - Street address line 1
- `patient address2` - Street address line 2
- `patient city` - City
- `patient state` - State code
- `patient zip` - ZIP code
- `patient homephone` - Home phone number

### Step 2: Transform CSV Data

```bash
python src/transformers/transform_csv_data.py \
  --input "data/input/patient_demographic/Patient_Demographics_20251002.csv" \
  --output "data/output/patient_demographic/Patient_Demographics_20251002_transformed.csv"
```

**What This Does:**

- Converts `patientid` → `AthenaPatientId` (integer)
- Converts `ptnt bqty lgcy ptnt d` → `PatientId` (integer)
- Splits `patient name` → `FirstName` + `LastName`
- Parses dates (handles 2-digit years: >50 = 19xx, ≤50 = 20xx)
- Expands gender (F → Female, M → Male)
- Cleans phone numbers (removes formatting, keeps 10 digits)
- Creates transformed CSV ready for MongoDB

**Output**: `data/output/patient_demographic/Patient_Demographics_20251002_transformed.csv`

**Log File**: `logs/patient_demographic/YYYYMMDD_HHMMSS_transform_csv_data.log`

### Step 3: Update MongoDB

```bash
python src/core/update_mongodb_from_csv.py \
  --csv "data/output/patient_demographic/Patient_Demographics_20251002_transformed.csv"
```

**What This Does:**

- Connects to MongoDB using unified `shared_config/.env` (suffixes like TRNG/PROD)
- Updates patient records one by one
- Updates top-level fields (FirstName, LastName, Dob, Gender, Email, AthenaPatientId)
- Updates Home address in Address array
- Updates Home phone in Phones array
- Sets metadata (UpdatedOn timestamps, IsActive flags)
- Sets `patient_demographic_updated = true` flag
- Logs all operations

**Output**: Updated MongoDB collection

**Log File**: `logs/patient_demographic/YYYYMMDD_HHMMSS_update_mongodb_from_csv.log`

### Step 4: Validate Updates

```bash
python validate_prod_vs_training.py
```

**What This Does:**

- Connects to BEFORE environment (Production via `env/env.prod`)
- Connects to AFTER environment (Training via `env/env.trng`)
- Samples 10 random PatientIds from CSV
- Compares BEFORE vs AFTER for each patient
- Validates all demographic fields were updated
- Validates metadata (UpdatedOn, patient_demographic_updated flag)
- Generates comprehensive validation report

**Output**: Validation report with success rate

**Log File**: `logs/YYYYMMDD_HHMMSS_validation_prod_vs_training.log`

______________________________________________________________________

## Validation

### What Gets Validated

**Top-Level Fields:**

- FirstName, LastName (and lowercase versions)
- Date of Birth (Dob)
- Gender
- Email
- AthenaPatientId

**Address Fields (Home address only):**

- Street1, Street2
- City, StateCode, Zip5
- UpdatedOn timestamp
- IsActive flag

**Phone Fields (Home phone only):**

- PhoneNumber (10-digit format)
- UpdatedOn timestamp
- IsActive flag

**Metadata:**

- `patient_demographic_updated` flag should be `true`
- `UpdatedOn` timestamps should be recent
- Lowercase name fields should match uppercase

### Success Criteria

✅ **100% Success Rate**: All sampled patients show changes\
✅ **All Fields Updated**: Every expected field shows BEFORE
→ AFTER change\
✅ **Metadata Valid**: Timestamps are recent, flags are set\
✅ **No Errors**: No patients missing from
either collection

### Example Validation Output

```
================================================================================
FINAL VALIDATION SUMMARY
================================================================================
Total Sampled: 10
Total Validated: 10
Changes Detected: 10
No Changes: 0
Not Found in BEFORE (Production): 0
Not Found in AFTER (Training): 0
Success Rate: 100.0%

--- PATIENT-BY-PATIENT SUMMARY ---
PatientId 7012467: ✓ PASS
  Changed: FirstName, LastName, Dob, Email, Address.Street1, Address.City, Phone.PhoneNumber
PatientId 2812722: ✓ PASS
  Changed: FirstName, LastName, Dob, Email, Address.Street1, Address.City, Phone.PhoneNumber
...
```

______________________________________________________________________

## Troubleshooting

### Common Issues

#### 1. Connection Failures

**Error**: `Failed to connect to MongoDB`

**Solution**:

- Check `env/env.trng` credentials are correct
- Verify network access to MongoDB host
- Confirm SSL/SRV settings match your MongoDB setup

#### 2. Type Errors

**Error**: `PatientId must be integer`

**Solution**:

- Ensure `ptnt bqty lgcy ptnt d` column has numeric values in CSV
- Check for empty or non-numeric values
- Review transformation log for parsing errors

#### 3. Date Parsing Errors

**Error**: `Could not parse date`

**Solution**:

- Verify date format is MM/DD/YY or MM/DD/YYYY
- Check for invalid dates (e.g., 13/32/2025)
- Review transformation log for specific date values

#### 4. No Records Updated

**Error**: `PatientId XXXXX not found in target collection`

**Solution**:

- Verify PatientIds in CSV exist in target MongoDB collection
- Check you're using the correct database/collection in env file
- Ensure PatientId column mapping is correct (7-digit number)

### Log Analysis

**Transformation Logs** (`logs/*_transform_csv_data.log`):

- Check number of rows processed
- Review sample transformed data
- Look for parsing warnings or errors

**Update Logs** (`logs/*_update_mongodb_from_csv.log`):

- Monitor successful updates
- Check for "not found" warnings
- Review error messages

**Validation Logs** (`logs/*_validation_prod_vs_training.log`):

- Review field-by-field comparisons
- Check metadata validation results
- Verify success rate

______________________________________________________________________

## Technical Details

### Data Transformation Logic

**PatientId Mapping:**

- CSV `ptnt bqty lgcy ptnt d` (7-digit) → MongoDB `PatientId`
- CSV `patientid` (4-digit) → MongoDB `AthenaPatientId`

**Name Parsing:**

- CSV `patient name` = "JOHN DOE"
- MongoDB `FirstName` = "JOHN"
- MongoDB `LastName` = "DOE"
- MongoDB `FirstNameLower` = "john" (auto-synced)
- MongoDB `LastNameLower` = "doe" (auto-synced)

**Date Parsing:**

- 2-digit year > 50 → 19xx (e.g., 57 → 1957)
- 2-digit year ≤ 50 → 20xx (e.g., 40 → 2040)
- Output format: YYYY-MM-DD

**Phone Formatting:**

- Input: "(555) 938-8855" or "555-938-8855"
- Output: "5559388855" (10 digits, no formatting)

### MongoDB Update Operations

**Top-Level Fields** (`$set`):

```javascript
{
  $set: {
    FirstName: "JOHN",
    LastName: "DOE",
    FirstNameLower: "john",
    LastNameLower: "doe",
    Dob: ISODate("1957-01-15"),
    Gender: "Male",
    Email: "john.doe@example.com",
    AthenaPatientId: 12345
  }
}
```

**Address Array** (Home type):

- If Home address exists: Update using `$set` with array index
- If Home address missing: Add using `$push`

```javascript
// Update existing
{
  $set: {
    "Address.0.Street1": "123 Main St",
    "Address.0.UpdatedOn": ISODate()
  }
}

// Add new
{
  $push: {
    Address: {
      AddressTypeValue: "Home",
      Street1: "123 Main St",
      IsActive: true,
      CreatedOn: ISODate(),
      UpdatedOn: ISODate()
    }
  }
}
```

**Phones Array** (Home type):

- If Home phone exists: Update using `$set`
- If Home phone missing: Add using `$push`

### Dependencies

```txt
pandas==2.0.3          # CSV processing and data manipulation
pymongo==4.5.0         # MongoDB driver
python-dateutil        # Date parsing utilities
```

______________________________________________________________________

## Security & Best Practices

### Security

- ✅ Environment variables for credentials (never hardcoded)
- ✅ `.gitignore` prevents committing sensitive files
- ✅ Separate environments for Production/Training/Staging
- ✅ Comprehensive logging for audit trails

### Best Practices

- ✅ Always test on Training environment first
- ✅ Run validation after every update
- ✅ Review logs before and after updates
- ✅ Keep backups of important collections
- ✅ Use staging environment for large-scale testing

______________________________________________________________________

## Support & Maintenance

### Log Files Location

All logs are stored under `logs/patient_demographic/` with timestamps:

- `logs/patient_demographic/YYYYMMDD_HHMMSS_transform_csv_data.log`
- `logs/patient_demographic/YYYYMMDD_HHMMSS_update_mongodb_from_csv.log`
- `logs/patient_demographic/YYYYMMDD_HHMMSS_validation_prod_vs_training.log`

### Cleanup

Logs and data files can accumulate. Periodically clean up:

```bash
# Remove old logs (older than 30 days)
find logs/ -name "*.log" -mtime +30 -delete

# Remove old CSV files
find data/output/ -name "*.csv" -mtime +30 -delete
```

______________________________________________________________________

## Version History

**Current Version**: 2.0\
**Last Updated**: October 2, 2025\
**Status**: Production-Ready

### Changelog

- **v2.0** (Oct 2025): Streamlined architecture, removed unused components
- **v1.0** (Jul 2025): Initial production release

______________________________________________________________________

## License

Internal use only. Proprietary software.

______________________________________________________________________

## Contact

For questions or issues, contact the development team.
