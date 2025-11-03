#!/usr/bin/env python
"""
Script to import representative sample data into the development database.
"""

import os
import sys
import json
import argparse
import logging
from dotenv import load_dotenv
from pymongo import MongoClient


def generate_sample_data(count=10):
    """Generate sample data with variations based on the provided example."""
    # Base document that follows the structure in patients_unmasked.json
    base_doc = {
        "PatientId": 2079044,
        "FirstName": "SUZANNE",
        "MiddleName": "E",
        "LastName": "FINLEY",
        "FirstNameLower": "suzanne",
        "MiddleNameLower": "e",
        "LastNameLower": "finley",
        "Dob": "1967-09-29T00:00:00.000Z",
        "Gender": "Female",
        "HealthPlanMemberId": "968490707-01",
        "Email": "suzanne.finley@example.com",
        "Address": [
            {
                "Street1": "2116 GEMINI ST",
                "Street2": "",
                "City": "HOUSTON",
                "StateCode": "TX",
                "Zip5": "77058",
                "StateName": "Texas",
            }
        ],
        "Phones": [{"PhoneNumber": "8324886106", "Notes": ""}],
        "PatientProblemList": [
            {
                "EncounterProblemList": [
                    {
                        "FinalNotes": "Chronic respiratory failure with hypoxia s/p COVID PNA in 2021.",
                        "Comments": "",
                    }
                ]
            }
        ],
        "Insurance": [
            {
                "EmployerStreet": "WellMed Claims, P.O. Box 30508",
                "PrimaryMemberName": "SUZANNE E FINLEY",
                "PrimaryMemberDOB": "1967-09-29T00:00:00.000Z",
            }
        ],
        "PatientCallLog": [
            {
                "PatientName": "SUZANNE FINLEY",
                "VisitAddress": "Home (2116 GEMINI ST, HOUSTON, TX, 77058)",
            }
        ],
        "PatientDat": [{"OtherReason": ""}],
        "OutreachActivitiesList": [{"Reason": "CHA scheduled call back"}],
        "DocuSign": [{"UserName": "SUZANNE E FINLEY"}],
        "Contacts": "",
    }

    # Data for variations
    first_names = [
        "JOHN",
        "MARY",
        "ROBERT",
        "PATRICIA",
        "JAMES",
        "LINDA",
        "MICHAEL",
        "ELIZABETH",
        "WILLIAM",
        "BARBARA",
    ]
    last_names = [
        "SMITH",
        "JOHNSON",
        "WILLIAMS",
        "JONES",
        "BROWN",
        "DAVIS",
        "MILLER",
        "WILSON",
        "MOORE",
        "TAYLOR",
    ]
    middle_initials = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    cities = [
        "HOUSTON",
        "CHICAGO",
        "NEW YORK",
        "LOS ANGELES",
        "PHOENIX",
        "PHILADELPHIA",
        "SAN ANTONIO",
        "SAN DIEGO",
        "DALLAS",
        "SAN JOSE",
    ]
    states = ["TX", "IL", "NY", "CA", "AZ", "PA", "TX", "CA", "TX", "CA"]
    state_names = [
        "Texas",
        "Illinois",
        "New York",
        "California",
        "Arizona",
        "Pennsylvania",
        "Texas",
        "California",
        "Texas",
        "California",
    ]

    samples = []
    for i in range(count):
        # Create a variation of the base document
        import copy

        doc = copy.deepcopy(base_doc)
        doc["_id"] = i + 1  # Use sequential IDs
        doc["PatientId"] = 2079044 + i

        # Vary the name
        doc["FirstName"] = first_names[i % len(first_names)]
        doc["MiddleName"] = middle_initials[i % len(middle_initials)]
        doc["LastName"] = last_names[i % len(last_names)]

        # Set lowercase versions
        doc["FirstNameLower"] = doc["FirstName"].lower()
        doc["MiddleNameLower"] = doc["MiddleName"].lower()
        doc["LastNameLower"] = doc["LastName"].lower()

        # Vary address
        doc["Address"][0][
            "Street1"
        ] = f"{1000 + i} {first_names[i % len(first_names)]} ST"
        doc["Address"][0]["City"] = cities[i % len(cities)]
        doc["Address"][0]["StateCode"] = states[i % len(states)]
        doc["Address"][0]["Zip5"] = f"{77000 + i}"
        doc["Address"][0]["StateName"] = state_names[i % len(state_names)]

        # Vary phone
        doc["Phones"][0]["PhoneNumber"] = f"{800 + i}4886{100 + i}"

        # Add email
        doc["Email"] = f"{doc['FirstNameLower']}.{doc['LastNameLower']}@example.com"

        # Update in nested objects too
        doc["Insurance"][0][
            "PrimaryMemberName"
        ] = f"{doc['FirstName']} {doc['MiddleName']} {doc['LastName']}"
        doc["Insurance"][0]["PrimaryMemberDOB"] = doc["Dob"]
        doc["PatientCallLog"][0][
            "PatientName"
        ] = f"{doc['FirstName']} {doc['LastName']}"
        doc["PatientCallLog"][0][
            "VisitAddress"
        ] = f"Home ({doc['Address'][0]['Street1']}, {doc['Address'][0]['City']}, {doc['Address'][0]['StateCode']}, {doc['Address'][0]['Zip5']})"
        doc["DocuSign"][0][
            "UserName"
        ] = f"{doc['FirstName']} {doc['MiddleName']} {doc['LastName']}"

        samples.append(doc)

    return samples


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Import sample data to MongoDB")
    parser.add_argument("--env", default=".env.dev", help="Path to environment file")
    parser.add_argument(
        "--count", type=int, default=10, help="Number of sample documents"
    )
    parser.add_argument(
        "--drop", action="store_true", help="Drop existing collection before import"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Load environment variables
    if not os.path.exists(args.env):
        logger.error(f"Environment file not found: {args.env}")
        return 1

    load_dotenv(args.env, override=True)

    # Generate sample data
    sample_data = generate_sample_data(args.count)

    # Connect to MongoDB
    uri = os.getenv("MONGO_SOURCE_URI")
    db_name = os.getenv("MONGO_SOURCE_DB")
    coll_name = os.getenv("MONGO_SOURCE_COLL")

    logger.info(f"Connecting to MongoDB at {uri}")
    client = MongoClient(uri)
    db = client[db_name]
    collection = db[coll_name]

    # Drop collection if requested
    if args.drop and collection.count_documents({}) > 0:
        logger.info(f"Dropping collection {db_name}.{coll_name}")
        collection.drop()

    # Insert sample data
    if collection.count_documents({}) == 0:
        logger.info(
            f"Inserting {len(sample_data)} documents into {db_name}.{coll_name}"
        )
        collection.insert_many(sample_data)
        logger.info("Sample data imported successfully")
    else:
        logger.info(
            f"Collection {db_name}.{coll_name} already contains data. Use --drop to replace."
        )

    # Verify import
    count = collection.count_documents({})
    logger.info(f"Collection {db_name}.{coll_name} now contains {count} documents")

    return 0


if __name__ == "__main__":
    sys.exit(main())
