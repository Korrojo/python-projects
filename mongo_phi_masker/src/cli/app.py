#!/usr/bin/env python3
"""
Typer-based CLI for MongoDB PHI Masker.

This module provides a modern, type-safe command-line interface using Typer.
It replaces the argparse-based CLI while maintaining backward compatibility.

Usage:
    phi-masker mask --config config.json --src-env LOCL --dst-env DEV --collection Patients
    phi-masker info --config config.json
    phi-masker validate --config config.json
"""

from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer

# Create the main Typer application
app = typer.Typer(
    name="phi-masker",
    help="MongoDB PHI Masker - HIPAA-compliant data masking for MongoDB",
    add_completion=False,
)


class Environment(str, Enum):
    """Supported environment codes."""

    LOCL = "LOCL"
    DEV = "DEV"
    STG = "STG"
    TRNG = "TRNG"
    PERF = "PERF"
    PRPRD = "PRPRD"
    PROD = "PROD"


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@app.command()
def mask(
    # Required arguments
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    # Environment-based configuration (new approach - recommended)
    src_env: Annotated[
        Optional[Environment],
        typer.Option(
            "--src-env",
            help="Source environment (loads from shared_config/.env)",
        ),
    ] = None,
    dst_env: Annotated[
        Optional[Environment],
        typer.Option(
            "--dst-env",
            help="Destination environment (loads from shared_config/.env)",
        ),
    ] = None,
    src_db: Annotated[
        Optional[str],
        typer.Option(
            "--src-db",
            help="Source database name (overrides DATABASE_NAME_{src_env})",
        ),
    ] = None,
    dst_db: Annotated[
        Optional[str],
        typer.Option(
            "--dst-db",
            help="Destination database name (overrides DATABASE_NAME_{dst_env})",
        ),
    ] = None,
    # Legacy environment file (for backward compatibility)
    env: Annotated[
        Optional[Path],
        typer.Option(
            "--env",
            "-e",
            help="Path to environment file (legacy mode, use --src-env instead)",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    # Collection and processing parameters
    collection: Annotated[
        Optional[str],
        typer.Option(
            "--collection",
            help="Specific collection to process (optional)",
        ),
    ] = None,
    limit: Annotated[
        Optional[int],
        typer.Option(
            "--limit",
            help="Maximum number of documents to process",
            min=1,
        ),
    ] = None,
    query: Annotated[
        Optional[str],
        typer.Option(
            "--query",
            "-q",
            help="MongoDB query to filter documents (JSON string)",
        ),
    ] = None,
    # Operation modes
    reset_checkpoint: Annotated[
        bool,
        typer.Option(
            "--reset-checkpoint",
            help="Reset checkpoint before processing",
        ),
    ] = False,
    verify_only: Annotated[
        bool,
        typer.Option(
            "--verify-only",
            help="Only verify results without processing",
        ),
    ] = False,
    in_situ: Annotated[
        bool,
        typer.Option(
            "--in-situ",
            help="Perform in-situ masking (modify documents in-place)",
        ),
    ] = False,
    # Batch processing
    batch_size: Annotated[
        Optional[int],
        typer.Option(
            "--batch-size",
            help="Override the default batch size from environment variable",
            min=1,
        ),
    ] = None,
    # Logging options
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug logging",
        ),
    ] = False,
    log_file: Annotated[
        Optional[Path],
        typer.Option(
            "--log-file",
            help="Custom log file path",
        ),
    ] = None,
    log_max_bytes: Annotated[
        int,
        typer.Option(
            "--log-max-bytes",
            help="Maximum log file size before rotation (bytes)",
        ),
    ] = 10485760,  # 10MB default
    log_backup_count: Annotated[
        int,
        typer.Option(
            "--log-backup-count",
            help="Number of backup log files to keep",
            min=0,
        ),
    ] = 5,
    log_timed_rotation: Annotated[
        bool,
        typer.Option(
            "--log-timed-rotation",
            help="Use time-based rotation instead of size-based",
        ),
    ] = False,
) -> None:
    """
    Mask PHI data in MongoDB collections.

    Reads unmasked data from source environment/database and writes
    masked data to destination environment/database.

    \b
    Examples:
        # Environment-based (recommended)
        phi-masker mask --config config.json --src-env LOCL --dst-env DEV --collection Patients

        # With database overrides
        phi-masker mask --config config.json --src-env DEV --dst-env DEV --src-db devdb --collection Patients

        # Legacy mode
        phi-masker mask --config config.json --env .env --collection Patients

        # With query filter and limit
        phi-masker mask --config config.json --src-env LOCL --dst-env DEV --query '{"active": true}' --limit 1000
    """
    # Validate environment configuration
    using_env_presets = src_env is not None or dst_env is not None
    using_legacy_env = env is not None

    if using_env_presets and using_legacy_env:
        typer.echo(
            "ERROR: Cannot use both --src-env/--dst-env and --env together. Choose one approach.",
            err=True,
        )
        raise typer.Exit(code=1)

    if not using_env_presets and not using_legacy_env:
        typer.echo(
            "ERROR: Must specify either --src-env/--dst-env (recommended) or --env (legacy)",
            err=True,
        )
        raise typer.Exit(code=1)

    if using_env_presets:
        if src_env is None or dst_env is None:
            typer.echo("ERROR: Both --src-env and --dst-env are required", err=True)
            raise typer.Exit(code=1)

    # Delegate to masking.py by building command-line arguments
    # This maintains backward compatibility and avoids refactoring masking.py
    import subprocess
    import sys
    from pathlib import Path as PathlibPath

    # Find masking.py in the project root
    project_root = PathlibPath(__file__).parent.parent.parent
    masking_script = project_root / "masking.py"

    if not masking_script.exists():
        typer.echo(f"ERROR: Could not find masking.py at {masking_script}", err=True)
        raise typer.Exit(code=1)

    # Build command-line arguments
    cmd = [sys.executable, str(masking_script), "--config", str(config)]

    # Add environment configuration
    if src_env:
        cmd.extend(["--src-env", src_env.value])
    if dst_env:
        cmd.extend(["--dst-env", dst_env.value])
    if src_db:
        cmd.extend(["--src-db", src_db])
    if dst_db:
        cmd.extend(["--dst-db", dst_db])
    if env:
        cmd.extend(["--env", str(env)])

    # Add processing parameters
    if collection:
        cmd.extend(["--collection", collection])
    if limit:
        cmd.extend(["--limit", str(limit)])
    if query:
        cmd.extend(["--query", query])

    # Add flags
    if reset_checkpoint:
        cmd.append("--reset-checkpoint")
    if verify_only:
        cmd.append("--verify-only")
    if debug:
        cmd.append("--debug")
    if in_situ:
        cmd.append("--in-situ")

    # Add batch processing
    if batch_size:
        cmd.extend(["--batch-size", str(batch_size)])

    # Add logging options
    if log_file:
        cmd.extend(["--log-file", str(log_file)])
    if log_max_bytes != 10 * 1024 * 1024:  # Only add if not default
        cmd.extend(["--log-max-bytes", str(log_max_bytes)])
    if log_backup_count != 5:  # Only add if not default
        cmd.extend(["--log-backup-count", str(log_backup_count)])
    if log_timed_rotation:
        cmd.append("--log-timed-rotation")

    # Execute masking.py
    result = subprocess.run(cmd)
    raise typer.Exit(code=result.returncode)


@app.command()
def info(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    src_env: Annotated[
        Optional[Environment],
        typer.Option("--src-env", help="Source environment"),
    ] = None,
    dst_env: Annotated[
        Optional[Environment],
        typer.Option("--dst-env", help="Destination environment"),
    ] = None,
    env: Annotated[
        Optional[Path],
        typer.Option(
            "--env",
            "-e",
            help="Path to environment file (legacy)",
            exists=True,
        ),
    ] = None,
) -> None:
    """
    Display configuration information.

    Shows loaded configuration, environment settings, and available collections.

    \b
    Example:
        phi-masker info --config config.json --src-env LOCL --dst-env DEV
    """
    typer.echo(f"Configuration file: {config}")
    typer.echo(f"Source environment: {src_env.value if src_env else 'N/A'}")
    typer.echo(f"Destination environment: {dst_env.value if dst_env else 'N/A'}")
    typer.echo(f"Legacy env file: {env if env else 'N/A'}")
    # TODO: Load and display actual configuration details
    typer.echo("\n[INFO command not fully implemented yet - placeholder]")


@app.command()
def validate(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
) -> None:
    """
    Validate configuration file.

    Checks configuration syntax, validates masking rules, and verifies
    that all required fields are present.

    \b
    Example:
        phi-masker validate --config config.json
    """
    typer.echo(f"Validating configuration: {config}")
    # TODO: Implement actual validation logic
    typer.echo("\n[VALIDATE command not fully implemented yet - placeholder]")


@app.command()
def version() -> None:
    """Display version information."""
    typer.echo("MongoDB PHI Masker v2.0.0")
    typer.echo("Typer-based CLI")


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
