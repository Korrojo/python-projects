"""Index utilization module - analyze index usage statistics."""

from datetime import datetime
from pathlib import Path
from typing import Any

import csv


def gather_index_utilization(db: Any, collection_name: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Gather index utilization statistics for a collection.

    Uses MongoDB's $indexStats aggregation to analyze index usage.

    Args:
        db: MongoDB database instance
        collection_name: Name of the collection to analyze

    Returns:
        Tuple of (utilization_data, index_sizes)
        - utilization_data: List of dicts with index usage info
        - index_sizes: Dict mapping index names to sizes in bytes
    """
    collection = db[collection_name]

    # Get index sizes using collStats
    index_sizes = {}
    try:
        stats = db.command("collStats", collection_name)
        index_sizes = stats.get("indexSizes", {})
    except Exception as e:
        # Log warning but continue without sizes
        print(f"⚠️  Warning: Could not get index sizes for {collection_name}: {e}")

    # Aggregation pipeline to gather index statistics
    pipeline = [
        {"$indexStats": {}},
        {
            "$project": {
                "indexName": "$name",
                "since": "$accesses.since",
                "ops": "$accesses.ops",
                "keys": {"$objectToArray": "$spec.key"},
            }
        },
        {"$unwind": "$keys"},
        {
            "$group": {
                "_id": "$indexName",
                "ops": {"$first": "$ops"},
                "since": {"$first": "$since"},
                "keys": {"$push": "$keys.k"},
            }
        },
        # Sort by ops descending (most used first)
        {"$sort": {"ops": -1}},
    ]

    try:
        utilization_data = list(collection.aggregate(pipeline))
    except Exception as e:
        print(f"❌ Error gathering index stats for {collection_name}: {e}")
        utilization_data = []

    return utilization_data, index_sizes


def print_utilization(
    collection_name: str,
    utilization_data: list[dict[str, Any]],
    index_sizes: dict[str, int],
) -> None:
    """Print index utilization statistics to console.

    Args:
        collection_name: Name of the collection
        utilization_data: List of index utilization dictionaries
        index_sizes: Dict mapping index names to sizes in bytes
    """
    print(f"\n{'=' * 120}")
    print(f"Index Utilization for Collection: {collection_name}")
    print(f"{'=' * 120}\n")

    if not utilization_data:
        print("  No index statistics available (collection may be empty or $indexStats not supported)\n")
        return

    # Print header
    print(f"{'No.':<5} {'Index Name':<40} {'Operations':<15} {'Size (MB)':<12} {'Since':<12} {'Keys'}")
    print("-" * 120)

    # Print each index
    for idx, item in enumerate(utilization_data, 1):
        index_name = item["_id"]
        ops = item.get("ops", 0)
        since_date = item.get("since")
        keys = item.get("keys", [])

        # Format index size
        index_size_bytes = index_sizes.get(index_name, 0)
        if index_size_bytes:
            size_mb = f"{index_size_bytes / 1048576:.2f}"
        else:
            size_mb = "N/A"

        # Format since date
        if since_date:
            since_str = since_date.strftime("%Y-%m-%d")
        else:
            since_str = "N/A"

        # Format keys
        keys_str = ", ".join(keys)

        # Highlight unused indexes
        unused_marker = "⚠️  UNUSED" if ops == 0 else ""

        print(f"{idx:<5} {index_name:<40} {ops:<15,} {size_mb:<12} {since_str:<12} {keys_str} {unused_marker}")

    print("\n" + "=" * 120)
    print(f"\n📊 Summary for {collection_name}:")
    print(f"  Total Indexes: {len(utilization_data)}")
    print(f"  Unused Indexes: {sum(1 for item in utilization_data if item.get('ops', 0) == 0)}")
    print()


def export_utilization_to_csv(
    collection_name: str,
    utilization_data: list[dict[str, Any]],
    index_sizes: dict[str, int],
    output_dir: Path,
    database_name: str,
) -> Path:
    """Export index utilization statistics to CSV file.

    Args:
        collection_name: Name of the collection
        utilization_data: List of index utilization dictionaries
        index_sizes: Dict mapping index names to sizes in bytes
        output_dir: Directory to save the CSV file
        database_name: Name of the database

    Returns:
        Path to the created CSV file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"index_utilization_{database_name}_{collection_name}_{timestamp}.csv"
    csv_path = output_dir / csv_filename

    # Determine max number of keys for column headers
    max_keys = max(len(item.get("keys", [])) for item in utilization_data) if utilization_data else 0

    # Build headers
    headers = ["No", "Index Name", "Operations", "Size (MB)", "Since"]
    for i in range(max_keys):
        headers.append(f"Key{i + 1}")

    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        # Write data rows
        for idx, item in enumerate(utilization_data, 1):
            index_name = item["_id"]
            ops = item.get("ops", 0)
            since_date = item.get("since")
            keys = item.get("keys", [])

            # Format index size
            index_size_bytes = index_sizes.get(index_name, 0)
            if index_size_bytes:
                size_mb = f"{index_size_bytes / 1048576:.2f}"
            else:
                size_mb = "N/A"

            # Format since date
            if since_date:
                since_str = since_date.strftime("%Y-%m-%d")
            else:
                since_str = "N/A"

            # Build row
            row = [idx, index_name, ops, size_mb, since_str]

            # Add keys
            for key in keys:
                row.append(key)

            # Pad with empty strings if needed
            while len(row) < len(headers):
                row.append("")

            writer.writerow(row)

    return csv_path
