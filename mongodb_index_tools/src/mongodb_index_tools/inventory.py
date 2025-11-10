"""Index inventory module - gather and display index information."""

from datetime import datetime
from pathlib import Path
from typing import Any

import csv


def gather_index_inventory(db: Any, collections: list[str]) -> list[dict[str, Any]]:
    """Gather index inventory from specified collections.

    Args:
        db: MongoDB database instance
        collections: List of collection names to analyze

    Returns:
        List of dictionaries containing index information
    """
    inventory_data = []

    for coll_name in sorted(collections):
        try:
            coll = db[coll_name]

            # Get all indexes for the collection
            indexes = list(coll.list_indexes())

            for idx in indexes:
                idx_name = idx.get("name", "")
                idx_key = idx.get("key", {})

                # Format key pattern
                key_str = ", ".join([f"{k}: {v}" for k, v in idx_key.items()])

                # Get additional index properties
                unique = idx.get("unique", False)
                sparse = idx.get("sparse", False)
                background = idx.get("background", False)
                expireAfterSeconds = idx.get("expireAfterSeconds")

                # Build attributes string
                attributes = []
                if unique:
                    attributes.append("unique")
                if sparse:
                    attributes.append("sparse")
                if background:
                    attributes.append("background")
                if expireAfterSeconds is not None:
                    attributes.append(f"TTL:{expireAfterSeconds}s")

                attributes_str = ", ".join(attributes) if attributes else ""

                inventory_data.append(
                    {
                        "collection_name": coll_name,
                        "index_name": idx_name,
                        "index_keys": key_str,
                        "unique": "Yes" if unique else "No",
                        "sparse": "Yes" if sparse else "No",
                        "attributes": attributes_str,
                    }
                )

        except Exception as e:
            # Log error but continue with other collections
            print(f"⚠️  Warning: Failed to analyze collection {coll_name}: {e}")
            continue

    return inventory_data


def print_inventory(inventory_data: list[dict[str, Any]], database_name: str) -> None:
    """Print index inventory to console.

    Args:
        inventory_data: List of index information dictionaries
        database_name: Name of the database
    """
    print("\n" + "=" * 120)
    print(f"Index Inventory for Database: {database_name}")
    print("=" * 120)

    current_collection = None
    total_indexes = 0

    for item in inventory_data:
        coll_name = item["collection_name"]

        # Print collection header when collection changes
        if coll_name != current_collection:
            if current_collection is not None:
                print()  # Add spacing between collections
            print(f"\n📊 Collection: {coll_name}")
            print("-" * 120)
            current_collection = coll_name

        # Print index details
        idx_name = item["index_name"]
        idx_keys = item["index_keys"]
        attributes = item["attributes"]

        attr_display = f" [{attributes}]" if attributes else ""
        print(f"  • {idx_name:35} | Keys: {idx_keys:50} {attr_display}")

        total_indexes += 1

    print("\n" + "=" * 120)
    print("\n📈 Summary:")
    print(f"  Total Collections: {len(set(item['collection_name'] for item in inventory_data))}")
    print(f"  Total Indexes: {total_indexes}")
    print()


def export_inventory_to_csv(inventory_data: list[dict[str, Any]], output_dir: Path, database_name: str) -> Path:
    """Export index inventory to CSV file.

    Args:
        inventory_data: List of index information dictionaries
        output_dir: Directory to save the CSV file
        database_name: Name of the database

    Returns:
        Path to the created CSV file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"index_inventory_{database_name}_{timestamp}.csv"
    csv_path = output_dir / csv_filename

    # Define CSV headers
    headers = [
        "Collection Name",
        "Index Name",
        "Index Keys",
        "Unique",
        "Sparse",
        "Attributes",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "collection_name",
                "index_name",
                "index_keys",
                "unique",
                "sparse",
                "attributes",
            ],
        )

        # Write headers
        csvfile.write(",".join(headers) + "\n")

        # Write data
        for item in inventory_data:
            writer.writerow(item)

    return csv_path
