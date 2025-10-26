#!/usr/bin/env python3
"""
Main execution script for Patient Data Extraction.

This script runs the complete two-step patient data extraction process:
1. Extract PatientIds from MO state patients (Database 1)
2. Extract detailed patient information using those IDs (Database 2)
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add local project 'src' so we can import 'patient_extractor'
sys.path.insert(0, str(Path(__file__).parent / "src"))

from patient_extractor import MultiDatabaseConfigManager, PatientDataExtractor  # type: ignore[import-not-found]

from common_config.config.settings import get_settings
from common_config.utils.logger import get_logger, get_run_timestamp, setup_logging


def main():
    """Main execution function."""

    # Initialize configuration and logging
    config_manager = MultiDatabaseConfigManager()
    settings = get_settings()
    # Use a project-specific logs subfolder
    log_dir = Path(settings.paths.logs) / "patient_data_extraction"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir)
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info("Patient Data Extraction - Starting")
    logger.info("=" * 60)

    try:
        # Validate configuration
        logger.info("Validating configuration...")
        config_manager.validate_config()

        # Test database connections
        logger.info("Testing database connections...")

        # Test DB1 connection
        try:
            db1_name = config_manager.get_db1_database()
            logger.info(f"DB1 configured: {db1_name}")
        except Exception as e:
            logger.error(f"DB1 configuration error: {e}")
            return 1

        # Test DB2 connection
        try:
            db2_name = config_manager.get_db2_database()
            logger.info(f"DB2 configured: {db2_name}")
        except Exception as e:
            logger.error(f"DB2 configuration error: {e}")
            return 1

        # Initialize extractor
        logger.info("Initializing Patient Data Extractor...")
        extractor = PatientDataExtractor()

        # Show extraction status
        status = extractor.get_extraction_status()
        logger.info(f"Output directory: {status['output_directory']}")
        logger.info(f"Configuration loaded: {status['config_loaded']}")

        # Run extraction
        logger.info("Starting patient data extraction...")
        results = extractor.run_full_extraction()

        # Process results
        if results["success"]:
            logger.info("=" * 60)
            logger.info("EXTRACTION COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            logger.info(f"Duration: {results['duration']:.2f} seconds")
            logger.info(f"Step 1 - MO PatientIds extracted: {results['step1_count']}")
            logger.info(f"Step 2 - Patient details extracted: {results['step2_count']}")

            if "output_files" in results:
                logger.info("Output files:")
                for file_type, file_path in results["output_files"].items():
                    logger.info(f"  {file_type}: {file_path}")

            # Generate summary report
            generate_summary_report(results, logger, config_manager)

            return 0
        else:
            logger.error("=" * 60)
            logger.error("EXTRACTION FAILED")
            logger.error("=" * 60)
            logger.error(f"Error: {results['error']}")
            logger.error(f"Duration: {results['duration']:.2f} seconds")
            return 1

    except KeyboardInterrupt:
        logger.warning("Extraction interrupted by user")
        return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error("Extraction failed", exc_info=True)
        return 1


def generate_summary_report(results: dict, logger, config_manager) -> None:
    """Generate a summary report of the extraction using configured data/output path."""

    try:
        ts = get_run_timestamp()
        report_dir = Path(config_manager.get_path("data_output"))
        report_file = report_dir / f"{ts}_extraction_summary.json"

        # Ensure output directory exists
        report_file.parent.mkdir(parents=True, exist_ok=True)

        # Add timestamp to results
        report_data = {
            **results,
            "extraction_timestamp": datetime.now().isoformat(),
            "report_generated": ts,
        }

        # Write summary report
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)

        logger.info(f"Summary report saved: {report_file}")

    except Exception as e:
        logger.warning(f"Could not generate summary report: {e}")


def show_help():
    """Show help information."""
    help_text = """
Patient Data Extraction Tool

This tool extracts patient data in two steps:
1. Extract PatientIds from MO state patients (Database 1)
2. Extract detailed patient information using those IDs (Database 2)

Usage:
    python run_extraction.py [options]

Options:
    --help, -h          Show this help message
    --config FILE       Use custom configuration file
    --dry-run          Validate configuration without running extraction
    --test-connections  Test database connections only

Configuration:
    - Update config/.env with your database connection details
    - Modify config/extraction_config.json for query parameters

Output:
    - data/output/<timestamp>_mo_patient_ids.csv        - PatientIds from MO state
    - data/output/<timestamp>_patient_details.csv       - Detailed patient information
    - data/output/<timestamp>_extraction_summary.json   - Execution summary
    - logs/<timestamp>_app.log                - Detailed logs

Examples:
    python run_extraction.py
    python run_extraction.py --test-connections
    python run_extraction.py --config custom_config.json
"""
    print(help_text)


def test_connections_only():
    """Test database connections without running extraction."""

    # Initialize configuration and logging
    settings = get_settings()
    setup_logging(log_dir=settings.paths.logs)
    logger = get_logger(__name__)

    logger.info("Testing database connections...")

    try:
        # Initialize extractor
        extractor = PatientDataExtractor()

        # Test DB1
        logger.info("Testing Database 1 connection...")
        db1_conn = extractor._get_db1_connection()
        with db1_conn:
            conn_info = db1_conn.test_connection()
            if conn_info["connected"]:
                logger.info(f"OK DB1 connected: {conn_info['database_name']} (v{conn_info['server_version']})")
                logger.info(f"  Collections: {conn_info['collections_count']}")
                logger.info(f"  Response time: {conn_info['response_time_ms']}ms")
            else:
                logger.error(f"FAIL DB1 connection failed: {conn_info['error']}")
                return 1

        # Test DB2
        logger.info("Testing Database 2 connection...")
        db2_conn = extractor._get_db2_connection()
        with db2_conn:
            conn_info = db2_conn.test_connection()
            if conn_info["connected"]:
                logger.info(f"OK DB2 connected: {conn_info['database_name']} (v{conn_info['server_version']})")
                logger.info(f"  Collections: {conn_info['collections_count']}")
                logger.info(f"  Response time: {conn_info['response_time_ms']}ms")
            else:
                logger.error(f"FAIL DB2 connection failed: {conn_info['error']}")
                return 1

        logger.info("All database connections successful")
        return 0

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return 1


if __name__ == "__main__":
    # Parse command line arguments
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        show_help()
        sys.exit(0)

    if "--test-connections" in args:
        sys.exit(test_connections_only())

    if "--dry-run" in args:
        print("Dry run mode - validating configuration only")
        try:
            config_manager = MultiDatabaseConfigManager()
            config_manager.validate_config()
            print("✓ Configuration validation passed")
            sys.exit(0)
        except Exception as e:
            print(f"✗ Configuration validation failed: {e}")
            sys.exit(1)

    # Run main extraction
    exit_code = main()
    sys.exit(exit_code)
