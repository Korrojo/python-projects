#!/usr/bin/env python3
"""
MongoDB PHI Masking Tool - Main Entry Point

This module serves as the main entry point for the MongoDB PHI Masking Tool.
It coordinates the overall masking process using the modular components.
"""

import json
import logging
import os
import sys
import time
import traceback
from typing import Dict, Any, Optional, List

from src.cli.parser import get_cli_config, parse_arguments
from src.core.orchestrator import MaskingOrchestrator
from src.utils.config_loader import ConfigLoader
from src.core.connector import MongoConnector
from src.utils.logger import setup_logging
from src.utils.results import ResultsHandler
from src.utils.verification import MaskingVerifier
from src.models.masking_rule import RuleEngine
from src.utils.compatibility import monkeypatch_backwards_compatibility

# Initialize compatibility layer for tests
monkeypatch_backwards_compatibility()

# Setup logger
logger = logging.getLogger(__name__)


def display_info(config: Any) -> None:
    """Display information about the running configuration.

    This function checks the type of the input:
    - If it's a dictionary (from get_cli_config), it uses it directly
    - If it's an object with a config attribute (orchestrator), it uses that
    - If it's an object with a __dict__ attribute, it treats it as a namespace

    Args:
        config: Configuration dictionary or object
    """
    # Convert config to dictionary if needed
    config_dict = None
    
    if isinstance(config, dict):
        config_dict = config
    elif hasattr(config, 'config'):
        # It's an orchestrator object
        config_dict = config.config
    elif hasattr(config, '__dict__'):
        # It's likely an argparse namespace - convert to dict
        config_dict = vars(config)
        
        # For backward compatibility with old-style argparse results
        # Map common argparse attributes to expected config structure
        if 'log_level' in config_dict:
            # It's definitely a namespace from parse_arguments
            structured_dict = {}
            
            # Build mongodb section
            mongodb = {}
            source = {}
            if 'mongo_uri' in config_dict:
                source['uri'] = config_dict.get('mongo_uri')
            if 'mongo_db' in config_dict:
                source['database'] = config_dict.get('mongo_db')
            if 'mongo_collection' in config_dict:
                source['collection'] = config_dict.get('mongo_collection')
            
            destination = {}
            if 'dest_uri' in config_dict:
                destination['uri'] = config_dict.get('dest_uri')
            if 'dest_db' in config_dict:
                destination['database'] = config_dict.get('dest_db')
            if 'dest_collection' in config_dict:
                destination['collection'] = config_dict.get('dest_collection')
            
            if source:
                mongodb['source'] = source
            if destination:
                mongodb['destination'] = destination
            if mongodb:
                structured_dict['mongodb'] = mongodb
            
            # Build processing section
            processing = {}
            batch_size = {}
            if 'batch_size' in config_dict:
                batch_size['initial'] = config_dict.get('batch_size')
            if 'min_batch_size' in config_dict:
                batch_size['min'] = config_dict.get('min_batch_size')
            if 'max_batch_size' in config_dict:
                batch_size['max'] = config_dict.get('max_batch_size')
            
            if 'masking_mode' in config_dict:
                processing['masking_mode'] = config_dict.get('masking_mode')
            if batch_size:
                processing['batch_size'] = batch_size
            if processing:
                structured_dict['processing'] = processing
            
            # Add remaining top-level keys
            for key, value in config_dict.items():
                if key not in ['mongo_uri', 'mongo_db', 'mongo_collection',
                              'dest_uri', 'dest_db', 'dest_collection',
                              'batch_size', 'min_batch_size', 'max_batch_size',
                              'masking_mode']:
                    structured_dict[key] = value
            
            config_dict = structured_dict
    
    if not config_dict:
        logging.error("Cannot display configuration info - unknown config format")
        return
        
    # Display configuration info
    logging.info("MongoDB PHI Masker Configuration:")
    
    # Display processing settings
    process_config = config_dict.get("processing", {})
    logging.info(f"Processing Mode: {process_config.get('masking_mode', 'Not specified')}")
    
    batch_config = config_dict.get("batch_size") or process_config.get("batch_size", {})
    if isinstance(batch_config, dict):
        logging.info(f"Batch Size: Initial={batch_config.get('initial', 'Not specified')}, "
                    f"Min={batch_config.get('min', 'Not specified')}, "
                    f"Max={batch_config.get('max', 'Not specified')}")
    else:
        logging.info(f"Batch Size: {batch_config}")
    
    # Display MongoDB settings (but mask credentials)
    mongo_config = config_dict.get("mongodb", {})
    if mongo_config:
        src_config = mongo_config.get("source", {})
        if src_config:
            # Extract hostname from URI without showing credentials
            src_uri = src_config.get("uri", "")
            if src_uri:
                parts = src_uri.split('@')
                if len(parts) > 1:
                    host_info = parts[1]
                else:
                    host_info = parts[0]
                logging.info(f"Source MongoDB: {host_info}, " 
                            f"DB={src_config.get('database', 'Not specified')}, "
                            f"Collection={src_config.get('collection', 'Not specified')}")
        
        dest_config = mongo_config.get("destination", {})
        if dest_config:
            # Extract hostname from URI without showing credentials
            dest_uri = dest_config.get("uri", "")
            if dest_uri:
                parts = dest_uri.split('@')
                if len(parts) > 1:
                    host_info = parts[1]
                else:
                    host_info = parts[0]
                logging.info(f"Destination MongoDB: {host_info}, "
                            f"DB={dest_config.get('database', 'Not specified')}, "
                            f"Collection={dest_config.get('collection', 'Not specified')}")


def verify_only(config: Dict[str, Any], log_level: str) -> Dict[str, Any]:
    """Verify masking results without processing documents.

    Args:
        config: Configuration dictionary
        log_level: Logging level

    Returns:
        Verification results
    """
    logger.info("Verifying masking results without processing...")

    try:
        # Create connectors
        source_config = config["mongodb"]["source"]
        dest_config = config["mongodb"]["destination"]

        source_connector = MongoConnector(
            uri=source_config["uri"],
            database=source_config["database"],
            collection=source_config["collection"],
        )

        dest_connector = MongoConnector(
            uri=dest_config["uri"],
            database=dest_config["database"],
            collection=dest_config["collection"],
        )

        # Create rule engine
        rule_engine = RuleEngine(config.get("masking_rules", []))

        # Create verifier
        verifier = MaskingVerifier(
            source_connector=source_connector,
            dest_connector=dest_connector,
            rule_engine=rule_engine,
        )

        # Verify masking
        verification_results = verifier.verify_masking(log_level=log_level)

        # Disconnect from MongoDB
        source_connector.disconnect()
        dest_connector.disconnect()

        return verification_results

    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        logger.debug(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "phi_fields_masked": False,
            "non_phi_fields_preserved": False,
            "verified_documents": 0,
            "details": {"error": str(e)},
        }


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        # Get CLI configuration
        cli_config = get_cli_config()

        # Setup logging with enhanced options
        log_file = setup_logging(
            log_level=cli_config["log_level"],
            environment=None,  # Will be set after loading config
            log_file=cli_config.get("log_file"),
            max_bytes=cli_config.get("log_max_bytes", 10*1024*1024),
            backup_count=cli_config.get("log_backup_count", 5),
            use_timed_rotating=cli_config.get("log_timed_rotation", False)
        )
        logger.info(f"Starting MongoDB PHI Masking Tool v2.0.0")
        logger.info(f"Log file: {log_file}")

        # Load configuration
        config_loader = ConfigLoader(cli_config["config_file"], cli_config["env_file"])
        config = config_loader.load_config()

        # Get environment name
        environment = config.get("environment", "DEFAULT")
        logger.info(f"Using environment: {environment}")

        # Initialize results handler
        results_handler = ResultsHandler(environment)

        # Display info if requested
        if cli_config["info_only"]:
            display_info(config)
            return 0

        # Validate configuration if requested
        if cli_config["validate_only"]:
            # Validate MongoDB connections
            source_config = config["mongodb"]["source"]
            dest_config = config["mongodb"]["destination"]

            logger.info("Validating MongoDB connections...")

            # Source connection
            try:
                source_connector = MongoConnector(
                    uri=source_config["uri"],
                    database=source_config["database"],
                    collection=source_config["collection"],
                )
                source_connector.test_connection()
                logger.info("Source MongoDB connection successful")
                source_connector.disconnect()
            except Exception as e:
                logger.error(f"Source MongoDB connection failed: {str(e)}")
                return 1

            # Destination connection
            try:
                dest_connector = MongoConnector(
                    uri=dest_config["uri"],
                    database=dest_config["database"],
                    collection=dest_config["collection"],
                )
                dest_connector.test_connection()
                logger.info("Destination MongoDB connection successful")
                dest_connector.disconnect()
            except Exception as e:
                logger.error(f"Destination MongoDB connection failed: {str(e)}")
                return 1

            # Validate masking rules
            try:
                rule_engine = RuleEngine(config.get("masking_rules", []))
                logger.info(
                    f"Masking rules validated successfully ({len(rule_engine.rules)} rules)"
                )
            except Exception as e:
                logger.error(f"Masking rules validation failed: {str(e)}")
                return 1

            logger.info("Configuration validation successful")
            return 0

        # Parse query if provided
        query = None
        if cli_config["query"]:
            try:
                query = json.loads(cli_config["query"])
                logger.info(f"Using query filter: {cli_config['query']}")
            except json.JSONDecodeError:
                logger.error(f"Invalid query filter: {cli_config['query']}")
                return 1

        # Verify only if requested
        if cli_config["verify_only"]:
            verification_results = verify_only(config, cli_config["log_level"])

            # Save verification results
            results_handler.save_results(
                verification_results, cli_config["output_file"]
            )
            results_handler.log_results_summary(verification_results, verify_only=True)

            if (
                not verification_results["phi_fields_masked"]
                or not verification_results["non_phi_fields_preserved"]
            ):
                logger.error("Masking verification failed")
                return 1
            else:
                logger.info("Masking verification completed successfully")
                return 0

        # Create and configure the orchestrator
        try:
            orchestrator = MaskingOrchestrator(config=config)
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {str(e)}")
            logger.debug(traceback.format_exc())
            return 1

        # Reset checkpoint if requested
        if cli_config["reset_checkpoint"]:
            logger.info("Resetting checkpoint...")
            orchestrator.reset_checkpoint()

        # Start the masking process
        start_time = time.time()

        if cli_config["dry_run"]:
            # Perform dry run (count only)
            try:
                count = orchestrator.count_documents(query)
                logger.info(
                    f"Dry run completed. Found {count} documents matching the query."
                )
                results = {"document_count": count, "dry_run": True}
            except Exception as e:
                logger.error(f"Dry run failed: {str(e)}")
                logger.debug(traceback.format_exc())
                return 1
        else:
            # Process documents
            logger.info("Starting document processing...")
            try:
                if cli_config["in_situ"]:
                    # Perform in-situ masking (modify documents in place)
                    logger.info("Using in-situ masking mode (modifying documents in place)")
                    results = orchestrator.run_in_situ_masking(
                        query=query,
                        batch_size=cli_config.get("batch_size_override", 100),
                        dry_run=False
                    )
                else:
                    # Traditional read-mask-transfer-insert approach
                    logger.info("Using traditional masking mode (read-mask-transfer-insert)")
                    results = orchestrator.process_documents(
                        query=query, incremental=cli_config["incremental"]
                    )
            except Exception as e:
                logger.error(f"Document processing failed: {str(e)}")
                logger.debug(traceback.format_exc())
                return 1

        # Add elapsed time to results
        elapsed_time = time.time() - start_time
        results["elapsed_time"] = elapsed_time
        logger.info(f"Processing completed in {elapsed_time:.2f} seconds")

        # Verify results if not a dry run and verification is requested
        if not cli_config["dry_run"] and cli_config["verify_after"]:
            logger.info("Verifying masking results...")
            verification_results = verify_only(config, cli_config["log_level"])

            # Add verification results to processing results
            results["verification"] = verification_results

            # Log verification summary
            results_handler.log_results_summary(verification_results, verify_only=False)

            if not verification_results.get(
                "phi_fields_masked", False
            ) or not verification_results.get("non_phi_fields_preserved", False):
                logger.warning("Masking verification after processing found issues")

        # Save results
        if cli_config["output_file"]:
            results_handler.save_results(results, cli_config["output_file"])
            logger.info(f"Results saved to {cli_config['output_file']}")

        # Log results summary
        results_handler.log_results_summary(results)

        # Check for errors
        if results.get("error_count", 0) > 0:
            logger.warning(f"Completed with {results['error_count']} errors")
            return 2 if results.get("processed_count", 0) > 0 else 1
        else:
            logger.info("Processing completed successfully")
            return 0

    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.debug(traceback.format_exc())
        sys.exit(1)
