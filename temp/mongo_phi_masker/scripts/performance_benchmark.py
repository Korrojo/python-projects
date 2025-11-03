#!/usr/bin/env python3
"""
scripts/performance_benchmark.py

Performance Testing Script for MongoDB PHI Masker

This script benchmarks performance using real data from an existing MongoDB collection
to find optimal configurations for masking large document sets.
"""

import argparse
import json
import logging
import os
import time
import sys
from typing import Dict, Any, List, Optional, Tuple, Callable
import matplotlib.pyplot as plt
import numpy as np

# Add project root to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# Now import project modules
from src.core.orchestrator import MaskingOrchestrator
from src.core.connector import MongoConnector
from src.core.dask_processor import DaskProcessor
from src.utils.config_loader import ConfigLoader, generate_mongodb_uri
from src.utils.logger import setup_logging
from src.utils.performance_monitor import PerformanceMonitor

# Setup logger
logger = logging.getLogger(__name__)


def validate_mongodb_connection(
    uri: str, database: str, collection: str, query: Optional[Dict[str, Any]] = None
) -> Tuple[bool, int]:
    """Validate MongoDB connection and return document count.

    Args:
        uri: MongoDB connection URI
        database: Database name
        collection: Collection name
        query: Optional query filter

    Returns:
        Tuple of (success, document count)
    """
    logger.info(f"Validating connection to {database}.{collection}")

    connector = MongoConnector(uri=uri, database=database, collection=collection)

    try:
        connector.connect()

        # Count total documents matching query
        doc_count = connector.count_documents(query)
        logger.info(f"Found {doc_count} total documents in collection")

        # Fetch one document to verify access
        sample_doc = connector.find_one(query=query)

        if not sample_doc:
            logger.error("No documents found in collection")
            return False, 0

        logger.info(f"Successfully connected to MongoDB and validated data access")
        logger.info(f"Sample document _id: {sample_doc.get('_id', 'unknown')}")

        return True, doc_count
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        return False, 0
    finally:
        connector.disconnect()


def process_documents_in_batches(
    uri: str,
    database: str,
    collection: str,
    processor_func: Callable,
    batch_size: int,
    limit: int = 0,
    query: Optional[Dict[str, Any]] = None,
    skip: int = 0,
) -> Dict[str, Any]:
    """Process documents in batches without loading everything into memory.

    Args:
        uri: MongoDB connection URI
        database: Database name
        collection: Collection name
        processor_func: Function to process each batch
        batch_size: Size of batches to process
        limit: Maximum number of documents to process (0 for all)
        query: Optional query filter
        skip: Number of documents to skip

    Returns:
        Processing statistics
    """
    connector = MongoConnector(uri=uri, database=database, collection=collection)

    stats = {
        "processed_count": 0,
        "error_count": 0,
        "batches_processed": 0,
        "batch_times": [],
        "start_time": time.time(),
    }

    try:
        connector.connect()

        # Process in batches
        remaining = limit
        current_skip = skip

        while True:
            # Calculate current batch size
            current_batch_size = batch_size
            if limit > 0:
                if remaining <= 0:
                    break
                current_batch_size = min(batch_size, remaining)

            # Fetch batch
            batch_start = time.time()
            cursor = connector.find_documents(
                query=query, limit=current_batch_size, skip=current_skip
            )

            # Convert to list for processing (only this batch is in memory)
            batch = list(cursor)

            # If no documents returned, we're done
            if not batch:
                break

            # Process batch
            try:
                batch_result = processor_func(batch)
                stats["processed_count"] += len(batch)
                stats["batches_processed"] += 1

                # Update batch timing stats
                batch_time = time.time() - batch_start
                stats["batch_times"].append(batch_time)

                # Log progress
                if stats["batches_processed"] % 5 == 0:
                    logger.info(
                        f"Processed {stats['processed_count']} documents in {stats['batches_processed']} batches"
                    )

            except Exception as e:
                logger.error(f"Error processing batch: {str(e)}")
                stats["error_count"] += 1

            # Update counters for next iteration
            if limit > 0:
                remaining -= len(batch)
            current_skip += len(batch)

        stats["total_time"] = time.time() - stats["start_time"]
        stats["avg_batch_time"] = (
            sum(stats["batch_times"]) / len(stats["batch_times"])
            if stats["batch_times"]
            else 0
        )
        stats["throughput"] = (
            stats["processed_count"] / stats["total_time"]
            if stats["total_time"] > 0
            else 0
        )

        return stats

    finally:
        connector.disconnect()


def run_performance_test(
    config: Dict[str, Any],
    source_uri: str,
    source_db: str,
    source_collection: str,
    total_docs: int,
    batch_sizes: List[int] = [100, 500, 1000, 5000],
    worker_counts: List[int] = [1, 2, 4, 8],
    connection_pool_sizes: List[int] = [50, 100, 200],
    use_dask: bool = False,
    test_duration_per_config: int = 60,  # seconds
    query: Optional[Dict[str, Any]] = None,
    output_path: str = None,
) -> Dict[str, Any]:
    """Run performance tests with various configurations.

    Args:
        config: Application configuration
        source_uri: MongoDB source URI
        source_db: Source database name
        source_collection: Source collection name
        total_docs: Total documents in collection
        batch_sizes: Batch sizes to test
        worker_counts: Worker counts to test
        connection_pool_sizes: MongoDB connection pool sizes to test
        use_dask: Whether to use Dask for processing
        test_duration_per_config: Time to test each configuration in seconds
        query: Optional query filter
        output_path: Optional path to save results

    Returns:
        Performance test results
    """
    results = {
        "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "document_count": total_docs,
        "configurations": [],
    }

    perf_monitor = PerformanceMonitor(logger=logger)

    # Create document masker from config
    from src.core.masker import DocumentMasker
    from src.models.masking_rule import RulesetLoader

    # Load rules
    ruleset_loader = RulesetLoader()
    rules_path = config.get("masking", {}).get("rules_path", "config/masking_rules/rules.json")
    rules = ruleset_loader.load_from_file(rules_path)
    masker = DocumentMasker(rules)

    # Define batch processor function
    def process_batch(batch):
        """Process a batch of documents."""
        return [masker.mask_document(doc) for doc in batch]

    # Test each configuration
    for batch_size in batch_sizes:
        for worker_count in worker_counts:
            for pool_size in connection_pool_sizes:
                # Skip invalid combinations
                if worker_count > batch_size / 10:
                    continue

                logger.info(
                    f"Testing configuration: batch_size={batch_size}, workers={worker_count}, pool_size={pool_size}, dask={use_dask}"
                )

                # Update config with test parameters
                test_config = config.copy()
                test_config["processing"]["batch_size"]["initial"] = batch_size
                test_config["processing"]["worker_count"] = worker_count

                # Update MongoDB connection pool settings
                if "mongodb" in test_config:
                    for db_config in ["source", "destination"]:
                        if db_config in test_config["mongodb"]:
                            test_config["mongodb"][db_config][
                                "max_pool_size"
                            ] = pool_size

                # Start monitoring
                perf_monitor.start_monitoring()

                try:
                    # Calculate documents to process in test duration
                    # Use a smaller sample for testing each configuration
                    test_docs = min(
                        total_docs, batch_size * 20
                    )  # Process at least 20 batches

                    # Process documents
                    if use_dask:
                        # Use Dask for processing (would need implementation)
                        # This is a placeholder
                        processor = DaskProcessor(
                            test_config, logger=logger, n_workers=worker_count
                        )
                        processor.start_client()
                        # Dask implementation here
                        stats = {"processed_count": 0, "total_time": 0, "throughput": 0}
                        processor.stop_client()
                    else:
                        # Use standard batch processing
                        stats = process_documents_in_batches(
                            uri=source_uri,
                            database=source_db,
                            collection=source_collection,
                            processor_func=process_batch,
                            batch_size=batch_size,
                            limit=test_docs,
                            query=query,
                        )

                except Exception as e:
                    logger.error(f"Error during test: {str(e)}")
                    perf_monitor.stop_monitoring()
                    continue

                # Stop monitoring
                perf_monitor.stop_monitoring()
                system_metrics = perf_monitor.metrics

                # Record results
                config_result = {
                    "batch_size": batch_size,
                    "worker_count": worker_count,
                    "connection_pool_size": pool_size,
                    "use_dask": use_dask,
                    "processed_count": stats["processed_count"],
                    "elapsed_time_seconds": stats["total_time"],
                    "throughput_docs_per_second": stats["throughput"],
                    "cpu_percent": system_metrics.get("cpu_percent", 0),
                    "memory_percent": system_metrics.get("memory_percent", 0),
                }

                results["configurations"].append(config_result)
                logger.info(
                    f"Results: {stats['throughput']:.2f} docs/sec, {stats['total_time']:.2f} seconds"
                )

    # Save results if output path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

    return results


def visualize_results(results: Dict[str, Any], output_dir: str = "results/performance"):
    """Generate visualizations of performance test results.

    Args:
        results: Performance test results
        output_dir: Directory to save visualizations
    """
    os.makedirs(output_dir, exist_ok=True)

    # Extract data
    configs = results["configurations"]

    # Check if we have meaningful results to visualize
    if not configs:
        logger.warning("No performance results to visualize")
        return

    batch_sizes = sorted(list(set(c["batch_size"] for c in configs)))
    worker_counts = sorted(list(set(c["worker_count"] for c in configs)))
    pool_sizes = sorted(list(set(c["connection_pool_size"] for c in configs)))

    # Generate throughput vs batch size plot
    plt.figure(figsize=(12, 8))

    for worker in worker_counts:
        # Filter configs for this worker count
        worker_configs = [c for c in configs if c["worker_count"] == worker]

        # Skip if no configs for this worker count
        if not worker_configs:
            continue

        # Group by batch size
        batch_throughputs = {}
        for config in worker_configs:
            batch_size = config["batch_size"]
            if batch_size not in batch_throughputs:
                batch_throughputs[batch_size] = []
            batch_throughputs[batch_size].append(config["throughput_docs_per_second"])

        # Calculate average throughput for each batch size
        x_values = []
        y_values = []
        for batch_size in sorted(batch_throughputs.keys()):
            x_values.append(batch_size)
            y_values.append(
                sum(batch_throughputs[batch_size]) / len(batch_throughputs[batch_size])
            )

        plt.plot(x_values, y_values, marker="o", label=f"{worker} workers")

    plt.xlabel("Batch Size")
    plt.ylabel("Throughput (docs/second)")
    plt.title("Throughput by Batch Size and Worker Count")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, "batch_vs_throughput.png"))

    # Generate throughput vs worker count plot
    plt.figure(figsize=(12, 8))

    for batch in batch_sizes:
        # Filter configs for this batch size
        batch_configs = [c for c in configs if c["batch_size"] == batch]

        # Skip if no configs for this batch size
        if not batch_configs:
            continue

        # Group by worker count
        worker_throughputs = {}
        for config in batch_configs:
            worker_count = config["worker_count"]
            if worker_count not in worker_throughputs:
                worker_throughputs[worker_count] = []
            worker_throughputs[worker_count].append(
                config["throughput_docs_per_second"]
            )

        # Calculate average throughput for each worker count
        x_values = []
        y_values = []
        for worker_count in sorted(worker_throughputs.keys()):
            x_values.append(worker_count)
            y_values.append(
                sum(worker_throughputs[worker_count])
                / len(worker_throughputs[worker_count])
            )

        plt.plot(x_values, y_values, marker="o", label=f"Batch {batch}")

    plt.xlabel("Worker Count")
    plt.ylabel("Throughput (docs/second)")
    plt.title("Throughput by Worker Count and Batch Size")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, "workers_vs_throughput.png"))

    # Generate pool size impact visualization
    if len(pool_sizes) > 1:
        plt.figure(figsize=(12, 8))

        # Group by pool size
        for pool in pool_sizes:
            # Filter configs for this pool size
            pool_configs = [c for c in configs if c["connection_pool_size"] == pool]

            # Group by batch size
            batch_throughputs = {}
            for config in pool_configs:
                batch_size = config["batch_size"]
                if batch_size not in batch_throughputs:
                    batch_throughputs[batch_size] = []
                batch_throughputs[batch_size].append(
                    config["throughput_docs_per_second"]
                )

            # Calculate average throughput for each batch size
            x_values = []
            y_values = []
            for batch_size in sorted(batch_throughputs.keys()):
                x_values.append(batch_size)
                y_values.append(
                    sum(batch_throughputs[batch_size])
                    / len(batch_throughputs[batch_size])
                )

            plt.plot(x_values, y_values, marker="o", label=f"Pool {pool}")

        plt.xlabel("Batch Size")
        plt.ylabel("Throughput (docs/second)")
        plt.title("Impact of Connection Pool Size on Throughput")
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(output_dir, "pool_size_impact.png"))

    # Generate a summary plot with optimal configuration
    optimal_config = max(configs, key=lambda x: x["throughput_docs_per_second"])

    plt.figure(figsize=(10, 6))
    plt.bar(
        ["Smallest Batch", "Largest Batch", "Optimal Batch"],
        [
            min(configs, key=lambda x: x["batch_size"])["throughput_docs_per_second"],
            max(configs, key=lambda x: x["batch_size"])["throughput_docs_per_second"],
            optimal_config["throughput_docs_per_second"],
        ],
    )
    plt.ylabel("Throughput (docs/second)")
    plt.title("Performance Comparison")

    # Add optimal configuration details
    plt.annotate(
        f"Optimal: Batch={optimal_config['batch_size']}, Workers={optimal_config['worker_count']}, Pool={optimal_config['connection_pool_size']}",
        xy=(2, optimal_config["throughput_docs_per_second"]),
        xytext=(1.5, optimal_config["throughput_docs_per_second"] * 1.1),
        arrowprops=dict(facecolor="black", shrink=0.05),
    )

    plt.savefig(os.path.join(output_dir, "optimal_config.png"))


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="MongoDB PHI Masker Performance Testing"
    )
    parser.add_argument(
        "--config", default="config/config_rules/config.json", help="Path to configuration file"
    )
    parser.add_argument("--env", default=".env.test", help="Path to environment file")
    parser.add_argument("--source-uri", help="MongoDB source URI (overrides config)")
    parser.add_argument(
        "--source-db", help="Source database name (defaults to env value)"
    )
    parser.add_argument(
        "--source-collection", help="Source collection name (defaults to env value)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100000,
        help="Maximum number of documents to process (0 for all)",
    )
    parser.add_argument(
        "--batch-sizes",
        default="100,500,1000,5000",
        help="Comma-separated batch sizes to test",
    )
    parser.add_argument(
        "--worker-counts",
        default="1,2,4,8",
        help="Comma-separated worker counts to test",
    )
    parser.add_argument(
        "--pool-sizes",
        default="50,100,200",
        help="Comma-separated MongoDB connection pool sizes to test",
    )
    parser.add_argument("--query", help="Optional MongoDB query filter in JSON format")
    parser.add_argument(
        "--use-dask", action="store_true", help="Use Dask for parallel processing"
    )
    parser.add_argument(
        "--output",
        default="results/performance/benchmark_results.json",
        help="Path to output file for test results",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level",
    )
    parser.add_argument(
        "--log-file", 
        type=str, 
        help="Custom log file path"
    )
    parser.add_argument(
        "--log-max-bytes", 
        type=int, 
        default=10 * 1024 * 1024,
        help="Maximum log file size before rotation (default: 10MB)"
    )
    parser.add_argument(
        "--log-backup-count", 
        type=int, 
        default=5,
        help="Number of backup log files to keep (default: 5)"
    )
    parser.add_argument(
        "--log-timed-rotation", 
        action="store_true",
        help="Use time-based rotation instead of size-based"
    )

    args = parser.parse_args()

    # Setup logging with enhanced options
    setup_logging(
        log_level=args.log_level,
        log_file=args.log_file,
        max_bytes=args.log_max_bytes,
        backup_count=args.log_backup_count,
        use_timed_rotating=args.log_timed_rotation
    )
    logger.info("Starting MongoDB PHI Masker Performance Testing")

    try:
        # Load configuration
        logger.info(f"Loading configuration from {args.config}")
        config_loader = ConfigLoader(args.config, args.env)
        config = config_loader.load_config()

        # Get environment variables directly
        import os
        from dotenv import load_dotenv

        # Load environment variables from the specified file
        if not os.path.exists(args.env):
            logger.error(f"Environment file {args.env} not found")
            return 1

        load_dotenv(args.env, override=True)

        # Get database info from environment or args
        source_db = args.source_db or os.environ.get(
            "MONGO_SOURCE_DB", "UbiquityPreProd"
        )
        source_collection = args.source_collection or os.environ.get(
            "MONGO_SOURCE_COLL", "Patients"
        )

        # Get MongoDB URI from args or build it directly
        source_uri = args.source_uri

        # Build MongoDB URI if not provided
        if not source_uri:
            # Get components directly from environment
            host = os.environ.get("MONGO_SOURCE_HOST")
            username = os.environ.get("MONGO_SOURCE_USERNAME")
            password = os.environ.get("MONGO_SOURCE_PASSWORD")
            use_ssl = os.environ.get("MONGO_SOURCE_USE_SSL", "true").lower() == "true"
            use_srv = os.environ.get("MONGO_SOURCE_USE_SRV", "false").lower() == "true"
            auth_db = os.environ.get("MONGO_SOURCE_AUTH_DB", "admin")

            # Build URI
            protocol = "mongodb+srv://" if use_srv else "mongodb://"
            credentials = f"{username}:{password}@" if username and password else ""
            ssl_str = "?ssl=true" if use_ssl else ""
            auth_str = (
                f"&authSource={auth_db}"
                if auth_db and use_ssl
                else f"?authSource={auth_db}" if auth_db else ""
            )

            source_uri = f"{protocol}{credentials}{host}/{ssl_str}{auth_str}"
            logger.info(
                f"Built source URI: {protocol}***:***@{host}/{ssl_str}{auth_str}"
            )

        if not source_uri:
            logger.error(
                "Source URI not provided and could not be built from environment variables"
            )
            return 1

        # Validate MongoDB connection and get document count
        success, doc_count = validate_mongodb_connection(
            uri=source_uri,
            database=source_db,
            collection=source_collection,
            query=args.query,
        )

        if not success:
            logger.error("Failed to connect to MongoDB")
            return 1

        # Determine document limit for testing
        doc_limit = args.limit if args.limit > 0 else doc_count
        if doc_limit > doc_count:
            logger.warning(
                f"Requested limit {doc_limit} exceeds available documents {doc_count}"
            )
            doc_limit = doc_count

        logger.info(
            f"Will test with up to {doc_limit} documents (total available: {doc_count})"
        )

        # Parse batch sizes and worker counts
        batch_sizes = [int(x.strip()) for x in args.batch_sizes.split(",")]
        worker_counts = [int(x.strip()) for x in args.worker_counts.split(",")]
        pool_sizes = [int(x.strip()) for x in args.pool_sizes.split(",")]

        # Run performance tests with batched processing
        results = run_performance_test(
            config,
            source_uri=source_uri,
            source_db=source_db,
            source_collection=source_collection,
            total_docs=doc_limit,
            batch_sizes=batch_sizes,
            worker_counts=worker_counts,
            connection_pool_sizes=pool_sizes,
            use_dask=args.use_dask,
            query=args.query,
            output_path=args.output,
        )

        # Visualize results
        visualize_results(results)

        # Print optimal configuration
        if results["configurations"]:
            optimal_config = max(
                results["configurations"], key=lambda x: x["throughput_docs_per_second"]
            )
            logger.info("\n=== OPTIMAL CONFIGURATION ===")
            logger.info(f"Batch Size: {optimal_config['batch_size']}")
            logger.info(f"Worker Count: {optimal_config['worker_count']}")
            logger.info(
                f"Connection Pool Size: {optimal_config['connection_pool_size']}"
            )
            logger.info(
                f"Throughput: {optimal_config['throughput_docs_per_second']:.2f} docs/second"
            )
            logger.info(
                f"Processing Time: {optimal_config['elapsed_time_seconds']:.2f} seconds"
            )
            logger.info("============================")

        logger.info("Performance testing completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Error during performance testing: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
