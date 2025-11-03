# Container Collection - Immediate Emergency Fixes
## Critical Issues Found in 32M Document Processing

---

## 🚨 **CRITICAL FINDINGS**

### **Performance Crisis Pattern**
- **Batch 33**: 158 docs/sec (22s duration, 2.5GB memory)
- **Batch 34**: **131 docs/sec (27s duration, 3.7GB memory)** ← WORST
- **Batch 46**: **2,756 docs/sec (1.3s duration, 1.5GB memory)** ← BEST

**Variance**: 2,400% performance difference between document types!

---

## 🛠️ **Emergency Configuration Updates**

### **1. Adaptive Batch Size Configuration**

#### **Container Collection Emergency Config (config_container_emergency.json)**
```json
{
    "mongodb": {
        "source": {
            "uri": "${MONGO_SOURCE_URI}",
            "database": "${MONGO_SOURCE_DB}",
            "collection": "${MONGO_SOURCE_COLL}"
        },
        "destination": {
            "uri": "${MONGO_DEST_URI}",
            "database": "${MONGO_DEST_DB}",
            "collection": "${MONGO_DEST_COLL}"
        }
    },
    "processing": {
        "masking_mode": "in-situ",
        "adaptive_batching": {
            "enabled": true,
            "simple_document_batch": 10000,
            "complex_document_batch": 1000,
            "performance_threshold_ms": 15000,
            "memory_threshold_mb": 2048
        },
        "batch_size": {
            "initial": 3000,
            "min": 500,
            "max": 10000,
            "auto_adjust": true
        },
        "memory": {
            "max_batch_memory_mb": 2048,
            "aggressive_cleanup": true,
            "cleanup_interval": 1,
            "memory_monitor": true
        },
        "workers": {
            "max_workers": 8,
            "threads_per_worker": 2,
            "worker_memory_mb": 512
        }
    },
    "masking": {
        "rules_path": "config/masking_rules/rules_container.json",
        "default_rules": "config/masking_rules/default.json"
    },
    "phi_collections": [
        "Container"
    ],
    "validation": {
        "enabled": true,
        "max_retries": 3
    },
    "metrics": {
        "enabled": true,
        "interval": 2,
        "performance_tracking": true,
        "memory_tracking": true
    },
    "connection": {
        "timeout_ms": 30000,
        "retry_writes": true,
        "retry_reads": true,
        "max_pool_size": 150,
        "min_pool_size": 30,
        "worker_connections": 4
    }
}
```

### **2. Emergency Memory Management (.env.phi updates)**
```dotenv
# Emergency Memory Settings for Container Collection
PROCESSING_BATCH_SIZE=2000              # Reduced from 3500
PROCESSING_MAX_WORKERS=8                # Conservative start
PROCESSING_CHECKPOINT_INTERVAL=1000     # More frequent saves
PROCESSING_MEMORY_TARGET=8GB            # Conservative allocation
PROCESSING_WORKER_MEMORY=512MB          # Per worker limit
PROCESSING_ADAPTIVE_BATCHING=true       # Enable smart batching
PROCESSING_MEMORY_THRESHOLD=2048MB      # Emergency memory limit
```

### **3. Emergency Batch Script (run_container_emergency.bat)**
```batch
@echo off
setlocal enabledelayedexpansion

REM Emergency Container Masker with Adaptive Batching
set PROJECT_NAME=MongoDB PHI Container Emergency Masker
set SCHEDULER_LOG_DIR=C:\Users\demesew\backups\PHI\logs\mask\emergency
set CONFIG_FILE=config\config_container_emergency.json
set ENV_FILE=.env.phi
set MAIN_SCRIPT=masking.py
set RULES_FILE=config\masking_rules\rules_container.json
set LOG_MAX_BYTES=5242880
set LOG_BACKUP_COUNT=20
set VENV_PYTHON=venv\Scripts\python.exe

REM Create emergency logs directory
if not exist "%SCHEDULER_LOG_DIR%" mkdir "%SCHEDULER_LOG_DIR%"

REM Set log file name with timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set TIMESTAMP=%dt:~0,4%%dt:~4,2%%dt:~6,2%_%dt:~8,2%%dt:~10,2%%dt:~12,2%
set SCHEDULER_LOG_FILE=%SCHEDULER_LOG_DIR%\container_emergency_%TIMESTAMP%_scheduler.log

REM Start logging
echo ================================================================= > "%SCHEDULER_LOG_FILE%"
echo %PROJECT_NAME% - Emergency Processing >> "%SCHEDULER_LOG_FILE%"
echo Collection: Container (32M documents, 400GB) >> "%SCHEDULER_LOG_FILE%"
echo Emergency Features: Adaptive batching, Memory monitoring >> "%SCHEDULER_LOG_FILE%"
echo Memory Spike Prevention: 2GB limit per batch >> "%SCHEDULER_LOG_FILE%"
echo Performance Variance Mitigation: Dynamic batch sizing >> "%SCHEDULER_LOG_FILE%"
echo Started at: %DATE% %TIME% >> "%SCHEDULER_LOG_FILE%"

REM Change to project directory
pushd "%~dp0"

REM Run with emergency settings
echo Running emergency Container masker... >> "%SCHEDULER_LOG_FILE%"
"%~dp0%VENV_PYTHON%" "%~dp0%MAIN_SCRIPT%" ^
  --config "%~dp0%CONFIG_FILE%" ^
  --env "%~dp0%ENV_FILE%" ^
  --collection Container ^
  --batch-size 2000 ^
  --max-workers 8 ^
  --memory-limit 8GB ^
  --adaptive-batching ^
  --memory-monitoring ^
  --log-max-bytes %LOG_MAX_BYTES% ^
  --log-backup-count %LOG_BACKUP_COUNT% >> "%SCHEDULER_LOG_FILE%" 2>&1

REM Capture exit status
set EXIT_STATUS=%ERRORLEVEL%

echo ================================================================= >> "%SCHEDULER_LOG_FILE%"
echo Emergency Container masker completed at: %DATE% %TIME% >> "%SCHEDULER_LOG_FILE%"
echo Exit Status: %EXIT_STATUS% >> "%SCHEDULER_LOG_FILE%"
echo Next: Analyze performance logs and optimize further >> "%SCHEDULER_LOG_FILE%"
echo ================================================================= >> "%SCHEDULER_LOG_FILE%"

popd
exit /b %EXIT_STATUS%
```

---

## 📊 **Expected Emergency Improvements**

### **Memory Spike Prevention**
| Scenario | Before | Emergency Fix | Improvement |
|----------|--------|---------------|-------------|
| **Complex Documents** | 3.7GB memory | 2.0GB max | **46% reduction** |
| **Worst Batch Duration** | 26.8 seconds | <8 seconds | **70% improvement** |
| **Performance Variance** | 2,400% | <800% | **67% more consistent** |

### **Adaptive Batching Benefits**
- **Complex Documents**: Batch size 1,000 (vs 3,500)
- **Simple Documents**: Batch size 10,000 (vs 3,500)  
- **Memory Control**: Hard limit at 2GB per batch
- **Auto-adjustment**: Batch size adapts to document complexity

---

## 🎯 **Implementation Steps**

### **Step 1: Stop Current Processing**
```bash
# Find and stop current Container masking
tasklist | findstr python
taskkill /F /PID [container_masking_process_id]
```

### **Step 2: Backup Current State**
```bash
# Note: Currently at batch 53 (185,500 documents processed)
# Remaining: 32,003,971 documents (99.42%)
```

### **Step 3: Deploy Emergency Configuration**
```bash
# Create emergency config files
cp config_container_emergency.json config/
cp run_container_emergency.bat ./

# Update .env.phi with emergency memory settings
```

### **Step 4: Test Emergency Settings**
```bash
# Run emergency version with monitoring
run_container_emergency.bat

# Monitor for:
# - Memory stays <2GB per batch  
# - Performance variance <800%
# - Batch duration <8 seconds max
```

---

## 📈 **Performance Targets**

### **Emergency Success Criteria**
| Metric | Target | Critical Threshold |
|--------|--------|--------------------|
| **Memory Usage** | <2GB per batch | Stop if >3GB |
| **Batch Duration** | <8 seconds | Alert if >15s |
| **Processing Rate** | >300 docs/sec | Alert if <200 |
| **Performance Variance** | <800% | Monitor closely |

### **Expected Results**
- **Worst Case**: 300 docs/sec (vs 131 previously)
- **Best Case**: 2,000 docs/sec (vs 3,100 previously)  
- **Average**: 800 docs/sec (vs 680 previously)
- **Total Duration**: 11.2 hours (vs 13.1 hours)

---

## 🚨 **Monitoring Alerts**

### **Red Alerts** (Stop Processing)
- Memory usage >3GB for any batch
- Batch duration >20 seconds
- Processing rate <150 docs/sec for 3+ consecutive batches

### **Yellow Alerts** (Monitor Closely)
- Memory usage >2.5GB
- Batch duration >10 seconds  
- Processing rate <250 docs/sec

### **Green Status**
- Memory usage <2GB
- Batch duration <5 seconds
- Processing rate >500 docs/sec

---

*Emergency Configuration Created: August 20, 2025*  
*Purpose: Prevent memory spikes and performance degradation*  
*Next: Full optimization after emergency testing*
