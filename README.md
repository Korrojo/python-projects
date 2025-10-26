# Python Projects Directory

Centralized Python projects using shared configuration and a unified automation package: `automate_refresh`.

> VS Code setup helpers: see [./.vscode/README.md](./.vscode/README.md) for one‑click extension install/export.
> Quick install on Windows: `./.vscode/install_extensions.ps1` | Git Bash/WSL: `./.vscode/install_extensions.sh`

## Workspace initialization (unified setup)

These steps bootstrap a single virtual environment and a shared configuration so every subproject runs consistently without per-project env duplication.

> **⚠️ IMPORTANT**: This repository uses **Python 3.11** by design. The virtual environment is named **`.venv311/`** to explicitly indicate this version requirement. All projects in this repository are developed and tested with Python 3.11.

1) Create and activate a virtual environment (Python 3.11 required)

Recommended (automated):

```bash
# Bash/Git Bash/Linux/macOS
./install_venv.sh

# PowerShell (Windows)
./install_venv.ps1
```

After running the install script, follow the printed instructions:
- `source activate_venv.sh`        # Bash/Git Bash/Linux/macOS
- `./activate_venv.ps1`            # PowerShell (Windows)
- `.venv311/Scripts/activate.bat`  # CMD (Windows)

Manual (if needed):
- PowerShell (Windows):
  - `python -m venv .venv311`
  - `\.venv311\Scripts\Activate.ps1`
- Git Bash (Windows) or macOS/Linux:
  - `python3.11 -m venv .venv311`
  - `source ./.venv311/bin/activate`

2) Install base dependencies and shared library (editable)

Install dependencies:
```bash
pip install -r requirements.txt
```

Install the shared package (editable):
```bash
pip install -e ./common_config
```
This provides: unified settings loader, standard paths (data/logs/temp/archive), logging, MongoDB connection helpers, and a scaffolder CLI.

3) Configure shared environment once

- Copy or create `shared_config/.env` and define environment‑suffixed variables:
  - Required per environment (example ENV suffixes: LOCL, DEV, STG, TRNG, PERF, PRPRD, PROD):
    - `MONGODB_URI_<ENV>`
    - `DATABASE_NAME_<ENV>`
    - `BACKUP_DIR_<ENV>` (for backups/exports when applicable)
    - `LOG_DIR_<ENV>` (optional; overrides default logs path)
  - Optional (for Mac SAS pulls): `AZ_SAS_DIR_URL_STG`, `AZ_SAS_DIR_URL_PROD`, etc.
- Select current environment via `APP_ENV` (case-insensitive: `locl`, `dev`, `stg`, `prod`, ...). You can:
  - Put `APP_ENV=<ENV>` in `shared_config/.env`, or
  - Export at runtime: `APP_ENV=stg python -m <project> ...`

4) Verify configuration quickly

Run this one-liner to confirm unified settings resolve correctly:

```bash
python -c "from common_config.config import get_settings; s=get_settings(); print(f'APP_ENV={s.app_env}\nURI={s.mongodb_uri}\nDB={s.database_name}\nPaths: data_in={s.paths.data_input}\n        data_out={s.paths.data_output}\n        logs={s.paths.logs}')"
```

5) Optional: install individual subprojects in editable mode for CLI entry-points

For projects that expose `-m <pkg>` CLIs (e.g., `patients_hcmid_validator`), install them in editable mode:

```bash
pip install -e ./patients_hcmid_validator
```

### Unified conventions

- Configuration precedence (last wins):
  1. Shared `.env` (auto-loaded from `shared_config/.env`)
  2. Project `config/.env` (if a project needs extra non-secret settings)
  3. Project root `.env` (rare)
  4. OS environment variables
- Standard paths are provided by `common_config` and used across projects:
  - Data input: `<repo>/data/input/<project_name>/`
  - Data output: `<repo>/data/output/<project_name>/`
  - Logs: `<repo>/logs/<project_name>/`
  - Temp: `<repo>/temp/<project_name>/` (if needed)
  - Archive: `<repo>/archive/<project_name>/` (if needed)
- **Directory Structure Convention**: All projects use **repo-level shared directories** for data and logs. Each project creates its own subdirectory within these shared directories (e.g., `data/input/appointment_comparison/`, `logs/patients_hcmid_validator/`). Projects should **NOT** create their own `data/`, `logs/`, `temp/`, or `archive/` directories at the project level to avoid confusion and maintain consistency.
- Goal: avoid per-project `env/`, `config/` (for secrets), `data/`, `logs/` duplication. Prefer `shared_config/.env` and the shared `data/` and `logs/` roots. Some legacy projects still contain local folders; new work should follow the unified setup.

## Current structure (key parts)

```text
.
├─ automate_refresh/
│  ├─ win/
│  │  ├─ export_sample_json.py      # Windows CLI entrypoint to export a sample
│  │  └─ modules/
│  │     ├─ config_loader.py        # Resolves APP_ENV + BACKUP_DIR to out_dir/export
│  │     └─ exporter.py             # Exports sample to JSON with progress logs and strict filename
│  ├─ mac/
│  │  ├─ run_mac_refresh.py         # macOS CLI: optional pull via azcopy + import
│  │  ├─ import_latest.py           # macOS CLI: import-only
│  │  └─ modules/
│  │     ├─ config_loader.py        # Resolves APP_ENV + BACKUP_DIR to in_dir
│  │     ├─ puller.py               # azcopy copy with include-pattern and overwrite=false
│  │     ├─ importer.py             # Finds latest strict file and imports, applies indexes
│  │     └─ indexer.py              # Applies PyMongo indexes from automate_refresh/indexes
│  └─ indexes/                      # Index JSONs: Index_<Collection>.js
├─ common_config/                   # Shared library (settings, logging, Mongo conn)
├─ patients_hcmid_validator/        # High-volume CSV vs Mongo Patients validator
├─ patient_data_extraction/          # Cross-DB patient extractor using common_config (shared paths)
├─ patient_demographic/              # Legacy demographics pipeline (uses its own env; to be unified)
├─ PatientOtherDetail_isActive_false/# Bulk toggle Admits.IsActive=false; partially unified (uses shared + local)
├─ shared_config/
│  └─ .env                          # APP_ENV, MONGODB_*, DATABASE_*, BACKUP_DIR_*, LOG_DIR_*, AZ_SAS_DIR_URL_*
├─ logs/                            # Auto logs/<env>/automate_refresh
├─ data/, temp/, archive/           # Standard dirs
├─ requirements.txt                 # Root (if present) or project specific
├─ pyproject.toml                   # Black + Ruff config
├─ LINTING.md, lint.sh              # Code quality
├─ TODO.md                          # Enhancements backlog (new)
└─ README.md                        # This file
```

## Core conventions

- Strict export filename:
  - `yyyymmdd_HHMMSS_export_<collection>.json`
- Default paths:
  - Windows export: `<BACKUP_DIR_<ENV>>/export/`
  - Mac import input: `BACKUP_DIR_LOCL` (e.g., `~/Backups/local/export`)
- Logs: `logs/<env>/automate_refresh/<timestamp>_{export|import}_<collection>.log`
- APP_ENV-driven resolution of environment-suffixed variables from `shared_config/.env`:
  - `MONGODB_URI_<ENV>`, `DATABASE_NAME_<ENV>`, `BACKUP_DIR_<ENV>`, `LOG_DIR_<ENV>`, `AZ_SAS_DIR_URL_<ENV>`

### Per-project quickstarts (summary; see individual READMEs)

- `automate_refresh/` (Windows/Mac): Uses `common_config` and `shared_config/.env`. See `automate_refresh/README.md` for export/import workflows.
- `patients_hcmid_validator/`: Fully unified; outputs to shared `data/output/patients_hcmid_validator/` and logs under `logs/patients_hcmid_validator/`. See `patients_hcmid_validator/README.md`.
- `staff_appointment_visitStatus/`: Unified; reads settings from `shared_config/.env`. See `staff_appointment_visitStatus/README.md`.
- `patient_data_extraction/`: Unified; uses shared DB settings for two databases and writes to `data/output/patient_data_extraction/`. See `patient_data_extraction/README.md`.
- `PatientOtherDetail_isActive_false/`: Unified; uses `shared_config/.env` only and shared paths under `data/` and `logs/`. See `PatientOtherDetail_isActive_false/README.md`.
- `appointment_comparison/`: Unified validator comparing Athena CSV appointments against MongoDB StaffAvailability. Inputs from `data/input/appointment_comparison/`, outputs to `data/output/appointment_comparison/`, logs to `logs/appointment_comparison/`. See `appointment_comparison/README.md`.

#### PatientOtherDetail_isActive_false quickstart

```bash
# Ensure APP_ENV is set (or define in shared_config/.env)
export APP_ENV=LOCL

# Place your Excel here (default name):
#   data/input/PatientOtherDetail_isActive_false/patient_updates.xlsx

# Update Admits.IsActive to false for matching rows
python PatientOtherDetail_isActive_false/run.py

# Verify before/after across two collections
python PatientOtherDetail_isActive_false/verify_updates.py

# Outputs
# - Logs:   logs/PatientOtherDetail_isActive_false/
# - Verify: data/output/PatientOtherDetail_isActive_false/<ts>_isactive_verification.csv
```
- `patient_demographic/`: Unified; uses shared_config/.env and shared data/logs paths. See `patient_demographic/README.md`.
- `users-provider-update/`: Unified; uses shared_config/.env and shared paths. See `users-provider-update/README.md`.

## Setup

### Prerequisites

- Python 3.11+
- Install `common_config` (editable) if not already in your env
  - pip install -e ./common_config
- Populate `shared_config/.env` with your environment values
  - Required: `MONGODB_URI_<ENV>`, `DATABASE_NAME_<ENV>`, `BACKUP_DIR_<ENV>`
  - Optional (Mac pull): `AZ_SAS_DIR_URL_STG`, `AZ_SAS_DIR_URL_PROD`

### Windows quick setup

1) Create venv and install minimal deps for automate_refresh
   - pip install -r automate_refresh/requirements.txt

2) Ensure `shared_config/.env` has:
   - `APP_ENV=prod` (or pass `--env` at runtime)
   - `BACKUP_DIR_PROD=F:/mongodrive/backups/prod`

3) Run export (25% sample):
   - .\.venv\Scripts\python.exe -m automate_refresh.win.export_sample_json --env prod --collection Patients --fraction 0.25

Output:
- File at `F:/mongodrive/backups/prod/export/yyyymmdd_HHMMSS_export_Patients.json`
- Log at `logs/prod/automate_refresh/<ts>_export_Patients.log` with progress every 10k docs

### macOS quick setup

1) Create venv and install minimal deps
   - python3 -m venv .venv; source ./.venv/bin/activate
   - pip install -r automate_refresh/requirements.txt
   - pip install -e ./common_config

2) Ensure `shared_config/.env` includes local entries:
   - `MONGODB_URI_LOCL="mongodb://localhost:27017"`
   - `DATABASE_NAME_LOCL=UbiquityLOCAL`
   - `BACKUP_DIR_LOCL="~/Backups/local/export"`
   - Optional SAS:
     - `AZ_SAS_DIR_URL_PROD=https://.../backups/prod/export?...`
     - `AZ_SAS_DIR_URL_STG=https://.../backups/stg/export?...`

3) Import-only (file already local):
   - python -m automate_refresh.mac.import_latest --env local --collection Patients
   - Or override input dir: `--in_dir "/Users/<you>/Backups/local/export"`

4) Pull + import:
   - python -m automate_refresh.mac.run_mac_refresh --env local --collection Patients --sas_url prod
   - Notes:
     - Puller copies only `*_export_<collection>.json` and skips existing files (`--overwrite=false`)
     - Logs include full stack traces for troubleshooting

## Troubleshooting

- Importer can’t find file on Mac:
  - Ensure input dir points to the `export/` subfolder
  - Filenames must be strict: `yyyymmdd_HHMMSS_export_<collection>.json`
  - Check the log for the exact search directory

- Progress seems stalled on Windows export:
  - Logs print every 10,000 docs with rate and ETA
  - Large `$sample` may take time before writes begin; we log when `$sample` starts

- SAS pulls too many files:
  - Ensure SAS URL points to the `export/` directory
  - Puller uses `--include-pattern "*_export_<collection>.json"`

## Verification and troubleshooting

- Verify environment resolution: see "Verify configuration quickly" above.
- Logs live under the shared `logs/` root; most CLIs include the resolved log path at startup.
- If a project appears to write to a local `data/` or `logs/` folder, check if its README is marked "legacy" above; prefer running unified projects for new work.

## Testing and CI

We use pytest for tests and GitHub Actions to run the suite on every push and pull request.

Local testing:

```bash
# From repo root
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\Activate.ps1 on Windows PowerShell
pip install -e ./common_config
pip install -r requirements.txt
pip install pytest pytest-cov

# Run tests (unit only by default; integration tests are marked and can be excluded)
pytest -q --maxfail=1 --disable-warnings

# With coverage
pytest -q --maxfail=1 --disable-warnings --cov=common_config --cov-report=term-missing

# Run only integration tests (marked with @pytest.mark.integration)
pytest -q -m "integration"

# Exclude integration tests explicitly (run unit tests only)
pytest -q -m "not integration"
```

**Note on integration tests:**
- Integration tests avoid real DB by monkeypatching settings and connections.
- `conftest.py` auto-adds repo root and `common_config/src` to `sys.path` for all tests.
- Mark new integration tests with `@pytest.mark.integration` so they can be included/excluded via `-m` flag.

CI integration (already included):

- The workflow `.github/workflows/python-ci.yml` runs on every push/PR, sets up Python 3.11, installs dependencies,
  and executes pytest with coverage. It installs `common_config` editable and attempts to install subprojects if their
  requirements are present.
- Integration tests are marked with `@pytest.mark.integration` and are excluded by default in CI. Configure secrets and
  environment for real DB tests separately if needed, or prefer mocking for CI stability.

Conventions:

- Place tests under `tests/` at the repo root or inside a subproject’s tests directory.
- Avoid live DB in unit tests; use mocks or fakes. Reserve live DB checks for integration tests behind markers.
- Keep tests fast (< 1s each ideally) and deterministic.

## Documentation

### Repository-Level Documentation

Comprehensive guides for all developers:

- **[Repository Lessons Learned](docs/REPOSITORY_LESSONS_LEARNED.md)** ⭐
  - Project structure evolution and pitfalls
  - Shared configuration challenges and solutions
  - Path management best practices
  - Environment management guidelines
  - Migration guide for legacy projects

- **[MongoDB Validation Best Practices](docs/MONGODB_VALIDATION_BEST_PRACTICES.md)** ⭐⭐⭐
  - 20 reusable patterns for validation/migration projects
  - MongoDB query optimization strategies
  - Statistics reporting patterns
  - Code organization standards
  - Quick reference checklists

- **[Documentation Guide](docs/README_DOCUMENTATION.md)**
  - Navigation guide - which doc to read when
  - Quick start templates
  - Learning paths
  - Success criteria checklists

- **[Documentation Summary](docs/DOCUMENTATION_SUMMARY.md)**
  - Overview of all documentation
  - Key achievements and metrics
  - Quick reference templates

### Cleanup & Migration Documentation (October 2024)

Recent repository cleanup and migration to unified structure:

- **[Cleanup Summary](CLEANUP_SUMMARY_20251024.md)** ⭐
  - All cleanup actions performed
  - Project migrations to shared structure
  - Files archived and relocated
  - Verification steps

- **[Code Migration Complete](CODE_MIGRATION_COMPLETE.md)** ⭐
  - Code updates to use `common_config`
  - Testing instructions
  - Breaking changes and impact

- **[Migration Code Update Guide](MIGRATION_CODE_UPDATE_GUIDE.md)**
  - Detailed before/after examples
  - Step-by-step migration instructions
  - Troubleshooting tips

### Project-Specific Documentation

See individual project directories for detailed docs:

- `appointment_comparison/LESSONS_LEARNED.md` - Performance optimization journey (50 min → 12 min)
- `appointment_comparison/PERFORMANCE_OPTIMIZATIONS.md` - Specific optimization details
- `appointment_comparison/STATISTICS_IMPROVEMENT.md` - Reporting enhancements
- `patients_hcmid_validator/README.md` - High-volume CSV validator
- Other project READMEs for specific usage

### Quick Links

**Starting a new project?**  
→ Read: `docs/MONGODB_VALIDATION_BEST_PRACTICES.md`

**Facing performance issues?**  
→ Read: `appointment_comparison/PERFORMANCE_OPTIMIZATIONS.md` + `docs/MONGODB_VALIDATION_BEST_PRACTICES.md` Section 2

**Setting up for the first time?**  
→ Read: `docs/REPOSITORY_LESSONS_LEARNED.md` Sections 1-5

**Migrating a legacy project?**  
→ Read: `docs/REPOSITORY_LESSONS_LEARNED.md` Section 7

## Enhancements backlog

See `TODO.md` for planned additions like gzip compression, chunked export, and tuneable progress logging.

## patients_hcmid_validator (Overview)

High-volume validator that enriches an input CSV of patient identity rows by:

- Looking up each `HcmId` in the Mongo `Patients` (or configurable) collection using batched `$in` queries.
- Writing / ensuring two output columns: `Match Found` (`True`/`False`) and `Comments`.
- `Comments` contains either `HcmId Not Found`, comma‑separated mismatched field names (`FirstName,Dob`), or
  `<Field> missing on csv` if mandatory data absent.
- Mandatory comparison fields: `FirstName`, `LastName`, `Dob`, `Gender` (with `HcmId` as key only).
- Robust DOB normalization: supports ISO (`YYYY-MM-DD`), numeric (`M/D/YY`, `MM/DD/YYYY`, `M-D-YY`), and
  day‑month‑abbr (`3-Apr-29`, `17-Jun-1956`).
- Configurable two‑digit year handling via `--dob-century-strategy` (`senior` default maps 29 -> 1929) or
  `--dob-two-digit-pivot` with `pivot` strategy.
- Header canonicalization (case-insensitive, BOM strip, legacy `Mismatched Fields` -> `Comments`).
- Streaming batches (constant memory per batch) with retry/backoff and progress logging every N rows.
- Debug mode (`--debug`) logs Mongo queries and detailed mismatch diagnostics.
- JSON summary printed to stdout for automation pipelines.

### Quick start

Create / activate your venv and install editable dependencies (example):

```bash
pip install -e ./common_config -e ./patients_hcmid_validator
``

Run validation (default env suffix LOCL):

```bash
python -m patients_hcmid_validator \
  --input data/input/patients_hcmid_validator/sample.csv \
  --collection Patients
```

Key options:

```bash
python -m patients_hcmid_validator \
  --input data/input/patients_hcmid_validator/sample.csv \
  --collection Patients \
  --batch-size 2000 \
  --progress-every 5000 \
  --limit 100000 \
  --dry-run \
  --debug \
  --dob-century-strategy senior  # senior|pivot|force1900|force2000 \
  --dob-two-digit-pivot 30       # Used only when strategy=pivot
```

Generated output (when not dry-run):

- CSV: `data/output/patients_hcmid_validator/<timestamp>_output.csv`
- Log: `logs/patients_hcmid_validator/<timestamp>_app.log`
- Stdout JSON: `{"summary": {"total_rows":..., "matched":..., "not_found":..., "mismatched":...}}`

### Via meta CLI (optional)

If you maintain or install the meta wrapper, you can call:

```bash
ppro patients --input data/input/patients_hcmid_validator/sample.csv --collection Patients --debug
```

### Indexing guidance

Ensure (non‑unique) index on `HcmId` for efficient `$in` lookups:

```javascript
db.Patients.createIndex({ HcmId: 1 })
```

An optional script at `patients_hcmid_validator/indexes/create_patients_indexes.js` can also create an
additional compound index (toggle inside the script) if you measure benefit for combined field filters later.

### Detailed docs

See the dedicated README: `patients_hcmid_validator/README.md` for full feature list, option explanations, and roadmap.

