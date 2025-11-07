# Windows Task Scheduler Setup Guide

Complete guide for scheduling automated PHI masking workflows on Windows.

______________________________________________________________________

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Setup (5 Steps)](#quick-setup-5-steps)
- [Detailed Configuration](#detailed-configuration)
- [Security Best Practices](#security-best-practices)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Common Issues](#common-issues)

______________________________________________________________________

## Prerequisites

### 1. Install WSL (Recommended) or Git Bash

**Option A: WSL (Windows Subsystem for Linux) - Recommended**

Open PowerShell as Administrator and run:

```powershell
wsl --install
```

After installation, restart your computer.

**Option B: Git for Windows (Alternative)**

Download and install from: https://git-scm.com/download/win

- During installation, select "Git Bash Here" option

### 2. Install Python in WSL/Git Bash

**For WSL:**

```bash
# Update package list
sudo apt update

# Install Python 3 and pip
sudo apt install python3 python3-pip python3-venv

# Verify installation
python3 --version
```

**For Git Bash:**

- Install Python from https://www.python.org/downloads/
- Ensure "Add Python to PATH" is checked during installation

### 3. Setup Project Environment

```bash
# Navigate to project directory
cd /path/to/mongo_phi_masker

# Create virtual environment
python3 -m venv .venv312

# Activate virtual environment
source .venv312/bin/activate  # WSL/Git Bash

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Ensure `../shared_config/.env` is properly configured with MongoDB credentials:

```bash
# Production MongoDB
MONGODB_URI_PROD=mongodb+srv://user:pass@cluster.mongodb.net
DATABASE_NAME_PROD=prod-phidb

# Development MongoDB
MONGODB_URI_DEV=mongodb+srv://user:pass@dev-cluster.mongodb.net
DATABASE_NAME_DEV=dev-phidb

# Email notifications (optional)
EMAIL_NOTIFICATIONS_ENABLED=true
EMAIL_RECIPIENTS=admin@company.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

______________________________________________________________________

## Quick Setup (5 Steps)

### Step 1: Test the Wrapper Script

Open Command Prompt and test:

```cmd
cd C:\path\to\mongo_phi_masker

REM Test with all required arguments
scripts\orchestrate_masking.bat Patients PROD prod-phidb DEV dev-phidb PROD prod-phidb-masked
```

Verify the script runs successfully and check the log file.

### Step 2: Open Task Scheduler

1. Press `Win + R`
1. Type `taskschd.msc`
1. Press Enter

### Step 3: Create New Task

1. Right-click "Task Scheduler Library"
1. Select **"Create Task..."** (NOT "Create Basic Task")
1. Choose a descriptive name: `PHI Masking - Patients Collection`

### Step 4: Configure Task Settings

**General Tab:**

- ✅ Name: `PHI Masking - Patients Collection`
- ✅ Description: `Automated PHI masking workflow for Patients collection`
- ✅ Security options:
  - Select: "Run whether user is logged on or not"
  - ✅ Check: "Run with highest privileges"
  - Select: User account with proper permissions

**Triggers Tab:**

1. Click "New..."
1. Configure schedule:
   - **Daily**: Run every day at 2:00 AM
   - **Weekly**: Run every Sunday at 2:00 AM
   - **Monthly**: Run on the 1st of each month at 2:00 AM
1. ✅ Check: "Enabled"
1. Click "OK"

**Actions Tab:**

1. Click "New..."
1. Action: "Start a program"
1. Settings:
   ```
   Program/script: C:\path\to\mongo_phi_masker\scripts\orchestrate_masking.bat

   Add arguments:
   Patients PROD prod-phidb DEV dev-phidb PROD prod-phidb-masked

   Start in:
   C:\path\to\mongo_phi_masker
   ```
1. Click "OK"

**Conditions Tab:**

- ⬜ Uncheck: "Start the task only if the computer is on AC power"
- ✅ Check: "Wake the computer to run this task" (if needed)

**Settings Tab:**

- ✅ Check: "Allow task to be run on demand"
- ✅ Check: "Run task as soon as possible after a scheduled start is missed"
- ✅ Check: "If the task fails, restart every: 10 minutes, Attempt to restart up to: 3 times"
- Stop the task if it runs longer than: `3 hours` (adjust based on data size)
- If the running task does not end when requested: "Stop the existing instance"

### Step 5: Test the Scheduled Task

1. Right-click the task
1. Select "Run"
1. Check the "Last Run Result" column (should show `0x0` for success)
1. Verify log file: `C:\path\to\mongo_phi_masker\logs\orchestration\YYYYMMDD_HHMMSS_orchestrate_Patients.log`

______________________________________________________________________

## Detailed Configuration

### Multiple Collection Scheduling

Create separate tasks for each collection:

**Task 1: PHI Masking - Patients**

```
Arguments: Patients PROD prod-phidb DEV dev-phidb PROD prod-phidb-masked
Schedule: Daily at 2:00 AM
```

**Task 2: PHI Masking - Messages**

```
Arguments: Messages PROD prod-phidb DEV dev-phidb PROD prod-phidb-masked
Schedule: Daily at 3:00 AM (offset to avoid conflicts)
```

**Task 3: PHI Masking - Tasks**

```
Arguments: Tasks PROD prod-phidb DEV dev-phidb PROD prod-phidb-masked
Schedule: Daily at 4:00 AM
```

### Advanced Arguments

**Skip Backup Source (Use Existing Backup):**

Modify the wrapper script to accept flags:

```cmd
REM In orchestrate_masking.bat, add to the bash command:
bash scripts/orchestrate_masking.sh ^
    --src-env %SRC_ENV% ^
    --src-db %SRC_DB% ^
    --proc-env %PROC_ENV% ^
    --proc-db %PROC_DB% ^
    --dst-env %DST_ENV% ^
    --dst-db %DST_DB% ^
    --collection %COLLECTION% ^
    --skip-backup-source ^
    --verify-samples 10
```

Or create a custom wrapper for each workflow variant.

### Email Notifications

Ensure `.env` is configured:

```bash
EMAIL_NOTIFICATIONS_ENABLED=true
EMAIL_RECIPIENTS=team@company.com,admin@company.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=noreply@company.com
SMTP_PASSWORD=your-app-password  # Use App Password, not account password
EMAIL_SENDER=phi-masker@company.com
EMAIL_SENDER_NAME=PHI Masking System
EMAIL_SUBJECT_PREFIX=[PHI Masker - PROD]
```

**Gmail App Password Setup:**

1. Go to Google Account → Security
1. Enable 2-Step Verification
1. Go to "App passwords"
1. Generate new app password for "Mail"
1. Use this password in `SMTP_PASSWORD`

______________________________________________________________________

## Security Best Practices

### 1. Secure Credential Storage

**DO NOT** store credentials in the batch file!

✅ **Use `.env` file** (recommended):

```bash
# Store in ../shared_config/.env (outside git repo)
MONGODB_URI_PROD=mongodb+srv://user:password@cluster.mongodb.net
```

✅ **Use Windows Credential Manager** (alternative):

```powershell
# Store credentials securely
cmdkey /generic:mongo_phi_prod_user /user:prod_user /pass:secure_password

# Retrieve in script
for /f "tokens=*" %%i in ('cmdkey /list:mongo_phi_prod_user') do set CRED=%%i
```

❌ **DON'T hardcode in batch files**:

```cmd
REM BAD - credentials visible in task properties!
set MONGODB_URI=mongodb+srv://user:password123@...
```

### 2. File Permissions

Restrict access to sensitive files:

```cmd
REM Allow only Administrators and SYSTEM
icacls "..\shared_config\.env" /inheritance:r
icacls "..\shared_config\.env" /grant:r "SYSTEM:(R)"
icacls "..\shared_config\.env" /grant:r "Administrators:(R)"
```

### 3. Task Account Permissions

Create a dedicated service account:

1. Create new Windows user: `PHIMaskingService`
1. Grant minimum required permissions:
   - Read/Write access to project directory
   - Read access to `.env` file
   - No admin rights (unless absolutely needed)
1. Use this account to run the scheduled task

### 4. Log File Rotation

Prevent log directory from growing too large:

```cmd
REM Add to batch file before running orchestration
forfiles /p "logs\orchestration" /s /m *.log /d -30 /c "cmd /c del @path"
```

This deletes logs older than 30 days.

______________________________________________________________________

## Monitoring & Troubleshooting

### View Task History

1. Open Task Scheduler
1. Click on your task
1. Go to "History" tab
1. Review execution events:
   - Event ID 100: Task started
   - Event ID 102: Task completed
   - Event ID 103: Task failed

### Check Logs

**Task Scheduler Logs:**

```
Event Viewer → Windows Logs → Application
Filter by Source: "Task Scheduler"
```

**Application Logs:**

```
C:\path\to\mongo_phi_masker\logs\orchestration\YYYYMMDD_HHMMSS_orchestrate_Patients.log
```

### Email Monitoring

Configure email notifications in `.env` to receive:

- ✅ Success notifications with execution time and artifacts
- ❌ Failure notifications with error details and step information

### Create Monitoring Script

Create `scripts/check_last_run.bat`:

```cmd
@echo off
REM Check last orchestration run status

set LATEST_LOG=
for /f "delims=" %%i in ('dir /b /o-d logs\orchestration\*_orchestrate_Patients.log 2^>nul') do (
    set LATEST_LOG=%%i
    goto :found
)

:found
if "%LATEST_LOG%"=="" (
    echo No logs found!
    exit /b 1
)

echo Latest log: %LATEST_LOG%
echo.

findstr /C:"All steps completed successfully" "logs\orchestration\%LATEST_LOG%" >nul
if %ERRORLEVEL% EQU 0 (
    echo Status: SUCCESS
    exit /b 0
) else (
    echo Status: FAILED
    echo.
    echo Last 20 lines:
    powershell -Command "Get-Content 'logs\orchestration\%LATEST_LOG%' -Tail 20"
    exit /b 1
)
```

Run this after each scheduled execution to verify success.

______________________________________________________________________

## Common Issues

### Issue 1: "WSL not found"

**Solution:**

```powershell
# Install WSL
wsl --install

# Or update WSL
wsl --update

# Verify installation
wsl --status
```

### Issue 2: "Permission denied" errors

**Solution:**

```cmd
REM Run task with elevated privileges
REM In Task Scheduler → General tab:
- Check "Run with highest privileges"
- Select admin account
```

### Issue 3: Task runs but does nothing

**Cause:** Working directory not set correctly

**Solution:**

```
In Task Scheduler → Actions → Edit Action:
Start in: C:\full\path\to\mongo_phi_masker
```

### Issue 4: Python not found in WSL

**Solution:**

```bash
# In WSL, install Python
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Verify
which python3
python3 --version
```

### Issue 5: Virtual environment not activated

**Solution:**

Modify batch wrapper to activate venv:

```cmd
REM Add before calling bash script
wsl bash -c "cd '%WSL_PATH%' && source .venv312/bin/activate && bash scripts/orchestrate_masking.sh ..."
```

### Issue 6: MongoDB connection timeout

**Cause:** Windows Firewall blocking outbound connections

**Solution:**

```cmd
REM Add firewall rule for MongoDB (port 27017)
netsh advfirewall firewall add rule name="MongoDB" dir=out action=allow protocol=TCP remoteport=27017
```

### Issue 7: Logs show "Authentication failed"

**Cause:** Incorrect MongoDB credentials or IP whitelist

**Solution:**

1. Verify credentials in `.env` file
1. Check MongoDB Atlas IP whitelist:
   - Add Windows machine IP address
   - Or use `0.0.0.0/0` for testing (not recommended for production)

### Issue 8: Task stuck in "Running" state

**Cause:** Process hung or waiting for input

**Solution:**

1. Kill the task manually
1. Check logs for errors
1. Add timeout in Settings tab: "Stop the task if it runs longer than: 2 hours"

______________________________________________________________________

## Testing Checklist

Before enabling scheduled tasks:

- [ ] Test batch wrapper from Command Prompt
- [ ] Verify WSL/Git Bash is working
- [ ] Check Python and dependencies are installed
- [ ] Validate `.env` configuration
- [ ] Run manual orchestration successfully
- [ ] Test Task Scheduler "Run" function
- [ ] Verify email notifications work
- [ ] Check log files are created correctly
- [ ] Confirm MongoDB connectivity
- [ ] Review file/folder permissions
- [ ] Set up log rotation
- [ ] Document schedule and contacts

______________________________________________________________________

## Useful Commands

**Manually trigger task:**

```cmd
schtasks /run /tn "PHI Masking - Patients Collection"
```

**Check task status:**

```cmd
schtasks /query /tn "PHI Masking - Patients Collection" /v /fo list
```

**Delete task:**

```cmd
schtasks /delete /tn "PHI Masking - Patients Collection"
```

**Export task (backup):**

```cmd
schtasks /query /tn "PHI Masking - Patients Collection" /xml > task_backup.xml
```

**Import task:**

```cmd
schtasks /create /tn "PHI Masking - Patients Collection" /xml task_backup.xml
```

______________________________________________________________________

## Support

For issues or questions:

- Check logs: `logs/orchestration/`
- Review [README.md](README.md) for workflow details
- See [COLLECTIONS.md](COLLECTIONS.md) for collection setup
- Validate configuration: `python scripts/validate_collection.py --collection Patients`

______________________________________________________________________

## See Also

- [README.md](README.md) - Main documentation
- [COLLECTIONS.md](COLLECTIONS.md) - Collection configuration
- [LOGGING_STANDARD.md](LOGGING_STANDARD.md) - Logging format
- `scripts/orchestrate_masking.sh` - Main orchestration script
- `scripts/orchestrate_masking.bat` - Windows wrapper
