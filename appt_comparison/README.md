# Appointment Comparison Validator

Validates Athena appointment data (CSV) against MongoDB `StaffAvailability` collection to ensure data consistency between systems.

## Overview

This project compares appointment records from Athena (provided as CSV) with MongoDB appointments stored in the `StaffAvailability` collection. It performs:

1. **Primary Matching**: Looks up appointments by `AthenaAppointmentId`
2. **Field Validation**: Compares 4 key fields between CSV and MongoDB
3. **Secondary Matching**: Falls back to 4-field combination if AthenaAppointmentId not found
4. **Cleanup**: Automatically removes cancelled appointments and creates cleaned CSV

## Features

- ✅ **Integrated with common_config**: Uses shared settings, logging, and MongoDB utilities
- ✅ **Environment-based configuration**: Supports APP_ENV switching (PROD, STG, LOCL)
- ✅ **Batch processing**: Efficient MongoDB queries using `$in` aggregation
- ✅ **Progress logging**: Real-time progress updates every N rows
- ✅ **Retry logic**: Automatic retry with exponential backoff for MongoDB queries
- ✅ **Cleanup automation**: Removes "Cancelled" appointments before validation
- ✅ **Flexible CLI**: Support for row limits, batch size, and environment overrides
- ✅ **Comprehensive output**: Enriched CSV with validation results and statistics

## Project Structure

```
appointment_comparison/
├── config/
│   ├── .env.example           # Environment configuration template
│   └── app_config.json        # Processing settings (batch size, retry config)
├── src/
│   └── appointment_comparison/
│       ├── __init__.py        # Package initialization
│       ├── __main__.py        # CLI entry point
│       ├── csv_handler.py     # CSV read/write, date parsing, cleanup
│       ├── field_comparator.py # Field-by-field comparison logic
│       ├── mongo_matcher.py   # MongoDB query logic (primary & secondary)
│       └── validator.py       # Main orchestration
├── tests/                     # Unit tests
├── run.py                     # Python entry point
├── run.bat                    # Windows batch runner
├── pyproject.toml             # Black & Ruff configuration
├── .gitignore                 # Git ignore patterns
└── README.md                  # This file

Repo-Level Shared Directories (used by all projects):
├── ../../data/
│   ├── input/
│   │   └── appointment_comparison/     # Input CSV files
│   └── output/
│       └── appointment_comparison/     # Output CSV files (results + cleaned)
└── ../../logs/
    └── appointment_comparison/         # Log files
```

**Note**: This project uses repo-level shared directories for data and logs, following the common_config pattern. No project-level `data/` or `logs/` directories exist to avoid confusion.

## Installation

### Prerequisites

- Python 3.11+
- `common_config` package installed (editable)
- MongoDB connection configured in `shared_config/.env`

### Setup

1. **Install common_config** (if not already):
   ```bash
   pip install -e ../common_config
   ```

2. **Configure environment** in `shared_config/.env`:
   ```bash
   # MongoDB credentials (environment-suffixed)
   APP_ENV=PROD
   
   MONGODB_URI_PROD=mongodb://your-mongo-host:27017
   DATABASE_NAME_PROD=UbiquityProduction
   
   MONGODB_URI_LOCL=mongodb://localhost:27017
   DATABASE_NAME_LOCL=UbiquityLocal
   ```

3. **Place input CSV** in repo-level data directory:
   ```bash
   # From python root, files go in:
   data/input/appointment_comparison/Daily_Appointment_Comparison_input1_20251023.csv
   
   # Full path example:
   f:/ubiquityMongo_phiMasking/python/data/input/appointment_comparison/
   ```

## Usage

### Basic Usage

```bash
# Using run.py
python run.py --input Daily_Appointment_Comparison_input1_20251023.csv --env PROD

# Using run.bat (Windows)
run.bat --input Daily_Appointment_Comparison_input1_20251023.csv --env PROD

# Using Python module directly
python -m appointment_comparison.src.appointment_comparison --input yourfile.csv --env PROD
```

### CLI Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--input` | `-i` | Input CSV filename (relative to data/input/appointment_comparison/) | **Required** |
| `--env` | `-e` | Override APP_ENV (PROD, STG, LOCL, etc.) | From shared_config/.env |
| `--collection` | `-c` | MongoDB collection name | `StaffAvailability` |
| `--limit` | `-l` | Limit number of rows to process (useful for testing) | None (all rows) |
| `--batch-size` | `-b` | Number of records per MongoDB batch | `100` |
| `--progress-frequency` | `-p` | Log progress every N rows | `100` |

### Examples

**Test with 50 rows:**
```bash
python run.py --input myfile.csv --env PROD --limit 50
```

**Use larger batch size for performance:**
```bash
python run.py --input myfile.csv --env PROD --batch-size 200
```

**Local testing:**
```bash
python run.py --input myfile.csv --env LOCL --limit 10
```

**Production run:**
```bash
python run.py --input Daily_Appointment_Comparison_input1_20251023.csv --env PROD
```

## Input CSV Format

Expected columns:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `AthenaAppointmentId` | String/Number | Primary key from Athena | `18821` |
| `PatientRef` | Number | Patient reference ID | `2565003` |
| `PatientName` | String | Patient name (not used for matching) | `GENA SHADE` |
| `VisitTypeValue` | String | Type of visit | `Palliative Prognosis Visit` |
| `VisitStartDateTime` | String | Visit start time | `1:35 PM` |
| `AvailabilityDate` | String | Appointment date (M/D/YY format) | `10/27/25` |
| `Cancel Status` | String | "Cancelled" or empty (optional) | `Cancelled` |

**Note**: If `Cancel Status` column exists and contains "Cancelled", those rows will be automatically removed before validation.

## Output

### 1. Cleaned CSV (if applicable)
- **Location**: `data/input/appointment_comparison/{filename}_cleaned.csv` (saved back to input directory)
- **Created**: Only if "Cancelled" rows were removed (one-time operation)
- **Purpose**: Input CSV with cancelled appointments removed
- **Reuse**: On subsequent runs with the same source file, the existing cleaned file is reused automatically

### 2. Validation Results CSV
- **Location**: `data/output/appointment_comparison/{timestamp}_appointment_comparison_output.csv`
- **Contains**: All original columns + validation columns:
  - `AthenaAppointmentId Found?` - `True` if found in MongoDB, `False` otherwise
  - `Total Match?` - `True` if all 4 fields match, `False` otherwise
  - `Mismatched Fields` - Comma-separated list of mismatched fields
  - `Missing Fields` - Comma-separated list of required fields that are missing/empty
  - `Comment` - Additional notes (e.g., "Found via secondary matching")

### 3. Log File
- **Location**: `logs/appointment_comparison/{timestamp}_app.log`
- **Contains**: Detailed processing logs, progress updates, statistics

## Field Mapping & Comparison Rules

| CSV Field | MongoDB Path | Comparison Rule |
|-----------|--------------|-----------------|
| `AthenaAppointmentId` | `Slots.Appointments.AthenaAppointmentId` | Primary lookup key |
| `PatientRef` | `Slots.Appointments.PatientRef` | Exact number match (no decimals) |
| `VisitTypeValue` | `Slots.Appointments.VisitTypeValue` | Case-insensitive, trimmed |
| `AvailabilityDate` | `AvailabilityDate` (root) | Date-only (ignores time), M/D/YY → YYYY-MM-DD |
| `VisitStartDateTime` | `Slots.Appointments.VisitStartDateTime` | Time normalization: CSV "1:35 PM" vs MongoDB "13:35:00" |

### Date Handling

- **Input format**: `M/D/YY` (e.g., `10/27/25`, `1/5/26`)
- **Year interpretation**: 
  - `25-99` → `2025-2099`
  - `00-24` → `2000-2024`
- **Comparison**: Date-only (time component ignored)

### Time Handling (VisitStartDateTime)

- **CSV format**: 12-hour with AM/PM (e.g., `"1:35 PM"`, `"09:00 AM"`)
- **MongoDB format**: 24-hour HH:MM:SS (e.g., `"13:35:00"`, `"09:00:00"`)
- **Comparison**: Both parsed to Python time objects and compared
- **Fallback**: If parsing fails, exact string match is attempted

## Matching Logic

### Primary Matching (by AthenaAppointmentId)

1. Query MongoDB for `Slots.Appointments.AthenaAppointmentId` matching CSV value
2. If found:
   - Mark `AthenaAppointmentId Found? = True`
   - Compare 4 fields: PatientRef, VisitTypeValue, AvailabilityDate, VisitStartDateTime
   - If all match: `Total Match? = True`
   - If any mismatch: `Total Match? = False`, list mismatched fields

### Secondary Matching (by 4-field combination)

3. If `AthenaAppointmentId` **not found**:
   - Mark `AthenaAppointmentId Found? = False`
   - Query MongoDB using all 4 fields as combination:
     - `PatientRef` (exact)
     - `VisitTypeValue` (case-insensitive)
     - `AvailabilityDate` (date-only)
     - `VisitStartDateTime` (exact)
   - If match found (first result used):
     - `Total Match? = True` if all fields match
     - `Comment = "Found via secondary matching (4-field combination)"`
   - If no match found:
     - `Total Match? = False`
     - `Comment = "No matching appointment found in MongoDB"`

### Missing Fields Handling

If any required field (`AthenaAppointmentId`, `PatientRef`, `VisitTypeValue`, `AvailabilityDate`, `VisitStartDateTime`) is missing or empty:
- `Missing Fields` column lists the missing fields
- `Comment = "Missing required fields - no comparison performed"`
- No MongoDB query is executed

## Configuration

### App Config (`config/app_config.json`)

```json
{
  "processing": {
    "batch_size": 100,              // MongoDB batch size
    "progress_log_frequency": 100,  // Log every N rows
    "max_retries": 3,                // MongoDB retry attempts
    "base_retry_sleep": 2            // Retry backoff (seconds)
  },
  "validation": {
    "case_sensitive_visit_type": false,  // Case-insensitive VisitTypeValue
    "trim_strings": true                  // Trim whitespace before comparison
  }
}
```

### Environment Variables (in `shared_config/.env`)

```bash
# Active environment
APP_ENV=PROD

# MongoDB credentials (per environment)
MONGODB_URI_PROD=mongodb://prod-host:27017
DATABASE_NAME_PROD=UbiquityProduction

MONGODB_URI_LOCL=mongodb://localhost:27017
DATABASE_NAME_LOCL=UbiquityLocal

# Optional collection override
COLLECTION_NAME=StaffAvailability
```

## Statistics Output

After validation completes, a JSON summary is printed:

```json
{
  "status": "success",
  "input_file": "data/input/appointment_comparison/myfile.csv",
  "output_file": "data/output/appointment_comparison/20251023_123456_appointment_comparison_output.csv",
  "cleaned_file": "data/output/appointment_comparison/myfile_cleaned.csv",
  "statistics": {
    "total_rows": 4179,
    "cancelled_removed": 1523,
    "processed": 2656,
    "missing_fields": 1,
    "athena_id_found": 2345,
    "athena_id_not_found": 310,
    "secondary_matches": 145,
    "total_match": 2400,
    "total_mismatch": 256
  }
}
```

## Troubleshooting

### Common Issues

**1. "MongoDB URI and DATABASE_NAME must be set"**
- Check `shared_config/.env` has `MONGODB_URI_<ENV>` and `DATABASE_NAME_<ENV>`
- Verify `APP_ENV` is set correctly

**2. "Input file not found"**
- Place CSV in `data/input/appointment_comparison/`
- Or provide absolute path: `--input /full/path/to/file.csv`

**3. "Failed to parse date"**
- Check CSV dates are in `M/D/YY` format (e.g., `10/27/25`)
- Invalid dates will be logged as warnings

**4. MongoDB connection timeout**
- Verify MongoDB host is reachable
- Check firewall/network settings
- Retry logic will attempt 3 times with exponential backoff

### Performance Tips

- **Increase batch size** for large files: `--batch-size 200`
- **Test with limit** first: `--limit 100`
- **Check indexes** on MongoDB: `Slots.Appointments.AthenaAppointmentId` should be indexed

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_csv_handler.py
```

### Code Quality

```bash
# Format code
black src/

# Lint code
ruff check src/
```

## Integration with Common Config

This project follows the repository's unified pattern:

- ✅ Uses `common_config` for settings, logging, MongoDB connection
- ✅ Reads from shared `data/input/`, writes to `data/output/`
- ✅ Logs to shared `logs/appointment_comparison/`
- ✅ Supports `APP_ENV` environment switching
- ✅ Standard Black & Ruff configuration

## Conversion changes (recent)

These changes were introduced during the recent conversion to add a lightweight export tool and to ensure the project follows repository standards for logging, configuration, and file naming.

Files added/modified

- `src/mongo_latest_status_export.py` (new)
  - Standalone CLI script to export the latest appointment status for each `AthenaAppointmentId` in an input CSV.
  - Key features:
    - CLI options: `--input`, `--output` (auto-generated if not provided), `--collection`, `--env`, `--batch-size`, `--log`.
    - Respects repo `APP_ENV` (can override with `--env`) and passes the environment explicitly to the MongoDB connector.
    - Generates timestamped output and log filenames following repo naming conventions: `YYYYMMDD_HHMMSS_latest_status_export_<Database>.(csv|log)`.
    - Uses `common_config` for settings, logging, and MongoDB connection.
    - Batch processing of Athena IDs and conversion of CSV `AthenaAppointmentId` values to integers to match MongoDB types.
    - Writes CSV with columns: `AthenaAppointmentId,AvailabilityDate,# of Dups,InsertedOn,VisitStatus,InsertedOn.1,VisitStatus.1,InsertedOn.2,VisitStatus.2,Comment`.

- Minor lint/style fixes
  - Adjusted small helper functions in the new script to satisfy Ruff (e.g., replacing list comprehensions with `list()` and renaming ambiguous variables).

Notes and rationale

- Security: MongoDB connection strings and credentials are no longer logged. Connector logging was sanitized to only reference the environment name (e.g., `env: PROD`).
- Deterministic env selection: the script sets `os.environ['APP_ENV']` from `--env` and explicitly passes the resolved env to `get_mongo_client()` to avoid cached-settings or import-time defaults from selecting the wrong environment.
- File naming: output and log filenames are auto-generated with timestamps and database names to match the repository's `FILE_NAMING_CONVENTIONS.md` guidance.


## How to use the export scripts

### 1. Latest Status Export (by AthenaAppointmentId)
Activate the repo virtualenv and ensure `shared_config/.env` contains environment settings (or pass `--env`):

```powershell
python appt_comparison/src/mongo_latest_status_export.py -i data/input/appt_comparison/Daily_Appointment_Comparison_input1_20251028.csv -c StaffAvailabilityHistory --env PROD
```

Output CSV will be saved under `data/output/appt_comparison/` with a timestamped filename. Logs are saved under `logs/appt_comparison/` with a timestamped filename.

### 2. Latest Status Export by VisitTypeValue (NEW)
This script matches by both AthenaAppointmentId and VisitTypeValue, and copies PatientRef and apptcheckoutdate from the input CSV to the output.

**Input CSV columns required:**
- AthenaAppointmentId
- VisitTypeValue
- PatientRef
- apptcheckoutdate

**Output CSV columns:**
- AthenaAppointmentId
- VisitTypeValue
- AvailabilityDate
- VisitStatus
- UpdatedOn
- PatientRef (copied from input)
- apptcheckoutdate (copied from input)
- Comment

**Features:**
- Filters by AvailabilityDate (10/27/2025 to 10/30/2025)
- Matches by AthenaAppointmentId and VisitTypeValue; falls back to id-only match if needed
- Batches queries for efficiency
- Uses repo-standard logging and output file naming

**Usage example:**
```powershell
python appt_comparison/src/mongo_latest_status_export_by_visittype.py --input data/input/appt_comparison/2025-10-30_input.csv --env PROD --collection StaffAvailabilityHistory
```


**Options:**
- `--input` (required): Path to input CSV
- `--env` (optional): Environment (DEV, PROD, STG)
- `--collection` (**required**): MongoDB collection name. If not provided, the script will abort with a clear error message.
- `--batch-size` (optional): Batch size for queries (default: 1000)

**Error Handling:**
If `--collection` is not provided, the script will log and print:
`Error: Collection name is missing. Please provide --collection <name>.`

Output CSV will be saved under `data/output/appt_comparison/` with a timestamped filename. Logs are saved under `logs/appt_comparison/` with a timestamped filename.

If you need the older validation flow, the original validator (`src/validator.py`) remains unchanged and can still be used via the project's `run.py`.

## License

Internal use only - Optum Home Community

## Support

For issues or questions, contact the data engineering team.
