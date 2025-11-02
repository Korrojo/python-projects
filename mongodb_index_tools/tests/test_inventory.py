"""Tests for inventory module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mongodb_index_tools.inventory import (
    export_inventory_to_csv,
    gather_index_inventory,
    print_inventory,
)


def test_gather_index_inventory():
    """Test gathering index inventory from collections."""
    # Mock database and collection
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    # Mock index data
    mock_indexes = [
        {
            "name": "_id_",
            "key": {"_id": 1},
            "unique": False,
            "sparse": False,
        },
        {
            "name": "idx_name",
            "key": {"name": 1, "email": -1},
            "unique": True,
            "sparse": False,
        },
    ]
    mock_collection.list_indexes.return_value = mock_indexes

    # Test
    collections = ["test_collection"]
    result = gather_index_inventory(mock_db, collections)

    # Assertions
    assert len(result) == 2
    assert result[0]["collection_name"] == "test_collection"
    assert result[0]["index_name"] == "_id_"
    assert result[0]["index_keys"] == "_id: 1"
    assert result[0]["unique"] == "No"

    assert result[1]["index_name"] == "idx_name"
    assert result[1]["index_keys"] == "name: 1, email: -1"
    assert result[1]["unique"] == "Yes"


def test_gather_index_inventory_with_ttl():
    """Test gathering index inventory with TTL index."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_indexes = [
        {
            "name": "ttl_index",
            "key": {"createdAt": 1},
            "unique": False,
            "sparse": False,
            "expireAfterSeconds": 3600,
        },
    ]
    mock_collection.list_indexes.return_value = mock_indexes

    collections = ["test_collection"]
    result = gather_index_inventory(mock_db, collections)

    assert len(result) == 1
    assert "TTL:3600s" in result[0]["attributes"]


def test_print_inventory(capsys):
    """Test printing inventory to console."""
    inventory_data = [
        {
            "collection_name": "users",
            "index_name": "_id_",
            "index_keys": "_id: 1",
            "unique": "No",
            "sparse": "No",
            "attributes": "",
        },
        {
            "collection_name": "users",
            "index_name": "idx_email",
            "index_keys": "email: 1",
            "unique": "Yes",
            "sparse": "No",
            "attributes": "unique",
        },
    ]

    print_inventory(inventory_data, "test_db")
    captured = capsys.readouterr()

    assert "Index Inventory for Database: test_db" in captured.out
    assert "Collection: users" in captured.out
    assert "_id_" in captured.out
    assert "idx_email" in captured.out
    assert "Total Collections: 1" in captured.out
    assert "Total Indexes: 2" in captured.out


def test_export_inventory_to_csv(tmp_path):
    """Test exporting inventory to CSV file."""
    inventory_data = [
        {
            "collection_name": "users",
            "index_name": "_id_",
            "index_keys": "_id: 1",
            "unique": "No",
            "sparse": "No",
            "attributes": "",
        },
    ]

    output_dir = tmp_path / "output"
    csv_path = export_inventory_to_csv(inventory_data, output_dir, "test_db")

    # Assertions
    assert csv_path.exists()
    assert csv_path.name.startswith("index_inventory_test_db_")
    assert csv_path.suffix == ".csv"

    # Read and verify content
    with open(csv_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Collection Name" in content
        assert "Index Name" in content
        assert "users" in content
        assert "_id_" in content
