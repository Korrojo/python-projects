# PatientOtherDetail IsActive Update (Unified Config)

Bulk update and verification tools to set `Admits.IsActive = false` in the MongoDB PatientOtherDetails collection, now
fully aligned to the unified configuration via `shared_config/.env` and `common_config`.

## What’s included

- `run.py` — updates `Admits.$.IsActive = false` for rows in an Excel file
- `verify_updates.py` — reads the same Excel and compares values between two collections

## Configuration (unified-only)

All configuration is loaded from `shared_config/.env` using `APP_ENV`-suffixed variables. No per-project `.env` is used.

Required (per environment):

- `MONGODB_URI_<ENV>`
- `DATABASE_NAME_<ENV>`

Optional (project-specific overrides, if you want to change defaults):

- `COLLECTION_NAME_<ENV>` — defaults to `PatientOtherDetails_copy` for `run.py`
- `COLLECTION_BEFORE_<ENV>` — defaults to `PatientOtherDetails_backup` for `verify_updates.py`
- `COLLECTION_AFTER_<ENV>` — defaults to `PatientOtherDetails_copy` for `verify_updates.py`
- `INPUT_EXCEL_FILE_<ENV>` — defaults to `patient_updates.xlsx`

Where `<ENV>` is the value of `APP_ENV` (for example, `LOCL`, `DEV`, `TRNG`, `PROD`).

## Standardized paths

This project uses shared paths provided by `common_config`:

- Logs: `logs/PatientOtherDetail_isActive_false/`
- Inputs: `data/input/PatientOtherDetail_isActive_false/`
- Outputs: `data/output/PatientOtherDetail_isActive_false/`

By default, the scripts look for an Excel file named `patient_updates.xlsx` under the shared input folder above. You can
override the filename with `INPUT_EXCEL_FILE_<ENV>`.

## Excel File Format

The input Excel file must contain these columns:

- **Patientid** (or PatientId) - Patient reference ID
- **\_id** - MongoDB ObjectId of the admit record

Other columns are ignored. Column order doesn't matter.

## Usage

### 1) Update script (`run.py`)

Updates `Admits.IsActive = false` for matching documents in the input Excel.

Run (Windows bash):

```bash
# Optional: select environment; defaults to APP_ENV from shared_config/.env
export APP_ENV=LOCL
python run.py
```

**What it does:**

1. Reads Excel file from `data/input/`
1. For each row:
   - Finds document where `PatientRef` matches `Patientid`
   - Finds matching `Admits._id` in the Admits array
   - Sets `Admits.$.IsActive = false` using MongoDB positional operator
1. Logs all operations to `logs/PatientOtherDetail_isActive_false/`
1. Reports summary:
   - Successfully updated count
   - Not found count
   - Error count

**MongoDB Query:**

```javascript
// Query
{
  "PatientRef": <PatientId>,
  "Admits._id": ObjectId(<_id>)
}

// Update
{
  "$set": { "Admits.$.IsActive": false }
}
```

### 2) Verification script (`verify_updates.py`)

Compares before/after states by querying two collections.

Run:

```bash
export APP_ENV=LOCL
python verify_updates.py
```

**What it does:**

1. Reads same Excel file
1. Queries BOTH collections (before and after)
1. Extracts `Admits.IsActive` from each
1. Exports CSV to `data/output/PatientOtherDetail_isActive_false/{timestamp}_isactive_verification.csv`
1. Shows comparison summary

**Output CSV Columns:**

- `PatientId` - Patient reference
- `_id` - Admit ObjectId
- `IsActive_before` - Value from backup collection
- `IsActive_after` - Value from updated collection

**Sample Output:**

```
PatientId,_id,IsActive_before,IsActive_after
7027002,68dd1812a27ebadd49d703a8,True,False
7027078,68dd017fa27ebadd49c72cc6,True,False
```

### Task Scheduler (Windows)

`run.bat` is provided for scheduling. It defers to the Python logger which writes to
`logs/PatientOtherDetail_isActive_false/`. You can still capture console output if desired.

## Dependencies

Relies on the shared `common_config` package and repo-level requirements. Use the repo’s unified setup documented in the
root `README.md`.

## Logging

All executions are logged to `logs/` with timestamps:

- Format: `YYYYMMDD_HHMMSS_app.log`
- Includes: INFO, WARNING, ERROR levels
- Detailed operation tracking
- Performance metrics

## Error Handling

The scripts handle:

- **Invalid ObjectIds** - Logged as warnings, skipped
- **Missing documents** - Logged as "NOT_FOUND"
- **MongoDB connection errors** - Graceful failure with error messages
- **Excel format issues** - Clear validation errors

## Safety Features

1. **Read-only verification** - `verify_updates.py` never modifies data
1. **Detailed logging** - Full audit trail of all operations
1. **Dry-run capability** - Test with small datasets first
1. **Before/after comparison** - Verify changes were applied correctly

## Example Workflow

1. **Backup your collection:**

   ```javascript
   db.PatientOtherDetails.aggregate([
     { $out: "PatientOtherDetails_bkp_20251001" }
   ])
   ```

1. **Update config/.env** with collection names

1. **Place Excel file** in `data/input/`

1. **Run update:**

   ```bash
   python run.py
   ```

1. **Verify changes:**

   ```bash
   python verify_updates.py
   ```

1. **Review CSV** in `data/output/` and logs in `logs/`

## Troubleshooting

### "Missing required columns"

- Ensure Excel has `Patientid` and `_id` columns (case-sensitive)
- Check column names match exactly

### "MongoDB connection test failed"

- Verify `MONGODB_URI` in `../shared_config/.env`
- Check network connectivity
- Verify credentials

### "Input file not found"

- Check `INPUT_EXCEL_FILE` path in `config/.env`
- Ensure file exists in `data/input/`

### No CSV output from verify script

- Let script complete (don't interrupt)
- Check logs for errors
- Verify both collections exist

## Performance

- **Update speed**: ~10-15 documents/second
- **Verification speed**: ~5-8 documents/second (queries 2 collections)
- **7000 rows**: ~8-10 minutes for update, ~15-20 minutes for verification

## Architecture

Uses `common_config` for:

- Pydantic settings with automatic `shared_config/.env` loading (via `APP_ENV`)
- MongoDB connection and health checks
- Structured logging under shared `logs/`
- Standardized error handling

## Notes

- Updates use MongoDB's positional operator `$` to update specific array element
- Only the first matching admit in the array is updated per query
- Duplicate PatientId + \_id combinations in Excel will show `modified=0` after first update
- Verification script is READ-ONLY and safe to run multiple times

## Support

For issues or questions, check:

1. Logs in `logs/PatientOtherDetail_isActive_false/`
1. Shared config in `shared_config/.env` (verify `APP_ENV`, `MONGODB_URI_<ENV>`, `DATABASE_NAME_<ENV>`)
