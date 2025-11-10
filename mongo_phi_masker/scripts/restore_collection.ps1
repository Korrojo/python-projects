<#
.SYNOPSIS
    MongoDB Collection Restore Script (PowerShell)

.DESCRIPTION
    Restores a MongoDB collection from backup with environment support.
    Integrates with shared_config environment presets.

.PARAMETER Env
    Target environment (LOCL, DEV, STG, PROD, etc.)

.PARAMETER BackupDir
    Backup directory to restore from

.PARAMETER Db
    Database name override

.PARAMETER Drop
    Drop collection before restoring

.EXAMPLE
    .\scripts\restore_collection.ps1 -Env DEV -BackupDir "backup\20251105_120000_localdb_Patients"

.EXAMPLE
    .\scripts\restore_collection.ps1 -Env LOCL -Db localdb-masked -BackupDir "backup\..." -Drop

.EXAMPLE
    .\scripts\restore_collection.ps1 -Env DEV -BackupDir "backup\20251105_120000_devdb_Patients"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$Env,

    [Parameter(Mandatory=$true)]
    [string]$BackupDir,

    [Parameter(Mandatory=$false)]
    [string]$Db,

    [Parameter(Mandatory=$false)]
    [switch]$Drop
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Timestamp for logging
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Setup logging
$LogDir = "logs\restore"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Logging functions
function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "SUCCESS", "ERROR", "WARNING")]
        [string]$Level = "INFO"
    )

    $TimeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $ColorMap = @{
        "INFO" = "Cyan"
        "SUCCESS" = "Green"
        "ERROR" = "Red"
        "WARNING" = "Yellow"
    }

    $LogMessage = "$TimeStamp | $Level | $Message"
    Write-Host $LogMessage -ForegroundColor $ColorMap[$Level]

    # Write to log file (without colors)
    if ($script:LogFile) {
        Add-Content -Path $script:LogFile -Value $LogMessage
    }
}

# Validate backup directory exists
if (-not (Test-Path $BackupDir)) {
    Write-Host "ERROR: Backup directory not found: $BackupDir" -ForegroundColor Red
    exit 1
}

# Extract collection name from backup directory
# Backup dir format: YYYYMMDD_HHMMSS_database_collection
$BackupDirName = Split-Path -Leaf $BackupDir
$CollectionName = ($BackupDirName -split '_')[-1]

# Setup log file
$script:LogFile = "$LogDir\${Timestamp}_restore_${CollectionName}.log"

# Header
Write-Host "======================================================================"
Write-Host "MongoDB Collection Restore"
Write-Host "======================================================================"
Write-Log "Environment: $Env" -Level INFO
Write-Log "Backup directory: $BackupDir" -Level INFO
Write-Log "Log file: $script:LogFile" -Level INFO
Write-Host ""

# Load environment configuration from shared_config/.env
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$SharedConfig = Join-Path (Split-Path -Parent $ProjectRoot) "shared_config\.env"

if (-not (Test-Path $SharedConfig)) {
    Write-Log "shared_config\.env not found at $SharedConfig" -Level ERROR
    exit 1
}

# Parse .env file
$EnvVars = @{}
Get-Content $SharedConfig | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)\s*=\s*(.+)\s*$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim().Trim('"').Trim("'")
        $EnvVars[$key] = $value
    }
}

# Get MongoDB URI and database from environment
$UriVar = "MONGODB_URI_$Env"
$DbVar = "DATABASE_NAME_$Env"

$MongoDbUri = $EnvVars[$UriVar]
$Database = if ($Db) { $Db } else { $EnvVars[$DbVar] }

if (-not $MongoDbUri) {
    Write-Log "MongoDB URI not configured for $Env environment" -Level ERROR
    Write-Log "Please set $UriVar in shared_config\.env" -Level ERROR
    exit 1
}

if (-not $Database) {
    Write-Log "Database name not configured for $Env environment" -Level ERROR
    Write-Log "Please set $DbVar in shared_config\.env or use -Db parameter" -Level ERROR
    exit 1
}

Write-Log "Target database: $Database" -Level INFO

# Extract and mask URI
if ($MongoDbUri -match '^([^:]+://)([^@]+@)?(.+)$') {
    $Protocol = $matches[1]
    $Host = ($matches[3] -split '/')[0]
    Write-Log "URI: ${Protocol}***:***@${Host}" -Level INFO
} else {
    Write-Log "URI: [REDACTED]" -Level INFO
}
Write-Host ""

# Detect source database from backup directory structure
# Backup dir structure: backup_dir/source_database/collection.bson
$SourceDbDir = Get-ChildItem -Path $BackupDir -Directory | Select-Object -First 1
if (-not $SourceDbDir) {
    Write-Log "Cannot detect source database from backup directory" -Level ERROR
    exit 1
}

$SourceDb = $SourceDbDir.Name
Write-Log "Source database (from backup): $SourceDb" -Level INFO

# List collections in backup
$Collections = Get-ChildItem -Path "$BackupDir\$SourceDb" -Filter "*.bson*" |
    ForEach-Object { $_.Name -replace '\.bson.*$', '' } |
    Select-Object -Unique |
    Sort-Object

$CollectionCount = ($Collections | Measure-Object).Count

Write-Log "Collections in backup: $CollectionCount" -Level INFO
foreach ($coll in $Collections) {
    Write-Log "  - $coll" -Level INFO
}
Write-Host ""

# Build mongorestore command
$MongoRestoreArgs = @(
    "--uri=`"$MongoDbUri`""
)

if ($Drop) {
    $MongoRestoreArgs += "--drop"
    Write-Log "Drop mode: Existing collection(s) will be dropped" -Level WARNING
}

# Use --nsInclude for modern MongoDB restore
$MongoRestoreArgs += "--nsInclude=`"${SourceDb}.${CollectionName}`""
$MongoRestoreArgs += "--nsFrom=`"${SourceDb}.${CollectionName}`""
$MongoRestoreArgs += "--nsTo=`"${Database}.${CollectionName}`""
$MongoRestoreArgs += "--dir=`"$BackupDir`""

# Check for gzip compression
$CompressedFiles = Get-ChildItem -Path "$BackupDir\$SourceDb" -Filter "*.bson.gz"
if ($CompressedFiles) {
    $MongoRestoreArgs += "--gzip"
    Write-Log "Compression detected: Enabled" -Level INFO
}

# Confirmation prompt
Write-Host ""
Write-Log "About to restore backup to: $Env / $Database" -Level WARNING
$Confirmation = Read-Host "Continue? (y/N)"
if ($Confirmation -notmatch '^[Yy]$') {
    Write-Log "Restore cancelled" -Level INFO
    exit 0
}

# Execute restore
Write-Log "Starting restore..." -Level INFO
Write-Host ""

$StartTime = Get-Date

try {
    $MongoRestoreCmd = "mongorestore $($MongoRestoreArgs -join ' ')"
    Invoke-Expression $MongoRestoreCmd

    $EndTime = Get-Date
    $Duration = ($EndTime - $StartTime).TotalSeconds

    Write-Host ""
    Write-Log "Restore completed successfully!" -Level SUCCESS
    Write-Log "Duration: $([math]::Round($Duration, 2))s" -Level INFO

    Write-Host ""
    Write-Host "======================================================================"
    Write-Log "Data restored to: $Env / $Database" -Level SUCCESS
    Write-Host "======================================================================"

    exit 0
} catch {
    Write-Log "Restore failed: $($_.Exception.Message)" -Level ERROR
    exit 1
}
