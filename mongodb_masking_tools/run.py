#!/usr/bin/env python3
"""
MongoDB PHI/PII Data Masking CLI

Command-line interface for masking Protected Health Information (PHI) and
Personally Identifiable Information (PII) in MongoDB collections.

SECURITY CRITICAL: Handles sensitive data masking for compliance and testing.

Author: Demesew Abebe
Version: 1.0.0
Date: 2025-11-02
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from pymongo import MongoClient
from pymongo.errors import BulkWriteError, ConnectionFailure, ServerSelectionTimeoutError
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

# Add parent directory to path for common_config import
sys.path.insert(0, str(Path(__file__).parent.parent))

from common_config.config.settings import get_settings
from src.masking_engine import MaskingEngine

app = typer.Typer(help="MongoDB PHI/PII Data Masking - Mask sensitive data for compliance")
console = Console()


def connect_to_database(
    connection_uri: str, database_name: str, max_retries: int = 5, retry_delay: int = 5
) -> tuple[MongoClient, any]:
    """Connect to MongoDB with retry logic."""
    client = None
    for attempt in range(max_retries):
        try:
            console.print(
                f"[yellow]Connecting to MongoDB (attempt {attempt + 1}/{max_retries})...[/yellow]"
            )
            client = MongoClient(connection_uri, serverSelectionTimeoutMS=5000)
            client.admin.command("ping")
            db = client[database_name]
            console.print(f"[green]✓ Connected to database: {database_name}[/green]")
            return client, db
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            console.print(f"[red]✗ Connection attempt {attempt + 1} failed: {e}[/red]")
            if attempt < max_retries - 1:
                console.print(f"[yellow]Retrying in {retry_delay} seconds...[/yellow]")
                time.sleep(retry_delay)
            else:
                raise ConnectionError(
                    f"Unable to connect to MongoDB after {max_retries} attempts"
                ) from e

    raise ConnectionError("Unable to connect to database")


@app.command()
def add_flag(
    collection: Optional[str] = typer.Option(
        None, "--collection", "-c", help="Specific collection (if None, all collections)"
    ),
    env: str = typer.Option("DEV", "--env", "-e", help="Environment (DEV, PROD, etc.)"),
    dry_run: bool = typer.Option(True, "--dry-run/--execute", help="Dry run mode (default: True)"),
):
    """
    Add 'isMasked: false' field to documents that don't have it.

    This is Step 1 of the masking process. Must be run before mask command.

    Example:
        python run.py add-flag --collection Patients --env DEV --execute
        python run.py add-flag --env DEV --execute  # All collections
    """
    console.print(f"\n[bold cyan]MongoDB PHI/PII Masking - Add isMasked Flag[/bold cyan]")
    console.print(f"[cyan]{'=' * 60}[/cyan]\n")

    if dry_run:
        console.print("[yellow]⚠ DRY RUN MODE - No changes will be made[/yellow]\n")

    # Load configuration
    try:
        # Set environment before loading settings
        os.environ["APP_ENV"] = env
        settings = get_settings()
        console.print(f"[green]✓ Loaded configuration for environment: {env}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Error loading configuration: {e}[/red]")
        raise typer.Exit(code=1)

    # Safety check for PROD
    if env == "PROD":
        console.print(
            "\n[bold red]⚠ WARNING: You are about to modify PRODUCTION data![/bold red]\n"
        )
        if not Confirm.ask("[bold]Are you absolutely sure you want to continue?[/bold]"):
            console.print("[yellow]Operation cancelled by user[/yellow]")
            raise typer.Exit(code=0)

    # Connect to database
    client = None
    try:
        client, db = connect_to_database(
            connection_uri=settings.mongodb_uri,
            database_name=settings.database_name,
            max_retries=5,
            retry_delay=5,
        )

        # Get collections to process
        if collection:
            collections = [collection] if collection in db.list_collection_names() else []
            if not collections:
                console.print(f"[red]✗ Collection '{collection}' not found[/red]")
                raise typer.Exit(code=1)
        else:
            collections = db.list_collection_names()
            console.print(f"[yellow]Processing all {len(collections)} collections[/yellow]\n")

        start_time = time.time()
        total_modified = 0

        for coll_name in collections:
            coll = db[coll_name]
            count = coll.count_documents({})

            if count == 0:
                console.print(f"[dim]{coll_name}: Empty, skipping[/dim]")
                continue

            console.print(f"\n[cyan]Processing: {coll_name}[/cyan] ({count:,} documents)")

            if dry_run:
                # Count how many documents would be modified
                needs_flag = coll.count_documents({"isMasked": {"$exists": False}})
                console.print(f"[yellow]  Would add flag to {needs_flag:,} documents[/yellow]")
            else:
                # Add isMasked: false to documents that don't have it
                result = coll.update_many(
                    {"isMasked": {"$exists": False}}, {"$set": {"isMasked": False}}
                )
                total_modified += result.modified_count
                console.print(
                    f"[green]  ✓ Added flag to {result.modified_count:,} documents[/green]"
                )

        elapsed_time = time.time() - start_time

        console.print(f"\n[bold green]{'=' * 60}[/bold green]")
        if dry_run:
            console.print(f"[bold yellow]DRY RUN COMPLETE[/bold yellow]")
        else:
            console.print(f"[bold green]✓ Flag Addition Complete![/bold green]")
            console.print(f"[green]Total documents modified: {total_modified:,}[/green]")
        console.print(f"[green]Time elapsed: {elapsed_time:.2f} seconds[/green]\n")

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Operation cancelled by user[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console.print(f"\n[red]✗ Error during flag addition: {e}[/red]")
        raise typer.Exit(code=1)
    finally:
        if client:
            client.close()


@app.command()
def mask(
    collection: Optional[str] = typer.Option(
        None, "--collection", "-c", help="Specific collection (if None, all collections)"
    ),
    env: str = typer.Option("DEV", "--env", "-e", help="Environment (DEV, PROD, etc.)"),
    batch_size: int = typer.Option(200, "--batch-size", "-b", help="Documents per batch"),
    dry_run: bool = typer.Option(True, "--dry-run/--execute", help="Dry run mode (default: True)"),
    seed: Optional[int] = typer.Option(None, "--seed", help="Random seed (testing only)"),
):
    """
    Mask PHI/PII data in documents where isMasked=false.

    This is Step 2 of the masking process. Must run add-flag first.

    Example:
        python run.py mask --collection Patients --env DEV --execute
        python run.py mask --env DEV --execute  # All collections
    """
    console.print(f"\n[bold cyan]MongoDB PHI/PII Masking - Mask Sensitive Data[/bold cyan]")
    console.print(f"[cyan]{'=' * 60}[/cyan]\n")

    if dry_run:
        console.print("[yellow]⚠ DRY RUN MODE - No changes will be made[/yellow]\n")

    # Load configuration
    try:
        # Set environment before loading settings
        os.environ["APP_ENV"] = env
        settings = get_settings()
        console.print(f"[green]✓ Loaded configuration for environment: {env}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Error loading configuration: {e}[/red]")
        raise typer.Exit(code=1)

    # Safety check for PROD
    if env == "PROD":
        console.print(
            "\n[bold red]⚠ WARNING: You are about to PERMANENTLY MASK PRODUCTION data![/bold red]\n"
        )
        console.print(
            "[bold red]This operation is IRREVERSIBLE and will destroy original data![/bold red]\n"
        )
        if not Confirm.ask("[bold]Are you absolutely sure you want to continue?[/bold]"):
            console.print("[yellow]Operation cancelled by user[/yellow]")
            raise typer.Exit(code=0)

    # Connect to database
    client = None
    try:
        client, db = connect_to_database(
            connection_uri=settings.mongodb_uri,
            database_name=settings.database_name,
            max_retries=5,
            retry_delay=5,
        )

        # Initialize masking engine
        engine = MaskingEngine(seed=seed)
        console.print(
            f"[green]✓ Masking engine initialized{' (seed: ' + str(seed) + ')' if seed else ''}[/green]"
        )

        # Get collections to process
        if collection:
            collections = [collection] if collection in db.list_collection_names() else []
            if not collections:
                console.print(f"[red]✗ Collection '{collection}' not found[/red]")
                raise typer.Exit(code=1)
        else:
            collections = db.list_collection_names()
            console.print(f"[yellow]Processing all {len(collections)} collections[/yellow]\n")

        console.print(f"[yellow]Masking started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/yellow]\n")

        start_time = time.time()
        total_masked = 0

        for coll_name in collections:
            coll = db[coll_name]
            unmasked_count = coll.count_documents({"isMasked": False})

            if unmasked_count == 0:
                console.print(f"[dim]{coll_name}: No unmasked documents, skipping[/dim]")
                continue

            console.print(
                f"\n[cyan]Processing: {coll_name}[/cyan] ({unmasked_count:,} unmasked documents)"
            )

            if dry_run:
                console.print(f"[yellow]  Would mask {unmasked_count:,} documents[/yellow]")
                continue

            # Process in batches
            batch_count = 0
            documents_masked = 0

            while True:
                # Get batch of unmasked documents
                docs = list(coll.find({"isMasked": False}).limit(batch_size))

                if not docs:
                    break

                # Create bulk update operations
                bulk_ops = []
                for doc in docs:
                    # Mask the document
                    masked_doc = engine.mask_fields(doc.copy())
                    masked_doc["isMasked"] = True

                    # Remove _id from update (can't update _id)
                    masked_doc.pop("_id", None)

                    bulk_ops.append({"filter": {"_id": doc["_id"]}, "update": {"$set": masked_doc}})

                # Execute bulk update
                if bulk_ops:
                    try:
                        for op in bulk_ops:
                            coll.update_one(op["filter"], op["update"])
                        batch_count += 1
                        documents_masked += len(bulk_ops)
                        total_masked += len(bulk_ops)
                        console.print(
                            f"[green]  ✓ Batch {batch_count}: Masked {len(bulk_ops)} documents "
                            f"(Total: {documents_masked:,}/{unmasked_count:,})[/green]"
                        )
                    except BulkWriteError as e:
                        console.print(f"[red]  ✗ Error in batch {batch_count}: {e.details}[/red]")

            console.print(f"[green]  ✓ Completed {coll_name}: {documents_masked:,} documents masked[/green]")

        elapsed_time = time.time() - start_time

        console.print(f"\n[bold green]{'=' * 60}[/bold green]")
        console.print(f"[yellow]Masking ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/yellow]")
        if dry_run:
            console.print(f"[bold yellow]DRY RUN COMPLETE[/bold yellow]")
        else:
            console.print(f"[bold green]✓ Masking Complete![/bold green]")
            console.print(f"[green]Total documents masked: {total_masked:,}[/green]")
        console.print(f"[green]Time elapsed: {elapsed_time:.2f} seconds[/green]\n")

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Operation cancelled by user[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console.print(f"\n[red]✗ Error during masking: {e}[/red]")
        import traceback

        traceback.print_exc()
        raise typer.Exit(code=1)
    finally:
        if client:
            client.close()


@app.command()
def status(
    collection: Optional[str] = typer.Option(None, "--collection", "-c", help="Specific collection"),
    env: str = typer.Option("DEV", "--env", "-e", help="Environment (DEV, PROD, etc.)"),
):
    """
    Show masking status for collections.

    Example:
        python run.py status --collection Patients --env DEV
        python run.py status --env DEV  # All collections
    """
    console.print(f"\n[bold cyan]MongoDB PHI/PII Masking - Status Report[/bold cyan]")
    console.print(f"[cyan]{'=' * 60}[/cyan]\n")

    # Load configuration
    try:
        # Set environment before loading settings
        os.environ["APP_ENV"] = env
        settings = get_settings()
    except Exception as e:
        console.print(f"[red]✗ Error loading configuration: {e}[/red]")
        raise typer.Exit(code=1)

    # Connect to database
    client = None
    try:
        client, db = connect_to_database(
            connection_uri=settings.mongodb_uri,
            database_name=settings.database_name,
        )

        # Get collections
        if collection:
            collections = [collection] if collection in db.list_collection_names() else []
        else:
            collections = db.list_collection_names()

        # Create status table
        table = Table(title=f"Masking Status - {settings.database_name}")
        table.add_column("Collection", style="cyan")
        table.add_column("Total Docs", justify="right", style="yellow")
        table.add_column("Masked", justify="right", style="green")
        table.add_column("Unmasked", justify="right", style="red")
        table.add_column("No Flag", justify="right", style="dim")
        table.add_column("Status", justify="center")

        for coll_name in collections:
            coll = db[coll_name]
            total = coll.count_documents({})
            masked = coll.count_documents({"isMasked": True})
            unmasked = coll.count_documents({"isMasked": False})
            no_flag = coll.count_documents({"isMasked": {"$exists": False}})

            if total == 0:
                status = "[dim]Empty[/dim]"
            elif unmasked > 0:
                status = "[red]⚠ Pending[/red]"
            elif no_flag > 0:
                status = "[yellow]⚠ No Flag[/yellow]"
            else:
                status = "[green]✓ Complete[/green]"

            table.add_row(
                coll_name,
                f"{total:,}",
                f"{masked:,}",
                f"{unmasked:,}",
                f"{no_flag:,}",
                status,
            )

        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        raise typer.Exit(code=1)
    finally:
        if client:
            client.close()


@app.command()
def info():
    """Display information about the masking tool."""
    console.print("\n[bold cyan]MongoDB PHI/PII Data Masking Tool[/bold cyan]")
    console.print("[cyan]" + "=" * 60 + "[/cyan]\n")
    console.print("[yellow]Purpose:[/yellow] Mask PHI/PII data for compliance and testing")
    console.print("[yellow]Migrated from:[/yellow] JavaScript MASKING_SCRIPTS_PHI_PII")
    console.print("[yellow]Author:[/yellow] Demesew Abebe")
    console.print("[yellow]Version:[/yellow] 1.0.0\n")
    console.print("[red]⚠ SECURITY CRITICAL - Handle with care![/red]\n")
    console.print("[green]Workflow:[/green]")
    console.print("  1. add-flag  - Add isMasked: false to documents")
    console.print("  2. mask      - Mask PHI/PII data (IRREVERSIBLE)")
    console.print("  3. status    - Check masking status\n")
    console.print("[green]Usage:[/green]")
    console.print("  python run.py add-flag --collection Patients --env DEV --execute")
    console.print("  python run.py mask --collection Patients --env DEV --execute")
    console.print("  python run.py status --env DEV\n")


if __name__ == "__main__":
    app()
