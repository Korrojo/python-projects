from __future__ import annotations

import time
from dataclasses import dataclass

from pymongo import MongoClient
from pymongo.errors import PyMongoError


@dataclass
class ConnectionInfo:
    connected: bool
    database_name: str | None
    server_version: str | None
    response_time_ms: float | None
    collections_count: int | None
    error: str | None = None


class MongoConnection:
    """Context-managed MongoDB connection wrapper.

    Usage:
        conn = MongoConnection(uri, db_name)
        with conn as c:
            db = c.db
            # ... use db
    """

    def __init__(self, uri: str, database_name: str, timeout_ms: int = 5000) -> None:
        self._uri = uri
        self._db_name = database_name
        self._timeout_ms = timeout_ms
        self._client: MongoClient | None = None

    def __enter__(self) -> MongoConnection:
        self._client = MongoClient(self._uri, serverSelectionTimeoutMS=self._timeout_ms)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    @property
    def client(self) -> MongoClient:
        if self._client is None:
            self._client = MongoClient(self._uri, serverSelectionTimeoutMS=self._timeout_ms)
        return self._client

    @property
    def db(self):
        return self.client[self._db_name]

    def test_connection(self) -> ConnectionInfo:
        start = time.perf_counter()
        try:
            # Ping server
            self.client.admin.command("ping")
            # Get server version
            server_info = self.client.server_info()
            version = server_info.get("version")
            # Quick list collections (may require permission)
            try:
                collections = self.db.list_collection_names()
                count = len(collections)
            except PyMongoError:
                count = None
            dt = (time.perf_counter() - start) * 1000.0
            return ConnectionInfo(
                connected=True,
                database_name=self._db_name,
                server_version=str(version) if version else None,
                response_time_ms=dt,
                collections_count=count,
            )
        except Exception as e:  # noqa: BLE001
            dt = (time.perf_counter() - start) * 1000.0
            return ConnectionInfo(
                connected=False,
                database_name=self._db_name,
                server_version=None,
                response_time_ms=dt,
                collections_count=None,
                error=str(e),
            )
