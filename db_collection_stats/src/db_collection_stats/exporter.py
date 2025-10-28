"""CSV export functionality for collection and index statistics."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from db_collection_stats.collector import CollectionStats


def export_to_csv(stats_list: List[CollectionStats], output_dir: Path, database_name: str) -> Path:
    """Export collection statistics to CSV file.

    Args:
        stats_list: List of CollectionStats to export
        output_dir: Directory to write CSV file
        database_name: Name of the database (used in filename)

    Returns:
        Path to the created CSV file

    Raises:
        IOError: If file writing fails
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp (timestamp first for chronological sorting)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_collection_stats_{database_name}.csv"
    output_path = output_dir / filename

    # Define CSV headers
    headers = [
        "collection_name",
        "document_count",
        "collection_size_bytes",
        "avg_document_size_bytes",
        "storage_size_bytes",
        "num_indexes",
        "total_index_size_bytes",
    ]

    # Write CSV file
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()

        for stats in stats_list:
            writer.writerow(stats.to_dict())

    return output_path


def format_bytes(bytes_value: int) -> str:
    """Format bytes into human-readable format.

    Args:
        bytes_value: Size in bytes

    Returns:
        Human-readable string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def print_summary(stats_list: List[CollectionStats], database_name: str) -> None:
    """Print a summary of collection statistics to console.

    Args:
        stats_list: List of CollectionStats to summarize
        database_name: Name of the database
    """
    print("\n" + "=" * 80)
    print(f"Collection Statistics Summary for Database: {database_name}")
    print("=" * 80)

    if not stats_list:
        print("No collections found.")
        return

    # Calculate totals
    total_docs = sum(s.document_count for s in stats_list)
    total_size = sum(s.collection_size_bytes for s in stats_list)
    total_storage = sum(s.storage_size_bytes for s in stats_list)
    total_indexes = sum(s.num_indexes for s in stats_list)
    total_index_size = sum(s.total_index_size_bytes for s in stats_list)

    print(f"\nTotal Collections: {len(stats_list)}")
    print(f"Total Documents: {total_docs:,}")
    print(f"Total Data Size: {format_bytes(total_size)}")
    print(f"Total Storage Size: {format_bytes(total_storage)}")
    print(f"Total Indexes: {total_indexes}")
    print(f"Total Index Size: {format_bytes(total_index_size)}")

    # Print top 5 largest collections
    print("\n" + "-" * 80)
    print("Top 5 Largest Collections (by data size):")
    print("-" * 80)

    sorted_by_size = sorted(stats_list, key=lambda s: s.collection_size_bytes, reverse=True)[:5]

    print(f"{'Collection':<30} {'Documents':>12} {'Data Size':>15} {'Indexes':>8}")
    print("-" * 80)

    for stats in sorted_by_size:
        print(
            f"{stats.collection_name:<30} "
            f"{stats.document_count:>12,} "
            f"{format_bytes(stats.collection_size_bytes):>15} "
            f"{stats.num_indexes:>8}"
        )

    print("=" * 80 + "\n")


def export_index_stats_to_csv(
    index_data: List[Dict], output_dir: Path, database_name: str
) -> Path:
    """Export index statistics to CSV file.

    Args:
        index_data: List of dicts with keys: collection_name, index_name, index_keys, usage_count, is_unused
        output_dir: Directory to write CSV file
        database_name: Name of the database (used in filename)

    Returns:
        Path to the created CSV file

    Raises:
        IOError: If file writing fails
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp (timestamp first for chronological sorting)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_index_stats_{database_name}.csv"
    output_path = output_dir / filename

    # Define CSV headers
    headers = [
        "collection_name",
        "index_name",
        "index_keys",
        "usage_count",
        "is_unused",
    ]

    # Write CSV file
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()

        for row in index_data:
            writer.writerow(row)

    return output_path
