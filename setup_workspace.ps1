<#!
Unified dev environment bootstrap for python_v2 workspace (PowerShell).
- Creates a single venv at .venv under repo root
- Installs core dev tools + editable common_config
- Optionally installs project extras (pandas, openpyxl)
Run:
  powershell -ExecutionPolicy Bypass -File .\setup_workspace.ps1
!#>
param(
  [switch]$IncludeDataPkgs = $true,  # pandas/openpyxl
  [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Ok($msg) { Write-Host "[ OK ] $msg" -ForegroundColor Green }

# 1) Create venv
$venvPath = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venvPath)) {
  Write-Info "Creating virtual environment at $venvPath"
  & $PythonExe -m venv $venvPath
} else {
  Write-Info "Virtual environment already exists: $venvPath"
}

# 2) Activate venv for this session
$activate = Join-Path $venvPath "Scripts/Activate.ps1"
. $activate
Write-Ok "Virtual environment activated"

# 3) Upgrade pip + tools
python -m pip install --upgrade pip
python -m pip install black ruff pytest

# 4) Install editable common_config
$commonPath = Join-Path $PSScriptRoot "common_config"
if (Test-Path $commonPath) {
  Write-Info "Installing common_config (editable)"
  python -m pip install -e $commonPath
} else {
  Write-Warn "common_config folder not found at $commonPath"
}

# 5) Optionally install common data libs used across projects
if ($IncludeDataPkgs) {
  Write-Info "Installing common data packages (pandas, openpyxl, pymongo, python-dotenv)"
  python -m pip install pandas openpyxl pymongo python-dotenv pydantic pydantic-settings typer
}

Write-Ok "Setup complete. To activate later: .\\.venv\\Scripts\\Activate.ps1"
