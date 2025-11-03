# PowerShell Commands for MongoDB PHI Masker

## Quick Reference for Running Background Jobs on Windows

### ⚠️ **Important: Bash vs PowerShell**
The README contains **Linux/Bash** commands (with `nohup`, `&`, `2>&1`). On Windows PowerShell, use these alternatives:

---

## 🚀 **Easy Way: Use the Helper Script**

```powershell
# Run with default settings (batch size from .env.phi = 9000)
.\run_masking_job.ps1 -Collection "StaffAvailabilityHistory"

# Run with custom batch size
.\run_masking_job.ps1 -Collection "StaffAvailabilityHistory" -BatchSize 5000

# Run with in-situ mode (default)
.\run_masking_job.ps1 -Collection "StaffAvailabilityHistory" -BatchSize 5000 -InSitu

# Run with different config
.\run_masking_job.ps1 -Collection "Patients" -ConfigFile "config/config_rules/config_Patients.json"
```

---

## 📝 **Manual Background Job Commands**

### **Method 1: Start-Job (Recommended)**
```powershell
Start-Job -ScriptBlock {
    Set-Location "C:\Users\demesew\projects\python\mongo_phi_masker"
    .\venv-3.11\Scripts\python.exe masking.py `
        --config config/config_rules/config_StaffAavailability.json `
        --env .env.phi `
        --in-situ `
        --batch-size 5000 `
        --collection StaffAvailabilityHistory `
        *>&1 | Out-File -FilePath "logs/phi/20251010_000000_masking_StaffAvailabilityHistory.log" -Encoding UTF8
}
```

### **Method 2: Start-Process (Background Process)**
```powershell
Start-Process -FilePath ".\venv-3.11\Scripts\python.exe" `
    -ArgumentList "masking.py --config config/config_rules/config_StaffAavailability.json --env .env.phi --in-situ --batch-size 5000 --collection StaffAvailabilityHistory" `
    -RedirectStandardOutput "logs/phi/20251010_000000_masking_StaffAvailabilityHistory.log" `
    -RedirectStandardError "logs/phi/20251010_000000_masking_StaffAvailabilityHistory.err.log" `
    -NoNewWindow `
    -PassThru
```

---

## 📊 **Monitoring Jobs**

### **Check All Background Jobs**
```powershell
Get-Job
```

### **Check Specific Job**
```powershell
Get-Job -Id 1
```

### **View Job Output**
```powershell
# View and keep in buffer
Receive-Job -Id 1 -Keep

# View and remove from buffer
Receive-Job -Id 1
```

### **Monitor Log File in Real-Time**
```powershell
# Tail and follow (like tail -f in Linux)
Get-Content -Path "logs/phi/20251010_000000_masking_StaffAvailabilityHistory.log" -Tail 20 -Wait

# Just view last 20 lines
Get-Content -Path "logs/phi/20251010_000000_masking_StaffAvailabilityHistory.log" -Tail 20
```

### **Check Running Python Processes**
```powershell
# All Python processes
Get-Process | Where-Object { $_.ProcessName -like "*python*" }

# With full details
Get-Process | Where-Object { $_.ProcessName -like "*python*" } | Format-Table ProcessName, Id, CPU, WorkingSet64 -AutoSize
```

---

## 🛑 **Stopping Jobs**

### **Stop Background Job**
```powershell
Stop-Job -Id 1
```

### **Stop Python Process**
```powershell
# Get the process ID first
Get-Process | Where-Object { $_.ProcessName -like "*python*" }

# Stop by ID
Stop-Process -Id <ProcessId>

# Force stop
Stop-Process -Id <ProcessId> -Force
```

### **Remove Completed Jobs**
```powershell
# Remove specific job
Remove-Job -Id 1

# Remove all completed jobs
Get-Job -State Completed | Remove-Job

# Remove all jobs
Get-Job | Remove-Job -Force
```

---

## 📋 **Common Command Translations**

| Linux/Bash Command | PowerShell Equivalent |
|--------------------|-----------------------|
| `nohup command &` | `Start-Job -ScriptBlock { command }` |
| `command > file 2>&1` | `command *>&1 \| Out-File file` |
| `tail -f file` | `Get-Content file -Tail 20 -Wait` |
| `tail -n 20 file` | `Get-Content file -Tail 20` |
| `ps aux \| grep python` | `Get-Process \| Where-Object { $_.ProcessName -like "*python*" }` |
| `kill -9 <pid>` | `Stop-Process -Id <pid> -Force` |
| `jobs` | `Get-Job` |
| `bg` | (Jobs run in background by default) |

---

## 🎯 **Common Usage Examples**

### **Example 1: Run single collection with custom batch size**
```powershell
.\run_masking_job.ps1 -Collection "StaffAvailabilityHistory" -BatchSize 5000
```

### **Example 2: Run and wait for completion**
```powershell
# Script will prompt if you want to wait
.\run_masking_job.ps1 -Collection "Patients" -BatchSize 3500
# Type 'y' when prompted
```

### **Example 3: Run multiple collections sequentially**
```powershell
$collections = @("StaffAvailability", "StaffAvailabilityHistory", "Tasks")
foreach ($coll in $collections) {
    .\run_masking_job.ps1 -Collection $coll -BatchSize 5000 -InSitu
    Start-Sleep -Seconds 5  # Wait 5 seconds between jobs
}
```

### **Example 4: Monitor all running jobs**
```powershell
# Watch jobs in real-time (refresh every 5 seconds)
while ($true) {
    Clear-Host
    Write-Host "=== Background Jobs ===" -ForegroundColor Cyan
    Get-Job | Format-Table Id, Name, State, HasMoreData -AutoSize
    Write-Host "`nPress Ctrl+C to stop monitoring" -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}
```

---

## 🔧 **Batch Size Priority**

When running `masking.py`, batch size is determined in this order:

1. **Command line `--batch-size`** (Highest Priority)
2. **Environment variable `PROCESSING_BATCH_SIZE`** from `.env.phi`
3. **Default hardcoded value** of `100` (Lowest Priority)

**Note:** The JSON config file batch size is **NOT** used by `masking.py`.

### Current `.env.phi` setting:
```
PROCESSING_BATCH_SIZE=9000
```

So if you don't specify `--batch-size`, it will use **9000**.

---

## 📁 **Log Files**

Logs are created in: `logs/phi/`

Format: `YYYYMMDD_HHMMSS_masking_<CollectionName>.log`

**View errors:**
```powershell
Get-Content "logs/phi/20251010_000000_masking_StaffAvailabilityHistory.log.err"
```

---

## 🆘 **Troubleshooting**

### **"The ampersand (&) character is not allowed"**
You're using Linux syntax. Use `Start-Job` or the helper script instead.

### **"Cannot find path"**
Make sure you're in the project directory:
```powershell
Set-Location "C:\Users\demesew\projects\python\mongo_phi_masker"
```

### **"Python not found"**
Activate the virtual environment first:
```powershell
.\venv-3.11\Scripts\Activate.ps1
```
Or use the full path: `.\venv-3.11\Scripts\python.exe`

### **Job stuck or not responding**
```powershell
# Check job state
Get-Job -Id <JobId>

# Force stop
Stop-Job -Id <JobId>
Remove-Job -Id <JobId> -Force
```

---

*End of Quick Reference*
