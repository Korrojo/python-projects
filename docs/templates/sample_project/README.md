# sample_project (unified)

A tiny scaffold that demonstrates the unified configuration pattern:

- Reads Mongo settings from `shared_config/.env` via `APP_ENV`
- Reads a small CSV from `data/input/sample_project/`
- Inserts docs into a collection (default `AD_test_<YYYYMMDD>`) in the configured database
- Dumps the inserted docs to `data/output/sample_project/` as JSON
- Logs under `logs/sample_project/`

## Quick start

```bash
# Set environment (or configure in shared_config/.env)
export APP_ENV=LOCL

# Prepare input (already included as sample_input.csv)
ls data/input/sample_project/

# Run
python sample_project/run.py

# Outputs
# - logs/sample_project/<timestamp>_app.log
# - data/output/sample_project/<timestamp>_inserted.json
```

## Configuration

From `shared_config/.env` using the current `APP_ENV`:

Required per environment:

- `MONGODB_URI_<ENV>`
- `DATABASE_NAME_<ENV>`

Optional overrides:

- `SAMPLE_COLLECTION_NAME_<ENV>` — target collection; default `AD_test_<YYYYMMDD>`
- `SAMPLE_INPUT_CSV_<ENV>` — input CSV path; default `sample_input.csv` under shared input dir

## CSV format

Default `data/input/sample_project/sample_input.csv`:

```
Id,Name,Email
1,Alice,alice@example.com
2,Bob,bob@example.com
3,Carol,carol@example.com
```

You can add additional columns; they will be included in the inserted documents.
