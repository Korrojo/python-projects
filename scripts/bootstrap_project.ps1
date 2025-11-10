# ==============================================================================
# Bootstrap Script for New Python Projects (PowerShell)
# ==============================================================================
# Automated setup for new projects in the unified repository structure
# Usage: .\scripts\bootstrap_project.ps1 <project-name> [environment]
#
# Example: .\scripts\bootstrap_project.ps1 db_collection_stats DEV
# ==============================================================================

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$ProjectName,

    [Parameter(Position=1)]
    [string]$Environment = "DEV"
)

$ErrorActionPreference = "Stop"

# Functions for colored output
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# ==============================================================================
# Configuration
# ==============================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

Write-Info "=========================================="
Write-Info "Project Bootstrap Automation"
Write-Info "=========================================="
Write-Info "Project Name: $ProjectName"
Write-Info "Environment: $Environment"
Write-Info "Repository Root: $RepoRoot"
Write-Info "=========================================="
Write-Host ""

Set-Location $RepoRoot

# ==============================================================================
# Step 1: Check Prerequisites
# ==============================================================================

Write-Info "Step 1/10: Checking prerequisites..."

if (-not (Test-Command python)) {
    Write-Error "Python is not installed or not in PATH"
    exit 1
}

if (-not (Test-Command pip)) {
    Write-Error "pip is not installed or not in PATH"
    exit 1
}

# Check Python version
$PythonVersion = (python --version 2>&1).ToString().Split()[1]
$VersionParts = $PythonVersion.Split('.')
$Major = [int]$VersionParts[0]
$Minor = [int]$VersionParts[1]

if (($Major -lt 3) -or (($Major -eq 3) -and ($Minor -lt 11))) {
    Write-Error "Python 3.11+ required. Found: $PythonVersion"
    exit 1
}

Write-Success "Prerequisites check passed (Python $PythonVersion)"
Write-Host ""

# ==============================================================================
# Step 2: Setup Virtual Environment
# ==============================================================================

Write-Info "Step 2/10: Setting up virtual environment..."

$VenvDir = Join-Path $RepoRoot ".venv311"

if (-not (Test-Path $VenvDir)) {
    Write-Info "Creating virtual environment at $VenvDir..."
    python -m venv $VenvDir
    Write-Success "Virtual environment created"
} else {
    Write-Success "Virtual environment already exists"
}

# Activate virtual environment
$ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
& $ActivateScript

Write-Success "Virtual environment activated"
Write-Host ""

# ==============================================================================
# Step 3: Install/Upgrade pip
# ==============================================================================

Write-Info "Step 3/10: Upgrading pip..."
python -m pip install --upgrade pip --quiet
Write-Success "pip upgraded"
Write-Host ""

# ==============================================================================
# Step 4: Install Repository Dependencies
# ==============================================================================

Write-Info "Step 4/10: Installing repository dependencies..."

$RequirementsFile = Join-Path $RepoRoot "requirements.txt"

if (Test-Path $RequirementsFile) {
    pip install -r $RequirementsFile --quiet
    Write-Success "Repository dependencies installed"
} else {
    Write-Warning "requirements.txt not found, skipping..."
}
Write-Host ""

# ==============================================================================
# Step 5: Install common_config
# ==============================================================================

Write-Info "Step 5/10: Installing common_config..."

$CommonConfigDir = Join-Path $RepoRoot "common_config"

if (Test-Path $CommonConfigDir) {
    pip install -e $CommonConfigDir --quiet
    Write-Success "common_config installed in editable mode"
} else {
    Write-Error "common_config directory not found!"
    exit 1
}
Write-Host ""

# ==============================================================================
# Step 6: Verify .env Configuration
# ==============================================================================

Write-Info "Step 6/10: Verifying environment configuration..."

$EnvFile = Join-Path $RepoRoot "shared_config\.env"

if (-not (Test-Path $EnvFile)) {
    Write-Warning ".env file not found at $EnvFile"
    $EnvExample = Join-Path $RepoRoot "shared_config\.env.example"

    if (Test-Path $EnvExample) {
        Write-Info "Creating .env from .env.example..."
        Copy-Item $EnvExample $EnvFile
        Write-Warning "Please edit $EnvFile with your actual credentials"
    } else {
        Write-Error "No .env.example found. Cannot proceed."
        exit 1
    }
}

# Check if environment-specific variables exist
$EnvContent = Get-Content $EnvFile -Raw

if ($EnvContent -notmatch "MONGODB_URI_$Environment") {
    Write-Warning "MONGODB_URI_$Environment not found in .env"
    Write-Warning "Please add: MONGODB_URI_$Environment=your_connection_string"
}

if ($EnvContent -notmatch "DATABASE_NAME_$Environment") {
    Write-Warning "DATABASE_NAME_$Environment not found in .env"
    Write-Warning "Please add: DATABASE_NAME_$Environment=your_database_name"
}

Write-Success "Environment configuration checked"
Write-Host ""

# ==============================================================================
# Step 7: Scaffold New Project
# ==============================================================================

Write-Info "Step 7/10: Scaffolding project structure..."

$ProjectDir = Join-Path $RepoRoot $ProjectName

if (Test-Path $ProjectDir) {
    Write-Error "Project directory already exists: $ProjectDir"
    $Response = Read-Host "Do you want to overwrite it? (yes/no)"

    if ($Response -ne "yes") {
        Write-Info "Aborting..."
        exit 1
    }
    $ForceFlag = "--force"
} else {
    $ForceFlag = ""
}

if ($ForceFlag) {
    python -m common_config init $ProjectName $ForceFlag
} else {
    python -m common_config init $ProjectName
}

Write-Success "Project scaffolded"
Write-Host ""

# ==============================================================================
# Step 8: Run Code Quality Checks
# ==============================================================================

Write-Info "Step 8/10: Running code quality checks..."

# Format code with Black
Write-Info "Formatting with Black..."
try {
    black $ProjectDir --line-length 120 --quiet
} catch {
    Write-Warning "Black formatting had warnings"
}

# Lint with Ruff
Write-Info "Linting with Ruff..."
try {
    ruff check $ProjectDir --fix --quiet
} catch {
    Write-Warning "Ruff found issues (auto-fixed where possible)"
}

Write-Success "Code quality checks completed"
Write-Host ""

# ==============================================================================
# Step 9: Run Tests
# ==============================================================================

Write-Info "Step 9/10: Running initial tests..."

$TestsDir = Join-Path $ProjectDir "tests"

if (Test-Path $TestsDir) {
    try {
        pytest $TestsDir -q --disable-warnings
    } catch {
        Write-Warning "Some tests failed (expected for initial scaffold)"
    }
    Write-Success "Tests executed"
} else {
    Write-Warning "No tests directory found, skipping..."
}
Write-Host ""

# ==============================================================================
# Step 10: Verify Project Setup
# ==============================================================================

Write-Info "Step 10/10: Verifying project setup..."

$ChecksPassed = $true

# Verify directory structure
@("src", "tests", "scripts", "temp") | ForEach-Object {
    $Dir = Join-Path $ProjectDir $_
    if (Test-Path $Dir) {
        Write-Success "Directory exists: $_/"
    } else {
        Write-Error "Missing directory: $_/"
        $ChecksPassed = $false
    }
}

# Verify centralized directories
@("data\input\$ProjectName", "data\output\$ProjectName", "logs\$ProjectName") | ForEach-Object {
    $Dir = Join-Path $RepoRoot $_
    if (Test-Path $Dir) {
        Write-Success "Centralized directory exists: $_/"
    } else {
        Write-Error "Missing centralized directory: $_/"
        $ChecksPassed = $false
    }
}

# Verify key files
@("run.py", "README.md", ".gitignore") | ForEach-Object {
    $File = Join-Path $ProjectDir $_
    if (Test-Path $File) {
        Write-Success "File exists: $_"
    } else {
        Write-Error "Missing file: $_"
        $ChecksPassed = $false
    }
}

Write-Host ""

# ==============================================================================
# Summary
# ==============================================================================

Write-Info "=========================================="
Write-Info "Bootstrap Complete!"
Write-Info "=========================================="
Write-Host ""

if ($ChecksPassed) {
    Write-Success "All verification checks passed ✓"
} else {
    Write-Warning "Some verification checks failed"
}

Write-Host ""
Write-Info "Project Location: $ProjectDir"
Write-Info "Data Input: $RepoRoot\data\input\$ProjectName\"
Write-Info "Data Output: $RepoRoot\data\output\$ProjectName\"
Write-Info "Logs: $RepoRoot\logs\$ProjectName\"
Write-Host ""

Write-Info "Next Steps:"
Write-Host "  1. Edit project code: code $ProjectDir\"
Write-Host "  2. Update .env if needed: code $EnvFile"
Write-Host "  3. Run project: python $ProjectDir\run.py"
Write-Host "  4. Run tests: pytest $ProjectDir\tests\ -v"
Write-Host "  5. Commit changes: git add $ProjectName && git commit -m 'feat: Add $ProjectName project'"
Write-Host ""

Write-Info "Quick Start Commands:"
Write-Host "  cd $ProjectDir"
Write-Host "  python run.py"
Write-Host ""

Write-Success "Happy coding! 🚀"
