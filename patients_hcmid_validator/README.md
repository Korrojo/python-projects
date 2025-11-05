# patients_hcmid_validator

High-volume validation utility to compare input CSV or Excel patient identity records against the MongoDB `Patients`
collection using `HcmId` as the primary key.

## Features (Current)

**Multi-format support with separated implementations**: Optimized CSV and Excel processing with distinct, specialized
validation logic.

Implemented through Phase 6 (separated implementations):

- **Separated CSV and Excel implementations**: Distinct optimized processors for each format
- **Multi-format input support**: Both CSV and Excel (.xlsx/.xls) files with automatic format detection
- Streaming & batched processing of large files (500K+ rows) with constant memory usage per batch
- Batch Mongo lookups via `$in` on `HcmId` (single find per batch)
- Case-insensitive, trimmed comparison for `FirstName` / `LastName`
- Exact comparison for `Gender`, `Dob` (date-only), and `HcmId`
- Populates existing CSV columns: `Match Found` (`True`/`False`) & `Comments`
- **NEW**: Separate mismatches CSV file with database values and mismatched field names
- **Excel date handling**: Automatic conversion of Excel date formats to standard format
- **Enhanced logging**: Input file, output file, and processing parameters logged at startup
- Comments semantics:
  - `HcmId Not Found` – no matching document
  - Comma-separated mismatched field names (e.g., `FirstName,Dob`)
  - `<FieldName> missing on csv` – missing mandatory field in input
- Periodic progress logging every N rows (default 10,000)
- Timestamped outputs:
  - `data/output/patients_hcmid_validator/{timestamp}_output.csv` (main validation results)
  - `data/output/patients_hcmid_validator/{timestamp}_output_mismatches.csv` (mismatches only with DB values)
- Logging to: `logs/patients_hcmid_validator/{timestamp}_app.log`
- Retry with exponential backoff on Mongo batch failures (`--max-retries`, `--base-retry-sleep`)
- Final machine-readable JSON summary printed to stdout

### Input File Support

The validator now supports both CSV and Excel files:

#### **CSV Files**

- Standard comma-separated values with full date processing capabilities
- Advanced DOB normalization supporting multiple formats (D-Mon-YY, M/D/YY, YYYY-MM-DD, etc.)
- Configurable 2-digit year interpretation strategies (senior, pivot, force1900, force2000)
- UTF-8 encoding support with BOM handling
- Memory-efficient streaming for large files
- **Implementation**: `runner_csv.py` with comprehensive date parsing

#### **Excel Files (.xlsx/.xls)**

- Simplified date handling expecting pre-formatted YYYY-MM-DD dates
- Excel-native date formats automatically converted by openpyxl
- No complex date parsing needed (Excel dates are already resolved)
- Supports multiple sheets (specify with `--excel-sheet`)
- Handles Excel-specific data types (dates, numbers, formulas)
- **Implementation**: `runner_excel.py` with streamlined processing

**Format Detection**: Automatic based on file extension (`.csv`, `.xlsx`, `.xls`) or force with `--input-format`

### Mismatches CSV Format

The mismatches CSV contains only records where `Match Found = False`, with the following columns:

- `HcmId`, `FirstName`, `LastName`, `Dob`, `Gender` - Values from the **database**
- `Mismatched Field` - Comma-separated field names that didn't match (e.g., "Dob", "FirstName,Gender")
  - For "HcmId Not Found" cases: Contains "HcmId" and uses input values (since no DB record exists)

Planned polish / future (not implemented yet): parallel batches, richer mismatch detail, optional stats export.

## Running the Validation

You can run the validator in three ways:

### 1. Main CLI (Recommended - Auto-Detection)

The main CLI automatically detects file format and routes to the appropriate implementation:

````bash
# Auto-detect format from file extension
python -m patients_hcmid_validator --input data/sample.csv --collection Patients
python -m patients_hcmid_validator --input data/sample.xlsx --collection Patients

# Force specific format
# patients_hcmid_validator

High-volume validation utility to compare input CSV or Excel patient identity records against the MongoDB `Patients` collection using `HcmId` as the primary key.

This README consolidates all documentation previously split across multiple files: Excel support, mismatches feature, how to run, logging examples, and implementation summaries.

## Features

- Multi-format input: CSV and Excel (.xlsx/.xls) with automatic detection or `--input-format` override
- Separated optimized processors for CSV and Excel
- Streaming and batched processing for large files (500K+ rows)
- Batch Mongo lookups via `$in` on `HcmId`
- Case-insensitive, trimmed comparison for `FirstName`/`LastName`; exact for `Gender`, `Dob`, `HcmId`
- Populates `Match Found` (True/False) and `Comments` in the main CSV output
- Mismatches CSV: Separate file with database values and comma-separated mismatched fields
- Excel date handling with automatic conversion to a standard format
- Enhanced logging: file paths, environment, collection, and progress
- Retries with exponential backoff (`--max-retries`, `--base-retry-sleep`)
- Timestamped outputs under `data/output/patients_hcmid_validator/`

## Input File Support

### CSV Files
- Full date processing and normalization (D-Mon-YY, M/D/YY, YYYY-MM-DD, etc.)
- Configurable 2-digit year interpretation strategies (senior, pivot, force1900, force2000)
- UTF-8 with BOM handling; memory-efficient streaming
- Implementation: `runner_csv.py`

### Excel Files (.xlsx/.xls)
- Simplified date handling; Excel-native dates auto-converted by `openpyxl`
- Supports multiple sheets via `--excel-sheet`
- Handles Excel types: dates, numbers, formulas
- Implementation: `runner_excel.py`

Format detection is automatic based on extension or can be forced with `--input-format`.

## Mismatches CSV

When `Match Found = False`, a separate mismatches CSV is written alongside the main output: `data/output/patients_hcmid_validator/{timestamp}_output_mismatches.csv`.

Columns:
- `HcmId`, `FirstName`, `LastName`, `Dob`, `Gender` — values from the database (or input if `HcmId` not found)
- `Mismatched Field` — comma-separated names of the fields that differed (e.g., `Dob`, `FirstName,Gender`)

Behavior:
- If `HcmId` not found: uses input values and sets `Mismatched Field = HcmId`
- For field mismatches: uses database values and lists all mismatched fields
- Not created during `--dry-run`; created only if mismatches exist

## Enhanced Logging

At startup, logs include input file path/format, output file path, collection, environment, and (for Excel) sheet name. Periodic progress logs report row counts and match statistics. Completion logs include output locations.

Example:

```log
2025-10-15 18:01:25 | INFO | common_config.db.connection | Connecting to MongoDB ...
2025-10-15 18:01:26 | INFO | patients_hcmid_validator.runner_excel | Starting Excel validation - Input file: data\input\patients_hcmid_validator\file.xlsx
2025-10-15 18:01:26 | INFO | patients_hcmid_validator.runner_excel | Output file: data\output\patients_hcmid_validator\20251015_180118_output.csv, Collection: Patients, Environment: prod
2025-10-15 18:01:28 | INFO | common_config.db.connection | Connected to database 'UbiquityProduction'
2025-10-15 18:01:30 | INFO | patients_hcmid_validator.runner_excel | Processed 10000 rows (matched=9683 mismatched=317 not_found=0)
````

## How to Run

You can run via the main CLI (auto-detection) or the format-specific CLIs.

### 1) Main CLI (Recommended)

```bash
# Auto-detect from file extension
python -m patients_hcmid_validator --input data/sample.csv --collection Patients
python -m patients_hcmid_validator --input data/sample.xlsx --collection Patients

# Force a specific format
python -m patients_hcmid_validator --input data/sample.data --input-format excel --collection Patients
```

Common options:

- `--mongodb-env LOCL|PROD|STAGING` select environment
- `--batch-size N`, `--progress-every N`, `--max-retries N`, `--base-retry-sleep SEC`
- `--limit N`, `--dry-run`, `--debug`
- `--output path/to/output.csv` to customize the main output path

### 2) Direct CSV Implementation

```bash
# Direct CSV CLI with DOB options
python -m patients_hcmid_validator.cli_csv validate \
  data/sample.csv \
  output/results.csv \
  --collection Patients \
  --mongodb-env PROD \
  --dob-century-strategy pivot \
  --dob-two-digit-pivot 30

# As a module entry point
python -c "from patients_hcmid_validator.cli_csv import app; app()" validate data/sample.csv output/results.csv
```

### 3) Direct Excel Implementation

```bash
# Direct Excel CLI with sheet selection
python -m patients_hcmid_validator.cli_excel validate \
  data/sample.xlsx \
  output/results.csv \
  --collection Patients \
  --mongodb-env PROD \
  --excel-sheet "Patient Data"

# As a module entry point
python -c "from patients_hcmid_validator.cli_excel import app; app()" validate data/sample.xlsx output/results.csv
```

### Output Files

- Main results CSV: `data/output/patients_hcmid_validator/{timestamp}_output.csv` (original data + `Match Found` +
  `Comments`)
- Mismatches CSV: `data/output/patients_hcmid_validator/{timestamp}_output_mismatches.csv` (DB values +
  `Mismatched Field`)
- Logs: `logs/patients_hcmid_validator/{timestamp}_app.log`

## Installation & Setup

Prerequisites:

- Python 3.11+ with pip
- MongoDB access
- Packages: `typer`, `pymongo`, `openpyxl`, `pydantic`

Install (editable) on Windows:

```powershell
cd f:\ubiquityMongo_phiMasking\python

# Install common_config first
cd common_config
C:/Python314/python.exe -m pip install -e .

# Install patients_hcmid_validator
cd ../patients_hcmid_validator
C:/Python314/python.exe -m pip install -e .

# Verify
C:/Python314/python.exe -m patients_hcmid_validator --help
```

Meta package (optional for local dev):

```powershell
pip install -e common_config -e patients_hcmid_validator
# or include meta wrapper
pip install -e meta_pyproject.toml -e common_config -e patients_hcmid_validator
```

Then you can run:

```powershell
patients-hcmid-validate --input data/input/patients_hcmid_validator/sample.csv --collection Patients
# or via umbrella CLI if configured
ppro patients --input data/input/patients_hcmid_validator/sample.csv --collection Patients
```

### Environment Configuration

Set environment variables in `shared_config/.env` (examples):

```env
MONGODB_URI_LOCL=mongodb://localhost:27017
DATABASE_NAME_LOCL=UbiquityLOCAL
MONGODB_URI_PROD=mongodb://prod-server:27017
DATABASE_NAME_PROD=UbiquityPROD
```

## Troubleshooting

- Module not found: install packages with `pip install -e .`
- MongoDB connection: check env vars/network; try another `--mongodb-env`
- File not found: use absolute paths and verify existence
- Excel dates: Excel implementation expects YYYY-MM-DD (or Excel-native dates)
- Memory: use smaller `--batch-size`; consider CSV for very large files

### Validation snippets

```powershell
# Test MongoDB connection
C:/Python314/python.exe -c "from common_config.db.connection import MongoDBConnection; from common_config.config.settings import get_settings; import os; os.environ['APP_ENV']='PROD'; s=get_settings(); print(f'URI: {s.mongodb_uri}\nDB: {s.database_name}')"

# Test file exists
C:/Python314/python.exe -c "from pathlib import Path; print(Path('f:/data/sample.csv').exists())"
```

## Performance Guidelines

File size recommendations:

- \<10K rows: defaults
- 10K–100K: `--batch-size 2000`
- 100K–1M: `--batch-size 5000 --progress-every 25000`
- > 1M: `--batch-size 10000 --progress-every 50000`

Memory optimization:

- Prefer CSV for very large files (lowest overhead)
- Excel is inherently slower; consider converting to CSV for frequent runs

MongoDB performance:

- Ensure index: `db.Patients.createIndex({ HcmId: 1 })`
- Use production-grade Mongo for large datasets

## Implementation Summaries

### Mismatches Feature

- Adds a dedicated mismatches CSV with DB values and `Mismatched Field`
- Not created during dry runs; includes duplicates; uses input values when `HcmId` not found

### Excel Support

- `ExcelDictReader` adapter to mimic `csv.DictReader`
- Auto-detect format by extension; create appropriate reader
- Excel date handling converts native dates to a standard format
- CLI additions: `--input-format` and `--excel-sheet`
- Dependency: `openpyxl>=3.1.0` (graceful message if missing)

### Separated Implementations Overview

File structure highlights:

```
src/patients_hcmid_validator/
├── runner_csv.py          # CSV-specific validation logic
├── runner_excel.py        # Excel-specific validation logic
├── cli_csv.py             # CSV-specific CLI interface
├── cli_excel.py           # Excel-specific CLI interface
├── cli.py                 # Main CLI with auto-detection routing
└── __init__.py            # Package initialization
```

Key differences:

- CSV: comprehensive date parsing, 2-digit year strategies, `csv.DictReader`
- Excel: simplified date assumption (Excel-native → YYYY-MM-DD), `ExcelDictReader`, sheet selection
- Main `cli.py` auto-detects by extension and routes accordingly

## Roadmap

1. Scaffolding & CLI skeleton
1. Matching logic
1. Batch I/O + performance
1. Integration (retry, config, logging polish)
1. Enhancements (dry-run, limit)
1. Polishing & docs

## Testing Guide (Quick Reference)

Quick run and verify mismatches:

```powershell
# Run validator
python -m patients_hcmid_validator --input data/input/patients_hcmid_validator/sample.csv --collection Patients

# List recent outputs
ls data/output/patients_hcmid_validator/ | Sort-Object LastWriteTime -Descending | Select-Object -First 5

# Peek mismatches
Get-Content data/output/patients_hcmid_validator/*_mismatches.csv | Select-Object -First 20

# Count checks
(Import-Csv data/output/patients_hcmid_validator/*_output.csv).Count
(Import-Csv data/output/patients_hcmid_validator/*_output.csv | Where-Object {$_.'Match Found' -eq 'False'}).Count
(Import-Csv data/output/patients_hcmid_validator/*_mismatches.csv).Count
```

Tips:

- Mismatches CSV only created when mismatches exist; not created in `--dry-run`
- Values in mismatches come from DB (except `HcmId Not Found` uses input)
- Use `--debug` for verbose logs and progress

├── cli_excel.py # Excel-specific CLI ├── cli.py # Main CLI with auto-detection └── **init**.py # Package initialization

````

## Output

1. CSV: Original columns plus `Match Found`, `Comments` (created if not present).

1. Stdout: Final JSON summary, e.g.:

```json
{"summary":{"total_rows":500000,"matched":480000,"not_found":15000,"mismatched":5000}}
````

1. Logs: Detailed progress & batch retry information.

## Exit Codes

- 0 success
- 2 Mongo connection failure
- 3 Input file not found

## Performance Tips

- Keep an index on `HcmId` for the `Patients` collection: `db.Patients.createIndex({ HcmId: 1 })`.
- Adjust `--batch-size` to balance memory and round-trip overhead (1k–5k typical sweet spot).
- Increase `--progress-every` for less verbose logging during very large runs.

## Notes / Future

Testing intentionally deferred per initial scope. Consider adding:

- Unit tests for normalization & mismatch detection.
- Integration test using `mongomock` to validate batch logic.
- Optional mismatch frequency report.
