"""MongoDB matching module for appointment lookup.

Handles primary (AthenaAppointmentId) and secondary (4-field) matching logic.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from csv_handler import format_date_for_mongo
from pymongo.database import Database

from common_config.utils.logger import get_logger

logger = get_logger(__name__)


class MongoMatcher:
    """Handles MongoDB queries for appointment matching."""

    def __init__(
        self,
        db: Database,
        collection_name: str,
        max_retries: int = 3,
        base_retry_sleep: float = 2.0,
        min_date: datetime | None = None,
        max_date: datetime | None = None,
    ):
        """Initialize MongoDB matcher.

        Args:
            db: MongoDB database connection
            collection_name: Name of StaffAvailability collection
            max_retries: Maximum retry attempts for queries
            base_retry_sleep: Base sleep time for exponential backoff
            min_date: Minimum AvailabilityDate to filter (optional optimization)
            max_date: Maximum AvailabilityDate to filter (optional optimization)
        """
        self.db = db
        self.collection_name = collection_name
        self.collection = db[collection_name]
        self.max_retries = max_retries
        self.base_retry_sleep = base_retry_sleep
        self.min_date = min_date
        self.max_date = max_date

    def _retry_query(self, query_func, *args, **kwargs) -> Any:
        """Execute query with retry logic.

        Args:
            query_func: Query function to execute
            *args: Positional arguments for query function
            **kwargs: Keyword arguments for query function

        Returns:
            Query result

        Raises:
            Exception: If all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return query_func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    sleep_time = self.base_retry_sleep * (2**attempt)
                    logger.warning(
                        f"Query failed (attempt {attempt + 1}/{self.max_retries}): {e}. Retrying in {sleep_time}s..."
                    )
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Query failed after {self.max_retries} attempts: {e}")

        raise last_exception  # type: ignore

    def find_by_athena_id_batch(self, athena_ids: list[Any]) -> dict[Any, dict[str, Any]]:
        """Find appointments by AthenaAppointmentId in batch.

        Args:
            athena_ids: List of AthenaAppointmentId values

        Returns:
            Dictionary mapping AthenaAppointmentId to appointment data:
            {
                athena_id: {
                    "appointment": {...},
                    "availability_date": ISODate(...)
                }
            }
        """
        if not athena_ids:
            return {}

        # Convert to appropriate types (handle mixed int/string)
        processed_ids = []
        for aid in athena_ids:
            if aid is None or aid == "":
                continue
            # Try as int first, fallback to string
            try:
                processed_ids.append(int(aid))
            except (ValueError, TypeError):
                processed_ids.append(str(aid))

        if not processed_ids:
            return {}

        def _query():
            # Build the match filter
            match_filter: dict[str, Any] = {
                "Slots.Appointments.0": {"$exists": True},  # Has at least one appointment
            }

            # Add date range filter if available (HUGE performance boost!)
            if self.min_date and self.max_date:
                match_filter["AvailabilityDate"] = {"$gte": self.min_date, "$lt": self.max_date}

            pipeline = [
                # OPTIMIZATION: Filter early to reduce documents before unwind
                {"$match": match_filter},
                # Unwind slots
                {"$unwind": "$Slots"},
                # Unwind appointments
                {"$unwind": "$Slots.Appointments"},
                # Match AthenaAppointmentId (index used here!)
                {"$match": {"Slots.Appointments.AthenaAppointmentId": {"$in": processed_ids}}},
                # Project needed fields
                {
                    "$project": {
                        "_id": 0,
                        "AthenaAppointmentId": "$Slots.Appointments.AthenaAppointmentId",
                        "PatientRef": "$Slots.Appointments.PatientRef",
                        "VisitTypeValue": "$Slots.Appointments.VisitTypeValue",
                        "VisitStartDateTime": "$Slots.Appointments.VisitStartDateTime",
                        "AvailabilityDate": "$AvailabilityDate",
                    }
                },
            ]

            return list(self.collection.aggregate(pipeline))

        results = self._retry_query(_query)

        # Build lookup dictionary
        lookup = {}
        for doc in results:
            athena_id = doc.get("AthenaAppointmentId")
            if athena_id:
                lookup[athena_id] = {"appointment": doc, "availability_date": doc.get("AvailabilityDate")}

        logger.debug(f"Found {len(lookup)} appointments from {len(processed_ids)} IDs queried")

        return lookup

    def find_by_four_fields(
        self, patient_ref: int, visit_type: str, availability_date: datetime, visit_start_time: str
    ) -> dict[str, Any] | None:
        """Find appointment by 4-field combination (secondary matching).

        Args:
            patient_ref: PatientRef value
            visit_type: VisitTypeValue (case-insensitive)
            availability_date: Parsed availability date
            visit_start_time: VisitStartDateTime value

        Returns:
            Dictionary with appointment and availability_date, or None if not found
        """
        # Format date for MongoDB query (date-only)
        date_str = format_date_for_mongo(availability_date)

        def _query():
            pipeline = [
                # Match AvailabilityDate (date part only)
                {
                    "$match": {
                        "$expr": {
                            "$eq": [{"$dateToString": {"format": "%Y-%m-%d", "date": "$AvailabilityDate"}}, date_str]
                        }
                    }
                },
                # Unwind slots
                {"$unwind": "$Slots"},
                # Unwind appointments
                {"$unwind": "$Slots.Appointments"},
                # Match appointment fields
                {
                    "$match": {
                        "Slots.Appointments.PatientRef": patient_ref,
                        "Slots.Appointments.VisitStartDateTime": visit_start_time,
                    }
                },
                # Case-insensitive VisitTypeValue match
                {
                    "$match": {
                        "$expr": {"$eq": [{"$toLower": "$Slots.Appointments.VisitTypeValue"}, visit_type.lower()]}
                    }
                },
                # Project needed fields
                {
                    "$project": {
                        "_id": 0,
                        "AthenaAppointmentId": "$Slots.Appointments.AthenaAppointmentId",
                        "PatientRef": "$Slots.Appointments.PatientRef",
                        "VisitTypeValue": "$Slots.Appointments.VisitTypeValue",
                        "VisitStartDateTime": "$Slots.Appointments.VisitStartDateTime",
                        "AvailabilityDate": "$AvailabilityDate",
                    }
                },
                # Limit to first match
                {"$limit": 1},
            ]

            return list(self.collection.aggregate(pipeline))

        results = self._retry_query(_query)

        if results:
            doc = results[0]
            return {"appointment": doc, "availability_date": doc.get("AvailabilityDate")}

        return None
