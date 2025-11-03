"""Unit tests for MongoDB connection error handling."""

import pytest
from pymongo.errors import ConnectionFailure, PyMongoError, ServerSelectionTimeoutError
from unittest.mock import MagicMock, patch

from src.core.connector import MongoConnector, ConnectionError


class TestMongoConnectorInitialization:
    """Test MongoConnector initialization."""

    def test_connector_init_minimal(self):
        """Test connector initialization with minimal parameters."""
        connector = MongoConnector(uri="mongodb://localhost:27017")

        assert connector.uri == "mongodb://localhost:27017"
        assert connector.database_name is None
        assert connector.collection_name is None
        assert connector.client is None
        assert connector.db is None
        assert connector.coll is None

    def test_connector_init_with_database(self):
        """Test connector initialization with database."""
        connector = MongoConnector(uri="mongodb://localhost:27017", database="test_db")

        assert connector.uri == "mongodb://localhost:27017"
        assert connector.database_name == "test_db"
        assert connector.database == "test_db"  # backwards compatibility

    def test_connector_init_with_collection(self):
        """Test connector initialization with database and collection."""
        connector = MongoConnector(uri="mongodb://localhost:27017", database="test_db", collection="test_coll")

        assert connector.database_name == "test_db"
        assert connector.collection_name == "test_coll"

    def test_connector_init_with_pool_settings(self):
        """Test connector initialization with custom pool settings."""
        connector = MongoConnector(
            uri="mongodb://localhost:27017",
            max_pool_size=500,
            min_pool_size=20,
            max_idle_time_ms=60000,
        )

        assert connector.max_pool_size == 500
        assert connector.min_pool_size == 20
        assert connector.max_idle_time_ms == 60000

    def test_connector_init_with_auth_database(self):
        """Test connector initialization with authentication database."""
        connector = MongoConnector(
            uri="mongodb://localhost:27017",
            database="test_db",
            auth_database="admin",
        )

        assert connector.auth_database == "admin"


class TestMongoConnectorConnection:
    """Test MongoConnector connection methods."""

    @patch("src.core.connector.MongoClient")
    def test_connect_success(self, mock_mongo_client):
        """Test successful MongoDB connection."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_mongo_client.return_value = mock_client

        connector = MongoConnector(uri="mongodb://localhost:27017", database="test_db")
        result = connector.connect()

        assert result is True
        assert connector.client is not None
        mock_client.admin.command.assert_called_once_with("ping")

    @patch("src.core.connector.MongoClient")
    def test_connect_with_collection(self, mock_mongo_client):
        """Test successful connection with database and collection."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1}
        mock_db = MagicMock()
        mock_coll = MagicMock()
        mock_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_coll
        mock_mongo_client.return_value = mock_client

        connector = MongoConnector(uri="mongodb://localhost:27017", database="test_db", collection="test_coll")
        result = connector.connect()

        assert result is True
        assert connector.client is not None
        assert connector.db is not None
        assert connector.coll is not None

    @patch("src.core.connector.MongoClient")
    def test_connect_failure_connection_refused(self, mock_mongo_client):
        """Test connection failure when MongoDB refuses connection."""
        # Setup mock to raise ConnectionFailure
        mock_mongo_client.side_effect = ConnectionFailure("Connection refused")

        connector = MongoConnector(uri="mongodb://localhost:27017")

        with pytest.raises(ConnectionFailure):
            connector.connect()

        # Verify connection objects are reset
        assert connector.client is None
        assert connector.db is None
        assert connector.coll is None

    @patch("src.core.connector.MongoClient")
    def test_connect_failure_server_timeout(self, mock_mongo_client):
        """Test connection failure when server times out."""
        # Setup mock to raise timeout error
        mock_mongo_client.side_effect = ServerSelectionTimeoutError("Server timeout")

        connector = MongoConnector(uri="mongodb://localhost:27017")

        with pytest.raises(ConnectionFailure):
            connector.connect()

    @patch("src.core.connector.MongoClient")
    def test_connect_failure_ping_fails(self, mock_mongo_client):
        """Test connection failure when ping command fails."""
        # Setup mock where ping fails
        mock_client = MagicMock()
        mock_client.admin.command.side_effect = ConnectionFailure("Ping failed")
        mock_mongo_client.return_value = mock_client

        connector = MongoConnector(uri="mongodb://localhost:27017")

        with pytest.raises(ConnectionFailure):
            connector.connect()

        # Verify connection objects are reset
        assert connector.client is None
        assert connector.db is None
        assert connector.coll is None

    @patch("src.core.connector.MongoClient")
    def test_connect_retry_on_failure(self, mock_mongo_client):
        """Test that connect retries on transient failures."""
        # Setup mock to fail twice then succeed
        mock_client = MagicMock()
        mock_client.admin.command.side_effect = [
            ConnectionFailure("Transient error"),
            ConnectionFailure("Transient error"),
            {"ok": 1},  # Success on third try
        ]
        mock_mongo_client.return_value = mock_client

        connector = MongoConnector(uri="mongodb://localhost:27017")

        # This should succeed after retries
        result = connector.connect()

        assert result is True
        # Verify ping was called 3 times due to retries
        assert mock_client.admin.command.call_count == 3

    @patch("src.core.connector.MongoClient")
    def test_connect_max_retries_exceeded(self, mock_mongo_client):
        """Test that connect fails after max retries."""
        # Setup mock to always fail
        mock_client = MagicMock()
        mock_client.admin.command.side_effect = ConnectionFailure("Persistent error")
        mock_mongo_client.return_value = mock_client

        connector = MongoConnector(uri="mongodb://localhost:27017")

        with pytest.raises(ConnectionFailure):
            connector.connect()

        # Verify retry attempts (should be 3 attempts based on decorator)
        assert mock_client.admin.command.call_count >= 3

    def test_disconnect(self):
        """Test disconnecting from MongoDB."""
        connector = MongoConnector(uri="mongodb://localhost:27017")

        # Mock a connected state
        connector.client = MagicMock()
        connector.db = MagicMock()
        connector.coll = MagicMock()

        connector.disconnect()

        # Verify close was called and objects reset
        connector.client.close.assert_called_once()
        assert connector.client is None
        assert connector.db is None
        assert connector.coll is None

    def test_disconnect_when_not_connected(self):
        """Test disconnecting when not connected (no error)."""
        connector = MongoConnector(uri="mongodb://localhost:27017")

        # Should not raise error
        connector.disconnect()

        assert connector.client is None


class TestMongoConnectorErrorHandling:
    """Test MongoDB connector error handling."""

    @patch("src.core.connector.MongoClient")
    def test_invalid_uri_format(self, mock_mongo_client):
        """Test handling of invalid URI format."""
        mock_mongo_client.side_effect = PyMongoError("Invalid URI")

        connector = MongoConnector(uri="invalid://uri")

        with pytest.raises(ConnectionFailure) as exc_info:
            connector.connect()

        assert "Failed to connect" in str(exc_info.value)

    @patch("src.core.connector.MongoClient")
    def test_authentication_failure(self, mock_mongo_client):
        """Test handling of authentication failures."""
        mock_client = MagicMock()
        mock_client.admin.command.side_effect = PyMongoError("Authentication failed")
        mock_mongo_client.return_value = mock_client

        connector = MongoConnector(uri="mongodb://user:pass@localhost:27017", auth_database="admin")

        with pytest.raises(ConnectionFailure):
            connector.connect()

    @patch("src.core.connector.MongoClient")
    def test_network_error_during_ping(self, mock_mongo_client):
        """Test handling of network errors during ping."""
        mock_client = MagicMock()
        mock_client.admin.command.side_effect = PyMongoError("Network error")
        mock_mongo_client.return_value = mock_client

        connector = MongoConnector(uri="mongodb://localhost:27017")

        with pytest.raises(ConnectionFailure):
            connector.connect()

        # Ensure connection is cleaned up
        assert connector.client is None

    @patch("src.core.connector.MongoClient")
    def test_generic_exception_converted_to_connection_failure(self, mock_mongo_client):
        """Test that generic exceptions are converted to ConnectionFailure."""
        mock_mongo_client.side_effect = Exception("Unexpected error")

        connector = MongoConnector(uri="mongodb://localhost:27017")

        with pytest.raises(ConnectionFailure) as exc_info:
            connector.connect()

        assert "Failed to connect to MongoDB" in str(exc_info.value)


class TestMongoConnectorContextManager:
    """Test MongoDB connector as context manager (if implemented)."""

    @patch("src.core.connector.MongoClient")
    def test_connection_cleanup_on_failure(self, mock_mongo_client):
        """Test that connection is cleaned up properly on failure."""
        mock_client = MagicMock()
        mock_client.admin.command.side_effect = ConnectionFailure("Connection lost")
        mock_mongo_client.return_value = mock_client

        connector = MongoConnector(uri="mongodb://localhost:27017", database="test_db")

        try:
            connector.connect()
        except ConnectionFailure:
            pass

        # Verify cleanup happened
        assert connector.client is None
        assert connector.db is None
        assert connector.coll is None


class TestConnectionErrorClass:
    """Test custom ConnectionError exception class."""

    def test_connection_error_instantiation(self):
        """Test creating ConnectionError exception."""
        error = ConnectionError("Test connection error")

        assert str(error) == "Test connection error"
        assert isinstance(error, Exception)

    def test_connection_error_raise(self):
        """Test raising ConnectionError exception."""
        with pytest.raises(ConnectionError) as exc_info:
            raise ConnectionError("Database unavailable")

        assert "Database unavailable" in str(exc_info.value)
