from __future__ import annotations

from typing import Any

from ..config.config_manager import ConfigManager
from ..db.connection import MongoDBConnection
from ..utils.logger import get_logger


class DataExtractor:
    """Minimal extractor for MongoDB collections.

    Provides extract_from_collection compatible with existing usage.
    """

    def __init__(
        self,
        connection: MongoDBConnection | None = None,
        config_manager: ConfigManager | None = None,
    ) -> None:
        self.config_manager = config_manager or ConfigManager()
        self.connection = connection or MongoDBConnection(self.config_manager)
        self.logger = get_logger(__name__)

    def extract_from_collection(
        self,
        collection_name: str,
        filter_query: dict[str, Any] | None = None,
        projection: dict[str, Any] | None = None,
        sort: list[tuple] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> list[dict[str, Any]]:
        self.logger.info(f"Extract from collection: {collection_name}")
        with self.connection:
            db = self.connection.get_database()
            coll = db[collection_name]
            cursor = coll.find(filter_query or {}, projection)
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(int(skip))
            if limit:
                cursor = cursor.limit(int(limit))
            return list(cursor)
