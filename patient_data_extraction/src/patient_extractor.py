"""
Patient Data Extractor

This module handles the two-step patient data extraction process:
1. Extract PatientIds from MO state patients (Database 1)
2. Extract detailed patient information using those IDs (Database 2)
"""

import json
import time
from pathlib import Path
from typing import Any

from common_config.config.config_manager import ConfigManager
from common_config.db.connection import MongoDBConnection
from common_config.export.data_exporter import DataExporter
from common_config.extraction.data_extractor import DataExtractor
from common_config.utils.exceptions import (
    DatabaseError,
    DataProcessingError,
    ValidationError,
)
from common_config.utils.logger import get_logger, get_run_timestamp


class MultiDatabaseConfigManager(ConfigManager):
    """Extended configuration manager for multiple database connections."""

    def get_db1_uri(self) -> str:
        """Get Database 1 MongoDB URI."""
        uri = self.get_env("DB1_MONGODB_URI", required=True)
        if not uri:
            raise ValidationError("DB1_MONGODB_URI is required", field="DB1_MONGODB_URI")
        return uri

    def get_db1_database(self) -> str:
        """Get Database 1 name."""
        db_name = self.get_env("DB1_DATABASE_NAME", required=True)
        if not db_name:
            raise ValidationError("DB1_DATABASE_NAME is required", field="DB1_DATABASE_NAME")
        return db_name

    def get_db2_uri(self) -> str:
        """Get Database 2 MongoDB URI."""
        uri = self.get_env("DB2_MONGODB_URI", required=True)
        if not uri:
            raise ValidationError("DB2_MONGODB_URI is required", field="DB2_MONGODB_URI")
        return uri

    def get_db2_database(self) -> str:
        """Get Database 2 name."""
        db_name = self.get_env("DB2_DATABASE_NAME", required=True)
        if not db_name:
            raise ValidationError("DB2_DATABASE_NAME is required", field="DB2_DATABASE_NAME")
        return db_name

    def validate_config(self) -> None:
        """Validate that required DB1/DB2 settings exist and ensure paths."""
        # Validate required multi-DB environment variables
        self.get_db1_uri()
        self.get_db1_database()
        self.get_db2_uri()
        self.get_db2_database()

        # Ensure standard paths exist (mirrors base implementation intent)
        for path_key in ["data_input", "data_output", "logs"]:
            path = Path(self.get_path(path_key))
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)


class PatientDataExtractor:
    """Main class for patient data extraction across multiple databases."""

    def __init__(self, config_file: str | None = None):
        """
        Initialize the patient data extractor.

        Args:
            config_file: Path to extraction configuration file
        """
        self.logger = get_logger(__name__)

        # Load configuration
        self.config_manager = MultiDatabaseConfigManager()
        self.config_file = config_file or "config/extraction_config.json"
        self._load_extraction_config()

        # Initialize output directory under shared data/output/<project>
        self.output_dir = Path(self.config_manager.get_path("data_output")) / "patient_data_extraction"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Run timestamp for file prefixes (YYYYMMDD_HHMMSS)
        self.run_ts = get_run_timestamp()
        # Placeholders for output file paths for summary
        self._step1_output_path = None
        self._step2_output_path = None

        # Initialize connections (will be created when needed)
        self.db1_connection = None
        self.db2_connection = None

        # Initialize components
        self.exporter = DataExporter(self.config_manager)

        self.logger.info("Patient Data Extractor initialized")

    def _load_extraction_config(self) -> None:
        """Load extraction-specific configuration."""
        try:
            config_path = Path(self.config_file)
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")

            with open(config_path, encoding="utf-8") as f:
                self.extraction_config = json.load(f)

            self.logger.info(f"Loaded extraction configuration from {config_path}")

        except Exception as e:
            raise DataProcessingError(f"Failed to load extraction configuration: {e}") from e

    def _get_db1_connection(self) -> MongoDBConnection:
        """Get or create Database 1 connection."""
        if self.db1_connection is None:
            # Create custom config manager for DB1
            class DB1ConfigManager(MultiDatabaseConfigManager):
                def get_mongodb_uri(self):
                    return super().get_db1_uri()

                def get_mongodb_database(self):
                    return super().get_db1_database()

            db1_config = DB1ConfigManager()
            self.db1_connection = MongoDBConnection(db1_config)
            self.logger.info("Created Database 1 connection")

        return self.db1_connection

    def _get_db2_connection(self) -> MongoDBConnection:
        """Get or create Database 2 connection."""
        if self.db2_connection is None:
            # Create custom config manager for DB2
            class DB2ConfigManager(MultiDatabaseConfigManager):
                def get_mongodb_uri(self):
                    return super().get_db2_uri()

                def get_mongodb_database(self):
                    return super().get_db2_database()

            db2_config = DB2ConfigManager()
            self.db2_connection = MongoDBConnection(db2_config)
            self.logger.info("Created Database 2 connection")

        return self.db2_connection

    def extract_mo_patient_ids(self) -> list[int]:
        """
        Step 1: Extract PatientIds from MO state patients.

        Returns:
            List of PatientIds
        """
        self.logger.info("Starting Step 1: Extract MO PatientIds")

        try:
            # Get step 1 configuration
            step1_config = self.extraction_config["extraction"]["step1"]

            # Connect to Database 1
            db1_conn = self._get_db1_connection()
            extractor = DataExtractor(db1_conn, self.config_manager)

            with db1_conn:
                # Test connection
                conn_info = db1_conn.test_connection()
                if not conn_info["connected"]:
                    raise DatabaseError(f"Database 1 connection failed: {conn_info['error']}")

                self.logger.info(f"Connected to Database 1: {conn_info['database_name']}")

                # Extract data
                self.logger.info(f"Querying collection: {step1_config['collection']}")
                self.logger.info(f"Query: {step1_config['query']}")

                documents = extractor.extract_from_collection(
                    collection_name=step1_config["collection"],
                    filter_query=step1_config["query"],
                    projection=step1_config["projection"],
                )

                if not documents:
                    self.logger.warning("No MO patients found")
                    return []

                # Extract PatientIds (numeric)
                patient_ids = []
                for doc in documents:
                    patient_id = doc.get("PatientId")
                    if patient_id:
                        patient_ids.append(patient_id)

                self.logger.info(f"Extracted {len(patient_ids)} PatientIds from MO state")

                # Save to CSV
                # Timestamp-prefixed filename
                output_file = self.output_dir / f"{self.run_ts}_{step1_config['output_file']}"
                patient_data = [{"PatientId": pid} for pid in patient_ids]

                self.exporter.to_csv(patient_data, output_file)
                self.logger.info(f"Saved PatientIds to: {output_file}")
                self._step1_output_path = output_file

                # Validate results
                if self.extraction_config["validation"]["validate_patient_ids"]:
                    self._validate_patient_ids(patient_ids)

                return patient_ids

        except Exception as e:
            self.logger.error(f"Step 1 failed: {e}")
            raise DataProcessingError(f"Failed to extract MO PatientIds: {e}") from e

    def extract_patient_details(self, patient_ids: list[int]) -> list[dict[str, Any]]:
        """
        Step 2: Extract detailed patient information using PatientIds.

        Args:
            patient_ids: List of PatientIds to query

        Returns:
            List of patient detail documents
        """
        self.logger.info(f"Starting Step 2: Extract patient details for {len(patient_ids)} patients")

        if not patient_ids:
            self.logger.warning("No PatientIds provided for step 2")
            return []

        try:
            # Get step 2 configuration
            step2_config = self.extraction_config["extraction"]["step2"]

            # Connect to Database 2
            db2_conn = self._get_db2_connection()
            extractor = DataExtractor(db2_conn, self.config_manager)

            with db2_conn:
                # Test connection
                conn_info = db2_conn.test_connection()
                if not conn_info["connected"]:
                    raise DatabaseError(f"Database 2 connection failed: {conn_info['error']}")

                self.logger.info(f"Connected to Database 2: {conn_info['database_name']}")

                # Build query with PatientIds
                query = {"PatientId": {"$in": patient_ids}}

                self.logger.info(f"Querying collection: {step2_config['collection']}")
                self.logger.info(f"Query: PatientId in list of {len(patient_ids)} IDs")

                # Extract data in batches for large datasets
                batch_size = step2_config.get("batch_size", 1000)
                all_documents = []

                if len(patient_ids) > batch_size:
                    self.logger.info(f"Processing in batches of {batch_size}")

                    for i in range(0, len(patient_ids), batch_size):
                        batch_ids = patient_ids[i : i + batch_size]
                        batch_query = {"PatientId": {"$in": batch_ids}}

                        batch_docs = extractor.extract_from_collection(
                            collection_name=step2_config["collection"],
                            filter_query=batch_query,
                            projection=step2_config["projection"],
                        )

                        all_documents.extend(batch_docs)
                        self.logger.info(f"Processed batch {i // batch_size + 1}: {len(batch_docs)} documents")
                else:
                    all_documents = extractor.extract_from_collection(
                        collection_name=step2_config["collection"],
                        filter_query=query,
                        projection=step2_config["projection"],
                    )

                self.logger.info(f"Extracted {len(all_documents)} patient detail records")

                # Save to CSV
                # Timestamp-prefixed filename
                output_file = self.output_dir / f"{self.run_ts}_{step2_config['output_file']}"

                if all_documents:
                    self.exporter.to_csv(all_documents, output_file)
                    self.logger.info(f"Saved patient details to: {output_file}")
                    self._step2_output_path = output_file
                else:
                    self.logger.warning("No patient details found")

                return all_documents

        except Exception as e:
            self.logger.error(f"Step 2 failed: {e}")
            raise DataProcessingError(f"Failed to extract patient details: {e}") from e

    def run_full_extraction(self) -> dict[str, Any]:
        """
        Run the complete two-step extraction process.

        Returns:
            Summary of extraction results
        """
        start_time = time.time()
        self.logger.info("Starting full patient data extraction")

        try:
            # Step 1: Extract MO PatientIds
            patient_ids = self.extract_mo_patient_ids()

            if not patient_ids:
                return {
                    "success": True,
                    "step1_count": 0,
                    "step2_count": 0,
                    "duration": time.time() - start_time,
                    "message": "No MO patients found",
                }

            # Step 2: Extract patient details
            patient_details = self.extract_patient_details(patient_ids)

            # Generate summary
            duration = time.time() - start_time

            summary = {
                "success": True,
                "step1_count": len(patient_ids),
                "step2_count": len(patient_details),
                "duration": duration,
                "output_files": {
                    "patient_ids": str(
                        self._step1_output_path
                        or self.output_dir / f"{self.run_ts}_"
                        + self.extraction_config["extraction"]["step1"]["output_file"]
                    ),
                    "patient_details": str(
                        self._step2_output_path
                        or self.output_dir / f"{self.run_ts}_"
                        + self.extraction_config["extraction"]["step2"]["output_file"]
                    ),
                },
            }

            self.logger.info(f"Extraction completed successfully in {duration:.2f} seconds")
            self.logger.info(f"Step 1: {summary['step1_count']} PatientIds")
            self.logger.info(f"Step 2: {summary['step2_count']} patient records")

            return summary

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Full extraction failed after {duration:.2f} seconds: {e}")

            return {"success": False, "error": str(e), "duration": duration}

        finally:
            # Clean up connections
            self._cleanup_connections()

    def _validate_patient_ids(self, patient_ids: list[int]) -> None:
        """Validate extracted PatientIds."""
        validation_config = self.extraction_config["validation"]

        # Check count limits
        max_ids = validation_config.get("max_patient_ids", 100000)
        if len(patient_ids) > max_ids:
            raise ValidationError(
                f"Too many PatientIds extracted: {len(patient_ids)} > {max_ids}",
                field="patient_ids_count",
            )

        # Check for duplicates
        unique_ids = set(patient_ids)
        if len(unique_ids) != len(patient_ids):
            duplicates = len(patient_ids) - len(unique_ids)
            self.logger.warning(f"Found {duplicates} duplicate PatientIds")

        # Check for empty/null IDs
        empty_ids = sum(1 for pid in patient_ids if pid is None or (isinstance(pid, str) and pid.strip() == ""))
        if empty_ids > 0:
            self.logger.warning(f"Found {empty_ids} empty PatientIds")

        self.logger.info(f"PatientId validation passed: {len(unique_ids)} unique IDs")

    def _cleanup_connections(self) -> None:
        """Clean up database connections."""
        if self.db1_connection:
            self.db1_connection.disconnect()
            self.db1_connection = None

        if self.db2_connection:
            self.db2_connection.disconnect()
            self.db2_connection = None

        self.logger.info("Database connections cleaned up")

    def get_extraction_status(self) -> dict[str, Any]:
        """Get current extraction status and configuration."""
        return {
            "config_loaded": hasattr(self, "extraction_config"),
            "output_directory": str(self.output_dir),
            "db1_connected": self.db1_connection is not None and self.db1_connection.is_connected(),
            "db2_connected": self.db2_connection is not None and self.db2_connection.is_connected(),
            "extraction_config": (self.extraction_config if hasattr(self, "extraction_config") else None),
        }
