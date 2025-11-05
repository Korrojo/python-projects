"""Tests for profiler_stats module."""

from datetime import datetime
from unittest.mock import MagicMock

from mongodb_profiler_tools.profiler_stats import get_profiler_stats, print_profiler_stats


def test_get_profiler_stats_enabled():
    """Test getting profiler stats when profiling is enabled."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    # Mock collection stats
    mock_db.command.side_effect = [
        # collStats response
        {
            "size": 10485760,  # 10 MB
            "storageSize": 15728640,  # 15 MB
            "avgObjSize": 1024,
            "capped": True,
            "maxSize": 104857600,  # 100 MB
        },
        # profile status response
        {
            "was": 1,  # Level 1 (slow operations)
            "slowms": 100,
        },
    ]

    # Mock document count
    mock_collection.count_documents.return_value = 5000

    # Mock time range
    oldest_entry = {"ts": datetime(2024, 1, 1, 0, 0)}
    newest_entry = {"ts": datetime(2024, 1, 2, 0, 0)}
    mock_collection.find_one.side_effect = [oldest_entry, newest_entry]

    result = get_profiler_stats(mock_db)

    assert result["profiling_enabled"] is True
    assert result["profiling_level"] == 1
    assert result["slowms"] == 100
    assert result["document_count"] == 5000
    assert result["size_mb"] == 10.0
    assert result["storage_size_mb"] == 15.0
    assert result["capped"] is True
    assert result["max_size"] == 104857600


def test_get_profiler_stats_disabled():
    """Test getting profiler stats when profiling is disabled."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_db.command.side_effect = [
        # collStats response
        {
            "size": 0,
            "storageSize": 0,
            "avgObjSize": 0,
            "capped": False,
        },
        # profile status response
        {
            "was": 0,  # Level 0 (off)
            "slowms": 100,
        },
    ]

    mock_collection.count_documents.return_value = 0
    mock_collection.find_one.side_effect = [None, None]

    result = get_profiler_stats(mock_db)

    assert result["profiling_enabled"] is False
    assert result["profiling_level"] == 0
    assert result["document_count"] == 0


def test_get_profiler_stats_no_entries():
    """Test getting profiler stats when no entries exist."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_db.command.side_effect = [
        {"size": 0, "storageSize": 0, "avgObjSize": 0, "capped": True},
        {"was": 1, "slowms": 100},
    ]

    mock_collection.count_documents.return_value = 0
    mock_collection.find_one.return_value = None

    result = get_profiler_stats(mock_db)

    assert result["oldest_timestamp"] is None
    assert result["newest_timestamp"] is None
    assert result["duration_ms"] == 0


def test_get_profiler_stats_exception():
    """Test handling exception when system.profile doesn't exist."""
    mock_db = MagicMock()
    mock_db.command.side_effect = Exception("Collection not found")

    result = get_profiler_stats(mock_db)

    assert "error" in result
    assert result["profiling_enabled"] is False


def test_print_profiler_stats_enabled(capsys):
    """Test printing profiler stats when enabled."""
    stats = {
        "profiling_enabled": True,
        "profiling_level": 1,
        "slowms": 100,
        "document_count": 5000,
        "size_mb": 10.5,
        "size_bytes": 11010048,
        "storage_size_mb": 15.2,
        "storage_size_bytes": 15932416,
        "avg_obj_size": 2048,
        "capped": True,
        "max_size": 104857600,
        "oldest_timestamp": datetime(2024, 1, 1, 0, 0),
        "newest_timestamp": datetime(2024, 1, 2, 0, 0),
        "duration_ms": 86400000,
        "duration_hours": 24.0,
        "duration_days": 1.0,
    }

    print_profiler_stats(stats)

    captured = capsys.readouterr()
    assert "MongoDB Profiler Statistics" in captured.out
    assert "Enabled: ✅ Yes" in captured.out
    assert "Level: 1" in captured.out
    assert "5,000" in captured.out
    assert "10.5" in captured.out


def test_print_profiler_stats_disabled(capsys):
    """Test printing profiler stats when disabled."""
    stats = {
        "profiling_enabled": False,
        "profiling_level": 0,
        "slowms": 100,
        "document_count": 0,
        "size_mb": 0,
        "size_bytes": 0,
        "storage_size_mb": 0,
        "storage_size_bytes": 0,
        "avg_obj_size": 0,
        "capped": False,
        "max_size": None,
        "oldest_timestamp": None,
        "newest_timestamp": None,
        "duration_ms": 0,
        "duration_hours": 0,
        "duration_days": 0,
    }

    print_profiler_stats(stats)

    captured = capsys.readouterr()
    assert "Enabled: ❌ No" in captured.out
    assert "Level: 0" in captured.out


def test_print_profiler_stats_error(capsys):
    """Test printing profiler stats with error."""
    stats = {
        "profiling_enabled": False,
        "error": "Collection not found",
    }

    print_profiler_stats(stats)

    captured = capsys.readouterr()
    assert "Error getting profiler statistics" in captured.out
    assert "Collection not found" in captured.out
