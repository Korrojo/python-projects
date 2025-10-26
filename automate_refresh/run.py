"""Unified CLI for automate_refresh - MongoDB collection export/import tool.

Example usage:
    # Export collection
    python run.py export --collection Users --env prod

    # Import collection
    python run.py import --collection Users --file backup.json.zip --env locl

    # Export with limit (for testing)
    python run.py export --collection Users --env prod --limit 100
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

import os
from typing import Optional

import typer

from common_config.config.settings import get_settings
from common_config.utils.logger import get_logger, setup_logging

app = typer.Typer(help="MongoDB Collection Export/Import Tool")


def _get_backup_dir() -> str:
    """Get backup directory from settings or environment."""
    settings = get_settings()
    backup_dir = getattr(settings.paths, "backup", None) or os.getenv("BACKUP_DIR_PROD") or "./mongo_exports"
    return backup_dir


@app.command()
def export(
    collection: str = typer.Option(..., "--collection", "-c", help="Collection name to export"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment (prod, locl, etc.)"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of documents (for testing)"),
    fraction: float = typer.Option(1.0, "--fraction", "-f", help="Fraction of documents to export (0.0-1.0)"),
    output_dir: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory (default: from settings)"),
):
    """Export a MongoDB collection to JSON (compressed as .zip)."""
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    # Set environment if provided
    if env:
        os.environ["APP_ENV"] = env.upper()
        logger.info(f"Set APP_ENV to {env.upper()}")

    # Import exporter here to use updated environment
    from automate_refresh.win.modules.exporter import export_sample

    # Load settings
    settings = get_settings()
    uri = settings.mongodb_uri
    db = settings.database_name
    backup_dir = output_dir or _get_backup_dir()

    # Validate required settings
    if not uri or not db:
        logger.error("Missing MongoDB URI or database name in settings")
        typer.echo("❌ Error: MongoDB URI or database name not configured")
        raise typer.Exit(code=1)

    logger.info(f"Starting export for collection: {collection}")
    logger.info(f"Database: {db}")
    logger.info(f"Output directory: {backup_dir}")

    if limit:
        logger.info(f"Limiting export to {limit} documents")
    if fraction < 1.0:
        logger.info(f"Exporting {fraction * 100}% of documents")

    # Export collection
    result = export_sample(
        uri=uri,
        database=db,
        collection_name=collection,
        fraction=fraction,
        limit=limit,
        out_dir=backup_dir,
    )

    logger.info(f"✅ Exported {result.written} documents to {result.out_path}")
    typer.echo(f"\n✅ Success! Exported {result.written} documents")
    typer.echo(f"📁 Output: {result.out_path}\n")


@app.command()
def import_collection(
    collection: str = typer.Option(..., "--collection", "-c", help="Collection name to import"),
    file: str = typer.Option(..., "--file", "-f", help="Input JSON or ZIP file path"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment (locl, dev, etc.)"),
    drop_first: bool = typer.Option(False, "--drop", help="Drop collection before import"),
):
    """Import a MongoDB collection from JSON (or .zip) file."""
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    # Set environment if provided
    if env:
        os.environ["APP_ENV"] = env.upper()
        logger.info(f"Set APP_ENV to {env.upper()}")

    # Import importer here to use updated environment
    from automate_refresh.mac.modules.importer import import_latest_file

    # Load settings
    settings = get_settings()
    uri = settings.mongodb_uri
    db = settings.database_name

    # Validate required settings
    if not uri or not db:
        logger.error("Missing MongoDB URI or database name in settings")
        typer.echo("❌ Error: MongoDB URI or database name not configured")
        raise typer.Exit(code=1)

    logger.info(f"Starting import for collection: {collection}")
    logger.info(f"Database: {db}")
    logger.info(f"Input file: {file}")

    if drop_first:
        logger.warning(f"Will DROP collection {collection} before import!")

    # Determine input directory from file path
    input_dir = str(Path(file).parent)

    # Import collection using import_latest_file
    result = import_latest_file(
        uri=uri,
        database=db,
        collection=collection,
        in_dir=input_dir,
        apply_indexes=True,
    )

    if result:
        logger.info(f"✅ Imported {result.rows_imported} documents")
        typer.echo(f"\n✅ Success! Imported {result.rows_imported} documents into {collection}")
    else:
        logger.warning("No matching file found to import")
        typer.echo("⚠️  Warning: No matching export file found")
    typer.echo()


if __name__ == "__main__":
    app()
