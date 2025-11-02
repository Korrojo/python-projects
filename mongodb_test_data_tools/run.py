#!/usr/bin/env python3
"""
MongoDB Test Data Generator CLI

Command-line interface for generating fake test data for MongoDB collections.
Migrated from JavaScript data_faker project to Python.

Author: Demesew Abebe
Version: 1.0.0
Date: 2025-11-02
"""

import os
import sys
import time
from pathlib import Path

import typer
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent directory to path for common_config import
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_generator import DataGenerator

from common_config.config.settings import get_settings

app = typer.Typer(help="MongoDB Test Data Generator - Generate fake data for testing")
console = Console()


def connect_to_database(
    connection_uri: str, database_name: str, max_retries: int = 5, retry_delay: int = 5
) -> tuple[MongoClient, any]:
    """
    Connect to MongoDB with retry logic.

    Args:
        connection_uri: MongoDB connection URI
        database_name: Database name to connect to
        max_retries: Maximum number of connection retry attempts
        retry_delay: Delay in seconds between retries

    Returns:
        Tuple of (MongoClient, Database)

    Raises:
        ConnectionError: If unable to connect after max retries
    """
    client = None
    for attempt in range(max_retries):
        try:
            console.print(f"[yellow]Connecting to MongoDB (attempt {attempt + 1}/{max_retries})...[/yellow]")
            client = MongoClient(connection_uri, serverSelectionTimeoutMS=5000)
            # Test connection
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
                raise ConnectionError(f"Unable to connect to MongoDB after {max_retries} attempts") from e

    raise ConnectionError("Unable to connect to database")


@app.command()
def generate(
    collection: str = typer.Option(..., "--collection", "-c", help="Target collection name"),
    total: int = typer.Option(100, "--total", "-t", help="Total number of documents to generate"),
    batch_size: int = typer.Option(10, "--batch-size", "-b", help="Number of documents per batch"),
    env: str = typer.Option("DEV", "--env", "-e", help="Environment (DEV, PROD, etc.)"),
    inserted_by: str = typer.Option("system", "--inserted-by", help="Username/system for insertedBy field"),
    seed: int | None = typer.Option(None, "--seed", help="Random seed for reproducible data"),
):
    """
    Generate fake test data and insert into MongoDB collection.

    Example:
        python mongodb_test_data_tools/run.py generate --collection Patients --total 100 --batch-size 10 --env DEV
    """
    console.print("\n[bold cyan]MongoDB Test Data Generator[/bold cyan]")
    console.print(f"[cyan]{'=' * 60}[/cyan]\n")

    # Load configuration
    try:
        # Set environment before loading settings
        os.environ["APP_ENV"] = env
        settings = get_settings()
        console.print(f"[green]✓ Loaded configuration for environment: {env}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Error loading configuration: {e}[/red]")
        raise typer.Exit(code=1)

    # Connect to database
    client = None
    try:
        client, db = connect_to_database(
            connection_uri=settings.mongodb_uri,
            database_name=settings.database_name,
            max_retries=5,
            retry_delay=5,
        )

        target_collection = db[collection]

        # Initialize data generator
        generator = DataGenerator(seed=seed)
        console.print(f"[green]✓ Data generator initialized{' (seed: ' + str(seed) + ')' if seed else ''}[/green]")

        # Calculate batches
        total_batches = (total + batch_size - 1) // batch_size
        console.print(f"\n[yellow]Generating {total} documents in {total_batches} batches...[/yellow]\n")

        # Generate and insert data in batches
        total_inserted = 0
        start_time = time.time()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Inserting documents...", total=total_batches)

            for batch_num in range(total_batches):
                # Determine documents for this batch
                docs_in_batch = min(batch_size, total - total_inserted)

                # Generate batch of documents
                documents = [generator.generate_mock_patient(inserted_by) for _ in range(docs_in_batch)]

                # Insert batch
                result = target_collection.insert_many(documents, ordered=False)
                inserted_count = len(result.inserted_ids)
                total_inserted += inserted_count

                progress.update(task, advance=1)
                console.print(
                    f"[green]✓ Batch {batch_num + 1}/{total_batches}: Inserted {inserted_count} documents "
                    f"(Total: {total_inserted}/{total})[/green]"
                )

        elapsed_time = time.time() - start_time
        docs_per_second = total_inserted / elapsed_time if elapsed_time > 0 else 0

        console.print(f"\n[bold green]{'=' * 60}[/bold green]")
        console.print("[bold green]✓ Generation Complete![/bold green]")
        console.print(f"[bold green]{'=' * 60}[/bold green]")
        console.print(f"[green]Total documents inserted: {total_inserted}[/green]")
        console.print(f"[green]Collection: {collection}[/green]")
        console.print(f"[green]Time elapsed: {elapsed_time:.2f} seconds[/green]")
        console.print(f"[green]Rate: {docs_per_second:.2f} docs/second[/green]\n")

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Operation cancelled by user[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console.print(f"\n[red]✗ Error during data generation: {e}[/red]")
        raise typer.Exit(code=1)
    finally:
        if client:
            client.close()
            console.print("[dim]Database connection closed[/dim]")


@app.command()
def info():
    """Display information about the test data generator."""
    console.print("\n[bold cyan]MongoDB Test Data Generator[/bold cyan]")
    console.print("[cyan]" + "=" * 60 + "[/cyan]\n")
    console.print("[yellow]Purpose:[/yellow] Generate realistic fake data for MongoDB testing")
    console.print("[yellow]Migrated from:[/yellow] JavaScript data_faker project")
    console.print("[yellow]Author:[/yellow] Demesew Abebe")
    console.print("[yellow]Version:[/yellow] 1.0.0\n")
    console.print("[green]Features:[/green]")
    console.print("  • Generate patient records with acuity intensity history")
    console.print("  • Batch insertion for performance")
    console.print("  • Connection retry logic")
    console.print("  • Environment-based configuration")
    console.print("  • Optional random seed for reproducibility\n")
    console.print("[green]Usage:[/green]")
    console.print("  python mongodb_test_data_tools/run.py generate --collection Patients --total 100 --env DEV\n")


if __name__ == "__main__":
    app()
