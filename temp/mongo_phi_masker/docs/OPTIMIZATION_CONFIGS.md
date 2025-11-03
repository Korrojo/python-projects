# Immediate Performance Optimization - Configuration Updates

## 🚀 **Quick Win #1: Optimized Configuration Files**

Based on system resource analysis showing 94% memory underutilization and 98% CPU underutilization, here are the immediate configuration changes to implement:

---

## 📝 **Environment Configuration (.env.phi)**

```dotenv
# MongoDB Source Connection - PRODUCTION  
MONGO_SOURCE_USERNAME=dabebe
MONGO_SOURCE_PASSWORD=pdemes
MONGO_SOURCE_HOST=ubiquityphi-pl-1.rgmqs.mongodb.net
MONGO_SOURCE_AUTH_DB=admin
MONGO_SOURCE_USE_SSL=true
MONGO_SOURCE_USE_SRV=true
MONGO_SOURCE_DB=UbiquityPhiMasked
# MONGO_SOURCE_COLL is now specified via --collection argument

# MongoDB Destination Connection - PRODUCTION
MONGO_DEST_USERNAME=dabebe
MONGO_DEST_PASSWORD=pdemes
MONGO_DEST_HOST=ubiquityphi-pl-1.rgmqs.mongodb.net
MONGO_DEST_AUTH_DB=admin
MONGO_DEST_USE_SSL=true
MONGO_DEST_USE_SRV=true
MONGO_DEST_DB=UbiquityPhiMasked  
# MONGO_DEST_COLL is now specified via --collection argument

# OPTIMIZED Processing Configuration for 64GB RAM / 64-Core System
PROCESSING_BATCH_SIZE=8000              # Increased from 3500
PROCESSING_MAX_WORKERS=32               # Increased from default
PROCESSING_CHECKPOINT_INTERVAL=5000     # More frequent checkpoints
PROCESSING_MEMORY_TARGET=16GB           # 25% of total RAM
PROCESSING_WORKER_MEMORY=512MB          # Per worker memory limit
```

---

## 📝 **Collection-Specific Optimized Configs**

### **Container Collection (config_container_optimized.json)**
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
        "batch_size": {
            "initial": 8000,
            "min": 4000,
            "max": 15000
        },
        "workers": {
            "max_workers": 32,
            "threads_per_worker": 2,
            "worker_memory_mb": 512
        },
        "memory": {
            "total_allocation_gb": 16,
            "batch_memory_mb": 2048,
            "cleanup_interval": 5
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
        "interval": 5
    },
    "connection": {
        "timeout_ms": 10000,
        "retry_writes": true,
        "retry_reads": true,
        "max_pool_size": 200,
        "min_pool_size": 50,
        "worker_connections": 8
    }
}
```

### **Tasks Collection (tasks_config_optimized.json)**
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
        "batch_size": {
            "initial": 10000,
            "min": 5000,
            "max": 20000
        },
        "workers": {
            "max_workers": 32,
            "threads_per_worker": 2,
            "worker_memory_mb": 512
        },
        "memory": {
            "total_allocation_gb": 16,
            "batch_memory_mb": 2048,
            "cleanup_interval": 3
        }
    },
    "masking": {
        "rules_path": "config/masking_rules/tasks_rules.json",
        "default_rules": "config/masking_rules/default.json"
    },
    "phi_collections": [
        "Tasks"
    ],
    "validation": {
        "enabled": true,
        "max_retries": 3
    },
    "metrics": {
        "enabled": true,
        "interval": 5
    },
    "connection": {
        "timeout_ms": 10000,
        "retry_writes": true,
        "retry_reads": true,
        "max_pool_size": 200,
        "min_pool_size": 50,
        "worker_connections": 8
    }
}
```

### **StaffAvailability Collection (staff_availability_config_optimized.json)**
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
        "batch_size": {
            "initial": 8000,
            "min": 4000,
            "max": 15000
        },
        "workers": {
            "max_workers": 32,
            "threads_per_worker": 2,
            "worker_memory_mb": 512
        },
        "memory": {
            "total_allocation_gb": 16,
            "batch_memory_mb": 2048,
            "cleanup_interval": 4
        }
    },
    "masking": {
        "rules_path": "config/masking_rules/staff_availability_rules.json",
        "default_rules": "config/masking_rules/default.json",
        "collection_groups": {
            "staff_availability": [
                "StaffAvailability"
            ]
        }
    },
    "phi_collections": [
        "StaffAvailability"
    ],
    "validation": {
        "enabled": true,
        "max_retries": 3
    },
    "metrics": {
        "enabled": true,
        "interval": 5
    },
    "connection": {
        "timeout_ms": 10000,
        "retry_writes": true,
        "retry_reads": true,
        "max_pool_size": 200,
        "min_pool_size": 50,
        "worker_connections": 8
    }
}
```

---

## 🔧 **Updated Batch Scripts with Optimization**

### **Optimized Production Masker (run_production_masker_optimized.bat)**
```batch
# Add these parameters to the existing script
set BATCH_SIZE_INITIAL=8000
set MAX_WORKERS=32
set MEMORY_ALLOCATION=16GB

# Update the Python command
"%~dp0%VENV_PYTHON%" "%~dp0%MAIN_SCRIPT%" ^
  --config "%~dp0config\config_container_optimized.json" ^
  --env "%~dp0%ENV_FILE%" ^
  --collection Container ^
  --batch-size %BATCH_SIZE_INITIAL% ^
  --max-workers %MAX_WORKERS% ^
  --memory-limit %MEMORY_ALLOCATION% ^
  --log-max-bytes %LOG_MAX_BYTES% ^
  --log-backup-count %LOG_BACKUP_COUNT% >> "%SCHEDULER_LOG_FILE%" 2>&1
```

---

## 📊 **Container Collection Analysis - CRITICAL INSIGHTS**

### **32M Document Dataset Findings (August 20, 2025)**
- **Total Documents**: 32,189,471 (~400GB)
- **Critical Issue**: 2,400% performance variance (131-3,100 docs/sec)
- **Memory Crisis**: Spikes from 1.3GB to 3.7GB causing 76% slowdown
- **Document Complexity**: Batches 33-44 contain complex documents requiring 26+ seconds vs 1-2 seconds for simple documents

### **Before Optimization (Container Collection)**
| Metric | Current Value | Issue |
|--------|---------------|-------|
| Processing Rate | 131-3,100 docs/sec | 2,400% variance |
| Memory Usage | 676MB-3,763MB | Uncontrolled spikes |
| Batch Duration | 1.1-26.8 seconds | Extreme inconsistency |
| ETA for Completion | 13.1 hours | Too long for maintenance window |

### **Critical Need: Document Complexity Handling**
The Container collection contains documents with varying PHI complexity:
- **Simple Documents**: Process at 3,000+ docs/sec with 1.3GB memory
- **Complex Documents**: Process at 131 docs/sec with 3.7GB memory  
- **Impact**: 2,270% processing time variance between document types

## 📈 **Updated Optimization Strategy**
| Metric | Expected Value | Improvement |
|--------|----------------|-------------|
| Processing Rate | 1,500-2,000 docs/sec | **3-4x faster** |
| Memory Usage | 16GB (25% of total) | **4x increase** |
| CPU Usage | 20-32 cores (50% of total) | **16x increase** |
| Batch Size | 8,000-10,000 documents | **2.3x larger** |
| StaffAvailability Duration | 30-40 minutes | **75% reduction** |

---

## ⚠️ **Implementation Steps**

### **Step 1: Backup Current Configuration**
```bash
cp config/config_container.json config/config_container_backup.json
cp config/tasks_config.json config/tasks_config_backup.json  
cp config/staff_availability_config.json config/staff_availability_config_backup.json
cp .env.phi .env.phi.backup
```

### **Step 2: Implement Optimized Configurations**
1. Update `.env.phi` with optimized processing parameters
2. Create optimized config files for each collection
3. Update batch scripts with new parameters

### **Step 3: Test with Single Collection**
```bash
# Test with StaffAvailability first (smallest collection)
run_staffavailability_masker_optimized.bat
```

### **Step 4: Monitor and Adjust**
- Watch memory usage (should reach ~16GB)
- Monitor CPU usage (should reach 40-60%)
- Verify processing rate improvements
- Check for any errors or bottlenecks

### **Step 5: Scale to All Collections**
Once StaffAvailability runs successfully with optimized settings:
```bash
# Run all collections in parallel
start run_production_masker_optimized.bat
start run_tasks_masker_optimized.bat  
start run_staffavailability_masker_optimized.bat
```

---

## 📈 **Success Metrics**

### **Resource Utilization Targets**
- **Memory**: 25-35% utilization (16-20GB)
- **CPU**: 40-60% utilization (25-40 cores)
- **Processing Rate**: 1,500+ docs/sec per collection
- **Total Duration**: All collections complete in <1 hour

### **Performance Indicators**
- Batch processing time: <4 seconds per batch
- Memory growth: Linear and controlled
- No memory leaks or crashes
- Consistent throughput rates

---

*Configuration Date: August 20, 2025*  
*Target: 75% performance improvement with immediate optimizations*
