"""Tests for analyzer module."""

from datetime import datetime
from unittest.mock import MagicMock


from mongodb_index_tools.analyzer import (
    analyze_query,
    assess_performance,
    determine_scan_type,
    extract_metrics,
    get_index_name,
    get_plan_stage,
    print_analysis,
    save_analysis_json,
)


def test_get_plan_stage():
    """Test extracting plan stage."""
    plan = {"stage": "IXSCAN"}
    assert get_plan_stage(plan) == "IXSCAN"

    # Test nested stage
    plan = {
        "stage": "FETCH",
        "inputStage": {"stage": "IXSCAN"}
    }
    assert get_plan_stage(plan) == "FETCH"


def test_get_index_name():
    """Test extracting index name."""
    plan = {"indexName": "idx_age"}
    assert get_index_name(plan) == "idx_age"

    # Test nested index name
    plan = {
        "stage": "FETCH",
        "inputStage": {"stage": "IXSCAN", "indexName": "idx_email"}
    }
    assert get_index_name(plan) == "idx_email"

    # Test no index
    plan = {"stage": "COLLSCAN"}
    assert get_index_name(plan) == "N/A"


def test_determine_scan_type():
    """Test determining scan type."""
    assert "Collection Scan" in determine_scan_type({"stage": "COLLSCAN"})
    assert "Index Scan" in determine_scan_type({"stage": "IXSCAN"})
    assert determine_scan_type({"stage": "COUNT_SCAN"}) == "Count Scan"


def test_assess_performance():
    """Test performance assessment."""
    # Good performance
    metrics = {
        "scan_type": "Index Scan (IXSCAN)",
        "examined_to_returned_ratio": 1.2
    }
    assert "GOOD" in assess_performance(metrics)

    # Collection scan warning
    metrics = {
        "scan_type": "Collection Scan (COLLSCAN)",
        "examined_to_returned_ratio": 1.0
    }
    assert "WARNING" in assess_performance(metrics)

    # High ratio warning
    metrics = {
        "scan_type": "Index Scan",
        "examined_to_returned_ratio": 150
    }
    assessment = assess_performance(metrics)
    assert "WARNING" in assessment
    assert "High examined:returned ratio" in assessment


def test_extract_metrics():
    """Test extracting metrics from explain result."""
    explain_result = {
        "queryPlanner": {
            "namespace": "testdb.testcoll",
            "winningPlan": {
                "stage": "FETCH",
                "inputStage": {
                    "stage": "IXSCAN",
                    "indexName": "idx_test"
                }
            }
        },
        "executionStats": {
            "executionTimeMillis": 25,
            "totalKeysExamined": 100,
            "totalDocsExamined": 100,
            "nReturned": 50
        }
    }

    metrics = extract_metrics(explain_result, "find")

    assert metrics["namespace"] == "testdb.testcoll"
    assert metrics["index_name"] == "idx_test"
    assert metrics["execution_time_ms"] == 25
    assert metrics["total_keys_examined"] == 100
    assert metrics["total_docs_examined"] == 100
    assert metrics["num_returned"] == 50
    assert metrics["examined_to_returned_ratio"] == 2.0


def test_analyze_query_find():
    """Test analyzing a find query."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    # Mock explain result
    mock_explain_result = {
        "queryPlanner": {
            "namespace": "testdb.testcoll",
            "winningPlan": {
                "stage": "FETCH",
                "inputStage": {
                    "stage": "IXSCAN",
                    "indexName": "idx_age"
                }
            }
        },
        "executionStats": {
            "executionTimeMillis": 15,
            "totalKeysExamined": 50,
            "totalDocsExamined": 50,
            "nReturned": 25
        }
    }

    mock_cursor = MagicMock()
    mock_cursor.explain.return_value = mock_explain_result
    mock_collection.find.return_value = mock_cursor

    query = {"filter": {"age": {"$gt": 25}}}
    analysis = analyze_query(mock_db, "testcoll", query, "find")

    assert "error" not in analysis
    assert analysis["query_type"] == "find"
    assert analysis["namespace"] == "testdb.testcoll"
    assert analysis["index_name"] == "idx_age"
    assert analysis["execution_time_ms"] == 15


def test_analyze_query_aggregate():
    """Test analyzing an aggregate query."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.__getitem__.return_value = mock_collection

    mock_explain_result = {
        "queryPlanner": {
            "namespace": "testdb.testcoll",
            "winningPlan": {"stage": "COLLSCAN"}
        },
        "executionStats": {
            "executionTimeMillis": 100,
            "totalKeysExamined": 0,
            "totalDocsExamined": 1000,
            "nReturned": 10
        }
    }

    mock_collection.aggregate.return_value = mock_explain_result

    query = {"pipeline": [{"$match": {"status": "active"}}]}
    analysis = analyze_query(mock_db, "testcoll", query, "aggregate")

    assert "error" not in analysis
    assert analysis["query_type"] == "aggregate"
    assert "COLLSCAN" in analysis["scan_type"]


def test_print_analysis(capsys):
    """Test printing analysis to console."""
    analysis = {
        "query_type": "find",
        "namespace": "testdb.testcoll",
        "scan_type": "Index Scan (IXSCAN)",
        "index_name": "idx_age",
        "execution_time_ms": 25,
        "total_keys_examined": 100,
        "total_docs_examined": 100,
        "num_returned": 50,
        "examined_to_returned_ratio": 2.0,
        "performance_assessment": "✅ GOOD: Query appears efficient"
    }

    print_analysis(analysis)
    captured = capsys.readouterr()

    assert "Query Execution Plan Analysis" in captured.out
    assert "FIND" in captured.out
    assert "testdb.testcoll" in captured.out
    assert "Index Scan" in captured.out
    assert "idx_age" in captured.out
    assert "25 ms" in captured.out
    assert "GOOD" in captured.out


def test_print_analysis_error(capsys):
    """Test printing analysis with error."""
    analysis = {
        "error": "Invalid query syntax",
        "query_type": "find"
    }

    print_analysis(analysis)
    captured = capsys.readouterr()

    assert "Error analyzing query" in captured.out
    assert "Invalid query syntax" in captured.out


def test_save_analysis_json(tmp_path):
    """Test saving analysis to JSON file."""
    analysis = {
        "query_type": "find",
        "namespace": "testdb.testcoll",
        "execution_time_ms": 25
    }

    output_path = tmp_path / "output" / "analysis.json"
    saved_path = save_analysis_json(analysis, output_path)

    assert saved_path.exists()
    assert saved_path == output_path

    # Verify content
    import json
    with open(saved_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
        assert loaded["query_type"] == "find"
        assert loaded["namespace"] == "testdb.testcoll"
