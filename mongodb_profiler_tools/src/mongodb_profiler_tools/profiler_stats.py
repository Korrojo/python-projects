"""Profiler statistics module - get profiling collection statistics."""

from typing import Any


def get_profiler_stats(db: Any) -> dict[str, Any]:
    """Get MongoDB profiler statistics.

    Args:
        db: MongoDB database instance

    Returns:
        Dictionary with profiler statistics
    """
    try:
        profile_collection = db["system.profile"]

        # Get collection stats
        stats_result = db.command("collStats", "system.profile")

        # Get document count
        doc_count = profile_collection.count_documents({})

        # Get time range
        oldest_entry = profile_collection.find_one(sort=[("ts", 1)])
        newest_entry = profile_collection.find_one(sort=[("ts", -1)])

        # Get profiling level
        profiling_status = db.command("profile", -1)

        # Calculate durations
        duration_ms = 0
        oldest_ts = None
        newest_ts = None

        if oldest_entry and newest_entry:
            oldest_ts = oldest_entry.get("ts")
            newest_ts = newest_entry.get("ts")
            if oldest_ts and newest_ts:
                duration_ms = (newest_ts - oldest_ts).total_seconds() * 1000

        # Build result
        result = {
            "profiling_enabled": profiling_status.get("was", 0) > 0,
            "profiling_level": profiling_status.get("was", 0),
            "slowms": profiling_status.get("slowms", 100),
            "document_count": doc_count,
            "size_bytes": stats_result.get("size", 0),
            "size_mb": round(stats_result.get("size", 0) / 1048576, 2),
            "storage_size_bytes": stats_result.get("storageSize", 0),
            "storage_size_mb": round(stats_result.get("storageSize", 0) / 1048576, 2),
            "avg_obj_size": stats_result.get("avgObjSize", 0),
            "capped": stats_result.get("capped", False),
            "max_size": stats_result.get("maxSize", 0) if stats_result.get("capped") else None,
            "oldest_timestamp": oldest_ts,
            "newest_timestamp": newest_ts,
            "duration_ms": duration_ms,
            "duration_hours": round(duration_ms / 3600000, 2) if duration_ms else 0,
            "duration_days": round(duration_ms / 86400000, 2) if duration_ms else 0,
        }

        return result

    except Exception as e:
        # system.profile might not exist
        return {
            "profiling_enabled": False,
            "error": str(e),
        }


def print_profiler_stats(stats: dict[str, Any]) -> None:
    """Print profiler statistics to console.

    Args:
        stats: Profiler statistics dictionary
    """
    print("\n" + "=" * 120)
    print("MongoDB Profiler Statistics")
    print("=" * 120)

    if "error" in stats:
        print("\n❌ Error getting profiler statistics:")
        print(f"   {stats['error']}")
        print("\nNote: Profiling might not be enabled or system.profile collection does not exist.")
        print("   Enable profiling: db.setProfilingLevel(1)  // Slow queries only")
        print("   Enable profiling: db.setProfilingLevel(2)  // All operations")
        print("\n" + "=" * 120 + "\n")
        return

    # Profiling status
    print("\n📊 Profiling Status:")
    print(f"   Enabled: {'✅ Yes' if stats['profiling_enabled'] else '❌ No'}")

    level_desc = {
        0: "Off (not collecting data)",
        1: "On (slow operations only)",
        2: "On (all operations)",
    }
    level = stats["profiling_level"]
    print(f"   Level: {level} - {level_desc.get(level, 'Unknown')}")

    if level == 1:
        print(f"   Slow threshold: {stats['slowms']}ms")

    # Collection size
    print("\n💾 Collection Size:")
    print(f"   Documents: {stats['document_count']:,}")
    print(f"   Size: {stats['size_mb']:.2f} MB ({stats['size_bytes']:,} bytes)")
    print(f"   Storage: {stats['storage_size_mb']:.2f} MB ({stats['storage_size_bytes']:,} bytes)")
    print(f"   Average document size: {stats['avg_obj_size']:,} bytes")

    if stats["capped"]:
        max_mb = stats["max_size"] / 1048576 if stats["max_size"] else 0
        print(f"   Capped collection: ✅ Yes (max size: {max_mb:.2f} MB)")
    else:
        print("   Capped collection: ❌ No")

    # Time range
    if stats["oldest_timestamp"] and stats["newest_timestamp"]:
        print("\n📅 Time Range:")
        print(f"   Oldest entry: {stats['oldest_timestamp']}")
        print(f"   Newest entry: {stats['newest_timestamp']}")
        print(f"   Duration: {stats['duration_hours']:.2f} hours ({stats['duration_days']:.2f} days)")
    else:
        print("\n📅 Time Range: No entries found")

    # Recommendations
    print("\n💡 Recommendations:")

    if not stats["profiling_enabled"]:
        print("   ⚠️  Profiling is disabled. Enable it to collect performance data:")
        print("      db.setProfilingLevel(1, { slowms: 100 })  // Collect slow queries (>100ms)")
        print("      db.setProfilingLevel(2)  // Collect all operations (impacts performance)")

    if stats["profiling_enabled"] and stats["document_count"] == 0:
        print("   ℹ️  No profiling data collected yet. Wait for operations to be profiled.")

    if stats["profiling_enabled"] and not stats["capped"]:
        print("   ⚠️  system.profile is not capped. It may grow without bounds.")
        print("      Consider recreating as a capped collection:")
        print("      db.setProfilingLevel(0)")
        print("      db.system.profile.drop()")
        print('      db.createCollection("system.profile", { capped: true, size: 104857600 })  // 100MB')
        print("      db.setProfilingLevel(1)")

    if stats["profiling_enabled"] and stats["size_mb"] > 500:
        print(f"   ⚠️  Profile collection is large ({stats['size_mb']:.2f} MB)")
        print("      Consider clearing old data or reducing the profiling level.")

    print("\n" + "=" * 120 + "\n")
