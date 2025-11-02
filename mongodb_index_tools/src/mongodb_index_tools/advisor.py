"""Index advisor module - provide index recommendations."""

from datetime import datetime
from pathlib import Path
from typing import Any

import csv


def analyze_collection_indexes(db: Any, collection_name: str) -> dict[str, Any]:
    """Analyze collection indexes and provide recommendations.

    Args:
        db: MongoDB database instance
        collection_name: Name of the collection to analyze

    Returns:
        Dictionary containing recommendations
    """
    collection = db[collection_name]

    # Get all indexes
    indexes = list(collection.list_indexes())

    # Get index usage statistics
    try:
        index_stats = list(collection.aggregate([{"$indexStats": {}}]))
        usage_lookup = {stat["name"]: stat.get("accesses", {}).get("ops", 0) for stat in index_stats}
    except Exception:
        usage_lookup = {}

    # Get index sizes
    try:
        stats = db.command("collStats", collection_name)
        size_lookup = stats.get("indexSizes", {})
    except Exception:
        size_lookup = {}

    # Analyze indexes
    unused_indexes = []
    redundant_indexes = []
    useful_indexes = []

    for idx in indexes:
        idx_name = idx["name"]
        idx_key = idx["key"]
        usage_count = usage_lookup.get(idx_name, 0)
        size_bytes = size_lookup.get(idx_name, 0)

        # Skip _id index (can't be dropped)
        if idx_name == "_id_":
            continue

        index_info = {
            "name": idx_name,
            "keys": list(idx_key.keys()),
            "key_pattern": idx_key,
            "usage_count": usage_count,
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / 1048576, 2) if size_bytes else 0,
        }

        # Categorize index
        if usage_count == 0:
            unused_indexes.append(index_info)
        else:
            # Check if redundant
            if is_redundant(idx_key, indexes, idx_name):
                redundant_indexes.append(index_info)
            else:
                useful_indexes.append(index_info)

    return {
        "collection_name": collection_name,
        "total_indexes": len(indexes),
        "unused_indexes": unused_indexes,
        "redundant_indexes": redundant_indexes,
        "useful_indexes": useful_indexes,
    }


def is_redundant(index_keys: dict[str, Any], all_indexes: list[dict], current_name: str) -> bool:
    """Check if an index is redundant (covered by another index).

    An index is redundant if there's another index with the same prefix.
    For example, index on {a: 1, b: 1} makes index on {a: 1} redundant.

    Args:
        index_keys: Keys of the current index
        all_indexes: List of all indexes
        current_name: Name of the current index

    Returns:
        True if redundant, False otherwise
    """
    current_keys = list(index_keys.keys())

    for other_idx in all_indexes:
        if other_idx["name"] == current_name:
            continue

        other_keys = list(other_idx["key"].keys())

        # Check if current index is a prefix of another index
        if len(current_keys) < len(other_keys):
            # Check if all current keys match the prefix of other keys
            if current_keys == other_keys[: len(current_keys)]:
                # Also check that the sort directions match
                all_match = True
                for key in current_keys:
                    if index_keys[key] != other_idx["key"].get(key):
                        all_match = False
                        break
                if all_match:
                    return True

    return False


def generate_recommendations(analysis: dict[str, Any]) -> list[dict[str, str]]:
    """Generate actionable recommendations based on analysis.

    Args:
        analysis: Analysis results from analyze_collection_indexes

    Returns:
        List of recommendation dictionaries
    """
    recommendations = []

    # Recommend dropping unused indexes
    for idx in analysis["unused_indexes"]:
        recommendations.append(
            {
                "type": "DROP",
                "severity": "HIGH",
                "index_name": idx["name"],
                "reason": f"Unused index (0 operations), consuming {idx['size_mb']} MB",
                "action": f'db.{analysis["collection_name"]}.dropIndex("{idx["name"]}")',
                "impact": f"Saves {idx['size_mb']} MB of storage and improves write performance",
            }
        )

    # Recommend dropping redundant indexes
    for idx in analysis["redundant_indexes"]:
        recommendations.append(
            {
                "type": "DROP",
                "severity": "MEDIUM",
                "index_name": idx["name"],
                "reason": f"Redundant index (covered by compound index), {idx['usage_count']:,} operations",
                "action": f'db.{analysis["collection_name"]}.dropIndex("{idx["name"]}")',
                "impact": f"Saves {idx['size_mb']} MB of storage, minor impact on reads (covered by compound index)",
            }
        )

    # Note about useful indexes
    if analysis["useful_indexes"]:
        total_useful = len(analysis["useful_indexes"])
        recommendations.append(
            {
                "type": "INFO",
                "severity": "INFO",
                "index_name": "N/A",
                "reason": f"{total_useful} useful indexes found - review periodically",
                "action": "Monitor index usage over time",
                "impact": "Ensure indexes continue to be used effectively",
            }
        )

    return recommendations


def print_recommendations(analysis: dict[str, Any], recommendations: list[dict[str, str]]) -> None:
    """Print recommendations to console.

    Args:
        analysis: Analysis results
        recommendations: List of recommendations
    """
    print("\n" + "=" * 120)
    print(f"Index Recommendations for Collection: {analysis['collection_name']}")
    print("=" * 120)

    print("\n📊 Summary:")
    print(f"  Total Indexes: {analysis['total_indexes']}")
    print(f"  Unused Indexes: {len(analysis['unused_indexes'])}")
    print(f"  Redundant Indexes: {len(analysis['redundant_indexes'])}")
    print(f"  Useful Indexes: {len(analysis['useful_indexes'])}")

    # Print unused indexes
    if analysis["unused_indexes"]:
        print(f"\n⚠️  Unused Indexes ({len(analysis['unused_indexes'])}):")
        print("-" * 120)
        for idx in analysis["unused_indexes"]:
            keys_str = ", ".join(idx["keys"])
            print(f"  • {idx['name']:40} | Keys: {keys_str:40} | Size: {idx['size_mb']:>8.2f} MB")

    # Print redundant indexes
    if analysis["redundant_indexes"]:
        print(f"\n🔄 Redundant Indexes ({len(analysis['redundant_indexes'])}):")
        print("-" * 120)
        for idx in analysis["redundant_indexes"]:
            keys_str = ", ".join(idx["keys"])
            print(
                f"  • {idx['name']:40} | Keys: {keys_str:40} | Usage: {idx['usage_count']:>10,} | Size: {idx['size_mb']:>8.2f} MB"
            )

    # Print useful indexes
    if analysis["useful_indexes"]:
        print(f"\n✅ Useful Indexes ({len(analysis['useful_indexes'])}):")
        print("-" * 120)
        for idx in analysis["useful_indexes"]:
            keys_str = ", ".join(idx["keys"])
            print(
                f"  • {idx['name']:40} | Keys: {keys_str:40} | Usage: {idx['usage_count']:>10,} | Size: {idx['size_mb']:>8.2f} MB"
            )

    # Print actionable recommendations
    if recommendations:
        print(f"\n💡 Recommendations ({len(recommendations)}):")
        print("=" * 120)
        for i, rec in enumerate(recommendations, 1):
            severity_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢", "INFO": "ℹ️ "}.get(rec["severity"], "•")

            print(f"\n{i}. {severity_icon} [{rec['severity']}] {rec['type']}: {rec['index_name']}")
            print(f"   Reason: {rec['reason']}")
            print(f"   Action: {rec['action']}")
            print(f"   Impact: {rec['impact']}")

    else:
        print("\n✅ No recommendations - all indexes appear to be in good shape!")

    print("\n" + "=" * 120 + "\n")


def export_recommendations_to_csv(
    analysis: dict[str, Any],
    recommendations: list[dict[str, str]],
    output_dir: Path,
    database_name: str,
) -> Path:
    """Export recommendations to CSV file.

    Args:
        analysis: Analysis results
        recommendations: List of recommendations
        output_dir: Directory to save CSV
        database_name: Database name

    Returns:
        Path to created CSV file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"index_recommendations_{database_name}_{analysis['collection_name']}_{timestamp}.csv"
    csv_path = output_dir / csv_filename

    headers = [
        "Type",
        "Severity",
        "Index Name",
        "Keys",
        "Usage Count",
        "Size (MB)",
        "Reason",
        "Action",
        "Impact",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile, fieldnames=[h.lower().replace(" ", "_").replace("(", "").replace(")", "") for h in headers]
        )

        # Write header row
        csvfile.write(",".join(headers) + "\n")

        # Write recommendations
        for rec in recommendations:
            # Find the index details
            idx_info = None
            for idx in analysis["unused_indexes"] + analysis["redundant_indexes"] + analysis["useful_indexes"]:
                if idx["name"] == rec["index_name"]:
                    idx_info = idx
                    break

            row = {
                "type": rec["type"],
                "severity": rec["severity"],
                "index_name": rec["index_name"],
                "keys": ", ".join(idx_info["keys"]) if idx_info else "",
                "usage_count": idx_info["usage_count"] if idx_info else "",
                "size_mb": idx_info["size_mb"] if idx_info else "",
                "reason": rec["reason"],
                "action": rec["action"],
                "impact": rec["impact"],
            }
            writer.writerow(row)

    return csv_path
