"""Index manager module - create and drop indexes safely."""

from typing import Any

from pymongo.errors import OperationFailure


def create_index(
    db: Any,
    collection_name: str,
    keys: dict[str, int],
    name: str | None = None,
    unique: bool = False,
    sparse: bool = False,
    background: bool = True,
    expire_after_seconds: int | None = None,
    partial_filter: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create an index on a collection.

    Args:
        db: MongoDB database instance
        collection_name: Name of the collection
        keys: Dictionary of field names and sort directions (1 or -1)
        name: Custom index name (auto-generated if None)
        unique: Create unique index
        sparse: Create sparse index
        background: Build index in background (default True)
        expire_after_seconds: TTL in seconds (for TTL indexes)
        partial_filter: Partial filter expression
        dry_run: If True, only validate without creating

    Returns:
        Dictionary with operation result
    """
    collection = db[collection_name]

    # Validate keys
    if not keys:
        return {
            "success": False,
            "error": "At least one key field is required",
        }

    # Build index options
    options: dict[str, Any] = {
        "background": background,
    }

    if name:
        options["name"] = name

    if unique:
        options["unique"] = True

    if sparse:
        options["sparse"] = True

    if expire_after_seconds is not None:
        options["expireAfterSeconds"] = expire_after_seconds

    if partial_filter:
        options["partialFilterExpression"] = partial_filter

    # Generate index name if not provided
    index_name = name or "_".join([f"{field}_{direction}" for field, direction in keys.items()])

    # Check if index already exists
    try:
        existing_indexes = list(collection.list_indexes())
        for idx in existing_indexes:
            if idx["name"] == index_name:
                return {
                    "success": False,
                    "error": f"Index '{index_name}' already exists",
                    "index_name": index_name,
                }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list existing indexes: {e}",
        }

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "message": "Dry run - index would be created",
            "index_name": index_name,
            "keys": keys,
            "options": options,
        }

    # Create the index
    try:
        created_name = collection.create_index(
            list(keys.items()),
            **options,
        )

        return {
            "success": True,
            "message": "Index created successfully",
            "index_name": created_name,
            "keys": keys,
            "options": options,
        }

    except OperationFailure as e:
        return {
            "success": False,
            "error": f"Failed to create index: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {e}",
        }


def drop_index(
    db: Any,
    collection_name: str,
    index_name: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Drop an index from a collection.

    Args:
        db: MongoDB database instance
        collection_name: Name of the collection
        index_name: Name of the index to drop
        dry_run: If True, only validate without dropping

    Returns:
        Dictionary with operation result
    """
    collection = db[collection_name]

    # Prevent dropping _id index
    if index_name == "_id_":
        return {
            "success": False,
            "error": "Cannot drop the _id index",
            "index_name": index_name,
        }

    # Check if index exists
    try:
        existing_indexes = list(collection.list_indexes())
        index_exists = False
        index_info = None

        for idx in existing_indexes:
            if idx["name"] == index_name:
                index_exists = True
                index_info = idx
                break

        if not index_exists:
            return {
                "success": False,
                "error": f"Index '{index_name}' does not exist",
                "index_name": index_name,
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list existing indexes: {e}",
        }

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "message": "Dry run - index would be dropped",
            "index_name": index_name,
            "index_info": index_info,
        }

    # Drop the index
    try:
        collection.drop_index(index_name)

        return {
            "success": True,
            "message": "Index dropped successfully",
            "index_name": index_name,
            "index_info": index_info,
        }

    except OperationFailure as e:
        return {
            "success": False,
            "error": f"Failed to drop index: {e}",
            "index_name": index_name,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {e}",
            "index_name": index_name,
        }


def list_indexes(db: Any, collection_name: str) -> dict[str, Any]:
    """List all indexes for a collection.

    Args:
        db: MongoDB database instance
        collection_name: Name of the collection

    Returns:
        Dictionary with indexes list
    """
    collection = db[collection_name]

    try:
        indexes = list(collection.list_indexes())
        return {
            "success": True,
            "collection_name": collection_name,
            "indexes": indexes,
            "count": len(indexes),
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list indexes: {e}",
        }
