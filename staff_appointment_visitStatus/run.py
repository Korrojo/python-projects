"""Unified CLI for staff_appointment_visitStatus - MongoDB StaffAvailability query tools.

Example usage:
    # Query single appointment
    python run.py query --athena-id 10025 --patient-ref 7010699

    # Query from CSV/Excel file
    python run.py query --input sample_input.xlsx

    # Generate visit status report
    python run.py report --input input.csv --output output.csv
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import argparse
from typing import Optional

import typer

from common_config.config.settings import get_settings
from common_config.utils.logger import setup_logging

app = typer.Typer(help="StaffAvailability MongoDB Query Tools")


@app.command()
def query(
    athena_id: Optional[int] = typer.Option(None, "--athena-id", help="AthenaAppointmentId to query"),
    patient_ref: Optional[int] = typer.Option(None, "--patient-ref", help="PatientRef to query"),
    input_file: Optional[str] = typer.Option(
        None, "--input", "-i", help="Input CSV/Excel file (first 2 columns: AthenaAppointmentId, PatientRef)"
    ),
    output_csv: Optional[str] = typer.Option(None, "--output", "-o", help="Output CSV file path"),
    collection: str = typer.Option("StaffAvailability", "--collection", "-c", help="MongoDB collection name"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment override (PROD, LOCL, etc.)"),
):
    """Run aggregation query on StaffAvailability collection.

    Query a single appointment with --athena-id and --patient-ref, OR
    batch query from --input file (CSV/Excel with 2 columns).
    """
    import os

    # Setup
    setup_logging()
    if env:
        os.environ["APP_ENV"] = env.upper()

    # Validate input
    if not input_file and (not athena_id or not patient_ref):
        typer.echo("❌ Error: Must provide either --input file OR both --athena-id and --patient-ref")
        raise typer.Exit(code=1)

    if input_file and (athena_id or patient_ref):
        typer.echo("❌ Error: Cannot use --input file with --athena-id/--patient-ref")
        raise typer.Exit(code=1)

    # Build command line args to pass to the original script
    cmd_args = ["--collection", collection]
    if athena_id:
        cmd_args.extend(["--athena_id", str(athena_id)])
    if patient_ref:
        cmd_args.extend(["--patient_ref", str(patient_ref)])
    if input_file:
        cmd_args.extend(["--input_file", input_file])
    if output_csv:
        cmd_args.extend(["--output_csv", output_csv])

    # Temporarily replace sys.argv and run
    import sys
    original_argv = sys.argv
    try:
        sys.argv = ["agg_query_runner.py"] + cmd_args
        from agg_query_runner import main as run_query  # type: ignore[import-not-found]
        run_query()
    finally:
        sys.argv = original_argv


@app.command()
def report(
    input_file: str = typer.Option(..., "--input", "-i", help="Input CSV file with appointment data"),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output CSV file path (default: data/output/)"
    ),
    collection: str = typer.Option("StaffAvailability", "--collection", "-c", help="MongoDB collection name"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment override (PROD, LOCL, etc.)"),
):
    """Generate VisitStatus report from input CSV.

    Input CSV must have header: PatientRef, VisitTypeValue, AthenaAppointmentId, AvailabilityDate, VisitStatus
    Output CSV will have VisitStatus populated from MongoDB.
    """
    import os

    # Setup
    setup_logging()
    if env:
        os.environ["APP_ENV"] = env.upper()

    # Build command line args to pass to the original script
    cmd_args = ["--input_file", input_file, "--collection", collection]
    if output_file:
        cmd_args.extend(["--output_csv", output_file])

    # Temporarily replace sys.argv and run
    import sys
    original_argv = sys.argv
    try:
        sys.argv = ["visit_status_report.py"] + cmd_args
        from visit_status_report import main as run_report  # type: ignore[import-not-found]
        run_report()
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    app()
