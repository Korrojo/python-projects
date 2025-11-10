@echo off
REM Windows batch wrapper for Patient Data Extraction
REM This script sets up the environment and runs the extraction

setlocal enabledelayedexpansion

REM Get the directory where this batch file is located
set PROJECT_DIR=%~dp0
set COMMON_FRAMEWORK_DIR=%PROJECT_DIR%..\common_project

REM Change to project directory
cd /d "%PROJECT_DIR%"

REM Check if common framework exists
if not exist "%COMMON_FRAMEWORK_DIR%\src" (
    echo Error: Common framework not found at %COMMON_FRAMEWORK_DIR%
    echo Please ensure the common_project directory exists
    exit /b 1
)

REM Check if virtual environment exists in common framework
if not exist "%COMMON_FRAMEWORK_DIR%\venv\Scripts\activate.bat" (
    echo Setting up common framework virtual environment...
    cd /d "%COMMON_FRAMEWORK_DIR%"
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment
        exit /b 1
    )

    REM Install common framework requirements
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install common framework requirements
        exit /b 1
    )
    deactivate

    cd /d "%PROJECT_DIR%"
)

REM Activate virtual environment from common framework
echo Activating virtual environment...
call "%COMMON_FRAMEWORK_DIR%\venv\Scripts\activate.bat"

REM Check if .env file exists
if not exist "config\.env" (
    echo Configuration file .env not found in config directory
    echo Please copy config\.env.example to config\.env and update with your settings
    exit /b 1
)

REM Create output and logs directories
if not exist "output" mkdir output
if not exist "logs" mkdir logs

REM Set Python path to include common framework
set PYTHONPATH=%COMMON_FRAMEWORK_DIR%\src;%PROJECT_DIR%\src;%PYTHONPATH%

REM Log the execution
echo [%date% %time%] Starting Patient Data Extraction >> logs\extraction.log

REM Run the extraction with all arguments passed to this batch file
echo Running Patient Data Extraction...
python run.py %*

REM Capture exit code
set EXIT_CODE=%errorlevel%

REM Log completion
echo [%date% %time%] Extraction completed with exit code: %EXIT_CODE% >> logs\extraction.log

REM Show results if successful
if %EXIT_CODE%==0 (
    echo.
    echo Extraction completed successfully!
    echo Check the output directory for results:
    if exist "output\mo_patient_ids.csv" (
        echo   - output\mo_patient_ids.csv
    )
    if exist "output\patient_details.csv" (
        echo   - output\patient_details.csv
    )
    echo   - logs\extraction.log
)

REM Deactivate virtual environment
deactivate

REM Exit with the same code as the Python script
exit /b %EXIT_CODE%
