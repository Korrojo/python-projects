# Project Logging Standard

## Purpose

This document defines the **unified logging format** for the MongoDB PHI Masker project. All scripts (Python and Bash)
MUST follow this standard to ensure:

1. **Consistency** across the codebase
1. **Easy parsing** for log aggregation tools
1. **Professional appearance**
1. **Debugging efficiency**

______________________________________________________________________

## Standard Format

```
YYYY-MM-DD HH:MM:SS | LEVEL | message
```

**Example:**

```
2025-11-06 14:31:39 | INFO | Processing collection: Patients
2025-11-06 14:31:40 | ERROR | Connection failed to mongodb://localhost:27017
2025-11-06 14:31:41 | SUCCESS | Masking completed: 100 documents
```

______________________________________________________________________

## Log Levels

Use these levels consistently:

- **INFO**: Normal operational messages
- **WARNING**: Warning messages (non-fatal issues)
- **ERROR**: Error messages (failures)
- **SUCCESS**: Success messages (for bash scripts, use INFO in Python)
- **DEBUG**: Debug-level messages (development only)

______________________________________________________________________

## Python Implementation

### Using logging module:

```python
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/operation/timestamp_operation.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)
logger.info("This is an info message")
logger.warning("This is a warning")
logger.error("This is an error")
```

### For logging.Formatter (when handlers are separate):

```python
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
```

______________________________________________________________________

## Bash Implementation

### Logging functions:

```bash
log_info() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}${timestamp} | INFO | ${NC}$1"
}

log_success() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}${timestamp} | SUCCESS | ${NC}$1"
}

log_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}${timestamp} | ERROR | ${NC}$1"
}

log_warning() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}${timestamp} | WARNING | ${NC}$1"
}
```

### Strip ANSI colors from log files:

```bash
exec > >(tee >(sed 's/\x1b\[[0-9;]*m//g' >> "$LOG_FILE"))
exec 2>&1
```

______________________________________________________________________

## Log File Naming Convention

### Format:

```
logs/<operation>/<timestamp>_<operation>_<subject>.log
```

### Examples:

```
logs/backup/20251106_143139_backup_Patients.log
logs/restore/20251106_143500_restore_Patients.log
logs/masking/20251106_144000_mask_Patients.log
logs/test_data/20251106_142607_Patients.log
```

### Directory structure:

```
logs/
├── backup/
├── restore/
├── masking/
├── test_data/
├── verification/
└── migration/
```

______________________________________________________________________

## What NOT to do

❌ **DON'T** use different formats in the same project:

```
2025-11-06 14:31:25,644 - __main__ - INFO - message  ❌ (includes module name, milliseconds)
INFO: message                                         ❌ (no timestamp)
[2025-11-06 14:31:25] INFO: message                   ❌ (brackets around timestamp)
```

❌ **DON'T** include module names in the format:

```
2025-11-06 14:31:25 - src.core.masker - INFO - message  ❌
```

File path in log file name is sufficient.

❌ **DON'T** include milliseconds:

```
2025-11-06 14:31:25,644 | INFO | message  ❌
```

Second-level precision is sufficient for operational logs.

______________________________________________________________________

## Summary Statistics

All operational scripts should include a summary section at the end of logs:

```
======================================================================
Operation Complete!
======================================================================
Documents processed: 100
Elapsed time: 0.12s
Throughput: 810 docs/sec
Errors: 0
======================================================================
```

This should be **both printed to terminal AND logged to file**.

______________________________________________________________________

## Updating Existing Scripts

When updating old scripts to use this standard:

1. Search for `logging.basicConfig` or `logging.Formatter`
1. Replace format string with: `"%(asctime)s | %(levelname)s | %(message)s"`
1. Add datefmt: `datefmt="%Y-%m-%d %H:%M:%S"`
1. Ensure summary statistics are logged (not just printed)

______________________________________________________________________

## Enforcement

- All new scripts MUST follow this standard
- All modified scripts SHOULD be updated to this standard
- Code reviews MUST check for logging format consistency
