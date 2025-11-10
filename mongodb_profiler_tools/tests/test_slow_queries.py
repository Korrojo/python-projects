"""Tests for slow_queries module."""

from datetime import datetime
from unittest.mock import MagicMock

from mongodb_profiler_tools.slow_queries import analyze_slow_queries, export_slow_queries_to_csv, print_slow_queries


def test_analyze_slow_queries_basic():
    """Test analyzing slow queries with basic filtering."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    # Mock profile data
    mock_profile_data = [
        {
            "ts": datetime(2024, 1, 15, 10, 30),
            "op": "query",
            "ns": "testdb.users",
            "millis": 250,
            "client": "192.168.1.100",
            "user": "testuser",
            "planSummary": "COLLSCAN",
            "docsExamined": 1000,
            "keysExamined": 0,
            "nreturned": 10,
            "command": {"find": "users"},
        },
        {
            "ts": datetime(2024, 1, 15, 10, 31),
            "op": "update",
            "ns": "testdb.orders",
            "millis": 150,
            "client": "192.168.1.101",
            "planSummary": "IXSCAN",
            "docsExamined": 100,
            "keysExamined": 100,
            "nReturned": 50,
            "command": {"update": "orders"},
        },
    ]

    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.__iter__.return_value = iter(mock_profile_data)

    mock_collection.find.return_value = mock_cursor

    result = analyze_slow_queries(
        db=mock_db,
        threshold_ms=100,
        limit=100,
    )

    assert len(result) == 2
    assert result[0]["operation"] == "query"
    assert result[0]["millis"] == 250
    assert result[1]["operation"] == "update"
    assert result[1]["millis"] == 150


def test_analyze_slow_queries_with_filters():
    """Test analyzing slow queries with collection and operation filters."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.__iter__.return_value = iter([])

    mock_collection.find.return_value = mock_cursor

    analyze_slow_queries(
        db=mock_db,
        threshold_ms=100,
        collection_filter="testdb.users",
        operation_filter="query",
        limit=50,
    )

    # Verify query was built correctly
    call_args = mock_collection.find.call_args
    query = call_args[0][0]

    assert query["millis"] == {"$gte": 100}
    assert query["ns"] == "testdb.users"
    assert query["op"] == "query"


def test_analyze_slow_queries_empty():
    """Test analyzing when no slow queries found."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.__iter__.return_value = iter([])

    mock_collection.find.return_value = mock_cursor

    result = analyze_slow_queries(db=mock_db, threshold_ms=1000)

    assert result == []


def test_analyze_slow_queries_exception():
    """Test handling exception when system.profile doesn't exist."""
    mock_db = MagicMock()
    mock_db.__getitem__.side_effect = Exception("Collection not found")

    result = analyze_slow_queries(db=mock_db)

    assert result == []


def test_print_slow_queries(capsys, sample_slow_ops):
    """Test printing slow queries to console."""
    print_slow_queries(sample_slow_ops, threshold=100)

    captured = capsys.readouterr()
    assert "Slow Queries Analysis" in captured.out
    assert ">= 100ms" in captured.out
    assert "query" in captured.out.lower()
    assert "update" in captured.out.lower()
    assert "250ms" in captured.out
    assert "150ms" in captured.out


def test_print_slow_queries_empty(capsys):
    """Test printing when no slow queries."""
    print_slow_queries([], threshold=100)

    captured = capsys.readouterr()
    assert "No slow queries found" in captured.out
    assert "performing well" in captured.out


def test_export_slow_queries_to_csv(tmp_path, sample_slow_ops):
    """Test exporting slow queries to CSV."""
    output_dir = tmp_path / "output"

    csv_path = export_slow_queries_to_csv(
        sample_slow_ops,
        output_dir,
        "testdb",
    )

    assert csv_path.exists()
    assert csv_path.name.startswith("slow_queries_testdb_")
    assert csv_path.suffix == ".csv"

    # Verify content
    with open(csv_path, encoding="utf-8") as f:
        content = f.read()
        assert "Timestamp,Operation,Namespace" in content
        assert "query" in content
        assert "update" in content
        assert "250" in content
        assert "150" in content
