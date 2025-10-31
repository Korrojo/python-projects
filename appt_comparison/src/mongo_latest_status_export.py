"""
Script: mongo_latest_status_export.py
Purpose: Export latest appointment status for AthenaAppointmentId from MongoDB, following repo standards.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import typer

from common_config.config.settings import get_settings
from common_config.connectors.mongodb import get_mongo_client
from common_config.utils.logger import get_logger, setup_logging
from common_config.utils.security import redact_uri

BATCH_SIZE_DEFAULT = 1000
OUTPUT_DIR = "data/output/appt_comparison"
LOG_DIR = "logs/appt_comparison"

# Output columns
OUTPUT_COLUMNS = [
    "AthenaAppointmentId",
    "AvailabilityDate",
    "# of Dups",
    "InsertedOn",
    "VisitStatus",
    "InsertedOn.1",
    "VisitStatus.1",
    "InsertedOn.2",
    "VisitStatus.2",
    "Comment",
]


def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)


def read_input_csv(input_path: str) -> list[dict[str, Any]]:
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def get_min_max_dates(rows: list[dict[str, Any]]) -> tuple[str, str]:
    """Extract min and max dates from input rows.

    Args:
        rows: List of CSV rows containing AvailabilityDate

    Returns:
        Tuple of (min_date, max_date) in YYYY-MM-DD format

    Raises:
        ValueError: If date parsing fails
    """
    dates = [row["AvailabilityDate"] for row in rows if row.get("AvailabilityDate")]
    if not dates:
        raise ValueError("No valid AvailabilityDate values found in input CSV")

    dt_objs = []
    for d in dates:
        try:
            dt_objs.append(datetime.strptime(d, "%m/%d/%y"))
        except ValueError:
            # Try alternate format
            try:
                dt_objs.append(datetime.strptime(d, "%m/%d/%Y"))
            except ValueError:
                logger = get_logger(__name__)
                logger.warning(f"Could not parse date: {d}, skipping")

    if not dt_objs:
        raise ValueError("No valid dates could be parsed from input CSV")

    min_date = min(dt_objs).strftime("%Y-%m-%d")
    max_date = max(dt_objs).strftime("%Y-%m-%d")
    return min_date, max_date


def batch(iterable, n=1):
    length = len(iterable)
    for ndx in range(0, length, n):
        yield iterable[ndx : min(ndx + n, length)]


def build_pipeline(ids: list[Any], min_date: str, max_date: str) -> list[dict[str, Any]]:
    return [
        {
            "$match": {
                "Slots.Appointments.0": {"$exists": True},
                "AvailabilityDate": {
                    "$gte": datetime.strptime(min_date, "%Y-%m-%d"),
                    "$lt": datetime.strptime(max_date, "%Y-%m-%d"),
                },
            }
        },
        {"$unwind": "$Slots"},
        {"$unwind": "$Slots.Appointments"},
        {"$match": {"Slots.Appointments.AthenaAppointmentId": {"$in": ids}}},
        {
            "$project": {
                "_id": 0,
                "AthenaAppointmentId": "$Slots.Appointments.AthenaAppointmentId",
                "AvailabilityDate": "$AvailabilityDate",
                "InsertedOn": "$InsertedOn",
                "VisitStatus": "$Slots.Appointments.VisitStatus",
            }
        },
        {"$sort": {"InsertedOn": -1}},
    ]


def process_results(input_rows, mongo_results) -> dict[str, list[dict[str, Any]]]:
    # Group results by AthenaAppointmentId
    grouped = {}
    for doc in mongo_results:
        aid = doc.get("AthenaAppointmentId")
        if aid:
            grouped.setdefault(str(aid), []).append(doc)
    return grouped


def write_output_csv(output_path: str, input_rows, grouped_results):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in input_rows:
            aid = str(row["AthenaAppointmentId"])
            avail_date = row["AvailabilityDate"]
            docs = grouped_results.get(aid, [])
            out = {
                "AthenaAppointmentId": aid,
                "AvailabilityDate": avail_date,
                "# of Dups": len(docs) if docs else 0,
                "InsertedOn": docs[0]["InsertedOn"] if len(docs) > 0 else "",
                "VisitStatus": docs[0]["VisitStatus"] if len(docs) > 0 else "",
                "InsertedOn.1": docs[1]["InsertedOn"] if len(docs) > 1 else "",
                "VisitStatus.1": docs[1]["VisitStatus"] if len(docs) > 1 else "",
                "InsertedOn.2": docs[2]["InsertedOn"] if len(docs) > 2 else "",
                "VisitStatus.2": docs[2]["VisitStatus"] if len(docs) > 2 else "",
                "Comment": "" if docs else "No match found",
            }
            writer.writerow(out)


app = typer.Typer(help="Export latest appointment status from MongoDB")


@app.command()
def main(
    input_file: str = typer.Option(..., "--input", "-i", help="Input CSV file path"),
    output_file: str | None = typer.Option(None, "--output", "-o", help="Output CSV file path (default: auto-generated)"),
    collection: str = typer.Option(..., "--collection", "-c", help="MongoDB collection name"),
    batch_size: int = typer.Option(BATCH_SIZE_DEFAULT, "--batch-size", help="Batch size for AthenaAppointmentId lookup"),
    log_file: str | None = typer.Option(None, "--log", "-l", help="Log file path (default: auto-generated)"),
    env: str | None = typer.Option(None, "--env", help="Environment to use (DEV, PROD, STG, etc.) - overrides APP_ENV"),
):
    """Export latest appointment status for each AthenaAppointmentId from MongoDB."""
    # Set environment if provided
    if env:
        os.environ["APP_ENV"] = env.upper()

    ensure_dirs()
    settings = get_settings()

    # Generate output file name if not provided
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_name = settings.database_name or "UnknownDB"
        output_file = os.path.join(OUTPUT_DIR, f"{timestamp}_latest_status_export_{db_name}.csv")

    # Generate log file name if not provided
    if not log_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_name = settings.database_name or "UnknownDB"
        log_file = os.path.join(LOG_DIR, f"{timestamp}_latest_status_export_{db_name}.log")

    log_dir = Path(os.path.dirname(log_file))
    log_filename = os.path.basename(log_file)
    setup_logging(log_dir=log_dir, file_name=log_filename)
    logger = get_logger(__name__)

    logger.info("=" * 80)
    logger.info("MongoDB Latest Status Export")
    logger.info("=" * 80)
    logger.info(f"Environment: {env.upper() if env else os.environ.get('APP_ENV', 'default')}")
    logger.info(f"MongoDB URI: {redact_uri(settings.mongodb_uri)}")
    logger.info(f"Database: {settings.database_name}")
    logger.info(f"Collection: {collection}")
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {output_file}")
    logger.info(f"Batch size: {batch_size}")

    try:
        with get_mongo_client(
            mongodb_uri=settings.mongodb_uri, database_name=settings.database_name
        ) as client:
            db = client[settings.database_name]
            coll = db[collection]

            logger.info("Reading input CSV...")
            input_rows = read_input_csv(input_file)
            logger.info(f"Found {len(input_rows)} rows in input CSV")

            logger.info("Determining date range from input...")
            min_date, max_date = get_min_max_dates(input_rows)
            logger.info(f"Date range: {min_date} to {max_date}")

            logger.info("Extracting AthenaAppointmentIds...")
            all_ids = [int(row["AthenaAppointmentId"]) for row in input_rows if row.get("AthenaAppointmentId")]
            logger.info(f"Found {len(all_ids)} valid IDs")

            grouped_results = {}
            batch_count = 0
            for batch_ids in batch(all_ids, batch_size):
                batch_count += 1
                logger.info(f"Processing batch {batch_count} ({len(batch_ids)} IDs)...")
                pipeline = build_pipeline(batch_ids, min_date, max_date)
                results = list(coll.aggregate(pipeline))
                logger.info(f"Batch {batch_count}: Found {len(results)} MongoDB documents")
                batch_grouped = process_results(input_rows, results)
                grouped_results.update(batch_grouped)

            logger.info("Writing output CSV...")
            write_output_csv(output_file, input_rows, grouped_results)
            logger.info(f"Export complete. Output saved to {output_file}")

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
