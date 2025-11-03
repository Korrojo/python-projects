#!/usr/bin/env python3
"""
MongoDB PHI Masker - Main CLI entry point using Typer

Production-ready HIPAA-compliant PHI/PII masking tool.
Processes 4M+ documents with 8 PHI complexity categories.
"""

import typer
from pathlib import Path
from typing import Optional
import sys

# Import from masking.py to keep existing functionality
from masking import run_masking

app = typer.Typer(
    name="mongo-phi-masker",
    help="MongoDB PHI/PII Masking Tool - HIPAA Compliant",
    add_completion=False,
)


@app.command()
def mask(
    config: Path = typer.Option(
        ..., "--config", "-c", help="Path to configuration JSON file", exists=True
    ),
    env: Path = typer.Option(
        ..., "--env", "-e", help="Path to environment file (.env)", exists=True
    ),
    collection: Optional[str] = typer.Option(
        None, "--collection", help="Process specific collection (overrides config)"
    ),
    in_situ: bool = typer.Option(
        False, "--in-situ", help="Enable in-situ masking (irreversible!)"
    ),
    reset_checkpoint: bool = typer.Option(
        False, "--reset-checkpoint", help="Reset checkpoint and start fresh"
    ),
    log_file: Optional[Path] = typer.Option(
        None, "--log-file", help="Custom log file path"
    ),
):
    """
    Mask PHI/PII data in MongoDB collections.

    Examples:

        # Basic masking
        python run.py mask --config config.json --env .env.prod

        # In-situ masking (irreversible)
        python run.py mask --config config.json --env .env.prod --in-situ

        # Specific collection only
        python run.py mask --config config.json --env .env.prod --collection Patients
    """
    try:
        # Convert paths to strings for compatibility with existing code
        exit_code = run_masking(
            config_path=str(config),
            env_path=str(env),
            collection=collection,
            in_situ=in_situ,
            reset_checkpoint=reset_checkpoint,
            log_file=str(log_file) if log_file else None,
        )
        raise typer.Exit(code=exit_code)
    except KeyboardInterrupt:
        typer.secho("\n\n⚠️  Masking interrupted by user", fg=typer.colors.YELLOW)
        raise typer.Exit(code=130)
    except Exception as e:
        typer.secho(f"❌ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@app.command()
def info():
    """Show information about the PHI masker."""
    typer.echo("MongoDB PHI Masker")
    typer.echo("=" * 50)
    typer.echo("Production-ready HIPAA-compliant PHI/PII masking tool")
    typer.echo("")
    typer.echo("Features:")
    typer.echo("  • 4M+ documents successfully masked in production")
    typer.echo("  • 8 PHI complexity categories")
    typer.echo("  • Batch processing with checkpoints")
    typer.echo("  • In-situ and masking-in-motion modes")
    typer.echo("")
    typer.echo("For help: python run.py mask --help")


if __name__ == "__main__":
    app()
