"""
MongoDB Test Data Generator

Generates realistic fake data for MongoDB collections using the Faker library.
Python migration from JavaScript data_faker project.

Author: Demesew Abebe
Version: 1.0.0
Date: 2025-11-02
"""

import random
from datetime import datetime, timedelta

from bson import ObjectId
from faker import Faker


class DataGenerator:
    """Generate fake test data for MongoDB collections"""

    def __init__(self, seed: int | None = None):
        """
        Initialize the data generator with optional seed for reproducibility.

        Args:
            seed: Random seed for reproducible data generation
        """
        self.fake = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)

    def generate_random_date(self, start_date: datetime, end_date: datetime) -> datetime:
        """
        Generate a random date between start_date and end_date.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Random datetime within the range
        """
        return self.fake.date_time_between(start_date=start_date, end_date=end_date)

    def get_objectid_from_date(self, days_ago: int) -> ObjectId:
        """
        Generate an ObjectId with timestamp set to days_ago.

        Args:
            days_ago: Number of days in the past for the timestamp

        Returns:
            ObjectId with specified timestamp
        """
        date = datetime.now() - timedelta(days=days_ago)
        timestamp = int(date.timestamp())

        # Generate ObjectId with timestamp
        timestamp_hex = format(timestamp, "08x")

        # Generate random component (16 hex characters)
        random_component = format(random.randint(0, 0xFFFFFFFFFFFFFFFF), "016x")

        # Combine to create valid 24-character ObjectId
        objectid_str = timestamp_hex + random_component[:16]

        return ObjectId(objectid_str)

    def create_patient_acuity_intensity_history(self, include_null_id: bool = False) -> dict:
        """
        Generate a single patient acuity intensity history entry.

        Args:
            include_null_id: Whether to potentially include null _id

        Returns:
            Dictionary representing acuity intensity history entry
        """
        start_date = datetime(2020, 1, 1)
        end_date = datetime.now()

        # Determine _id (null or ObjectId)
        if include_null_id and self.fake.boolean():
            _id = None
        else:
            _id = ObjectId()

        return {
            "_id": _id,
            "AcuityLevel": self.fake.word(),
            "AcuityRef": self.fake.random_int(min=1, max=10000),
            "BHAcuityRef": self.fake.random_int(min=1, max=10000),
            "BHAcuityValue": self.fake.word(),
            "CreatedByName": self.fake.name(),
            "CreatedByRef": self.fake.uuid4(),
            "CreatedOn": self.generate_random_date(start_date, end_date),
            "CreatedTimeZone": self.fake.timezone(),
            "EmrId": self.fake.random_int(min=1, max=100000),
            "EndDate": self.generate_random_date(start_date, end_date) if self.fake.boolean() else None,
            "Intensity": self.fake.word(),
            "IntensityRef": self.fake.random_int(min=1, max=10000),
            "LastUpdatedBySystemRef": self.fake.random_int(min=1, max=100),
            "LastUpdatedBySystemValue": self.fake.word(),
            "NotesOnAcuityChange": self.fake.sentence(),
            "NotesUpdatedOn": self.generate_random_date(start_date, end_date),
            "PatientRef": self.fake.random_int(min=1, max=100000),
            "StartDate": self.generate_random_date(start_date, end_date),
            "UpdatedByName": self.fake.name(),
            "UpdatedByRef": self.fake.uuid4(),
            "UpdatedOn": self.generate_random_date(start_date, end_date),
            "UpdatedTimeZone": self.fake.timezone(),
        }

    def generate_mock_patient(self, inserted_by: str = "system") -> dict:
        """
        Generate a complete mock patient document with acuity history.

        Args:
            inserted_by: Username/system name that inserted the record

        Returns:
            Dictionary representing a complete patient document
        """
        # Generate 1-3 history entries
        history_count = random.randint(1, 3)
        include_null_id = True  # Flag to ensure at least one entry has _id as null

        history_array = []
        for _ in range(history_count):
            entry = self.create_patient_acuity_intensity_history(include_null_id)
            # Once a null _id is included, set the flag to false
            if entry["_id"] is None:
                include_null_id = False
            history_array.append(entry)

        return {
            "_id": self.get_objectid_from_date(random.randint(0, 7)),
            "PatientId": self.fake.random_int(min=1, max=100000),
            "FirstName": self.fake.first_name(),
            "MiddleName": self.fake.first_name(),  # Faker doesn't have middle_name
            "LastName": self.fake.last_name(),
            "PatientAcuityIntensityHistory": history_array,
            "RecordLastModifiedByRef": self.fake.uuid4(),
            "RecordLastModifiedUTC": datetime.utcnow(),
            "insertedBy": inserted_by,
            "insertedAt": datetime.utcnow(),
        }
