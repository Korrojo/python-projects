# File Naming Conventions

**Standard patterns for output files, logs, and artifacts across all projects**

______________________________________________________________________

## Purpose

Consistent file naming ensures:

- ✅ Chronological sorting by default (files sort by date automatically)
- ✅ Easy identification of file type and purpose
- ✅ Simple automated cleanup (delete files older than X days)
- ✅ Clear provenance (which project, which database, which run)

______________________________________________________________________

## Standard Pattern

### Primary Format

**All timestamped output files MUST follow this pattern:**

```
YYYYMMDD_HHMMSS_<description>.<ext>
```

**Examples:**

```
20250127_143022_collection_stats_UbiquityProduction.csv
20250127_143022_app.log
20250127_143022_patient_export.json
20250127_143022_validation_report.xlsx
```

### Why Timestamp First?

**❌ Bad (timestamp at end):**

```
collection_stats_UbiquityProduction_20250127_143022.csv
collection_stats_UbiquityProduction_20250126_091523.csv
collection_stats_UbiquityDevelopment_20250127_143022.csv
```

**Problem:** Files don't sort chronologically. Latest files are scattered.

**✅ Good (timestamp first):**

```
20250126_091523_collection_stats_UbiquityProduction.csv
20250127_143022_collection_stats_UbiquityDevelopment.csv
20250127_143022_collection_stats_UbiquityProduction.csv
```

**Benefit:** Latest files appear at the bottom (or top if reverse sorted). Easy to find today's files.

______________________________________________________________________

## Implementation Guidelines

### In Python Code

```python
from datetime import datetime
from pathlib import Path

def generate_output_filename(description: str, database_name: str, extension: str) -> str:
    """Generate timestamped filename following repository standards.

    Args:
        description: File type/purpose (e.g., "collection_stats", "validation_report")
        database_name: Database name (if applicable)
        extension: File extension without dot (e.g., "csv", "json", "log")

    Returns:
        Filename following pattern: YYYYMMDD_HHMMSS_<description>_<database>.<ext>
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{description}_{database_name}.{extension}"

# Usage examples
csv_file = generate_output_filename("collection_stats", "UbiquityProduction", "csv")
# Result: 20250127_143022_collection_stats_UbiquityProduction.csv

log_file = generate_output_filename("app", "", "log").replace("__", "_")
# Result: 20250127_143022_app.log
```

### Log Files

**Pattern:** `YYYYMMDD_HHMMSS_<logtype>.log`

```python
from datetime import datetime
from pathlib import Path

# Generate log filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"{timestamp}_app.log"
log_path = Path("logs/my_project") / log_file
# Result: logs/my_project/20250127_143022_app.log
```

**Examples:**

- `20250127_143022_app.log` - Application log
- `20250127_143022_error.log` - Error log
- `20250127_143022_audit.log` - Audit log

### CSV Exports

**Pattern:** `YYYYMMDD_HHMMSS_<reporttype>_<context>.<ext>`

```python
from datetime import datetime

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Collection statistics
csv_file = f"{timestamp}_collection_stats_{database_name}.csv"

# Validation report
csv_file = f"{timestamp}_validation_report_{input_file_basename}.csv"

# Patient export
csv_file = f"{timestamp}_patient_data_export.csv"
```

**Examples:**

- `20250127_143022_collection_stats_UbiquityProduction.csv`
- `20250127_143022_validation_report_patients.csv`
- `20250127_143022_appointment_comparison_results.csv`

### JSON/Data Exports

**Pattern:** Same as CSV

```python
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
json_file = f"{timestamp}_export_{collection_name}.json"
# Result: 20250127_143022_export_Patients.json
```

______________________________________________________________________

## Special Cases

### Temporary Files

**Pattern:** `YYYYMMDD_HHMMSS_temp_<description>.<ext>`

```python
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
temp_file = f"{timestamp}_temp_processing.tmp"
# Result: 20250127_143022_temp_processing.tmp
```

### Archive Files

**Pattern:** `YYYYMMDD_HHMMSS_archive_<original_name>.<ext>`

```python
import shutil
from datetime import datetime
from pathlib import Path

def archive_file(file_path: Path, archive_dir: Path) -> Path:
    """Archive file with timestamp prefix."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archived_name = f"{timestamp}_archive_{file_path.name}"
    archive_path = archive_dir / archived_name
    shutil.copy2(file_path, archive_path)
    return archive_path
```

### Batch/Run Identifiers

When creating multiple files from a single run, use the same timestamp for all:

```python
from datetime import datetime

# Generate once at start of run
run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Use for all outputs
csv_file = f"{run_timestamp}_collection_stats_{db_name}.csv"
log_file = f"{run_timestamp}_app.log"
summary_file = f"{run_timestamp}_summary.txt"

# All files share same timestamp = easy to identify files from same run
```

______________________________________________________________________

## File Cleanup

### Automatic Cleanup Script Pattern

```python
from datetime import datetime, timedelta
from pathlib import Path

def cleanup_old_files(directory: Path, days_to_keep: int = 30, pattern: str = "*.csv"):
    """Remove files older than specified days.

    Args:
        directory: Directory to clean
        days_to_keep: Keep files from last N days
        pattern: File pattern to match (e.g., "*.csv", "*.log")
    """
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    cutoff_str = cutoff_date.strftime("%Y%m%d")

    for file_path in directory.glob(pattern):
        # Extract timestamp from filename (first 8 characters)
        if len(file_path.name) >= 8 and file_path.name[:8].isdigit():
            file_date_str = file_path.name[:8]
            if file_date_str < cutoff_str:
                print(f"Deleting old file: {file_path}")
                file_path.unlink()

# Usage
cleanup_old_files(
    directory=Path("data/output/my_project"),
    days_to_keep=30,
    pattern="*.csv"
)
```

______________________________________________________________________

## Migration Guide

### Converting Existing Projects

If you have a project with the old naming pattern, here's how to migrate:

**1. Update code that generates filenames:**

```python
# ❌ Old way (timestamp at end)
filename = f"collection_stats_{database_name}_{timestamp}.csv"

# ✅ New way (timestamp first)
filename = f"{timestamp}_collection_stats_{database_name}.csv"
```

**2. Update tests that check filenames:**

```python
# ❌ Old assertion
assert output_path.name.startswith("collection_stats_")

# ✅ New assertion (checks pattern)
assert "_collection_stats_" in output_path.name
assert output_path.name[0].isdigit()  # Starts with timestamp
```

**3. Update documentation:**

- Update README examples to show new pattern
- Add note explaining timestamp-first convention

**4. (Optional) Rename existing files:**

```bash
# Example: Rename existing CSV files
for file in data/output/my_project/collection_stats_*_20*.csv; do
    # Extract parts: collection_stats_DatabaseName_20250127_143022.csv
    # New format: 20250127_143022_collection_stats_DatabaseName.csv
    # (This is project-specific; adjust regex pattern as needed)
    newname=$(echo "$file" | sed -E 's/(.*)collection_stats_([^_]+)_([0-9]{8}_[0-9]{6})\.csv/\1\3_collection_stats_\2.csv/')
    mv "$file" "$newname"
done
```

______________________________________________________________________

## Common Mistakes

### ❌ Mistake 1: Timestamp at End

```python
# Wrong
filename = f"output_{database_name}_{timestamp}.csv"
# Problem: Doesn't sort chronologically
```

### ❌ Mistake 2: No Underscore Separators

```python
# Wrong
filename = f"{timestamp}collectionstats{database_name}.csv"
# Problem: Hard to parse, hard to read
```

### ❌ Mistake 3: Inconsistent Date Format

```python
# Wrong - Different projects use different formats
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Project A
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")        # Project B
# Problem: Inconsistent, harder to parse, doesn't sort correctly
```

### ❌ Mistake 4: Human-Readable but Not Sortable

```python
# Wrong
filename = f"Report_Jan_27_2025_2_30_PM.csv"
# Problem: Doesn't sort chronologically, inconsistent format
```

______________________________________________________________________

## Validation Checklist

When creating output files, verify:

- [ ] Timestamp is first: `YYYYMMDD_HHMMSS_<description>.<ext>`
- [ ] Timestamp format is `YYYYMMDD_HHMMSS` (no hyphens, no colons)
- [ ] Underscores separate all parts
- [ ] Description is clear and concise
- [ ] Extension is appropriate (.csv, .json, .log, etc.)
- [ ] Files sort chronologically when listed
- [ ] Tests verify the filename pattern
- [ ] Documentation shows correct examples

______________________________________________________________________

## Tools and Utilities

### Filename Pattern Validator

```python
import re
from pathlib import Path

def validate_filename_pattern(filename: str) -> bool:
    """Validate filename follows repository standard.

    Pattern: YYYYMMDD_HHMMSS_<description>.<ext>

    Returns:
        True if valid, False otherwise
    """
    pattern = r"^\d{8}_\d{6}_[a-z0-9_]+\.[a-z0-9]+$"
    return bool(re.match(pattern, filename.lower()))

# Usage
assert validate_filename_pattern("20250127_143022_collection_stats_prod.csv")  # Valid
assert not validate_filename_pattern("collection_stats_20250127_143022.csv")   # Invalid
```

### Extract Timestamp from Filename

```python
from datetime import datetime
from pathlib import Path

def extract_timestamp(filename: str) -> datetime:
    """Extract datetime from filename following repository standard.

    Args:
        filename: Filename following pattern YYYYMMDD_HHMMSS_<description>.<ext>

    Returns:
        datetime object

    Raises:
        ValueError: If filename doesn't match expected pattern
    """
    # Extract first 15 characters: YYYYMMDD_HHMMSS
    timestamp_str = filename[:15]
    return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

# Usage
file_path = Path("20250127_143022_collection_stats.csv")
timestamp = extract_timestamp(file_path.name)
print(f"File created: {timestamp}")
```

______________________________________________________________________

## Examples by Project Type

### MongoDB Statistics Tool

```
20250127_143022_collection_stats_UbiquityProduction.csv
20250127_143022_app.log
```

### Data Validator

```
20250127_143022_validation_report_patients.csv
20250127_143022_validation_errors.log
20250127_143022_validation_summary.json
```

### Data Exporter

```
20250127_143022_export_Patients.json
20250127_143022_export_Appointments.json
20250127_143022_export.log
```

### Report Generator

```
20250127_143022_monthly_report_January.xlsx
20250127_143022_report_generation.log
```

______________________________________________________________________

## Related Documentation

- [Repository Standards](../guides/REPOSITORY_STANDARDS.md) - Overall conventions
- [Testing Guide](../guides/TESTING_GUIDE.md) - How to test filename patterns
- [MongoDB Best Practices](MONGODB_VALIDATION_BEST_PRACTICES.md) - Data export patterns

______________________________________________________________________

## Enforcement

### In Code Reviews

Check that all new code follows this convention:

- ✅ Filenames use timestamp-first pattern
- ✅ Tests validate the pattern
- ✅ Documentation shows correct examples

### In Pre-Push Validation

(Future enhancement - not yet implemented)

______________________________________________________________________

**Last Updated:** 2025-01-27
