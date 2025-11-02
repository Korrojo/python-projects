@echo off
setlocal
cd /d %~dp0
REM Use shared virtual environment
call "..\.\.venv311\Scripts\activate.bat"
python run.py %*
