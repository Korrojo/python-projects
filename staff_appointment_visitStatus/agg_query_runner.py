#!/usr/bin/env python3
r"""
Minimal aggregation runner for StaffAvailability.

Replicates the refined pipeline from c:/Users/dabebe/projects/python/query/query_v2.js:
 - Initial $match with IsActive=true, AvailabilityDate >= 2025-06-30 (UTC), and nested $elemMatch
   to pre-filter documents using indexes
 - $project builds filteredSlots by mapping Slots and filtering Appointments to the
   target (AthenaAppointmentId, PatientRef)
 - $unwind filteredSlots twice to flatten to individual appointment rows
 - $project flattens appointment fields for easy consumption

Usage examples:
  # Single pair (debug)
  .venv\Scripts\python.exe agg_query_runner.py --athena_id 10025 --patient_ref 7010699

  # Batch from file (first two columns only: AthenaAppointmentId,PatientRef)
  .venv\Scripts\python.exe agg_query_runner.py --input_file .\sample_input_20251007.xlsx

You can override the connection string or DB/collection via CLI flags.
"""

import argparse
import csv
import json
import os
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from common_config.config.settings import get_settings
from common_config.db.connection import MongoDBConnection
from common_config.utils.logger import get_logger, setup_logging

DEFAULT_COLLECTION = "StaffAvailability"


def _to_jsonable(obj: Any) -> Any:
    """Convert datetimes recursively to ISO strings for clean console output."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, list):
        return [_to_jsonable(x) for x in obj]
    if isinstance(obj, tuple):
        return tuple(_to_jsonable(x) for x in obj)
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    return obj


# Hard-coded filters (do not pass via CLI)
HARD_CODED_IS_ACTIVE: bool = True
HARD_CODED_START_DATE: datetime = datetime(2025, 6, 30, 0, 0, 0, tzinfo=UTC)


FIELDNAMES = [
    "IsActive",
    "AvailabilityDate",
    "PatientName",
    "VisitTypeValue",
    "VisitStartDateTime",
    "VisitStartEndTime",
    "VisitActualStartDateTime",
    "VisitActualEndDateTime",
    "VisitStatus",
    "UpdatedByName",
    "UpdatedOn",
    "AthenaAppointmentId",
    "PatientRef",
]


def _write_csv(out_path: str, results: list[dict[str, Any]]) -> None:
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for doc in results:
            row = {
                "IsActive": doc.get("IsActive"),
                "AvailabilityDate": doc.get("AvailabilityDate"),
                "PatientName": doc.get("PatientName"),
                "VisitTypeValue": doc.get("VisitTypeValue"),
                "VisitStartDateTime": doc.get("VisitStartDateTime"),
                "VisitStartEndTime": doc.get("VisitStartEndTime"),
                "VisitActualStartDateTime": doc.get("VisitActualStartDateTime"),
                "VisitActualEndDateTime": doc.get("VisitActualEndDateTime"),
                "VisitStatus": doc.get("VisitStatus"),
                "UpdatedByName": doc.get("UpdatedByName"),
                "UpdatedOn": doc.get("UpdatedOn"),
                "AthenaAppointmentId": doc.get("AthenaAppointmentId"),
                "PatientRef": doc.get("PatientRef"),
            }
            writer.writerow(_to_jsonable(row))


def _load_pairs(input_path: str) -> list[tuple[int, int]]:
    """Load (AthenaAppointmentId, PatientRef) from first two columns of CSV or Excel."""
    path_lower = input_path.lower()
    try:
        if path_lower.endswith(".xlsx") or path_lower.endswith(".xls"):
            df = pd.read_excel(input_path, header=0, usecols=[0, 1])
        else:
            df = pd.read_csv(input_path, header=0, usecols=[0, 1])
    except Exception as e:
        raise RuntimeError(f"Failed to read input file '{input_path}': {e}") from e

    # Coerce numeric, drop rows with missing values in first two columns
    df.iloc[:, 0] = pd.to_numeric(df.iloc[:, 0], errors="coerce")
    df.iloc[:, 1] = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    df = df.dropna(subset=[df.columns[0], df.columns[1]])

    pairs: list[tuple[int, int]] = []
    for a, p in zip(df.iloc[:, 0].astype("int64"), df.iloc[:, 1].astype("int64"), strict=False):
        pairs.append((int(a), int(p)))
    return pairs


class _SimpleConfig:
    def __init__(self, uri: str, database: str):
        self._uri = uri
        self._db = database

    def get_mongodb_uri(self) -> str:
        return self._uri

    def get_mongodb_database(self) -> str:
        return self._db


def run_aggregation(
    uri: str,
    database: str,
    collection: str,
    athena_id: int,
    patient_ref: int,
    limit: int | None = None,
    output_csv: str | None = None,
    save_csv: bool = True,
    shared_col=None,
    allow_disk_use: bool = True,
    max_time_ms: int = 600000,
    show_connection_info: bool = True,
) -> list[dict[str, Any]]:
    logger = get_logger(__name__)

    created_conn = False
    if shared_col is not None:
        col = shared_col
        conn = None
    else:
        conn = MongoDBConnection(_SimpleConfig(uri, database))
        created_conn = True
        try:
            conn.connect()
        except Exception as e:
            logger.error(f"MongoDB connect failed: {e}")
            raise
        db = conn.get_database()
        col = db[collection]

    # Connectivity and environment info
    if created_conn and show_connection_info:
        info = conn.test_connection() if conn else {}
        if info.get("connected"):
            logger.info(
                f"Connected to MongoDB | db={info.get('database_name')} | version={info.get('server_version')} | collections={info.get('collections_count')} | rt={info.get('response_time_ms')}ms"
            )
        else:
            logger.warning(f"MongoDB ping failed: {info.get('error')}")

    logger.info(f"Running aggregation for AthenaAppointmentId={athena_id}, PatientRef={patient_ref}")

    # Pipeline mirrors query_v2.js with filteredSlots approach
    pipeline = [
        {
            "$match": {
                "IsActive": HARD_CODED_IS_ACTIVE,
                "AvailabilityDate": {"$gte": HARD_CODED_START_DATE},
                "Slots": {
                    "$elemMatch": {
                        "Appointments": {
                            "$elemMatch": {
                                "AthenaAppointmentId": athena_id,
                                "PatientRef": patient_ref,
                            }
                        }
                    }
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "IsActive": 1,
                "AvailabilityDate": 1,
                "filteredSlots": {
                    "$map": {
                        "input": "$Slots",
                        "as": "slot",
                        "in": {
                            "$filter": {
                                "input": "$$slot.Appointments",
                                "as": "appointment",
                                "cond": {
                                    "$and": [
                                        {
                                            "$eq": [
                                                "$$appointment.AthenaAppointmentId",
                                                athena_id,
                                            ]
                                        },
                                        {
                                            "$eq": [
                                                "$$appointment.PatientRef",
                                                patient_ref,
                                            ]
                                        },
                                    ]
                                },
                            }
                        },
                    }
                },
            }
        },
        {"$unwind": "$filteredSlots"},
        {"$unwind": "$filteredSlots"},
        {
            "$project": {
                "_id": 0,
                "IsActive": 1,
                "AvailabilityDate": 1,
                "PatientName": "$filteredSlots.PatientName",
                "VisitTypeValue": "$filteredSlots.VisitTypeValue",
                "VisitStartDateTime": "$filteredSlots.VisitStartDateTime",
                "VisitStartEndTime": "$filteredSlots.VisitStartEndTime",
                "VisitActualStartDateTime": "$filteredSlots.VisitActualStartDateTime",
                "VisitActualEndDateTime": "$filteredSlots.VisitActualEndDateTime",
                "VisitStatus": "$filteredSlots.VisitStatus",
                "UpdatedByName": "$filteredSlots.UpdatedByName",
                "UpdatedOn": "$filteredSlots.UpdatedOn",
                "AthenaAppointmentId": "$filteredSlots.AthenaAppointmentId",
                "PatientRef": "$filteredSlots.PatientRef",
            }
        },
    ]

    if limit and limit > 0:
        pipeline.append({"$limit": int(limit)})

    try:
        results = list(col.aggregate(pipeline, allowDiskUse=allow_disk_use, maxTimeMS=max_time_ms))
        logger.info("Matches: %s", len(results))
        # Print every result with all projected fields
        for i, doc in enumerate(results, start=1):
            row = {
                "IsActive": doc.get("IsActive"),
                "AvailabilityDate": doc.get("AvailabilityDate"),
                "PatientName": doc.get("PatientName"),
                "VisitTypeValue": doc.get("VisitTypeValue"),
                "VisitStartDateTime": doc.get("VisitStartDateTime"),
                "VisitStartEndTime": doc.get("VisitStartEndTime"),
                "VisitActualStartDateTime": doc.get("VisitActualStartDateTime"),
                "VisitActualEndDateTime": doc.get("VisitActualEndDateTime"),
                "VisitStatus": doc.get("VisitStatus"),
                "UpdatedByName": doc.get("UpdatedByName"),
                "UpdatedOn": doc.get("UpdatedOn"),
                "AthenaAppointmentId": doc.get("AthenaAppointmentId"),
                "PatientRef": doc.get("PatientRef"),
            }
            logger.info("[%s] %s", i, json.dumps(_to_jsonable(row), ensure_ascii=False))

        if save_csv:
            try:
                if output_csv and output_csv.strip():
                    out_path = output_csv.strip()
                else:
                    settings = get_settings()
                    out_dir = str(settings.paths.data_output)
                    out_path = os.path.join(
                        out_dir,
                        f"appointments_{athena_id}_{patient_ref}_{HARD_CODED_START_DATE.date().isoformat()}.csv",
                    )
                _write_csv(out_path, results)
                logger.info("CSV saved: %s (rows: %s)", out_path, len(results))
            except Exception as e:
                logger.error("Failed to write CSV: %s", e)
        return results
    except Exception as e:
        logger.error("Aggregation failed: %s", e)
        return []
    finally:
        if created_conn and conn is not None:
            conn.disconnect()
            get_logger(__name__).info("MongoDB connection closed")


def _parse_bool(val: str) -> bool:
    v = val.strip().lower()
    if v in ("1", "true", "t", "yes", "y"):  # truthy
        return True
    if v in ("0", "false", "f", "no", "n"):  # falsy
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {val}")


# Removed date parsing; filters are hard-coded


def main() -> None:
    # Initialize shared settings and logging
    settings = get_settings()
    setup_logging(log_dir=settings.paths.logs, level=settings.log_level)
    logger = get_logger(__name__)

    default_uri = settings.mongodb_uri or "mongodb://localhost:27017"
    default_db = settings.database_name or "UbiquityProduction"
    default_collection = settings.collection_name or DEFAULT_COLLECTION

    parser = argparse.ArgumentParser(description="Run StaffAvailability aggregation")
    parser.add_argument("--uri", default=default_uri, help="MongoDB connection string")
    parser.add_argument("--database", default=default_db, help="Database name")
    parser.add_argument("--collection", default=default_collection, help="Collection name")
    parser.add_argument("--athena_id", type=int, default=10025, help="AthenaAppointmentId to match")
    parser.add_argument("--patient_ref", type=int, default=7010699, help="PatientRef to match")
    # Filters are hard-coded; no CLI flags for them
    parser.add_argument("--limit", type=int, default=0, help="Optional $limit on results")
    parser.add_argument(
        "--output_csv",
        default="",
        help="Optional CSV path to write results. One row per matched appointment.",
    )
    parser.add_argument(
        "--input_file",
        default="",
        help="Optional CSV/Excel of pairs in first two columns: AthenaAppointmentId,PatientRef.",
    )
    parser.add_argument(
        "--allow_disk_use",
        type=_parse_bool,
        default=True,
        help="Enable allowDiskUse on aggregation (default: true)",
    )
    parser.add_argument(
        "--max_time_ms",
        type=int,
        default=600000,
        help="Max time in ms for each aggregation (default: 600000)",
    )

    args = parser.parse_args()

    # Batch mode if input_file provided; otherwise single pair mode
    if args.input_file:
        pairs = _load_pairs(args.input_file)
        logger.info("Loaded %s pairs from %s", len(pairs), args.input_file)
        all_results: list[dict[str, Any]] = []
        # Create one shared connection/collection for the entire batch
        conn = MongoDBConnection(_SimpleConfig(args.uri, args.database))
        conn.connect()
        info = conn.test_connection()
        if info.get("connected"):
            logger.info(
                f"Connected to MongoDB | db={info.get('database_name')} | version={info.get('server_version')} | collections={info.get('collections_count')} | rt={info.get('response_time_ms')}ms"
            )
        else:
            logger.warning(f"MongoDB ping failed: {info.get('error')}")
        shared_col = conn.get_database()[args.collection]

        try:
            for idx, (aid, pref) in enumerate(pairs, start=1):
                logger.info(
                    "=== Processing pair %s/%s: AthenaAppointmentId=%s, PatientRef=%s ===",
                    idx,
                    len(pairs),
                    aid,
                    pref,
                )
                res = run_aggregation(
                    uri=args.uri,
                    database=args.database,
                    collection=args.collection,
                    athena_id=aid,
                    patient_ref=pref,
                    limit=args.limit if args.limit and args.limit > 0 else None,
                    output_csv=None,
                    save_csv=False,
                    shared_col=shared_col,
                    allow_disk_use=args.allow_disk_use,
                    max_time_ms=args.max_time_ms,
                    show_connection_info=False,
                )
                all_results.extend(res)
        finally:
            conn.disconnect()
            logger.info("MongoDB connection closed")

        # Write combined CSV (use provided path or default batch name)
        combined_out = (
            args.output_csv.strip()
            if args.output_csv
            else os.path.join(
                str(settings.paths.data_output),
                f"appointments_batch_{HARD_CODED_START_DATE.date().isoformat()}_{len(pairs)}.csv",
            )
        )
        try:
            _write_csv(combined_out, all_results)
            logger.info("CSV saved: %s (rows: %s)", combined_out, len(all_results))
        except Exception as e:
            logger.error("Failed to write combined CSV: %s", e)
    else:
        run_aggregation(
            uri=args.uri,
            database=args.database,
            collection=args.collection,
            athena_id=args.athena_id,
            patient_ref=args.patient_ref,
            limit=args.limit if args.limit and args.limit > 0 else None,
            output_csv=(args.output_csv or None),
            save_csv=True,
            shared_col=None,
            allow_disk_use=args.allow_disk_use,
            max_time_ms=args.max_time_ms,
            show_connection_info=True,
        )


if __name__ == "__main__":
    main()
