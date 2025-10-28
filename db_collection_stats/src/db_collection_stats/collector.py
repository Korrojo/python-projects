"""MongoDB collection statistics collector."""

from dataclasses import dataclass
from typing import List

from pymongo import MongoClient
from pymongo.database import Database


@dataclass
class CollectionStats:
    """Statistics for a single MongoDB collection."""

    collection_name: str
    document_count: int
    collection_size_bytes: int
    avg_document_size_bytes: float
    storage_size_bytes: int
    num_indexes: int
    total_index_size_bytes: int

    def to_dict(self) -> dict:
        """Convert stats to dictionary for CSV export."""
        return {
            "collection_name": self.collection_name,
            "document_count": self.document_count,
            "collection_size_bytes": self.collection_size_bytes,
            "avg_document_size_bytes": round(self.avg_document_size_bytes, 2),
            "storage_size_bytes": self.storage_size_bytes,
            "num_indexes": self.num_indexes,
            "total_index_size_bytes": self.total_index_size_bytes,
        }


def gather_collection_stats(db: Database, collection_name: str) -> CollectionStats:
    """Gather statistics for a single collection.

    Args:
        db: MongoDB database instance
        collection_name: Name of the collection to analyze

    Returns:
        CollectionStats object with gathered statistics

    Raises:
        Exception: If stats gathering fails
    """
    stats = db.command("collStats", collection_name)

    return CollectionStats(
        collection_name=collection_name,
        document_count=stats.get("count", 0),
        collection_size_bytes=stats.get("size", 0),
        avg_document_size_bytes=stats.get("avgObjSize", 0.0),
        storage_size_bytes=stats.get("storageSize", 0),
        num_indexes=stats.get("nindexes", 0),
        total_index_size_bytes=stats.get("totalIndexSize", 0),
    )


def gather_all_collections_stats(
    client: MongoClient, database_name: str, exclude_system: bool = True
) -> List[CollectionStats]:
    """Gather statistics for all collections in a database.

    Args:
        client: MongoDB client instance
        database_name: Name of the database to analyze
        exclude_system: If True, exclude system collections (default: True)

    Returns:
        List of CollectionStats for all collections

    Raises:
        Exception: If database access fails
    """
    db = client[database_name]
    collection_names = db.list_collection_names()

    # Filter out system collections if requested
    if exclude_system:
        collection_names = [name for name in collection_names if not name.startswith("system.")]

    stats_list = []
    for collection_name in sorted(collection_names):
        try:
            stats = gather_collection_stats(db, collection_name)
            stats_list.append(stats)
        except Exception as e:
            # Log error but continue with other collections
            print(f"Warning: Failed to gather stats for {collection_name}: {e}")

    return stats_list
