@echo off
setlocal
cd /d %~dp0
set TS=%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%
set TS=%TS: =0%
set LOGDIR=..\logs\PatientOtherDetail_isActive_false
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
echo Starting at %date% %time% > "%LOGDIR%\%TS%_run.log"
python run.py %* >> "%LOGDIR%\%TS%_run.log" 2>&1
