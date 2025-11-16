#!/usr/bin/env python3
"""
Batch script to resolve VisitStatus for appointment rows supplied via CSV.

Input CSV header:
    PatientRef, VisitTypeValue, AthenaAppointmentId, AvailabilityDate

Behavior:
- Filters per row by AthenaAppointmentId, PatientRef, and VisitTypeValue
- Applies a global AvailabilityDate window: 2025-06-28 through 2025-10-15 (inclusive)
- Overwrites VisitStatus with value from MongoDB
- Duplicates the input row once per match; if no match, VisitStatus is blank and Comment is "match not found"
- AvailabilityDate in the output is normalized to YYYY-MM-DD

Now integrated with common_config for settings, logging, and DB connection.
"""

from __future__ import annotations

import argparse
import csv
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from common_config.config.settings import get_settings
from common_config.db.connection import MongoDBConnection
from common_config.utils.logger import get_logger, setup_logging

DEFAULT_COLLECTION = "StaffAvailability"

# Hard-coded filters (do not pass via CLI)
HARD_CODED_IS_ACTIVE: bool = True
HARD_CODED_START_DATE: datetime = datetime(2025, 6, 28, 0, 0, 0, tzinfo=UTC)
HARD_CODED_END_DATE: datetime = datetime(2025, 10, 15, 23, 59, 59, tzinfo=UTC)

INPUT_COLUMNS: list[str] = [
    "PatientRef",
    "AthenaAppointmentId",
    "AvailabilityDate",
    "VisitTypeValue",
]
OUTPUT_COLUMNS: list[str] = [
    "PatientRef",
    "AthenaAppointmentId",
    "AvailabilityDate",
    "VisitTypeValue",
    "VisitStatus",
    "Comment",
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
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M", "%m/%d/%y", "%m/%d/%y %H:%M"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt.replace(tzinfo=UTC)
        except Exception:
            continue
    return None


def _format_date_yyyy_mm_dd(value: Any) -> str:
    """Format any date-like input to YYYY-MM-DD; fallback to original string if unparseable."""
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = _parse_datetime(str(value) if value is not None else "")
        except Exception:
            dt = None
    if dt:
        return dt.date().isoformat()
    return str(value) if value else ""


ALLOWED_FILTERS = {"athena_appt_id", "patient_id", "visit_type"}


def _parse_filters_arg(text: str | None) -> set[str]:
    raw = (text or "").strip()
    if not raw:
        return set()
    parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
    invalid = [p for p in parts if p not in ALLOWED_FILTERS]
    if invalid:
        raise SystemExit("Invalid --filters tokens: " + ", ".join(invalid))
    return set(parts)


def _build_pipeline(
    athena_appt_id: int | None,
    patient_ref: int | None,
    visit_type: str,
    filters: set[str],
    date_mode: str,
    row_availability: datetime | None,
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, Any]]:
    appointment_filters: list[dict[str, Any]] = []
    appointments_match: dict[str, Any] = {}

    if "athena_appt_id" in filters and athena_appt_id is not None:
        appointment_filters.append({"$eq": ["$$appointment.AthenaAppointmentId", athena_appt_id]})
        appointments_match["AthenaAppointmentId"] = athena_appt_id
    if "patient_id" in filters and patient_ref is not None:
        appointment_filters.append({"$eq": ["$$appointment.PatientRef", patient_ref]})
        appointments_match["PatientRef"] = patient_ref
    if "visit_type" in filters and visit_type:
        appointment_filters.append({"$eq": ["$$appointment.VisitTypeValue", visit_type]})
        appointments_match["VisitTypeValue"] = visit_type

    base_match: dict[str, Any] = {
        "IsActive": HARD_CODED_IS_ACTIVE,
    }

    if date_mode == "per_row":
        if row_availability is not None:
            base_match["AvailabilityDate"] = row_availability
        else:
            # Let caller handle invalid date; keep no date constraint to avoid accidental matches
            base_match["AvailabilityDate"] = {"$exists": True}
    else:
        base_match["AvailabilityDate"] = {"$gte": start_date, "$lte": end_date}

    if appointments_match:
        base_match["Slots"] = {"$elemMatch": {"Appointments": {"$elemMatch": appointments_match}}}
    else:
        # No appointment-level filters would explode results; enforce at least one
        raise SystemExit("At least one of the filters must be specified: athena_appt_id, patient_id, visit_type")

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
                    "AthenaAppointmentId": "$filteredSlots.AthenaAppointmentId",
                    "PatientRef": "$filteredSlots.PatientRef",
                    "VisitTypeValue": "$filteredSlots.VisitTypeValue",
                    "VisitStartDateTime": "$filteredSlots.VisitStartDateTime",
                    "UpdatedOn": "$filteredSlots.UpdatedOn",
                }
            },
        ]
    )

    return pipeline


def _prepare_output_row(row: dict[str, Any]) -> dict[str, str]:
    return {col: str(row.get(col, "")) for col in OUTPUT_COLUMNS}


def _process_rows(
    collection,
    rows: list[dict[str, Any]],
    allow_disk_use: bool,
    max_time_ms: int,
    logger,
    filters: set[str],
    date_mode: str,
    start_dt: datetime,
    end_dt: datetime,
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []

    for idx, row in enumerate(rows, start=1):
        base_row = _prepare_output_row(row)
        # Parse fields based on active filters
        athena_appt_id: int | None = None
        patient_ref: int | None = None
        visit_type = (row.get("VisitTypeValue") or "").strip()

        try:
            if "athena_appt_id" in filters:
                athena_appt_id = _parse_int(row.get("AthenaAppointmentId"), "AthenaAppointmentId")
            if "patient_id" in filters:
                patient_ref = _parse_int(row.get("PatientRef"), "PatientRef")
        except ValueError as exc:
            logger.warning("[Row %s] Invalid identifiers: %s", idx, exc)
            base_row["VisitStatus"] = ""
            output.append(base_row)
            continue

        row_availability: datetime | None = None
        if date_mode == "per_row":
            row_availability = _parse_datetime(row.get("AvailabilityDate", ""))
            if row_availability is None:
                logger.warning("[Row %s] Invalid AvailabilityDate: %s", idx, row.get("AvailabilityDate"))
                base_row["VisitStatus"] = ""
                base_row["Comment"] = "invalid AvailabilityDate"
                output.append(base_row)
                continue

        pipeline = _build_pipeline(
            athena_appt_id,
            patient_ref,
            visit_type,
            filters,
            date_mode,
            row_availability,
            start_dt,
            end_dt,
        )

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
                "[Row %s] Aggregation failed for AthenaAppointmentId=%s, PatientRef=%s: %s",
                idx,
                athena_appt_id,
                patient_ref,
                exc,
            )
            base_row["VisitStatus"] = ""
            output.append(base_row)
            continue

        if not matches:
            logger.info(
                "[Row %s] No matches for AthenaAppointmentId=%s, PatientRef=%s",
                idx,
                athena_appt_id,
                patient_ref,
            )
            base_row["VisitStatus"] = ""
            base_row["Comment"] = "match not found"
            base_row["AvailabilityDate"] = _format_date_yyyy_mm_dd(row.get("AvailabilityDate"))
            output.append(base_row)
            continue

        logger.info(
            "[Row %s] Matches: %s for AthenaAppointmentId=%s, PatientRef=%s",
            idx,
            len(matches),
            athena_appt_id,
            patient_ref,
        )

        for match in matches:
            row_out = dict.fromkeys(OUTPUT_COLUMNS, "")
            row_out["PatientRef"] = str(match.get("PatientRef", "") or "")
            row_out["AthenaAppointmentId"] = str(match.get("AthenaAppointmentId", "") or "")
            availability_val = match.get("AvailabilityDate")
            row_out["AvailabilityDate"] = _format_date_yyyy_mm_dd(availability_val)
            row_out["VisitStatus"] = str(match.get("VisitStatus", "") or "")
            row_out["VisitTypeValue"] = str(match.get("VisitTypeValue", "") or "")
            row_out["Comment"] = ""
            output.append(row_out)

    return output


def main() -> None:
    # Initialize shared settings and logging
    settings = get_settings()
    project_logs = Path(settings.paths.logs) / "staff-appointment-visitStatus"
    setup_logging(log_dir=project_logs, level=settings.log_level)
    logger = get_logger(__name__)

    default_uri = settings.mongodb_uri or "mongodb://localhost:27017"
    default_db = settings.database_name or "UbiquityProduction"
    default_collection = settings.collection_name or DEFAULT_COLLECTION

    parser = argparse.ArgumentParser(description="Fetch VisitStatus for appointments listed in a CSV file.")
    parser.add_argument("--uri", default=default_uri, help="MongoDB connection string")
    parser.add_argument("--database", default=default_db, help="Database name")
    parser.add_argument("--collection", default=default_collection, help="Collection name")
    parser.add_argument(
        "--input_file",
        required=True,
        help="CSV input containing PatientRef, VisitTypeValue, AthenaAppointmentId, AvailabilityDate",
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

    parser.add_argument(
        "--filters",
        default="athena_appt_id,patient_id,visit_type",
        help="Comma-separated filters to apply: athena_appt_id,patient_id,visit_type",
    )
    parser.add_argument(
        "--date_mode",
        choices=["window", "per_row"],
        default="window",
        help="Use global date window or per-row AvailabilityDate",
    )
    parser.add_argument(
        "--start_date",
        default=HARD_CODED_START_DATE.date().isoformat(),
        help="Start date (YYYY-MM-DD) when date_mode=window",
    )
    parser.add_argument(
        "--end_date",
        default=HARD_CODED_END_DATE.date().isoformat(),
        help="End date (YYYY-MM-DD) when date_mode=window",
    )

    args = parser.parse_args()

    # Resolve dynamic filters and dates
    active_filters = _parse_filters_arg(args.filters)
    if not active_filters:
        raise SystemExit("--filters must include at least one of: athena_appt_id, patient_id, visit_type")
    effective_start = _parse_datetime(args.start_date) or HARD_CODED_START_DATE
    effective_end = _parse_datetime(args.end_date) or HARD_CODED_END_DATE

    logger.info("Starting visit_status_report...")
    logger.info("Input file: %s", args.input_file)
    if args.output_csv:
        logger.info("Output path (requested): %s", args.output_csv)

    # Read CSV using builtin csv module to avoid heavy deps
    try:
        with open(args.input_file, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            # Dynamic header requirements based on filters/date mode
            required_columns: list[str] = []
            if "athena_appt_id" in active_filters:
                required_columns.append("AthenaAppointmentId")
            if "patient_id" in active_filters:
                required_columns.append("PatientRef")
            if "visit_type" in active_filters:
                required_columns.append("VisitTypeValue")
            if args.date_mode == "per_row":
                required_columns.append("AvailabilityDate")

            missing_columns = [col for col in required_columns if col not in headers]
            if missing_columns:
                raise SystemExit("Input file missing required columns: " + ", ".join(missing_columns))
            rows: list[dict[str, str]] = []
            for rec in reader:
                # Read superset of known input fields; missing ones default to empty
                row = {col: (rec.get(col, "") or "") for col in INPUT_COLUMNS}
                row["VisitStatus"] = ""
                row["Comment"] = ""
                rows.append(row)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Failed to read input file '{args.input_file}': {exc}") from exc

    logger.info("Loaded %s rows from %s", len(rows), args.input_file)

    # Connection wrapper for common_config
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
            filters=active_filters,
            date_mode=args.date_mode,
            start_dt=effective_start,
            end_dt=effective_end,
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
