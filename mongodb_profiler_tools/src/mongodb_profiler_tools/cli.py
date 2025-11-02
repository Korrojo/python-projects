"""CLI interface for mongodb_profiler_tools with multiple commands."""

import os
from pathlib import Path

import typer

from common_config.config.settings import get_settings
from common_config.connectors.mongodb import get_mongo_client
from common_config.utils.logger import get_logger, setup_logging
from common_config.utils.security import redact_uri

app = typer.Typer(
    help="MongoDB profiler tools for analyzing slow queries and profiling statistics",
    no_args_is_help=True,
)


@app.command("slow-queries")
def slow_queries(
    env: str = typer.Option(
        None,
        "--env",
        help="Environment to use (DEV, PROD, STG, etc.) - overrides APP_ENV",
    ),
    threshold: int = typer.Option(
        100,
        "--threshold",
        "-t",
        help="Minimum execution time in milliseconds (default: 100ms)",
    ),
    collection: str = typer.Option(
        None,
        "--collection",
        "-c",
        help="Filter by specific collection (format: database.collection)",
    ),
    operation: str = typer.Option(
        None,
        "--operation",
        "-o",
        help="Filter by operation type (query, update, delete, command, etc.)",
    ),
    limit: int = typer.Option(
        100,
        "--limit",
        "-l",
        help="Maximum number of results to return (default: 100)",
    ),
    output_csv: bool = typer.Option(
        True,
        "--output-csv/--no-csv",
        help="Export results to CSV file",
    ),
):
    """Find slow queries from MongoDB profiler data.

    Analyzes the system.profile collection to identify slow operations
    based on execution time threshold. Helps identify performance bottlenecks.
    """
    from mongodb_profiler_tools.slow_queries import analyze_slow_queries, export_slow_queries_to_csv, print_slow_queries

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
        logger.info(f"Threshold: {threshold}ms")
        logger.info("=" * 60)

        # Connect to MongoDB
        with get_mongo_client(mongodb_uri=settings.mongodb_uri, database_name=settings.database_name) as client:
            db = client[settings.database_name]

            # Analyze slow queries
            logger.info("Analyzing slow queries...")
            slow_ops = analyze_slow_queries(
                db=db,
                threshold_ms=threshold,
                collection_filter=collection,
                operation_filter=operation,
                limit=limit,
            )

            logger.info(f"Found {len(slow_ops)} slow operations")

            # Display results
            print_slow_queries(slow_ops, threshold)

            # Export to CSV if requested
            if output_csv and slow_ops:
                output_dir = Path(settings.paths.data_output) / "mongodb_profiler_tools"
                logger.info("Exporting to CSV...")
                csv_path = export_slow_queries_to_csv(
                    slow_ops,
                    output_dir,
                    settings.database_name,
                )
                logger.info(f"Exported to: {csv_path}")
                print(f"\n📄 CSV exported to: {csv_path}")

            logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        raise typer.Exit(code=1)


@app.command("profiler-stats")
def profiler_stats(
    env: str = typer.Option(
        None,
        "--env",
        help="Environment to use (DEV, PROD, STG, etc.) - overrides APP_ENV",
    ),
):
    """Get MongoDB profiler statistics.

    Shows profiling collection size, document count, and time range covered.
    """
    from mongodb_profiler_tools.profiler_stats import get_profiler_stats, print_profiler_stats

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
        logger.info("=" * 60)

        # Connect to MongoDB
        with get_mongo_client(mongodb_uri=settings.mongodb_uri, database_name=settings.database_name) as client:
            db = client[settings.database_name]

            # Get profiler stats
            logger.info("Getting profiler statistics...")
            stats = get_profiler_stats(db)

            # Display results
            print_profiler_stats(stats)

            logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        raise typer.Exit(code=1)


@app.callback()
def main():
    """MongoDB profiler tools for analyzing slow queries and profiling statistics.

    Run 'python run.py --help' to see available commands.
    """
    pass


if __name__ == "__main__":
    app()
