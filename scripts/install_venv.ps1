# Automated virtual environment installer for Windows PowerShell
# Detects Python installations and creates venv with selected version

$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Green "=== Python Virtual Environment Installer ==="
Write-Output ""

Write-ColorOutput Blue "Detected OS: Windows (PowerShell)"
Write-Output ""

# Function to get Python version from executable
function Get-PythonVersion {
    param([string]$PyCmd)

    try {
        $version = & $PyCmd --version 2>&1 | Select-String -Pattern '\d+\.\d+\.\d+' | ForEach-Object { $_.Matches.Value }
        return $version
    }
    catch {
        return $null
    }
}

# Find all Python installations
$pythonVersions = @()
$pythonPaths = @()

Write-ColorOutput Yellow "Searching for Python installations..."
Write-Output ""

# Check py launcher
if (Get-Command py -ErrorAction SilentlyContinue) {
    Write-ColorOutput Green "✓ Found py launcher (Windows)"

    # Get list of available versions
    $pyList = & py -0 2>&1

    foreach ($line in $pyList) {
        if ($line -match '-(\d+\.\d+)') {
            $majorMinor = $matches[1]
            $version = Get-PythonVersion "py -$majorMinor"

            if ($version) {
                $pythonVersions += $version
                $pythonPaths += "py -$majorMinor"
                Write-Output "  Found: Python $version (py -$majorMinor)"
            }
        }
    }
}

# Check common installation paths
$commonPaths = @(
    "C:\Python3*\python.exe",
    "C:\Program Files\Python3*\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe"
)

foreach ($pathPattern in $commonPaths) {
    $paths = Get-ChildItem -Path $pathPattern -ErrorAction SilentlyContinue

    foreach ($path in $paths) {
        $version = Get-PythonVersion $path.FullName

        if ($version -and $pythonVersions -notcontains $version) {
            $pythonVersions += $version
            $pythonPaths += $path.FullName
            Write-Output "  Found: Python $version ($($path.FullName))"
        }
    }
}

# Check python in PATH
if (Get-Command python -ErrorAction SilentlyContinue) {
    $version = Get-PythonVersion "python"
    if ($version -and $pythonVersions -notcontains $version) {
        $pythonVersions += $version
        $pythonPaths += "python"
        Write-Output "  Found: Python $version (python in PATH)"
    }
}

Write-Output ""

# Check if any Python found
if ($pythonVersions.Count -eq 0) {
    Write-ColorOutput Red "ERROR: No Python installations found!"
    Write-Output ""
    Write-Output "Please install Python 3.11+ from:"
    Write-Output "  https://www.python.org/downloads/windows/"
    Write-Output ""
    Write-Output "After installation, ensure Python is in your PATH."
    exit 1
}

# Display found versions and prompt for selection
Write-ColorOutput Green "Found $($pythonVersions.Count) Python installation(s):"
Write-Output ""

for ($i = 0; $i -lt $pythonVersions.Count; $i++) {
    $idx = $i + 1
    $version = $pythonVersions[$i]
    $path = $pythonPaths[$i]

    # Highlight Python 3.11 (recommended)
    if ($version -like "3.11.*") {
        Write-Host "  $idx) Python " -NoNewline
        Write-ColorOutput Green "$version (RECOMMENDED)"
        Write-Output "     $path"
    }
    else {
        Write-Output "  $idx) Python $version - $path"
    }
}

Write-Output ""

# Prompt for selection
do {
    $selection = Read-Host "Select Python version (1-$($pythonVersions.Count)) [default: 1]"
    if ([string]::IsNullOrWhiteSpace($selection)) { $selection = "1" }

    $selectionInt = 0
    $valid = [int]::TryParse($selection, [ref]$selectionInt) -and
    $selectionInt -ge 1 -and
    $selectionInt -le $pythonVersions.Count

    if (-not $valid) {
        Write-ColorOutput Red "Invalid selection. Please enter a number between 1 and $($pythonVersions.Count)"
    }
} while (-not $valid)

$idx = $selectionInt - 1
$selectedVersion = $pythonVersions[$idx]
$selectedPath = $pythonPaths[$idx]

Write-Output ""
Write-ColorOutput Green "Selected: Python $selectedVersion"
Write-ColorOutput Blue "Path: $selectedPath"
Write-Output ""

# Determine venv directory name
$venvVersion = $selectedVersion -replace '^(\d+\.\d+).*', '$1' -replace '\.', ''
$venvDir = ".venv$venvVersion"

# Warn if different version already exists
if (Test-Path $venvDir) {
    Write-ColorOutput Yellow "Warning: Virtual environment '$venvDir' already exists!"
    $confirm = Read-Host "Do you want to remove it and recreate? (y/N)"

    if ($confirm -eq 'y' -or $confirm -eq 'Y') {
        Write-Output "Removing existing venv..."
        Remove-Item -Recurse -Force $venvDir
    }
    else {
        Write-Output "Installation cancelled."
        exit 0
    }
}

# Create virtual environment
Write-Output ""
Write-ColorOutput Yellow "Creating virtual environment: $venvDir"

if ($selectedPath -like "py -*") {
    # Use py launcher
    $pyCmd = $selectedPath -split ' '
    & $pyCmd[0] $pyCmd[1] -m venv $venvDir
}
else {
    # Direct Python path
    & $selectedPath -m venv $venvDir
}

if (-not (Test-Path $venvDir)) {
    Write-ColorOutput Red "ERROR: Failed to create virtual environment!"
    exit 1
}

Write-ColorOutput Green "✓ Virtual environment created successfully!"
Write-Output ""

# Verify venv Python version
Write-ColorOutput Yellow "Verifying virtual environment..."
$venvPython = "$venvDir\Scripts\python.exe"
$venvVersionCheck = & $venvPython --version 2>&1 | Select-String -Pattern '\d+\.\d+\.\d+' | ForEach-Object { $_.Matches.Value }

Write-ColorOutput Green "✓ Virtual environment Python version: $venvVersionCheck"

# Check if version matches
if ($venvVersionCheck -eq $selectedVersion) {
    Write-ColorOutput Green "✓ Version verified!"
}
else {
    Write-ColorOutput Yellow "⚠ Warning: venv version ($venvVersionCheck) differs from selected ($selectedVersion)"
}

Write-Output ""
Write-ColorOutput Green "=== Installation Complete! ==="
Write-Output ""
Write-Output "Virtual environment created at: $venvDir"
Write-Output ""
Write-Output "Next steps:"
Write-Output ""
Write-Output "1) Activate the virtual environment:"
Write-ColorOutput Blue "   .\activate_venv.ps1"
Write-Output "   Or manually: $venvDir\Scripts\Activate.ps1"
Write-Output ""
Write-Output "2) Install dependencies:"
Write-ColorOutput Blue "   pip install -r requirements.txt"
Write-ColorOutput Yellow "   (This automatically installs common_config in editable mode)"
Write-Output ""
Write-Output "3) Verify installation:"
Write-ColorOutput Blue "   python --version"
Write-ColorOutput Blue "   pip show common-config"
