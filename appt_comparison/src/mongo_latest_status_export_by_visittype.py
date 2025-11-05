"""
Simplified clone of mongo_latest_status_export.py tailored to input CSV with
`AthenaAppointmentId` and `VisitTypeValue`. It matches DB docs by AthenaAppointmentId
and selects the first document whose VisitTypeValue equals the input row's VisitTypeValue.

Design goals:
- Minimal changes from existing logic (clone)
- Quick validation of input columns and types
- Batch DB queries by AthenaAppointmentId, then lightweight Python filtering by VisitTypeValue
- Populate AvailabilityDate, VisitStatus, UpdatedOn columns in output CSV
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

# Locations
OUTPUT_DIR = "data/output/appt_comparison"
LOG_DIR = "logs/appt_comparison"

OUTPUT_COLUMNS = [
    "AthenaAppointmentId",
    "VisitTypeValue",
    "AvailabilityDate",
    "VisitStatus",
    "UpdatedOn",
    "PatientRef",
    "apptcheckoutdate",
    "Comment",
]


def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)


def read_input_csv(path: str) -> list[dict[str, str]]:
    """Read input CSV file."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows


def batch(iterable, n=1):
    """Yield successive n-sized chunks from iterable."""
    length = len(iterable)
    for ndx in range(0, length, n):
        yield iterable[ndx : min(ndx + n, length)]


def build_pipeline(
    ids: list[int],
    min_date: datetime | None = None,
    max_date: datetime | None = None,
) -> list[dict[str, Any]]:
    """Build MongoDB aggregation pipeline.

    Args:
        ids: List of AthenaAppointmentIds to match
        min_date: Optional minimum AvailabilityDate filter
        max_date: Optional maximum AvailabilityDate filter

    Returns:
        MongoDB aggregation pipeline
    """
    match_filter: dict[str, Any] = {
        "Slots.Appointments.0": {"$exists": True},
        "IsActive": True,
        "Slots.Appointments.AthenaAppointmentId": {"$in": ids},
    }

    # Add optional date range filter
    if min_date and max_date:
        match_filter["AvailabilityDate"] = {
            "$gte": min_date,
            "$lte": max_date,
        }

    return [
        {"$match": match_filter},
        {"$unwind": "$Slots"},
        {"$unwind": "$Slots.Appointments"},
        {"$match": {"Slots.Appointments.AthenaAppointmentId": {"$in": ids}}},
        {
            "$project": {
                "_id": 0,
                "AthenaAppointmentId": "$Slots.Appointments.AthenaAppointmentId",
                "VisitTypeValue": "$Slots.Appointments.VisitTypeValue",
                "AvailabilityDate": "$AvailabilityDate",
                "VisitStatus": "$Slots.Appointments.VisitStatus",
                "UpdatedOn": "$Slots.Appointments.UpdatedOn",
                "InsertedOn": "$InsertedOn",
            }
        },
        {"$sort": {"UpdatedOn": -1}},
    ]


def process_batch_results(results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group results by AthenaAppointmentId|VisitTypeValue key."""
    mapping: dict[str, list[dict[str, Any]]] = {}
    for doc in results:
        aid = doc.get("AthenaAppointmentId")
        vt = doc.get("VisitTypeValue") or ""
        key = f"{aid}|{vt}"
        mapping.setdefault(key, []).append(doc)
    return mapping


def write_output(path: str, input_rows: list[dict[str, str]], mapping: dict[str, list[dict[str, Any]]]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in input_rows:
            aid = row.get("AthenaAppointmentId") or ""
            vt = row.get("VisitTypeValue") or ""
            out = dict.fromkeys(OUTPUT_COLUMNS, "")
            out["AthenaAppointmentId"] = aid
            out["VisitTypeValue"] = vt
            out["PatientRef"] = row.get("PatientRef", "")
            out["apptcheckoutdate"] = row.get("apptcheckoutdate", "")
            key = f"{aid}|{vt}"
            docs = mapping.get(key)
            # fallback: try matching by id only
            if not docs:
                docs = mapping.get(f"{aid}|")
            if docs:
                # take the first (already sorted by UpdatedOn desc)
                doc = docs[0]
                # AvailabilityDate may be a datetime; format as MM/DD/YYYY if present
                ad = doc.get("AvailabilityDate")
                if isinstance(ad, datetime):
                    out["AvailabilityDate"] = ad.strftime("%m/%d/%Y")
                else:
                    out["AvailabilityDate"] = ad or ""
                out["VisitStatus"] = doc.get("VisitStatus") or ""
                u = doc.get("UpdatedOn") or doc.get("InsertedOn")
                out["UpdatedOn"] = u if u else ""
                out["Comment"] = ""
            else:
                out["Comment"] = "No match found"
            writer.writerow(out)


app = typer.Typer(help="Export appointment status by VisitTypeValue from MongoDB")


@app.command()
def main(
    input_file: str = typer.Option(..., "--input", "-i", help="Input CSV path"),
    collection: str = typer.Option(..., "--collection", "-c", help="MongoDB collection name"),
    env: str | None = typer.Option(None, "--env", help="Environment (DEV, PROD, STG, etc.) - overrides APP_ENV"),
    batch_size: int = typer.Option(1000, "--batch-size", help="Batch size for queries"),
    min_date: str | None = typer.Option(None, "--min-date", help="Minimum AvailabilityDate (YYYY-MM-DD)"),
    max_date: str | None = typer.Option(None, "--max-date", help="Maximum AvailabilityDate (YYYY-MM-DD)"),
):
    """Export appointment status matching by AthenaAppointmentId and VisitTypeValue."""
    # Set environment if provided
    if env:
        os.environ["APP_ENV"] = env.upper()

    ensure_dirs()
    settings = get_settings()

    # Generate output and log file names
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = settings.database_name or "DB"
    out_file = os.path.join(OUTPUT_DIR, f"{timestamp}_by_visittype_{db_name}.csv")
    log_file = os.path.join(LOG_DIR, f"{timestamp}_by_visittype_{db_name}.log")

    setup_logging(log_dir=Path(LOG_DIR), file_name=os.path.basename(log_file))
    logger = get_logger(__name__)

    logger.info("=" * 80)
    logger.info("MongoDB Export by VisitTypeValue")
    logger.info("=" * 80)
    logger.info(f"Environment: {env.upper() if env else os.environ.get('APP_ENV', 'default')}")
    logger.info(f"MongoDB URI: {redact_uri(settings.mongodb_uri)}")
    logger.info(f"Database: {settings.database_name}")
    logger.info(f"Collection: {collection}")
    logger.info(f"Input: {input_file}")
    logger.info(f"Output: {out_file}")
    logger.info(f"Batch size: {batch_size}")
    if min_date and max_date:
        logger.info(f"Date range: {min_date} to {max_date}")

    try:
        # Read and validate input CSV
        logger.info("Reading input CSV...")
        rows = read_input_csv(input_file)
        logger.info(f"Found {len(rows)} rows in input CSV")

        # Validate required columns
        missing_cols = []
        for col in ("AthenaAppointmentId", "VisitTypeValue"):
            if not rows or col not in rows[0]:
                missing_cols.append(col)
        if missing_cols:
            logger.error(f"Missing required columns in input CSV: {missing_cols}")
            raise typer.Exit(code=1)

        # Build id list, skip rows with empty or non-numeric IDs
        logger.info("Extracting and validating AthenaAppointmentIds...")
        valid_rows = []
        ids = []
        for r in rows:
            aid = r.get("AthenaAppointmentId")
            if not aid:
                logger.warning("Skipping row with empty AthenaAppointmentId")
                continue
            try:
                aid_int = int(aid)
                ids.append(aid_int)
                valid_rows.append(r)
            except Exception:
                logger.warning(f"Skipping row with non-numeric AthenaAppointmentId: {aid}")

        logger.info(f"Found {len(ids)} valid IDs out of {len(rows)} total rows")

        # Parse date range if provided
        min_dt = None
        max_dt = None
        if min_date and max_date:
            try:
                min_dt = datetime.strptime(min_date, "%Y-%m-%d")
                max_dt = datetime.strptime(max_date, "%Y-%m-%d")
            except ValueError as e:
                logger.error(f"Invalid date format: {e}. Use YYYY-MM-DD format.")
                raise typer.Exit(code=1) from e

        # Query MongoDB
        # Ensure database_name is set
        if not settings.database_name:
            logger.error("Database name not configured in settings")
            raise typer.Exit(code=1)

        mapping: dict[str, list[dict[str, Any]]] = {}
        with get_mongo_client(mongodb_uri=settings.mongodb_uri, database_name=settings.database_name) as client:
            db = client[settings.database_name]
            coll = db[collection]

            batch_count = 0
            for batch_ids in batch(ids, batch_size):
                batch_count += 1
                logger.info(f"Processing batch {batch_count} ({len(batch_ids)} IDs)...")
                pipeline = build_pipeline(batch_ids, min_dt, max_dt)
                results = list(coll.aggregate(pipeline))
                logger.info(f"Batch {batch_count}: Found {len(results)} MongoDB documents")
                batch_map = process_batch_results(results)
                mapping.update(batch_map)

        # Write output
        logger.info("Writing output CSV...")
        write_output(out_file, valid_rows, mapping)
        logger.info(f"Export complete. Output saved to {out_file}")

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
