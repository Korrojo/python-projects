"""Slow queries analyzer module - find and analyze slow operations."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any


def analyze_slow_queries(
    db: Any,
    threshold_ms: int = 100,
    collection_filter: str | None = None,
    operation_filter: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Analyze slow queries from system.profile collection.

    Args:
        db: MongoDB database instance
        threshold_ms: Minimum execution time in milliseconds
        collection_filter: Filter by collection (format: database.collection)
        operation_filter: Filter by operation type (query, update, delete, etc.)
        limit: Maximum number of results

    Returns:
        List of slow operation documents
    """
    # Build query
    query: dict[str, Any] = {"millis": {"$gte": threshold_ms}}

    if collection_filter:
        query["ns"] = collection_filter

    if operation_filter:
        query["op"] = operation_filter

    # Query system.profile
    try:
        profile_collection = db["system.profile"]

        # Get slow operations
        slow_ops = list(profile_collection.find(query).sort("millis", -1).limit(limit))  # Sort by slowest first

        # Extract and format relevant fields
        formatted_ops = []
        for op in slow_ops:
            formatted_op = {
                "timestamp": op.get("ts"),
                "operation": op.get("op", "N/A"),
                "namespace": op.get("ns", "N/A"),
                "millis": op.get("millis", 0),
                "client": op.get("client", "N/A"),
                "user": op.get("user", "N/A"),
                "plan_summary": op.get("planSummary", "N/A"),
                "docs_examined": op.get("docsExamined", 0),
                "keys_examined": op.get("keysExamined", 0),
                "n_returned": op.get("nreturned", op.get("nReturned", 0)),
                "command": str(op.get("command", {}))[:200],  # Truncate long commands
            }
            formatted_ops.append(formatted_op)

        return formatted_ops

    except Exception:
        # system.profile might not exist if profiling is not enabled
        return []


def print_slow_queries(slow_ops: list[dict[str, Any]], threshold: int) -> None:
    """Print slow queries to console.

    Args:
        slow_ops: List of slow operations
        threshold: Threshold used for filtering
    """
    print("\n" + "=" * 120)
    print(f"Slow Queries Analysis (>= {threshold}ms)")
    print("=" * 120)

    if not slow_ops:
        print("\n✅ No slow queries found! Your database is performing well.")
        print("\nNote: Make sure profiling is enabled:")
        print("  - Check profiling level: db.getProfilingLevel()")
        print("  - Enable profiling: db.setProfilingLevel(1)  // Slow queries only")
        print("  - Enable profiling: db.setProfilingLevel(2)  // All operations")
        print("\n" + "=" * 120 + "\n")
        return

    print(f"\n📊 Total slow operations found: {len(slow_ops)}")
    print("\n🐌 Top Slow Operations:")
    print("-" * 120)

    for i, op in enumerate(slow_ops[:20], 1):  # Show top 20
        print(f"\n{i}. {op['operation'].upper()} - {op['millis']}ms")
        print(f"   Namespace: {op['namespace']}")
        print(f"   Timestamp: {op['timestamp']}")
        print(f"   Plan: {op['plan_summary']}")
        print(f"   Examined: {op['docs_examined']} docs, {op['keys_examined']} keys | Returned: {op['n_returned']}")
        if op["client"] != "N/A":
            print(f"   Client: {op['client']}")
        if op["user"] != "N/A":
            print(f"   User: {op['user']}")

    if len(slow_ops) > 20:
        print(f"\n... and {len(slow_ops) - 20} more slow operations")
        print("   (See CSV export for full list)")

    # Summary statistics
    total_time = sum(op["millis"] for op in slow_ops)
    avg_time = total_time / len(slow_ops) if slow_ops else 0
    max_time = max((op["millis"] for op in slow_ops), default=0)

    print("\n📈 Statistics:")
    print(f"   Total execution time: {total_time:,}ms ({total_time / 1000:.2f}s)")
    print(f"   Average execution time: {avg_time:.2f}ms")
    print(f"   Maximum execution time: {max_time}ms")

    # Operation type breakdown
    op_types: dict[str, int] = {}
    for op in slow_ops:
        op_type = op["operation"]
        op_types[op_type] = op_types.get(op_type, 0) + 1

    print("\n📋 Operation Types:")
    for op_type, count in sorted(op_types.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(slow_ops)) * 100
        print(f"   {op_type}: {count} ({percentage:.1f}%)")

    print("\n" + "=" * 120 + "\n")


def export_slow_queries_to_csv(
    slow_ops: list[dict[str, Any]],
    output_dir: Path,
    database_name: str,
) -> Path:
    """Export slow queries to CSV file.

    Args:
        slow_ops: List of slow operations
        output_dir: Directory to save CSV
        database_name: Database name

    Returns:
        Path to created CSV file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"slow_queries_{database_name}_{timestamp}.csv"
    csv_path = output_dir / csv_filename

    headers = [
        "Timestamp",
        "Operation",
        "Namespace",
        "Duration (ms)",
        "Docs Examined",
        "Keys Examined",
        "Returned",
        "Plan Summary",
        "Client",
        "User",
        "Command",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        for op in slow_ops:
            writer.writerow(
                [
                    op["timestamp"],
                    op["operation"],
                    op["namespace"],
                    op["millis"],
                    op["docs_examined"],
                    op["keys_examined"],
                    op["n_returned"],
                    op["plan_summary"],
                    op["client"],
                    op["user"],
                    op["command"],
                ]
            )

    return csv_path
