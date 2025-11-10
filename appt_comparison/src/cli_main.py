"""CLI entry point for appointment comparison validator."""

from __future__ import annotations

import json
import os
from pathlib import Path

import typer
from validator import AppointmentValidator

from common_config.config import get_settings, load_app_config
from common_config.db.connection import MongoDBConnection
from common_config.utils.logger import get_logger, setup_logging

app = typer.Typer(help="Appointment Comparison Validator - Compare Athena CSV vs MongoDB StaffAvailability")


class SimpleConfigManager:
    """Simple config manager for MongoDB connection."""

    def __init__(self, uri: str, database: str):
        self._uri = uri
        self._database = database

    def get_mongodb_uri(self) -> str:
        return self._uri

    def get_mongodb_database(self) -> str:
        return self._database


@app.command()
def validate(
    input_file: str = typer.Option(
        ..., "--input", "-i", help="Path to input CSV file (relative to data/input/appointment_comparison/ or absolute)"
    ),
    env: str | None = typer.Option(None, "--env", "-e", help="Override APP_ENV (e.g., PROD, STG, LOCL)"),
    collection: str = typer.Option("StaffAvailability", "--collection", "-c", help="MongoDB collection name"),
    limit: int | None = typer.Option(
        None, "--limit", "-l", help="Limit number of rows to process (useful for testing)"
    ),
    batch_size: int = typer.Option(100, "--batch-size", "-b", help="Number of records to process per batch"),
    progress_frequency: int = typer.Option(100, "--progress-frequency", "-p", help="Log progress every N rows"),
):
    """Validate appointment CSV against MongoDB StaffAvailability collection."""

    # Override APP_ENV if specified
    if env:
        os.environ["APP_ENV"] = env.upper()

    # Get settings
    settings = get_settings()

    # Setup logging - use absolute path to repo-level logs directory
    # Path structure: python/appointment_comparison/src/appointment_comparison/__main__.py
    # Go up 4 levels to get to python/ root
    python_root = Path(__file__).parent.parent.parent.parent
    log_dir = python_root / settings.paths.logs / "appointment_comparison"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir)
    logger = get_logger(__name__)

    try:
        # Load app config
        app_config = load_app_config(required=False)

        # Get MongoDB credentials
        if not settings.mongodb_uri or not settings.database_name:
            logger.error("MongoDB URI and DATABASE_NAME must be set in shared_config/.env")
            logger.error(f"Current APP_ENV: {os.environ.get('APP_ENV', '(not set)')}")
            raise typer.Exit(code=1)

        # Resolve input file path
        input_path = Path(input_file)
        if not input_path.is_absolute():
            # Try relative to data/input/appointment_comparison
            # Use absolute path from current working directory up to python repo root
            # Path structure: python/appointment_comparison/src/appointment_comparison/__main__.py
            # So we need to go up 4 levels to get to python/
            python_root = Path(__file__).parent.parent.parent.parent
            input_path = python_root / settings.paths.data_input / "appointment_comparison" / input_file

        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            logger.error(f"Searched in: {input_path.parent}")
            raise typer.Exit(code=1)

        # Output directory
        python_root = Path(__file__).parent.parent.parent.parent
        output_dir = python_root / settings.paths.data_output / "appointment_comparison"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Connect to MongoDB
        logger.info("Connecting to MongoDB...")
        config_mgr = SimpleConfigManager(settings.mongodb_uri, settings.database_name)

        with MongoDBConnection(config_mgr) as conn:
            db = conn.get_database()

            # Get processing config
            processing_config = app_config.get("processing", {}) if app_config else {}
            validation_config = app_config.get("validation", {}) if app_config else {}

            # Create validator
            validator = AppointmentValidator(
                db=db,
                collection_name=collection,
                batch_size=batch_size or processing_config.get("batch_size", 100),
                progress_log_frequency=progress_frequency or processing_config.get("progress_log_frequency", 100),
                max_retries=processing_config.get("max_retries", 3),
                base_retry_sleep=processing_config.get("base_retry_sleep", 2.0),
                case_sensitive_visit_type=validation_config.get("case_sensitive_visit_type", False),
                trim_strings=validation_config.get("trim_strings", True),
            )

            # Run validation
            output_path, cleaned_path = validator.validate_file(input_path, output_dir, limit)

            # Print summary for machine reading
            summary = {
                "status": "success",
                "input_file": str(input_path),
                "output_file": str(output_path),
                "cleaned_file": str(cleaned_path) if cleaned_path else None,
                "statistics": validator.stats,
            }

            print("\n" + "=" * 80)
            print("VALIDATION SUMMARY (JSON)")
            print("=" * 80)
            print(json.dumps(summary, indent=2))

    except Exception as e:
        logger.exception(f"Validation failed: {e}")
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
