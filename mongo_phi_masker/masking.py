#!/usr/bin/env python
"""
Bridge script for MongoDB PHI Masker with improved field matching.
"""

import argparse
import copy
import gc  # Import garbage collector for explicit memory management
import json
import logging
import logging.handlers
import os
import random
import re
import string
import sys
import time
from datetime import datetime
from pathlib import Path

import pymongo
from bson import ObjectId  # Add json_util for BSON serialization
from dotenv import load_dotenv

# Try to import psutil for memory monitoring, but don't fail if not available
try:
    import psutil

    MEMORY_TRACKING_AVAILABLE = True
except ImportError:
    MEMORY_TRACKING_AVAILABLE = False

# Assuming the script is run from the project root or its path is correctly resolved
PROJECT_ROOT = Path(__file__).parent.parent  # Adjust if necessary
sys.path.append(str(PROJECT_ROOT))


# Custom JSON encoder for MongoDB ObjectId
class ObjectIdEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)


def redact_uri(uri):
    """Redact sensitive information from URI."""
    if not uri:
        return None

    # Replace username:password with ***:*** if present
    redacted = re.sub(r"//([^@:]+):([^@]+)@", "//***:***@", uri)

    # If there's no auth info, just return the URL structure
    if "//" in redacted and "@" not in redacted:
        host_part = redacted.split("//")[1]
        redacted = redacted.replace(host_part, f"host:{host_part.split(':')[-1]}")

    return redacted


def build_mongo_uri(prefix, logger=None, db_name=None, coll_name=None):
    """Build or retrieve MongoDB URI from environment variables.

    Priority:
    1. Use {prefix}_URI if it exists (full connection string from shared_config)
    2. Otherwise build from component variables for backward compatibility
    """
    # PRIORITY 1: Check if full URI already exists (from shared_config/.env)
    existing_uri = os.getenv(f"{prefix}_URI")
    if existing_uri:
        if logger:
            # Mask credentials in log - show only protocol and host
            if "mongodb+srv://" in existing_uri or "mongodb://" in existing_uri:
                # Extract protocol
                protocol = existing_uri.split("://")[0] + "://"
                # Extract host (after @ if credentials exist, otherwise after protocol)
                if "@" in existing_uri:
                    host_part = existing_uri.split("@")[1].split("/")[0].split("?")[0]
                    masked_uri = f"{protocol}***:***@{host_part}"
                else:
                    host_part = existing_uri.split("://")[1].split("/")[0].split("?")[0]
                    masked_uri = f"{protocol}{host_part}"
            else:
                masked_uri = "[REDACTED]"

            namespace_info = ""
            if db_name and coll_name:
                namespace_info = f", Namespace={db_name}.{coll_name}"

            logger.info(f"Using existing {prefix}_URI: {masked_uri}{namespace_info}")

        return existing_uri

    # PRIORITY 2: Build from components (backward compatibility)
    username = os.getenv(f"{prefix}_USERNAME", "")
    password = os.getenv(f"{prefix}_PASSWORD", "")
    host = os.getenv(f"{prefix}_HOST", "localhost")
    port = os.getenv(f"{prefix}_PORT", "27017")
    auth_db = os.getenv(f"{prefix}_AUTH_DB", "admin")
    use_ssl = os.getenv(f"{prefix}_USE_SSL", "false").lower() == "true"
    use_srv = os.getenv(f"{prefix}_USE_SRV", "false").lower() == "true"

    if logger:
        logger.info(f"Building {prefix} URI from components:")
        logger.info(f"  {prefix}_USERNAME: {username}")
        logger.info(f"  {prefix}_PASSWORD: ***")
        logger.info(f"  {prefix}_HOST: {host}")
        logger.info(f"  {prefix}_PORT: {port}")
        logger.info(f"  {prefix}_AUTH_DB: {auth_db}")
        logger.info(f"  {prefix}_USE_SSL: {use_ssl}")
        logger.info(f"  {prefix}_USE_SRV: {use_srv}")

    # Auth string (if credentials provided)
    auth_string = ""
    if username and password:
        auth_string = f"{username}:{password}@"

    # Protocol (mongodb:// or mongodb+srv://)
    protocol = "mongodb+srv://" if use_srv else "mongodb://"

    # Host and port (SRV doesn't use port)
    host_part = host if use_srv else f"{host}:{port}"

    # SSL options
    options = []
    if auth_db:
        options.append(f"authSource={auth_db}")
    if use_ssl:
        options.append("ssl=true")

    options_str = "&".join(options)
    if options_str:
        options_str = f"?{options_str}"

    # Build final URI
    uri = f"{protocol}{auth_string}{host_part}/{options_str}"

    if logger:
        namespace_info = ""
        if db_name and coll_name:
            namespace_info = f", Namespace={db_name}.{coll_name}"
        logger.info(f"Built URI: {protocol}***@{host_part}{namespace_info}")

    return uri


def setup_logging(
    log_level="INFO",
    log_file=None,
    max_bytes=10 * 1024 * 1024,
    backup_count=5,
    use_timed_rotating=False,
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

    if log_file is None:
        # Check if we're running as part of a multi-collection run
        run_log_dir = os.environ.get("PHI_RUN_LOG_DIR")

        if run_log_dir:
            # Use the run-specific log directory
            log_dir = run_log_dir
        else:
            # Use the default base log directory (cross-platform)
            log_dir = "logs/masking"

        # Create logs directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)

        # Generate timestamped log filename with your naming convention
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Check if this is single collection processing
        collection_name = None
        for i, arg in enumerate(sys.argv):
            if arg == "--collection" and i + 1 < len(sys.argv):
                collection_name = sys.argv[i + 1]
                break

        if collection_name:
            # Single collection processing
            log_file = f"{log_dir}/mask_{collection_name}_{timestamp}.log"
        else:
            # Multi-collection processing (fallback, orchestration script handles this)
            log_file = f"{log_dir}/mask_parallel_{timestamp}.log"

    # Set up logging format and level
    # Use consistent format across project: YYYY-MM-DD HH:MM:SS | LEVEL | message
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler with appropriate rotation
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

    # Root logger configuration
    root_logger = logging.getLogger()

    # Convert string log level to numeric if needed
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger.setLevel(log_level)

    # Remove existing handlers if any
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Log initialization message
    logger = logging.getLogger(__name__)
    rotation_msg = "time-based" if use_timed_rotating else f"size-based ({max_bytes/1024/1024:.1f}MB max)"
    logger.info(
        f"Logging initialized with level={logging.getLevelName(log_level)}, file={log_file}, rotation={rotation_msg}"
    )

    return logger


def extract_key_fields(document):
    """Extract key fields from a document using the aggregation pipeline."""
    result = {}

    # This maps to your aggregation.js pipeline
    field_mappings = {
        "_id": "_id",
        "FirstName": "FirstName",
        "FirstNameLower": "FirstNameLower",
        "LastName": "LastName",
        "LastNameLower": "LastNameLower",
        "MiddleName": "MiddleName",
        "MiddleNameLower": "MiddleNameLower",
        "Address_Street1": "Address.0.Street1",
        "Address_City": "Address.0.City",
        "Phones_PhoneNumber": "Phones.0.PhoneNumber",
        "Email": "Email",
        "Gender": "Gender",
        "Dob": "Dob",  # Add Dob field for validation
        # Add other fields you want to validate
    }

    # Extract fields using the mapping
    for result_key, doc_path in field_mappings.items():
        value = get_nested_field(document, doc_path)
        if value is not None:
            result[result_key] = value

    return result


def get_nested_field(document, doc_path):
    """Get a nested field value from a document."""
    parts = doc_path.split(".")

    current = document
    for part in parts:
        # Handle array access
        if part.isdigit() and isinstance(current, list):
            index = int(part)
            if index < len(current):
                current = current[index]
            else:
                return None
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None

    return current


def validate_masked_document(original_doc, masked_doc, logger):
    """Validate that a document was masked properly."""
    logger.info("Comparing original and masked documents:")

    # Extract fields using the aggregation.js structure
    original_fields = extract_key_fields(original_doc)
    masked_fields = extract_key_fields(masked_doc)

    # Check fields that should be masked
    for field in [
        "FirstName",
        "FirstNameLower",
        "MiddleName",
        "MiddleNameLower",
        "LastName",
        "LastNameLower",
        "Address_Street1",
        "Phones_PhoneNumber",
        "Email",
        "Dob",  # Add Dob to the validation list
    ]:
        if field in original_fields and field in masked_fields:
            original_value = original_fields[field]
            masked_value = masked_fields[field]

            if original_value == masked_value and original_value:  # Skip empty values
                logger.warning(f"❌ {field} was not masked: {original_value}")
            else:
                logger.info(f"✓ {field} masked: {masked_value}")

    # Special check for Gender - should always be "Female" regardless of original value
    if "Gender" in masked_fields:
        if masked_fields["Gender"] == "Female":
            logger.info("✓ Gender masked to Female")
        else:
            logger.warning(f"❌ Gender was not correctly masked to Female: {masked_fields['Gender']}")

    # Special check for Dob - ensure it's properly shifted by milliseconds
    if "Dob" in original_fields and "Dob" in masked_fields and original_fields["Dob"] and masked_fields["Dob"]:
        original_dob = original_fields["Dob"]
        masked_dob = masked_fields["Dob"]
        if original_dob == masked_dob:
            logger.warning(f"❌ Dob was not shifted with add_milliseconds: {original_dob}")
        else:
            logger.info(f"✓ Dob masked to {masked_dob}")

    # Check lowercase consistency
    name_pairs = [
        ("FirstName", "FirstNameLower"),
        ("LastName", "LastNameLower"),
        ("MiddleName", "MiddleNameLower"),
    ]

    for upper, lower in name_pairs:
        if upper in masked_fields and lower in masked_fields and masked_fields[upper]:
            if masked_fields[upper].lower() == masked_fields[lower]:
                logger.info(f"✓ {lower} correctly matches lowercase of {upper}")
            else:
                logger.warning(f"❌ {lower} mismatch: {masked_fields[lower]} != {masked_fields[upper].lower()}")


def should_validate_collection(collection_name):
    """Determine if this collection should be validated."""
    # Always validate all collections
    return True


def run_masking(
    config_path: str,
    env_path: str,
    collection: str | None = None,
    in_situ: bool = False,
    reset_checkpoint: bool = False,
    log_file: str | None = None,
) -> int:
    """
    Programmatic entry point for PHI masking.

    Args:
        config_path: Path to configuration JSON file
        env_path: Path to environment file (.env)
        collection: Optional specific collection to process
        in_situ: Enable in-situ masking (irreversible)
        reset_checkpoint: Reset checkpoint and start fresh
        log_file: Optional custom log file path

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Build sys.argv for main() function
    original_argv = sys.argv.copy()

    try:
        sys.argv = ["masking.py", "--config", config_path, "--env", env_path]

        if collection:
            sys.argv.extend(["--collection", collection])

        if in_situ:
            sys.argv.append("--in-situ")

        if reset_checkpoint:
            sys.argv.append("--reset-checkpoint")

        if log_file:
            sys.argv.extend(["--log-file", log_file])

        # Call the main function
        return main()

    finally:
        # Restore original sys.argv
        sys.argv = original_argv


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="MongoDB PHI Masker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment-based usage (recommended):
  python masking.py --config config.json --src-env LOCL --dst-env DEV --collection Patients
  python masking.py --config config.json --src-env DEV --dst-env DEV --src-db devdb --collection Patients

Legacy usage:
  python masking.py --config config.json --env .env --collection Patients
        """,
    )

    # Configuration file (required)
    parser.add_argument("--config", required=True, help="Path to configuration file")

    # Environment-based configuration (new approach)
    parser.add_argument(
        "--src-env",
        choices=["LOCL", "DEV", "STG", "TRNG", "PERF", "PRPRD", "PROD"],
        help="Source environment (loads from shared_config/.env)",
    )
    parser.add_argument(
        "--dst-env",
        choices=["LOCL", "DEV", "STG", "TRNG", "PERF", "PRPRD", "PROD"],
        help="Destination environment (loads from shared_config/.env)",
    )
    parser.add_argument("--src-db", help="Source database name (overrides DATABASE_NAME_{src_env})")
    parser.add_argument(
        "--dst-db",
        help="Destination database name (overrides DATABASE_NAME_{dst_env})",
    )

    # Legacy environment file (for backward compatibility)
    parser.add_argument("--env", help="Path to environment file (legacy mode, use --src-env instead)")

    # Collection and processing parameters
    parser.add_argument("--collection", help="Specific collection to process (optional)")
    parser.add_argument("--limit", type=int, help="Maximum number of documents to process")
    parser.add_argument("--query", help="MongoDB query to filter documents")
    parser.add_argument("--reset-checkpoint", action="store_true", help="Reset checkpoint")
    parser.add_argument("--verify-only", action="store_true", help="Only verify results")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # Batch processing parameters
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Override the default batch size from environment variable",
    )
    parser.add_argument("--log-file", type=str, help="Custom log file path")
    parser.add_argument(
        "--log-max-bytes",
        type=int,
        default=10 * 1024 * 1024,
        help="Maximum log file size before rotation (default: 10MB)",
    )
    parser.add_argument(
        "--log-backup-count",
        type=int,
        default=5,
        help="Number of backup log files to keep (default: 5)",
    )
    parser.add_argument(
        "--log-timed-rotation",
        action="store_true",
        help="Use time-based rotation instead of size-based",
    )
    parser.add_argument(
        "--in-situ",
        action="store_true",
        help="Perform in-situ masking (modify documents in-place instead of creating new ones)",
    )

    args = parser.parse_args()

    # Validate arguments
    using_env_presets = args.src_env or args.dst_env
    using_legacy_env = args.env

    if using_env_presets and using_legacy_env:
        print("ERROR: Cannot use both --src-env/--dst-env and --env together. " "Choose one approach.")
        return 1

    if not using_env_presets and not using_legacy_env:
        print("ERROR: Must specify either --src-env/--dst-env (recommended) or --env (legacy)")
        return 1

    if using_env_presets:
        if not args.src_env or not args.dst_env:
            print("ERROR: Both --src-env and --dst-env are required")
            return 1

    # Setup logging with enhanced options
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logging(
        log_level=log_level,
        log_file=args.log_file,
        max_bytes=args.log_max_bytes,
        backup_count=args.log_backup_count,
        use_timed_rotating=args.log_timed_rotation,
    )

    # Load environment variables
    if using_env_presets:
        # New approach: Load from shared_config using environment presets
        logger.info(f"Loading environment configuration: {args.src_env} → {args.dst_env}")
        try:
            from src.utils.env_config import setup_masking_env_vars

            src_uri, src_db_name, dst_uri, dst_db_name = setup_masking_env_vars(
                args.src_env, args.dst_env, args.src_db, args.dst_db
            )

            logger.info(f"Source: {args.src_env} / {src_db_name}")
            logger.info(f"Destination: {args.dst_env} / {dst_db_name}")

        except (ValueError, EnvironmentError) as e:
            logger.error(f"Environment configuration error: {e}")
            return 1
    else:
        # Legacy approach: Load from specified .env file
        logger.info(f"Loading environment from file: {args.env}")
        load_dotenv(args.env, override=True)

    # Load configuration
    if not os.path.exists(args.config):
        logger.error(f"Configuration file not found: {args.config}")
        return 1

    try:
        with open(args.config) as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return 1

    # Import the new module
    sys.path.insert(0, os.path.abspath("."))

    # Get masking configuration
    masking_config = config.get("masking", {})
    rules_path = masking_config.get("rules_path", "config/masking_rules/rules.json")

    # Parse query if provided
    query = None
    if args.query:
        try:
            query = json.loads(args.query)
        except json.JSONDecodeError:
            logger.error(f"Invalid query format: {args.query}")
            return 1

    # Use environment variable or a very large number if not specified
    limit = args.limit if args.limit is not None else int(os.getenv("PROCESSING_DOC_LIMIT", "9999999999"))

    try:
        # Import necessary components
        from src.core.connector import MongoConnector

        # Determine collections to process
        if args.collection:
            # When called with --collection, assume it's the one to process
            collections_to_process = [args.collection]
            logger.info(f"Processing specified collection: {args.collection}")
            # Set the environment variable to match command line input
            os.environ["MONGO_SOURCE_COLL"] = args.collection
            os.environ["MONGO_DEST_COLL"] = args.collection
        else:
            # Process all PHI collections from config
            collections_to_process = config.get("phi_collections", [])
            if not collections_to_process:
                logger.warning("No PHI collections specified via --collection and none found in config.json.")
                sys.exit(0)
            logger.info(
                f"Processing {len(collections_to_process)} PHI collections: {', '.join(collections_to_process)}"
            )

        # Process each collection
        for collection_name in collections_to_process:
            logger.info("\n==================================")
            logger.info(f"Processing collection: {collection_name}")
            logger.info("==================================\n")

            # Set the environment variable for current collection
            os.environ["MONGO_SOURCE_COLL"] = collection_name
            os.environ["MONGO_DEST_COLL"] = collection_name

            # Initialize MongoDB clients for this collection
            source_client, dest_client = None, None
            source, destination = None, None
            direct_client = None  # Initialize direct_client

            try:
                # Set up MongoDB connections for this specific collection
                source_db = os.getenv("MONGO_SOURCE_DB")
                source_coll = collection_name  # Use the current collection name directly

                dest_db = os.getenv("MONGO_DEST_DB")
                dest_coll = collection_name  # Use the current collection name directly

                # Build URIs for source and destination with db and collection info
                source_uri = build_mongo_uri("MONGO_SOURCE", logger, source_db, source_coll)
                dest_uri = build_mongo_uri("MONGO_DEST", logger, dest_db, dest_coll)

                # Store in environment for rest of script
                os.environ["MONGO_SOURCE_URI"] = source_uri
                os.environ["MONGO_DEST_URI"] = dest_uri

                # Log redacted URIs
                logger.info(f"Source URI: {redact_uri(source_uri)}")
                logger.info(f"Destination URI: {redact_uri(dest_uri)}")

                # Log source and destination namespaces
                logger.info(f"Source namespace: {source_db}.{source_coll}")
                logger.info(f"Destination namespace: {dest_db}.{dest_coll}")

                # Create fresh connectors for this collection
                source = MongoConnector(source_uri, source_db, source_coll)
                destination = MongoConnector(dest_uri, dest_db, dest_coll)

                # Connect to databases
                source.connect()
                destination.connect()

                # Check if the collection exists and has documents
                logger.info(f"Checking for documents in {source_db}.{source_coll}...")

                total_docs = 0
                # Initialize direct_cursor here; it will be populated by either pymongo or the connector
                db_cursor = None  # Renamed from direct_cursor to avoid confusion if direct_client is closed early
                # Determine the query to use, defaulting to an empty query
                mongo_query = query if "query" in locals() and query is not None else {}

                try:
                    # Attempt to use a direct PyMongo connection for efficiency
                    logger.info(f"Attempting direct PyMongo connection for {source_db}.{source_coll}")
                    direct_client = pymongo.MongoClient(source_uri)  # direct_client is opened here
                    direct_db = direct_client[source_db]
                    direct_coll = direct_db[source_coll]

                    # Use efficient counting method based on query
                    if mongo_query == {}:
                        # For empty query (all documents), use fast estimated count
                        total_docs = direct_coll.estimated_document_count()
                        logger.info(
                            f"Direct PyMongo estimated count for {source_db}.{source_coll}: {total_docs} documents (all documents)"
                        )
                    else:
                        # For filtered queries, we need the slower count_documents
                        total_docs = direct_coll.count_documents(mongo_query)
                        logger.info(
                            f"Direct PyMongo count for {source_db}.{source_coll}: {total_docs} documents using query: {mongo_query}"
                        )

                    if total_docs > 0:
                        db_cursor = direct_coll.find(mongo_query)
                        logger.info(f"Established Direct PyMongo cursor for {total_docs} documents.")
                        # Optional: Log a sample document ID to confirm cursor validity
                        # sample_doc_from_cursor = direct_coll.find_one(mongo_query)
                        # if sample_doc_from_cursor:
                        #     logger.debug(f"Sample document ID from direct cursor: {sample_doc_from_cursor.get('_id')}")
                    else:
                        logger.info(
                            f"No documents found for {source_db}.{source_coll} via direct PyMongo connection with query: {mongo_query}. Nothing to process."
                        )
                        # If no docs, direct_client can be closed here as db_cursor is None
                        if direct_client:
                            direct_client.close()
                            direct_client = None  # Mark as closed

                except Exception as e:
                    logger.error(
                        f"Error with direct PyMongo connection: {str(e)}. Attempting fallback to MongoConnector."
                    )
                    if direct_client:  # Ensure client is closed if an error occurred after opening
                        direct_client.close()
                        direct_client = None  # Mark as closed

                    # Fallback to MongoConnector
                    if source and hasattr(source, "is_connected") and source.is_connected():
                        logger.info(f"Using MongoConnector for {source_db}.{source_coll}")
                        try:
                            # Attempt to count documents using the connector
                            if hasattr(source, "count_documents"):
                                # Use efficient counting if possible
                                if mongo_query == {} and hasattr(source, "estimated_document_count"):
                                    total_docs = source.estimated_document_count()
                                    logger.info(
                                        f"MongoConnector estimated count: {total_docs} documents (all documents)"
                                    )
                                else:
                                    total_docs = source.count_documents(mongo_query)
                                    logger.info(
                                        f"MongoConnector count: {total_docs} documents using query: {mongo_query}"
                                    )
                            else:
                                # If no count_documents, we can't get total_docs efficiently beforehand
                                # We'll have to rely on iterating the cursor; set total_docs to -1 to indicate unknown
                                logger.warning(
                                    "MongoConnector does not have 'count_documents' method. Total count unknown before iteration."
                                )
                                total_docs = -1  # Indicates count is unknown, loop will proceed differently or estimate

                            if total_docs == 0:
                                logger.info(
                                    f"No documents found via MongoConnector for query: {mongo_query}. Nothing to process."
                                )
                                db_cursor = None
                            else:  # total_docs > 0 or total_docs == -1 (unknown but try to get cursor)
                                db_cursor = source.find_documents(
                                    query=mongo_query, limit=0
                                )  # limit=0 for all matching
                                if db_cursor:
                                    logger.info(
                                        f"Established MongoConnector cursor. Total docs (if known): {total_docs}"
                                    )
                                else:
                                    logger.error("Failed to establish cursor via MongoConnector.")
                        except Exception as conn_e:
                            logger.error(f"Error using MongoConnector for count/cursor: {str(conn_e)}")
                            db_cursor = None  # Ensure cursor is None on error
                            total_docs = 0  # Assume no documents if connector fails badly
                    else:
                        logger.error(
                            "MongoConnector not available or not connected for fallback. Cannot fetch documents."
                        )
                        db_cursor = None
                        total_docs = 0

                # Log total document count
                logger.info(f"Collection {collection_name}: Found {total_docs} documents to process")

                if total_docs == 0:
                    logger.warning(f"No documents found in {source_db}.{source_coll}")
                    continue  # Skip to next collection if no documents found

                # Initialize checkpoint file for this specific collection
                checkpoint_dir = "checkpoints/masking"
                os.makedirs(checkpoint_dir, exist_ok=True)
                checkpoint_file = os.path.join(checkpoint_dir, f"{source_db}_{source_coll}_checkpoint.json")

                # Reset checkpoint if requested
                if args.reset_checkpoint and os.path.exists(checkpoint_file):
                    logger.info(f"Resetting checkpoint file: {checkpoint_file}")
                    os.remove(checkpoint_file)

                # Load checkpoint if it exists
                last_id = None
                if os.path.exists(checkpoint_file) and not args.reset_checkpoint:
                    try:
                        with open(checkpoint_file) as f:
                            checkpoint_data = json.load(f)
                            last_id_str = checkpoint_data.get("last_id")
                            if last_id_str:
                                try:
                                    last_id = ObjectId(last_id_str)
                                    logger.info(f"Resuming from checkpoint with last_id: {last_id}")
                                except:
                                    logger.warning(f"Could not convert checkpoint ID to ObjectId: {last_id_str}")
                                    last_id = last_id_str
                    except Exception as e:
                        logger.warning(f"Error loading checkpoint: {e}")

                # Load masking rules directly from rules.json
                logger.info(f"Loading masking rules from {rules_path}")
                with open(rules_path) as f:
                    rules_data = json.load(f)

                # Extract rules from the JSON
                rules = rules_data.get("rules", [])

                if not rules:
                    logger.error(f"No rules found in {rules_path}")
                    return 1

                logger.info(f"Loaded {len(rules)} masking rules")

                # Create lookup dictionary for rules by field name
                field_rules = {}
                for rule in rules:
                    field_rules[rule["field"]] = rule

                # Helper function to apply a specific masking rule
                def apply_rule(value, rule):
                    """Apply a masking rule to a value."""
                    if value is None or (isinstance(value, str) and not value.strip()):
                        return value

                    rule_type = rule["rule"]
                    params = rule["params"]

                    # Apply the appropriate rule
                    if rule_type == "random_uppercase":
                        if isinstance(value, str):
                            return "".join(random.choice(string.ascii_uppercase) for _ in range(len(value)))
                        return value

                    elif rule_type == "random_uppercase_name":
                        if isinstance(value, str):
                            # Split by spaces to get name parts
                            name_parts = value.split()
                            random_parts = []
                            for part in name_parts:
                                if part:
                                    random_part = "".join(
                                        random.choice(string.ascii_uppercase) for _ in range(len(part))
                                    )
                                    random_parts.append(random_part)
                                else:
                                    random_parts.append("")
                            return " ".join(random_parts)
                        return value

                    elif rule_type == "replace_string":
                        return params

                    elif rule_type == "replace_email":
                        return params

                    elif rule_type == "replace_gender":
                        # Always return the gender value from the rule, regardless of original value
                        return params  # Will be "Female" as specified in rules.json

                    elif rule_type == "replace_path":
                        return params

                    elif rule_type == "random_10_digit_number":
                        return "".join(random.choice("0123456789") for _ in range(10))

                    elif rule_type == "add_milliseconds":
                        if isinstance(value, str):
                            try:
                                # Handle ISO format date strings
                                original_format = None
                                if "T" in value:
                                    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                                    original_format = "iso"
                                else:
                                    # Try different date formats and remember which one worked
                                    try:
                                        dt = datetime.strptime(value, "%Y-%m-%d")
                                        original_format = "%Y-%m-%d"
                                    except ValueError:
                                        try:
                                            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                                            original_format = "%Y-%m-%d %H:%M:%S"
                                        except ValueError:
                                            # Try one more format that might be used
                                            dt = datetime.strptime(value, "%m/%d/%Y")
                                            original_format = "%m/%d/%Y"

                                # Calculate years to shift (preserves month and day)
                                # Milliseconds per year (approximate): 31,536,000,000
                                years = round(int(params) / (1000 * 60 * 60 * 24 * 365))

                                # Shift by exactly N years (preserve month and day)
                                try:
                                    new_dt = dt.replace(year=dt.year + years)
                                except ValueError:
                                    # Handle leap year edge case (Feb 29 -> Feb 28)
                                    new_dt = dt.replace(year=dt.year + years, day=28)

                                # Return in the same format as the original string
                                if original_format == "iso":
                                    result = new_dt.isoformat()
                                else:
                                    result = new_dt.strftime(original_format)

                                logger.debug(
                                    f"Masked Dob from {value} to {result} by shifting {years} years (preserved month/day)"
                                )
                                return result
                            except Exception as e:
                                logger.debug(f"Date parsing error: {e}, value: {value}")
                                return value
                        elif isinstance(value, datetime):
                            # Handle datetime objects directly
                            try:
                                # Calculate years to shift
                                years = int(params) // (1000 * 60 * 60 * 24 * 365)

                                # Shift by exactly N years (preserve month and day)
                                try:
                                    new_dt = value.replace(year=value.year + years)
                                except ValueError:
                                    # Handle leap year edge case (Feb 29 -> Feb 28)
                                    new_dt = value.replace(year=value.year + years, day=28)

                                # Return datetime object to preserve original type
                                logger.debug(f"Masked Dob from {value} to {new_dt} by shifting {years} years")
                                return new_dt
                            except Exception as e:
                                logger.debug(f"Date processing error: {e}")
                                return value
                        return value

                    return value

                # Main function to mask a document
                def mask_document(doc):
                    """Mask a document according to rules."""
                    if not doc:
                        return doc

                    # Create a deep copy for masking
                    masked_doc = copy.deepcopy(doc)

                    # Phase 1: First process direct name fields (FirstName, MiddleName, LastName)
                    # and store their masked values
                    name_masks = {}
                    for field in ["FirstName", "MiddleName", "LastName"]:
                        if field in masked_doc and field in field_rules:
                            rule = field_rules[field]
                            if rule["rule"] == "random_uppercase":
                                masked_value = apply_rule(masked_doc[field], rule)
                                masked_doc[field] = masked_value
                                name_masks[field] = masked_value
                                logger.debug(f"Masked {field}: {masked_doc[field]}")

                    # Phase 2: Process lowercase matches using the masked names
                    for field in ["FirstNameLower", "MiddleNameLower", "LastNameLower"]:
                        if field in masked_doc and field in field_rules:
                            rule = field_rules[field]
                            if rule["rule"] == "lowercase_match":
                                target = rule["params"]

                                # Better handling for null uppercase fields
                                if target in name_masks and name_masks[target] is not None:
                                    # Normal case - uppercase field exists and is not null
                                    masked_doc[field] = name_masks[target].lower()
                                    logger.debug(f"Matched {field} to lowercase of {target}: {masked_doc[field]}")
                                else:
                                    # Uppercase field is missing or null - apply fallback logic

                                    # Option 1: If the original lowercase exists, mask it directly
                                    if masked_doc[field] is not None and masked_doc[field]:
                                        # Apply random masking directly to lowercase field
                                        import random
                                        import string

                                        random_chars = "".join(
                                            random.choice(string.ascii_lowercase) for _ in range(len(masked_doc[field]))
                                        )
                                        masked_doc[field] = random_chars
                                        logger.debug(f"Applied direct masking to {field}: {masked_doc[field]}")

                                    # Option 2: Leave lowercase as is if no better option
                                    # This is already covered by not changing the field

                    # Phase 3: Recursively find and mask all other fields by field name or full path
                    def find_and_mask_fields(obj, path=""):
                        """Recursively find and mask fields in a document."""
                        if isinstance(obj, dict):
                            # Process each field in this dictionary
                            for key, value in list(obj.items()):
                                # Build the current full path for this field
                                current_path = f"{path}.{key}" if path else key

                                # Special handling for Gender field - always ensure it's processed
                                if key == "Gender" and "Gender" in field_rules:
                                    rule = field_rules["Gender"]
                                    obj[key] = apply_rule(value, rule)
                                    logger.debug(f"Masked Gender field: {obj[key]}")

                                # Check if there's a rule for this exact field name
                                elif key in field_rules:
                                    rule = field_rules[key]
                                    # Skip fields already processed in earlier phases
                                    if key not in [
                                        "FirstName",
                                        "MiddleName",
                                        "LastName",
                                        "FirstNameLower",
                                        "MiddleNameLower",
                                        "LastNameLower",
                                    ]:
                                        obj[key] = apply_rule(value, rule)
                                        logger.debug(f"Masked by field name {current_path}: {obj[key]}")

                                # Check if there's a rule for the full field path
                                elif current_path in field_rules:
                                    rule = field_rules[current_path]
                                    obj[key] = apply_rule(value, rule)
                                    logger.debug(f"Masked by full path {current_path}: {obj[key]}")

                                # Recursively process nested structures
                                if isinstance(value, (dict, list)):
                                    find_and_mask_fields(value, current_path)

                        elif isinstance(obj, list):
                            # Process each item in the list
                            for i, item in enumerate(obj):
                                current_path = f"{path}[{i}]"
                                find_and_mask_fields(item, current_path)

                    # Start recursive processing from the root
                    find_and_mask_fields(masked_doc)

                    return masked_doc

                # Initialize processing variables for this collection
                processed_count = 0
                error_count = 0
                start_time = datetime.now()

                # Use batch size from command line if provided, otherwise from environment variable
                batch_size = args.batch_size if args.batch_size else int(os.getenv("PROCESSING_BATCH_SIZE", "100"))

                # Memory management settings
                max_memory_mb = 4000  # Increased from 2000 - you have plenty of system memory
                min_batch_size = 100  # Minimum batch size
                max_batch_size = batch_size  # Store original batch size as maximum

                # Optimized sequential processing with memory management and connection pooling
                from pymongo import WriteConcern

                # Initialize performance metrics
                metrics = {
                    "total_processing_time": 0,
                    "total_docs_processed": 0,
                    "batch_times": [],
                    "batch_sizes": [],
                    "write_times": [],
                    "memory_samples": [],
                }

                # Set up memory tracking if psutil is available
                memory_tracking = MEMORY_TRACKING_AVAILABLE
                if memory_tracking:
                    try:
                        process = psutil.Process()
                        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
                        metrics["memory_samples"].append(initial_memory)
                        logger.info(f"Initial memory usage: {initial_memory:.2f} MB")
                    except Exception as e:
                        logger.warning(f"Error initializing memory tracking: {str(e)}")
                        memory_tracking = False
                else:
                    logger.info("Memory tracking disabled - psutil not available")

                # Configure optimal write concern for better performance
                write_concern = WriteConcern(w=1, j=False)
                if args.in_situ:
                    # Access the actual collection object from the connector
                    collection = source.coll.with_options(write_concern=write_concern)
                else:
                    # Access the actual collection object from the connector
                    collection = destination.coll.with_options(write_concern=write_concern)

                logger.info(
                    f"Processing collection {collection_name} with optimized sequential processing (batch size: {batch_size})"
                )

                current_batch = []
                batch_counter = 0
                retry_attempts = 3  # Number of retry attempts for failed operations

                # Configure cursor for optimal memory usage
                if db_cursor:
                    db_cursor.batch_size(batch_size)  # Optimize MongoDB wire protocol batch size
                    for doc in db_cursor:
                        current_batch.append(doc)

                        # When batch is full, process it
                        if len(current_batch) >= batch_size:
                            # Check memory before processing batch
                            if memory_tracking:
                                pre_batch_memory = process.memory_info().rss / (1024 * 1024)  # MB
                                if pre_batch_memory > max_memory_mb * 1.2:
                                    # Emergency memory situation - force cleanup before processing
                                    logger.warning(f"Emergency memory cleanup triggered at {pre_batch_memory:.2f} MB")
                                    gc.collect()
                                    gc.collect()
                                    time.sleep(0.5)

                            batch_counter += 1
                            batch_size_actual = len(current_batch)
                            progress_log_total = f"/{total_docs}" if total_docs != -1 else ""

                            # Log batch start with memory info if available
                            memory_info = ""
                            if memory_tracking:
                                current_memory = process.memory_info().rss / (1024 * 1024)  # MB
                                memory_info = f" [Memory: {current_memory:.2f} MB]"

                            logger.info(
                                f"Collection {collection_name}: Processing batch {batch_counter} ({batch_size_actual} documents)...{memory_info}"
                            )

                            # Process the batch with retry logic and performance tracking
                            try:
                                batch_start = time.time()
                                masked_docs = []
                                doc_errors = 0

                                # Mask all documents in the batch
                                for single_doc in current_batch:
                                    try:
                                        masked_doc = mask_document(single_doc)
                                        masked_docs.append(masked_doc)
                                    except Exception as e_doc:
                                        logger.error(f"Error masking document {single_doc.get('_id')}: {str(e_doc)}")
                                        doc_errors += 1

                                # Optimized bulk update with retry logic
                                if masked_docs:
                                    write_start = time.time()
                                    for attempt in range(retry_attempts):
                                        try:
                                            bulk_ops = [
                                                pymongo.ReplaceOne(
                                                    {"_id": doc["_id"]},
                                                    doc,
                                                    upsert=not args.in_situ,
                                                )
                                                for doc in masked_docs
                                            ]
                                            if bulk_ops:
                                                collection.bulk_write(bulk_ops, ordered=False)
                                                break
                                        except pymongo.errors.BulkWriteError as bwe:
                                            if attempt == retry_attempts - 1:
                                                logger.error(
                                                    f"Bulk write failed after {retry_attempts} attempts: {str(bwe)}"
                                                )
                                            else:
                                                logger.warning(f"Bulk write attempt {attempt + 1} failed, retrying...")
                                                time.sleep(0.5 * (attempt + 1))
                                        except Exception as e_bulk:
                                            logger.error(f"Error in bulk update: {str(e_bulk)}")
                                            break
                                    write_time = time.time() - write_start
                                    metrics["write_times"].append(write_time)

                                processed_count += batch_size_actual - doc_errors
                                error_count += doc_errors

                                # Update metrics and log completion
                                batch_duration = time.time() - batch_start
                                metrics["batch_times"].append(batch_duration)
                                metrics["total_processing_time"] += batch_duration
                                docs_per_second = batch_size_actual / batch_duration if batch_duration > 0 else 0

                                logger.info(
                                    f"Collection {collection_name}: Processed {processed_count}{progress_log_total} documents. Batch {batch_counter} took {batch_duration:.2f}s ({docs_per_second:.2f} docs/sec)."
                                )

                            except Exception as e_batch:
                                logger.error(f"Error processing batch {batch_counter}: {str(e_batch)}")
                                error_count += len(current_batch)

                            # Clear the batch for the next iteration
                            current_batch = []
                            masked_docs = []  # Explicitly clear masked documents

                            # Force garbage collection and memory cleanup
                            gc.collect()
                            gc.collect()  # Run twice for better cleanup

                            # Log memory after cleanup if tracking is available
                            if memory_tracking:
                                post_cleanup_memory = process.memory_info().rss / (1024 * 1024)  # MB
                                logger.info(f"Memory after cleanup: {post_cleanup_memory:.2f} MB")

                                # Automatic batch size adjustment based on memory usage
                                if post_cleanup_memory > max_memory_mb:
                                    # Memory too high - reduce batch size
                                    new_batch_size = max(min_batch_size, int(batch_size * 0.7))
                                    if new_batch_size != batch_size:
                                        logger.warning(
                                            f"High memory usage ({post_cleanup_memory:.2f} MB) - reducing batch size from {batch_size} to {new_batch_size}"
                                        )
                                        batch_size = new_batch_size
                                elif post_cleanup_memory < max_memory_mb * 0.5 and batch_size < max_batch_size:
                                    # Memory usage low - can increase batch size
                                    new_batch_size = min(max_batch_size, int(batch_size * 1.2))
                                    if new_batch_size != batch_size:
                                        logger.info(
                                            f"Low memory usage ({post_cleanup_memory:.2f} MB) - increasing batch size from {batch_size} to {new_batch_size}"
                                        )
                                        batch_size = new_batch_size

                            time.sleep(0.2)  # Slightly longer pause for memory cleanup

                    # After the loop, process any remaining documents in the final batch
                    if current_batch:
                        batch_counter += 1
                        batch_size_actual = len(current_batch)
                        logger.info(
                            f"Collection {collection_name}: Processing final batch {batch_counter} ({batch_size_actual} documents)..."
                        )

                        try:
                            batch_start = time.time()
                            masked_docs = []
                            doc_errors = 0

                            for single_doc in current_batch:
                                try:
                                    masked_doc = mask_document(single_doc)
                                    masked_docs.append(masked_doc)
                                except Exception as e_doc:
                                    logger.error(f"Error masking document {single_doc.get('_id')}: {str(e_doc)}")
                                    doc_errors += 1

                            if masked_docs:
                                for attempt in range(retry_attempts):
                                    try:
                                        bulk_ops = [
                                            pymongo.ReplaceOne(
                                                {"_id": doc["_id"]},
                                                doc,
                                                upsert=not args.in_situ,
                                            )
                                            for doc in masked_docs
                                        ]
                                        if bulk_ops:
                                            collection.bulk_write(bulk_ops, ordered=False)
                                            break
                                    except Exception as e_bulk:
                                        if attempt == retry_attempts - 1:
                                            logger.error(f"Final batch bulk write failed: {str(e_bulk)}")
                                        else:
                                            logger.warning(
                                                f"Final batch bulk write attempt {attempt + 1} failed, retrying..."
                                            )
                                            time.sleep(0.5 * (attempt + 1))

                            processed_count += batch_size_actual - doc_errors
                            error_count += doc_errors
                            batch_duration = time.time() - batch_start
                            logger.info(
                                f"Collection {collection_name}: Processed {processed_count}/{total_docs} documents. Final batch {batch_counter} took {batch_duration:.2f}s."
                            )

                        except Exception as e_final:
                            logger.error(f"Error processing final batch: {str(e_final)}")
                            error_count += len(current_batch)

                    else:
                        logger.warning(
                            f"No documents or cursor available for sequential processing in {collection_name}."
                        )

                    if direct_client:  # If direct_client was used for db_cursor
                        logger.info("Closing direct_client after sequential processing loop.")
                        direct_client.close()
                        direct_client = None

                # Final summary for this collection
                end_time = datetime.now()
                total_elapsed = (end_time - start_time).total_seconds()
                success_rate = (processed_count / total_docs * 100) if total_docs > 0 else 0
                avg_throughput = processed_count / total_elapsed if total_elapsed > 0 else 0

                # Calculate memory stats
                if memory_tracking and len(metrics["memory_samples"]) > 0:
                    initial_mem = metrics["memory_samples"][0]
                    peak_mem = max(metrics["memory_samples"])
                    mem_growth = peak_mem - initial_mem
                else:
                    initial_mem = peak_mem = mem_growth = 0

                # Build comprehensive summary
                logger.info("")
                logger.info("=" * 70)
                logger.info(f"MASKING SUMMARY - {collection_name} Collection")
                logger.info("=" * 70)
                logger.info(f"Total Documents:        {total_docs}")
                logger.info(f"Successfully Masked:    {processed_count}")
                logger.info(f"Errors:                 {error_count}")
                logger.info(f"Success Rate:          {success_rate:.2f}%")
                logger.info("")
                logger.info("Performance Metrics:")
                logger.info(f"  Total Time:          {total_elapsed:.2f}s")
                logger.info(f"  Processing Rate:     {avg_throughput:.2f} docs/sec")
                logger.info(f"  Batch Size:          {max_batch_size}")
                logger.info(f"  Batches Processed:   {batch_counter}")
                logger.info("")
                if memory_tracking and initial_mem > 0:
                    logger.info("Memory Usage:")
                    logger.info(f"  Initial:             {initial_mem:.2f} MB")
                    logger.info(f"  Peak:                {peak_mem:.2f} MB")
                    logger.info(f"  Growth:              +{mem_growth:.2f} MB")
                    logger.info("")
                logger.info("Database:")
                logger.info(f"  Environment:         {args.src_env} → {args.dst_env}")
                logger.info(f"  Namespace:           {source_db}.{source_coll}")
                logger.info(f"  Mode:                {'In-situ' if args.in_situ else 'Copy'}")
                logger.info("")
                logger.info(f"Rules Applied:         {len(rules)} masking rules")
                logger.info("=" * 70)
                logger.info("")

            finally:
                # Ensure connections are closed for this collection
                if direct_client:  # Final safeguard for direct_client
                    logger.info("Ensuring direct_client is closed in main collection finally block.")
                    direct_client.close()
                    direct_client = None
                if source:
                    source.disconnect()
                if destination:
                    destination.disconnect()

        return 0

    except Exception as e:
        logger.error(f"System error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Wrap main execution in a try-except to catch specific errors and set exit codes
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Unhandled error: {str(e)}")
        import traceback

        traceback.print_exc()
        # Log the exception with full details
        logging.getLogger(__name__).exception(f"Unhandled Exception: {e}")
        sys.exit(1)  # Connection error
