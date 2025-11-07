@echo off
REM ============================================================================
REM Windows Batch Wrapper for PHI Masking Orchestration
REM
REM This wrapper allows the bash orchestration script to run on Windows
REM via WSL (Windows Subsystem for Linux) or Git Bash.
REM
REM Usage (Task Scheduler):
REM   Program: C:\path\to\mongo_phi_masker\scripts\orchestrate_masking.bat
REM   Arguments: Patients PROD prod-phidb DEV dev-phidb PROD prod-phidb-masked
REM
REM Usage (Command Line):
REM   orchestrate_masking.bat Patients PROD prod-phidb DEV dev-phidb PROD prod-phidb-masked
REM ============================================================================

REM Change to script directory
cd /d "%~dp0"
cd ..

REM Parse arguments
set COLLECTION=%1
set SRC_ENV=%2
set SRC_DB=%3
set PROC_ENV=%4
set PROC_DB=%5
set DST_ENV=%6
set DST_DB=%7

REM Validate required arguments
if "%COLLECTION%"=="" (
    echo ERROR: Missing required arguments
    echo.
    echo Usage: %0 COLLECTION SRC_ENV SRC_DB PROC_ENV PROC_DB DST_ENV DST_DB
    echo.
    echo Example:
    echo   %0 Patients PROD prod-phidb DEV dev-phidb PROD prod-phidb-masked
    exit /b 1
)

REM Create timestamp for logging
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%

REM Setup log directory
if not exist "logs\orchestration" mkdir "logs\orchestration"
set LOG_FILE=logs\orchestration\%TIMESTAMP%_orchestrate_%COLLECTION%.log

echo ====================================================================== >> "%LOG_FILE%" 2>&1
echo Windows Task Scheduler - PHI Masking Orchestration >> "%LOG_FILE%" 2>&1
echo ====================================================================== >> "%LOG_FILE%" 2>&1
echo Start Time: %date% %time% >> "%LOG_FILE%" 2>&1
echo Collection: %COLLECTION% >> "%LOG_FILE%" 2>&1
echo Source: %SRC_ENV% / %SRC_DB% >> "%LOG_FILE%" 2>&1
echo Processing: %PROC_ENV% / %PROC_DB% >> "%LOG_FILE%" 2>&1
echo Destination: %DST_ENV% / %DST_DB% >> "%LOG_FILE%" 2>&1
echo ====================================================================== >> "%LOG_FILE%" 2>&1
echo. >> "%LOG_FILE%" 2>&1

REM Check for WSL (preferred method)
where wsl >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Using WSL to execute bash script... >> "%LOG_FILE%" 2>&1

    REM Convert Windows path to WSL path
    for /f "tokens=*" %%i in ('wsl wslpath -a "%CD%"') do set WSL_PATH=%%i

    REM Execute via WSL
    wsl bash "%WSL_PATH%/scripts/orchestrate_masking.sh" ^
        --src-env %SRC_ENV% ^
        --src-db %SRC_DB% ^
        --proc-env %PROC_ENV% ^
        --proc-db %PROC_DB% ^
        --dst-env %DST_ENV% ^
        --dst-db %DST_DB% ^
        --collection %COLLECTION% >> "%LOG_FILE%" 2>&1

    set EXIT_CODE=%ERRORLEVEL%
    goto :result
)

REM Check for Git Bash (alternative method)
if exist "C:\Program Files\Git\bin\bash.exe" (
    echo Using Git Bash to execute bash script... >> "%LOG_FILE%" 2>&1

    "C:\Program Files\Git\bin\bash.exe" -c "cd '%CD%' && bash scripts/orchestrate_masking.sh --src-env %SRC_ENV% --src-db %SRC_DB% --proc-env %PROC_ENV% --proc-db %PROC_DB% --dst-env %DST_ENV% --dst-db %DST_DB% --collection %COLLECTION%" >> "%LOG_FILE%" 2>&1

    set EXIT_CODE=%ERRORLEVEL%
    goto :result
)

REM No bash environment found
echo ERROR: Neither WSL nor Git Bash found! >> "%LOG_FILE%" 2>&1
echo Please install WSL or Git for Windows. >> "%LOG_FILE%" 2>&1
set EXIT_CODE=1

:result
echo. >> "%LOG_FILE%" 2>&1
echo ====================================================================== >> "%LOG_FILE%" 2>&1
echo End Time: %date% %time% >> "%LOG_FILE%" 2>&1
echo Exit Code: %EXIT_CODE% >> "%LOG_FILE%" 2>&1
echo ====================================================================== >> "%LOG_FILE%" 2>&1

if %EXIT_CODE% EQU 0 (
    echo SUCCESS: Orchestration completed successfully
    echo Log file: %LOG_FILE%
) else (
    echo FAILURE: Orchestration failed with exit code %EXIT_CODE%
    echo Check log file: %LOG_FILE%
)

exit /b %EXIT_CODE%
