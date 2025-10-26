from __future__ import annotations

import time
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

from ..utils.logger import get_logger


class MongoDBConnection:
    """Lightweight MongoDB connection compatible with existing projects.

    Expects a config_manager that implements:
      - get_mongodb_uri()
      - get_mongodb_database()
    """

    def __init__(self, config_manager):
        self.logger = get_logger(__name__)
        self.config_manager = config_manager
        self.uri: str = self.config_manager.get_mongodb_uri()
        self.database_name: str = self.config_manager.get_mongodb_database()
        self._client: MongoClient | None = None
        self._database: Database | None = None

    # Context manager support
    def __enter__(self) -> MongoDBConnection:
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disconnect()

    # Lifecycle
    def connect(self) -> None:
        if self._client is not None:
            return
        self.logger.info("Connecting to MongoDB ...")
        self._client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
        # Test connection
        self._client.admin.command("ping")
        self._database = self._client[self.database_name]
        self.logger.info(f"Connected to database '{self.database_name}'")

    def disconnect(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            finally:
                self._client = None
                self._database = None
                self.logger.info("MongoDB connection closed")

    def is_connected(self) -> bool:
        if self._client is None or self._database is None:
            return False
        try:
            self._client.admin.command("ping")
            return True
        except Exception:
            return False

    # Accessors
    def get_client(self) -> MongoClient:
        if self._client is None:
            self.connect()
        assert self._client is not None
        return self._client

    def get_database(self) -> Database:
        if self._database is None:
            self.connect()
        assert self._database is not None
        return self._database

    # Diagnostics
    def test_connection(self) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            client = self.get_client()
            db = self.get_database()
            client.admin.command("ping")
            info = client.server_info()
            try:
                collections = db.list_collection_names()
                count = len(collections)
            except Exception:
                count = None
            dt = (time.perf_counter() - start) * 1000.0
            return {
                "connected": True,
                "server_version": info.get("version"),
                "database_name": self.database_name,
                "collections_count": count,
                "response_time_ms": round(dt, 2),
            }
        except Exception as e:
            dt = (time.perf_counter() - start) * 1000.0
            return {
                "connected": False,
                "error": str(e),
                "response_time_ms": round(dt, 2),
            }
