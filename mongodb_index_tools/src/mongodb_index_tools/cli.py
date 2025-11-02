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


@app.command("advisor")
def advisor(
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
        help="Export recommendations to CSV file",
    ),
):
    """Get index recommendations for a collection.

    Analyzes indexes to identify:
    - Unused indexes (0 operations) that can be dropped
    - Redundant indexes (covered by compound indexes) that waste space
    - Useful indexes that should be kept

    Provides actionable recommendations with impact assessment.
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
    logger.info("mongodb_index_tools - Index Advisor")
    logger.info("=" * 60)

    # Validate required settings
    if not settings.mongodb_uri or not settings.database_name:
        logger.error("MongoDB URI and database name are required in configuration")
        print("❌ Error: MongoDB URI and database name must be configured in shared_config/.env")
        raise typer.Exit(code=1)

    # Validate collection parameter
    if not collection:
        logger.error("Collection name is required")
        print("❌ Error: --collection is required for index recommendations")
        print("   Example: python run.py advisor -c Patients --env PROD")
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

            # Analyze collection indexes
            from mongodb_index_tools.advisor import (
                analyze_collection_indexes,
                generate_recommendations,
                print_recommendations,
            )

            logger.info("Analyzing collection indexes...")
            analysis = analyze_collection_indexes(db, collection)

            logger.info("Generating recommendations...")
            recommendations = generate_recommendations(analysis)

            logger.info(
                f"Found {len(analysis['unused_indexes'])} unused, "
                f"{len(analysis['redundant_indexes'])} redundant, "
                f"{len(analysis['useful_indexes'])} useful indexes"
            )

            # Display recommendations
            print_recommendations(analysis, recommendations)

            # Export to CSV if requested
            if output_csv and recommendations:
                from mongodb_index_tools.advisor import export_recommendations_to_csv

                output_dir = Path(settings.paths.data_output) / "mongodb_index_tools"
                logger.info("Exporting recommendations to CSV...")
                csv_path = export_recommendations_to_csv(analysis, recommendations, output_dir, settings.database_name)
                logger.info(f"CSV exported to: {csv_path}")
                print(f"📄 Recommendations saved to: {csv_path}\n")
            elif not recommendations:
                logger.info("No recommendations to export")
            else:
                logger.info("CSV export skipped (--no-csv)")

            logger.info("=" * 60)
            logger.info("Completed successfully")
            logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        raise typer.Exit(code=1)


@app.command("create-index")
def create_index_cmd(
    env: str = typer.Option(
        None,
        "--env",
        help="Environment to use (DEV, PROD, STG, etc.) - overrides APP_ENV",
    ),
    collection: str = typer.Option(
        ...,
        "--collection",
        "-c",
        help="Collection to create index on",
    ),
    keys: str = typer.Option(
        ...,
        "--keys",
        "-k",
        help="Index keys in format: field1:1,field2:-1 (1=ascending, -1=descending)",
    ),
    name: str = typer.Option(
        None,
        "--name",
        "-n",
        help="Custom index name (auto-generated if not provided)",
    ),
    unique: bool = typer.Option(
        False,
        "--unique",
        help="Create unique index",
    ),
    sparse: bool = typer.Option(
        False,
        "--sparse",
        help="Create sparse index",
    ),
    background: bool = typer.Option(
        True,
        "--background/--foreground",
        help="Build index in background (default: background)",
    ),
    ttl_seconds: int = typer.Option(
        None,
        "--ttl",
        help="TTL in seconds (for TTL indexes)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be created without actually creating",
    ),
):
    """Create an index on a collection.

    Examples:
        # Create single-field ascending index
        python run.py create-index -c Users --keys email:1

        # Create compound index
        python run.py create-index -c Users --keys status:1,created_at:-1

        # Create unique index with custom name
        python run.py create-index -c Users --keys email:1 --unique --name idx_unique_email

        # Create TTL index (expires documents after 30 days)
        python run.py create-index -c Sessions --keys created_at:1 --ttl 2592000

        # Dry run to preview
        python run.py create-index -c Users --keys status:1 --dry-run
    """
    from mongodb_index_tools.manager import create_index

    # Set environment if provided
    if env:
        os.environ["APP_ENV"] = env.upper()

    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    try:
        # Get settings
        settings = get_settings()

        # Validate settings
        if not settings.mongodb_uri or not settings.database_name:
            logger.error("MongoDB URI and database name are required")
            print("❌ Error: MongoDB URI and database name must be configured\n")
            raise typer.Exit(code=1)

        logger.info("=" * 60)
        logger.info(f"Environment: {os.environ.get('APP_ENV', 'DEV')}")
        logger.info(f"MongoDB URI: {redact_uri(settings.mongodb_uri)}")
        logger.info(f"Database: {settings.database_name}")
        logger.info(f"Collection: {collection}")
        logger.info("=" * 60)

        # Parse keys
        try:
            keys_dict = {}
            for key_spec in keys.split(","):
                field, direction = key_spec.strip().split(":")
                keys_dict[field.strip()] = int(direction.strip())
        except Exception as e:
            logger.error(f"Invalid keys format: {e}")
            print("\n❌ Error: Invalid keys format. Use 'field1:1,field2:-1' format\n")
            raise typer.Exit(code=1)

        # Connect to MongoDB
        with get_mongo_client(mongodb_uri=settings.mongodb_uri, database_name=settings.database_name) as client:
            db = client[settings.database_name]

            # Validate collection exists
            if collection not in db.list_collection_names():
                logger.error(f"Collection '{collection}' does not exist")
                print(f"\n❌ Error: Collection '{collection}' does not exist\n")
                raise typer.Exit(code=1)

            # Create index
            result = create_index(
                db=db,
                collection_name=collection,
                keys=keys_dict,
                name=name,
                unique=unique,
                sparse=sparse,
                background=background,
                expire_after_seconds=ttl_seconds,
                dry_run=dry_run,
            )

            # Display result
            if result["success"]:
                if dry_run:
                    print("\n🔍 DRY RUN - No changes made")
                    print("=" * 60)
                    print(f"Would create index: {result['index_name']}")
                    print(f"Keys: {result['keys']}")
                    print(f"Options: {result['options']}")
                    print("=" * 60)
                else:
                    print("\n✅ Index created successfully!")
                    print("=" * 60)
                    print(f"Index name: {result['index_name']}")
                    print(f"Keys: {result['keys']}")
                    print(f"Options: {result['options']}")
                    print("=" * 60)

                logger.info(f"Index operation completed: {result}")
            else:
                print(f"\n❌ Failed to create index: {result.get('error', 'Unknown error')}")
                logger.error(f"Index creation failed: {result}")
                raise typer.Exit(code=1)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        raise typer.Exit(code=1)


@app.command("drop-index")
def drop_index_cmd(
    env: str = typer.Option(
        None,
        "--env",
        help="Environment to use (DEV, PROD, STG, etc.) - overrides APP_ENV",
    ),
    collection: str = typer.Option(
        ...,
        "--collection",
        "-c",
        help="Collection to drop index from",
    ),
    index_name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="Name of the index to drop",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be dropped without actually dropping",
    ),
):
    """Drop an index from a collection.

    Examples:
        # Drop an index (with confirmation)
        python run.py drop-index -c Users --name idx_email_1

        # Drop without confirmation
        python run.py drop-index -c Users --name idx_email_1 --force

        # Dry run to preview
        python run.py drop-index -c Users --name idx_email_1 --dry-run
    """
    from mongodb_index_tools.manager import drop_index

    # Set environment if provided
    if env:
        os.environ["APP_ENV"] = env.upper()

    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    try:
        # Get settings
        settings = get_settings()

        # Validate settings
        if not settings.mongodb_uri or not settings.database_name:
            logger.error("MongoDB URI and database name are required")
            print("❌ Error: MongoDB URI and database name must be configured\n")
            raise typer.Exit(code=1)

        logger.info("=" * 60)
        logger.info(f"Environment: {os.environ.get('APP_ENV', 'DEV')}")
        logger.info(f"MongoDB URI: {redact_uri(settings.mongodb_uri)}")
        logger.info(f"Database: {settings.database_name}")
        logger.info(f"Collection: {collection}")
        logger.info("=" * 60)

        # Connect to MongoDB
        with get_mongo_client(mongodb_uri=settings.mongodb_uri, database_name=settings.database_name) as client:
            db = client[settings.database_name]

            # Validate collection exists
            if collection not in db.list_collection_names():
                logger.error(f"Collection '{collection}' does not exist")
                print(f"\n❌ Error: Collection '{collection}' does not exist\n")
                raise typer.Exit(code=1)

            # Confirmation prompt (unless force or dry-run)
            if not force and not dry_run:
                confirm = typer.confirm(
                    f"Are you sure you want to drop index '{index_name}' from collection '{collection}'?"
                )
                if not confirm:
                    print("\n❌ Operation cancelled\n")
                    logger.info("User cancelled drop operation")
                    raise typer.Exit(code=0)

            # Drop index
            result = drop_index(
                db=db,
                collection_name=collection,
                index_name=index_name,
                dry_run=dry_run,
            )

            # Display result
            if result["success"]:
                if dry_run:
                    print("\n🔍 DRY RUN - No changes made")
                    print("=" * 60)
                    print(f"Would drop index: {result['index_name']}")
                    if result.get("index_info"):
                        print(f"Index keys: {result['index_info'].get('key', {})}")
                    print("=" * 60)
                else:
                    print("\n✅ Index dropped successfully!")
                    print("=" * 60)
                    print(f"Index name: {result['index_name']}")
                    if result.get("index_info"):
                        print(f"Index keys: {result['index_info'].get('key', {})}")
                    print("=" * 60)

                logger.info(f"Index operation completed: {result}")
            else:
                print(f"\n❌ Failed to drop index: {result.get('error', 'Unknown error')}")
                logger.error(f"Index drop failed: {result}")
                raise typer.Exit(code=1)

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
