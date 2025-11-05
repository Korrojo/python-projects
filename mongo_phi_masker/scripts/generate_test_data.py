#!/usr/bin/env python3
"""Generate realistic test data based on collection schema.

This script generates test data for MongoDB collections based on schema definitions
and PHI field configurations. It supports generating 10K-100K documents with
realistic, diverse data for testing the PHI masking pipeline.

Usage:
    # Generate 10K Patients documents
    python scripts/generate_test_data.py --collection Patients --size 10000 --env LOCL

    # With custom schema file
    python scripts/generate_test_data.py --collection Patients --schema-file schemas/patients.json --size 50000 --env LOCL
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from faker import Faker
from pymongo import MongoClient
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.collection_rule_mapping import get_phi_fields
from src.utils.env_config import get_env_config, load_shared_config

# Initialize Faker for realistic data generation
fake = Faker()


class TestDataGenerator:
    """Generate realistic test data based on schema."""

    def __init__(
        self,
        collection: str,
        schema: dict[str, Any],
        phi_fields: list[str],
        batch_size: int = 1000,
    ):
        """Initialize the test data generator.

        Args:
            collection: Collection name
            schema: Schema definition (field types and constraints)
            phi_fields: List of PHI field paths
            batch_size: Number of documents to generate per batch
        """
        self.collection = collection
        self.schema = schema
        self.phi_fields = set(phi_fields)
        self.batch_size = batch_size
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        return logging.getLogger(__name__)

    def generate_field_value(self, field_name: str, field_config: dict[str, Any]) -> Any:
        """Generate a realistic value for a field based on its type and name.

        Args:
            field_name: Name of the field
            field_config: Field configuration (type, constraints)

        Returns:
            Generated value
        """
        field_type = field_config.get("type", "string")
        is_phi = field_name in self.phi_fields

        # String fields
        if field_type == "string":
            if "FirstName" in field_name or field_name == "first_name":
                return fake.first_name()
            elif "LastName" in field_name or field_name == "last_name":
                return fake.last_name()
            elif "Email" in field_name or field_name == "email":
                return fake.email()
            elif "Phone" in field_name or field_name == "phone":
                return fake.phone_number()
            elif "Address" in field_name or "Street" in field_name:
                return fake.street_address()
            elif "City" in field_name:
                return fake.city()
            elif "State" in field_name:
                return fake.state_abbr()
            elif "Zip" in field_name or "Postal" in field_name:
                return fake.zipcode()
            elif "SSN" in field_name or "SocialSecurity" in field_name:
                return fake.ssn()
            elif "Gender" in field_name:
                return fake.random_element(["Male", "Female", "Other", "Unknown"])
            else:
                # Default string
                return fake.word() if not is_phi else fake.name()

        # Date fields
        elif field_type == "date" or "Date" in field_name:
            if "Birth" in field_name or "DOB" in field_name:
                # Generate DOB between 18-80 years ago
                start_date = datetime.now() - timedelta(days=365 * 80)
                end_date = datetime.now() - timedelta(days=365 * 18)
                return fake.date_time_between(start_date=start_date, end_date=end_date)
            else:
                # Recent date (within last 5 years)
                return fake.date_time_between(start_date="-5y", end_date="now")

        # Number fields
        elif field_type in ["int", "integer"]:
            min_val = field_config.get("min", 0)
            max_val = field_config.get("max", 100000)
            return fake.random_int(min=min_val, max=max_val)

        elif field_type in ["float", "double", "number"]:
            min_val = field_config.get("min", 0.0)
            max_val = field_config.get("max", 100000.0)
            return round(fake.pyfloat(min_value=min_val, max_value=max_val), 2)

        # Boolean fields
        elif field_type == "boolean":
            return fake.boolean()

        # Array fields
        elif field_type == "array":
            item_config = field_config.get("items", {"type": "string"})
            array_length = fake.random_int(min=0, max=field_config.get("maxItems", 5))
            return [
                self.generate_field_value(f"{field_name}_item", item_config)
                for _ in range(array_length)
            ]

        # Object fields
        elif field_type == "object":
            properties = field_config.get("properties", {})
            return {
                prop_name: self.generate_field_value(f"{field_name}.{prop_name}", prop_config)
                for prop_name, prop_config in properties.items()
            }

        # Default
        else:
            return fake.word()

    def generate_document(self) -> dict[str, Any]:
        """Generate a single document based on schema.

        Returns:
            Generated document dictionary
        """
        document = {}

        for field_name, field_config in self.schema.items():
            # Check if field is required
            if field_config.get("required", True):
                document[field_name] = self.generate_field_value(field_name, field_config)
            else:
                # Optional field - 80% chance of inclusion
                if fake.boolean(chance_of_getting_true=80):
                    document[field_name] = self.generate_field_value(field_name, field_config)

        return document

    def generate_batch(self, batch_size: int) -> list[dict[str, Any]]:
        """Generate a batch of documents.

        Args:
            batch_size: Number of documents to generate

        Returns:
            List of generated documents
        """
        return [self.generate_document() for _ in range(batch_size)]

    def generate_and_insert(
        self, mongo_uri: str, database: str, collection: str, total_count: int
    ) -> int:
        """Generate and insert documents into MongoDB.

        Args:
            mongo_uri: MongoDB connection URI
            database: Database name
            collection: Collection name
            total_count: Total number of documents to generate

        Returns:
            Number of documents inserted
        """
        self.logger.info(f"Connecting to MongoDB: {database}.{collection}")
        client = MongoClient(mongo_uri)
        db = client[database]
        coll = db[collection]

        # Clear existing data (optional - can be made configurable)
        self.logger.info(f"Clearing existing data from {database}.{collection}")
        coll.delete_many({})

        inserted_count = 0
        batches = (total_count + self.batch_size - 1) // self.batch_size

        self.logger.info(
            f"Generating {total_count} documents in {batches} batches of {self.batch_size}"
        )

        with tqdm(total=total_count, desc="Generating documents") as pbar:
            for batch_num in range(batches):
                # Determine batch size for last batch
                remaining = total_count - inserted_count
                current_batch_size = min(self.batch_size, remaining)

                # Generate batch
                documents = self.generate_batch(current_batch_size)

                # Insert batch
                result = coll.insert_many(documents, ordered=False)
                inserted_count += len(result.inserted_ids)

                pbar.update(len(result.inserted_ids))

        client.close()

        self.logger.info(f"✓ Successfully inserted {inserted_count} documents")
        return inserted_count


def load_schema(schema_file: Path) -> dict[str, Any]:
    """Load schema from file.

    Args:
        schema_file: Path to schema file

    Returns:
        Schema dictionary

    Raises:
        FileNotFoundError: If schema file doesn't exist
        json.JSONDecodeError: If schema file has invalid JSON
    """
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    with schema_file.open() as f:
        return json.load(f)


def get_default_patient_schema() -> dict[str, Any]:
    """Get default schema for Patients collection.

    Returns:
        Default patient schema
    """
    return {
        # "_id" is auto-generated by MongoDB, don't include it
        "FirstName": {"type": "string", "required": True},
        "LastName": {"type": "string", "required": True},
        "DateOfBirth": {"type": "date", "required": True},
        "Gender": {"type": "string", "required": True},
        "Email": {"type": "string", "required": True},
        "Phone": {"type": "string", "required": True},
        "Address": {
            "type": "object",
            "required": True,
            "properties": {
                "Street": {"type": "string"},
                "City": {"type": "string"},
                "State": {"type": "string"},
                "ZipCode": {"type": "string"},
            },
        },
        "SSN": {"type": "string", "required": True},
        "MedicalRecordNumber": {"type": "string", "required": True},
        "InsuranceNumber": {"type": "string", "required": False},
        "EmergencyContact": {
            "type": "object",
            "required": False,
            "properties": {
                "Name": {"type": "string"},
                "Phone": {"type": "string"},
                "Relationship": {"type": "string"},
            },
        },
        "Allergies": {
            "type": "array",
            "required": False,
            "maxItems": 5,
            "items": {"type": "string"},
        },
        "Medications": {
            "type": "array",
            "required": False,
            "maxItems": 10,
            "items": {"type": "string"},
        },
        "CreatedAt": {"type": "date", "required": True},
        "UpdatedAt": {"type": "date", "required": True},
        "IsActive": {"type": "boolean", "required": True},
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate realistic test data for MongoDB collections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 10K Patients using default schema
  python scripts/generate_test_data.py --collection Patients --size 10000 --env LOCL

  # Generate with custom schema file
  python scripts/generate_test_data.py --collection Patients --schema-file schemas/patients.json --size 50000 --env DEV

  # Generate with database override
  python scripts/generate_test_data.py --collection Patients --size 100000 --env LOCL --db localdb-unmasked
        """,
    )

    parser.add_argument("--collection", required=True, help="Collection name")

    parser.add_argument(
        "--schema-file",
        type=Path,
        help="Path to schema JSON file (if not provided, uses default schema)",
    )

    parser.add_argument(
        "--size",
        type=int,
        default=10000,
        help="Number of documents to generate (default: 10000)",
    )

    parser.add_argument(
        "--env",
        required=True,
        choices=["LOCL", "DEV", "STG", "TRNG", "PERF", "PRPRD", "PROD"],
        help="Target environment",
    )

    parser.add_argument(
        "--db", help="Database name override (uses DATABASE_NAME_{env} if not specified)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for inserts (default: 1000)",
    )

    parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="Clear existing documents before generating (default: True)",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("MongoDB PHI Masker - Test Data Generator")
    print("=" * 70)
    print(f"Collection: {args.collection}")
    print(f"Target Size: {args.size:,} documents")
    print(f"Environment: {args.env}")
    print("")

    try:
        # Load shared config
        load_shared_config()

        # Get environment configuration
        env_config = get_env_config(args.env, args.db)
        print(f"Target Database: {env_config['database']}")
        print(f"MongoDB URI: {env_config['uri']}")
        print("")

        # Load schema
        if args.schema_file:
            print(f"Loading schema from: {args.schema_file}")
            schema = load_schema(args.schema_file)
        else:
            print("Using default Patients schema")
            schema = get_default_patient_schema()

        print(f"Schema fields: {len(schema)}")

        # Get PHI fields
        try:
            phi_fields = get_phi_fields(args.collection)
            print(f"PHI fields: {len(phi_fields)}")
        except Exception as e:
            print(f"Warning: Could not load PHI fields: {e}")
            phi_fields = []

        print("")

        # Initialize generator
        generator = TestDataGenerator(
            collection=args.collection,
            schema=schema,
            phi_fields=phi_fields,
            batch_size=args.batch_size,
        )

        # Generate and insert data
        start_time = datetime.now()

        inserted_count = generator.generate_and_insert(
            mongo_uri=env_config["uri"],
            database=env_config["database"],
            collection=args.collection,
            total_count=args.size,
        )

        elapsed_time = (datetime.now() - start_time).total_seconds()

        print("")
        print("=" * 70)
        print("Generation Complete!")
        print("=" * 70)
        print(f"Documents inserted: {inserted_count:,}")
        print(f"Elapsed time: {elapsed_time:.2f}s")
        print(f"Throughput: {inserted_count / elapsed_time:.0f} docs/sec")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
