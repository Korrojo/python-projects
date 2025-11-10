<#
.SYNOPSIS
    MongoDB Collection Backup Script (PowerShell)

.DESCRIPTION
    Backs up a MongoDB collection with timestamp naming convention.
    Integrates with shared_config environment presets.

.PARAMETER Env
    Environment (LOCL, DEV, STG, PROD, etc.)

.PARAMETER Collection
    Collection name to backup

.PARAMETER Db
    Database name override

.PARAMETER OutputDir
    Output directory (default: backup/)

.PARAMETER Compress
    Enable compression (gzip)

.EXAMPLE
    .\scripts\backup_collection.ps1 -Env LOCL -Collection Patients

.EXAMPLE
    .\scripts\backup_collection.ps1 -Env DEV -Db devdb -Collection Patients -Compress

.EXAMPLE
    .\scripts\backup_collection.ps1 -Env LOCL -Collection Patients -OutputDir "C:\backups"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$Env,

    [Parameter(Mandatory=$true)]
    [string]$Collection,

    [Parameter(Mandatory=$false)]
    [string]$Db,

    [Parameter(Mandatory=$false)]
    [string]$OutputDir = "backup",

    [Parameter(Mandatory=$false)]
    [switch]$Compress
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Timestamp for backup
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Setup logging
$LogDir = "logs\backup"
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

# Setup log file
$script:LogFile = "$LogDir\${Timestamp}_backup_${Collection}.log"

# Header
Write-Host "======================================================================"
Write-Host "MongoDB Collection Backup"
Write-Host "======================================================================"
Write-Log "Environment: $Env" -Level INFO
Write-Log "Collection: $Collection" -Level INFO
Write-Log "Timestamp: $Timestamp" -Level INFO
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

Write-Log "Database: $Database" -Level INFO

# Extract and mask URI
if ($MongoDbUri -match '^([^:]+://)([^@]+@)?(.+)$') {
    $Protocol = $matches[1]
    $Host = ($matches[3] -split '/')[0]
    Write-Log "URI: ${Protocol}***:***@${Host}" -Level INFO
} else {
    Write-Log "URI: [REDACTED]" -Level INFO
}
Write-Host ""

# Create backup directory with timestamp
$BackupDir = Join-Path $OutputDir "${Timestamp}_${Database}_${Collection}"
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

Write-Log "Backup directory: $BackupDir" -Level INFO
Write-Host ""

# Build mongodump command
$MongoDumpArgs = @(
    "--uri=`"$MongoDbUri`""
    "--db=`"$Database`""
    "--collection=`"$Collection`""
    "--out=`"$BackupDir`""
)

if ($Compress) {
    $MongoDumpArgs += "--gzip"
    Write-Log "Compression: Enabled" -Level INFO
}

# Execute backup
Write-Log "Starting backup..." -Level INFO
Write-Host ""

$StartTime = Get-Date

try {
    $MongoDumpCmd = "mongodump $($MongoDumpArgs -join ' ')"
    Invoke-Expression $MongoDumpCmd

    $EndTime = Get-Date
    $Duration = ($EndTime - $StartTime).TotalSeconds

    Write-Host ""
    Write-Log "Backup completed successfully!" -Level SUCCESS
    Write-Log "Duration: $([math]::Round($Duration, 2))s" -Level INFO

    # Show backup size
    $BackupSize = (Get-ChildItem -Path $BackupDir -Recurse | Measure-Object -Property Length -Sum).Sum
    $BackupSizeMB = [math]::Round($BackupSize / 1MB, 2)
    Write-Log "Backup size: ${BackupSizeMB} MB" -Level INFO

    Write-Host ""
    Write-Host "======================================================================"
    Write-Log "Backup saved to: $BackupDir" -Level SUCCESS
    Write-Host "======================================================================"

    exit 0
} catch {
    Write-Log "Backup failed: $($_.Exception.Message)" -Level ERROR
    exit 1
}
