# MongoDB Data Validation Projects - Best Practices Guide

**Audience**: Developers building data validation, migration, or comparison tools\
**Scope**: Repository-wide patterns
and practices\
**Last Updated**: October 24, 2025

______________________________________________________________________

## Table of Contents

1. [Project Structure](#1-project-structure)
1. [MongoDB Query Optimization](#2-mongodb-query-optimization)
1. [Statistics & Reporting](#3-statistics--reporting)
1. [Error Handling & Validation](#4-error-handling--validation)
1. [Performance Patterns](#5-performance-patterns)
1. [Testing Strategy](#6-testing-strategy)
1. [Code Organization](#7-code-organization)
1. [Common Patterns Library](#8-common-patterns-library)

______________________________________________________________________

## 1. Project Structure

### Standard Layout for Validation Projects

```
project_name/
├── README.md                    # Project overview, setup, usage
├── LESSONS_LEARNED.md          # Post-project insights
├── requirements.txt            # Dependencies
├── run.py                      # CLI entry point
├── config/
│   ├── __init__.py
│   └── settings.py             # Configuration classes
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── validator.py        # Main orchestration
│       ├── db_matcher.py       # Database queries
│       ├── comparator.py       # Comparison logic
│       ├── file_handler.py     # File I/O operations
│       └── models.py           # Data models
├── data/
│   ├── input/                  # Input files
│   └── output/                 # Generated output files
├── logs/                       # Log files
├── tests/
│   ├── test_validator.py
│   ├── test_comparator.py
│   └── fixtures/               # Test data
└── docs/
    ├── AGGREGATION_QUERIES.md  # MongoDB queries
    └── INDEX_CREATION.md       # Index documentation
```

### Key Principles

✅ **DO**:

- Separate source code into `src/` directory
- Use `data/input/` and `data/output/` for data files
- Include comprehensive README with examples
- Document MongoDB queries in separate markdown files
- Create LESSONS_LEARNED.md at project end

❌ **DON'T**:

- Mix source code with data files
- Store logs in project directory (use repo-level `logs/`)
- Hard-code file paths
- Skip documentation

______________________________________________________________________

## 2. MongoDB Query Optimization

### Pattern 1: Early Filtering Before Unwind

**Use Case**: Querying nested arrays in documents

**Anti-Pattern** (Slow):

```javascript
db.collection.aggregate([
    { $unwind: "$nestedArray" },           // Processes ALL documents
    { $match: { "nestedArray.field": value } }
])
```

**Best Practice** (Fast):

```javascript
db.collection.aggregate([
    { 
        $match: {
            "rootField": rootValue,         // Filter at root level FIRST
            "nestedArray.0": { $exists: true }  // Has elements
        }
    },
    { $unwind: "$nestedArray" },            // Only filtered documents
    { $match: { "nestedArray.field": value } }
])
```

**Impact**: 50-90% reduction in documents processed

______________________________________________________________________

### Pattern 2: Dynamic Date Range Filtering

**Use Case**: Input data spans limited time range, but database has years of data

**Implementation**:

```python
def calculate_date_range(input_rows: list[dict]) -> tuple[datetime, datetime]:
    """Calculate min/max dates from input data."""
    dates = [parse_date(row["date_field"]) for row in input_rows]
    dates = [d for d in dates if d]  # Remove None values

    if not dates:
        return None, None

    min_date = min(dates)
    max_date = max(dates) + timedelta(days=1)  # Buffer for inclusive comparison

    return min_date, max_date


# Apply to queries
min_date, max_date = calculate_date_range(rows)
pipeline = [
    {"$match": {"date_field": {"$gte": min_date, "$lt": max_date}}},
    # ... rest of pipeline
]
```

**Benefits**:

- One-time CSV scan (fast)
- Reduces MongoDB documents by 50-90%
- Automatic - no manual configuration
- Uses existing date indexes

______________________________________________________________________

### Pattern 3: Existence Checks for Arrays

**Use Case**: Many documents have empty arrays that still get unwound

**Best Practice**:

```javascript
{
    $match: {
        "arrayField.0": { $exists: true }  // Has at least one element
    }
}
```

**Impact**: 20-40% reduction in documents processed

______________________________________________________________________

### Pattern 4: Index Strategy

#### Required Indexes for Nested Array Queries

```javascript
// Primary lookup field (nested)
db.collection.createIndex(
    { "array.field": 1 },
    { 
        name: "IX_Array_Field",
        background: true  // Don't block production
    }
)

// Date range filter (root level)
db.collection.createIndex(
    { "dateField": 1 },
    { name: "IX_DateField", background: true }
)

// Composite index for common queries
db.collection.createIndex(
    { "dateField": 1, "statusField": 1 },
    { name: "IX_Date_Status", background: true }
)
```

#### Index Verification

```javascript
// Check indexes exist
db.collection.getIndexes()

// Verify index usage in query
db.collection.explain("executionStats").aggregate([...])

// Look for:
// - "indexName" in winning plan
// - totalDocsExamined close to nReturned
// - executionTimeMillis < 1000ms
```

______________________________________________________________________

### Pattern 5: Batch Queries with $in

**Anti-Pattern** (Slow):

```python
for row in rows:  # 2,000 queries!
    result = db.collection.find_one({"id": row["id"]})
```

**Best Practice** (Fast):

```python
def process_in_batches(rows: list[dict], batch_size: int = 100):
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        ids = [row["id"] for row in batch]

        # One query per batch
        results = db.collection.aggregate(
            [
                {"$match": {"id": {"$in": ids}}},
                # ... rest of pipeline
            ]
        )

        # Create lookup dictionary
        result_lookup = {r["id"]: r for r in results}

        # Process batch with results
        for row in batch:
            result = result_lookup.get(row["id"])
            # ... compare ...
```

**Impact**: 50-100x reduction in queries

**Batch Size Guidelines**:

- Small documents: 200-500 per batch
- Medium documents: 100-200 per batch
- Large documents: 50-100 per batch
- Consider network latency and memory

______________________________________________________________________

## 3. Statistics & Reporting

### Pattern 6: Hierarchical Statistics

**Use Case**: Multi-stage validation with different failure types

**Implementation**:

```python
class ValidationStats:
    def __init__(self):
        self.total_processed = 0
        self.skipped_invalid = 0

        # Primary matching
        self.primary_found = 0
        self.primary_not_found = 0

        # Results
        self.exact_match = 0
        self.field_mismatch = 0
        self.not_found_mismatch = 0

        # Secondary matching
        self.secondary_attempts = 0
        self.secondary_success = 0

    def log_summary(self):
        """Log hierarchical statistics."""
        total_valid = self.total_processed - self.skipped_invalid

        logger.info("Validation Statistics:")
        logger.info(f"  Total processed: {self.total_processed}")
        logger.info(f"  Skipped (invalid): {self.skipped_invalid}")
        logger.info("")
        logger.info(f"  Valid records: {total_valid}")
        logger.info(f"    ├─ Primary ID found: {self.primary_found}")
        logger.info(f"    │  ├─ Exact matches: {self.exact_match}")
        logger.info(f"    │  └─ Field mismatches: {self.field_mismatch}")
        logger.info(f"    └─ Primary ID not found: {self.primary_not_found}")
        logger.info(f"       ├─ Secondary matches: {self.secondary_success}")
        logger.info(f"       └─ Not found: {self.not_found_mismatch}")
        logger.info("")
        logger.info(f"  Total matches: {self.exact_match + self.secondary_success}")
        logger.info(
            f"  Total mismatches: {self.field_mismatch + self.not_found_mismatch}"
        )

        # Verify math
        expected = (
            self.exact_match
            + self.field_mismatch
            + self.not_found_mismatch
            + self.skipped_invalid
        )
        if expected == self.total_processed:
            logger.info(f"  ✓ Math verified: {expected} = {self.total_processed}")
        else:
            logger.warning(f"  ⚠ Math error: {expected} ≠ {self.total_processed}")
```

**Output Example**:

```
Validation Statistics:
  Total processed: 2127
  Skipped (invalid): 403

  Valid records: 1724
    ├─ Primary ID found: 1581
    │  ├─ Exact matches: 1457
    │  └─ Field mismatches: 124
    └─ Primary ID not found: 143
       ├─ Secondary matches: 0
       └─ Not found: 143

  Total matches: 1457
  Total mismatches: 267 (124 field + 143 not found)
  ✓ Math verified: 2127 = 2127
```

______________________________________________________________________

### Pattern 7: Math Verification

**Always verify statistics add up**:

```python
def verify_statistics(stats: dict) -> bool:
    """Verify statistics totals are consistent."""
    expected_total = stats["matches"] + stats["mismatches"] + stats["skipped"]

    actual_total = stats["processed"]

    if expected_total != actual_total:
        logger.warning(
            f"Statistics mismatch: " f"expected {expected_total}, got {actual_total}"
        )
        return False

    logger.info(f"✓ Math verified: {expected_total} = {actual_total}")
    return True
```

______________________________________________________________________

### Pattern 8: Distinguish Failure Types

**Track WHY validation failed**:

```python
class ValidationResult:
    def __init__(self):
        self.success = False
        self.failure_reason = None  # "not_found" | "field_mismatch" | "invalid_data"
        self.mismatched_fields = []
        self.comment = ""


# Track in statistics
if result.failure_reason == "not_found":
    stats["not_found_mismatch"] += 1
elif result.failure_reason == "field_mismatch":
    stats["field_mismatch"] += 1
    # Track which fields commonly mismatch
    for field in result.mismatched_fields:
        stats["field_mismatch_counts"][field] += 1
```

**Benefits**:

- Actionable insights (fix data vs fix code)
- Pattern detection (same field always mismatches)
- Better user communication

______________________________________________________________________

## 4. Error Handling & Validation

### Pattern 9: Validate Early, Fail Gracefully

**Required field validation**:

```python
def validate_required_fields(row: dict, required: list[str]) -> list[str]:
    """Return list of missing required fields."""
    missing = []
    for field in required:
        value = row.get(field, "").strip()
        if not value:
            missing.append(field)
    return missing


# Use in processing
missing = validate_required_fields(row, ["id", "date", "type"])
if missing:
    row["Missing Fields"] = ", ".join(missing)
    row["Comment"] = "Missing required fields - skipped"
    stats["skipped_invalid"] += 1
    continue  # Don't process, don't crash
```

**Key Principle**: Never crash on bad data. Skip gracefully and report exactly what's wrong.

______________________________________________________________________

### Pattern 10: Data Type Conversion with Error Handling

```python
def safe_int_conversion(value: Any, field_name: str) -> int | None:
    """Safely convert value to int, return None on failure."""
    try:
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            return int(value.strip())
        return None
    except (ValueError, TypeError) as e:
        logger.debug(f"Cannot convert {field_name}='{value}' to int: {e}")
        return None


# Use in code
patient_ref = safe_int_conversion(row.get("PatientRef"), "PatientRef")
if patient_ref is None:
    row["Comment"] = "Invalid PatientRef - must be numeric"
    stats["invalid_data"] += 1
    continue
```

______________________________________________________________________

### Pattern 11: Date Parsing with Multiple Formats

```python
from datetime import datetime
from typing import Optional


def parse_date_flexible(date_str: str) -> Optional[datetime]:
    """Try multiple date formats."""
    if not date_str or not date_str.strip():
        return None

    formats = [
        "%m/%d/%Y",  # 10/23/2025
        "%m/%d/%y",  # 10/23/25
        "%Y-%m-%d",  # 2025-10-23
        "%m-%d-%Y",  # 10-23-2025
    ]

    date_str = date_str.strip()

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    logger.debug(f"Cannot parse date: '{date_str}'")
    return None
```

______________________________________________________________________

## 5. Performance Patterns

### Pattern 12: Progress Reporting

```python
def process_with_progress(
    rows: list[dict], batch_size: int = 100, log_frequency: int = 100
):
    """Process with periodic progress updates."""
    total = len(rows)
    start_time = time.time()

    for i in range(0, total, batch_size):
        batch = rows[i : i + batch_size]

        # Process batch
        process_batch(batch)

        # Log progress
        processed = min(i + batch_size, total)
        if processed % log_frequency == 0 or processed == total:
            elapsed = time.time() - start_time
            rate = processed / elapsed
            remaining = (total - processed) / rate if rate > 0 else 0

            logger.info(
                f"Processed {processed}/{total} rows "
                f"({stats['matched']} matched, "
                f"{stats['mismatched']} mismatched) "
                f"[{elapsed:.0f}s elapsed, {remaining:.0f}s remaining]"
            )
```

______________________________________________________________________

### Pattern 13: Connection Pooling & Retry Logic

```python
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import time


class MongoConnection:
    def __init__(
        self, connection_string: str, max_retries: int = 3, retry_delay: float = 2.0
    ):
        self.connection_string = connection_string
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = None

    def query_with_retry(self, query_func, *args, **kwargs):
        """Execute query with retry logic."""
        for attempt in range(self.max_retries):
            try:
                return query_func(*args, **kwargs)
            except (ConnectionFailure, OperationFailure) as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Query failed after {self.max_retries} attempts: {e}")
                    raise

                wait_time = self.retry_delay * (2**attempt)  # Exponential backoff
                logger.warning(f"Query failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
```

______________________________________________________________________

### Pattern 14: Memory-Efficient Processing

**For large datasets**:

```python
def process_large_csv_streaming(file_path: Path, batch_size: int = 100):
    """Process CSV in batches without loading entire file."""
    import csv

    batch = []

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            batch.append(row)

            if len(batch) >= batch_size:
                process_batch(batch)
                batch = []  # Clear memory

        # Process remaining rows
        if batch:
            process_batch(batch)
```

______________________________________________________________________

## 6. Testing Strategy

### Pattern 15: Sample-Based Testing

```python
# In CLI
@click.option("--limit", type=int, help="Limit number of rows to process")
def main(input_file: str, limit: Optional[int] = None):
    rows = read_csv(input_file)

    if limit:
        rows = rows[:limit]
        logger.info(f"Limited processing to {limit} rows")

    validator.validate(rows)
```

**Testing Workflow**:

1. Smoke test: `--limit 10` (seconds)
1. Validation test: `--limit 100` (1-2 minutes)
1. Full run: no limit (only after above pass)

______________________________________________________________________

### Pattern 16: Test Data Fixtures

```python
# tests/fixtures/sample_data.py
def get_sample_csv_rows() -> list[dict]:
    """Sample CSV data for testing."""
    return [
        {"id": "123", "date": "10/23/2025", "time": "1:35 PM", "type": "Visit"},
        {"id": "456", "date": "10/24/2025", "time": "2:00 PM", "type": "Consult"},
    ]


def get_sample_mongo_docs() -> list[dict]:
    """Sample MongoDB documents for testing."""
    return [
        {
            "_id": "abc123",
            "appointmentId": 123,
            "date": datetime(2025, 10, 23),
            "time": "13:35:00",
            "type": "Visit",
        }
    ]
```

______________________________________________________________________

## 7. Code Organization

### Pattern 17: Configuration Management

```python
# config/settings.py
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DatabaseConfig:
    connection_string: str
    database_name: str
    collection_name: str
    batch_size: int = 100
    max_retries: int = 3


@dataclass
class ProcessingConfig:
    batch_size: int = 100
    log_frequency: int = 100
    case_sensitive: bool = False
    trim_strings: bool = True


@dataclass
class PathConfig:
    project_root: Path
    input_dir: Path
    output_dir: Path
    log_dir: Path


# Usage
config = DatabaseConfig(
    connection_string=os.getenv("MONGO_CONNECTION"),
    database_name="MyDatabase",
    collection_name="MyCollection",
)
```

______________________________________________________________________

### Pattern 18: Dependency Injection

```python
# Good: Dependencies injected
class Validator:
    def __init__(
        self,
        db_matcher: DatabaseMatcher,
        comparator: FieldComparator,
        file_handler: FileHandler,
    ):
        self.matcher = db_matcher
        self.comparator = comparator
        self.file_handler = file_handler

    def validate(self, input_path: Path):
        rows = self.file_handler.read_csv(input_path)
        # ... validation logic
```

**Benefits**:

- Easy to test (inject mocks)
- Easy to swap implementations
- Clear dependencies

______________________________________________________________________

## 8. Common Patterns Library

### Pattern 19: Primary + Fallback Matching

```python
def find_with_fallback(
    row: dict, primary_matcher: Callable, fallback_matcher: Callable
) -> tuple[dict | None, str]:
    """
    Try primary matching first, fallback to secondary.

    Returns: (result, match_method)
    """
    # Try primary
    result = primary_matcher(row)
    if result:
        return result, "primary"

    # Try fallback
    result = fallback_matcher(row)
    if result:
        return result, "fallback"

    return None, "not_found"


# Track which method worked
result, method = find_with_fallback(row, find_by_id, find_by_fields)
stats[f"{method}_matches"] += 1
```

______________________________________________________________________

### Pattern 20: Field-by-Field Comparison

```python
def compare_all_fields(
    source: dict,
    target: dict,
    field_mapping: dict[str, str],
    ignore_case: dict[str, bool] = None,
) -> tuple[bool, list[str]]:
    """
    Compare all fields between source and target.

    Returns: (all_match, list_of_mismatched_fields)
    """
    mismatched = []
    ignore_case = ignore_case or {}

    for source_field, target_field in field_mapping.items():
        source_val = str(source.get(source_field, "")).strip()
        target_val = str(target.get(target_field, "")).strip()

        # Case-insensitive comparison if configured
        if ignore_case.get(source_field, False):
            source_val = source_val.lower()
            target_val = target_val.lower()

        if source_val != target_val:
            mismatched.append(source_field)

    return len(mismatched) == 0, mismatched
```

______________________________________________________________________

## Quick Reference Checklist

### Before Starting a New Validation Project

- [ ] Review this guide and `appointment_comparison/LESSONS_LEARNED.md`
- [ ] Set up standard project structure
- [ ] Configure logging to repo-level `logs/` directory
- [ ] Plan statistics output format
- [ ] Identify required MongoDB indexes
- [ ] Design primary + fallback matching strategy
- [ ] Add `--limit` flag for testing with samples
- [ ] Implement batch processing from the start
- [ ] Add math verification to statistics

### During Development

- [ ] Test with 10 rows frequently
- [ ] Use MongoDB `explain()` to verify indexes
- [ ] Add early filtering before $unwind operations
- [ ] Calculate date ranges from input data
- [ ] Log progress every 100 records
- [ ] Track failure reasons separately
- [ ] Validate required fields before processing
- [ ] Handle missing data gracefully

### Before Production Deployment

- [ ] Test with 100 rows and verify results
- [ ] Check MongoDB query execution plans
- [ ] Verify indexes exist and are used
- [ ] Review statistics output for clarity
- [ ] Document MongoDB queries in markdown
- [ ] Add performance metrics to README
- [ ] Create example commands
- [ ] Test idempotency (run twice, same result)

### After Completion

- [ ] Create LESSONS_LEARNED.md document
- [ ] Document actual vs expected performance
- [ ] Note any data quality issues discovered
- [ ] List recommendations for similar projects
- [ ] Update this guide with new patterns learned

______________________________________________________________________

## MongoDB Quick Reference

### Check Index Usage

```javascript
db.collection.explain("executionStats").aggregate([...])
```

### Create Index

```javascript
db.collection.createIndex(
    { "field": 1 },
    { name: "IX_Field", background: true }
)
```

### Check Query Performance

```javascript
var start = Date.now();
db.collection.aggregate([...]);
print("Time:", Date.now() - start, "ms");
```

### Count Documents in Date Range

```javascript
db.collection.countDocuments({
    "dateField": {
        $gte: ISODate("2025-10-01"),
        $lt: ISODate("2025-11-01")
    }
})
```

______________________________________________________________________

## Additional Resources

- **MongoDB Aggregation Pipeline**: <https://www.mongodb.com/docs/manual/core/aggregation-pipeline/>
- **MongoDB Index Strategies**: <https://www.mongodb.com/docs/manual/indexes/>
- **Python Type Hints**: <https://docs.python.org/3/library/typing.html>
- **Pytest Documentation**: <https://docs.pytest.org/>

______________________________________________________________________

**Document Version**: 1.0\
**Last Updated**: October 24, 2025\
**Maintainer**: Development Team\
**Repository**:
ubiquityMongo_phiMasking
