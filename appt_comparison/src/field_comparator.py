"""Field comparison module for appointment validation.

Handles field-by-field comparison between CSV and MongoDB data.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from csv_handler import format_date_for_mongo

from common_config.utils.logger import get_logger

logger = get_logger(__name__)


class FieldComparator:
    """Compares fields between CSV and MongoDB documents."""

    def __init__(self, case_sensitive_visit_type: bool = False, trim_strings: bool = True):
        """Initialize comparator with configuration.

        Args:
            case_sensitive_visit_type: Whether to compare VisitTypeValue case-sensitively
            trim_strings: Whether to trim whitespace before comparison
        """
        self.case_sensitive_visit_type = case_sensitive_visit_type
        self.trim_strings = trim_strings

    def compare_patient_ref(self, csv_value: str, mongo_value: Any) -> bool:
        """Compare PatientRef field (exact number match).

        Args:
            csv_value: PatientRef from CSV (string)
            mongo_value: PatientRef from MongoDB (number)

        Returns:
            True if values match
        """
        if not csv_value or not str(csv_value).strip():
            return False

        try:
            csv_num = int(csv_value.strip())

            # MongoDB value might be int or float
            if isinstance(mongo_value, (int, float)):
                # For float, check if it's a whole number
                if isinstance(mongo_value, float):
                    return csv_num == int(mongo_value) and mongo_value == int(mongo_value)
                return csv_num == mongo_value

            return False
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to compare PatientRef: csv='{csv_value}', mongo='{mongo_value}': {e}")
            return False

    def compare_visit_type(self, csv_value: str, mongo_value: Any) -> bool:
        """Compare VisitTypeValue field (case-insensitive, trimmed).

        Args:
            csv_value: VisitTypeValue from CSV
            mongo_value: VisitTypeValue from MongoDB

        Returns:
            True if values match
        """
        if not isinstance(mongo_value, str):
            return False

        csv_val = csv_value.strip() if self.trim_strings else csv_value
        mongo_val = mongo_value.strip() if self.trim_strings else mongo_value

        if self.case_sensitive_visit_type:
            return csv_val == mongo_val
        else:
            return csv_val.lower() == mongo_val.lower()

    def compare_availability_date(self, csv_date: datetime, mongo_date: Any) -> bool:
        """Compare AvailabilityDate field (date-only comparison).

        Args:
            csv_date: Parsed datetime from CSV
            mongo_date: Date from MongoDB (ISODate or string)

        Returns:
            True if dates match (ignoring time)
        """
        if not csv_date:
            return False

        csv_date_str = format_date_for_mongo(csv_date)

        # MongoDB date might be:
        # 1. datetime object (ISODate)
        # 2. dict with "$date" key ({"$date": "2018-05-21T00:00:00.000Z"})
        # 3. string (ISO string)
        if isinstance(mongo_date, datetime):
            mongo_date_str = format_date_for_mongo(mongo_date)
        elif isinstance(mongo_date, dict) and "$date" in mongo_date:
            # Handle {"$date": "2018-05-21T00:00:00.000Z"} format
            date_value = mongo_date["$date"]
            if isinstance(date_value, str):
                mongo_date_str = date_value.split("T")[0] if "T" in date_value else date_value
            elif isinstance(date_value, datetime):
                mongo_date_str = format_date_for_mongo(date_value)
            else:
                logger.debug(f"Unexpected $date value type: {type(date_value)}")
                return False
        elif isinstance(mongo_date, str):
            # Try to extract date part from ISO string
            mongo_date_str = mongo_date.split("T")[0] if "T" in mongo_date else mongo_date
        else:
            logger.debug(f"Unexpected mongo_date type: {type(mongo_date)}")
            return False

        return csv_date_str == mongo_date_str

    def compare_visit_start_time(self, csv_value: str, mongo_value: Any) -> bool:
        """Compare VisitStartDateTime field.

        Normalizes both values to HH:MM:SS format for comparison.
        CSV format: "1:35 PM" or "09:35 AM"
        MongoDB format: "09:35:00" (24-hour HH:MM:SS)

        Args:
            csv_value: VisitStartDateTime from CSV (e.g., "1:35 PM")
            mongo_value: VisitStartDateTime from MongoDB (e.g., "09:35:00")

        Returns:
            True if values match after normalization
        """
        if not isinstance(mongo_value, str):
            return False

        csv_val = csv_value.strip() if self.trim_strings else csv_value
        mongo_val = mongo_value.strip() if self.trim_strings else mongo_value

        try:
            # Parse CSV time (12-hour format with AM/PM)
            csv_time = datetime.strptime(csv_val, "%I:%M %p").time()

            # Parse MongoDB time (24-hour HH:MM:SS format)
            mongo_time = datetime.strptime(mongo_val, "%H:%M:%S").time()

            # Compare time objects
            return csv_time == mongo_time
        except ValueError:
            # If parsing fails, fall back to exact string match
            return csv_val == mongo_val

    def compare_all_fields(
        self,
        csv_row: dict[str, Any],
        mongo_appointment: dict[str, Any],
        csv_date: datetime,
        mongo_availability_date: Any,
    ) -> tuple[bool, list[str]]:
        """Compare all required fields between CSV and MongoDB.

        Args:
            csv_row: CSV row dictionary
            mongo_appointment: MongoDB appointment document
            csv_date: Parsed availability date from CSV
            mongo_availability_date: AvailabilityDate from MongoDB root

        Returns:
            Tuple of (all_match, mismatched_fields)
        """
        mismatched = []

        # Compare PatientRef
        if not self.compare_patient_ref(csv_row.get("PatientRef", ""), mongo_appointment.get("PatientRef")):
            mismatched.append("PatientRef")

        # Compare VisitTypeValue
        if not self.compare_visit_type(csv_row.get("VisitTypeValue", ""), mongo_appointment.get("VisitTypeValue")):
            mismatched.append("VisitTypeValue")

        # Compare AvailabilityDate
        if not self.compare_availability_date(csv_date, mongo_availability_date):
            mismatched.append("AvailabilityDate")

        # Compare VisitStartDateTime
        if not self.compare_visit_start_time(
            csv_row.get("VisitStartDateTime", ""), mongo_appointment.get("VisitStartDateTime")
        ):
            mismatched.append("VisitStartDateTime")

        all_match = len(mismatched) == 0

        return all_match, mismatched
