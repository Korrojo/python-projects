#!/usr/bin/env python3
"""Resolve VisitStatus using only PatientRef, AvailabilityDate, and VisitTypeValue."""

from __future__ import annotations

import argparse
import csv
import os
from datetime import UTC, datetime
from typing import Any

from common_config.config.settings import get_settings
from common_config.db.connection import MongoDBConnection
from common_config.utils.logger import get_logger, setup_logging

DEFAULT_COLLECTION = "StaffAvailability"

# Hard-coded filters (do not pass via CLI)
HARD_CODED_IS_ACTIVE: bool = True
HARD_CODED_START_DATE: datetime = datetime(2025, 6, 30, 0, 0, 0, tzinfo=UTC)

REQUIRED_COLUMNS: list[str] = [
    "PatientRef",
    "AvailabilityDate",
    "VisitTypeValue",
]
OUTPUT_COLUMNS: list[str] = [
    "PatientRef",
    "AvailabilityDate",
    "VisitTypeValue",
    "VisitStatus",
]


def _parse_bool(val: str) -> bool:
    v = val.strip().lower()
    if v in ("1", "true", "t", "yes", "y"):
        return True
    if v in ("0", "false", "f", "no", "n"):
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {val}")


def _parse_int(value: Any, field_name: str) -> int:
    if value is None:
        raise ValueError(f"{field_name} is required")
    try:
        text = str(value).strip().replace(",", "")
        if not text:
            raise ValueError
        return int(float(text)) if "." in text else int(text)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Invalid integer for {field_name}: {value!r}") from exc


def _parse_datetime(value: str) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except Exception:
        pass
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(tzinfo=UTC)
        except Exception:
            continue
    return None


def _build_pipeline(
    patient_ref: int,
    visit_type: str,
    availability_dt: datetime | None,
) -> list[dict[str, Any]]:
    appointment_filters: list[dict[str, Any]] = [
        {"$eq": ["$$appointment.PatientRef", patient_ref]},
    ]
    if visit_type:
        appointment_filters.append({"$eq": ["$$appointment.VisitTypeValue", visit_type]})

    base_match: dict[str, Any] = {
        "IsActive": HARD_CODED_IS_ACTIVE,
        "Slots": {
            "$elemMatch": {
                "Appointments": {
                    "$elemMatch": {
                        "PatientRef": patient_ref,
                        **({"VisitTypeValue": visit_type} if visit_type else {}),
                    }
                }
            }
        },
    }

    if availability_dt is not None:
        base_match["AvailabilityDate"] = availability_dt
    else:
        base_match["AvailabilityDate"] = {"$gte": HARD_CODED_START_DATE}

    pipeline: list[dict[str, Any]] = [{"$match": base_match}]

    pipeline.extend(
        [
            {
                "$project": {
                    "_id": 0,
                    "AvailabilityDate": 1,
                    "filteredSlots": {
                        "$map": {
                            "input": "$Slots",
                            "as": "slot",
                            "in": {
                                "$filter": {
                                    "input": "$$slot.Appointments",
                                    "as": "appointment",
                                    "cond": {"$and": appointment_filters},
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
                    "AvailabilityDate": 1,
                    "VisitStatus": "$filteredSlots.VisitStatus",
                    "VisitTypeValue": "$filteredSlots.VisitTypeValue",
                    "PatientRef": "$filteredSlots.PatientRef",
                    "VisitStartDateTime": "$filteredSlots.VisitStartDateTime",
                    "VisitActualStartDateTime": "$filteredSlots.VisitActualStartDateTime",
                    "VisitActualEndDateTime": "$filteredSlots.VisitActualEndDateTime",
                    "UpdatedOn": "$filteredSlots.UpdatedOn",
                }
            },
        ]
    )

    return pipeline


def _prepare_output_row(row: dict[str, Any]) -> dict[str, str]:
    prepared = {col: str(row.get(col, "")) for col in OUTPUT_COLUMNS}
    return prepared


def _process_rows(
    collection,
    rows: list[dict[str, Any]],
    allow_disk_use: bool,
    max_time_ms: int,
    logger,
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []

    for idx, row in enumerate(rows, start=1):
        base_row = _prepare_output_row(row)
        try:
            patient_ref = _parse_int(row.get("PatientRef"), "PatientRef")
        except ValueError as exc:
            logger.warning("[Row %s] Invalid PatientRef: %s", idx, exc)
            base_row["VisitStatus"] = ""
            output.append(base_row)
            continue

        visit_type = (row.get("VisitTypeValue") or "").strip()
        availability_dt = _parse_datetime(row.get("AvailabilityDate", ""))
        if availability_dt is None:
            logger.warning(
                "[Row %s] Invalid AvailabilityDate for PatientRef=%s: %s",
                idx,
                patient_ref,
                row.get("AvailabilityDate"),
            )
            base_row["VisitStatus"] = ""
            output.append(base_row)
            continue

        pipeline = _build_pipeline(patient_ref, visit_type, availability_dt)

        try:
            matches = list(
                collection.aggregate(
                    pipeline,
                    allowDiskUse=allow_disk_use,
                    maxTimeMS=max_time_ms,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "[Row %s] Aggregation failed for PatientRef=%s, VisitTypeValue=%s, AvailabilityDate=%s: %s",
                idx,
                patient_ref,
                visit_type,
                availability_dt.isoformat(),
                exc,
            )
            base_row["VisitStatus"] = ""
            output.append(base_row)
            continue

        if not matches:
            logger.info(
                "[Row %s] No matches for PatientRef=%s, VisitTypeValue=%s, AvailabilityDate=%s",
                idx,
                patient_ref,
                visit_type,
                availability_dt.isoformat(),
            )
            base_row["VisitStatus"] = ""
            output.append(base_row)
            continue

        logger.info(
            "[Row %s] Matches: %s for PatientRef=%s, VisitTypeValue=%s, AvailabilityDate=%s",
            idx,
            len(matches),
            patient_ref,
            visit_type,
            availability_dt.isoformat(),
        )

        for match in matches:
            row_out = base_row.copy()
            row_out["VisitStatus"] = str(match.get("VisitStatus", "") or "")
            output.append(row_out)

    return output


def main() -> None:
    # Initialize shared settings and logging
    settings = get_settings()
    setup_logging(log_dir=settings.paths.logs, level=settings.log_level)
    logger = get_logger(__name__)

    default_uri = settings.mongodb_uri or "mongodb://localhost:27017"
    default_db = settings.database_name or "UbiquityProduction"
    default_collection = settings.collection_name or DEFAULT_COLLECTION

    parser = argparse.ArgumentParser(
        description=("Fetch VisitStatus for appointments using PatientRef, AvailabilityDate, and VisitTypeValue.")
    )
    parser.add_argument("--uri", default=default_uri, help="MongoDB connection string")
    parser.add_argument("--database", default=default_db, help="Database name")
    parser.add_argument("--collection", default=default_collection, help="Collection name")
    parser.add_argument(
        "--input_file",
        required=True,
        help="CSV input containing PatientRef, AvailabilityDate, VisitTypeValue",
    )
    parser.add_argument(
        "--output_csv",
        default="",
        help="Output CSV path. Defaults to data/output/<input>_with_status.csv",
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

    logger.info("Starting visit_status_report_threecol...")
    logger.info("Input file: %s", args.input_file)
    if args.output_csv:
        logger.info("Output path (requested): %s", args.output_csv)

    # Read CSV using builtin csv module to avoid heavy deps
    try:
        with open(args.input_file, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            missing_columns = [col for col in REQUIRED_COLUMNS if col not in headers]
            if missing_columns:
                raise SystemExit("Input file missing required columns: " + ", ".join(missing_columns))

            rows: list[dict[str, str]] = []
            for rec in reader:
                row = {col: (rec.get(col, "") or "") for col in OUTPUT_COLUMNS}
                rows.append(row)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Failed to read input file '{args.input_file}': {exc}") from exc

    logger.info("Loaded %s rows from %s", len(rows), args.input_file)

    class _Cfg:
        def __init__(self, uri: str, db: str) -> None:
            self._uri = uri
            self._db = db

        def get_mongodb_uri(self) -> str:
            return self._uri

        def get_mongodb_database(self) -> str:
            return self._db

    conn = MongoDBConnection(_Cfg(args.uri, args.database))
    info = conn.test_connection()
    if info.get("connected"):
        logger.info(
            "Connected to MongoDB | db=%s | version=%s | collections=%s | rt=%sms",
            info.get("database_name"),
            info.get("server_version"),
            info.get("collections_count"),
            info.get("response_time_ms"),
        )
    else:
        logger.warning("MongoDB ping failed: %s", info.get("error"))

    try:
        collection = conn.get_database()[args.collection]
        output_rows = _process_rows(
            collection,
            rows,
            allow_disk_use=args.allow_disk_use,
            max_time_ms=args.max_time_ms,
            logger=logger,
        )
    finally:
        conn.disconnect()
        logger.info("MongoDB connection closed")

    # Determine output path
    if args.output_csv and args.output_csv.strip():
        out_path = args.output_csv.strip()
    else:
        base = os.path.splitext(os.path.basename(args.input_file))[0]
        out_path = os.path.join(str(settings.paths.data_output), f"{base}_with_status.csv")

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(output_rows)

    logger.info("CSV saved: %s (rows written: %s)", out_path, len(output_rows))


if __name__ == "__main__":
    main()
