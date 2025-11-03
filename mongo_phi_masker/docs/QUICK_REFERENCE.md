# MongoDB PHI Masker - Quick Reference Guide

## 🚀 **Before Running Any Script - CRITICAL CHECKLIST**

### **1. Configuration Files to Verify**

| File                              | Location                | What to Check                                                                                            |
| --------------------------------- | ----------------------- | -------------------------------------------------------------------------------------------------------- |
| **`.env.phi`**                    | Root directory          | ✅ Database credentials<br/>✅ NO collection names (removed for flexibility)                             |
| **`config_[collection].json`**    | `config/`               | ✅ Correct collection in `phi_collections`<br/>✅ Appropriate batch sizes<br/>✅ Correct rules file path |
| **`rules_[collection].json`**     | `config/masking_rules/` | ✅ PHI field mappings<br/>✅ Masking strategies per field                                                |
| **`run_[collection]_masker.bat`** | Root directory          | ✅ Correct `--collection` argument<br/>✅ Correct config file path                                       |

### **2. Pre-Execution Verification Commands**

```bash
# Test database connectivity
python -c "from src.core.connector import MongoConnector; print('Connection OK')"

# Verify config file syntax
python -c "import json; print(json.load(open('config/config_rules/tasks_config.json')))"

# Check virtual environment
venv\Scripts\python.exe --version

# Verify log directory exists and is writable
mkdir -p "C:\Users\demesew\backups\PHI\logs\mask\tasks"
```

______________________________________________________________________

## 📊 **Current Production Setup**

### **Collections & Scripts**

| Collection            | Documents | PHI Fields | Script                             | Estimated Duration |
| --------------------- | --------- | ---------- | ---------------------------------- | ------------------ |
| **Container**         | ~Unknown  | Multiple   | `run_production_masker.bat`        | TBD                |
| **Tasks**             | ~4.30M    | 3 fields   | `run_tasks_masker.bat`             | ~2.4 hours         |
| **StaffAvailability** | ~3.76M    | 5 fields   | `run_staffavailability_masker.bat` | ~2.1 hours         |

### **Log File Locations**

| Collection        | Log Directory                                               | Log File Pattern                                          |
| ----------------- | ----------------------------------------------------------- | --------------------------------------------------------- |
| Container         | `C:\Users\demesew\backups\PHI\logs\mask\`                   | `masking_YYYYMMDD_HHMMSS_scheduler.log`                   |
| Tasks             | `C:\Users\demesew\backups\PHI\logs\mask\tasks\`             | `tasks_masking_YYYYMMDD_HHMMSS_scheduler.log`             |
| StaffAvailability | `C:\Users\demesew\backups\PHI\logs\mask\staffavailability\` | `staffavailability_masking_YYYYMMDD_HHMMSS_scheduler.log` |

______________________________________________________________________

## ⚡ **Quick Commands**

### **Run Individual Collection**

```bash
# Container Collection
run_production_masker.bat

# Tasks Collection  
run_tasks_masker.bat

# StaffAvailability Collection
run_staffavailability_masker.bat
```

### **Manual Python Execution**

```bash
# Direct Python execution (if needed)
venv\Scripts\python.exe masking.py --config config\tasks_config.json --env .env.phi --collection Tasks

# With additional parameters
venv\Scripts\python.exe masking.py --config config\tasks_config.json --env .env.phi --collection Tasks --limit 1000 --debug
```

### **Monitor Progress**

```bash
# Watch log file in real-time
tail -f "C:\Users\demesew\backups\PHI\logs\mask\tasks\tasks_masking_20250819_081457_scheduler.log"

# Check current batch progress
grep "Processed.*documents" "C:\Users\demesew\backups\PHI\logs\mask\tasks\*.log" | tail -5
```

______________________________________________________________________

## 🔧 **Configuration Quick Reference**

### **Batch Sizes by Collection**

```json
// Container (config_container.json)
"batch_size": {"initial": 3500, "min": 1000, "max": 5000}

// Tasks (tasks_config.json)  
"batch_size": {"initial": 3500, "min": 1000, "max": 5000}

// StaffAvailability (staff_availability_config.json)
"batch_size": {"initial": 3500, "min": 1000, "max": 5000}
```

### **PHI Fields by Collection**

```json
// Container: Multiple fields (see rules_container.json)

// Tasks: 3 fields
["PatientName", "UserName", "Notes"]

// StaffAvailability: 5 fields  
["PatientName", "City", "VisitNotes", "VisitAddress", "Comments"]
```

______________________________________________________________________

## 🚨 **Troubleshooting Quick Fixes**

### **Common Issues & Solutions**

| Issue                       | Quick Fix                                         |
| --------------------------- | ------------------------------------------------- |
| "Collection not found"      | ✅ Check `--collection` argument matches database |
| "Config file not found"     | ✅ Verify file path in batch script               |
| "Virtual environment error" | ✅ Check `venv\Scripts\python.exe` exists         |
| "Permission denied on logs" | ✅ Ensure log directory is writable               |
| "Memory issues"             | ✅ Reduce batch size in config file               |
| "Connection timeout"        | ✅ Check database credentials in `.env.phi`       |

### **Emergency Stop Procedures**

```bash
# Find and kill masking process
tasklist | findstr python
taskkill /F /PID [process_id]

# Check if any locks remain
# MongoDB: Check for active operations in database
```

______________________________________________________________________

## 📈 **Performance Monitoring**

### **Key Metrics to Watch**

- **Processing Rate**: Should be 400-600 docs/sec
- **Memory Usage**: Should stay under 1GB
- **Batch Duration**: Should be 5-8 seconds per batch
- **Error Rate**: Should be 0%

### **Performance Tuning**

```json
// Increase performance
"batch_size": {"initial": 5000, "max": 8000}
"PROCESSING_MAX_WORKERS": 64

// Reduce memory usage  
"batch_size": {"initial": 2000, "max": 3000}
"PROCESSING_MAX_WORKERS": 16
```

______________________________________________________________________

## 🔒 **Security Checklist**

- ✅ Database credentials secured in `.env.phi`
- ✅ No hardcoded passwords in scripts
- ✅ Log files in secure directory
- ✅ Virtual environment isolated
- ✅ Collection names not in environment file

______________________________________________________________________

## 📞 **Support Information**

### **Key Files for Diagnostics**

1. **Scheduler Logs**: `C:\Users\demesew\backups\PHI\logs\mask\[collection]\`
1. **Application Logs**: `logs/test/masking_*_size.log`
1. **Configuration Files**: `config/conf` directory
1. **Environment**: `.env.phi`

### **What to Include in Support Requests**

- Collection name being processed
- Exact error message
- Relevant log file excerpts
- Configuration file contents (redacted credentials)
- System resource usage at time of issue

______________________________________________________________________

*Quick Reference Updated: August 19, 2025*
