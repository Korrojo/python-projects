# Performance Tracking and Monitoring

The Performance Tracking system provides comprehensive monitoring and reporting of the PHI masking pipeline's
performance. It tracks both system resource usage (CPU, memory, disk I/O) and phase-by-phase execution timing, enabling
detailed analysis and optimization of masking operations.

## Features

- **Phase-by-Phase Tracking**: Monitor individual stages of the masking workflow
- **Resource Monitoring**: Background tracking of CPU, memory, and disk I/O
- **Context Manager Support**: Automatic phase start/end with Python context managers
- **Detailed Reporting**: JSON reports with phase statistics and resource metrics
- **Metadata Support**: Attach custom metadata to phases for additional context
- **Multiple Phase Instances**: Track the same phase multiple times (e.g., batch processing)
- **Human-Readable Formatting**: Duration formatting in hours, minutes, seconds
- **Performance Summary Logging**: Console output with phase breakdowns

## Core Concepts

### Performance Monitor

The `PerformanceMonitor` class is the central component for tracking performance metrics. It provides:

1. **Background Resource Monitoring**: Optional thread that samples CPU, memory, and disk I/O at regular intervals
1. **Phase Tracking**: Start/stop tracking for named phases with metadata
1. **Report Generation**: Create comprehensive JSON reports with all performance data
1. **Summary Logging**: Human-readable console output for quick analysis

### Phase Tracking

A **phase** represents a logical step in the masking workflow. Examples include:

- Database Connection
- Document Query
- Document Masking
- Document Insertion
- Index Creation

Each phase tracks:

- Start time and timestamp
- End time and timestamp
- Duration in seconds
- Optional metadata (e.g., batch size, document count)
- Optional result metadata (e.g., documents processed, errors encountered)

## Usage

### Basic Setup

```python
from src.utils.performance_monitor import PerformanceMonitor

# Initialize the monitor
monitor = PerformanceMonitor(logger=your_logger)

# Optional: Start background resource monitoring
monitor.start_monitoring(interval=5.0)  # Sample every 5 seconds
```

### Method 1: Manual Phase Tracking

Explicitly start and end phases:

```python
# Start a phase
monitor.start_phase("Database Connection", metadata={"uri": "mongodb://..."})

# Perform the operation
client = connect_to_database()

# End the phase
monitor.end_phase("Database Connection", result_metadata={"status": "success"})
```

### Method 2: Context Manager (Recommended)

Use the context manager for automatic phase tracking:

```python
# Phase automatically starts and ends
with monitor.phase("Document Query", metadata={"batch_size": 1000}):
    documents = collection.find(query).limit(1000)

# Phase ends automatically, even if an exception occurs
```

### Method 3: Nested Phases

Track sub-phases within larger operations:

```python
with monitor.phase("Batch Processing", metadata={"total_batches": 10}):
    for batch_num in range(10):
        with monitor.phase("Process Batch", metadata={"batch_num": batch_num}):
            # Process batch
            process_batch(batch_num)
```

This creates multiple instances of the "Process Batch" phase, one for each iteration.

### Complete Example

```python
from src.utils.performance_monitor import PerformanceMonitor
import logging

# Set up logging
logger = logging.getLogger("masking")

# Initialize monitor
monitor = PerformanceMonitor(logger=logger)
monitor.start_monitoring(interval=5.0)

try:
    # Connect to database
    with monitor.phase("Database Connection"):
        connector = MongoConnector(uri, database, collection)
        connector.connect()

    # Query documents
    with monitor.phase("Document Query", metadata={"limit": 10000}):
        cursor = connector.find(limit=10000)
        documents = list(cursor)

    # Mask documents in batches
    batch_size = 100
    total_batches = len(documents) // batch_size

    with monitor.phase("Masking Process", metadata={"total_docs": len(documents)}):
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i+batch_size]

            with monitor.phase("Mask Batch", metadata={"batch_num": i//batch_size}):
                masked_batch = [mask_document(doc) for doc in batch]

            with monitor.phase("Insert Batch", metadata={"batch_size": len(masked_batch)}):
                connector.bulk_insert(masked_batch)

finally:
    # Stop monitoring and generate report
    monitor.stop_monitoring()

    # Log summary to console
    monitor.log_phase_summary()

    # Generate JSON report
    report = monitor.generate_performance_report(
        output_file="reports/performance_report.json"
    )
```

## Performance Reports

### Report Structure

The `generate_performance_report()` method creates a JSON report with the following structure:

```json
{
  "report_timestamp": "2025-01-04T15:30:45",
  "total_runtime_seconds": 245.67,
  "total_runtime_formatted": "4m 5.67s",
  "resource_usage": {
    "average_cpu_percent": 45.2,
    "average_memory_percent": 62.8,
    "peak_cpu_percent": 89.5,
    "peak_memory_percent": 78.3,
    "samples_collected": 49
  },
  "phases": {
    "Database Connection": {
      "count": 1,
      "total_duration": 2.34,
      "average_duration": 2.34,
      "min_duration": 2.34,
      "max_duration": 2.34,
      "entries": [
        {
          "start_time": 1704380445.123,
          "start_timestamp": "2025-01-04T15:27:25",
          "end_time": 1704380447.463,
          "end_timestamp": "2025-01-04T15:27:27",
          "duration_seconds": 2.34,
          "metadata": {"uri": "mongodb://..."},
          "result_metadata": {"status": "success"}
        }
      ]
    },
    "Document Query": {
      "count": 1,
      "total_duration": 15.67,
      "average_duration": 15.67,
      "min_duration": 15.67,
      "max_duration": 15.67,
      "entries": [...]
    },
    "Mask Batch": {
      "count": 100,
      "total_duration": 180.45,
      "average_duration": 1.80,
      "min_duration": 1.65,
      "max_duration": 2.15,
      "entries": [...]
    }
  },
  "phase_order": [
    "Database Connection",
    "Document Query",
    "Masking Process",
    "Mask Batch",
    "Insert Batch"
  ]
}
```

### Report Fields

| Field                     | Description                                        |
| ------------------------- | -------------------------------------------------- |
| `report_timestamp`        | When the report was generated (ISO format)         |
| `total_runtime_seconds`   | Total execution time in seconds                    |
| `total_runtime_formatted` | Human-readable duration (e.g., "2h 15m 30s")       |
| `resource_usage`          | CPU, memory statistics from background monitoring  |
| `phases`                  | Dictionary of phase statistics keyed by phase name |
| `phase_order`             | List of phases in execution order                  |

### Phase Statistics

For each phase:

| Field              | Description                                       |
| ------------------ | ------------------------------------------------- |
| `count`            | Number of times this phase executed               |
| `total_duration`   | Sum of all durations for this phase               |
| `average_duration` | Mean duration across all instances                |
| `min_duration`     | Fastest execution of this phase                   |
| `max_duration`     | Slowest execution of this phase                   |
| `entries`          | List of individual phase executions with metadata |

## Console Output

### Phase Summary

The `log_phase_summary()` method outputs a formatted summary to the console:

```
======================================================================
Performance Phase Summary
======================================================================
Total Runtime: 4m 5.67s

Phase: Database Connection
  Count: 1
  Total Duration: 2.34s
  Average Duration: 2.34s
  Min Duration: 2.34s
  Max Duration: 2.34s

Phase: Document Query
  Count: 1
  Total Duration: 15.67s
  Average Duration: 15.67s
  Min Duration: 15.67s
  Max Duration: 15.67s

Phase: Mask Batch
  Count: 100
  Total Duration: 3m 0.45s
  Average Duration: 1.80s
  Min Duration: 1.65s
  Max Duration: 2.15s

Phase: Insert Batch
  Count: 100
  Total Duration: 1m 42.21s
  Average Duration: 1.02s
  Min Duration: 0.95s
  Max Duration: 1.25s

======================================================================
```

## Integration with Masking Workflow

### Masking Pipeline Example

Here's how to integrate performance tracking into the main masking pipeline:

```python
# In masking.py or your main masking script
from src.utils.performance_monitor import PerformanceMonitor

def run_masking(config, collection_name):
    """Run masking with performance tracking."""
    logger = setup_logging()
    monitor = PerformanceMonitor(logger=logger)

    # Start background monitoring
    monitor.start_monitoring(interval=5.0)

    try:
        # Initialize connections
        with monitor.phase("Initialize Connections"):
            source_connector = MongoConnector(
                config.source_uri,
                config.source_db,
                collection_name
            )
            source_connector.connect()

            dest_connector = MongoConnector(
                config.dest_uri,
                config.dest_db,
                f"{collection_name}_masked"
            )
            dest_connector.connect()

        # Count documents
        with monitor.phase("Count Documents"):
            total_docs = source_connector.count_documents()
            logger.info(f"Processing {total_docs} documents")

        # Process in batches
        batch_size = config.batch_size
        processed = 0

        with monitor.phase("Masking Pipeline", metadata={"total_docs": total_docs}):
            for batch_num, batch_start in enumerate(range(0, total_docs, batch_size)):
                # Fetch batch
                with monitor.phase("Fetch Batch", metadata={"batch_num": batch_num}):
                    cursor = source_connector.find(
                        skip=batch_start,
                        limit=batch_size
                    )
                    documents = list(cursor)

                # Mask batch
                with monitor.phase("Mask Batch", metadata={"batch_num": batch_num, "batch_size": len(documents)}):
                    masker = DocumentMasker(config.masking_rules)
                    masked_docs = [masker.mask(doc) for doc in documents]

                # Insert batch
                with monitor.phase("Insert Batch", metadata={"batch_num": batch_num}):
                    dest_connector.bulk_insert(masked_docs)

                processed += len(documents)
                logger.info(f"Processed {processed}/{total_docs} documents")

        # Create indexes
        with monitor.phase("Create Indexes"):
            create_indexes(dest_connector)

        logger.info("Masking completed successfully")

    finally:
        # Stop monitoring
        monitor.stop_monitoring()

        # Log summary
        monitor.log_phase_summary()

        # Generate report
        report_file = f"reports/masking_performance_{collection_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        monitor.generate_performance_report(output_file=report_file)
        logger.info(f"Performance report saved to {report_file}")
```

### Checkpoint-Based Processing

For checkpoint-based masking (resumable operations):

```python
def run_masking_with_checkpoints(config, collection_name):
    """Run masking with checkpoints and performance tracking."""
    monitor = PerformanceMonitor(logger=logger)
    monitor.start_monitoring()

    try:
        # Load checkpoint
        with monitor.phase("Load Checkpoint"):
            checkpoint = load_checkpoint(collection_name)
            start_offset = checkpoint.get("offset", 0)

        # Resume from checkpoint
        with monitor.phase("Masking Pipeline", metadata={"resumed_from": start_offset}):
            for batch_num, offset in enumerate(range(start_offset, total_docs, batch_size)):
                with monitor.phase("Process Batch", metadata={"offset": offset}):
                    # Process batch
                    process_batch(offset, batch_size)

                # Save checkpoint
                with monitor.phase("Save Checkpoint"):
                    save_checkpoint(collection_name, offset + batch_size)

    finally:
        monitor.stop_monitoring()
        monitor.log_phase_summary()
        monitor.generate_performance_report(
            output_file=f"reports/checkpoint_masking_{collection_name}.json"
        )
```

## API Reference

### PerformanceMonitor Class

#### `__init__(logger=None)`

Initialize the performance monitor.

**Args:**

- `logger`: Optional logger instance (defaults to module logger)

#### `start_monitoring(interval=5.0)`

Start background resource monitoring thread.

**Args:**

- `interval`: Monitoring interval in seconds (default: 5.0)

#### `stop_monitoring()`

Stop background monitoring thread.

#### `start_phase(phase_name, metadata=None)`

Start tracking a performance phase.

**Args:**

- `phase_name`: Name of the phase (e.g., "Database Connection")
- `metadata`: Optional dictionary of metadata for this phase

**Example:**

```python
monitor.start_phase("Document Query", metadata={"limit": 1000})
```

#### `end_phase(phase_name=None, result_metadata=None)`

End tracking a performance phase.

**Args:**

- `phase_name`: Name of the phase to end (uses current phase if None)
- `result_metadata`: Optional dictionary of result metadata

**Example:**

```python
monitor.end_phase("Document Query", result_metadata={"docs_found": 850})
```

#### `phase(phase_name, metadata=None)` [Context Manager]

Context manager for automatic phase tracking.

**Args:**

- `phase_name`: Name of the phase
- `metadata`: Optional metadata dictionary

**Example:**

```python
with monitor.phase("Mask Documents", metadata={"count": 100}):
    # Masking code here
    pass
```

#### `get_phase_summary()`

Get summary statistics for all tracked phases.

**Returns:** Dictionary with phase statistics

- `count`: Number of executions
- `total_duration`: Sum of all durations
- `average_duration`: Mean duration
- `min_duration`: Minimum duration
- `max_duration`: Maximum duration
- `entries`: List of individual executions

**Example:**

```python
summary = monitor.get_phase_summary()
for phase_name, stats in summary.items():
    print(f"{phase_name}: {stats['average_duration']:.2f}s avg")
```

#### `generate_performance_report(output_file=None)`

Generate comprehensive performance report.

**Args:**

- `output_file`: Optional path to save report as JSON

**Returns:** Performance report dictionary

**Example:**

```python
report = monitor.generate_performance_report(
    output_file="reports/performance_20250104.json"
)
print(f"Total runtime: {report['total_runtime_formatted']}")
```

#### `log_phase_summary()`

Log a human-readable summary of all tracked phases to console.

**Example:**

```python
monitor.log_phase_summary()
```

#### `calculate_throughput(doc_count, elapsed=None)`

Calculate and log processing throughput.

**Args:**

- `doc_count`: Number of documents processed
- `elapsed`: Elapsed time in seconds (uses total runtime if None)

**Returns:** Throughput in documents/second

**Example:**

```python
throughput = monitor.calculate_throughput(10000)
# Logs: "Processed 10000 documents in 245.67 seconds"
# Logs: "Throughput: 40.71 documents/second"
```

## Best Practices

### 1. Use Context Managers

Always prefer the `phase()` context manager over manual `start_phase()`/`end_phase()` calls:

```python
# Good
with monitor.phase("Mask Documents"):
    mask_documents()

# Avoid (unless you need fine-grained control)
monitor.start_phase("Mask Documents")
mask_documents()
monitor.end_phase("Mask Documents")
```

### 2. Add Meaningful Metadata

Include relevant metadata to make reports more useful:

```python
with monitor.phase("Process Batch", metadata={
    "batch_num": batch_num,
    "batch_size": len(batch),
    "collection": collection_name,
    "total_phi_fields": len(phi_fields)
}):
    process_batch(batch)
```

### 3. Track at Appropriate Granularity

Balance detail with overhead:

```python
# Good - track major phases
with monitor.phase("Masking Pipeline"):
    for batch in batches:
        with monitor.phase("Process Batch"):
            for doc in batch:
                mask_document(doc)  # Don't track individual docs

# Avoid - too granular, excessive overhead
with monitor.phase("Masking Pipeline"):
    for doc in all_documents:
        with monitor.phase("Mask Single Document"):  # Too many phases!
            mask_document(doc)
```

### 4. Always Stop Monitoring

Use try/finally to ensure monitoring is stopped and reports are generated:

```python
monitor = PerformanceMonitor(logger)
monitor.start_monitoring()

try:
    # Your masking code
    run_masking()
finally:
    monitor.stop_monitoring()
    monitor.log_phase_summary()
    monitor.generate_performance_report("reports/performance.json")
```

### 5. Use Consistent Phase Names

Maintain consistent naming across your codebase:

```python
# Good - consistent naming
PHASE_DB_CONNECT = "Database Connection"
PHASE_QUERY_DOCS = "Document Query"
PHASE_MASK_BATCH = "Mask Batch"

with monitor.phase(PHASE_DB_CONNECT):
    connect()
```

### 6. Include Result Metadata

Add result metadata when ending phases to track success/failure:

```python
with monitor.phase("Insert Batch"):
    try:
        result = connector.bulk_insert(documents)
        monitor.end_phase(result_metadata={
            "status": "success",
            "inserted": len(documents)
        })
    except Exception as e:
        monitor.end_phase(result_metadata={
            "status": "failed",
            "error": str(e)
        })
        raise
```

## Performance Analysis

### Analyzing Reports

Use the JSON report to identify bottlenecks:

```python
import json

# Load report
with open("reports/performance_report.json") as f:
    report = json.load(f)

# Find slowest phases
phases = report["phases"]
sorted_phases = sorted(
    phases.items(),
    key=lambda x: x[1]["total_duration"],
    reverse=True
)

print("Slowest phases:")
for phase_name, stats in sorted_phases[:5]:
    print(f"  {phase_name}: {stats['total_duration']:.2f}s total")

# Find phases with high variance
for phase_name, stats in phases.items():
    if stats["count"] > 1:
        variance = stats["max_duration"] - stats["min_duration"]
        if variance > stats["average_duration"] * 0.5:  # >50% variance
            print(f"High variance in {phase_name}: {variance:.2f}s")
```

### Command-Line Analysis

Use `jq` to analyze reports from the command line:

```bash
# Get total runtime
cat reports/performance_report.json | jq '.total_runtime_formatted'

# List phases by total duration
cat reports/performance_report.json | jq '.phases | to_entries | sort_by(.value.total_duration) | reverse | .[] | {phase: .key, duration: .value.total_duration}'

# Get average CPU and memory usage
cat reports/performance_report.json | jq '.resource_usage | {avg_cpu, avg_memory}'

# Find slowest batch
cat reports/performance_report.json | jq '.phases["Mask Batch"].entries | max_by(.duration_seconds)'
```

## Troubleshooting

### High Memory Usage

**Symptom**: System becomes slow or crashes during monitoring

**Causes**:

- Too many phase entries (tracking too many small operations)
- Large metadata dictionaries
- Background monitoring samples accumulating

**Solutions**:

1. Reduce phase tracking granularity
1. Minimize metadata size
1. Increase monitoring interval: `monitor.start_monitoring(interval=10.0)`
1. Periodically generate reports and reset: `monitor.generate_performance_report(); monitor.phases.clear()`

### Missing Phase Data

**Symptom**: Phases don't appear in report or have zero duration

**Causes**:

- Phase not ended before report generation
- Exception occurred before `end_phase()` call
- Typo in phase name between start/end

**Solutions**:

1. Always use context managers: `with monitor.phase("name"):`
1. Check for exceptions interrupting phase tracking
1. Verify phase names match exactly

### Background Monitoring Not Working

**Symptom**: No resource usage data in reports

**Causes**:

- `start_monitoring()` not called
- Monitoring stopped before report generation
- psutil not installed

**Solutions**:

1. Call `monitor.start_monitoring()` before operations
1. Ensure `stop_monitoring()` is in finally block
1. Install psutil: `pip install psutil`

### Report Generation Fails

**Symptom**: `generate_performance_report()` raises exception

**Causes**:

- Invalid output file path
- Permission denied on report directory
- Phase data contains non-serializable objects

**Solutions**:

1. Ensure report directory exists: `os.makedirs("reports", exist_ok=True)`
1. Check write permissions on directory
1. Use only JSON-serializable data in metadata

## Related Documentation

- [Masking Validation](MASKING_VALIDATION.md) - Validating masking results
- [Test Data Export](TEST_DATA_EXPORT.md) - Exporting PHI-rich test data
- [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) - Testing infrastructure overview

## Examples Repository

See `examples/performance_tracking_examples.py` for complete working examples:

- Basic phase tracking
- Nested phase tracking
- Checkpoint-based processing with tracking
- Multi-collection masking with tracking
- Performance report analysis scripts
