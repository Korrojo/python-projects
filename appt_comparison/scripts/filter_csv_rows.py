#!/usr/bin/env python3
"""Filter CSV rows based on column value.

This script filters rows in a CSV file based on a specific column value
and saves the result to a new CSV file.

Example usage:
    python appt_comparison/scripts/filter_csv_rows.py \\
        --input data/input/appt_comparison/input.csv \\
        --output data/output/appt_comparison/filtered.csv \\
        --column Comment2 \\
        --value "compare with staff availability history collection"
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer

from common_config.utils.logger import get_logger, setup_logging

app = typer.Typer()


@app.command()
def main(
    input_file: str = typer.Option(..., "--input", "-i", help="Input CSV file path"),
    output_file: str = typer.Option(..., "--output", "-o", help="Output CSV file path"),
    column: str = typer.Option(..., "--column", "-c", help="Column name to filter"),
    value: str = typer.Option(..., "--value", "-v", help="Filter value"),
):
    """Filter CSV rows based on column value."""
    # Setup logging
    setup_logging(log_dir=Path("logs/appt_comparison"))
    logger = get_logger(__name__)

    logger.info("Starting CSV filtering operation")

    try:
        # Convert paths to Path objects
        input_path = Path(input_file)
        output_path = Path(output_file)

        # Validate input file exists
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            raise typer.Exit(code=1)

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Read the CSV file
        logger.info(f"Reading CSV file: {input_path}")
        df = pd.read_csv(input_path)

        # Clean up column names
        df.columns = df.columns.str.strip()

        # Validate column exists
        if column not in df.columns:
            logger.error(f"Column '{column}' not found in CSV file")
            logger.error(f"Available columns: {', '.join(df.columns)}")
            raise typer.Exit(code=1)

        # Filter the DataFrame
        filtered_df = df[df[column].astype(str) == value]

        # Save the filtered DataFrame
        logger.info(f"Saving filtered data to: {output_path}")
        filtered_df.to_csv(output_path, index=False)

        # Log results
        logger.info("Successfully filtered the data")
        logger.info(f"Original rows: {len(df)}")
        logger.info(f"Filtered rows: {len(filtered_df)}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise typer.Exit(code=1)
    except KeyError as e:
        logger.error(f"Column not found: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
