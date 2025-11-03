# System Resource Analysis - MongoDB PHI Masker
## Date: August 19-20, 2025

---

## 🖥️ **System Specifications**

### **Hardware Configuration**
- **Processor**: AMD EPYC 7763 64-Core Processor @ 2.44 GHz
- **RAM**: 64.0 GB total installed
- **System**: 64-bit Windows, x64-based processor
- **Environment**: Azure VM (vm-01-c-prod)

### **Available Resources vs. Current Utilization**

| Resource | Available | Current Usage | Utilization % | Potential |
|----------|-----------|---------------|---------------|-----------|
| **CPU Cores** | 64 cores | ~1-2 cores | 10-15% | **85-90% unused** |
| **Memory** | 64 GB | ~4 GB allocated | 15-20% | **80-85% unused** |
| **Network** | High-speed Azure | 46 MB/sec (mongodump) | Moderate | Good utilization |

---

## 📊 **Current Performance Analysis**

### **StaffAvailability Masking Performance**
- **Processing Rate**: 400-600 docs/sec
- **Memory Usage**: 560-710 MB stable
- **CPU Usage**: Single-threaded processing
- **Batch Size**: 3,500 documents
- **Processing Mode**: Sequential, in-situ masking

### **Resource Bottlenecks Identified**

#### **🔴 Critical Underutilization**
1. **CPU**: Only 1-2 cores used out of 64 available (98% waste)
2. **Memory**: Only 4GB allocated out of 64GB available (94% waste)
3. **Processing**: Single-threaded sequential processing

#### **🟡 Moderate Inefficiencies**
1. **Batch Size**: Conservative 3,500 docs vs. potential for larger batches
2. **Network**: MongoDB connection pooling not maximized
3. **I/O**: Not utilizing parallel read/write operations

---

## 🚀 **Optimization Recommendations**

### **Priority 1: Parallel Processing (HIGH IMPACT)**

#### **Multi-Collection Parallel Execution**
```bash
# Current: Sequential execution
run_production_masker.bat      # 2+ hours
run_tasks_masker.bat          # 2.4 hours  
run_staffavailability_masker.bat # 2.1 hours
# Total: 6.5+ hours sequential

# Recommended: Parallel execution
# All three can run simultaneously
# Total: ~2.4 hours (longest collection duration)
# Time Savings: 60-65%
```

#### **Multi-Processing Within Single Collection**
```python
# Current configuration enhancement
PROCESSING_MAX_WORKERS=32  # Increase from current
PROCESSING_BATCH_SIZE=8000 # Increase from 3500
```

### **Priority 2: Memory Optimization (MEDIUM IMPACT)**

#### **Increase Memory Allocation**
```json
// Current config
"batch_size": {"initial": 3500, "min": 1000, "max": 5000}

// Recommended config (with 64GB available)
"batch_size": {"initial": 10000, "min": 5000, "max": 20000}
"memory_allocation": "16GB",  // 25% of total RAM
"worker_memory": "512MB"      // Per worker process
```

#### **Memory-Optimized Processing**
```python
# Recommended memory settings
PROCESSING_MEMORY_TARGET=16GB    # 25% of total RAM
WORKER_MEMORY_LIMIT=512MB        # Per worker
BATCH_MEMORY_LIMIT=2GB           # Per batch processing
```

### **Priority 3: Network & I/O Optimization (MEDIUM IMPACT)**

#### **Connection Pool Optimization**
```json
"connection": {
    "max_pool_size": 200,        // Increase from 100
    "min_pool_size": 50,         // Increase from 10
    "worker_connections": 8,     // Per worker thread
    "connection_timeout_ms": 10000 // Reduce timeout
}
```

### **Priority 4: Batch Size Optimization (LOW-MEDIUM IMPACT)**

#### **Dynamic Batch Sizing**
```python
# Adaptive batch sizing based on document complexity
def calculate_optimal_batch_size(phi_field_count, avg_doc_size):
    base_size = 10000
    if phi_field_count > 5:
        return base_size // 2  # Smaller batches for complex docs
    elif phi_field_count < 3:
        return base_size * 2   # Larger batches for simple docs
    return base_size
```

---

## 📈 **Performance Improvement Projections**

### **Current Performance Baseline**
| Collection | Documents | Current Rate | Current Duration |
|------------|-----------|--------------|------------------|
| StaffAvailability | 3.76M | 500 docs/sec | 2.1 hours |
| Tasks | 4.30M | ~500 docs/sec | 2.4 hours |
| Container | Unknown | ~500 docs/sec | TBD |

### **Optimized Performance Projections**

#### **Scenario 1: Parallel Collections Only**
| Collection | Documents | Rate | Duration | Improvement |
|------------|-----------|------|----------|-------------|
| **All Collections** | Combined | Same rate | 2.4 hours | **65% time reduction** |

#### **Scenario 2: Memory + Batch Optimization**
| Collection | Documents | Rate | Duration | Improvement |
|------------|-----------|------|----------|-------------|
| StaffAvailability | 3.76M | 1,200 docs/sec | 52 minutes | **75% time reduction** |
| Tasks | 4.30M | 1,200 docs/sec | 60 minutes | **75% time reduction** |

#### **Scenario 3: Full Optimization (Recommended)**
| Collection | Documents | Rate | Duration | Improvement |
|------------|-----------|------|----------|-------------|
| **All Collections** | Combined | 2,000+ docs/sec | 35-45 minutes | **85% time reduction** |

---

## 🔧 **Implementation Plan**

### **Phase 1: Immediate Wins (1-2 days)**
1. **✅ Parallel Collection Execution**
   - Run all three collections simultaneously
   - Monitor resource usage
   - Expected: 65% time reduction

2. **📝 Increase Batch Sizes**
   ```json
   "batch_size": {"initial": 8000, "min": 4000, "max": 15000}
   ```

3. **📝 Optimize Connection Pools**
   ```json
   "max_pool_size": 200,
   "min_pool_size": 50
   ```

### **Phase 2: Memory Optimization (3-5 days)**
1. **🔧 Multi-Processing Implementation**
   ```python
   # Add to masking.py
   import multiprocessing as mp
   WORKER_COUNT = min(32, mp.cpu_count())
   ```

2. **📝 Memory Configuration**
   ```json
   "processing": {
       "max_workers": 32,
       "worker_memory_mb": 512,
       "total_memory_gb": 16
   }
   ```

### **Phase 3: Advanced Optimization (1-2 weeks)**
1. **⚡ Asynchronous Processing**
2. **📊 Dynamic Batch Sizing**
3. **🔄 Pipeline Optimization**

---

## 🎯 **Expected Outcomes**

### **Resource Utilization Targets**
| Resource | Current | Target | Improvement |
|----------|---------|--------|-------------|
| **CPU Usage** | 10-15% | 40-60% | 4x increase |
| **Memory Usage** | 15-20% | 25-35% | 2x increase |
| **Processing Speed** | 500 docs/sec | 2000+ docs/sec | 4x increase |
| **Total Duration** | 6.5+ hours | <1 hour | 6.5x improvement |

### **Business Impact**
- **Time Savings**: 85% reduction in processing time
- **Resource Efficiency**: 4x better hardware utilization
- **Scalability**: Can handle larger datasets without hardware upgrades
- **Parallel Capability**: Multiple collections simultaneously
- **Maintenance Windows**: Reduced from 6+ hours to <1 hour

---

## ⚠️ **Implementation Considerations**

### **Risk Mitigation**
1. **Memory Monitoring**: Watch for memory leaks with increased allocation
2. **Database Load**: Monitor MongoDB performance under increased load
3. **Network Saturation**: Ensure network can handle increased throughput
4. **Testing**: Implement changes incrementally with thorough testing

### **Rollback Plan**
- Keep current configuration files as backup
- Implement gradual increases in batch sizes and workers
- Monitor performance metrics continuously
- Have ability to reduce workers/batches if issues occur

---

## 📋 **Next Steps**

### **Week 1: Quick Wins**
- [ ] Enable parallel collection execution
- [ ] Increase batch sizes to 8,000
- [ ] Optimize connection pools
- [ ] Monitor and document improvements

### **Week 2: Memory Optimization**
- [ ] Implement multi-processing support
- [ ] Increase memory allocation to 16GB
- [ ] Test with 32 worker processes
- [ ] Performance benchmarking

### **Week 3: Fine-tuning**
- [ ] Optimize based on Week 1-2 results
- [ ] Implement dynamic batch sizing
- [ ] Create automated performance monitoring
- [ ] Document final configuration

---

*Analysis Date: August 20, 2025*  
*Baseline: StaffAvailability masking performance*  
*Target: 85% performance improvement through full optimization*
