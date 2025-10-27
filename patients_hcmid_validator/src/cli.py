from __future__ import annotations

import os
from pathlib import Path

import typer
from runner_csv import run_validation
from runner_excel import run_validation_excel

from common_config.config.settings import get_settings
from common_config.utils.logger import get_logger, get_run_timestamp, setup_logging

app = typer.Typer(help="Patients HcmId validator - validate CSV rows against MongoDB Patients collection")


def _resolve_input_path(path: str) -> Path:
    p = Path(path)
    if not p.exists():
        typer.echo(f"[ERROR] Input file not found: {p}", err=True)
        raise typer.Exit(code=3)
    return p


def _default_batch_size() -> int:
    try:
        settings = get_settings()
        proc = getattr(settings, "processing", None)
        return int(getattr(proc, "batch_size", 1000)) if proc else 1000
    except Exception:
        return 1000


@app.command()
def validate(
    input: str = typer.Option(..., "--input", help="Input CSV or Excel file path"),
    collection: str = typer.Option("Patients", "--collection", help="Mongo collection name"),
    batch_size: int | None = typer.Option(
        None, "--batch-size", min=1, help="Override batch size (default from shared config)"
    ),
    limit: int | None = typer.Option(None, "--limit", help="Process only first N rows (debug)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Do everything except write output CSV"),
    progress_every: int = typer.Option(10000, "--progress-every", help="Log progress every N rows"),
    output: str | None = typer.Option(None, "--output", help="Explicit output CSV path (else timestamp pattern)"),
    mongodb_env: str = typer.Option(
        "LOCL", "--mongodb-env", help="Environment suffix for MONGODB_URI_ and DATABASE_NAME_ (e.g., LOCL)"
    ),
    max_retries: int = typer.Option(3, "--max-retries", help="Max Mongo batch query retries"),
    base_retry_sleep: float = typer.Option(0.5, "--base-retry-sleep", help="Initial backoff sleep seconds"),
    debug: bool = typer.Option(False, "--debug", help="Verbose debug: log batch queries & unmatched details"),
    dob_two_digit_pivot: int = typer.Option(
        30,
        "--dob-two-digit-pivot",
        min=1,
        max=99,
        help="(If strategy=pivot) YY < pivot -> 2000+YY else 1900+YY. NOT used when strategy=senior (default).",
    ),
    dob_century_strategy: str = typer.Option(
        "senior",
        "--dob-century-strategy",
        help="Century rule for 2-digit years: senior (YY 00-49 => 1900s), pivot (use pivot), force1900, force2000",
    ),
    input_format: str | None = typer.Option(
        None,
        "--input-format",
        help="Force input format: csv, excel (default: auto-detect from file extension)",
    ),
    excel_sheet: str | None = typer.Option(
        None,
        "--excel-sheet",
        help="Excel sheet name to process (default: active sheet). Only used with Excel files.",
    ),
):
    """Run validation for a CSV or Excel file."""
    # Set APP_ENV for suffix resolution (shared_config/.env already loaded via common_config)
    os.environ["APP_ENV"] = mongodb_env.upper()

    run_ts = get_run_timestamp()
    settings = get_settings()
    log_dir = Path(settings.paths.logs) / "patients_hcmid_validator"  # type: ignore
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_dir=log_dir, file_name=f"{run_ts}_app.log")
    logger = get_logger(__name__)

    input_path = _resolve_input_path(input)

    # Derive output path
    if output:
        out_path = Path(output)
    else:
        out_dir = Path(settings.paths.data_output) / "patients_hcmid_validator"  # type: ignore
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{run_ts}_output.csv"

    effective_batch_size = batch_size if batch_size is not None else _default_batch_size()

    # Determine input format
    if input_format:
        detected_format = input_format.lower()
    else:
        # Auto-detect from file extension
        ext = input_path.suffix.lower()
        if ext == ".csv":
            detected_format = "csv"
        elif ext in [".xlsx", ".xls"]:
            detected_format = "excel"
        else:
            typer.echo(
                f"[ERROR] Cannot determine file format from extension '{ext}'. Use --input-format to specify.", err=True
            )
            raise typer.Exit(code=3)

    try:
        if detected_format == "csv":
            # Use CSV runner
            summary = run_validation(
                input_csv=input_path,
                output_csv=out_path,
                collection_name=collection,
                batch_size=effective_batch_size,
                limit=limit,
                dry_run=dry_run,
                progress_every=progress_every,
                mongodb_env=mongodb_env,
                max_retries=max_retries,
                base_retry_sleep=base_retry_sleep,
                debug=debug,
                dob_two_digit_pivot=dob_two_digit_pivot,
                dob_century_strategy=dob_century_strategy,
            )
        elif detected_format == "excel":
            # Use Excel runner
            summary = run_validation_excel(
                input_file=input_path,
                output_csv=out_path,
                collection_name=collection,
                batch_size=effective_batch_size,
                limit=limit,
                dry_run=dry_run,
                progress_every=progress_every,
                mongodb_env=mongodb_env,
                max_retries=max_retries,
                base_retry_sleep=base_retry_sleep,
                excel_sheet=excel_sheet if excel_sheet is not None else None,  # type: ignore[arg-type]
                debug=debug,
            )
        else:
            typer.echo(f"[ERROR] Unsupported input format: {detected_format}", err=True)
            raise typer.Exit(code=3)

    except Exception as e:
        logger.exception("Validation failed")
        raise typer.Exit(code=2) from e

    logger.info("Run summary: %s", summary)
    if dry_run:
        typer.echo("[DRY-RUN] Completed (no output written)")
    else:
        typer.echo(f"Output written to: {out_path}")
        if "mismatches_csv" in summary:
            typer.echo(f"Mismatches CSV written to: {summary['mismatches_csv']}")


def main():  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
