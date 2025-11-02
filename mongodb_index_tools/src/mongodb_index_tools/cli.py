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


@app.callback()
def main():
    """MongoDB index management and analysis tools.

    Run 'python run.py --help' to see available commands.
    """
    pass


if __name__ == "__main__":
    app()
