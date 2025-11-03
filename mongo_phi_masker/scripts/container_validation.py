#!/usr/bin/env python3
"""
Container Masking Validation Script

This script validates that PHI data in the Container collection has been properly
masked according to defined rules, with special handling for the nested Encounter array.
"""

import argparse
import json
import logging
import os
import re
from datetime import datetime

from pymongo import MongoClient


def setup_logging(
    log_level="INFO", log_file=None, max_bytes=10 * 1024 * 1024, backup_count=5, use_timed_rotating=False
):
    """Set up logging configuration with rotation options.

    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str): Path to log file, if None a default path is generated
        max_bytes (int): Maximum size in bytes before rotating the log file
        backup_count (int): Number of backup files to keep
        use_timed_rotating (bool): If True, use time-based rotation instead of size-based
    """
    # Override settings from environment variables if present
    max_bytes = int(os.environ.get("LOG_MAX_BYTES", max_bytes))
    backup_count = int(os.environ.get("LOG_BACKUP_COUNT", backup_count))
    use_timed_rotating = os.environ.get("LOG_TIMED_ROTATION", str(use_timed_rotating)).lower() == "true"

    log_dir = "logs/validation"
    os.makedirs(log_dir, exist_ok=True)

    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rotation_type = "time" if use_timed_rotating else "size"
        log_file = f"{log_dir}/container_validation_{timestamp}_{rotation_type}.log"

        # Create a symlink to the latest log
        latest_log = f"{log_dir}/container_validation_latest.log"
        if os.path.exists(latest_log):
            try:
                os.remove(latest_log)
            except:
                pass
        try:
            os.symlink(log_file, latest_log)
        except:
            pass

    # Set up logging format
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Use the appropriate handler based on rotation type
    if use_timed_rotating:
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file, when="midnight", interval=1, backupCount=backup_count
        )
    else:
        file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configure the root logger
    root_logger = logging.getLogger()

    # Convert string log level to numeric if needed
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger.setLevel(log_level)

    # Remove existing handlers if any
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add the handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Create the module logger
    logger = logging.getLogger(__name__)

    # Log initialization message
    rotation_msg = "time-based" if use_timed_rotating else f"size-based ({max_bytes/1024/1024:.1f}MB max)"
    logger.info(
        f"Logging initialized with level={logging.getLevelName(log_level)}, file={log_file}, rotation={rotation_msg}"
    )

    return logger


# MongoDB connection settings
def get_mongodb_uri(env_prefix):
    """Generate MongoDB URI from environment variables."""
    username = os.environ.get(f"{env_prefix}_USERNAME")
    password = os.environ.get(f"{env_prefix}_PASSWORD")
    host = os.environ.get(f"{env_prefix}_HOST")
    use_srv = os.environ.get(f"{env_prefix}_USE_SRV", "false").lower() == "true"

    protocol = "mongodb+srv" if use_srv else "mongodb"
    return f"{protocol}://{username}:{password}@{host}"


def get_nested_value(document, path):
    """Get a value from a nested document using dot notation and array indexing.

    For paths with array iteration (using []), returns all matching values as a list.
    For regular paths, returns the single matching value.
    """
    if not document:
        return None

    # Handle special array iteration path syntax ([] indicates any array element)
    if "[]" in path:
        base_path, rest_path = path.split("[]", 1)
        if rest_path.startswith("."):
            rest_path = rest_path[1:]  # Remove leading dot if present

        base_value = get_nested_value(document, base_path)

        if not isinstance(base_value, list):
            return None

        # Process all elements in the array
        results = []
        for item in base_value:
            value = get_nested_value(item, rest_path)
            if value is not None:
                if isinstance(value, list):  # Handle nested array results
                    results.extend(value)
                else:
                    results.append(value)

        return results if results else None

    # Regular path handling
    parts = path.split(".")
    current = document

    for part in parts:
        # Handle array indexing (e.g., "Encounter[0]")
        if "[" in part and part.endswith("]"):
            array_name, idx_str = part.split("[")
            idx = int(idx_str[:-1])  # Remove closing bracket and convert to int

            if not isinstance(current, dict) or array_name not in current:
                return None

            array_value = current[array_name]
            if not isinstance(array_value, list) or idx >= len(array_value):
                return None

            current = array_value[idx]
        else:
            # Regular dict access
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]

    return current


def validate_field_value(source_value, dest_value, field_config):
    """Validate that a field has been properly masked."""
    validation_type = field_config["type"]

    # If source was None/null, dest should also be None/null
    if source_value is None:
        return dest_value is None

    # Skip empty values for certain types
    if isinstance(source_value, str) and not source_value.strip():
        return True

    # Different validation logic based on masking type
    if validation_type == "replace_string":
        return dest_value == field_config["value"]

    elif validation_type == "random_uppercase":
        # Should be all uppercase and not equal to source
        return (
            dest_value is not None
            and isinstance(dest_value, str)
            and dest_value.isupper()
            and dest_value != source_value
        )

    elif validation_type == "replace_email":
        return dest_value == "xxxxxx@xxxx.com"

    elif validation_type == "random_10_digit_number":
        # Should be a 10-digit number
        return dest_value is not None and re.match(field_config["pattern"], str(dest_value))

    elif validation_type == "replace_path":
        return dest_value == field_config["value"]

    # Add more validation types as needed

    return False


def validate_container_masking(sample_size=100, logger=None):
    """Validate PHI masking in Container collection."""
    if logger is None:
        logger = logging.getLogger(__name__)

    # Connect to source MongoDB (original data)
    source_uri = get_mongodb_uri("MONGO_SOURCE")
    source_client = MongoClient(source_uri)
    source_db = source_client[os.environ.get("MONGO_SOURCE_DB")]
    source_coll = source_db[os.environ.get("MONGO_SOURCE_COLL")]

    # Connect to destination MongoDB (masked data)
    dest_uri = get_mongodb_uri("MONGO_DEST")
    dest_client = MongoClient(dest_uri)
    dest_db = dest_client[os.environ.get("MONGO_DEST_DB")]
    dest_coll = dest_db[os.environ.get("MONGO_DEST_COLL")]

    logger.info(f"Starting Container masking validation with sample size {sample_size}")
    logger.info(f"Source DB: {os.environ.get('MONGO_SOURCE_DB')}.{os.environ.get('MONGO_SOURCE_COLL')}")
    logger.info(f"Destination DB: {os.environ.get('MONGO_DEST_DB')}.{os.environ.get('MONGO_DEST_COLL')}")

    # Get sample documents for validation
    pipeline = [{"$sample": {"size": sample_size}}]
    sample_ids = [doc["_id"] for doc in source_coll.aggregate(pipeline, allowDiskUse=True)]

    validation_results = {
        "total_documents": sample_size,
        "documents_checked": 0,
        "documents_passed": 0,
        "documents_failed": 0,
        "field_validation": {
            # Track how many times each field was validated
        },
    }

    # Define fields to validate with their expected masking outcomes
    field_validations = [
        # Direct fields with array notation
        {"path": "Encounter[].PatientFirstName", "type": "random_uppercase", "case_sensitive": True},
        {"path": "Encounter[].PatientMiddleName", "type": "random_uppercase", "case_sensitive": True},
        {"path": "Encounter[].PatientLastName", "type": "random_uppercase", "case_sensitive": True},
        {"path": "Encounter[].UserName", "type": "random_uppercase", "case_sensitive": True},
        {"path": "Encounter[].CaseNote.Notes", "type": "replace_string", "value": "xxxxxxxxxx"},
        {"path": "Encounter[].HPI.HPINote", "type": "replace_string", "value": "xxxxxxxxxx"},
        {"path": "Encounter[].CareSnapshot.Goals", "type": "replace_string", "value": "xxxxxxxxxx"},
        # Array fields with nested arrays
        {"path": "Encounter[].PhoneCall.Activities[].VisitAddress", "type": "replace_string", "value": "xxxxxxxxxx"},
        {
            "path": "Encounter[].PhoneCall.Activities[].PhoneNumber",
            "type": "random_10_digit_number",
            "pattern": r"^\d{10}$",
        },
        {
            "path": "Encounter[].AssessmentAndPlan.ProblemList[].Comments",
            "type": "replace_string",
            "value": "xxxxxxxxxx",
        },
        {
            "path": "Encounter[].AssessmentAndPlan.ProblemList[].FinalNotes",
            "type": "replace_string",
            "value": "xxxxxxxxxx",
        },
        {"path": "Encounter[].Dat[].OtherReason", "type": "replace_string", "value": "xxxxxxxxxx"},
        {
            "path": "Encounter[].Document.Documents[].Path",
            "type": "replace_path",
            "value": "//vm_fs01/Projects/EMRQAReports/sampledoc.pdf",
        },
    ]

    # Initialize field validation counters
    for field_config in field_validations:
        path = field_config["path"]
        validation_results["field_validation"][path] = {"checked": 0, "passed": 0, "failed": 0, "not_found": 0}

    # Validate each document
    for doc_id in sample_ids:
        source_doc = source_coll.find_one({"_id": doc_id})
        dest_doc = dest_coll.find_one({"_id": doc_id})

        if not source_doc or not dest_doc:
            logger.warning(f"Document with _id {doc_id} not found in both collections")
            continue

        validation_results["documents_checked"] += 1
        doc_passed = True

        # Validate each field
        for field_config in field_validations:
            path = field_config["path"]

            # Get values from source and destination documents
            source_values = get_nested_value(source_doc, path)
            dest_values = get_nested_value(dest_doc, path)

            # Skip if field not found in source
            if source_values is None:
                validation_results["field_validation"][path]["not_found"] += 1
                continue

            # Convert to list if not already
            if not isinstance(source_values, list):
                source_values = [source_values]

            if not isinstance(dest_values, list):
                dest_values = [dest_values] if dest_values is not None else []

            # Check if we have matching number of values
            if len(source_values) != len(dest_values):
                logger.warning(
                    f"Document {doc_id}: Field {path} has {len(source_values)} values in source but {len(dest_values)} in destination"
                )
                doc_passed = False
                validation_results["field_validation"][path]["failed"] += len(source_values)
                continue

            # Validate each value
            for i, (source_value, dest_value) in enumerate(zip(source_values, dest_values, strict=False)):
                validation_results["field_validation"][path]["checked"] += 1

                if validate_field_value(source_value, dest_value, field_config):
                    validation_results["field_validation"][path]["passed"] += 1
                else:
                    validation_results["field_validation"][path]["failed"] += 1
                    doc_passed = False
                    logger.warning(f"Field validation failed: {path}[{i}] in document {doc_id}")

        # Update document results
        if doc_passed:
            validation_results["documents_passed"] += 1
        else:
            validation_results["documents_failed"] += 1

    # Log summary
    logger.info("Container Masking Validation Summary:")
    logger.info(f"Documents checked: {validation_results['documents_checked']}")
    logger.info(f"Documents passed: {validation_results['documents_passed']}")
    logger.info(f"Documents failed: {validation_results['documents_failed']}")
    logger.info("Field validation results:")

    for field, stats in validation_results["field_validation"].items():
        pass_rate = (stats["passed"] / stats["checked"] * 100) if stats["checked"] > 0 else 0
        logger.info(
            f"  {field}: {pass_rate:.1f}% passed ({stats['passed']}/{stats['checked']} checked, {stats['not_found']} not found)"
        )

    # Cleanup
    source_client.close()
    dest_client.close()

    return validation_results


def main():
    """Main entry point for container validation script."""
    parser = argparse.ArgumentParser(description="Validate Container collection masking")
    parser.add_argument("--sample-size", type=int, default=100, help="Number of documents to sample for validation")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level",
    )
    parser.add_argument(
        "--config", default="config/validation/container_fields.json", help="Path to field validation config"
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

    args = parser.parse_args()

    # Setup enhanced logging
    logger = setup_logging(
        log_level=args.log_level,
        log_file=args.log_file,
        max_bytes=args.log_max_bytes,
        backup_count=args.log_backup_count,
        use_timed_rotating=args.log_timed_rotation,
    )

    # Load appropriate .env file
    env_file = f".env.{args.env}"
    if not os.path.isfile(env_file):
        logger.error(f"Environment file {env_file} not found")
        return 1

    from dotenv import load_dotenv

    load_dotenv(env_file)
    logger.info(f"Loaded environment from {env_file}")

    # Run validation
    validation_results = validate_container_masking(sample_size=args.sample_size, logger=logger)

    # Save results to file
    results_dir = "logs/validation"
    os.makedirs(results_dir, exist_ok=True)
    results_file = f"{results_dir}/container_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(results_file, "w") as f:
        json.dump(validation_results, f, indent=2)

    logger.info(f"Results saved to {results_file}")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
