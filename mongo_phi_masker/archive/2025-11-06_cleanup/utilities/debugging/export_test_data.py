#!/usr/bin/env python3
"""
Intelligent Test Data Export Script

Purpose: Export documents with maximum PHI field coverage for testing
Features:
- PHI field ranking (1 point per PHI field present)
- Top N richest documents selection
- Test database targeting
- Support for both raw and masked data export

Usage:
    # Export top 10 PHI-rich documents from Patients collection
    python scripts/export_test_data.py --collection Patients --count 10 \
        --source-uri mongodb://localhost:27017 --source-db source_db \
        --dest-uri mongodb://localhost:27017 --dest-db test_db

    # Export with custom collection name in destination
    python scripts/export_test_data.py --collection Patients --count 20 \
        --source-uri mongodb://localhost:27017 --source-db prod_db \
        --dest-uri mongodb://localhost:27017 --dest-db test_db \
        --dest-collection test_patients_unmasked
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from pymongo import MongoClient

# Add project root to path to import config modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.collection_rule_mapping import PATH_MAPPING, get_phi_fields

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)


class PHIDocumentScorer:
    """Scores documents based on PHI field presence."""

    def __init__(self, collection_name: str):
        """Initialize scorer with collection-specific PHI fields.

        Args:
            collection_name: Name of the MongoDB collection
        """
        self.collection_name = collection_name
        self.phi_fields = get_phi_fields(collection_name)
        self.path_mapping = PATH_MAPPING.get(collection_name, {})

        logger.info(f"Initialized scorer for {collection_name} with {len(self.phi_fields)} PHI fields")

    def get_nested_value(self, doc: dict[str, Any], path: str) -> Any:
        """Get value from nested document using dot notation.

        Args:
            doc: Document to search
            path: Dot-notation path (e.g., "Address.Street1")

        Returns:
            Value at the path, or None if not found
        """
        keys = path.split(".")
        value = doc

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and value:
                # For arrays, check if any element has the key
                for item in value:
                    if isinstance(item, dict) and key in item:
                        value = item.get(key)
                        break
                else:
                    return None
            else:
                return None

            if value is None:
                return None

        return value

    def score_document(self, doc: dict[str, Any]) -> dict[str, Any]:
        """Score a document based on PHI field presence.

        Each PHI field present = 1 point
        Higher score = more PHI fields = better test data

        Args:
            doc: MongoDB document to score

        Returns:
            Dict with score and field details
        """
        score = 0
        present_fields = []
        missing_fields = []

        for field in self.phi_fields:
            # Get the full path for this field
            field_path = self.path_mapping.get(field, field)

            # Check if field exists and has a non-None value
            value = self.get_nested_value(doc, field_path)

            if value is not None and value != "":
                score += 1
                present_fields.append(field)
            else:
                missing_fields.append(field)

        return {
            "score": score,
            "total_phi_fields": len(self.phi_fields),
            "coverage_percent": (score / len(self.phi_fields) * 100) if self.phi_fields else 0,
            "present_fields": present_fields,
            "missing_fields": missing_fields,
        }


class TestDataExporter:
    """Exports PHI-rich test documents to a test database."""

    def __init__(
        self,
        source_uri: str,
        source_db: str,
        source_collection: str,
        dest_uri: str,
        dest_db: str,
        dest_collection: str | None = None,
    ):
        """Initialize exporter with source and destination configs.

        Args:
            source_uri: Source MongoDB URI
            source_db: Source database name
            source_collection: Source collection name
            dest_uri: Destination MongoDB URI
            dest_db: Destination database name
            dest_collection: Destination collection name (optional)
        """
        self.source_uri = source_uri
        self.source_db = source_db
        self.source_collection = source_collection
        self.dest_uri = dest_uri
        self.dest_db = dest_db
        self.dest_collection = dest_collection or f"test_{source_collection}_unmasked"

        self.scorer = PHIDocumentScorer(source_collection)
        self.source_client = None
        self.dest_client = None

    def connect(self):
        """Connect to source and destination MongoDB instances."""
        logger.info(f"Connecting to source: {self.source_db}.{self.source_collection}")
        self.source_client = MongoClient(self.source_uri)

        logger.info(f"Connecting to destination: {self.dest_db}.{self.dest_collection}")
        self.dest_client = MongoClient(self.dest_uri)

        # Test connections
        self.source_client.admin.command("ping")
        self.dest_client.admin.command("ping")
        logger.info("✓ Connected to both databases")

    def disconnect(self):
        """Close database connections."""
        if self.source_client:
            self.source_client.close()
        if self.dest_client:
            self.dest_client.close()
        logger.info("✓ Disconnected from databases")

    def find_richest_documents(self, count: int = 10, query: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Find documents with highest PHI field coverage.

        Args:
            count: Number of top documents to return
            query: Optional MongoDB query filter

        Returns:
            List of documents with scores
        """
        source_coll = self.source_client[self.source_db][self.source_collection]

        # Get total document count
        total_docs = source_coll.count_documents(query or {})
        logger.info(f"Scanning {total_docs} documents to find PHI-rich samples...")

        # Score all documents
        scored_docs = []
        processed = 0
        batch_size = 1000

        cursor = source_coll.find(query or {}).batch_size(batch_size)

        for doc in cursor:
            score_info = self.scorer.score_document(doc)
            scored_docs.append({"_id": doc["_id"], "document": doc, "score_info": score_info})

            processed += 1
            if processed % batch_size == 0:
                logger.info(f"  Scored {processed}/{total_docs} documents...")

        logger.info(f"✓ Scored all {processed} documents")

        # Sort by score (highest first) and take top N
        scored_docs.sort(key=lambda x: x["score_info"]["score"], reverse=True)
        top_docs = scored_docs[:count]

        # Log statistics
        if top_docs:
            avg_score = sum(d["score_info"]["score"] for d in top_docs) / len(top_docs)
            avg_coverage = sum(d["score_info"]["coverage_percent"] for d in top_docs) / len(top_docs)
            logger.info(f"✓ Selected top {len(top_docs)} documents")
            logger.info(f"  Average PHI fields present: {avg_score:.1f}")
            logger.info(f"  Average coverage: {avg_coverage:.1f}%")

        return top_docs

    def export_documents(self, documents: list[dict[str, Any]], drop_existing: bool = False) -> int:
        """Export documents to destination collection.

        Args:
            documents: List of documents with scores to export
            drop_existing: Whether to drop existing destination collection

        Returns:
            Number of documents exported
        """
        dest_coll = self.dest_client[self.dest_db][self.dest_collection]

        # Drop existing collection if requested
        if drop_existing:
            logger.info(f"Dropping existing collection: {self.dest_collection}")
            dest_coll.drop()

        # Prepare documents for insert (remove score_info)
        docs_to_insert = [d["document"] for d in documents]

        # Insert documents
        result = dest_coll.insert_many(docs_to_insert)
        logger.info(f"✓ Inserted {len(result.inserted_ids)} documents into {self.dest_db}.{self.dest_collection}")

        return len(result.inserted_ids)

    def export_score_report(self, documents: list[dict[str, Any]], output_file: str):
        """Export detailed scoring report to JSON file.

        Args:
            documents: List of scored documents
            output_file: Path to output JSON file
        """
        report = {
            "collection": self.source_collection,
            "timestamp": datetime.now().isoformat(),
            "total_documents_selected": len(documents),
            "phi_field_count": len(self.scorer.phi_fields),
            "phi_fields": self.scorer.phi_fields,
            "documents": [
                {
                    "_id": str(d["_id"]),
                    "score": d["score_info"]["score"],
                    "coverage_percent": d["score_info"]["coverage_percent"],
                    "present_fields": d["score_info"]["present_fields"],
                    "missing_fields": d["score_info"]["missing_fields"],
                }
                for d in documents
            ],
        }

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"✓ Exported score report to {output_file}")


def main():
    """CLI entry point for test data export."""
    parser = argparse.ArgumentParser(
        description="Export PHI-rich test documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export top 10 PHI-rich Patients documents
  python scripts/export_test_data.py --collection Patients --count 10 \\
      --source-uri mongodb://localhost:27017 --source-db prod_db \\
      --dest-uri mongodb://localhost:27017 --dest-db test_db

  # Export with custom destination collection name
  python scripts/export_test_data.py --collection Container --count 20 \\
      --source-uri mongodb://localhost:27017 --source-db prod_db \\
      --dest-uri mongodb://localhost:27017 --dest-db test_db \\
      --dest-collection test_container_rich_phi

  # Export with MongoDB query filter
  python scripts/export_test_data.py --collection Patients --count 50 \\
      --source-uri mongodb://localhost:27017 --source-db prod_db \\
      --dest-uri mongodb://localhost:27017 --dest-db test_db \\
      --query '{"createdAt": {"$gte": {"$date": "2024-01-01T00:00:00Z"}}}'
        """,
    )

    parser.add_argument("--collection", type=str, required=True, help="Source collection name")
    parser.add_argument(
        "--count", type=int, default=10, help="Number of top PHI-rich documents to export (default: 10)"
    )
    parser.add_argument("--source-uri", type=str, required=True, help="Source MongoDB connection URI")
    parser.add_argument("--source-db", type=str, required=True, help="Source database name")
    parser.add_argument(
        "--dest-uri", type=str, required=True, help="Destination MongoDB connection URI (can be same as source)"
    )
    parser.add_argument("--dest-db", type=str, required=True, help="Destination database name")
    parser.add_argument(
        "--dest-collection",
        type=str,
        help="Destination collection name (default: test_{collection}_unmasked)",
    )
    parser.add_argument(
        "--query", type=str, help='MongoDB query filter in JSON format (e.g., \'{"status": "active"}\')'
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop destination collection if it exists",
    )
    parser.add_argument(
        "--report",
        type=str,
        default="reports/phi_export_report.json",
        help="Path to save scoring report (default: reports/phi_export_report.json)",
    )

    args = parser.parse_args()

    # Parse query if provided
    query = None
    if args.query:
        try:
            query = json.loads(args.query)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON query: {e}")
            sys.exit(1)

    print("=" * 70)
    print("MongoDB PHI Masker - Test Data Export")
    print("=" * 70)
    print("\nConfiguration:")
    print(f"  Collection: {args.collection}")
    print(f"  Documents to export: {args.count}")
    print(f"  Source: {args.source_db}.{args.collection}")
    print(f"  Destination: {args.dest_db}.{args.dest_collection or f'test_{args.collection}_unmasked'}")
    print(f"  Query filter: {query if query else 'None (all documents)'}")
    print()

    # Initialize exporter
    exporter = TestDataExporter(
        source_uri=args.source_uri,
        source_db=args.source_db,
        source_collection=args.collection,
        dest_uri=args.dest_uri,
        dest_db=args.dest_db,
        dest_collection=args.dest_collection,
    )

    try:
        # Connect to databases
        exporter.connect()

        # Find richest documents
        start_time = datetime.now()
        rich_docs = exporter.find_richest_documents(count=args.count, query=query)
        scan_duration = (datetime.now() - start_time).total_seconds()

        if not rich_docs:
            logger.warning("No documents found matching criteria")
            return

        # Export to destination
        exported_count = exporter.export_documents(rich_docs, drop_existing=args.drop_existing)

        # Export scoring report
        exporter.export_score_report(rich_docs, args.report)

        # Summary
        print("\n" + "=" * 70)
        print("✓ Export Complete!")
        print("=" * 70)
        print("\nSummary:")
        print(f"  Documents scanned: {scan_duration:.2f}s")
        print(f"  Documents exported: {exported_count}")
        print(f"  Destination: {args.dest_db}.{exporter.dest_collection}")
        print(f"  Score report: {args.report}")
        print("\nNext steps:")
        print(f"  1. Review score report: cat {args.report}")
        print(
            f"  2. Verify exported data: mongosh {args.dest_uri} --eval 'use {args.dest_db}; db.{exporter.dest_collection}.count()'"
        )
        print("  3. Run masking on test data to compare results")
        print()

    except Exception as e:
        logger.error(f"Export failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        exporter.disconnect()


if __name__ == "__main__":
    main()
