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

import csv
import os
from datetime import datetime
from typing import Any, Dict, List

import click

from common_config.config.settings import get_settings
from common_config.connectors.mongodb import get_mongo_client
from common_config.utils.logger import get_logger

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


def read_input_csv(path: str) -> List[Dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows


def batch(iterable, n=1):
    length = len(iterable)
    for ndx in range(0, length, n):
        yield iterable[ndx : min(ndx + n, length)]


def build_pipeline(ids: List[int]) -> List[Dict[str, Any]]:
    # Basic pipeline matching appointment ids and projecting the fields we need
    # Add AvailabilityDate range filter: 10/27/2025 to 10/30/2025
    return [
        {"$match": {
            "Slots.Appointments.0": {"$exists": True},
            "IsActive": True,
            "Slots.Appointments.AthenaAppointmentId": {"$in": ids},
            "AvailabilityDate": {
                "$gte": datetime(2025, 10, 27),
                "$lte": datetime(2025, 10, 30)
            }
        }},
        {"$unwind": "$Slots"},
        {"$unwind": "$Slots.Appointments"},
        {"$match": {"Slots.Appointments.AthenaAppointmentId": {"$in": ids}}},
        {"$project": {"_id": 0,
                      "AthenaAppointmentId": "$Slots.Appointments.AthenaAppointmentId",
                      "VisitTypeValue": "$Slots.Appointments.VisitTypeValue",
                      "AvailabilityDate": "$AvailabilityDate",
                      "VisitStatus": "$Slots.Appointments.VisitStatus",
                      "UpdatedOn": "$Slots.Appointments.UpdatedOn",
                      "InsertedOn": "$InsertedOn"
                      }},
        {"$sort": {"UpdatedOn": -1}},
    ]


def process_batch_results(results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    # Map key: "{aid}|{visitType}"
    mapping: Dict[str, List[Dict[str, Any]]] = {}
    for doc in results:
        aid = doc.get("AthenaAppointmentId")
        vt = doc.get("VisitTypeValue") or ""
        key = f"{aid}|{vt}"
        mapping.setdefault(key, []).append(doc)
    return mapping


def write_output(path: str, input_rows: List[Dict[str, Any]], mapping: Dict[str, List[Dict[str, Any]]]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in input_rows:
            aid = row.get("AthenaAppointmentId")
            vt = row.get("VisitTypeValue") or ""
            out = {col: "" for col in OUTPUT_COLUMNS}
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


@click.command()
@click.option("--input", "input_path", required=True, help="Input CSV path")
@click.option("--collection", "collection", default=None, help="Collection name")
@click.option("--env", "env", default=None, help="Environment (DEV, PROD, STG)")
@click.option("--batch-size", default=1000, help="Batch size for queries")
def main(input_path, collection, env, batch_size):
    if env:
        os.environ["APP_ENV"] = env.upper()

    ensure_dirs()
    from pathlib import Path
    from common_config.utils.logger import setup_logging

    settings = get_settings()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = os.path.join(OUTPUT_DIR, f"{timestamp}_by_visittype_{settings.database_name or 'DB'}.csv")
    log_file = os.path.join(LOG_DIR, f"{timestamp}_by_visittype_{settings.database_name or 'DB'}.log")
    setup_logging(log_dir=Path(LOG_DIR), file_name=os.path.basename(log_file))
    logger = get_logger(__name__)

    logger.info(f"Simple export by VisitTypeValue starting: input={input_path}, collection={collection}, env={os.environ.get('APP_ENV')}")

    if not collection:
        logger.error("Collection name is missing. Please provide --collection <name>.")
        click.echo("Error: Collection name is missing. Please provide --collection <name>.", err=True)
        raise click.Abort()

    rows = read_input_csv(input_path)
    # quick validation: check required columns exist and types
    missing_cols = []
    for col in ("AthenaAppointmentId", "VisitTypeValue"):
        if not rows or col not in rows[0]:
            missing_cols.append(col)
    if missing_cols:
        logger.error(f"Missing required columns in input CSV: {missing_cols}")
        raise click.Abort()

    # Build id list, skip rows with empty or non-numeric IDs
    valid_rows = []
    ids = []
    for r in rows:
        aid = r.get("AthenaAppointmentId")
        if not aid:
            logger.warning(f"Skipping row with empty AthenaAppointmentId: {r}")
            continue
        try:
            aid_int = int(aid)
            ids.append(aid_int)
            valid_rows.append(r)
        except Exception:
            logger.warning(f"Skipping row with non-numeric AthenaAppointmentId: {aid}")

    mapping: Dict[str, List[Dict[str, Any]]] = {}
    current_env = os.environ.get("APP_ENV", "DEV")
    with get_mongo_client(env=current_env, mongodb_uri=settings.mongodb_uri, database_name=settings.database_name) as client:
        db = client[settings.database_name]
        coll = db[collection]
        for batch_ids in batch(ids, batch_size):
            pipeline = build_pipeline(batch_ids)
            results = list(coll.aggregate(pipeline))
            batch_map = process_batch_results(results)
            mapping.update(batch_map)

    write_output(out_file, valid_rows, mapping)
    logger.info(f"Simple export complete. Output saved to {out_file}")


if __name__ == "__main__":
    main()
