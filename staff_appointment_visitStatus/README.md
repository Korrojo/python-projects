# StaffAvailability Aggregation Utilities

This project contains a Python runner and a Mongo shell script to extract appointment rows from the
`UbiquityProduction.StaffAvailability` collection, using an index-friendly aggregation that pre-filters and then
flattens only the matching appointments.

The current focus is: given pairs of `(AthenaAppointmentId, PatientRef)`, return one row per matching appointment, with
key appointment details.

> Note on unified configuration (new)
>
> This project is now integrated with the shared `common_config` package used across the workspace. By default it reads
> settings from the unified environment:
>
> - Global `.env` locations (precedence): `shared_config/.env` < `config/.env` < project `.env` < OS env vars
> - Select environment via `APP_ENV` (dev, stg, stg1, stg2, trng, perf, phi, prprd, prod). For example, set
>   `APP_ENV=stg` to map `MONGODB_URI_STG` → `MONGODB_URI` implicitly.
> - When not provided via CLI, defaults for `--uri`, `--database`, `--collection`, and output folders come from
>   `common_config` settings.
>
> For best results, bootstrap the unified virtual environment at the repo root using `setup_workspace.ps1` and populate
> `shared_config/.env` from `.env.example`.

## Project structure

- `agg_query_runner.py` — Python CLI tool for the general aggregation
  - Supports single pair or batch input from CSV/Excel (first two columns only)
  - Reuses one MongoDB connection for batch processing
  - Prints JSON lines and writes CSV output
- `visit_status_report.py` — CSV-to-CSV tool that appends VisitStatus
  - Input headers (CSV): `PatientRef, VisitTypeValue, AthenaAppointmentId, AvailabilityDate`
  - Per-row filters (configurable via `--filters`): any of `AthenaAppointmentId` (token: `athena_appt_id`), `PatientRef`
    (token: `patient_id`), and `VisitTypeValue` (token: `visit_type`)
  - Date handling:
    - Default global date window: `AvailabilityDate` between `2025-06-28` and `2025-10-15` (inclusive)
    - Overridable via `--date_mode window --start_date YYYY-MM-DD --end_date YYYY-MM-DD`, or use per-row exact date with
      `--date_mode per_row`
  - Overwrites `VisitStatus` from DB; output also includes `VisitTypeValue` and a `Comment` column
  - If multiple appointments match, emits multiple rows (one per match)
  - If no match, writes a row with `VisitStatus` blank and `Comment = "match not found"`
  - `AvailabilityDate` in the output is normalized to `YYYY-MM-DD`
  - When `--output_csv` is not provided, the file is saved under the shared `data/output` path from `common_config`
    (e.g., `<repo>/common_project/data/output/...` depending on settings)
- `visit_status_report_threecol.py` — Variant VisitStatus appender that relies on `PatientRef`, `AvailabilityDate`, and
  `VisitTypeValue` only
  - Designed for extracts that lack `AthenaAppointmentId`
  - Exact date matches are required; multiple matches emit multiple rows
  - Exposed via the Typer command `run.py report-threecol`
- `agg_query.js` — Equivalent aggregation pipeline for Mongo shell / NoSQLBooster
- `data/`
  - `input/`
    - `sample_input_20251007.xlsx` — example input file (first two columns used)
    - `input_20251007.xlsx` — another example file
    - `input_20251009.csv` — input for `visit_status_report.py`
  - `output/`
    - `patients_appointments_20251007.csv` — example output CSV
  - `info/`
    - `schema_StaffAvailability_20251007.js` — schema snapshot to understand fields
    - `indexes_StaffAvailability.js` — reference of existing indexes
- `requirements.txt` — Python dependencies (pandas, pymongo, openpyxl)
- `.venv/` — local virtual environment (not required, but recommended)
- `archive/` — deprecated examples; excluded from current workflows

## Aggregation query (current shape)

Both `agg_query_runner.py` and `agg_query.js` use the same logic:

- `$match` (defaults and filters):
  - `IsActive: true`
  - Default `AvailabilityDate` window `2025-06-28T00:00:00Z` to `2025-10-15T23:59:59Z` (overridable via CLI in window
    mode)
  - Existence of at least one appointment in `Slots.Appointments[]` matching the selected filter fields
    (`athena_appt_id`, `patient_id`, `visit_type`)
- `$project` with `$map` + `$filter` to keep only matching appointments per slot
- `$unwind` twice to flatten each matching appointment to a separate row
- Final `$project` to produce a clean, flat record with these columns:
  - `IsActive, AvailabilityDate`
  - `PatientName, VisitTypeValue`
  - `VisitStartDateTime, VisitStartEndTime`
  - `VisitActualStartDateTime, VisitActualEndDateTime`
  - `VisitStatus, UpdatedByName, UpdatedOn`
  - `AthenaAppointmentId, PatientRef`

## Setup

1. Python 3.11+ recommended.

1. Create a virtual environment (optional but recommended):

   - PowerShell:

     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```

1. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

## MongoDB connection

- `agg_query_runner.py`
  - Connection details are read from `common_config` by default (URI, DB, collection). You can always override with CLI
    flags.
- `visit_status_report.py`
  - Also reads connection details from `common_config`. If your environment requires SRV resolution (`mongodb+srv://`),
    ensure `dnspython` is present in the environment (installed by the unified setup script). You can pass a standard
    `mongodb://host:port` via `--uri` to avoid SRV.

Examples:

- Default (uses the hard-coded `DEFAULT_URI`):

  ```powershell
  .venv\Scripts\python.exe agg_query_runner.py --athena_appt_id 10025 --patient_ref 7010699
  ```

- Overriding the URI (e.g., default local port):

  ```powershell
  .venv\Scripts\python.exe agg_query_runner.py --athena_appt_id 10025 --patient_ref 7010699 --uri "mongodb://localhost:27017"
  ```

## Usage

### Single pair (debug)

- PowerShell (one line):

  ```powershell
  .venv\Scripts\python.exe agg_query_runner.py --athena_appt_id 10025 --patient_ref 7010699
  ```

- Output:

  - Console: JSON lines with all projected fields
  - CSV: `./results/appointments_10025_7010699_2025-06-30.csv`

### Batch mode (first two columns only)

- Provide a CSV or Excel file with the first two columns as:

  - Column 1: `AthenaAppointmentId`
  - Column 2: `PatientRef`

- Example:

  ```powershell
  .venv\Scripts\python.exe agg_query_runner.py --input_file .\data\input\sample_input_20251007.xlsx
  ```

- Output:

  - A single combined CSV with all rows from all pairs:

    - Default: `./results/appointments_batch_2025-06-30_{N}.csv` where `{N}` is the number of pairs processed

  - Override output path:

    ```powershell
    .venv\Scripts\python.exe agg_query_runner.py --input_file .\data\input\sample_input_20251007.xlsx --output_csv .\results\appointments_batch.csv
    ```

### Visit Status Report (CSV to CSV)

- Input file format (CSV headers):

  - `PatientRef, VisitTypeValue, AthenaAppointmentId, AvailabilityDate`

- Behavior:

  - Filters are configurable via `--filters` using tokens: `athena_appt_id`, `patient_id`, `visit_type`.
  - Default global date window applies (`2025-06-28`..`2025-10-15`) unless overridden; or use per-row exact dates with
    `--date_mode per_row`.
  - Overwrites `VisitStatus` with the value from MongoDB; output includes `VisitTypeValue` and `Comment`.
  - If multiple appointments match, emits multiple rows (one per match).
  - If no match, writes a row with `VisitStatus` blank and `Comment = "match not found"`.
  - Output `AvailabilityDate` is normalized to `YYYY-MM-DD`.

- Dynamic options:

  - `--filters` (default: `athena_appt_id,patient_id,visit_type`)
    - Comma-separated tokens: `athena_appt_id`, `patient_id`, `visit_type`
    - Controls which appointment fields are used in the filter
  - `--date_mode` (default: `window`)
    - `window`: use global date window (see below)
    - `per_row`: use `AvailabilityDate` from each CSV row (exact match)
  - `--start_date`, `--end_date` (YYYY-MM-DD)
    - Only used when `--date_mode=window`; override the script defaults

#### Representative commands (Git Bash)

- All three filters with actual input date range (used in recent run):

```bash
python staff_appointment_visitStatus/visit_status_report.py \
  --input_file data/input/staff_appointment_visitStatus/Appointments_checkout_in_Athena_Sep_to_Nov_11-check_status_in_UB.csv \
  --output_csv data/output/staff_appointment_visitStatus/20251110_000002_athena_visit_status_report.csv \
  --filters "athena_appt_id,patient_id,visit_type" \
  --date_mode window \
  --start_date 2025-06-30 \
  --end_date 2025-11-10
```

- Excluding patient_id (athena_appt_id + visit_type only):

```bash
python staff_appointment_visitStatus/visit_status_report.py \
  --input_file data/input/staff_appointment_visitStatus/Appointments_checkout_in_Athena_Sep_to_Nov_11-check_status_in_UB.csv \
  --output_csv data/output/staff_appointment_visitStatus/20251110_000004_athena_visit_status_report.csv \
  --filters "athena_appt_id,visit_type" \
  --date_mode window \
  --start_date 2025-06-30 \
  --end_date 2025-11-10
```

- Only athena_appt_id (widest appointment-level capture):

```bash
python staff_appointment_visitStatus/visit_status_report.py \
  --input_file data/input/staff_appointment_visitStatus/Appointments_checkout_in_Athena_Sep_to_Nov_11-check_status_in_UB.csv \
  --output_csv data/output/staff_appointment_visitStatus/20251110_000003_athena_visit_status_report.csv \
  --filters "athena_appt_id" \
  --date_mode window \
  --start_date 2025-06-30 \
  --end_date 2025-11-10
```

- Per-row exact date mode (requires AvailabilityDate in CSV):

```bash
python staff_appointment_visitStatus/visit_status_report.py \
  --input_file data/input/staff_appointment_visitStatus/Appointments_checkout_in_Athena_Sep_to_Nov_11-check_status_in_UB.csv \
  --output_csv data/output/staff_appointment_visitStatus/athena_visit_status_report_perrow.csv \
  --filters "athena_appt_id,patient_id,visit_type" \
  --date_mode per_row
```

- Example run:

  ```powershell
  .venv\Scripts\python.exe visit_status_report.py `
    --input_file data\input\input_20251010.csv `
    --output_csv data\output\output_20251010.csv
  ```

  Use only AthenaAppointmentId + PatientRef (ignore VisitTypeValue):

  ```powershell
  .venv\Scripts\python.exe visit_status_report.py `
    --input_file data\input\input_20251010.csv `
    --output_csv data\output\output_20251010.csv `
    --filters "athena_appt_id,patient_id" `
    --date_mode window `
    --start_date 2025-06-28 `
    --end_date 2025-10-15
  ```

  Per-row exact date matching with all three filters:

  ```powershell
  .venv\Scripts\python.exe visit_status_report.py `
    --input_file data\input\input_20251010.csv `
    --output_csv data\output\output_20251010.csv `
    --filters "athena_appt_id,patient_id,visit_type" `
    --date_mode per_row
  ```

  Using an SRV MongoDB URI (mongodb+srv):

  ```powershell
  python staff_appointment_visitStatus\visit_status_report.py `
    --input_file staff_appointment_visitStatus\data\input\input_20251020.csv `
    --output_csv staff_appointment_visitStatus\data\output\output_20251020.csv `
    --uri mongodb+srv://<username>:<password>@ubiquityproduction.rgmqs.mongodb.net/
  ```

  Note: SRV URIs require the dnspython package in your environment. If you see an error about DNS/SRV resolution,
  install it:

  ```powershell
  pip install dnspython
  ```

- Notes:

  - The script logs start, input path, optional output path, Mongo URI, row count, and per-row match summaries, then
    prints a final "CSV saved" line.
  - It uses Python's builtin `csv` module (no pandas dependency).
  - If `--output_csv` is omitted, the output path defaults to the shared `data/output` directory from `common_config`.

### Visit Status Report (three-column variant)

- Input file format (CSV headers):

  - `PatientRef, AvailabilityDate, VisitTypeValue`

- Behavior:

  - Filters using patient, visit type, and exact availability timestamp (UTC is preferred; common date formats are
    parsed).
  - Overwrites/creates a `VisitStatus` column in the output; every matching appointment produces a row.
  - When no match is found, the row is emitted with an empty `VisitStatus`.
  - Hard-coded filters still require `IsActive=true` and default to `AvailabilityDate >= 2025-06-30` if the input date
    is missing or unparsable.

- Example run (leveraging unified settings via `shared_config/.env`):

  ```powershell
  python staff_appointment_visitStatus/run.py report-threecol `
    --input staff_appointment_visitStatus/vist_ststus_input.csv `
    --output staff_appointment_visitStatus/data/output/visit_status_results.csv
  ```

  Provide `--env prod` (or another environment) if your shared `.env` uses suffixed variables such as
  `MONGODB_URI_PROD`. The Typer wrapper sets `APP_ENV` automatically before invoking the script.

- Notes:

  - The script mirrors the original reporter's logging and output conventions.
  - Rows with unparsable dates are logged and written with blank VisitStatus to aid clean-up.
  - Because `AthenaAppointmentId` is not part of the filter, duplicates may occur when multiple appointments share the
    same patient, date, and visit type.

### Performance flags

- `--allow_disk_use` (default: true)
- `--max_time_ms` (default: 600000)

These are passed to MongoDB’s `aggregate()` to make long-running jobs more robust.

### Notes for PowerShell

- Use a single line or PowerShell backticks for multi-line commands:

  ```powershell
  .venv\Scripts\python.exe agg_query_runner.py `
    --input_file ".\data\input\sample_input_20251007.xlsx" `
    --output_csv ".\results\appointments_batch.csv"
  ```

- Backtick must be the last character on the line (no trailing spaces).

## Running the aggregation in Mongo shell

You can run `agg_query.js` in NoSQLBooster/MongoDB shell to test the pipeline. It contains the same logic but currently
hard-codes a single `(AthenaAppointmentId, PatientRef)` pair.

## Index recommendations

To accelerate this query shape, ensure the following indexes exist (collection: `UbiquityProduction.StaffAvailability`):

- Compound multikey on appointment fields:

  ```javascript
  db.getSiblingDB("UbiquityProduction").getCollection("StaffAvailability").createIndex(
    {
      "Slots.Appointments.AthenaAppointmentId": 1,
      "Slots.Appointments.PatientRef": 1
    },
    { name: "IX_Appt_AthenaId_PatientRef" }
  );
  ```

- Optional combined index (if you often use the same top-level filters):

  ```javascript
  db.getSiblingDB("UbiquityProduction").getCollection("StaffAvailability").createIndex(
    {
      IsActive: 1,
      "Slots.Appointments.AthenaAppointmentId": 1,
      "Slots.Appointments.PatientRef": 1,
      AvailabilityDate: 1
    },
    { name: "IX_Active_Appt_Then_Date", partialFilterExpression: { IsActive: true } }
  );
  ```

These allow MongoDB to reduce the candidate documents early and quickly locate matching appointment subdocuments.

## Current limitations

- **Defaults**: `IsActive=true` is fixed; the default `AvailabilityDate` window is `2025-06-28` through `2025-10-15`,
  but you can override it via CLI (`--date_mode window --start_date --end_date`). Code constants are
  `HARD_CODED_IS_ACTIVE`, `HARD_CODED_START_DATE`, `HARD_CODED_END_DATE`.
- **Input parsing (agg_query_runner.py)**: first two columns only (numeric). Rows with blanks/non-numeric are skipped.
- **Input parsing (visit_status_report.py)**: reads all required headers via `csv.DictReader`.
- **Console verbosity**: Printing every JSON/result row can slow very large batches.
- **Single-threaded**: Pairs are processed sequentially. Large batches can take time.
- **Connection strings**: You can always override via `--uri`.
- **Excluded folder**: `archive/` is deprecated; do not use scripts under it.

## Recommendations for improvement

- **Add a quiet mode**: `--quiet` to suppress per-row console output and show only progress + summary.
- **Parallel processing**: Optional `--workers N` to process multiple pairs concurrently (be mindful of server load and
  rate limits).
- **Single-aggregation batching**: For very large input lists, generate tokens of `(AthenaAppointmentId, PatientRef)`
  and use `$in` on a precomputed field to reduce round-trips.
- **Config file support**: Load connection and defaults from a `.env` or YAML (e.g., `config.yaml`) instead of code
  constants.
- **Robust logging**: Structured logs with per-batch/per-pair timing and error metrics.
- **Resumable batch**: Ability to resume from a checkpoint if the batch is interrupted.
- **Schema-driven projections**: Centralize the projection list and validations against the schema (see
  `data/info/schema_StaffAvailability_20251007.js`).
- **CI/test**: Add a test harness with a small local dataset and expected outputs for regression checks.

## Logging & Troubleshooting

- Logs are written automatically to `logs/staff-appointment-visitStatus/<YYYYMMDD_HHMMSS>_app.log`.

- To change the base log directory, set `LOG_DIR` (or `LOG_DIR_<ENV>`) in `shared_config/.env`.

- For more verbose diagnostics, you can run Python in unbuffered mode:

  ```powershell
  .venv\Scripts\python.exe -u staff_appointment_visitStatus\visit_status_report.py --input_file data\input\... --output_csv data\output\...
  ```

- If you see connection errors, verify the URI and port match your environment. Default MongoDB port is 27017.

- If imports like `common_config.*` are reported as missing in your editor, ensure the unified virtual environment is
  activated (see `setup_workspace.ps1`).

- For Excel input with `agg_query_runner.py`, ensure `openpyxl` is installed (included in `requirements.txt`).

- If results are unexpectedly empty, verify that all filters (IDs, VisitTypeValue, dates) match the DB schema.
