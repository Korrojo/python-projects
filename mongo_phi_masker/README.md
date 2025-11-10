# MongoDB PHI Masker

A production-ready data pipeline for masking Protected Health Information (PHI) in MongoDB collections.

## 📚 Documentation Index

### Core Documentation

| Document                                                   | Purpose                                          | When to Use                                |
| ---------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------ |
| **[README.md](README.md)** (this file)                     | Main documentation, workflows, quick start       | Start here for overview                    |
| **[COLLECTIONS.md](COLLECTIONS.md)**                       | Collection configuration inventory & setup guide | Adding new collections, validating configs |
| **[WINDOWS_TASK_SCHEDULER.md](WINDOWS_TASK_SCHEDULER.md)** | Windows Task Scheduler setup guide               | Scheduling automated workflows on Windows  |
| **[LOGGING_STANDARD.md](LOGGING_STANDARD.md)**             | Unified logging format specification             | Writing new scripts, debugging             |

### Quick Reference

- **New to the project?** → Start with [Quick Start](#quick-start) below
- **Setting up a new collection?** → See [COLLECTIONS.md](COLLECTIONS.md)
- **Running production workflow?** → See [Automated Orchestration](#automated-orchestration-production)
- **Scheduling on Windows?** → See [WINDOWS_TASK_SCHEDULER.md](WINDOWS_TASK_SCHEDULER.md)
- **Troubleshooting?** → See [Troubleshooting](#troubleshooting) section
- **Email notifications?** → See [Email Notifications](#email-notifications)
- **Understanding Steps 0-6?** → See [Complete End-to-End Workflow](#complete-end-to-end-workflow)

______________________________________________________________________

## Quick Start

### Prerequisites

- Python 3.11+
- MongoDB 4.4+ (local or Atlas)
- Shared configuration file: `../shared_config/.env`

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/mongo_phi_masker.git
   cd mongo_phi_masker
   ```

1. Create virtual environment:

   ```bash
   python3 -m venv .venv311
   source .venv311/bin/activate
   ```

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

1. Configure environments in `../shared_config/.env`:

   ```bash
   # Local MongoDB
   MONGODB_URI_LOCL=mongodb://localhost:27017
   DATABASE_NAME_LOCL=localdb

   # Atlas DEV
   MONGODB_URI_DEV=mongodb+srv://user:pass@cluster.mongodb.net
   DATABASE_NAME_DEV=dev-phidb
   ```

______________________________________________________________________

## Complete End-to-End Workflow

This workflow demonstrates the full PHI masking pipeline from test data generation through verification.

### Automated vs Manual Workflows

**Automated Production Workflow:**

- Use `scripts/orchestrate_masking.sh` for production
- Runs Steps 1-6 automatically
- Stops on any error
- Creates comprehensive logs
- See "Automated Orchestration" section below

**Manual Step-by-Step Workflow:**

- Best for learning, testing, troubleshooting
- Full control over each step
- See Steps 0-6 below

### Database Naming Convention

**Use these database names consistently:**

- **LOCL (Localhost):**
  - Unmasked: `local-phi-unmasked`
  - Masked: `local-phi-masked`
- **DEV (Atlas):**
  - Working database: `dev-phidb`

______________________________________________________________________

### ⚠️ Step 0: Generate Test Data (TESTING ONLY)

**NOT FOR PRODUCTION.** This simulates unmasked production data for testing purposes.

```bash
python scripts/generate_test_data.py \
  --env LOCL \
  --db local-phi-unmasked \
  --collection Patients \
  --size 100
```

**Output:** 100 test documents in `local-phi-unmasked.Patients` **Log:** `logs/test_data/YYYYMMDD_HHMMSS_Patients.log`

______________________________________________________________________

## Production Workflow (Steps 1-6)

### Step 1: Backup Unmasked Data from Source

```bash
bash scripts/backup_collection.sh \
  --env LOCL \
  --db local-phi-unmasked \
  --collection Patients \
  --compress
```

**Output:** `backup/YYYYMMDD_HHMMSS_local-phi-unmasked_Patients/` **Log:**
`logs/backup/YYYYMMDD_HHMMSS_backup_Patients.log`

______________________________________________________________________

### Step 2: Restore Unmasked Data to DEV

```bash
echo "y" | bash scripts/restore_collection.sh \
  --env DEV \
  --db dev-phidb \
  --backup-dir backup/20251106_172046_local-phi-unmasked_Patients \
  --drop
```

**Note:** Replace timestamp with your actual backup directory. **Log:**
`logs/restore/YYYYMMDD_HHMMSS_restore_Patients.log`

______________________________________________________________________

### Step 3: Mask Data on DEV (In-Situ)

```bash
python masking.py \
  --config config/config_rules/config_Patients.json \
  --collection Patients \
  --src-env DEV \
  --dst-env DEV \
  --src-db dev-phidb \
  --dst-db dev-phidb \
  --in-situ
```

**Verifies:**

- 34 masking rules applied
- DOB dates shifted by 2 years (month/day preserved)
- All PHI fields masked

**Log:** `logs/masking/YYYYMMDD_HHMMSS_mask_Patients_XXXXXX.log`

______________________________________________________________________

### Step 4: Backup Masked Data from DEV

```bash
bash scripts/backup_collection.sh \
  --env DEV \
  --db dev-phidb \
  --collection Patients \
  --compress
```

**Output:** `backup/YYYYMMDD_HHMMSS_dev-phidb_Patients/` **Log:** `logs/backup/YYYYMMDD_HHMMSS_backup_Patients.log`

______________________________________________________________________

### Step 5: Restore Masked Data to Destination

```bash
echo "y" | bash scripts/restore_collection.sh \
  --env LOCL \
  --db local-phi-masked \
  --backup-dir backup/20251106_174712_dev-phidb_Patients \
  --drop
```

**Note:** Replace timestamp with your actual backup directory. **Log:**
`logs/restore/YYYYMMDD_HHMMSS_restore_Patients.log`

______________________________________________________________________

### Step 6: Verify Masking Results

```bash
python scripts/verify_masking.py \
  --src-env LOCL \
  --dst-env LOCL \
  --src-db local-phi-unmasked \
  --dst-db local-phi-masked \
  --collection Patients \
  --sample-size 5
```

**Expected Results:**

- ✅ All PHI fields masked (FirstName, LastName, Email, DOB)
- ✅ Lowercase fields match uppercase
- ✅ DOB dates shifted by exactly 2 years
- ✅ Gender set to "Female"
- ✅ Non-PHI fields preserved

**Log:** `logs/verification/YYYYMMDD_HHMMSS_verify_Patients.log`

______________________________________________________________________

## Automated Orchestration (Production)

For production environments, use the orchestration script to automate Steps 1-6:

### Full Production Workflow

```bash
./scripts/orchestrate_masking.sh \
  --src-env PROD \
  --src-db prod-phidb \
  --proc-env DEV \
  --proc-db dev-phidb \
  --dst-env PROD \
  --dst-db prod-phidb-masked \
  --collection Patients
```

### Development/Testing Workflow

```bash
# Skip backups for faster testing
# NOTE: Masked data stays in DEV/dev-phidb ONLY
# Local databases (local-phi-unmasked, local-phi-masked) are NEVER created
./scripts/orchestrate_masking.sh \
  --src-env LOCL \
  --src-db local-phi-unmasked \
  --proc-env DEV \
  --proc-db dev-phidb \
  --dst-env LOCL \
  --dst-db local-phi-masked \
  --collection Patients \
  --skip-backup-source \
  --skip-backup-masked
```

### Create Local Masked Database

```bash
# Run ALL steps to populate local databases
# Requires: local-phi-unmasked exists (run Step 0 first)
# Creates: local-phi-masked with masked data
./scripts/orchestrate_masking.sh \
  --src-env LOCL \
  --src-db local-phi-unmasked \
  --proc-env DEV \
  --proc-db dev-phidb \
  --dst-env LOCL \
  --dst-db local-phi-masked \
  --collection Patients
```

### What It Does

The orchestration script automatically: 0. ✅ Validates collection configuration (Step 0 - automatic pre-flight check)

1. ✅ Backs up source data (Step 1)
1. ✅ Restores to processing environment (Step 2)
1. ✅ Masks data in-situ (Step 3)
1. ✅ Backs up masked data (Step 4)
1. ✅ Restores to destination (Step 5)
1. ✅ Verifies masking results (Step 6)

**Features:**

- **Automatic validation**: Checks collection configuration before starting (fails fast on errors)
- Stops immediately on any error
- Creates unified log file: `logs/orchestration/YYYYMMDD_HHMMSS_orchestrate_<collection>.log`
- Tracks execution time
- Shows clear progress for each step
- Lists all created artifacts

### Optional Flags

**`--skip-backup-source`** (Skip Step 1)

- Uses most recent existing backup instead of creating new one
- Source database is NOT accessed/modified
- Useful for: Testing when you already have a backup

**`--skip-backup-masked`** (Skip Step 4)

- No backup created from processing environment after masking
- **CASCADING EFFECT**: Automatically skips Step 5 (restore to destination)
- **Result**: Masked data stays in **processing environment ONLY**
- **Destination database is NEVER created/populated**
- Useful for: Development/testing when you only want to mask data in DEV

**`--skip-restore-dest`** (Skip Step 5)

- Masked data not restored to destination environment
- Destination database is NEVER created/populated
- Useful for: When you only need masked data in processing environment

**`--skip-validation`** (Skip Step 0)

- Bypasses pre-flight configuration validation
- **Not recommended** unless you're confident config is valid
- Useful for: Repeated runs on known-good collections

**`--skip-verification`** (Skip Step 6)

- No masking verification performed
- Useful for: Trusted workflows where verification is not needed

**`--verify-samples N`**

- Number of documents to verify (default: 5)
- Higher numbers = more thorough verification but slower

### Data Flow Based on Flags

**No flags (Full Production)**:

```
Source DB → Backup → Processing DB → Mask → Backup → Destination DB
Result: Masked data in DESTINATION database
```

**`--skip-backup-source --skip-backup-masked` (Development/Testing)**:

```
Existing Backup → Processing DB → Mask (stays in Processing DB)
Result: Masked data in PROCESSING database ONLY
Note: Source and Destination databases are NEVER touched
```

**`--skip-backup-source` (Use existing backup)**:

```
Existing Backup → Processing DB → Mask → Backup → Destination DB
Result: Masked data in DESTINATION database
```

### Monitoring

```bash
# Watch progress in real-time
tail -f logs/orchestration/YYYYMMDD_HHMMSS_orchestrate_Patients.log

# Check status
ps aux | grep orchestrate_masking.sh
```

### Email Notifications

The orchestration script can send HTML-formatted email notifications on success or failure.

**Configuration** (`../shared_config/.env`):

```bash
# Enable email notifications
EMAIL_NOTIFICATIONS_ENABLED=true

# Recipients (comma-separated)
EMAIL_RECIPIENTS=admin@company.com,team@company.com

# SMTP settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Optional customization
EMAIL_SENDER=phi-masker-noreply@company.com
EMAIL_SENDER_NAME=PHI Masking System
EMAIL_SUBJECT_PREFIX=[PHI Masker]
```

**Success Email** includes:

- Collection name and duration
- Data flow (source → processing → destination)
- List of artifacts created
- Log file path

**Failure Email** includes:

- Failed step number and name
- Error message
- Environment details
- Log file path
- Action required notice

**Disable for specific run**:

```bash
./scripts/orchestrate_masking.sh \
  --src-env PROD \
  --src-db prod-phidb \
  --proc-env DEV \
  --proc-db dev-phidb \
  --dst-env PROD \
  --dst-db prod-phidb-masked \
  --collection Patients \
  --no-email  # Disable emails for this run
```

______________________________________________________________________

## Data Quality Checks

After completing the workflow:

1. **Date Format:** All DOB fields should be `YYYY-MM-DDTHH:00:00.000Z`
1. **No Unix Timestamps:** Dates should not appear as negative numbers
1. **Masking Coverage:** All 34 rules applied (check verification log)
1. **Document Count:** Same count in original and masked collections

______________________________________________________________________

## Troubleshooting

**Issue:** Wrong database used **Solution:** Always specify `--db` flag explicitly

**Issue:** Credentials visible in logs **Solution:** Logs should show `mongodb+srv://***:***@host`

**Issue:** Date format issues **Solution:** Regenerate test data with updated script

______________________________________________________________________

## Configuration

### Collections Supported

- **Patients** - Primary test collection (34 masking rules)
- Container
- Messages
- OfflineAppointments
- PatientCarePlanHistory
- PatientReportFaxQueue
- StaffAvailability
- Tasks

Each collection has:

- Config file: `config/config_rules/config_<Collection>.json`
- Rules file: `config/masking_rules/rules_<collection>.json`

### Masking Rules

Rules are defined per collection in `config/masking_rules/rules_*.json`:

```json
{
  "rules": [
    {"field": "FirstName", "rule": "random_uppercase", "params": null},
    {"field": "Dob", "rule": "add_milliseconds", "params": 63072000000},
    {"field": "Email", "rule": "replace_email", "params": "xxxxxx@xxxx.com"}
  ]
}
```

**Available rules:**

- `random_uppercase` - Random uppercase string
- `add_milliseconds` - Shift dates by N milliseconds (2 years = 63072000000)
- `replace_email` - Replace with fixed email
- `replace_string` - Replace with fixed string
- `replace_gender` - Replace with fixed gender
- `random_10_digit_number` - Random 10-digit number
- `lowercase_match` - Match lowercase version of another field

______________________________________________________________________

## Project Structure

```
mongo_phi_masker/
├── config/
│   ├── collection_rule_mapping.py   # Field path mappings
│   ├── config_rules/                # Collection configs
│   └── masking_rules/               # Masking rules per collection
├── scripts/
│   ├── orchestrate_masking.sh       # Automated workflow (Steps 1-6)
│   ├── backup_collection.sh         # Backup script
│   ├── restore_collection.sh        # Restore script
│   ├── generate_test_data.py        # Test data generator
│   └── verify_masking.py            # Verification script
├── src/
│   ├── core/
│   │   ├── masker.py                # Core masking engine
│   │   └── connector.py             # MongoDB connection
│   ├── models/
│   │   └── masking_rule.py          # Rule definitions
│   └── utils/
│       ├── env_config.py            # Environment config loader
│       ├── config_loader.py         # Config file loader
│       └── logger.py                # Logging utilities
├── logs/                            # Log files (by operation)
├── backup/                          # Backup files
├── test-data/                       # Sample data files
├── tests/                           # Test suite
├── masking.py                       # Main masking script
├── README.md                        # This file
└── LOGGING_STANDARD.md              # Logging format standard
```

______________________________________________________________________

## Development

### Running Tests

```bash
# Run all unit tests
pytest tests/ -m "unit"

# Run specific test
pytest tests/test_masking_rules.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Adding a New Collection

1. Create masking rules: `config/masking_rules/rules_<collection>.json`
1. Create config file: `config/config_rules/config_<Collection>.json`
1. Add field mappings to `config/collection_rule_mapping.py`
1. Test with Step 0-6 workflow

______________________________________________________________________

## License

This project is licensed under the MIT License.

## Contributing

Contributions welcome! Please ensure:

1. Follow [LOGGING_STANDARD.md](LOGGING_STANDARD.md)
1. Test with Steps 0-6 workflow
1. Update documentation
