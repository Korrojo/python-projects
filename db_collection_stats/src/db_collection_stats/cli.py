"""CLI interface for db_collection_stats with multiple commands."""

import os
from pathlib import Path

import typer

from common_config.config.settings import get_settings
from common_config.connectors.mongodb import get_mongo_client
from common_config.utils.logger import get_logger, setup_logging
from common_config.utils.security import redact_uri

from db_collection_stats.collector import gather_all_collections_stats
from db_collection_stats.exporter import export_to_csv, export_index_stats_to_csv, print_summary

app = typer.Typer(
    help="MongoDB database statistics and analysis tools",
    no_args_is_help=True,
)


@app.command("coll-stats")
def coll_stats(
    env: str = typer.Option(
        None,
        "--env",
        help="Environment to use (DEV, PROD, STG, etc.) - overrides APP_ENV",
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
    """Gather statistics for all collections in the database.

    Collects document counts, sizes, storage info, and index details
    for each collection. Prints summary to console and optionally
    exports to CSV.
    """
    # Set environment if provided
    if env:
        os.environ["APP_ENV"] = env.upper()

    settings = get_settings()
    log_dir = Path(settings.paths.logs) / "db_collection_stats"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir)
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info("db_collection_stats - Collection Statistics")
    logger.info("=" * 60)

    try:
        with get_mongo_client(
            mongodb_uri=settings.mongodb_uri, database_name=settings.database_name
        ) as client:
            logger.info(f"Environment: {env.upper() if env else os.environ.get('APP_ENV', 'default')}")
            logger.info(f"MongoDB URI: {redact_uri(settings.mongodb_uri)}")
            logger.info(f"Database: {settings.database_name}")
            logger.info(f"Exclude system collections: {exclude_system}")

            # Gather statistics
            logger.info("Gathering collection statistics...")
            stats_list = gather_all_collections_stats(
                client, settings.database_name, exclude_system=exclude_system
            )

            logger.info(f"Found {len(stats_list)} collections")

            # Print summary
            print_summary(stats_list, settings.database_name)

            # Export to CSV
            if output_csv:
                output_dir = Path(settings.paths.data_output) / "db_collection_stats"
                logger.info("Exporting to CSV...")
                csv_path = export_to_csv(stats_list, output_dir, settings.database_name)
                logger.info(f"CSV exported to: {csv_path}")
                print(f"\n✅ CSV file saved to: {csv_path}\n")
            else:
                logger.info("CSV export skipped (--no-csv)")

            logger.info("=" * 60)
            logger.info("Completed successfully")
            logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command("index-stats")
def index_stats(
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
        help="Exclude system collections",
    ),
    show_unused: bool = typer.Option(
        False,
        "--show-unused",
        help="Highlight indexes with zero usage",
    ),
    output_csv: bool = typer.Option(
        True,
        "--output-csv/--no-csv",
        help="Export results to CSV file",
    ),
):
    """Analyze index usage statistics for collections.

    Shows index names, key patterns, and usage statistics (operations count).
    Helps identify unused or underutilized indexes that could be removed.

    Note: Index usage statistics are reset when MongoDB restarts.
    """
    # Set environment if provided
    if env:
        os.environ["APP_ENV"] = env.upper()

    settings = get_settings()
    log_dir = Path(settings.paths.logs) / "db_collection_stats"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir)
    logger = get_logger(__name__)

    logger.info("=" * 60)
    logger.info("db_collection_stats - Index Statistics")
    logger.info("=" * 60)

    try:
        with get_mongo_client(
            mongodb_uri=settings.mongodb_uri, database_name=settings.database_name
        ) as client:
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

            # Collect index data for CSV export
            all_index_data = []

            # Analyze each collection
            print("\n" + "=" * 100)
            print(f"Index Statistics for Database: {settings.database_name}")
            print("=" * 100)

            for coll_name in sorted(collections):
                try:
                    coll = db[coll_name]

                    # Get index information
                    indexes = list(coll.list_indexes())

                    # Get index usage stats (requires MongoDB 3.2+)
                    try:
                        index_stats = list(coll.aggregate([{"$indexStats": {}}]))
                    except Exception:
                        index_stats = []

                    # Create usage lookup
                    usage_lookup = {stat["name"]: stat.get("accesses", {}).get("ops", 0) for stat in index_stats}

                    # Print collection header
                    print(f"\n📊 Collection: {coll_name} ({len(indexes)} indexes)")
                    print("-" * 100)

                    # Print each index and collect data
                    for idx in indexes:
                        idx_name = idx["name"]
                        idx_key = idx["key"]
                        usage_count = usage_lookup.get(idx_name, "N/A")

                        # Format key pattern
                        key_str = ", ".join([f"{k}: {v}" for k, v in idx_key.items()])

                        # Check if unused
                        is_unused = usage_count == 0 if isinstance(usage_count, int) else False
                        unused_marker = "⚠️  UNUSED" if is_unused and show_unused else ""

                        print(f"  • {idx_name:30} | Keys: {key_str:40} | Usage: {usage_count:>10} {unused_marker}")

                        # Collect for CSV
                        all_index_data.append({
                            "collection_name": coll_name,
                            "index_name": idx_name,
                            "index_keys": key_str,
                            "usage_count": usage_count if usage_count != "N/A" else "",
                            "is_unused": "Yes" if is_unused else "No",
                        })

                    logger.info(f"Analyzed {coll_name}: {len(indexes)} indexes")

                except Exception as e:
                    logger.warning(f"Failed to analyze {coll_name}: {e}")
                    print(f"\n⚠️  Failed to analyze {coll_name}: {e}")

            print("\n" + "=" * 100)
            print("\n💡 Tips:")
            print("  - Indexes with 0 usage may be candidates for removal")
            print("  - Usage stats reset when MongoDB restarts")
            print("  - Use --show-unused to highlight unused indexes")
            print("  - Use --collection <name> to analyze specific collection\n")

            # Export to CSV
            if output_csv and all_index_data:
                output_dir = Path(settings.paths.data_output) / "db_collection_stats"
                logger.info("Exporting to CSV...")
                csv_path = export_index_stats_to_csv(all_index_data, output_dir, settings.database_name)
                logger.info(f"CSV exported to: {csv_path}")
                print(f"✅ CSV file saved to: {csv_path}\n")
            elif not all_index_data:
                logger.info("No index data to export")
            else:
                logger.info("CSV export skipped (--no-csv)")

            logger.info("Completed successfully")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        raise typer.Exit(code=1)


@app.callback()
def main():
    """MongoDB database statistics and analysis tools.

    Run 'python run.py --help' to see available commands.
    """
    pass


if __name__ == "__main__":
    app()
