#!/usr/bin/env python3
"""CLI interface for Excel patient validation."""

from pathlib import Path
from typing import Annotated

import typer

from common_config.utils.logger import get_logger
from patients_hcmid_validator.runner_excel import run_validation_excel

logger = get_logger(__name__)

app = typer.Typer(
    name="patients-hcmid-validator-excel",
    help="Validate patient Excel data against MongoDB collections with mismatches reporting.",
)


@app.command("validate")
def validate(
    input_excel: Annotated[Path, typer.Argument(help="Input Excel file to validate")],
    output_csv: Annotated[Path, typer.Argument(help="Output CSV file with validation results")],
    collection: Annotated[str, typer.Option("--collection", "-c", help="MongoDB collection name")] = "Patients",
    batch_size: Annotated[int | None, typer.Option("--batch-size", "-b", help="Batch size for MongoDB queries")] = None,
    limit: Annotated[int | None, typer.Option("--limit", "-l", help="Limit number of rows to process")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Run without writing output files")] = False,
    progress_every: Annotated[int, typer.Option("--progress-every", help="Log progress every N rows")] = 1000,
    mongodb_env: Annotated[str, typer.Option("--mongodb-env", help="MongoDB environment suffix")] = "prod",
    max_retries: Annotated[int, typer.Option("--max-retries", help="Maximum retry attempts for MongoDB queries")] = 3,
    base_retry_sleep: Annotated[
        float, typer.Option("--base-retry-sleep", help="Base sleep time between retries")
    ] = 0.5,
    excel_sheet: Annotated[
        str | None, typer.Option("--excel-sheet", help="Excel sheet name (defaults to active sheet)")
    ] = None,
    debug: Annotated[bool, typer.Option("--debug", help="Enable debug logging")] = False,
) -> None:
    """Validate Excel patient data against MongoDB collections.

    This command processes Excel files and validates patient records against MongoDB.
    It generates two output files:
    1. Main validation results CSV with Match Found and Comments columns
    2. Separate mismatches CSV with database values and mismatched field details

    The mismatches CSV contains all database values (HcmId, FirstName, LastName, Dob, Gender)
    plus a "Mismatched Field" column listing comma-separated field names that didn't match.

    Note: DOB fields in Excel input should be formatted as YYYY-MM-DD.
    No complex date parsing is performed for Excel inputs.
    """
    try:
        if not input_excel.exists():
            logger.error("Input Excel file does not exist: %s", input_excel)
            raise typer.Exit(1)

        summary = run_validation_excel(
            input_file=input_excel,
            output_csv=output_csv,
            collection_name=collection,
            batch_size=batch_size,
            limit=limit,
            dry_run=dry_run,
            progress_every=progress_every,
            mongodb_env=mongodb_env,
            max_retries=max_retries,
            base_retry_sleep=base_retry_sleep,
            excel_sheet=excel_sheet,
            debug=debug,
        )

        if not dry_run:
            logger.info("Validation completed successfully. Results written to: %s", output_csv)
            if summary.get("mismatches_csv"):
                logger.info("Mismatches written to: %s", summary["mismatches_csv"])
        else:
            logger.info("Dry run completed successfully")

    except Exception as e:
        logger.error("Validation failed: %s", e)
        if debug:
            import traceback

            traceback.print_exc()
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
