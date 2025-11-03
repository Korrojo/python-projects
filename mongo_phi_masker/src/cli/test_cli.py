#!/usr/bin/env python3
"""
Testing CLI Module

This module provides a command-line interface for testing masking
functionality in development and test environments.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any

from src.core.orchestrator import MaskingOrchestrator
from src.utils.config_loader import ConfigLoader
from src.utils.logger import setup_logging

# Setup logger
logger = logging.getLogger(__name__)


def parse_test_args() -> argparse.Namespace:
    """Parse command line arguments for the testing tool.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="MongoDB PHI Masking Test Tool")
    parser.add_argument(
        "--config",
        default="config/config_rules/masking_config.json",
        help="Path to configuration file",
    )
    parser.add_argument("--env", default=".env.test", help="Path to environment file")
    parser.add_argument("--input", help="Path to input JSON file containing test documents")
    parser.add_argument("--output", help="Path to output JSON file for masked documents")
    parser.add_argument(
        "--source",
        action="store_true",
        help="Use source collection for test documents",
    )
    parser.add_argument(
        "--field",
        action="append",
        help="Specific field to check (can be used multiple times)",
    )
    parser.add_argument("--limit", type=int, default=10, help="Maximum documents to process")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level",
    )
    parser.add_argument("--log-file", type=str, help="Custom log file path")
    parser.add_argument(
        "--log-max-bytes",
        type=int,
        default=10 * 1024 * 1024,
        help="Maximum log file size before rotation (default: 10MB)",
    )
    parser.add_argument(
        "--log-backup-count", type=int, default=5, help="Number of backup log files to keep (default: 5)"
    )
    parser.add_argument(
        "--log-timed-rotation", action="store_true", help="Use time-based rotation instead of size-based"
    )

    return parser.parse_args()


def load_test_documents(input_file: str) -> list[dict[str, Any]]:
    """Load test documents from a file.

    Args:
        input_file: Path to input file

    Returns:
        List of test documents
    """
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    try:
        with open(input_file) as f:
            # Check if file is a JSON array or a JSONL file
            content = f.read().strip()
            if content.startswith("[") and content.endswith("]"):
                # JSON array
                docs = json.loads(content)
            else:
                # JSONL file (one JSON object per line)
                f.seek(0)
                docs = [json.loads(line) for line in f if line.strip()]

        logger.info(f"Loaded {len(docs)} test documents from {input_file}")
        return docs
    except Exception as e:
        logger.error(f"Error loading test documents: {str(e)}")
        sys.exit(1)


def save_masked_documents(docs: list[dict[str, Any]], output_file: str) -> None:
    """Save masked documents to a file.

    Args:
        docs: List of masked documents
        output_file: Path to output file
    """
    try:
        with open(output_file, "w") as f:
            json.dump(docs, f, indent=2, default=str)

        logger.info(f"Saved {len(docs)} masked documents to {output_file}")
    except Exception as e:
        logger.error(f"Error saving masked documents: {str(e)}")


def compare_documents(
    original_docs: list[dict[str, Any]],
    masked_docs: list[dict[str, Any]],
    fields: list[str] | None = None,
) -> dict[str, Any]:
    """Compare original and masked documents to verify masking.

    Args:
        original_docs: List of original documents
        masked_docs: List of masked documents
        fields: List of fields to verify (None for all fields)

    Returns:
        Comparison results
    """
    if len(original_docs) != len(masked_docs):
        logger.warning(f"Document count mismatch: {len(original_docs)} original vs {len(masked_docs)} masked")

    # Fields to verify
    phi_fields = fields or [
        # Basic PHI fields
        "FirstName",
        "LastName",
        "MiddleName",
        "FirstNameLower",
        "LastNameLower",
        "MiddleNameLower",
        "Email",
        "Dob",
        "HealthPlanMemberId",
        # Address fields
        "Address_City",
        "Address_StateCode",
        "Address_StateName",
        "Address_Street1",
        "Address_Street2",
        "Address_Zip5",
        # Phone fields
        "Phones_PhoneNumber",
        "PatientCallLog_PhoneNumber",
        "Insurance_PhoneNumber",
        # Name fields in nested structures
        "DocuSign_UserName",
        "PatientCallLog_PatientName",
        "Insurance_PrimaryMemberName",
        # Notes fields that might contain PHI
        "Allergies_Notes",
        "PatientCallLog_Notes",
        "PatientDat_Notes",
        "Phones_Notes",
        # Visit address
        "PatientCallLog_VisitAddress",
    ]

    # Track results
    results = {
        "total_documents": min(len(original_docs), len(masked_docs)),
        "masked_fields": {},
        "unmasked_fields": {},
        "field_mismatch": {},  # Fields present in original but not in masked or vice versa
    }

    # Compare documents
    for i, (original, masked) in enumerate(zip(original_docs, masked_docs[: len(original_docs)], strict=False)):
        logger.debug(f"Comparing document {i+1}/{results['total_documents']}")

        # Verify _id is preserved
        if "_id" in original and "_id" in masked and original["_id"] != masked["_id"]:
            logger.warning(f"Document {i+1}: _id mismatch: {original['_id']} vs {masked['_id']}")

        # Verify PHI fields are masked
        for field in phi_fields:
            if field in original:
                # Field is in original document
                if field not in masked:
                    # Field is missing in masked document
                    logger.warning(f"Document {i+1}: Field {field} is missing in masked document")
                    results["field_mismatch"][field] = results["field_mismatch"].get(field, 0) + 1
                    continue

                # Check if field was masked
                original_value = original[field]
                masked_value = masked[field]

                if original_value is None:
                    # Skip null values
                    continue

                if original_value == masked_value and original_value is not None and str(original_value).strip():
                    # Field wasn't masked
                    logger.warning(f"Document {i+1}: Field {field} was not masked: {original_value}")
                    results["unmasked_fields"][field] = results["unmasked_fields"].get(field, 0) + 1
                else:
                    # Field was masked
                    logger.debug(f"Document {i+1}: Field {field} was masked: {original_value} -> {masked_value}")
                    results["masked_fields"][field] = results["masked_fields"].get(field, 0) + 1

    # Calculate overall results
    total_fields_checked = sum(results["masked_fields"].values()) + sum(results["unmasked_fields"].values())
    if total_fields_checked > 0:
        results["masking_success_rate"] = sum(results["masked_fields"].values()) / total_fields_checked
    else:
        results["masking_success_rate"] = 0

    # Log summary
    logger.info("Masking verification results:")
    logger.info(f"  Documents compared: {results['total_documents']}")
    logger.info(f"  Fields masked successfully: {len(results['masked_fields'])}")
    logger.info(f"  Fields not masked: {len(results['unmasked_fields'])}")
    logger.info(f"  Fields with mismatch: {len(results['field_mismatch'])}")
    logger.info(f"  Overall masking success rate: {results['masking_success_rate']*100:.1f}%")

    if results["unmasked_fields"]:
        logger.warning(f"Unmasked fields: {', '.join(results['unmasked_fields'].keys())}")

    return results


def test_masking(args: argparse.Namespace) -> int:
    """Test masking functionality.

    Args:
        args: Command line arguments

    Returns:
        Exit code
    """
    # Setup logging with enhanced options
    setup_logging(
        log_level=args.log_level,
        log_file=args.log_file,
        max_bytes=args.log_max_bytes,
        backup_count=args.log_backup_count,
        use_timed_rotating=args.log_timed_rotation,
    )
    logger.info("Starting MongoDB PHI Masking Testing Tool")

    try:
        # Load configuration
        config_loader = ConfigLoader(args.config, args.env)
        config = config_loader.load_config()

        # Create orchestrator
        orchestrator = MaskingOrchestrator(config)

        # Load test documents
        if args.source:
            # Load from source collection
            logger.info("Loading test documents from source collection...")
            orchestrator.start()
            docs = list(orchestrator.source_connector.find_documents(limit=args.limit))
            logger.info(f"Loaded {len(docs)} test documents from source collection")
        elif args.input:
            # Load from input file
            docs = load_test_documents(args.input)
        else:
            # Create sample document
            logger.info("No input file or source specified, using sample document")
            docs = [
                {
                    "_id": "sample1",
                    "FirstName": "John",
                    "LastName": "Doe",
                    "Email": "john.doe@example.com",
                    "Dob": "1980-01-01",
                    "Phones_PhoneNumber": "123-456-7890",
                    "Address_Street1": "123 Main St",
                    "Address_City": "Anytown",
                    "Address_StateCode": "CA",
                    "Address_Zip5": "12345",
                    "PatientCallLog_Notes": "Patient reported feeling better",
                }
            ]

        # Process test documents
        logger.info(f"Processing {len(docs)} test documents...")
        masked_docs = orchestrator.process_test_documents(docs)

        # Save masked documents if output file specified
        if args.output:
            save_masked_documents(masked_docs, args.output)

        # Compare documents
        results = compare_documents(docs, masked_docs, args.field)

        # Determine success or failure
        if results["unmasked_fields"]:
            logger.error("Masking test failed: Some fields were not masked")
            return 1
        else:
            logger.info("Masking test completed successfully!")
            return 0

    except Exception as e:
        logger.error(f"Error during masking test: {str(e)}", exc_info=True)
        return 1
    finally:
        # Clean up resources
        if "orchestrator" in locals():
            orchestrator.stop()


def main() -> int:
    """Main entry point for testing.

    Returns:
        Exit code
    """
    args = parse_test_args()
    return test_masking(args)


if __name__ == "__main__":
    sys.exit(main())
