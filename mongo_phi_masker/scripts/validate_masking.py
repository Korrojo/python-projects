#!/usr/bin/env python3
"""
Before/After Masking Validation Script

Purpose: Compare original vs masked data for accuracy
Features:
- Field-by-field comparison
- PHI field masking verification
- Non-PHI field preservation checks
- Data integrity validation
- Statistical analysis and reporting

Usage:
    # Compare collections in same database
    python scripts/validate_masking.py \
        --uri mongodb://localhost:27017 \
        --database test_db \
        --original-collection test_Patients_unmasked \
        --masked-collection test_Patients_masked \
        --collection-type Patients

    # Compare collections in different databases
    python scripts/validate_masking.py \
        --original-uri mongodb://localhost:27017 --original-db source_db --original-collection Patients \
        --masked-uri mongodb://localhost:27017 --masked-db dest_db --masked-collection Patients_masked \
        --collection-type Patients

    # With detailed output
    python scripts/validate_masking.py \
        --uri mongodb://localhost:27017 --database test_db \
        --original-collection test_Patients_unmasked \
        --masked-collection test_Patients_masked \
        --collection-type Patients \
        --report validation_report.json \
        --verbose
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


class MaskingValidator:
    """Validates masking by comparing original and masked documents."""

    def __init__(self, collection_type: str):
        """Initialize validator with collection-specific PHI fields.

        Args:
            collection_type: Type of collection (e.g., Patients, Container)
        """
        self.collection_type = collection_type
        self.phi_fields = get_phi_fields(collection_type)
        self.path_mapping = PATH_MAPPING.get(collection_type, {})

        logger.info(f"Initialized validator for {collection_type} with {len(self.phi_fields)} PHI fields")

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
                found = False
                for item in value:
                    if isinstance(item, dict) and key in item:
                        value = item.get(key)
                        found = True
                        break
                if not found:
                    return None
            else:
                return None

            if value is None:
                return None

        return value

    def set_nested_value(self, doc: dict[str, Any], path: str, value: Any):
        """Set value in nested document using dot notation.

        Args:
            doc: Document to modify
            path: Dot-notation path
            value: Value to set
        """
        keys = path.split(".")
        current = doc

        for i, key in enumerate(keys[:-1]):
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def compare_documents(self, original: dict[str, Any], masked: dict[str, Any]) -> dict[str, Any]:
        """Compare original and masked documents.

        Args:
            original: Original unmasked document
            masked: Masked document

        Returns:
            Comparison results with field-level details
        """
        results = {
            "_id": str(original.get("_id")),
            "phi_fields_checked": 0,
            "phi_fields_masked": 0,
            "phi_fields_unchanged": 0,
            "phi_fields_missing": 0,
            "non_phi_fields_checked": 0,
            "non_phi_fields_preserved": 0,
            "non_phi_fields_changed": 0,
            "phi_field_details": [],
            "non_phi_field_issues": [],
            "errors": [],
        }

        # Check PHI fields - should be masked
        for field in self.phi_fields:
            field_path = self.path_mapping.get(field, field)

            original_value = self.get_nested_value(original, field_path)
            masked_value = self.get_nested_value(masked, field_path)

            results["phi_fields_checked"] += 1

            if original_value is None and masked_value is None:
                # Field doesn't exist in either document
                results["phi_fields_missing"] += 1
                continue

            if original_value is None:
                results["errors"].append(f"PHI field {field} ({field_path}) exists in masked but not in original")
                continue

            if masked_value is None:
                results["errors"].append(f"PHI field {field} ({field_path}) missing in masked document")
                continue

            # Check if value was actually masked (changed)
            if original_value == masked_value:
                results["phi_fields_unchanged"] += 1
                results["phi_field_details"].append(
                    {
                        "field": field,
                        "path": field_path,
                        "status": "UNCHANGED",
                        "original": self._safe_value_repr(original_value),
                        "masked": self._safe_value_repr(masked_value),
                    }
                )
            else:
                results["phi_fields_masked"] += 1
                results["phi_field_details"].append(
                    {
                        "field": field,
                        "path": field_path,
                        "status": "MASKED",
                        "original": self._safe_value_repr(original_value),
                        "masked": self._safe_value_repr(masked_value),
                    }
                )

        # Check non-PHI fields - should be preserved
        # Compare top-level fields that are not in PHI list
        all_fields = set(original.keys()) | set(masked.keys())
        top_level_phi_fields = {
            field for field in self.phi_fields if "." not in (self.path_mapping.get(field) or field)
        }

        for field in all_fields:
            if field == "_id":
                continue  # Skip _id comparison

            if field in top_level_phi_fields:
                continue  # Skip PHI fields

            # Check if this is a nested PHI container (e.g., Address, Phones)
            if self._is_phi_container(field):
                continue  # Skip nested containers

            results["non_phi_fields_checked"] += 1

            original_value = original.get(field)
            masked_value = masked.get(field)

            if original_value != masked_value:
                results["non_phi_fields_changed"] += 1
                results["non_phi_field_issues"].append(
                    {
                        "field": field,
                        "original": self._safe_value_repr(original_value),
                        "masked": self._safe_value_repr(masked_value),
                    }
                )
            else:
                results["non_phi_fields_preserved"] += 1

        return results

    def _is_phi_container(self, field: str) -> bool:
        """Check if a field is a container for nested PHI fields.

        Args:
            field: Field name to check

        Returns:
            True if field contains nested PHI fields
        """
        # Check if any PHI field path starts with this field
        for phi_field in self.phi_fields:
            path = self.path_mapping.get(phi_field) or phi_field
            if path.startswith(f"{field}."):
                return True
        return False

    def _safe_value_repr(self, value: Any, max_len: int = 50) -> str:
        """Get safe string representation of value for reporting.

        Args:
            value: Value to represent
            max_len: Maximum length of string representation

        Returns:
            String representation
        """
        if value is None:
            return "null"
        if isinstance(value, (dict, list)):
            repr_str = json.dumps(value, default=str)
            if len(repr_str) > max_len:
                return repr_str[:max_len] + "..."
            return repr_str
        str_value = str(value)
        if len(str_value) > max_len:
            return str_value[:max_len] + "..."
        return str_value


class ValidationComparator:
    """Compares original and masked collections for validation."""

    def __init__(
        self,
        original_uri: str,
        original_db: str,
        original_collection: str,
        masked_uri: str,
        masked_db: str,
        masked_collection: str,
        collection_type: str,
    ):
        """Initialize comparator with connection details.

        Args:
            original_uri: Original MongoDB URI
            original_db: Original database name
            original_collection: Original collection name
            masked_uri: Masked MongoDB URI
            masked_db: Masked database name
            masked_collection: Masked collection name
            collection_type: Collection type for PHI field mapping
        """
        self.original_uri = original_uri
        self.original_db = original_db
        self.original_collection = original_collection
        self.masked_uri = masked_uri
        self.masked_db = masked_db
        self.masked_collection = masked_collection
        self.collection_type = collection_type

        self.validator = MaskingValidator(collection_type)
        self.original_client = None
        self.masked_client = None

    def connect(self):
        """Connect to MongoDB instances."""
        logger.info(f"Connecting to original: {self.original_db}.{self.original_collection}")
        self.original_client = MongoClient(self.original_uri)

        logger.info(f"Connecting to masked: {self.masked_db}.{self.masked_collection}")
        self.masked_client = MongoClient(self.masked_uri)

        # Test connections
        self.original_client.admin.command("ping")
        self.masked_client.admin.command("ping")
        logger.info("✓ Connected to both databases")

    def disconnect(self):
        """Close database connections."""
        if self.original_client:
            self.original_client.close()
        if self.masked_client:
            self.masked_client.close()
        logger.info("✓ Disconnected from databases")

    def validate_collections(self, sample_size: int | None = None) -> dict[str, Any]:
        """Validate masking by comparing collections.

        Args:
            sample_size: Optional limit on number of documents to compare

        Returns:
            Validation results with statistics
        """
        original_coll = self.original_client[self.original_db][self.original_collection]
        masked_coll = self.masked_client[self.masked_db][self.masked_collection]

        # Get document counts
        original_count = original_coll.count_documents({})
        masked_count = masked_coll.count_documents({})

        logger.info(f"Original documents: {original_count}")
        logger.info(f"Masked documents: {masked_count}")

        if original_count != masked_count:
            logger.warning(f"Document count mismatch: {original_count} vs {masked_count}")

        # Determine documents to compare
        docs_to_compare = min(original_count, masked_count)
        if sample_size:
            docs_to_compare = min(docs_to_compare, sample_size)

        logger.info(f"Comparing {docs_to_compare} documents...")

        # Get documents sorted by _id for consistent comparison
        original_docs = list(original_coll.find().sort("_id", 1).limit(docs_to_compare))
        masked_docs_map = {doc["_id"]: doc for doc in masked_coll.find().sort("_id", 1).limit(docs_to_compare)}

        # Compare documents
        comparison_results = []
        matched_count = 0
        missing_in_masked = []

        for original_doc in original_docs:
            doc_id = original_doc["_id"]

            if doc_id not in masked_docs_map:
                missing_in_masked.append(str(doc_id))
                continue

            matched_count += 1
            masked_doc = masked_docs_map[doc_id]

            result = self.validator.compare_documents(original_doc, masked_doc)
            comparison_results.append(result)

        # Calculate aggregate statistics
        stats = self._calculate_statistics(comparison_results)

        return {
            "validation_timestamp": datetime.now().isoformat(),
            "collection_type": self.collection_type,
            "original": {
                "uri": self.original_uri,
                "database": self.original_db,
                "collection": self.original_collection,
                "count": original_count,
            },
            "masked": {
                "uri": self.masked_uri,
                "database": self.masked_db,
                "collection": self.masked_collection,
                "count": masked_count,
            },
            "comparison": {
                "documents_compared": matched_count,
                "missing_in_masked": len(missing_in_masked),
                "missing_ids": missing_in_masked[:10] if missing_in_masked else [],  # First 10
            },
            "statistics": stats,
            "document_results": comparison_results,
        }

    def _calculate_statistics(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate aggregate statistics from document comparison results.

        Args:
            results: List of document comparison results

        Returns:
            Aggregate statistics
        """
        if not results:
            return {}

        total_docs = len(results)

        # Aggregate counts
        total_phi_checked = sum(r["phi_fields_checked"] for r in results)
        total_phi_masked = sum(r["phi_fields_masked"] for r in results)
        total_phi_unchanged = sum(r["phi_fields_unchanged"] for r in results)
        total_phi_missing = sum(r["phi_fields_missing"] for r in results)

        total_non_phi_checked = sum(r["non_phi_fields_checked"] for r in results)
        total_non_phi_preserved = sum(r["non_phi_fields_preserved"] for r in results)
        total_non_phi_changed = sum(r["non_phi_fields_changed"] for r in results)

        # Calculate percentages
        phi_masking_rate = (total_phi_masked / total_phi_checked * 100) if total_phi_checked > 0 else 0
        phi_missing_rate = (total_phi_missing / total_phi_checked * 100) if total_phi_checked > 0 else 0
        non_phi_preservation_rate = (
            (total_non_phi_preserved / total_non_phi_checked * 100) if total_non_phi_checked > 0 else 0
        )

        # Documents with issues
        docs_with_phi_issues = sum(1 for r in results if r["phi_fields_unchanged"] > 0 or r["errors"])
        docs_with_non_phi_issues = sum(1 for r in results if r["non_phi_fields_changed"] > 0)

        return {
            "documents_analyzed": total_docs,
            "phi_fields": {
                "total_checked": total_phi_checked,
                "total_masked": total_phi_masked,
                "total_unchanged": total_phi_unchanged,
                "total_missing": total_phi_missing,
                "masking_rate_percent": round(phi_masking_rate, 2),
                "missing_rate_percent": round(phi_missing_rate, 2),
                "documents_with_issues": docs_with_phi_issues,
            },
            "non_phi_fields": {
                "total_checked": total_non_phi_checked,
                "total_preserved": total_non_phi_preserved,
                "total_changed": total_non_phi_changed,
                "preservation_rate_percent": round(non_phi_preservation_rate, 2),
                "documents_with_issues": docs_with_non_phi_issues,
            },
            "overall_status": self._determine_status(phi_masking_rate, non_phi_preservation_rate),
        }

    def _determine_status(self, phi_masking_rate: float, non_phi_preservation_rate: float) -> str:
        """Determine overall validation status.

        Args:
            phi_masking_rate: Percentage of PHI fields masked
            non_phi_preservation_rate: Percentage of non-PHI fields preserved

        Returns:
            Status string
        """
        if phi_masking_rate >= 95 and non_phi_preservation_rate >= 95:
            return "EXCELLENT"
        elif phi_masking_rate >= 90 and non_phi_preservation_rate >= 90:
            return "GOOD"
        elif phi_masking_rate >= 80 and non_phi_preservation_rate >= 80:
            return "ACCEPTABLE"
        elif phi_masking_rate >= 70:
            return "NEEDS_IMPROVEMENT"
        else:
            return "FAILED"


def main():
    """CLI entry point for masking validation."""
    parser = argparse.ArgumentParser(
        description="Validate masking by comparing original and masked collections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare collections in same database
  python scripts/validate_masking.py \\
      --uri mongodb://localhost:27017 --database test_db \\
      --original-collection test_Patients_unmasked \\
      --masked-collection test_Patients_masked \\
      --collection-type Patients

  # Compare collections in different databases
  python scripts/validate_masking.py \\
      --original-uri mongodb://localhost:27017 --original-db source_db \\
      --original-collection Patients \\
      --masked-uri mongodb://localhost:27017 --masked-db dest_db \\
      --masked-collection Patients_masked \\
      --collection-type Patients

  # With sample size limit
  python scripts/validate_masking.py \\
      --uri mongodb://localhost:27017 --database test_db \\
      --original-collection test_Container_unmasked \\
      --masked-collection test_Container_masked \\
      --collection-type Container \\
      --sample-size 100
        """,
    )

    # Simplified mode - same database
    parser.add_argument("--uri", type=str, help="MongoDB URI (for both collections if same database)")
    parser.add_argument("--database", type=str, help="Database name (for both collections if same database)")

    # Original collection details
    parser.add_argument("--original-uri", type=str, help="Original collection MongoDB URI")
    parser.add_argument("--original-db", type=str, help="Original database name")
    parser.add_argument("--original-collection", type=str, required=True, help="Original collection name")

    # Masked collection details
    parser.add_argument("--masked-uri", type=str, help="Masked collection MongoDB URI")
    parser.add_argument("--masked-db", type=str, help="Masked database name")
    parser.add_argument("--masked-collection", type=str, required=True, help="Masked collection name")

    # Collection type
    parser.add_argument(
        "--collection-type",
        type=str,
        required=True,
        help="Collection type (e.g., Patients, Container, Tasks)",
    )

    # Options
    parser.add_argument(
        "--sample-size",
        type=int,
        help="Limit number of documents to compare (default: all documents)",
    )
    parser.add_argument(
        "--report",
        type=str,
        default="reports/validation_report.json",
        help="Path to save validation report (default: reports/validation_report.json)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output with detailed field comparisons",
    )

    args = parser.parse_args()

    # Determine URIs and databases
    original_uri = args.original_uri or args.uri
    original_db = args.original_db or args.database
    masked_uri = args.masked_uri or args.uri
    masked_db = args.masked_db or args.database

    # Validate required parameters
    if not original_uri or not original_db:
        parser.error("Must provide either --uri/--database or --original-uri/--original-db")
    if not masked_uri or not masked_db:
        parser.error("Must provide either --uri/--database or --masked-uri/--masked-db")

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("=" * 70)
    print("MongoDB PHI Masker - Masking Validation")
    print("=" * 70)
    print("\nConfiguration:")
    print(f"  Collection type: {args.collection_type}")
    print(f"  Original: {original_db}.{args.original_collection}")
    print(f"  Masked: {masked_db}.{args.masked_collection}")
    print(f"  Sample size: {args.sample_size if args.sample_size else 'All documents'}")
    print()

    # Initialize comparator
    comparator = ValidationComparator(
        original_uri=original_uri,
        original_db=original_db,
        original_collection=args.original_collection,
        masked_uri=masked_uri,
        masked_db=masked_db,
        masked_collection=args.masked_collection,
        collection_type=args.collection_type,
    )

    try:
        # Connect to databases
        comparator.connect()

        # Validate collections
        start_time = datetime.now()
        results = comparator.validate_collections(sample_size=args.sample_size)
        validation_duration = (datetime.now() - start_time).total_seconds()

        # Save report
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with report_path.open("w") as f:
            json.dump(results, f, indent=2, default=str)

        # Print summary
        stats = results["statistics"]
        print("\n" + "=" * 70)
        print("✓ Validation Complete!")
        print("=" * 70)
        print("\nSummary:")
        print(f"  Duration: {validation_duration:.2f}s")
        print(f"  Documents analyzed: {stats['documents_analyzed']}")
        print(f"  Overall status: {stats['overall_status']}")
        print("\nPHI Fields:")
        print(f"  Total checked: {stats['phi_fields']['total_checked']}")
        print(f"  Masked: {stats['phi_fields']['total_masked']} ({stats['phi_fields']['masking_rate_percent']}%)")
        print(f"  Unchanged: {stats['phi_fields']['total_unchanged']}")
        print(f"  Documents with issues: {stats['phi_fields']['documents_with_issues']}")
        print("\nNon-PHI Fields:")
        print(f"  Total checked: {stats['non_phi_fields']['total_checked']}")
        print(
            f"  Preserved: {stats['non_phi_fields']['total_preserved']} ({stats['non_phi_fields']['preservation_rate_percent']}%)"
        )
        print(f"  Changed: {stats['non_phi_fields']['total_changed']}")
        print(f"  Documents with issues: {stats['non_phi_fields']['documents_with_issues']}")
        print(f"\nReport saved: {args.report}")
        print("\nNext steps:")
        print(f"  1. Review full report: cat {args.report} | jq '.statistics'")
        if stats["phi_fields"]["documents_with_issues"] > 0:
            print("  2. Investigate PHI fields that were not masked")
        if stats["non_phi_fields"]["documents_with_issues"] > 0:
            print("  3. Review non-PHI fields that were changed unexpectedly")
        print()

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        comparator.disconnect()


if __name__ == "__main__":
    main()
