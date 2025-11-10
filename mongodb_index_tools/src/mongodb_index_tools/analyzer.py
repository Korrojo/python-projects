"""Query analyzer module - analyze query execution plans."""

import json
from pathlib import Path
from typing import Any


def analyze_query(db: Any, collection_name: str, query: dict[str, Any], query_type: str = "find") -> dict[str, Any]:
    """Analyze a query using MongoDB's explain command.

    Args:
        db: MongoDB database instance
        collection_name: Name of the collection
        query: Query to analyze (dict format)
        query_type: Type of query ("find", "aggregate", "update", "delete")

    Returns:
        Dictionary containing explain results and analysis
    """
    collection = db[collection_name]

    # Build explain command based on query type
    try:
        if query_type == "find":
            # For find queries
            filter_query = query.get("filter", {})
            projection = query.get("projection")
            sort = query.get("sort")
            limit = query.get("limit")

            cursor = collection.find(filter_query)
            if projection:
                cursor = cursor.projection(projection)
            if sort:
                cursor = cursor.sort(list(sort.items()))
            if limit:
                cursor = cursor.limit(limit)

            explain_result = cursor.explain()

        elif query_type == "aggregate":
            # For aggregation queries
            pipeline = query.get("pipeline", [])
            explain_result = collection.aggregate(pipeline, explain=True)

        elif query_type == "update":
            # For update queries - use explain on runCommand
            filter_query = query.get("filter", {})
            update_doc = query.get("update", {})
            multi = query.get("multi", False)

            explain_cmd = {
                "explain": {
                    "update": collection_name,
                    "updates": [{"q": filter_query, "u": update_doc, "multi": multi}],
                },
                "verbosity": "executionStats",
            }
            explain_result = db.command(explain_cmd)

        elif query_type == "delete":
            # For delete queries
            filter_query = query.get("filter", {})
            limit_val = query.get("limit", 0)

            explain_cmd = {
                "explain": {"delete": collection_name, "deletes": [{"q": filter_query, "limit": limit_val}]},
                "verbosity": "executionStats",
            }
            explain_result = db.command(explain_cmd)

        else:
            raise ValueError(f"Unsupported query type: {query_type}")

    except Exception as e:
        return {"error": str(e), "query": query, "query_type": query_type}

    # Extract key metrics from explain result
    analysis = extract_metrics(explain_result, query_type)
    analysis["query"] = query
    analysis["query_type"] = query_type
    analysis["raw_explain"] = explain_result

    return analysis


def extract_metrics(explain_result: dict[str, Any], query_type: str) -> dict[str, Any]:
    """Extract key performance metrics from explain result.

    Args:
        explain_result: Raw explain output from MongoDB
        query_type: Type of query analyzed

    Returns:
        Dictionary with extracted metrics
    """
    metrics = {}

    try:
        # Get query planner info
        query_planner = explain_result.get("queryPlanner", {})
        metrics["namespace"] = query_planner.get("namespace", "N/A")

        # Get winning plan
        winning_plan = query_planner.get("winningPlan", {})
        metrics["winning_plan_stage"] = get_plan_stage(winning_plan)
        metrics["index_name"] = get_index_name(winning_plan)

        # Get execution stats
        exec_stats = explain_result.get("executionStats", {})
        metrics["execution_time_ms"] = exec_stats.get("executionTimeMillis", 0)
        metrics["total_keys_examined"] = exec_stats.get("totalKeysExamined", 0)
        metrics["total_docs_examined"] = exec_stats.get("totalDocsExamined", 0)
        metrics["num_returned"] = exec_stats.get("nReturned", 0)

        # Calculate efficiency ratio
        if metrics["num_returned"] > 0:
            metrics["examined_to_returned_ratio"] = metrics["total_docs_examined"] / metrics["num_returned"]
        else:
            metrics["examined_to_returned_ratio"] = (
                metrics["total_docs_examined"] if metrics["total_docs_examined"] > 0 else 0
            )

        # Determine scan type and performance assessment
        metrics["scan_type"] = determine_scan_type(winning_plan)
        metrics["performance_assessment"] = assess_performance(metrics)

    except Exception as e:
        metrics["extraction_error"] = str(e)

    return metrics


def get_plan_stage(plan: dict[str, Any], depth: int = 0) -> str:
    """Recursively get the execution stage from a plan.

    Args:
        plan: Plan dictionary
        depth: Current recursion depth

    Returns:
        Stage name or "N/A"
    """
    if not plan or depth > 10:  # Prevent infinite recursion
        return "N/A"

    stage = plan.get("stage", "N/A")
    if stage != "N/A":
        return stage

    # Check input stage
    if "inputStage" in plan:
        return get_plan_stage(plan["inputStage"], depth + 1)

    # Check input stages (for multi-branch plans)
    if "inputStages" in plan and plan["inputStages"]:
        return get_plan_stage(plan["inputStages"][0], depth + 1)

    return "N/A"


def get_index_name(plan: dict[str, Any], depth: int = 0) -> str:
    """Recursively extract index name from plan.

    Args:
        plan: Plan dictionary
        depth: Current recursion depth

    Returns:
        Index name or "N/A"
    """
    if not plan or depth > 10:
        return "N/A"

    # Check for indexName at current level
    if "indexName" in plan:
        return plan["indexName"]

    # Check input stage
    if "inputStage" in plan:
        result = get_index_name(plan["inputStage"], depth + 1)
        if result != "N/A":
            return result

    # Check input stages
    if "inputStages" in plan:
        for stage in plan["inputStages"]:
            result = get_index_name(stage, depth + 1)
            if result != "N/A":
                return result

    return "N/A"


def determine_scan_type(plan: dict[str, Any]) -> str:
    """Determine the type of scan performed.

    Args:
        plan: Winning plan dictionary

    Returns:
        Scan type (COLLSCAN, IXSCAN, FETCH, etc.)
    """
    stage = plan.get("stage", "UNKNOWN")

    # Common scan types
    if stage == "COLLSCAN":
        return "Collection Scan (COLLSCAN)"
    elif stage == "IXSCAN":
        return "Index Scan (IXSCAN)"
    elif stage == "FETCH":
        # FETCH usually has an input stage with the actual scan
        if "inputStage" in plan:
            return determine_scan_type(plan["inputStage"])
        return "Fetch with Index"
    elif stage == "COUNT_SCAN":
        return "Count Scan"
    elif stage == "DISTINCT_SCAN":
        return "Distinct Scan"
    else:
        return stage


def assess_performance(metrics: dict[str, Any]) -> str:
    """Assess query performance based on metrics.

    Args:
        metrics: Extracted metrics dictionary

    Returns:
        Performance assessment string
    """
    scan_type = metrics.get("scan_type", "")
    ratio = metrics.get("examined_to_returned_ratio", 0)

    # Collection scan is generally bad for large collections
    if "COLLSCAN" in scan_type:
        return "⚠️  WARNING: Collection scan - consider adding an index"

    # High examined:returned ratio indicates inefficiency
    if ratio > 100:
        return "⚠️  WARNING: High examined:returned ratio - query may be inefficient"
    elif ratio > 10:
        return "⚙️  MODERATE: Ratio suggests room for optimization"
    elif ratio <= 1.5:
        return "✅ GOOD: Query appears efficient"
    else:
        return "✓ OK: Acceptable performance"


def print_analysis(analysis: dict[str, Any]) -> None:
    """Print query analysis to console.

    Args:
        analysis: Analysis dictionary from analyze_query
    """
    if "error" in analysis:
        print(f"\n❌ Error analyzing query: {analysis['error']}\n")
        return

    print("\n" + "=" * 100)
    print("Query Execution Plan Analysis")
    print("=" * 100)

    print(f"\n📋 Query Type: {analysis['query_type'].upper()}")
    print(f"📊 Namespace: {analysis.get('namespace', 'N/A')}")
    print(f"\n🔍 Scan Type: {analysis.get('scan_type', 'N/A')}")
    print(f"🏷️  Index Used: {analysis.get('index_name', 'None')}")

    print("\n⏱️  Performance Metrics:")
    print(f"  • Execution Time: {analysis.get('execution_time_ms', 0):,} ms")
    print(f"  • Keys Examined: {analysis.get('total_keys_examined', 0):,}")
    print(f"  • Docs Examined: {analysis.get('total_docs_examined', 0):,}")
    print(f"  • Docs Returned: {analysis.get('num_returned', 0):,}")
    print(f"  • Examined:Returned Ratio: {analysis.get('examined_to_returned_ratio', 0):.2f}")

    print(f"\n💡 Assessment: {analysis.get('performance_assessment', 'N/A')}")
    print("\n" + "=" * 100 + "\n")


def save_analysis_json(analysis: dict[str, Any], output_path: Path) -> Path:
    """Save full analysis to JSON file.

    Args:
        analysis: Analysis dictionary
        output_path: Path to save JSON file

    Returns:
        Path to saved file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, default=str)

    return output_path
