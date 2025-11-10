# MongoDB Backup/Restore Scripts

Cross-platform scripts for backing up and restoring MongoDB collections with environment support.

## Available Scripts

| Script                   | Platform             | Purpose                    |
| ------------------------ | -------------------- | -------------------------- |
| `backup_collection.sh`   | Bash (Mac/Linux)     | Backup MongoDB collection  |
| `backup_collection.ps1`  | PowerShell (Windows) | Backup MongoDB collection  |
| `restore_collection.sh`  | Bash (Mac/Linux)     | Restore MongoDB collection |
| `restore_collection.ps1` | PowerShell (Windows) | Restore MongoDB collection |

## Features

✅ Environment-based configuration (LOCL, DEV, STG, PROD) ✅ Loads credentials from `shared_config/.env` ✅ Timestamped
backup directories ✅ Compression support (gzip) ✅ Detailed logging with timestamps ✅ URI masking for security ✅
Confirmation prompts for restore ✅ Cross-platform (Bash + PowerShell)

## Prerequisites

### All Platforms

- MongoDB Database Tools (`mongodump`, `mongorestore`)
- Configuration in `shared_config/.env` with environment variables:

```bash
# Example shared_config/.env
MONGODB_URI_LOCL=mongodb://localhost:27017
DATABASE_NAME_LOCL=localdb

MONGODB_URI_DEV=mongodb://dev.example.com:27017
DATABASE_NAME_DEV=devdb
```

### Installation

**MongoDB Database Tools:**

- **Mac (Homebrew):** `brew install mongodb-database-tools`
- **Windows (Chocolatey):** `choco install mongodb-database-tools`
- **Manual:** <https://www.mongodb.com/try/download/database-tools>

## Backup Collection

### Bash (Mac/Linux)

```bash
# Basic backup
./scripts/backup_collection.sh --env LOCL --collection Patients

# With compression
./scripts/backup_collection.sh --env DEV --collection Patients --compress

# Custom database and output directory
./scripts/backup_collection.sh --env LOCL --db mydb --collection Patients --output-dir /backups

# Show help
./scripts/backup_collection.sh --help
```

### PowerShell (Windows)

```powershell
# Basic backup
.\scripts\backup_collection.ps1 -Env LOCL -Collection Patients

# With compression
.\scripts\backup_collection.ps1 -Env DEV -Collection Patients -Compress

# Custom database and output directory
.\scripts\backup_collection.ps1 -Env LOCL -Db mydb -Collection Patients -OutputDir "C:\backups"

# Show help
Get-Help .\scripts\backup_collection.ps1 -Full
```

### Backup Output

```
backup/
└── 20251109_143022_localdb_Patients/
    └── localdb/
        ├── Patients.bson
        ├── Patients.metadata.json
        └── Patients.bson.gz (if compressed)
```

## Restore Collection

### Bash (Mac/Linux)

```bash
# Basic restore
./scripts/restore_collection.sh --env DEV --backup-dir backup/20251109_143022_localdb_Patients

# With drop (drops existing collection first)
./scripts/restore_collection.sh --env LOCL --backup-dir backup/... --drop

# Custom target database
./scripts/restore_collection.sh --env DEV --db mydb-masked --backup-dir backup/...

# Show help
./scripts/restore_collection.sh --help
```

### PowerShell (Windows)

```powershell
# Basic restore
.\scripts\restore_collection.ps1 -Env DEV -BackupDir "backup\20251109_143022_localdb_Patients"

# With drop (drops existing collection first)
.\scripts\restore_collection.ps1 -Env LOCL -BackupDir "backup\..." -Drop

# Custom target database
.\scripts\restore_collection.ps1 -Env DEV -Db mydb-masked -BackupDir "backup\..."

# Show help
Get-Help .\scripts\restore_collection.ps1 -Full
```

### Restore Behavior

- **Source database** is auto-detected from backup directory structure
- **Target database** is determined by environment config or `-Db` parameter
- Collections are **remapped** to target database automatically
- **Confirmation prompt** prevents accidental overwrites
- Supports both **uncompressed** and **gzipped** backups

## Parameters

### Backup Scripts

| Parameter        | Bash Flag      | PowerShell    | Required | Description                          |
| ---------------- | -------------- | ------------- | -------- | ------------------------------------ |
| Environment      | `--env`        | `-Env`        | ✅       | Target environment (LOCL, DEV, etc.) |
| Collection       | `--collection` | `-Collection` | ✅       | Collection name                      |
| Database         | `--db`         | `-Db`         | ❌       | Database name override               |
| Output Directory | `--output-dir` | `-OutputDir`  | ❌       | Backup output directory              |
| Compress         | `--compress`   | `-Compress`   | ❌       | Enable gzip compression              |

### Restore Scripts

| Parameter        | Bash Flag      | PowerShell   | Required | Description                    |
| ---------------- | -------------- | ------------ | -------- | ------------------------------ |
| Environment      | `--env`        | `-Env`       | ✅       | Target environment             |
| Backup Directory | `--backup-dir` | `-BackupDir` | ✅       | Path to backup directory       |
| Database         | `--db`         | `-Db`        | ❌       | Database name override         |
| Drop             | `--drop`       | `-Drop`      | ❌       | Drop existing collection first |

## Logging

All operations are logged to timestamped files:

- **Backup logs:** `logs/backup/YYYYMMDD_HHMMSS_backup_CollectionName.log`
- **Restore logs:** `logs/restore/YYYYMMDD_HHMMSS_restore_CollectionName.log`

Log format: `YYYY-MM-DD HH:MM:SS | LEVEL | message`

## Example Workflow

### Backup from LOCL, Restore to DEV

**Step 1: Backup from local environment**

```bash
# Bash
./scripts/backup_collection.sh --env LOCL --collection Patients --compress

# PowerShell
.\scripts\backup_collection.ps1 -Env LOCL -Collection Patients -Compress
```

Output: `backup/20251109_143022_localdb_Patients/`

**Step 2: Restore to dev environment**

```bash
# Bash
./scripts/restore_collection.sh --env DEV --backup-dir backup/20251109_143022_localdb_Patients

# PowerShell
.\scripts\restore_collection.ps1 -Env DEV -BackupDir "backup\20251109_143022_localdb_Patients"
```

### Migrate Between Databases

```bash
# Backup from source
./scripts/backup_collection.sh --env PROD --collection Patients --compress

# Restore to different database in same environment
./scripts/restore_collection.sh --env PROD --db prod-archive --backup-dir backup/... --drop
```

## Security Notes

- ✅ MongoDB URIs are **masked in logs** (`mongodb://***:***@host`)
- ✅ Credentials loaded from `shared_config/.env` (not in scripts)
- ✅ Restore operations require **confirmation prompt**
- ⚠️ Use `--drop` carefully - it **permanently deletes** existing data
- ⚠️ Keep `shared_config/.env` out of version control (`.gitignore`)

## Troubleshooting

### mongodump/mongorestore not found

**Install MongoDB Database Tools:**

- Mac: `brew install mongodb-database-tools`
- Windows: `choco install mongodb-database-tools`

### Environment not configured

**Error:** `MongoDB URI not configured for XXX environment`

**Solution:** Add to `shared_config/.env`:

```bash
MONGODB_URI_XXX=mongodb://...
DATABASE_NAME_XXX=yourdb
```

### Permission denied (PowerShell)

**Error:** `cannot be loaded because running scripts is disabled`

**Solution:** Enable script execution:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Backup directory not found

**Solution:** Use **relative** or **absolute** paths:

```bash
# Relative (from project root)
--backup-dir backup/20251109_143022_localdb_Patients

# Absolute
--backup-dir /full/path/to/backup/20251109_143022_localdb_Patients
```

## See Also

- [MongoDB Database Tools Documentation](https://www.mongodb.com/docs/database-tools/)
- [mongodump Reference](https://www.mongodb.com/docs/database-tools/mongodump/)
- [mongorestore Reference](https://www.mongodb.com/docs/database-tools/mongorestore/)
- [mongo_phi_masker README](../README.md)
