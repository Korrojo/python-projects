# Automated virtual environment activator for PowerShell
# Detects available venv and activates it

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Find available virtual environments
$venvDirs = @()
$venvVersions = @()

Get-ChildItem -Directory -Filter ".venv*" | ForEach-Object {
    $venvDir = $_.Name
    $pythonExe = Join-Path $venvDir "Scripts\python.exe"

    if (Test-Path $pythonExe) {
        $venvDirs += $venvDir

        # Get Python version
        $version = & $pythonExe --version 2>&1 | Select-String -Pattern '\d+\.\d+\.\d+' | ForEach-Object { $_.Matches.Value }
        if (-not $version) { $version = "unknown" }
        $venvVersions += $version
    }
}

# Check if any venv found
if ($venvDirs.Count -eq 0) {
    Write-ColorOutput Red "ERROR: No virtual environments found!"
    Write-Output ""
    Write-Output "Create one first using:"
    Write-ColorOutput Blue "  .\install_venv.ps1"
    exit 1
}

# If only one venv, use it
if ($venvDirs.Count -eq 1) {
    $selectedVenv = $venvDirs[0]
    $selectedVersion = $venvVersions[0]
}
else {
    # Multiple venvs found, prompt for selection
    Write-ColorOutput Yellow "Multiple virtual environments found:"
    Write-Output ""

    for ($i = 0; $i -lt $venvDirs.Count; $i++) {
        $idx = $i + 1
        $venv = $venvDirs[$i]
        $version = $venvVersions[$i]
        Write-Output "  $idx) $venv (Python $version)"
    }

    Write-Output ""

    do {
        $selection = Read-Host "Select virtual environment (1-$($venvDirs.Count)) [default: 1]"
        if ([string]::IsNullOrWhiteSpace($selection)) { $selection = "1" }

        $selectionInt = 0
        $valid = [int]::TryParse($selection, [ref]$selectionInt) -and
        $selectionInt -ge 1 -and
        $selectionInt -le $venvDirs.Count

        if (-not $valid) {
            Write-ColorOutput Red "Invalid selection. Please enter a number between 1 and $($venvDirs.Count)"
        }
    } while (-not $valid)

    $idx = $selectionInt - 1
    $selectedVenv = $venvDirs[$idx]
    $selectedVersion = $venvVersions[$idx]
}

# Activate the selected venv
Write-Output ""
Write-ColorOutput Green "Activating: $selectedVenv (Python $selectedVersion)"
Write-Output ""

$activateScript = Join-Path $selectedVenv "Scripts\Activate.ps1"

if (-not (Test-Path $activateScript)) {
    Write-ColorOutput Red "ERROR: Activation script not found: $activateScript"
    exit 1
}

# Execute the activation script
& $activateScript

# Verify activation
if (-not $env:VIRTUAL_ENV) {
    Write-ColorOutput Red "ERROR: Failed to activate virtual environment"
    exit 1
}

Write-ColorOutput Green "✓ Virtual environment activated!"
Write-Output ""
Write-Output "Python version: $(python --version)"
Write-Output "Python path: $(Get-Command python | Select-Object -ExpandProperty Source)"
Write-Output ""
Write-ColorOutput Yellow "To deactivate, run: deactivate"
