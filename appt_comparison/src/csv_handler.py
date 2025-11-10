"""CSV handling module for appointment comparison.

Handles reading, cleaning, date parsing, and writing CSV files.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from common_config.utils.logger import get_logger

logger = get_logger(__name__)


def parse_date(date_str: str) -> datetime | None:
    """Parse date from M/D/YY format to datetime.

    Assumes 2-digit years: 25 = 2025, 26 = 2026

    Args:
        date_str: Date string in M/D/YY format (e.g., "10/27/25")

    Returns:
        datetime object or None if parsing fails
    """
    if not date_str or not date_str.strip():
        return None

    try:
        date_str = date_str.strip()
        # Parse M/D/YY format
        dt = datetime.strptime(date_str, "%m/%d/%y")

        # Adjust century: 25-99 -> 2025-2099, 00-24 -> 2000-2024
        if dt.year < 2000:
            dt = dt.replace(year=dt.year + 2000)

        return dt
    except ValueError as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None


def format_date_for_mongo(dt: datetime) -> str:
    """Format datetime for MongoDB comparison (date-only, ISO format).

    Args:
        dt: datetime object

    Returns:
        ISO date string (YYYY-MM-DD)
    """
    return dt.strftime("%Y-%m-%d")


def read_csv_file(file_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Read CSV file and return rows with fieldnames.

    Args:
        file_path: Path to CSV file

    Returns:
        Tuple of (rows, fieldnames)
    """
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    rows = []
    fieldnames: list[str] = []

    with file_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])

        for row in reader:
            rows.append(row)

    logger.info(f"Read {len(rows)} rows from {file_path}")
    logger.info(f"CSV columns: {', '.join(fieldnames)}")

    return rows, fieldnames


def clean_cancelled_rows(
    rows: list[dict[str, Any]], fieldnames: list[str]
) -> tuple[list[dict[str, Any]], list[str], int]:
    """Remove rows with 'Cancelled' status and remove 'Cancel Status' column.

    Args:
        rows: List of CSV row dictionaries
        fieldnames: List of CSV column names

    Returns:
        Tuple of (cleaned_rows, cleaned_fieldnames, num_removed)
    """
    cancel_col = "Cancel Status"

    # Check if Cancel Status column exists
    if cancel_col not in fieldnames:
        logger.info("'Cancel Status' column not found - no cleanup needed")
        return rows, fieldnames, 0

    # Filter out cancelled rows
    cleaned_rows = []
    removed_count = 0

    for row in rows:
        status = (row.get(cancel_col) or "").strip()
        if status.lower() == "cancelled":
            removed_count += 1
        else:
            # Remove Cancel Status column from row
            cleaned_row = {k: v for k, v in row.items() if k != cancel_col}
            cleaned_rows.append(cleaned_row)

    # Remove Cancel Status from fieldnames
    cleaned_fieldnames = [f for f in fieldnames if f != cancel_col]

    logger.info(f"Removed {removed_count} cancelled rows")
    logger.info(f"Remaining rows: {len(cleaned_rows)}")

    return cleaned_rows, cleaned_fieldnames, removed_count


def remove_validation_columns(
    rows: list[dict[str, Any]], fieldnames: list[str]
) -> tuple[list[dict[str, Any]], list[str]]:
    """Remove validation columns if they exist (from previous runs).

    Args:
        rows: List of CSV row dictionaries
        fieldnames: List of CSV column names

    Returns:
        Tuple of (cleaned_rows, cleaned_fieldnames)
    """
    validation_cols = ["AthenaAppointmentId Found?", "Total Match?", "Mismatched Fields", "Missing Fields", "Comment"]

    # Check if any validation columns exist
    existing_validation_cols = [col for col in validation_cols if col in fieldnames]

    if not existing_validation_cols:
        logger.info("No existing validation columns found")
        return rows, fieldnames

    logger.warning(f"Found existing validation columns from previous run: {', '.join(existing_validation_cols)}")
    logger.info("Removing validation columns to prevent duplicates")

    # Remove validation columns from fieldnames
    cleaned_fieldnames = [f for f in fieldnames if f not in validation_cols]

    # Remove validation columns from rows
    cleaned_rows = []
    for row in rows:
        cleaned_row = {k: v for k, v in row.items() if k not in validation_cols}
        cleaned_rows.append(cleaned_row)

    logger.info(f"Removed {len(existing_validation_cols)} validation columns")

    return cleaned_rows, cleaned_fieldnames


def write_csv_file(file_path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    """Write rows to CSV file.

    Args:
        file_path: Output file path
        rows: List of row dictionaries
        fieldnames: List of column names
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Wrote {len(rows)} rows to {file_path}")


def validate_required_fields(row: dict[str, Any], required_fields: list[str]) -> list[str]:
    """Check if required fields are present and non-empty in a row.

    Args:
        row: CSV row dictionary
        required_fields: List of field names to check

    Returns:
        List of missing field names
    """
    missing = []

    for field in required_fields:
        value = row.get(field, "").strip()
        if not value:
            missing.append(field)

    return missing


def normalize_time_string(time_str: str) -> str:
    """Normalize time string for comparison.

    Args:
        time_str: Time string (e.g., "1:35 PM", "09:28 AM")

    Returns:
        Normalized time string
    """
    if not time_str:
        return ""

    return time_str.strip()


def normalize_visit_type(visit_type: str) -> str:
    """Normalize visit type for case-insensitive comparison.

    Args:
        visit_type: Visit type string

    Returns:
        Normalized visit type (trimmed, lowercase)
    """
    if not visit_type:
        return ""

    return visit_type.strip().lower()
