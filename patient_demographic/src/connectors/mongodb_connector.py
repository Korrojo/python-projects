#!/usr/bin/env python3
"""
MongoDB Connection Manager
Unified: uses `common_config` (shared_config/.env + APP_ENV) exclusively.
Legacy dotenv and per-project env files have been removed.
"""

import logging
from pathlib import Path
from typing import Any

from pymongo import MongoClient

from common_config.config import get_settings  # type: ignore
from common_config.utils.logger import get_logger, setup_logging  # type: ignore


class MongoDBConnector:
    """Reusable MongoDB connection manager using unified settings only."""

    def __init__(self):
        self.client = None
        self.config: dict[str, Any] | None = None
        self._settings = get_settings()
        # Initialize shared logging target (project subfolder)
        proj_logs = Path(self._settings.paths.logs) / "patient_demographic"  # type: ignore
        proj_logs.mkdir(parents=True, exist_ok=True)
        setup_logging(log_dir=proj_logs, level=self._settings.log_level)  # type: ignore
        self._logger = get_logger(__name__)

    def _setup_logging(self):
        """Setup logging configuration."""
        logging.getLogger("pymongo").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    def connect(self) -> tuple[MongoClient | None, dict[str, Any] | None]:
        """Establish MongoDB connection using unified settings."""
        try:
            uri = self._settings.mongodb_uri
            db_name = self._settings.database_name
            if not uri or not db_name:
                logging.error("Unified settings missing mongodb_uri or database_name")
                return None, None
            logging.info(
                "Attempting MongoDB connection (APP_ENV=%s)...",
                getattr(self._settings, "app_env", ""),
            )
            self.client = MongoClient(uri, serverSelectionTimeoutMS=10000)
            self.client.admin.command("ping")
            logging.info("Successfully connected to MongoDB")
            # Minimal config dict to preserve existing return shape
            self.config = {"MONGO_DB": db_name}
            return self.client, self.config
        except Exception as e:
            logging.error(f"MongoDB connection failed: {e}", exc_info=True)
            return None, None

    def get_collection(self, db_name: str | None = None, collection_name: str | None = None):
        """
        Get MongoDB collection object.

        Args:
            db_name: Database name (uses config default if None)
            collection_name: Collection name (uses config default if None)

        Returns:
            MongoDB collection object or None if connection not established
        """
        if not self.client or not self.config:
            logging.error("MongoDB connection not established. Call connect() first.")
            return None
        # Unified settings - ensure non-None values for subscripting
        resolved_db_name: str = db_name or getattr(self._settings, "database_name", None) or "Ubiquity"
        resolved_collection_name: str = collection_name or "Patients"

        logging.info(f"Accessing collection: {resolved_db_name}.{resolved_collection_name}")
        return self.client[resolved_db_name][resolved_collection_name]

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logging.info("MongoDB connection closed.")

    def __enter__(self):
        """Context manager entry."""
        client, config = self.connect()
        if not client:
            raise ConnectionError("Failed to establish MongoDB connection")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# EnvironmentManager removed (legacy)
