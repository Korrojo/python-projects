#!/usr/bin/env python3
"""
Verify PHI masking results by comparing original vs masked documents.

Usage:
    python scripts/verify_masking.py --src-env LOCL --dst-env LOCL --src-db local-phi-unmasked --dst-db local-phi-masked --collection Patients
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import pymongo

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.env_config import get_env_config, load_shared_config


def compare_documents(original_db, masked_db, collection_name, logger, sample_size=5):
    """Compare original and masked documents."""
    logger.info("=" * 70)
    logger.info(f"Verifying Masking Results: {collection_name}")
    logger.info("=" * 70)

    # Get sample documents
    original_docs = list(original_db[collection_name].find().limit(sample_size))
    masked_docs = list(masked_db[collection_name].find().limit(sample_size))

    if len(original_docs) != len(masked_docs):
        logger.warning(
            f"Document count mismatch! "
            f"Original: {original_db[collection_name].count_documents({})}, "
            f"Masked: {masked_db[collection_name].count_documents({})}"
        )

    logger.info(f"Comparing {len(original_docs)} sample documents...")
    logger.info("")

    issues_found = []
    checks_passed = []

    for i, (orig, masked) in enumerate(zip(original_docs, masked_docs), 1):
        logger.info(f"Document {i}:")
        logger.info(f"  _id: {orig['_id']}")

        # Check FirstName
        if "FirstName" in orig and "FirstName" in masked:
            if orig["FirstName"] == masked["FirstName"]:
                issues_found.append(f"Doc {i}: FirstName not masked ({orig['FirstName']})")
                logger.error(f"  FirstName: NOT MASKED ({orig['FirstName']})")
            else:
                checks_passed.append(f"Doc {i}: FirstName masked")
                logger.info(f"  FirstName: {orig['FirstName']} → {masked['FirstName']}")

        # Check LastName
        if "LastName" in orig and "LastName" in masked:
            if orig["LastName"] == masked["LastName"]:
                issues_found.append(f"Doc {i}: LastName not masked ({orig['LastName']})")
                logger.error(f"  LastName: NOT MASKED ({orig['LastName']})")
            else:
                checks_passed.append(f"Doc {i}: LastName masked")
                logger.info(f"  LastName: {orig['LastName']} → {masked['LastName']}")

        # Check Email
        if "Email" in orig and "Email" in masked:
            if orig["Email"] == masked["Email"]:
                issues_found.append(f"Doc {i}: Email not masked ({orig['Email']})")
                logger.error(f"  Email: NOT MASKED ({orig['Email']})")
            else:
                checks_passed.append(f"Doc {i}: Email masked")
                logger.info(f"  Email: {orig['Email']} → {masked['Email']}")

        # Check Gender (should be "Female")
        if "Gender" in masked:
            if masked["Gender"] == "Female":
                checks_passed.append(f"Doc {i}: Gender set to Female")
                logger.info(f"  Gender: {orig.get('Gender', 'N/A')} → {masked['Gender']}")
            else:
                issues_found.append(f"Doc {i}: Gender not set to Female ({masked['Gender']})")
                logger.error(f"  Gender: NOT SET TO FEMALE ({masked['Gender']})")

        # Check lowercase consistency
        if "FirstName" in masked and "FirstNameLower" in masked:
            if masked["FirstName"].lower() == masked["FirstNameLower"]:
                checks_passed.append(f"Doc {i}: FirstNameLower matches")
                logger.info("  FirstNameLower: matches lowercase of FirstName")
            else:
                issues_found.append(
                    f"Doc {i}: FirstNameLower mismatch "
                    f"({masked['FirstName'].lower()} != {masked['FirstNameLower']})"
                )
                logger.error(
                    f"  FirstNameLower: MISMATCH " f"({masked['FirstName'].lower()} != {masked['FirstNameLower']})"
                )

        # Check Dob (should be shifted)
        if "Dob" in orig and "Dob" in masked:
            if orig["Dob"] == masked["Dob"]:
                issues_found.append(f"Doc {i}: Dob not shifted ({orig['Dob']})")
                logger.error(f"  Dob: NOT SHIFTED ({orig['Dob']})")
            else:
                checks_passed.append(f"Doc {i}: Dob shifted")
                logger.info(f"  Dob: {orig['Dob']} → {masked['Dob']}")

        logger.info("")

    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Checks Passed: {len(checks_passed)}")
    logger.info(f"Issues Found: {len(issues_found)}")

    if issues_found:
        logger.info("")
        logger.info("Issues:")
        for issue in issues_found:
            logger.error(f"  - {issue}")

    logger.info("")
    logger.info("=" * 70)

    return len(issues_found) == 0


def main():
    """Main verification function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Verify PHI masking results by comparing original vs masked documents")
    parser.add_argument(
        "--src-env",
        required=True,
        help="Source environment (LOCL, DEV, STG, PROD, etc.)",
    )
    parser.add_argument(
        "--dst-env",
        required=True,
        help="Destination environment (LOCL, DEV, STG, PROD, etc.)",
    )
    parser.add_argument(
        "--src-db",
        required=True,
        help="Source database name (e.g., local-phi-unmasked)",
    )
    parser.add_argument(
        "--dst-db",
        required=True,
        help="Destination database name (e.g., local-phi-masked)",
    )
    parser.add_argument(
        "--collection",
        required=True,
        help="Collection name to verify (e.g., Patients)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=5,
        help="Number of sample documents to compare (default: 5)",
    )

    args = parser.parse_args()

    # Setup logging - create logs/verification directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path("logs/verification")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{timestamp}_verify_{args.collection}.log"

    # Configure logging with unified format
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger(__name__)

    logger.info("=" * 70)
    logger.info("PHI Masking Verification")
    logger.info("=" * 70)
    logger.info(f"Source: {args.src_env} / {args.src_db}")
    logger.info(f"Destination: {args.dst_env} / {args.dst_db}")
    logger.info(f"Collection: {args.collection}")
    logger.info(f"Sample size: {args.sample_size}")
    logger.info(f"Log file: {log_file}")
    logger.info("")

    # Load shared configuration
    load_shared_config()

    # Get source configuration
    src_config = get_env_config(args.src_env)
    src_uri = src_config["uri"]

    # Get destination configuration
    dst_config = get_env_config(args.dst_env)
    dst_uri = dst_config["uri"]

    # Mask credentials in logs
    def mask_uri(uri):
        if "@" in uri:
            protocol = uri.split("://")[0]
            host = uri.split("@")[1].split("/")[0]
            return f"{protocol}://***:***@{host}"
        return uri

    logger.info(f"Source URI: {mask_uri(src_uri)}")
    logger.info(f"Destination URI: {mask_uri(dst_uri)}")
    logger.info("")

    # Connect to databases
    try:
        logger.info("Connecting to source database...")
        src_client = pymongo.MongoClient(src_uri)
        src_db = src_client[args.src_db]

        logger.info("Connecting to destination database...")
        dst_client = pymongo.MongoClient(dst_uri)
        dst_db = dst_client[args.dst_db]

        # Verify connections
        src_client.admin.command("ping")
        dst_client.admin.command("ping")
        logger.info("Database connections established")
        logger.info("")

        # Verify collection
        success = compare_documents(
            src_db,
            dst_db,
            args.collection,
            logger,
            sample_size=args.sample_size,
        )

        # Close connections
        src_client.close()
        dst_client.close()

        logger.info("")
        if success:
            logger.info("All verification checks passed!")
            return 0
        else:
            logger.error("Some verification checks failed. Review the issues above.")
            return 1

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
