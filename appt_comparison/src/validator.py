"""Main validator orchestration module.

Coordinates CSV processing, MongoDB matching, and output generation.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pymongo.database import Database

from common_config.utils.logger import get_logger, get_run_timestamp

from csv_handler import (
    clean_cancelled_rows,
    parse_date,
    read_csv_file,
    remove_validation_columns,
    validate_required_fields,
    write_csv_file,
)
from field_comparator import FieldComparator
from mongo_matcher import MongoMatcher

logger = get_logger(__name__)


class AppointmentValidator:
    """Main validator for appointment comparison."""

    def __init__(
        self,
        db: Database,
        collection_name: str,
        batch_size: int = 100,
        progress_log_frequency: int = 100,
        max_retries: int = 3,
        base_retry_sleep: float = 2.0,
        case_sensitive_visit_type: bool = False,
        trim_strings: bool = True,
    ):
        """Initialize validator.

        Args:
            db: MongoDB database connection
            collection_name: StaffAvailability collection name
            batch_size: Number of records to process per batch
            progress_log_frequency: Log progress every N rows
            max_retries: Max retry attempts for MongoDB queries
            base_retry_sleep: Base sleep time for retry backoff
            case_sensitive_visit_type: Case-sensitive VisitTypeValue comparison
            trim_strings: Trim whitespace before comparison
        """
        self.db = db
        self.collection_name = collection_name
        self.batch_size = batch_size
        self.progress_log_frequency = progress_log_frequency

        self.matcher = MongoMatcher(db, collection_name, max_retries, base_retry_sleep)
        self.comparator = FieldComparator(case_sensitive_visit_type, trim_strings)

        # Statistics
        self.stats = {
            "total_rows": 0,
            "cancelled_removed": 0,
            "processed": 0,
            "athena_id_found": 0,
            "athena_id_not_found": 0,
            "total_match": 0,
            "total_mismatch": 0,
            "field_mismatch": 0,  # Mismatches when record found but fields differ
            "not_found_mismatch": 0,  # Mismatches when record not found at all
            "missing_fields": 0,
            "secondary_matches": 0,
        }

    def validate_file(self, input_path: Path, output_dir: Path, limit: int | None = None) -> tuple[Path, Path | None]:
        """Validate appointment CSV file.

        Args:
            input_path: Path to input CSV file
            output_dir: Directory for output files
            limit: Optional limit on number of rows to process

        Returns:
            Tuple of (output_csv_path, cleaned_csv_path)
        """
        logger.info("=" * 80)
        logger.info("Starting appointment validation")
        logger.info(f"Input file: {input_path}")
        logger.info(f"Collection: {self.collection_name}")
        logger.info(f"Database: {self.db.name}")
        logger.info(f"Batch size: {self.batch_size}")
        if limit:
            logger.info(f"Row limit: {limit}")
        logger.info("=" * 80)

        # Check if cleaned version already exists (save to input dir, not output)
        cleaned_filename = input_path.stem + "_cleaned.csv"
        cleaned_csv_path = input_path.parent / cleaned_filename

        if cleaned_csv_path.exists():
            # Use existing cleaned file
            logger.info(f"Using existing cleaned file: {cleaned_csv_path}")
            rows, fieldnames = read_csv_file(cleaned_csv_path)
            self.stats["total_rows"] = len(rows)
            self.stats["cancelled_removed"] = 0  # Already cleaned
        else:
            # Read original CSV and clean it
            rows, fieldnames = read_csv_file(input_path)
            self.stats["total_rows"] = len(rows)

            # Remove any existing validation columns from previous runs
            rows, fieldnames = remove_validation_columns(rows, fieldnames)

            # Clean cancelled rows if needed
            rows, fieldnames, removed = clean_cancelled_rows(rows, fieldnames)
            self.stats["cancelled_removed"] = removed

            if removed > 0:
                # Save cleaned CSV for future use
                write_csv_file(cleaned_csv_path, rows, fieldnames)
                logger.info(f"Saved cleaned CSV to: {cleaned_csv_path}")
            else:
                # No cancelled rows, so no cleaned file created
                cleaned_csv_path = None

        # Apply row limit if specified
        if limit and limit > 0:
            rows = rows[:limit]
            logger.info(f"Limited processing to {len(rows)} rows")

        # Calculate date range for optimization (scan all AvailabilityDate values)
        logger.info("Calculating date range from CSV for query optimization...")
        min_date = None
        max_date = None
        for row in rows:
            date_str = row.get("AvailabilityDate", "").strip()
            if date_str:
                parsed = parse_date(date_str)
                if parsed:
                    if min_date is None or parsed < min_date:
                        min_date = parsed
                    if max_date is None or parsed > max_date:
                        max_date = parsed

        if min_date and max_date:
            # Add one day buffer to max_date for date-only comparison
            from datetime import timedelta

            max_date = max_date + timedelta(days=1)
            logger.info(f"Date range filter: {min_date.date()} to {max_date.date()}")
            logger.info("This will significantly improve query performance!")

            # Update matcher with date range
            self.matcher.min_date = min_date
            self.matcher.max_date = max_date
        else:
            logger.warning("Could not determine date range - queries may be slower")

        # Add validation columns
        output_fieldnames = fieldnames + [
            "AthenaAppointmentId Found?",
            "Total Match?",
            "Mismatched Fields",
            "Missing Fields",
            "Comment",
        ]

        # Process rows in batches
        total_rows = len(rows)
        for batch_start in range(0, total_rows, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_rows)
            batch = rows[batch_start:batch_end]

            self._process_batch(batch)

            # Log progress
            if (batch_end % self.progress_log_frequency == 0) or (batch_end == total_rows):
                logger.info(
                    f"Processed {batch_end}/{total_rows} rows "
                    f"(matched={self.stats['total_match']} "
                    f"mismatched={self.stats['total_mismatch']} "
                    f"not_found={self.stats['athena_id_not_found']})"
                )

        # Write output CSV
        timestamp = get_run_timestamp()
        output_filename = f"{timestamp}_appointment_comparison_output.csv"
        output_path = output_dir / output_filename
        write_csv_file(output_path, rows, output_fieldnames)

        logger.info("=" * 80)
        logger.info("Validation complete!")
        logger.info(f"Output CSV: {output_path}")
        if cleaned_csv_path:
            logger.info(f"Cleaned CSV: {cleaned_csv_path}")
        self._log_statistics()
        logger.info("=" * 80)

        return output_path, cleaned_csv_path

    def _process_batch(self, batch: list[dict[str, Any]]) -> None:
        """Process a batch of CSV rows.

        Args:
            batch: List of CSV row dictionaries
        """
        # Collect AthenaAppointmentIds for batch query
        athena_ids = []
        for row in batch:
            athena_id = row.get("AthenaAppointmentId", "").strip()
            if athena_id:
                athena_ids.append(athena_id)

        # Batch lookup by AthenaAppointmentId
        mongo_lookup = {}
        if athena_ids:
            mongo_lookup = self.matcher.find_by_athena_id_batch(athena_ids)

        # Process each row
        for row in batch:
            self._process_row(row, mongo_lookup)

    def _process_row(self, row: dict[str, Any], mongo_lookup: dict[Any, dict[str, Any]]) -> None:
        """Process a single CSV row.

        Args:
            row: CSV row dictionary
            mongo_lookup: Lookup dictionary from batch query
        """
        self.stats["processed"] += 1

        # Initialize output fields
        row["AthenaAppointmentId Found?"] = ""
        row["Total Match?"] = ""
        row["Mismatched Fields"] = ""
        row["Missing Fields"] = ""
        row["Comment"] = ""

        # Check for missing required fields
        required_fields = [
            "AthenaAppointmentId",
            "PatientRef",
            "VisitTypeValue",
            "AvailabilityDate",
            "VisitStartDateTime",
        ]
        missing = validate_required_fields(row, required_fields)

        if missing:
            row["Missing Fields"] = ", ".join(missing)
            row["Comment"] = "Missing required fields - no comparison performed"
            self.stats["missing_fields"] += 1
            return

        # Parse availability date
        availability_date_str = row.get("AvailabilityDate", "").strip()
        csv_date = parse_date(availability_date_str)

        if not csv_date:
            row["Missing Fields"] = "AvailabilityDate"
            row["Comment"] = "Invalid date format"
            self.stats["missing_fields"] += 1
            return

        # Primary matching: by AthenaAppointmentId
        athena_id = row.get("AthenaAppointmentId", "").strip()

        # Try to convert athena_id to int for lookup
        athena_id_lookup = athena_id
        try:
            athena_id_lookup = int(athena_id)
        except (ValueError, TypeError):
            pass

        mongo_data = mongo_lookup.get(athena_id_lookup)

        if mongo_data:
            # AthenaAppointmentId found
            row["AthenaAppointmentId Found?"] = "True"
            self.stats["athena_id_found"] += 1

            # Compare all fields
            all_match, mismatched = self.comparator.compare_all_fields(
                row, mongo_data["appointment"], csv_date, mongo_data["availability_date"]
            )

            if all_match:
                row["Total Match?"] = "True"
                self.stats["total_match"] += 1
            else:
                row["Total Match?"] = "False"
                row["Mismatched Fields"] = ", ".join(mismatched)
                self.stats["total_mismatch"] += 1
                self.stats["field_mismatch"] += 1  # Track field-level mismatch
        else:
            # AthenaAppointmentId not found - try secondary matching
            row["AthenaAppointmentId Found?"] = "False"
            self.stats["athena_id_not_found"] += 1

            self._secondary_matching(row, csv_date)

    def _secondary_matching(self, row: dict[str, Any], csv_date: datetime) -> None:
        """Perform secondary matching using 4-field combination.

        Args:
            row: CSV row dictionary (modified in-place)
            csv_date: Parsed availability date
        """
        try:
            patient_ref = int(row.get("PatientRef", "").strip())
            visit_type = row.get("VisitTypeValue", "").strip()
            visit_start_time = row.get("VisitStartDateTime", "").strip()

            # Query MongoDB
            mongo_data = self.matcher.find_by_four_fields(patient_ref, visit_type, csv_date, visit_start_time)

            if mongo_data:
                # Match found using 4-field combination
                self.stats["secondary_matches"] += 1

                # Compare all fields
                all_match, mismatched = self.comparator.compare_all_fields(
                    row, mongo_data["appointment"], csv_date, mongo_data["availability_date"]
                )

                if all_match:
                    row["Total Match?"] = "True"
                    row["Comment"] = "Found via secondary matching (4-field combination)"
                    self.stats["total_match"] += 1
                else:
                    row["Total Match?"] = "False"
                    row["Mismatched Fields"] = ", ".join(mismatched)
                    self.stats["total_mismatch"] += 1
                    self.stats["field_mismatch"] += 1  # Track field-level mismatch
            else:
                # No match found
                row["Total Match?"] = "False"
                row["Comment"] = "No matching appointment found in MongoDB"
                self.stats["total_mismatch"] += 1
                self.stats["not_found_mismatch"] += 1  # Track not-found mismatch

        except (ValueError, TypeError) as e:
            logger.warning(f"Secondary matching failed for row: {e}")
            row["Total Match?"] = "False"
            row["Comment"] = "Secondary matching failed due to invalid data"
            self.stats["total_mismatch"] += 1
            self.stats["not_found_mismatch"] += 1  # Treat as not-found

    def _log_statistics(self) -> None:
        """Log validation statistics."""
        logger.info("Validation Statistics:")
        logger.info(f"  Total rows in input: {self.stats['total_rows']}")
        logger.info(f"  Cancelled rows removed: {self.stats['cancelled_removed']}")
        logger.info(f"  Rows processed: {self.stats['processed']}")
        logger.info(f"  Rows with missing fields: {self.stats['missing_fields']}")

        # Calculate rows with complete data
        rows_with_complete_data = self.stats["processed"] - self.stats["missing_fields"]

        logger.info("")
        logger.info(f"  Rows with complete data: {rows_with_complete_data}")
        logger.info(f"    ├─ AthenaAppointmentId found: {self.stats['athena_id_found']}")
        logger.info(f"    │  ├─ Exact matches: {self.stats['athena_id_found'] - self.stats.get('field_mismatch', 0)}")
        logger.info(f"    │  └─ Field mismatches: {self.stats.get('field_mismatch', 0)}")
        logger.info(f"    └─ AthenaAppointmentId not found: {self.stats['athena_id_not_found']}")
        logger.info(f"       ├─ Secondary matches: {self.stats['secondary_matches']}")
        logger.info(f"       └─ No match found: {self.stats.get('not_found_mismatch', 0)}")

        logger.info("")
        logger.info(f"  Total matches: {self.stats['total_match']}")
        logger.info(
            f"  Total mismatches: {self.stats['total_mismatch']} ({self.stats.get('field_mismatch', 0)} field mismatches + {self.stats.get('not_found_mismatch', 0)} not found)"
        )

        # Verification math
        expected_total = self.stats["total_match"] + self.stats["total_mismatch"] + self.stats["missing_fields"]
        if expected_total == self.stats["processed"]:
            logger.info(
                f"  ✓ Math verified: {self.stats['total_match']} + {self.stats['total_mismatch']} + {self.stats['missing_fields']} = {self.stats['processed']}"
            )
        else:
            logger.warning(
                f"  ⚠ Math mismatch: {self.stats['total_match']} + {self.stats['total_mismatch']} + {self.stats['missing_fields']} = {expected_total} (expected {self.stats['processed']})"
            )
