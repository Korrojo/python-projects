@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM Appointment Comparison Validator - Windows Batch Runner
REM ============================================================================

cd /d %~dp0

REM Get timestamp for logging
set TIMESTAMP=%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

REM Ensure logs directory exists
if not exist "..\..\logs\appointment_comparison" mkdir "..\..\logs\appointment_comparison"

REM Log start
echo [%DATE% %TIME%] Starting appointment comparison validation > "..\..\logs\appointment_comparison\%TIMESTAMP%_run.log"

REM Run Python script with all arguments passed through
python run.py %* >> "..\..\logs\appointment_comparison\%TIMESTAMP%_run.log" 2>&1

REM Log completion
echo [%DATE% %TIME%] Validation completed with exit code: %ERRORLEVEL% >> "..\..\logs\appointment_comparison\%TIMESTAMP%_run.log"

REM Display result
if %ERRORLEVEL% EQU 0 (
    echo Validation completed successfully!
    echo Log: logs\appointment_comparison\%TIMESTAMP%_run.log
) else (
    echo Validation failed with error code %ERRORLEVEL%
    echo Check log: logs\appointment_comparison\%TIMESTAMP%_run.log
)

endlocal
exit /b %ERRORLEVEL%
