"""CLI interface for mongodb_index_tools with multiple commands."""

import os
from pathlib import Path

import typer

from common_config.config.settings import get_settings
from common_config.connectors.mongodb import get_mongo_client
from common_config.utils.logger import get_logger, setup_logging
from common_config.utils.security import redact_uri

app = typer.Typer(
    help="MongoDB index management and analysis tools",
    no_args_is_help=True,
)


@app.command("inventory")
def inventory(
    env: str = typer.Option(
        None,
        "--env",
        help="Environment to use (DEV, PROD, STG, etc.) - overrides APP_ENV",
    ),
    collection: str = typer.Option(
        None,
        "--collection",
        "-c",
        help="Analyze specific collection (default: all collections)",
    ),
    exclude_system: bool = typer.Option(
        True,
        "--exclude-system/--include-system",
        help="Exclude system collections (system.*)",
    ),
    output_csv: bool = typer.Option(
        True,
        "--output-csv/--no-csv",
        help="Export results to CSV file",
    ),
):
    """List all indexes in the database with detailed information.

    Shows collection name, index name, keys, and attributes for each index.
    Helps understand the current index landscape and identify opportunities
    for optimization.
    """
    # Set environment if provided
    if env:
        os.environ["APP_ENV"] = env.upper()

    settings = get_settings()
    log_dir = Path(settings.paths.logs) / "mongodb_index_tools"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir)
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info("mongodb_index_tools - Index Inventory")
    logger.info("=" * 60)

    # Validate required settings
    if not settings.mongodb_uri or not settings.database_name:
        logger.error("MongoDB URI and database name are required in configuration")
        print("❌ Error: MongoDB URI and database name must be configured in shared_config/.env")
        raise typer.Exit(code=1)

    try:
        with get_mongo_client(mongodb_uri=settings.mongodb_uri, database_name=settings.database_name) as client:
            db = client[settings.database_name]
            logger.info(f"Environment: {env.upper() if env else os.environ.get('APP_ENV', 'default')}")
            logger.info(f"MongoDB URI: {redact_uri(settings.mongodb_uri)}")
            logger.info(f"Database: {settings.database_name}")

            # Determine collections to analyze
            if collection:
                collections = [collection]
                logger.info(f"Analyzing collection: {collection}")
            else:
                collections = db.list_collection_names()
                if exclude_system:
                    collections = [c for c in collections if not c.startswith("system.")]
                logger.info(f"Analyzing {len(collections)} collections")

            # Gather index inventory
            from mongodb_index_tools.inventory import gather_index_inventory

            logger.info("Gathering index inventory...")
            inventory_data = gather_index_inventory(db, collections)

            logger.info(f"Found {len(inventory_data)} indexes across {len(collections)} collections")

            # Display inventory
            from mongodb_index_tools.inventory import print_inventory

            print_inventory(inventory_data, settings.database_name)

            # Export to CSV if requested
            if output_csv:
                from mongodb_index_tools.inventory import export_inventory_to_csv

                output_dir = Path(settings.paths.data_output) / "mongodb_index_tools"
                logger.info("Exporting to CSV...")
                csv_path = export_inventory_to_csv(inventory_data, output_dir, settings.database_name)
                logger.info(f"CSV exported to: {csv_path}")
                print(f"\n✅ CSV file saved to: {csv_path}\n")
            else:
                logger.info("CSV export skipped (--no-csv)")

            logger.info("=" * 60)
            logger.info("Completed successfully")
            logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        raise typer.Exit(code=1)


@app.command("utilization")
def utilization(
    env: str = typer.Option(
        None,
        "--env",
        help="Environment to use (DEV, PROD, STG, etc.) - overrides APP_ENV",
    ),
    collection: str = typer.Option(
        None,
        "--collection",
        "-c",
        help="Collection name to analyze (required)",
    ),
    output_csv: bool = typer.Option(
        True,
        "--output-csv/--no-csv",
        help="Export results to CSV file",
    ),
):
    """Analyze index usage statistics for a collection.

    Uses MongoDB's $indexStats aggregation to show how often each index
    is used. Helps identify unused indexes that could be removed and
    heavily-used indexes that may need optimization.

    Note: Index usage statistics are reset when MongoDB restarts.
    """
    # Set environment if provided
    if env:
        os.environ["APP_ENV"] = env.upper()

    settings = get_settings()
    log_dir = Path(settings.paths.logs) / "mongodb_index_tools"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir)
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info("mongodb_index_tools - Index Utilization")
    logger.info("=" * 60)

    # Validate required settings
    if not settings.mongodb_uri or not settings.database_name:
        logger.error("MongoDB URI and database name are required in configuration")
        print("❌ Error: MongoDB URI and database name must be configured in shared_config/.env")
        raise typer.Exit(code=1)

    # Validate collection parameter
    if not collection:
        logger.error("Collection name is required")
        print("❌ Error: --collection is required for utilization analysis")
        print("   Example: python run.py utilization -c Patients --env PROD")
        raise typer.Exit(code=1)

    try:
        with get_mongo_client(mongodb_uri=settings.mongodb_uri, database_name=settings.database_name) as client:
            db = client[settings.database_name]
            logger.info(f"Environment: {env.upper() if env else os.environ.get('APP_ENV', 'default')}")
            logger.info(f"MongoDB URI: {redact_uri(settings.mongodb_uri)}")
            logger.info(f"Database: {settings.database_name}")
            logger.info(f"Collection: {collection}")

            # Verify collection exists
            if collection not in db.list_collection_names():
                logger.error(f"Collection '{collection}' not found in database")
                print(f"\n❌ Error: Collection '{collection}' not found in database '{settings.database_name}'")
                raise typer.Exit(code=1)

            # Gather utilization statistics
            from mongodb_index_tools.utilization import gather_index_utilization

            logger.info("Gathering index utilization statistics...")
            utilization_data, index_sizes = gather_index_utilization(db, collection)

            logger.info(f"Found {len(utilization_data)} indexes with usage statistics")

            # Display utilization
            from mongodb_index_tools.utilization import print_utilization

            print_utilization(collection, utilization_data, index_sizes)

            # Export to CSV if requested
            if output_csv and utilization_data:
                from mongodb_index_tools.utilization import export_utilization_to_csv

                output_dir = Path(settings.paths.data_output) / "mongodb_index_tools"
                logger.info("Exporting to CSV...")
                csv_path = export_utilization_to_csv(
                    collection, utilization_data, index_sizes, output_dir, settings.database_name
                )
                logger.info(f"CSV exported to: {csv_path}")
                print(f"✅ CSV file saved to: {csv_path}\n")
            elif not utilization_data:
                logger.info("No utilization data to export")
            else:
                logger.info("CSV export skipped (--no-csv)")

            logger.info("=" * 60)
            logger.info("Completed successfully")
            logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        raise typer.Exit(code=1)


@app.command("analyzer")
def analyzer(
    env: str = typer.Option(
        None,
        "--env",
        help="Environment to use (DEV, PROD, STG, etc.) - overrides APP_ENV",
    ),
    collection: str = typer.Option(
        None,
        "--collection",
        "-c",
        help="Collection name to analyze (required)",
    ),
    query_file: str = typer.Option(
        None,
        "--query-file",
        "-f",
        help="Path to JSON file containing query",
    ),
    query_type: str = typer.Option(
        "find",
        "--query-type",
        "-t",
        help="Query type: find, aggregate, update, delete",
    ),
    save_json: bool = typer.Option(
        False,
        "--save-json",
        help="Save full explain output to JSON file",
    ),
):
    """Analyze query execution plan using MongoDB's explain command.

    Analyzes how MongoDB executes a query, showing scan type, index usage,
    and performance metrics. Helps identify inefficient queries that need
    optimization.

    Example query file (find):
    {
      "filter": {"age": {"$gt": 25}},
      "projection": {"name": 1, "email": 1},
      "sort": {"name": 1},
      "limit": 100
    }

    Example query file (aggregate):
    {
      "pipeline": [
        {"$match": {"status": "active"}},
        {"$group": {"_id": "$city", "count": {"$sum": 1}}}
      ]
    }
    """
    import json

    # Set environment if provided
    if env:
        os.environ["APP_ENV"] = env.upper()

    settings = get_settings()
    log_dir = Path(settings.paths.logs) / "mongodb_index_tools"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir)
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info("mongodb_index_tools - Query Analyzer")
    logger.info("=" * 60)

    # Validate required settings
    if not settings.mongodb_uri or not settings.database_name:
        logger.error("MongoDB URI and database name are required in configuration")
        print("❌ Error: MongoDB URI and database name must be configured in shared_config/.env")
        raise typer.Exit(code=1)

    # Validate collection parameter
    if not collection:
        logger.error("Collection name is required")
        print("❌ Error: --collection is required for query analysis")
        print("   Example: python run.py analyzer -c Patients -f query.json --env PROD")
        raise typer.Exit(code=1)

    # Validate and load query
    if not query_file:
        logger.error("Query file is required")
        print("❌ Error: --query-file is required")
        print("   Example: python run.py analyzer -c Patients -f query.json")
        raise typer.Exit(code=1)

    query_path = Path(query_file)
    if not query_path.exists():
        logger.error(f"Query file not found: {query_file}")
        print(f"❌ Error: Query file not found: {query_file}")
        raise typer.Exit(code=1)

    try:
        with open(query_path, "r", encoding="utf-8") as f:
            query = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in query file: {e}")
        print(f"❌ Error: Invalid JSON in query file: {e}")
        raise typer.Exit(code=1)

    try:
        with get_mongo_client(mongodb_uri=settings.mongodb_uri, database_name=settings.database_name) as client:
            db = client[settings.database_name]
            logger.info(f"Environment: {env.upper() if env else os.environ.get('APP_ENV', 'default')}")
            logger.info(f"MongoDB URI: {redact_uri(settings.mongodb_uri)}")
            logger.info(f"Database: {settings.database_name}")
            logger.info(f"Collection: {collection}")
            logger.info(f"Query Type: {query_type}")

            # Verify collection exists
            if collection not in db.list_collection_names():
                logger.error(f"Collection '{collection}' not found in database")
                print(f"\n❌ Error: Collection '{collection}' not found in database '{settings.database_name}'")
                raise typer.Exit(code=1)

            # Analyze query
            from mongodb_index_tools.analyzer import analyze_query, print_analysis

            logger.info("Analyzing query execution plan...")
            analysis = analyze_query(db, collection, query, query_type)

            logger.info("Analysis complete")

            # Display analysis
            print_analysis(analysis)

            # Save JSON if requested
            if save_json and "error" not in analysis:
                from mongodb_index_tools.analyzer import save_analysis_json

                output_dir = Path(settings.paths.data_output) / "mongodb_index_tools"
                from datetime import datetime

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                json_filename = f"explain_{settings.database_name}_{collection}_{timestamp}.json"
                json_path = output_dir / json_filename

                logger.info("Saving full explain output to JSON...")
                save_analysis_json(analysis, json_path)
                logger.info(f"JSON saved to: {json_path}")
                print(f"📄 Full explain output saved to: {json_path}\n")

            logger.info("=" * 60)
            logger.info("Completed successfully")
            logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        raise typer.Exit(code=1)


@app.callback()
def main():
    """MongoDB index management and analysis tools.

    Run 'python run.py --help' to see available commands.
    """
    pass


if __name__ == "__main__":
    app()
