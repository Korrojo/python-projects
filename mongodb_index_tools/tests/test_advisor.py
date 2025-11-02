"""Tests for advisor module."""

from unittest.mock import MagicMock


from mongodb_index_tools.advisor import (
    analyze_collection_indexes,
    export_recommendations_to_csv,
    generate_recommendations,
    is_redundant,
    print_recommendations,
)


def test_is_redundant():
    """Test detecting redundant indexes."""
    # Index on {a: 1} is redundant if there's an index on {a: 1, b: 1}
    index_keys = {"a": 1}
    all_indexes = [
        {"name": "idx_a", "key": {"a": 1}},
        {"name": "idx_a_b", "key": {"a": 1, "b": 1}},
    ]

    assert is_redundant(index_keys, all_indexes, "idx_a") is True

    # Index on {a: 1, b: 1} is NOT redundant
    index_keys = {"a": 1, "b": 1}
    assert is_redundant(index_keys, all_indexes, "idx_a_b") is False

    # Different sort direction - not redundant
    index_keys = {"a": -1}
    all_indexes = [
        {"name": "idx_a_desc", "key": {"a": -1}},
        {"name": "idx_a_asc", "key": {"a": 1}},
    ]
    assert is_redundant(index_keys, all_indexes, "idx_a_desc") is False


def test_analyze_collection_indexes():
    """Test analyzing collection indexes."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    # Mock indexes
    mock_indexes = [
        {"name": "_id_", "key": {"_id": 1}},
        {"name": "idx_unused", "key": {"field1": 1}},
        {"name": "idx_redundant", "key": {"field2": 1}},
        {"name": "idx_compound", "key": {"field2": 1, "field3": 1}},
        {"name": "idx_used", "key": {"field4": 1}},
    ]
    mock_collection.list_indexes.return_value = mock_indexes

    # Mock index stats
    mock_index_stats = [
        {"name": "idx_unused", "accesses": {"ops": 0}},
        {"name": "idx_redundant", "accesses": {"ops": 100}},
        {"name": "idx_compound", "accesses": {"ops": 500}},
        {"name": "idx_used", "accesses": {"ops": 1000}},
    ]
    mock_collection.aggregate.return_value = mock_index_stats

    # Mock collStats
    mock_db.command.return_value = {
        "indexSizes": {
            "idx_unused": 1048576,  # 1 MB
            "idx_redundant": 2097152,  # 2 MB
            "idx_compound": 3145728,  # 3 MB
            "idx_used": 4194304,  # 4 MB
        }
    }

    analysis = analyze_collection_indexes(mock_db, "testcoll")

    assert analysis["collection_name"] == "testcoll"
    assert analysis["total_indexes"] == 5  # Including _id_

    # Check categorization
    assert len(analysis["unused_indexes"]) == 1
    assert analysis["unused_indexes"][0]["name"] == "idx_unused"

    # idx_redundant is covered by idx_compound (same prefix)
    assert len(analysis["redundant_indexes"]) == 1
    assert analysis["redundant_indexes"][0]["name"] == "idx_redundant"

    # idx_used and idx_compound are useful
    assert len(analysis["useful_indexes"]) == 2


def test_generate_recommendations():
    """Test generating recommendations."""
    analysis = {
        "collection_name": "testcoll",
        "total_indexes": 4,
        "unused_indexes": [
            {
                "name": "idx_unused",
                "keys": ["field1"],
                "usage_count": 0,
                "size_mb": 1.0,
            }
        ],
        "redundant_indexes": [
            {
                "name": "idx_redundant",
                "keys": ["field2"],
                "usage_count": 100,
                "size_mb": 2.0,
            }
        ],
        "useful_indexes": [
            {
                "name": "idx_useful",
                "keys": ["field3"],
                "usage_count": 1000,
                "size_mb": 4.0,
            }
        ],
    }

    recommendations = generate_recommendations(analysis)

    # Should recommend dropping unused and redundant, plus one info message
    assert len(recommendations) == 3

    # Check DROP recommendations
    drop_recs = [r for r in recommendations if r["type"] == "DROP"]
    assert len(drop_recs) == 2

    # Unused index should be HIGH severity
    unused_rec = [r for r in drop_recs if r["index_name"] == "idx_unused"][0]
    assert unused_rec["severity"] == "HIGH"
    assert "dropIndex" in unused_rec["action"]

    # Redundant index should be MEDIUM severity
    redundant_rec = [r for r in drop_recs if r["index_name"] == "idx_redundant"][0]
    assert redundant_rec["severity"] == "MEDIUM"

    # Info recommendation
    info_rec = [r for r in recommendations if r["type"] == "INFO"][0]
    assert "useful" in info_rec["reason"].lower()


def test_print_recommendations(capsys):
    """Test printing recommendations to console."""
    analysis = {
        "collection_name": "testcoll",
        "total_indexes": 3,
        "unused_indexes": [{"name": "idx_unused", "keys": ["field1"], "usage_count": 0, "size_mb": 1.0}],
        "redundant_indexes": [],
        "useful_indexes": [{"name": "idx_useful", "keys": ["field2"], "usage_count": 500, "size_mb": 2.0}],
    }

    recommendations = [
        {
            "type": "DROP",
            "severity": "HIGH",
            "index_name": "idx_unused",
            "reason": "Unused index (0 operations), consuming 1.0 MB",
            "action": 'db.testcoll.dropIndex("idx_unused")',
            "impact": "Saves 1.0 MB of storage and improves write performance",
        }
    ]

    print_recommendations(analysis, recommendations)
    captured = capsys.readouterr()

    assert "Index Recommendations for Collection: testcoll" in captured.out
    assert "Total Indexes: 3" in captured.out
    assert "Unused Indexes: 1" in captured.out
    assert "idx_unused" in captured.out
    assert "Recommendations (1)" in captured.out
    assert "DROP" in captured.out


def test_export_recommendations_to_csv(tmp_path):
    """Test exporting recommendations to CSV."""
    analysis = {
        "collection_name": "testcoll",
        "total_indexes": 2,
        "unused_indexes": [{"name": "idx_unused", "keys": ["field1"], "usage_count": 0, "size_mb": 1.0}],
        "redundant_indexes": [],
        "useful_indexes": [],
    }

    recommendations = [
        {
            "type": "DROP",
            "severity": "HIGH",
            "index_name": "idx_unused",
            "reason": "Unused index",
            "action": "db.testcoll.dropIndex(...)",
            "impact": "Saves storage",
        }
    ]

    output_dir = tmp_path / "output"
    csv_path = export_recommendations_to_csv(analysis, recommendations, output_dir, "testdb")

    assert csv_path.exists()
    assert csv_path.name.startswith("index_recommendations_testdb_testcoll_")
    assert csv_path.suffix == ".csv"

    # Verify content
    with open(csv_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Type,Severity,Index Name" in content
        assert "DROP,HIGH,idx_unused" in content
