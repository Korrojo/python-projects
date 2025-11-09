# Activation script for Python 3.11 virtual environment
# Usage: .\activate-venv-3.11.ps1

Write-Host "Activating Python 3.11 virtual environment..." -ForegroundColor Green

# Activate the virtual environment
& .\venv-3.11\Scripts\Activate.ps1

# Display Python version
Write-Host "`nPython version:" -ForegroundColor Cyan
python --version

Write-Host "`nEnvironment activated!" -ForegroundColor Green
Write-Host "Location: $(Get-Location)\venv-3.11" -ForegroundColor Yellow
Write-Host "`nInstalled packages: $(pip list --format=freeze | Measure-Object -Line | Select-Object -ExpandProperty Lines)" -ForegroundColor Yellow
Write-Host "`nTo deactivate, run: deactivate`n" -ForegroundColor Yellow
