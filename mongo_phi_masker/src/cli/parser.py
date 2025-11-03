#!/usr/bin/env python3
"""
Command-line interface parser for MongoDB PHI Masking Tool.

This module handles argument parsing for the MongoDB PHI Masking Tool,
providing a flexible CLI interface for various masking operations.
"""

import argparse
import logging
import os
from typing import Dict, Any, Optional


def get_cli_config() -> Dict[str, Any]:
    """Parse command-line arguments and return configuration.

    Returns:
        Dictionary containing CLI configuration
    """
    parser = argparse.ArgumentParser(
        description="MongoDB PHI Masking Tool - Mask PHI data in MongoDB collections"
    )

    # Configuration files
    parser.add_argument(
        "-c",
        "--config",
        dest="config_file",
        default=os.environ.get("MONGO_PHI_CONFIG", "config.json"),
        help="Path to the configuration file (default: config.json)",
    )

    parser.add_argument(
        "-e",
        "--env",
        dest="env_file",
        default=os.environ.get("MONGO_PHI_ENV", ".env"),
        help="Path to environment variables file (default: .env)",
    )

    # Modes of operation
    mode_group = parser.add_argument_group("Operation Modes")
    mode_group.add_argument(
        "--info",
        dest="info_only",
        action="store_true",
        help="Display configuration information and exit",
    )

    mode_group.add_argument(
        "--validate",
        dest="validate_only",
        action="store_true",
        help="Validate configuration and exit without processing",
    )

    mode_group.add_argument(
        "--verify",
        dest="verify_only",
        action="store_true",
        help="Verify masking without processing documents",
    )

    mode_group.add_argument(
        "--verify-after",
        dest="verify_after",
        action="store_true",
        help="Verify masking after processing documents",
    )

    mode_group.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Count documents but don't perform masking",
    )

    mode_group.add_argument(
        "--incremental",
        dest="incremental",
        action="store_true",
        help="Process only documents not previously masked",
    )

    mode_group.add_argument(
        "--reset-checkpoint",
        dest="reset_checkpoint",
        action="store_true",
        help="Reset checkpoint before processing",
    )

    mode_group.add_argument(
        "--in-situ",
        dest="in_situ",
        action="store_true",
        help="Perform in-situ masking (modify documents in-place instead of creating new ones)",
    )

    # Query options
    query_group = parser.add_argument_group("Query Options")
    query_group.add_argument(
        "-q", "--query", dest="query", help="JSON query filter for document selection"
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "-o", "--output", dest="output_file", help="Path to save results JSON file"
    )

    output_group.add_argument(
        "-l",
        "--log-level",
        dest="log_level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.environ.get("MONGO_PHI_LOG_LEVEL", "INFO"),
        help="Set logging level (default: INFO)",
    )
    
    # Logging options
    log_group = parser.add_argument_group("Logging Options")
    log_group.add_argument(
        "--log-file", 
        dest="log_file",
        help="Path to custom log file (default: logs/{environment}/masking_{date}.log)"
    )
    
    log_group.add_argument(
        "--log-max-bytes",
        dest="log_max_bytes",
        type=int,
        default=int(os.environ.get("MONGO_PHI_LOG_MAX_BYTES", 10 * 1024 * 1024)),
        help="Maximum log file size in bytes before rotation (default: 10MB)"
    )
    
    log_group.add_argument(
        "--log-backup-count",
        dest="log_backup_count",
        type=int,
        default=int(os.environ.get("MONGO_PHI_LOG_BACKUP_COUNT", 5)),
        help="Number of backup log files to keep (default: 5)"
    )
    
    log_group.add_argument(
        "--log-timed-rotation",
        dest="log_timed_rotation",
        action="store_true",
        help="Use time-based log rotation (midnight) instead of size-based"
    )

    # Performance options
    perf_group = parser.add_argument_group("Performance Options")
    perf_group.add_argument(
        "--batch-size",
        dest="batch_size",
        type=int,
        help="Override batch size from config",
    )

    perf_group.add_argument(
        "--workers",
        dest="worker_count",
        type=int,
        help="Override worker count from config",
    )

    perf_group.add_argument(
        "--disable-dynamic-batch",
        dest="disable_dynamic_batch",
        action="store_true",
        help="Disable dynamic batch sizing",
    )

    # Parse arguments
    args = parser.parse_args()

    # Convert to dictionary
    config = {
        "config_file": args.config_file,
        "env_file": args.env_file,
        "info_only": args.info_only,
        "validate_only": args.validate_only,
        "verify_only": args.verify_only,
        "verify_after": args.verify_after,
        "dry_run": args.dry_run,
        "incremental": args.incremental,
        "reset_checkpoint": args.reset_checkpoint,
        "in_situ": args.in_situ,
        "query": args.query,
        "output_file": args.output_file,
        "log_level": args.log_level,
        "log_file": args.log_file,
        "log_max_bytes": args.log_max_bytes,
        "log_backup_count": args.log_backup_count,
        "log_timed_rotation": args.log_timed_rotation,
        "batch_size_override": args.batch_size,
        "worker_count_override": args.worker_count,
        "disable_dynamic_batch": args.disable_dynamic_batch,
    }

    return config


# Add this function to maintain backward compatibility with tests
def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments and return Namespace object.
    This is maintained for backward compatibility with tests.
    
    Returns:
        Namespace containing parsed arguments
    """
    # Create parser with the same arguments as get_cli_config but return the Namespace directly
    parser = argparse.ArgumentParser(
        description="MongoDB PHI Masking Tool - Mask PHI data in MongoDB collections"
    )
    
    # Configuration files
    parser.add_argument(
        "-c",
        "--config",
        dest="config",  # Keep original name for backward compatibility
        default=os.environ.get("MONGO_PHI_CONFIG", "config/config_rules/config.json"),
        help="Path to the configuration file (default: config/config_rules/config.json)",
    )

    parser.add_argument(
        "-e",
        "--env",
        dest="env",  # Keep original name for backward compatibility
        default=os.environ.get("MONGO_PHI_ENV", ".env"),
        help="Path to environment variables file (default: .env)",
    )
    
    # Add simplified arguments for backward compatibility
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate configuration and exit without processing",
    )
    
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Count documents but don't perform masking",
    )
    
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Process only documents not previously masked",
    )
    
    parser.add_argument(
        "--info",
        action="store_true",
        help="Display configuration information and exit",
    )
    
    parser.add_argument(
        "--in-situ",
        action="store_true",
        help="Perform in-situ masking (modify documents in-place instead of creating new ones)",
    )
    
    parser.add_argument(
        "-q", "--query", 
        help="JSON query filter for document selection"
    )
    
    parser.add_argument(
        "-o", "--output", 
        help="Path to save results JSON file"
    )
    
    return parser.parse_args()
