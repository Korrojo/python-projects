#!/usr/bin/env python3
"""Generate realistic test data based on PATH_MAPPING.

This script generates test data for MongoDB collections using the PATH_MAPPING
from collection_rule_mapping.py. It creates documents with the exact nested
structure needed for PHI masking validation.

Usage:
    # Generate 100 Patients documents
    python scripts/generate_test_data.py --collection Patients --size 100 --env LOCL

    # Generate 10K documents
    python scripts/generate_test_data.py --collection Patients --size 10000 --env LOCL
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from faker import Faker
from pymongo import MongoClient
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.collection_rule_mapping import PATH_MAPPING, get_phi_fields
from src.utils.env_config import get_env_config, load_shared_config

# Initialize Faker for realistic data generation
fake = Faker()


class PathBasedDataGenerator:
    """Generate realistic test data based on PATH_MAPPING."""

    def __init__(self, collection: str, batch_size: int = 1000):
        """Initialize the path-based data generator.

        Args:
            collection: Collection name
            batch_size: Number of documents to generate per batch
        """
        self.collection = collection
        self.batch_size = batch_size

        # Setup logging with proper file path: logs/test_data/YYYYMMDD_HHMMSS_<collectionname>.log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path("logs/test_data")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create custom log file name with timestamp and collection name
        log_file = log_dir / f"{timestamp}_{collection}.log"

        # Setup logging - configure to write to both console and file
        # Use consistent format across project: YYYY-MM-DD HH:MM:SS | LEVEL | message
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized test data generator for {collection}")
        self.logger.info(f"Log file: {log_file}")

        # Try to load sample file as template
        sample_file = Path(f"test-data/sample_{collection.lower()}.json")
        if sample_file.exists():
            self.logger.info(f"Found sample file: {sample_file}")
            self.use_template = True
            self.template_schema = self._load_and_parse_sample(sample_file)
            self.logger.info("Parsed template schema from sample file")
        else:
            self.logger.warning(f"No sample file found at {sample_file}, falling back to PATH_MAPPING")
            self.use_template = False
            # Get PATH_MAPPING for this collection
            self.path_mapping = PATH_MAPPING.get(collection, {})
            if not self.path_mapping:
                self.logger.warning(f"No PATH_MAPPING found for {collection}, will generate flat documents")
            # Parse the paths to understand document structure
            self.structure = self._parse_path_structure()
            self.logger.info(f"Parsed document structure: {len(self.structure)} top-level fields")

    def _load_and_parse_sample(self, sample_file: Path) -> dict[str, Any]:
        """Load and parse a sample JSON file to infer document structure.

        Args:
            sample_file: Path to sample JSON file

        Returns:
            Template schema dict
        """
        with sample_file.open() as f:
            sample_data = json.load(f)

        # Sample files are arrays of documents - use first document as template
        if isinstance(sample_data, list) and len(sample_data) > 0:
            sample_doc = sample_data[0]
        elif isinstance(sample_data, dict):
            sample_doc = sample_data
        else:
            raise ValueError(f"Invalid sample file format: {sample_file}")

        # Parse the structure recursively
        return self._infer_structure(sample_doc)

    def _infer_structure(self, obj: Any) -> Any:
        """Infer structure from a sample object.

        Args:
            obj: Sample object to analyze

        Returns:
            Structure template ("field", dict, or list)
        """
        if isinstance(obj, dict):
            # It's an object - recursively infer structure of nested fields
            # Skip _id field (MongoDB auto-generates it)
            return {key: self._infer_structure(value) for key, value in obj.items() if key != "_id"}

        elif isinstance(obj, list):
            # It's an array - infer structure from first item
            if len(obj) == 0:
                return []
            # Use first item as template
            return [self._infer_structure(obj[0])]

        else:
            # It's a leaf field (string, number, date, etc.)
            return "field"

    def _parse_path_structure(self) -> dict[str, Any]:
        """Parse PATH_MAPPING to understand document structure.

        Returns:
            Dictionary describing the document structure with arrays and objects
        """
        if not self.path_mapping:
            return {}

        structure = defaultdict(lambda: {"type": "unknown", "fields": {}})

        # Analyze all paths
        for field_name, path in self.path_mapping.items():
            parts = path.split(".")

            if len(parts) == 1:
                # Top-level field
                structure[path] = {"type": "field", "field_name": field_name}
            else:
                # Nested field - build structure
                self._add_to_structure(structure, parts, field_name)

        return dict(structure)

    def _add_to_structure(self, structure: dict, parts: list[str], field_name: str):
        """Add a path to the structure dictionary.

        Args:
            structure: Structure dictionary to update
            parts: Path parts (e.g., ['Address', 'Street1'])
            field_name: Original field name
        """
        root = parts[0]

        if root not in structure or structure[root]["type"] == "unknown":
            # Determine if this is likely an array based on naming patterns
            is_array = self._is_array_field(root)
            structure[root] = {"type": "array" if is_array else "object", "fields": {}}

        # Add nested fields
        if len(parts) == 2:
            structure[root]["fields"][parts[1]] = {"type": "field", "field_name": field_name}
        else:
            # Deeper nesting (e.g., PatientProblemList.EncounterProblemList.FinalNotes)
            current = structure[root]["fields"]
            for i in range(1, len(parts) - 1):
                part = parts[i]
                if part not in current:
                    is_array = self._is_array_field(part)
                    current[part] = {"type": "array" if is_array else "object", "fields": {}}
                current = current[part]["fields"]

            # Add the final field
            current[parts[-1]] = {"type": "field", "field_name": field_name}

    def _is_array_field(self, field_name: str) -> bool:
        """Determine if a field name suggests an array.

        Args:
            field_name: Field name to check

        Returns:
            True if likely an array, False otherwise
        """
        # Common array field patterns
        array_patterns = [
            "List",
            "Phones",
            "Specialists",
            "Activities",
            "Documents",
            "Contacts",  # Could be object or array
            "Medications",
            "Allergies",
            "Problems",
            "Appointments",
            "Slots",
        ]

        return any(pattern in field_name for pattern in array_patterns)

    def _generate_field_value(self, field_name: str) -> Any:
        """Generate a realistic value based on field name.

        Args:
            field_name: Name of the field

        Returns:
            Generated value
        """
        field_lower = field_name.lower()

        # Name fields
        if "firstname" in field_lower:
            return fake.first_name()
        elif "middlename" in field_lower:
            return fake.first_name()  # Use first name for middle name
        elif "lastname" in field_lower:
            return fake.last_name()
        elif "patientname" in field_lower or field_name == "PatientName":
            return f"{fake.first_name()} {fake.last_name()}"
        elif "username" in field_lower:
            return fake.user_name()
        elif "providername" in field_lower or "membername" in field_lower:
            return f"Dr. {fake.name()}"

        # Date fields
        elif "dob" in field_lower or "dateofbirth" in field_lower:
            # DOB should be date only (no time component)
            # Generate dates from 1970 onwards to avoid Extended JSON timestamp format
            dob = fake.date_time_between(start_date="-55y", end_date="-18y")
            return dob.replace(hour=0, minute=0, second=0, microsecond=0)
        elif "memberdobdate" in field_lower or "memberdob" in field_lower:
            # Member DOB should be date only (no time component)
            # Generate dates from 1970 onwards to avoid Extended JSON timestamp format
            dob = fake.date_time_between(start_date="-55y", end_date="-18y")
            return dob.replace(hour=0, minute=0, second=0, microsecond=0)
        elif "date" in field_lower or "createdat" in field_lower or "updatedat" in field_lower:
            return fake.date_time_between(start_date="-2y", end_date="now")
        elif "subscriptiondate" in field_lower or "activitydate" in field_lower or "calldate" in field_lower:
            return fake.date_time_between(start_date="-1y", end_date="now")

        # Contact fields
        elif "email" in field_lower:
            return fake.email()
        elif "phonetype" in field_lower:
            return fake.random_element(["Mobile", "Home", "Work"])
        elif "phone" in field_lower:
            return fake.numerify("##########")  # 10-digit number
        elif "fax" in field_lower or "mrr" in field_lower:
            return fake.numerify("##########")  # 10-digit number
        elif "ssn" in field_lower:
            return fake.ssn()
        elif "medicareid" in field_lower:
            return fake.bothify("?##-??-####").upper()

        # Address fields
        elif "street" in field_lower and "employer" not in field_lower:
            if "street1" in field_lower:
                return fake.street_address()
            elif "street2" in field_lower:
                return fake.secondary_address() if fake.boolean(chance_of_getting_true=40) else None
            return fake.street_address()
        elif "employerstreet" in field_lower:
            return fake.street_address()
        elif "city" in field_lower:
            return fake.city()
        elif "statename" in field_lower:
            return fake.state()
        elif "statecode" in field_lower or field_name == "StateCode":
            return fake.state_abbr()
        elif "zip" in field_lower:
            return fake.zipcode()
        elif "address" in field_lower and "visit" in field_lower:
            return f"{fake.street_address()}, {fake.city()}, {fake.state_abbr()}"

        # Medical fields
        elif "gender" in field_lower:
            return fake.random_element(["Male", "Female", "Other"])
        elif "specialtytype" in field_lower:
            return fake.random_element(["Cardiology", "Endocrinology", "Gastroenterology", "Psychiatry", "Neurology"])
        elif "phonetype" in field_lower:
            return fake.random_element(["Mobile", "Home", "Work"])
        elif "problem" in field_lower and "list" not in field_lower:
            return fake.random_element(["Diabetes", "Hypertension", "Asthma", "Arthritis", "Depression", "Anxiety"])

        # Text fields
        elif "notes" in field_lower or "finalnotes" in field_lower or "comments" in field_lower:
            return fake.sentence(nb_words=10)
        elif "reason" in field_lower and "other" not in field_lower:
            return fake.random_element(
                [
                    "Appointment confirmation",
                    "Medication refill reminder",
                    "Annual wellness check reminder",
                    "Flu vaccination reminder",
                ]
            )
        elif "otherreason" in field_lower:
            return fake.sentence(nb_words=15)
        elif "goals" in field_lower or "snapshot" in field_lower:
            return fake.sentence(nb_words=12)
        elif "relationship" in field_lower:
            return fake.random_element(["Spouse", "Parent", "Sibling", "Child", "Friend"])

        # Boolean fields
        elif "isactive" in field_lower or "enabled" in field_lower:
            return fake.boolean(chance_of_getting_true=90)

        # Number fields
        elif "number" in field_lower and "record" in field_lower:
            return fake.bothify("MRN-########")

        # Default fallback
        else:
            return fake.word()

    def _generate_nested_object(self, structure: dict) -> dict[str, Any]:
        """Generate a nested object based on structure.

        Args:
            structure: Structure definition

        Returns:
            Generated nested object
        """
        result = {}

        for key, value in structure.items():
            if value["type"] == "field":
                # Generate field value
                result[key] = self._generate_field_value(value["field_name"])

            elif value["type"] == "object":
                # Generate nested object
                if "fields" in value:
                    result[key] = self._generate_nested_object(value["fields"])
                else:
                    result[key] = {}

            elif value["type"] == "array":
                # Generate array of objects
                array_length = fake.random_int(min=1, max=3)  # 1-3 items per array
                if "fields" in value:
                    result[key] = [self._generate_nested_object(value["fields"]) for _ in range(array_length)]
                else:
                    result[key] = []

        return result

    def _generate_from_template(self, schema: dict | list) -> Any:
        """Generate data from template schema.

        Args:
            schema: Template schema (dict, list, or "field")

        Returns:
            Generated data matching the schema structure
        """
        if isinstance(schema, dict):
            # Check if it's an object with fields
            result = {}
            for key, value in schema.items():
                if value == "field":
                    # Generate field value
                    result[key] = self._generate_field_value(key)
                else:
                    # Nested object or array
                    result[key] = self._generate_from_template(value)
            return result

        elif isinstance(schema, list):
            # Array - generate 1-3 items
            if len(schema) == 0:
                return []
            array_length = fake.random_int(min=1, max=3)
            item_template = schema[0]
            return [self._generate_from_template(item_template) for _ in range(array_length)]

        elif schema == "field":
            return fake.word()

        else:
            return None

    def _apply_derived_fields(self, document: dict) -> dict:
        """Apply derived field rules (e.g., FirstNameLower from FirstName).

        Args:
            document: Generated document

        Returns:
            Document with derived fields corrected
        """
        # Lowercase name fields
        if "FirstName" in document and "FirstNameLower" in document:
            document["FirstNameLower"] = document["FirstName"].lower()

        if "MiddleName" in document and "MiddleNameLower" in document:
            document["MiddleNameLower"] = document["MiddleName"].lower()

        if "LastName" in document and "LastNameLower" in document:
            document["LastNameLower"] = document["LastName"].lower()

        return document

    def generate_document(self) -> dict[str, Any]:
        """Generate a single document based on template or PATH_MAPPING.

        Returns:
            Generated document dictionary
        """
        if self.use_template:
            # Use template schema
            document = self._generate_from_template(self.template_schema)
            # Apply derived field rules
            document = self._apply_derived_fields(document)
            return document
        else:
            # Fall back to PATH_MAPPING approach
            if not self.structure:
                # No PATH_MAPPING - generate basic document
                return {"_id": None, "name": fake.name(), "created_at": datetime.now()}

            document = self._generate_nested_object(self.structure)
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
        self, mongo_uri: str, database: str, collection: str, total_count: int, clear_existing: bool = True
    ) -> int:
        """Generate and insert documents into MongoDB.

        Args:
            mongo_uri: MongoDB connection URI
            database: Database name
            collection: Collection name
            total_count: Total number of documents to generate
            clear_existing: Whether to clear existing data

        Returns:
            Number of documents inserted
        """
        self.logger.info(f"Connecting to MongoDB: {database}.{collection}")
        client = MongoClient(mongo_uri)
        db = client[database]
        coll = db[collection]

        if clear_existing:
            self.logger.info(f"Clearing existing data from {database}.{collection}")
            delete_result = coll.delete_many({})
            self.logger.info(f"Deleted {delete_result.deleted_count} existing documents")

        inserted_count = 0
        batches = (total_count + self.batch_size - 1) // self.batch_size

        self.logger.info(f"Generating {total_count} documents in {batches} batches of {self.batch_size}")

        with tqdm(total=total_count, desc="Generating documents") as pbar:
            for batch_num in range(batches):
                # Determine batch size for last batch
                remaining = total_count - inserted_count
                current_batch_size = min(self.batch_size, remaining)

                # Generate batch
                documents = self.generate_batch(current_batch_size)

                # Insert batch
                try:
                    result = coll.insert_many(documents, ordered=False)
                    inserted_count += len(result.inserted_ids)
                    pbar.update(len(result.inserted_ids))
                except Exception as e:
                    self.logger.error(f"Error inserting batch {batch_num}: {e}")
                    raise

        client.close()

        self.logger.info(f"✓ Successfully inserted {inserted_count} documents")
        return inserted_count


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate realistic test data for MongoDB collections using PATH_MAPPING",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 100 Patients using PATH_MAPPING
  python scripts/generate_test_data.py --collection Patients --size 100 --env LOCL

  # Generate 10K documents
  python scripts/generate_test_data.py --collection Patients --size 10000 --env DEV

  # Generate with database override
  python scripts/generate_test_data.py --collection Patients --size 100000 --env LOCL --db localdb-unmasked
        """,
    )

    parser.add_argument("--collection", required=True, help="Collection name")

    parser.add_argument("--size", type=int, default=100, help="Number of documents to generate (default: 100)")

    parser.add_argument(
        "--env",
        required=True,
        choices=["LOCL", "DEV", "STG", "TRNG", "PERF", "PRPRD", "PROD"],
        help="Target environment",
    )

    parser.add_argument("--db", help="Database name override (uses DATABASE_NAME_{env} if not specified)")

    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for inserts (default: 1000)")

    parser.add_argument(
        "--keep-existing", action="store_true", help="Keep existing documents (default: clear before generating)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("MongoDB PHI Masker - Test Data Generator (PATH_MAPPING Based)")
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

        # Check if we have sample file or PATH_MAPPING
        sample_file = Path(f"test-data/sample_{args.collection.lower()}.json")
        if sample_file.exists():
            print(f"✓ Using sample file as template: {sample_file}")
        elif args.collection in PATH_MAPPING:
            print(f"✓ Using PATH_MAPPING with {len(PATH_MAPPING[args.collection])} field mappings")
        else:
            print(f"⚠ Warning: No sample file or PATH_MAPPING found for {args.collection}")
            print("Will generate basic documents.")
            print("")

        # Get PHI fields
        try:
            phi_fields = get_phi_fields(args.collection)
            print(f"PHI fields: {len(phi_fields)}")
        except Exception as e:
            print(f"Warning: Could not load PHI fields: {e}")
            phi_fields = []

        print("")

        # Initialize generator
        generator = PathBasedDataGenerator(collection=args.collection, batch_size=args.batch_size)

        # Generate and insert data
        start_time = datetime.now()

        inserted_count = generator.generate_and_insert(
            mongo_uri=env_config["uri"],
            database=env_config["database"],
            collection=args.collection,
            total_count=args.size,
            clear_existing=not args.keep_existing,
        )

        elapsed_time = (datetime.now() - start_time).total_seconds()

        # Log and print summary
        print("")
        print("=" * 70)
        print("Generation Complete!")
        print("=" * 70)
        print(f"Documents inserted: {inserted_count:,}")
        print(f"Elapsed time: {elapsed_time:.2f}s")
        print(f"Throughput: {inserted_count / elapsed_time:.0f} docs/sec")
        print("=" * 70)

        # Also log to file
        generator.logger.info("=" * 70)
        generator.logger.info("Generation Complete!")
        generator.logger.info("=" * 70)
        generator.logger.info(f"Documents inserted: {inserted_count:,}")
        generator.logger.info(f"Elapsed time: {elapsed_time:.2f}s")
        generator.logger.info(f"Throughput: {inserted_count / elapsed_time:.0f} docs/sec")
        generator.logger.info("=" * 70)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
