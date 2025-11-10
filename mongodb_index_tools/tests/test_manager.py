"""Tests for manager module."""

from unittest.mock import MagicMock

from pymongo.errors import OperationFailure

from mongodb_index_tools.manager import create_index, drop_index, list_indexes


def test_create_index_success():
    """Test creating an index successfully."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    # Mock list_indexes to return no existing indexes
    mock_collection.list_indexes.return_value = []

    # Mock create_index to return index name
    mock_collection.create_index.return_value = "email_1"

    result = create_index(
        db=mock_db,
        collection_name="users",
        keys={"email": 1},
    )

    assert result["success"] is True
    assert result["index_name"] == "email_1"
    assert result["keys"] == {"email": 1}
    mock_collection.create_index.assert_called_once()


def test_create_index_compound():
    """Test creating a compound index."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_collection.list_indexes.return_value = []
    mock_collection.create_index.return_value = "status_1_created_at_-1"

    result = create_index(
        db=mock_db,
        collection_name="users",
        keys={"status": 1, "created_at": -1},
    )

    assert result["success"] is True
    assert result["index_name"] == "status_1_created_at_-1"


def test_create_index_with_options():
    """Test creating an index with various options."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_collection.list_indexes.return_value = []
    mock_collection.create_index.return_value = "idx_unique_email"

    result = create_index(
        db=mock_db,
        collection_name="users",
        keys={"email": 1},
        name="idx_unique_email",
        unique=True,
        sparse=True,
        background=False,
    )

    assert result["success"] is True
    assert result["index_name"] == "idx_unique_email"
    assert result["options"]["unique"] is True
    assert result["options"]["sparse"] is True
    assert result["options"]["background"] is False


def test_create_index_ttl():
    """Test creating a TTL index."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_collection.list_indexes.return_value = []
    mock_collection.create_index.return_value = "created_at_1"

    result = create_index(
        db=mock_db,
        collection_name="sessions",
        keys={"created_at": 1},
        expire_after_seconds=3600,
    )

    assert result["success"] is True
    assert result["options"]["expireAfterSeconds"] == 3600


def test_create_index_already_exists():
    """Test creating an index that already exists."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    # Mock existing index
    mock_collection.list_indexes.return_value = [{"name": "email_1", "key": {"email": 1}}]

    result = create_index(
        db=mock_db,
        collection_name="users",
        keys={"email": 1},
    )

    assert result["success"] is False
    assert "already exists" in result["error"]


def test_create_index_no_keys():
    """Test creating an index with no keys."""
    mock_db = MagicMock()

    result = create_index(
        db=mock_db,
        collection_name="users",
        keys={},
    )

    assert result["success"] is False
    assert "At least one key field is required" in result["error"]


def test_create_index_dry_run():
    """Test dry run mode for create index."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_collection.list_indexes.return_value = []

    result = create_index(
        db=mock_db,
        collection_name="users",
        keys={"email": 1},
        dry_run=True,
    )

    assert result["success"] is True
    assert result["dry_run"] is True
    assert "would be created" in result["message"].lower()
    # Verify create_index was not called
    mock_collection.create_index.assert_not_called()


def test_create_index_operation_failure():
    """Test handling MongoDB operation failure."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_collection.list_indexes.return_value = []
    mock_collection.create_index.side_effect = OperationFailure("Index build failed")

    result = create_index(
        db=mock_db,
        collection_name="users",
        keys={"email": 1},
    )

    assert result["success"] is False
    assert "Failed to create index" in result["error"]


def test_drop_index_success():
    """Test dropping an index successfully."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    # Mock existing index
    mock_collection.list_indexes.return_value = [
        {"name": "email_1", "key": {"email": 1}},
        {"name": "status_1", "key": {"status": 1}},
    ]

    result = drop_index(
        db=mock_db,
        collection_name="users",
        index_name="email_1",
    )

    assert result["success"] is True
    assert result["index_name"] == "email_1"
    mock_collection.drop_index.assert_called_once_with("email_1")


def test_drop_index_not_exists():
    """Test dropping an index that doesn't exist."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_collection.list_indexes.return_value = [{"name": "_id_", "key": {"_id": 1}}]

    result = drop_index(
        db=mock_db,
        collection_name="users",
        index_name="email_1",
    )

    assert result["success"] is False
    assert "does not exist" in result["error"]


def test_drop_index_prevent_id():
    """Test preventing drop of _id index."""
    mock_db = MagicMock()

    result = drop_index(
        db=mock_db,
        collection_name="users",
        index_name="_id_",
    )

    assert result["success"] is False
    assert "Cannot drop the _id index" in result["error"]


def test_drop_index_dry_run():
    """Test dry run mode for drop index."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_collection.list_indexes.return_value = [{"name": "email_1", "key": {"email": 1}}]

    result = drop_index(
        db=mock_db,
        collection_name="users",
        index_name="email_1",
        dry_run=True,
    )

    assert result["success"] is True
    assert result["dry_run"] is True
    assert "would be dropped" in result["message"].lower()
    # Verify drop_index was not called
    mock_collection.drop_index.assert_not_called()


def test_drop_index_operation_failure():
    """Test handling MongoDB operation failure when dropping."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_collection.list_indexes.return_value = [{"name": "email_1", "key": {"email": 1}}]
    mock_collection.drop_index.side_effect = OperationFailure("Drop failed")

    result = drop_index(
        db=mock_db,
        collection_name="users",
        index_name="email_1",
    )

    assert result["success"] is False
    assert "Failed to drop index" in result["error"]


def test_list_indexes_success():
    """Test listing indexes successfully."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_indexes = [
        {"name": "_id_", "key": {"_id": 1}},
        {"name": "email_1", "key": {"email": 1}},
        {"name": "status_1_created_at_-1", "key": {"status": 1, "created_at": -1}},
    ]
    mock_collection.list_indexes.return_value = mock_indexes

    result = list_indexes(
        db=mock_db,
        collection_name="users",
    )

    assert result["success"] is True
    assert result["collection_name"] == "users"
    assert result["count"] == 3
    assert len(result["indexes"]) == 3


def test_list_indexes_failure():
    """Test handling failure when listing indexes."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_collection.list_indexes.side_effect = Exception("Connection error")

    result = list_indexes(
        db=mock_db,
        collection_name="users",
    )

    assert result["success"] is False
    assert "Failed to list indexes" in result["error"]
