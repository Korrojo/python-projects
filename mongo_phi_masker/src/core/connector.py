"""
MongoDB connector module for PHI masking pipeline.

This module provides connection management for MongoDB databases.
"""

import logging
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, PyMongoError
from pymongo.operations import InsertOne, ReplaceOne


# Define a simple retry decorator instead of importing it
def retry(max_attempts=3, delay=2, backoff_factor=2.0, exceptions=(ConnectionFailure,)):
    """Simple retry decorator to avoid circular imports."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    import time

                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            return func(*args, **kwargs)  # final attempt

        return wrapper

    return decorator


# Define a custom exception class
class ConnectionError(Exception):
    """Exception raised for MongoDB connection errors."""

    pass


class MongoConnector:
    """Manages connections to MongoDB instances."""

    def __init__(
        self,
        uri: str,
        database: str | None = None,
        collection: str | None = None,
        max_pool_size: int = 300,
        min_pool_size: int = 10,
        max_idle_time_ms: int = 30000,
        auth_database: str | None = None,
    ):
        """Initialize the MongoDB connector.

        Args:
            uri: MongoDB connection URI
            database: Optional database name
            collection: Optional collection name
            max_pool_size: Maximum connection pool size
            min_pool_size: Minimum connection pool size
            max_idle_time_ms: Maximum idle time for connections
            auth_database: Authentication database
        """
        self.logger = logging.getLogger(__name__)
        self.uri = uri
        self.database_name = database
        self.collection_name = collection

        # For backwards compatibility
        self.database = database
        self.collection = collection

        # Connection pooling settings
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        self.max_idle_time_ms = max_idle_time_ms
        self.auth_database = auth_database

        # Initialize client, db, and collection to None - DO NOT CONNECT HERE
        self.client: MongoClient | None = None
        self.db: Database | None = None
        self.coll: Collection | None = None  # For backward compatibility

    @retry(max_attempts=3, delay=2)
    def connect(self) -> bool:
        """Establish connection to MongoDB.

        Returns:
            True if connection successful

        Raises:
            ConnectionFailure: If connection fails
        """
        try:
            # Always create a new client here to ensure tests can mock it
            self.client = MongoClient(
                self.uri,
                maxPoolSize=self.max_pool_size,
                minPoolSize=self.min_pool_size,
                maxIdleTimeMS=self.max_idle_time_ms,
                connect=True,
                appname="MongoPHIMasker",
                retryWrites=True,
                w=1,
            )

            # Test connection by running ping command
            self.client.admin.command("ping")

            # Set up database and collection if specified
            if self.database_name:
                self.db = self.client[self.database_name]

                if self.auth_database:
                    self.db.authenticate(mechanism="SCRAM-SHA-1", source=self.auth_database)

                if self.collection_name:
                    self.coll = self.client[self.database_name][self.collection_name]

            return True

        except Exception as e:
            # Reset connection objects
            self.client = None
            self.db = None
            self.coll = None

            # Make sure we're raising ConnectionFailure for tests
            if isinstance(e, ConnectionFailure):
                raise
            raise ConnectionFailure(f"Failed to connect to MongoDB: {str(e)}")

    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self.coll = None
            self.logger.info("Disconnected from MongoDB")

    def is_connected(self) -> bool:
        """Check if connected to MongoDB."""
        if not self.client:
            return False

        try:
            # Try to ping the server
            self.client.admin.command("ping")
            return True
        except Exception:
            return False

    def ensure_connected(self) -> None:
        """Ensure connection to MongoDB exists."""
        if not self.is_connected():
            self.connect()

    def get_database(self, database_name: str = None) -> Database | None:
        """Get a MongoDB database.

        Args:
            database_name: Optional database name override

        Returns:
            MongoDB database object

        Raises:
            ConnectionError: If not connected
        """
        self.ensure_connected()

        # Use specified database or the one from initialization
        db_name = database_name or self.database_name

        if not db_name:
            raise ValueError("No database name specified")

        return self.client[db_name]

    def get_collection(self, collection_name: str = None, database_name: str = None) -> Collection | None:
        """Get a MongoDB collection.

        Args:
            collection_name: Optional collection name override
            database_name: Optional database name override

        Returns:
            MongoDB collection object

        Raises:
            ConnectionError: If not connected
        """
        self.ensure_connected()

        # Use specified database or get from initialization
        db = self.get_database(database_name)

        # Use specified collection or the one from initialization
        coll_name = collection_name or self.collection_name

        if not coll_name:
            raise ValueError("No collection name specified")

        return db[coll_name]

    def collection_exists(self, collection_name: str = None, database_name: str = None) -> bool:
        """Check if a collection exists.

        Args:
            collection_name: Optional collection name override
            database_name: Optional database name override

        Returns:
            True if collection exists, False otherwise
        """
        # Use provided names or defaults
        db_name = database_name or self.database_name
        coll_name = collection_name or self.collection_name

        if not db_name or not coll_name:
            return False

        # If we're not connected, don't try to connect
        if not self.client:
            return False

        try:
            # Get database
            db = self.client[db_name]

            # Get collection names and check
            collection_names = db.list_collection_names()
            return coll_name in collection_names
        except:
            return False

    def list_collections(self, database_name: str = None) -> list[str]:
        """List collections in a database.

        Args:
            database_name: Optional database name override

        Returns:
            List of collection names
        """
        db = self.get_database(database_name)
        return db.list_collection_names()

    @retry(max_attempts=3, delay=1, backoff_factor=2.0)
    def find(
        self,
        query: dict[str, Any] = None,
        projection: dict[str, Any] = None,
        sort: list[tuple[str, int]] = None,
        limit: int = 0,
        skip: int = 0,
        batch_size: int = None,
        collection_name: str = None,
        database_name: str = None,
    ) -> Cursor:
        """Find documents in a collection.

        Args:
            query: MongoDB query
            projection: Fields to include/exclude
            sort: Sort specification
            limit: Maximum number of documents
            skip: Number of documents to skip
            batch_size: Cursor batch size
            collection_name: Optional collection name override
            database_name: Optional database name override

        Returns:
            MongoDB cursor for the query
        """
        try:
            collection = self.get_collection(collection_name, database_name)
            cursor = collection.find(
                filter=query or {},
                projection=projection,
                sort=sort,
                skip=skip,
                limit=limit,
            )

            if batch_size:
                cursor = cursor.batch_size(batch_size)

            return cursor
        except PyMongoError as e:
            self.logger.error(f"Error executing find query: {str(e)}")
            raise ConnectionError(f"Error executing find query: {str(e)}")

    # Alias for compatibility
    find_documents = find

    def count_documents(
        self,
        query: dict[str, Any] = None,
        collection_name: str = None,
        database_name: str = None,
    ) -> int:
        """Count documents in a collection.

        Args:
            query: MongoDB query
            collection_name: Optional collection name override
            database_name: Optional database name override

        Returns:
            Document count
        """
        try:
            collection = self.get_collection(collection_name, database_name)
            return collection.count_documents(query or {})
        except PyMongoError as e:
            self.logger.error(f"Error counting documents: {str(e)}")
            raise ConnectionError(f"Error counting documents: {str(e)}")

    def estimated_document_count(
        self,
        collection_name: str | None = None,
        database_name: str | None = None,
    ) -> int:
        """Get an estimated count of documents in a collection.

        This is faster than count_documents() but less accurate as it uses
        collection metadata rather than scanning all documents.

        Args:
            collection_name: Optional collection name override
            database_name: Optional database name override

        Returns:
            Estimated document count
        """
        try:
            collection = self.get_collection(collection_name, database_name)
            if collection is None:
                raise ConnectionError("Collection not initialized")
            return collection.estimated_document_count()
        except PyMongoError as e:
            self.logger.error(f"Error getting estimated document count: {str(e)}")
            raise ConnectionError(f"Error getting estimated document count: {str(e)}")

    @retry(max_attempts=3, delay=1, backoff_factor=2.0)
    def insert_document(
        self,
        document: dict[str, Any],
        collection_name: str = None,
        database_name: str = None,
    ) -> Any:
        """Insert a document into a collection.

        Args:
            document: Document to insert
            collection_name: Optional collection name override
            database_name: Optional database name override

        Returns:
            Inserted document ID
        """
        try:
            collection = self.get_collection(collection_name, database_name)
            result = collection.insert_one(document)
            return result.inserted_id
        except PyMongoError as e:
            self.logger.error(f"Error inserting document: {str(e)}")
            raise ConnectionError(f"Error inserting document: {str(e)}")

    # Alias for compatibility
    insert_one = insert_document

    @retry(max_attempts=3, delay=1, backoff_factor=2.0)
    def update_document(
        self,
        query: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
        collection_name: str = None,
        database_name: str = None,
    ) -> int:
        """Update a document in a collection.

        Args:
            query: Query to find document
            update: Update to apply
            upsert: Whether to insert if document doesn't exist
            collection_name: Optional collection name override
            database_name: Optional database name override

        Returns:
            Number of documents modified
        """
        try:
            collection = self.get_collection(collection_name, database_name)
            result = collection.update_one(query, update, upsert=upsert)
            return result.modified_count
        except PyMongoError as e:
            self.logger.error(f"Error updating document: {str(e)}")
            raise ConnectionError(f"Error updating document: {str(e)}")

    # Alias for compatibility
    update_one = update_document

    @retry(max_attempts=3, delay=1, backoff_factor=2.0)
    def replace_one(
        self,
        query: dict[str, Any],
        document: dict[str, Any],
        upsert: bool = False,
        collection_name: str = None,
        database_name: str = None,
    ) -> int:
        """Replace a document in a collection.

        Args:
            query: Query to find document
            document: Document to replace with
            upsert: Whether to insert if document doesn't exist
            collection_name: Optional collection name override
            database_name: Optional database name override

        Returns:
            Number of documents modified
        """
        try:
            collection = self.get_collection(collection_name, database_name)
            result = collection.replace_one(query, document, upsert=upsert)
            return result.modified_count
        except PyMongoError as e:
            self.logger.error(f"Error replacing document: {str(e)}")
            raise ConnectionError(f"Error replacing document: {str(e)}")

    @retry(max_attempts=3, delay=1, backoff_factor=2.0)
    def bulk_insert(
        self,
        documents: list[dict[str, Any]],
        collection_name: str = None,
        database_name: str = None,
        ordered: bool = True,
    ) -> int:
        """Insert multiple documents in bulk.

        Args:
            documents: List of documents to insert
            collection_name: Optional collection name override
            database_name: Optional database name override
            ordered: Whether to perform an ordered operation

        Returns:
            Number of documents inserted
        """
        if not documents:
            return 0

        try:
            collection = self.get_collection(collection_name, database_name)
            result = collection.insert_many(documents, ordered=ordered)
            return len(result.inserted_ids)
        except PyMongoError as e:
            self.logger.error(f"Error in bulk insert: {str(e)}")
            raise ConnectionError(f"Error in bulk insert: {str(e)}")

    @retry(max_attempts=3, delay=1, backoff_factor=2.0)
    def bulk_update(
        self,
        documents: list[dict[str, Any]],
        collection_name: str = None,
        database_name: str = None,
        ordered: bool = True,
    ) -> int:
        """Update multiple documents in bulk.

        Args:
            documents: List of documents to update
            collection_name: Optional collection name override
            database_name: Optional database name override
            ordered: Whether to perform an ordered operation

        Returns:
            Number of documents updated
        """
        if not documents:
            return 0

        try:
            collection = self.get_collection(collection_name, database_name)

            # Prepare bulk operations
            operations = []
            for doc in documents:
                # Ensure document has an _id field
                if "_id" not in doc:
                    # If no _id provided, let MongoDB generate one
                    operations.append(InsertOne(doc))
                else:
                    # If _id exists, use it as filter and update with upsert
                    operations.append(ReplaceOne(filter={"_id": doc["_id"]}, replacement=doc, upsert=True))

            # Execute bulk write operation
            result = collection.bulk_write(operations, ordered=ordered)

            # Return total number of documents affected
            return result.upserted_count + result.modified_count

        except PyMongoError as e:
            self.logger.error(f"Error in bulk update: {str(e)}")
            raise ConnectionError(f"Error in bulk update: {str(e)}")

    def find_one(
        self,
        query: dict[str, Any] = None,
        projection: dict[str, Any] = None,
        collection_name: str = None,
        database_name: str = None,
    ) -> dict[str, Any] | None:
        """Find a single document in a collection.

        Args:
            query: MongoDB query
            projection: Fields to include/exclude
            collection_name: Optional collection name override
            database_name: Optional database name override

        Returns:
            Document or None if not found
        """
        try:
            collection = self.get_collection(collection_name, database_name)
            return collection.find_one(query or {}, projection)
        except PyMongoError as e:
            self.logger.error(f"Error finding document: {str(e)}")
            raise ConnectionError(f"Error finding document: {str(e)}")

    def _sanitize_uri(self, uri: str) -> str:
        """Sanitize URI for logging by removing credentials.

        Args:
            uri: MongoDB URI

        Returns:
            Sanitized URI
        """
        import re

        # Replace username:password with username:***
        sanitized = re.sub(r"([^/]+:[^/]+@)", "***:***@", uri)
        return sanitized

    # Note: update_document method is defined earlier in the class with full functionality
