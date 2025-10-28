"""Tests for collection stats collector."""

from unittest.mock import MagicMock, patch

import pytest

from db_collection_stats.collector import (
    CollectionStats,
    gather_all_collections_stats,
    gather_collection_stats,
)


class TestCollectionStats:
    """Tests for CollectionStats dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        stats = CollectionStats(
            collection_name="users",
            document_count=1000,
            collection_size_bytes=500000,
            avg_document_size_bytes=500.5,
            storage_size_bytes=600000,
            num_indexes=3,
            total_index_size_bytes=50000,
        )

        result = stats.to_dict()

        assert result["collection_name"] == "users"
        assert result["document_count"] == 1000
        assert result["collection_size_bytes"] == 500000
        assert result["avg_document_size_bytes"] == 500.5
        assert result["storage_size_bytes"] == 600000
        assert result["num_indexes"] == 3
        assert result["total_index_size_bytes"] == 50000

    def test_to_dict_rounds_avg_size(self):
        """Test that average document size is rounded to 2 decimals."""
        stats = CollectionStats(
            collection_name="test",
            document_count=100,
            collection_size_bytes=1000,
            avg_document_size_bytes=123.456789,
            storage_size_bytes=2000,
            num_indexes=1,
            total_index_size_bytes=100,
        )

        result = stats.to_dict()

        assert result["avg_document_size_bytes"] == 123.46


class TestGatherCollectionStats:
    """Tests for gather_collection_stats function."""

    def test_gather_collection_stats_success(self):
        """Test successful stats gathering."""
        # Mock database
        mock_db = MagicMock()
        mock_db.command.return_value = {
            "count": 1500,
            "size": 750000,
            "avgObjSize": 500.0,
            "storageSize": 800000,
            "nindexes": 4,
            "totalIndexSize": 60000,
        }

        result = gather_collection_stats(mock_db, "test_collection")

        assert result.collection_name == "test_collection"
        assert result.document_count == 1500
        assert result.collection_size_bytes == 750000
        assert result.avg_document_size_bytes == 500.0
        assert result.storage_size_bytes == 800000
        assert result.num_indexes == 4
        assert result.total_index_size_bytes == 60000

        mock_db.command.assert_called_once_with("collStats", "test_collection")

    def test_gather_collection_stats_missing_fields(self):
        """Test gathering stats when some fields are missing."""
        mock_db = MagicMock()
        mock_db.command.return_value = {
            "count": 100,
            # Missing other fields
        }

        result = gather_collection_stats(mock_db, "sparse_collection")

        assert result.collection_name == "sparse_collection"
        assert result.document_count == 100
        assert result.collection_size_bytes == 0
        assert result.avg_document_size_bytes == 0.0
        assert result.storage_size_bytes == 0
        assert result.num_indexes == 0
        assert result.total_index_size_bytes == 0

    def test_gather_collection_stats_empty_collection(self):
        """Test gathering stats for empty collection."""
        mock_db = MagicMock()
        mock_db.command.return_value = {
            "count": 0,
            "size": 0,
            "avgObjSize": 0,
            "storageSize": 0,
            "nindexes": 1,  # Default _id index
            "totalIndexSize": 0,
        }

        result = gather_collection_stats(mock_db, "empty_collection")

        assert result.document_count == 0
        assert result.collection_size_bytes == 0
        assert result.num_indexes == 1


class TestGatherAllCollectionsStats:
    """Tests for gather_all_collections_stats function."""

    def test_gather_all_collections_stats_success(self):
        """Test gathering stats for all collections."""
        # Mock client and database
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        mock_db.list_collection_names.return_value = ["users", "orders", "products"]

        mock_db.command.side_effect = [
            {
                "count": 100,
                "size": 10000,
                "avgObjSize": 100.0,
                "storageSize": 12000,
                "nindexes": 2,
                "totalIndexSize": 1000,
            },
            {
                "count": 50,
                "size": 5000,
                "avgObjSize": 100.0,
                "storageSize": 6000,
                "nindexes": 1,
                "totalIndexSize": 500,
            },
            {
                "count": 200,
                "size": 20000,
                "avgObjSize": 100.0,
                "storageSize": 24000,
                "nindexes": 3,
                "totalIndexSize": 2000,
            },
        ]

        result = gather_all_collections_stats(mock_client, "test_db")

        assert len(result) == 3
        assert result[0].collection_name == "orders"  # Sorted alphabetically
        assert result[1].collection_name == "products"
        assert result[2].collection_name == "users"

    def test_gather_all_collections_excludes_system(self):
        """Test that system collections are excluded by default."""
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        mock_db.list_collection_names.return_value = [
            "users",
            "system.indexes",
            "system.profile",
            "orders",
        ]

        mock_db.command.side_effect = [
            {
                "count": 100,
                "size": 10000,
                "avgObjSize": 100.0,
                "storageSize": 12000,
                "nindexes": 2,
                "totalIndexSize": 1000,
            },
            {
                "count": 50,
                "size": 5000,
                "avgObjSize": 100.0,
                "storageSize": 6000,
                "nindexes": 1,
                "totalIndexSize": 500,
            },
        ]

        result = gather_all_collections_stats(mock_client, "test_db", exclude_system=True)

        assert len(result) == 2
        assert all("system" not in s.collection_name for s in result)

    def test_gather_all_collections_includes_system_when_requested(self):
        """Test that system collections are included when exclude_system=False."""
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        mock_db.list_collection_names.return_value = ["users", "system.indexes"]

        mock_db.command.side_effect = [
            {
                "count": 10,
                "size": 1000,
                "avgObjSize": 100.0,
                "storageSize": 1200,
                "nindexes": 1,
                "totalIndexSize": 100,
            },
            {
                "count": 100,
                "size": 10000,
                "avgObjSize": 100.0,
                "storageSize": 12000,
                "nindexes": 2,
                "totalIndexSize": 1000,
            },
        ]

        result = gather_all_collections_stats(mock_client, "test_db", exclude_system=False)

        assert len(result) == 2
        assert any("system" in s.collection_name for s in result)

    def test_gather_all_collections_handles_error(self, capsys):
        """Test that errors for individual collections are handled gracefully."""
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        mock_db.list_collection_names.return_value = ["good_collection", "bad_collection"]

        def command_side_effect(cmd, coll_name):
            if coll_name == "bad_collection":
                raise Exception("Permission denied")
            return {
                "count": 100,
                "size": 10000,
                "avgObjSize": 100.0,
                "storageSize": 12000,
                "nindexes": 2,
                "totalIndexSize": 1000,
            }

        mock_db.command.side_effect = command_side_effect

        result = gather_all_collections_stats(mock_client, "test_db")

        # Should have stats for good_collection only
        assert len(result) == 1
        assert result[0].collection_name == "good_collection"

        # Should print warning
        captured = capsys.readouterr()
        assert "Warning: Failed to gather stats for bad_collection" in captured.out

    def test_gather_all_collections_empty_database(self):
        """Test gathering stats when database has no collections."""
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_client.__getitem__.return_value = mock_db

        mock_db.list_collection_names.return_value = []

        result = gather_all_collections_stats(mock_client, "empty_db")

        assert len(result) == 0
