# PowerShell Script to Run MongoDB PHI Masking in Background
# Usage: .\run_masking_job.ps1 -Collection "StaffAvailabilityHistory" -BatchSize 5000

param(
    [Parameter(Mandatory=$true)]
    [string]$Collection,

    [Parameter(Mandatory=$false)]
    [int]$BatchSize = 9000,  # Default from .env.phi

    [Parameter(Mandatory=$false)]
    [string]$ConfigFile = "config/config_rules/config_StaffAavailability.json",

    [Parameter(Mandatory=$false)]
    [string]$EnvFile = ".env.phi",

    [Parameter(Mandatory=$false)]
    [switch]$InSitu,

    [Parameter(Mandatory=$false)]
    [string]$LogDir = "logs/phi"
)

# Generate timestamp for log file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "$LogDir/${timestamp}_masking_${Collection}.log"

# Ensure log directory exists
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    Write-Host "Created log directory: $LogDir" -ForegroundColor Green
}

# Build command arguments
$arguments = @(
    "masking.py",
    "--config", $ConfigFile,
    "--env", $EnvFile,
    "--collection", $Collection,
    "--batch-size", $BatchSize
)

# Default to in-situ mode unless explicitly disabled
if ($InSitu -or -not $PSBoundParameters.ContainsKey('InSitu')) {
    $arguments += "--in-situ"
}

# Display command being executed
Write-Host "`n===================================" -ForegroundColor Cyan
Write-Host "Starting Masking Job" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "Collection:  $Collection" -ForegroundColor Yellow
Write-Host "Batch Size:  $BatchSize" -ForegroundColor Yellow
Write-Host "Config:      $ConfigFile" -ForegroundColor Yellow
Write-Host "Environment: $EnvFile" -ForegroundColor Yellow
Write-Host "Mode:        $(if($InSitu){'In-Situ'}else{'Source-to-Dest'})" -ForegroundColor Yellow
Write-Host "Log File:    $logFile" -ForegroundColor Yellow
Write-Host "===================================" -ForegroundColor Cyan

# Resolve full paths
$pythonExePath = Join-Path $PSScriptRoot "venv-3.11\Scripts\python.exe"
$fullLogFile = Join-Path $PSScriptRoot $logFile

# Start the job
$job = Start-Job -ScriptBlock {
    param($WorkDir, $PythonExe, $Arguments, $LogFile)

    Set-Location $WorkDir

    # Use cmd /c to properly capture output
    $outputFile = "${LogFile}"
    $errorFile = "${LogFile}.err"

    # Build the full command
    $argString = ($Arguments | ForEach-Object {
        if ($_ -match '\s') { "`"$_`"" } else { $_ }
    }) -join ' '

    $fullCommand = "& `"$PythonExe`" $argString > `"$outputFile`" 2> `"$errorFile`""

    $exitCode = 0
    try {
        Invoke-Expression $fullCommand
        $exitCode = $LASTEXITCODE
    } catch {
        $exitCode = 1
        $_.Exception.Message | Out-File -FilePath $errorFile -Append
    }

    return @{
        ExitCode = $exitCode
        LogFile = $LogFile
    }
} -ArgumentList $PSScriptRoot, $pythonExePath, $arguments, $fullLogFile

Write-Host "`nJob started with ID: $($job.Id)" -ForegroundColor Green
Write-Host "`nMonitoring commands:" -ForegroundColor Cyan
Write-Host "  Check job status:    Get-Job -Id $($job.Id)" -ForegroundColor White
Write-Host "  View job output:     Receive-Job -Id $($job.Id) -Keep" -ForegroundColor White
Write-Host "  Monitor log file:    Get-Content -Path '$logFile' -Tail 20 -Wait" -ForegroundColor White
Write-Host "  Stop job:            Stop-Job -Id $($job.Id)" -ForegroundColor White
Write-Host "  Remove job:          Remove-Job -Id $($job.Id)" -ForegroundColor White

Write-Host "`nJob Information:" -ForegroundColor Cyan
$job | Format-Table Id, Name, State, HasMoreData -AutoSize

# Optionally, wait for job to complete
$waitForCompletion = Read-Host "`nWait for job to complete? (y/N)"
if ($waitForCompletion -eq 'y' -or $waitForCompletion -eq 'Y') {
    Write-Host "Waiting for job to complete..." -ForegroundColor Yellow
    $job | Wait-Job | Out-Null

    $result = Receive-Job -Job $job
    Write-Host "`nJob completed with exit code: $($result.ExitCode)" -ForegroundColor $(if($result.ExitCode -eq 0){"Green"}else{"Red"})

    Write-Host "`nLog file location: $logFile" -ForegroundColor Cyan

    if (Test-Path "$logFile.err") {
        $errContent = Get-Content "$logFile.err"
        if ($errContent) {
            Write-Host "`nErrors found:" -ForegroundColor Red
            Write-Host $errContent -ForegroundColor Red
        }
    }

    Remove-Job -Job $job
} else {
    Write-Host "`nJob is running in background. Use 'Get-Job' to check status." -ForegroundColor Green
}
