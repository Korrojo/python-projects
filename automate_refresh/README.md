# Automate Refresh

A cross-platform (Windows/Mac) utility for exporting, transferring, and importing MongoDB collections between
environments (e.g., production to local) with environment-based configuration and robust logging.

______________________________________________________________________

## Common Project Overview

- **Purpose:** Automate the refresh of MongoDB collections (such as Users) from one environment to another.
- **Supported Platforms:** Windows and Mac (distinct workflows in `win/` and `mac/`)
- **Configuration:** All environment and connection details are managed via `.env` and `shared_config/.env`.
- **Logging:** Centralized, configurable logging for all operations.
- **Export Format:** JSON (compressed to ZIP for transfer)
- **Error Handling:** Skips problematic records during import/export.

### Prerequisites

- Python 3.11+ (venv recommended)
- All dependencies installed via `requirements.txt`
- Properly configured `.env` and `shared_config/.env` files

### Environment Variables

- `APP_ENV` (e.g., `prod`, `dev`, `locl`, etc.)
- `MONGODB_URI_<ENV>` and `DATABASE_NAME_<ENV>`
- `BACKUP_DIR_<ENV>` and `LOG_DIR_<ENV>`

______________________________________________________________________

## Windows Workflow (`win/`)

### Main Scripts

- `modules/exporter.py`: Exports a collection from MongoDB to a compressed JSON zip file.
- `modules/config_loader.py`: Loads environment and path configuration.
- `export_sample_json.py`: Example/sample export script.

### Typical Usage

1. **Activate venv and install dependencies:**

   ```powershell
   .venv311\Scripts\activate
   pip install -r requirements.txt
   ```

1. **Set environment (if not in .env):**

   ```powershell
   $env:APP_ENV="prod"
   ```

1. **Run export script:**

   ```powershell
   python -m automate_refresh.win.modules.exporter
   ```

   - Output: Zipped JSON file in the backup directory (see logs for exact path)
   - Log: Log file in the logs directory

### Export/Backup/Log Directories

- Controlled by `BACKUP_DIR_<ENV>` and `LOG_DIR_<ENV>` in `.env`/`shared_config/.env`.
- Example: `BACKUP_DIR_PROD=F:/mongodrive/backups/prod`

______________________________________________________________________

## Mac Workflow (`mac/`)

### Main Scripts

- `modules/importer.py`: Imports a collection from a JSON (or zipped JSON) file into MongoDB.
- `modules/config_loader.py`: Loads environment and path configuration.
- `run_mac_refresh.py`: Orchestrates the refresh process for Mac.

### Typical Usage

1. **Activate venv and install dependencies:**

   ```bash
   source .venv311/bin/activate
   pip install -r requirements.txt
   ```

1. **Set environment (if not in .env):**

   ```bash
   export APP_ENV=locl
   ```

1. **Run import script:**

   ```bash
   python -m automate_refresh.mac.modules.importer
   ```

   - Input: Zipped JSON file from Windows export
   - Log: Log file in the logs directory

### Import/Backup/Log Directories

- Controlled by `BACKUP_DIR_<ENV>` and `LOG_DIR_<ENV>` in `.env`/`shared_config/.env`.
- Example: `BACKUP_DIR_LOCL=~/Backups/local/export`

______________________________________________________________________

## Q&A and Policy (applies to both platforms)

- **MongoDB Connection:**
  - Connection strings for all environments are in `.env`/`shared_config/.env`.
  - Authentication is handled via these files.
- **Data Volume:**
  - Handles large collections (tested with 1GB+).
- **Schema:**
  - Assumes identical schema between environments.
- **Refresh Policy:**
  - Local collection is dropped and fully replaced on import.
- **Export Format:**
  - JSON, zipped for transfer.
- **Error Handling:**
  - Skips problematic records.
- **Logging:**
  - Uses existing logging configuration; no changes required.
- **Dependencies:**
  - Install with `pip install -r requirements.txt`.
- **Windows/Mac Constraints:**
  - No special constraints; paths are configurable.

______________________________________________________________________

## Troubleshooting

- Check the log files for errors and export/import paths.
- Ensure `APP_ENV` is set correctly for your operation.
- Confirm backup and log directories exist and are writable.

______________________________________________________________________

## Contribution & Maintenance

- Update this README if workflows or configuration change.
- Keep Q&A and policy sections up to date for onboarding and audit.
