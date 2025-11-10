"""Tests for utilization module."""

from datetime import datetime
from unittest.mock import MagicMock


from mongodb_index_tools.utilization import (
    export_utilization_to_csv,
    gather_index_utilization,
    print_utilization,
)


def test_gather_index_utilization():
    """Test gathering index utilization statistics."""
    # Mock database and collection
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    # Mock collStats response
    mock_db.command.return_value = {
        "indexSizes": {
            "_id_": 1048576,  # 1 MB
            "idx_email": 2097152,  # 2 MB
        }
    }

    # Mock aggregation results
    mock_utilization_data = [
        {
            "_id": "idx_email",
            "ops": 1500,
            "since": datetime(2024, 1, 1),
            "keys": ["email"],
        },
        {
            "_id": "_id_",
            "ops": 500,
            "since": datetime(2024, 1, 1),
            "keys": ["_id"],
        },
        {
            "_id": "idx_unused",
            "ops": 0,
            "since": datetime(2024, 1, 1),
            "keys": ["field1", "field2"],
        },
    ]
    mock_collection.aggregate.return_value = mock_utilization_data

    # Test
    utilization_data, index_sizes = gather_index_utilization(mock_db, "test_collection")

    # Assertions
    assert len(utilization_data) == 3
    assert index_sizes["_id_"] == 1048576
    assert index_sizes["idx_email"] == 2097152

    # Verify aggregation was called
    mock_collection.aggregate.assert_called_once()
    pipeline = mock_collection.aggregate.call_args[0][0]
    assert pipeline[0] == {"$indexStats": {}}


def test_gather_index_utilization_no_stats():
    """Test gathering utilization when collStats fails."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    # Mock collStats failure
    mock_db.command.side_effect = Exception("Permission denied")

    # Mock aggregation results
    mock_collection.aggregate.return_value = [
        {
            "_id": "_id_",
            "ops": 100,
            "since": datetime(2024, 1, 1),
            "keys": ["_id"],
        }
    ]

    # Test - should not raise, just warn
    utilization_data, index_sizes = gather_index_utilization(mock_db, "test_collection")

    assert len(utilization_data) == 1
    assert index_sizes == {}  # Empty because collStats failed


def test_print_utilization(capsys):
    """Test printing utilization to console."""
    utilization_data = [
        {
            "_id": "idx_email",
            "ops": 1500,
            "since": datetime(2024, 1, 1),
            "keys": ["email"],
        },
        {
            "_id": "idx_unused",
            "ops": 0,
            "since": datetime(2024, 1, 1),
            "keys": ["field1", "field2"],
        },
    ]

    index_sizes = {
        "idx_email": 2097152,  # 2 MB
        "idx_unused": 1048576,  # 1 MB
    }

    print_utilization("test_collection", utilization_data, index_sizes)
    captured = capsys.readouterr()

    assert "Index Utilization for Collection: test_collection" in captured.out
    assert "idx_email" in captured.out
    assert "1,500" in captured.out  # Formatted with comma
    assert "idx_unused" in captured.out
    assert "⚠️  UNUSED" in captured.out
    assert "Total Indexes: 2" in captured.out
    assert "Unused Indexes: 1" in captured.out


def test_print_utilization_empty(capsys):
    """Test printing utilization with no data."""
    print_utilization("empty_collection", [], {})
    captured = capsys.readouterr()

    assert "Index Utilization for Collection: empty_collection" in captured.out
    assert "No index statistics available" in captured.out


def test_export_utilization_to_csv(tmp_path):
    """Test exporting utilization to CSV file."""
    utilization_data = [
        {
            "_id": "idx_email",
            "ops": 1500,
            "since": datetime(2024, 1, 1),
            "keys": ["email"],
        },
        {
            "_id": "idx_compound",
            "ops": 500,
            "since": datetime(2024, 1, 15),
            "keys": ["field1", "field2", "field3"],
        },
    ]

    index_sizes = {
        "idx_email": 2097152,
        "idx_compound": 3145728,
    }

    output_dir = tmp_path / "output"
    csv_path = export_utilization_to_csv("test_collection", utilization_data, index_sizes, output_dir, "test_db")

    # Assertions
    assert csv_path.exists()
    assert csv_path.name.startswith("index_utilization_test_db_test_collection_")
    assert csv_path.suffix == ".csv"

    # Read and verify content
    with open(csv_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

        # Check headers
        assert "No,Index Name,Operations,Size (MB),Since,Key1,Key2,Key3" in lines[0]

        # Check data rows
        content = "".join(lines)
        assert "idx_email" in content
        assert "1500" in content
        assert "2024-01-01" in content
        assert "field1" in content
        assert "field2" in content
        assert "field3" in content
