#!/usr/bin/env python3
"""
Generate No-PHI Collections Report with Metrics

This script generates a CSV report with actual production collection metrics
for collections that don't contain PHI data.
"""

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any

import pymongo
from dotenv import load_dotenv

# Add project directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.insert(0, project_dir)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# File paths
NO_PHI_COLLECTIONS_FILE = os.path.join(project_dir, "docs/nophi_collections/no-phi_collections.json")
CONFIG_FILE = os.path.join(project_dir, "config/config_rules/config.json")
OUTPUT_CSV_FILE = os.path.join(
    project_dir, f"docs/nophi_collections/no_phi_collections_report_{datetime.now().strftime('%Y%m%d')}.csv"
)
ENV_FILE = os.path.join(project_dir, ".env.prod")


def load_environment():
    """Load environment variables from .env.prod file."""
    if os.path.exists(ENV_FILE):
        load_dotenv(ENV_FILE)
        logger.info(f"Loaded environment variables from {ENV_FILE}")
    else:
        logger.warning(f"Environment file {ENV_FILE} not found, using existing environment variables")


def build_mongo_uri(prefix, logger=None, db_name=None, coll_name=None):
    """Build a MongoDB URI from environment variables with proper SRV handling."""
    username = os.getenv(f"{prefix}_USERNAME", "")
    password = os.getenv(f"{prefix}_PASSWORD", "")
    host = os.getenv(f"{prefix}_HOST", "localhost")
    port = os.getenv(f"{prefix}_PORT", "27017")
    auth_db = os.getenv(f"{prefix}_AUTH_DB", "admin")
    use_ssl = os.getenv(f"{prefix}_USE_SSL", "false").lower() == "true"
    use_srv = os.getenv(f"{prefix}_USE_SRV", "false").lower() == "true"

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

    # Log components if logger provided
    if logger:
        namespace_info = ""
        if db_name and coll_name:
            namespace_info = f", Namespace={db_name}.{coll_name}"

        logger.info(
            f"URI components for {prefix}: Protocol={protocol}, Host={host_part}, Auth DB={auth_db}, SSL={use_ssl}, SRV={use_srv}{namespace_info}"
        )

    return uri


def load_collections_from_file(file_path: str) -> list[str]:
    """Load the list of no-PHI collections from JSON file."""
    try:
        with open(file_path) as f:
            collections = json.load(f)
            logger.info(f"Loaded {len(collections)} collections from {file_path}")
            return collections
    except Exception as e:
        logger.error(f"Failed to load collections from {file_path}: {e}")
        return []


def load_config() -> dict[str, Any]:
    """Load the configuration file."""
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
            logger.info("Configuration loaded successfully")
            return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)


def get_mongodb_connection() -> pymongo.MongoClient:
    """Create a MongoDB connection using environment variables."""
    try:
        # Build MongoDB URI using the project's standard approach
        uri = build_mongo_uri("MONGO_SOURCE", logger)

        # Connect to MongoDB
        client = pymongo.MongoClient(uri)
        # Test connection
        client.admin.command("ping")
        logger.info("Connected to MongoDB successfully")

        # List available databases
        databases = client.list_database_names()
        logger.info(f"Available databases: {', '.join(databases)}")

        return client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)


def get_collection_stats(client: pymongo.MongoClient, collection_name: str, database_name: str) -> dict[str, Any]:
    """Get collection statistics from MongoDB."""
    try:
        # Check if database exists
        if database_name not in client.list_database_names():
            logger.error(f"Database {database_name} does not exist")
            return {}

        # Print available collections for debugging
        available_collections = client[database_name].list_collection_names()
        if not available_collections:
            logger.warning(f"No collections found in database {database_name}")
            return {}

        # Only log this once per database
        if collection_name == client[database_name].list_collection_names()[0]:
            logger.info(f"Found {len(available_collections)} collections in database {database_name}")

        # Check if collection exists before getting stats
        if collection_name not in available_collections:
            logger.warning(f"Collection {collection_name} does not exist in database {database_name}")
            return {}

        result = client[database_name].command("collStats", collection_name)
        return result
    except Exception as e:
        logger.error(f"Failed to get stats for collection {collection_name}: {e}")
        return {}


def get_collection_metrics(collection_name: str, client: pymongo.MongoClient, database_name: str) -> dict[str, Any]:
    """
    Get metrics for a MongoDB collection.

    Args:
        collection_name: Name of the collection
        client: MongoDB client instance
        database_name: Name of the database

    Returns:
        Dict with collection metrics
    """
    try:
        # Get collection stats
        stats = get_collection_stats(client, collection_name, database_name)

        if not stats:
            raise Exception("Failed to retrieve collection stats")

        # Calculate size in MB (as integers, no decimals)
        size_mb = int(stats.get("size", 0) / (1024 * 1024))
        storage_size_mb = int(stats.get("storageSize", 0) / (1024 * 1024))

        # Extract key metrics
        metrics = {
            "collection_name": collection_name,
            "document_count": stats.get("count", 0),
            "size_mb": size_mb,
            "storage_size_mb": storage_size_mb,
            "avg_doc_size_bytes": stats.get("avgObjSize", 0),
            "index_count": len(stats.get("indexSizes", {})),
            "index_size_mb": int(stats.get("totalIndexSize", 0) / (1024 * 1024)),
        }

        logger.info(f"Collected metrics for {collection_name}: {metrics['document_count']} docs, {size_mb} MB")
        return metrics

    except Exception as e:
        logger.error(f"Failed to get metrics for {collection_name}: {e}")
        # Return empty metrics with collection name
        return {
            "collection_name": collection_name,
            "document_count": 0,
            "size_mb": 0,
            "storage_size_mb": 0,
            "avg_doc_size_bytes": 0,
            "index_count": 0,
            "index_size_mb": 0,
            "error": str(e),
        }


def write_csv_report(collection_metrics: list[dict[str, Any]], output_file: str) -> None:
    """
    Write a CSV report with collection metrics.

    Args:
        collection_metrics: List of dictionaries with collection metrics
        output_file: Path to output CSV file
    """
    try:
        # Define CSV headers with Total Size column
        headers = [
            "Collection Name",
            "Document Count",
            "Size (MB)",
            "Storage Size (MB)",
            "Avg Doc Size (bytes)",
            "Index Count",
            "Index Size (MB)",
            "Total Size (MB)",
        ]

        # Sort collections by size (largest first)
        sorted_metrics = sorted(collection_metrics, key=lambda x: x["size_mb"], reverse=True)

        # Write to CSV
        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(headers)

            # Write data rows
            for metrics in sorted_metrics:
                # Calculate total size (size + index size) as a whole number
                total_size_mb = int(metrics["size_mb"] + metrics["index_size_mb"])

                writer.writerow(
                    [
                        metrics["collection_name"],
                        metrics["document_count"],
                        metrics["size_mb"],
                        metrics["storage_size_mb"],
                        metrics["avg_doc_size_bytes"],
                        metrics["index_count"],
                        metrics["index_size_mb"],
                        total_size_mb,
                    ]
                )

        logger.info(f"CSV report written to {output_file}")

    except Exception as e:
        logger.error(f"Failed to write CSV report: {e}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate No-PHI Collections Report")
    parser.add_argument("--collections", default=NO_PHI_COLLECTIONS_FILE, help="Path to no-phi collections JSON file")
    parser.add_argument("--output", default=OUTPUT_CSV_FILE, help="Path to output CSV file")
    parser.add_argument("--env", default=ENV_FILE, help="Path to environment file")
    parser.add_argument("--database", help="MongoDB database name to use (overrides MONGO_SOURCE_DB)")
    return parser.parse_args()


def main():
    """Main entry point for the script."""
    # Parse command line arguments
    args = parse_args()

    # Load environment variables
    load_environment()

    # Load collections
    collections = load_collections_from_file(args.collections)
    if not collections:
        logger.error("No collections found. Exiting.")
        return 1

    # Initialize MongoDB connection
    try:
        client = get_mongodb_connection()
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB connection: {e}")
        return 1

    # Determine which database to use
    database_name = args.database or os.getenv("MONGO_SOURCE_DB")
    if not database_name:
        logger.error(
            "Database name not specified. Please provide it with --database or set MONGO_SOURCE_DB environment variable."
        )
        return 1

    logger.info(f"Using database: {database_name}")

    # Get metrics for each collection
    collection_metrics = []
    for i, collection_name in enumerate(collections):
        logger.info(f"Processing collection {i+1}/{len(collections)}: {collection_name}")
        metrics = get_collection_metrics(collection_name, client, database_name)
        collection_metrics.append(metrics)

    # Write CSV report
    write_csv_report(collection_metrics, args.output)

    logger.info(f"Processed {len(collections)} collections")
    return 0


if __name__ == "__main__":
    sys.exit(main())
