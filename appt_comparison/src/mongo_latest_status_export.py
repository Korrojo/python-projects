"""
Script: mongo_latest_status_export.py
Purpose: Export latest appointment status for AthenaAppointmentId from MongoDB, following repo standards.
"""

import csv
import os
from datetime import datetime
from typing import Any

import click

from common_config.config.settings import get_settings
from common_config.connectors.mongodb import get_mongo_client
from common_config.utils.logger import get_logger

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


def get_min_max_dates(rows: list[dict[str, Any]]) -> (str, str):
    dates = [row["AvailabilityDate"] for row in rows if row["AvailabilityDate"]]
    dt_objs = [datetime.strptime(d, "%m/%d/%y") for d in dates]
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


@click.command()
@click.option("--input", "-i", required=True, help="Input CSV file path")
@click.option("--output", "-o", help="Output CSV file path (default: auto-generated)")
@click.option("--collection", "-c", required=True, help="MongoDB collection name")
@click.option("--batch-size", default=BATCH_SIZE_DEFAULT, help="Batch size for AthenaAppointmentId lookup")
@click.option("--log", "-l", help="Log file path (default: auto-generated)")
@click.option("--env", default=None, help="Environment to use (DEV, PROD, STG, etc.) - overrides APP_ENV")
def main(input, output, collection, batch_size, log, env):
    if env:
        os.environ["APP_ENV"] = env.upper()
    ensure_dirs()
    from pathlib import Path
    from common_config.utils.logger import setup_logging
    from datetime import datetime
    settings = get_settings()
    # Generate output file name if not provided
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_name = settings.database_name or "UnknownDB"
        output = os.path.join(OUTPUT_DIR, f"{timestamp}_latest_status_export_{db_name}.csv")
    # Generate log file name if not provided
    if not log:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_name = settings.database_name or "UnknownDB"
        log = os.path.join(LOG_DIR, f"{timestamp}_latest_status_export_{db_name}.log")
    log_dir = Path(os.path.dirname(log))
    log_file = os.path.basename(log)
    setup_logging(log_dir=log_dir, file_name=log_file)
    logger = get_logger()
    logger.info(f"Starting export: input={input}, output={output}, collection={collection}, env={env}")
    current_env = os.environ.get("APP_ENV", "DEV")
    with get_mongo_client(env=current_env, mongodb_uri=settings.mongodb_uri, database_name=settings.database_name) as client:
        db = client[settings.database_name]
        coll = db[collection]
        input_rows = read_input_csv(input)
        min_date, max_date = get_min_max_dates(input_rows)
        all_ids = [int(row["AthenaAppointmentId"]) for row in input_rows if row["AthenaAppointmentId"]]
        grouped_results = {}
        for batch_ids in batch(all_ids, batch_size):
            pipeline = build_pipeline(batch_ids, min_date, max_date)
            results = list(coll.aggregate(pipeline))
            batch_grouped = process_results(input_rows, results)
            grouped_results.update(batch_grouped)
        write_output_csv(output, input_rows, grouped_results)
        logger.info(f"Export complete. Output saved to {output}")


if __name__ == "__main__":
    main()
