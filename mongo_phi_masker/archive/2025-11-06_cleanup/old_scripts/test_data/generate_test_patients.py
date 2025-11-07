#!/usr/bin/env python3
"""
Generate realistic test patient data using Faker library.
Focuses on 34 PHI fields identified in the Patients collection.

Usage:
    # Generate 100 patients to JSON
    python scripts/generate_test_patients.py --count 100 --output test-data/test_patients.json

    # Generate and load into MongoDB
    python scripts/generate_test_patients.py --count 1000 \\
        --mongo-uri "mongodb://localhost:27017" \\
        --database local_test_db \\
        --collection Patients
"""

import json
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from faker import Faker


class PatientDataGenerator:
    """Generates test patient documents with realistic PHI data."""

    # US State abbreviation to full name mapping
    STATE_MAP = {
        "AL": "Alabama",
        "AK": "Alaska",
        "AZ": "Arizona",
        "AR": "Arkansas",
        "CA": "California",
        "CO": "Colorado",
        "CT": "Connecticut",
        "DE": "Delaware",
        "FL": "Florida",
        "GA": "Georgia",
        "HI": "Hawaii",
        "ID": "Idaho",
        "IL": "Illinois",
        "IN": "Indiana",
        "IA": "Iowa",
        "KS": "Kansas",
        "KY": "Kentucky",
        "LA": "Louisiana",
        "ME": "Maine",
        "MD": "Maryland",
        "MA": "Massachusetts",
        "MI": "Michigan",
        "MN": "Minnesota",
        "MS": "Mississippi",
        "MO": "Missouri",
        "MT": "Montana",
        "NE": "Nebraska",
        "NV": "Nevada",
        "NH": "New Hampshire",
        "NJ": "New Jersey",
        "NM": "New Mexico",
        "NY": "New York",
        "NC": "North Carolina",
        "ND": "North Dakota",
        "OH": "Ohio",
        "OK": "Oklahoma",
        "OR": "Oregon",
        "PA": "Pennsylvania",
        "RI": "Rhode Island",
        "SC": "South Carolina",
        "SD": "South Dakota",
        "TN": "Tennessee",
        "TX": "Texas",
        "UT": "Utah",
        "VT": "Vermont",
        "VA": "Virginia",
        "WA": "Washington",
        "WV": "West Virginia",
        "WI": "Wisconsin",
        "WY": "Wyoming",
        "DC": "District of Columbia",
    }

    MEDICAL_PROBLEMS = [
        "Hypertension",
        "Type 2 Diabetes",
        "Asthma",
        "Arthritis",
        "Chronic Back Pain",
        "Migraine",
        "GERD",
        "Depression",
        "Anxiety",
        "Hyperlipidemia",
    ]

    SPECIALTIES = [
        "Cardiology",
        "Dermatology",
        "Orthopedics",
        "Endocrinology",
        "Neurology",
        "Gastroenterology",
        "Psychiatry",
    ]

    OUTREACH_REASONS = [
        "Annual wellness check reminder",
        "Flu vaccination reminder",
        "Medication refill reminder",
        "Lab work follow-up",
        "Preventive screening reminder",
        "Appointment confirmation",
    ]

    def __init__(self, seed: int = 42):
        """Initialize generator with optional seed for reproducibility."""
        self.fake = Faker("en_US")
        Faker.seed(seed)
        random.seed(seed)

    def generate_patient(self) -> dict[str, Any]:
        """Generate a single patient document with all 34 PHI fields."""

        # Generate consistent name data (normal capitalization for realistic data)
        first_name = self.fake.first_name()
        middle_name = self.fake.first_name()
        last_name = self.fake.last_name()

        # Generate address data (keep StateCode consistent with StateName)
        state_abbr = self.fake.state_abbr()
        state_name = self.STATE_MAP.get(state_abbr, state_abbr)

        return {
            # Top-level Personal Info (9 fields)
            "FirstName": first_name,
            "MiddleName": middle_name,
            "LastName": last_name,
            "FirstNameLower": first_name.lower(),
            "MiddleNameLower": middle_name.lower(),
            "LastNameLower": last_name.lower(),
            "Email": self.fake.email(),
            "Dob": self.fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(),
            "Gender": random.choice(["Male", "Female", "Other"]),
            "MedicareId": self.fake.bothify("?##-??-####").upper(),
            # Address nested object (6 fields)
            "Address": {
                "Street1": self.fake.street_address(),
                "Street2": (self.fake.secondary_address() if random.random() > 0.5 else None),
                "City": self.fake.city(),
                "StateName": state_name,
                "StateCode": state_abbr,
                "Zip5": self.fake.zipcode()[:5],
            },
            # Phones nested array (2 fields)
            "Phones": [
                {
                    "PhoneType": "Mobile",
                    "PhoneNumber": self.fake.numerify("##########"),
                    "Notes": self.fake.sentence(nb_words=10),
                }
            ],
            # Contacts nested object (2 fields)
            "Contacts": {
                "HomePhoneNumber": self.fake.numerify("##########"),
                "WorkPhoneNumber": self.fake.numerify("##########"),
            },
            # Pcp (Primary Care Provider) nested object (3 fields)
            "Pcp": {
                "ProviderName": f"Dr. {self.fake.name()}",
                "Fax": self.fake.numerify("##########"),
                "PcpSecondaryFaxNumber": self.fake.numerify("##########"),
                "MRRFax": self.fake.numerify("##########"),
            },
            # Insurance nested object (3 fields)
            "Insurance": {
                "PrimaryMemberName": self.fake.name(),
                "PrimaryMemberDOB": self.fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(),
                "EmployerStreet": self.fake.street_address(),
            },
            # Specialists nested array (2 fields)
            "Specialists": [
                {
                    "SpecialtyType": random.choice(self.SPECIALTIES),
                    "MRRFaxNumber": self.fake.numerify("##########"),
                    "FaxNumber2": self.fake.numerify("##########"),
                }
            ],
            # PatientCallLog nested array (2 fields)
            "PatientCallLog": [
                {
                    "CallDate": self.fake.date_time_this_year().isoformat(),
                    "PatientName": f"{first_name} {last_name}",
                    "VisitAddress": f"{self.fake.street_address()}, {self.fake.city()}, {state_abbr}",
                }
            ],
            # PatientProblemList nested structure (2 fields)
            "PatientProblemList": {
                "EncounterProblemList": [
                    {
                        "Problem": random.choice(self.MEDICAL_PROBLEMS),
                        "FinalNotes": self.fake.text(max_nb_chars=200),
                        "Comments": self.fake.text(max_nb_chars=150),
                    }
                ]
            },
            # SubscribedUserDetails nested object (1 field)
            "SubscribedUserDetails": {
                "UserName": self.fake.user_name(),
                "SubscriptionDate": self.fake.date_time_this_year().isoformat(),
            },
            # OutreachActivitiesList nested array (1 field)
            "OutreachActivitiesList": [
                {
                    "ActivityDate": self.fake.date_time_this_month().isoformat(),
                    "Reason": random.choice(self.OUTREACH_REASONS),
                }
            ],
            # PatientDat nested object (1 field)
            "PatientDat": {"OtherReason": self.fake.sentence(nb_words=10)},
        }

    def generate_batch(self, count: int) -> list[dict[str, Any]]:
        """Generate a batch of patient documents."""
        print(f"Generating {count} patient documents...")
        patients = []
        for i in range(count):
            if (i + 1) % 100 == 0:
                print(f"  Generated {i + 1}/{count} documents...")
            patients.append(self.generate_patient())
        return patients

    def save_to_json(self, patients: list[dict[str, Any]], filepath: str):
        """Save generated patients to JSON file."""
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            json.dump(patients, f, indent=2, default=str)

        print(f"✓ Generated {len(patients)} patient documents → {filepath}")

    def save_to_mongodb(
        self,
        patients: list[dict[str, Any]],
        connection_string: str,
        database: str,
        collection: str,
    ):
        """Save generated patients directly to MongoDB."""
        try:
            from pymongo import MongoClient
        except ImportError:
            print("ERROR: pymongo not installed. Install with: pip install pymongo")
            sys.exit(1)

        print(f"Connecting to MongoDB: {database}.{collection}")
        client = MongoClient(connection_string)

        try:
            db = client[database]
            coll = db[collection]

            result = coll.insert_many(patients)
            print(f"✓ Inserted {len(result.inserted_ids)} documents into {database}.{collection}")
        finally:
            client.close()


def main():
    """CLI entry point for test data generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate test patient data with Faker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 100 patients to JSON file
  python scripts/generate_test_patients.py --count 100 --output test-data/test_patients.json

  # Generate and load into LOCAL MongoDB
  python scripts/generate_test_patients.py --count 1000 \\
      --mongo-uri "mongodb://localhost:27017" \\
      --database local_test_db \\
      --collection Patients

  # Generate with custom seed for reproducibility
  python scripts/generate_test_patients.py --count 50 --seed 12345
        """,
    )

    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Number of patients to generate (default: 100)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="test-data/test_patients.json",
        help="Output JSON file path (default: test-data/test_patients.json)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument("--mongo-uri", type=str, help="MongoDB connection URI (optional)")
    parser.add_argument(
        "--database",
        type=str,
        default="local_test_db",
        help="MongoDB database name (default: local_test_db)",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="Patients",
        help="MongoDB collection name (default: Patients)",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("MongoDB PHI Masker - Test Patient Data Generator")
    print("=" * 70)
    print("\nConfiguration:")
    print(f"  Document count: {args.count}")
    print(f"  Random seed: {args.seed}")
    print("  PHI fields per document: 34")
    print()

    # Generate test data
    generator = PatientDataGenerator(seed=args.seed)
    start_time = datetime.now()

    patients = generator.generate_batch(args.count)

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n✓ Generation complete in {elapsed:.2f} seconds")

    # Save to JSON file
    generator.save_to_json(patients, args.output)

    # Optionally save to MongoDB
    if args.mongo_uri:
        generator.save_to_mongodb(patients, args.mongo_uri, args.database, args.collection)

    print("\n" + "=" * 70)
    print("✓ Test data generation complete!")
    print("=" * 70)
    print("\nSummary:")
    print(f"  Documents generated: {args.count}")
    print(f"  Output file: {args.output}")
    if args.mongo_uri:
        print(f"  MongoDB: {args.database}.{args.collection}")
    print("\nNext steps:")
    print(f"  1. Review generated data: head -50 {args.output}")
    if not args.mongo_uri:
        print(
            f"  2. Load into MongoDB: mongoimport --db local_test_db --collection Patients --file {args.output} --jsonArray"
        )
    print(f"  3. Run masking test: ./scripts/test_local_to_dev.sh Patients {min(args.count, 100)}")
    print()


if __name__ == "__main__":
    main()
