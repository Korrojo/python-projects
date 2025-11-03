#!/usr/bin/env python
"""
Simple script to check if PatientName is being masked correctly.
"""

import json
import sys

from pymongo import MongoClient


def main():
    # MongoDB connection string
    mongo_uri = "mongodb+srv://dabebe:pdemes@Ubiquityproduction-pl-1.rgmqs.mongodb.net/test?authSource=admin&ssl=true"

    # Connect to MongoDB
    print("Connecting to MongoDB...")
    client = MongoClient(mongo_uri)
    db = client["test"]
    collection = db["StaffAvailability"]

    # Find a document with PatientName
    print("\nFinding a document with PatientName...")
    doc = collection.find_one({"Slots.Appointments.PatientName": {"$exists": True}})

    if not doc:
        print("No documents found with PatientName field")
        return 1

    print("\nDocument found. Checking PatientName fields...")

    # Check if document has Slots array
    if "Slots" not in doc:
        print("Document does not have Slots array")
        return 1

    # Check each Slot for Appointments with PatientName
    patient_names_found = []

    for slot in doc["Slots"]:
        if "Appointments" not in slot:
            continue

        for appointment in slot["Appointments"]:
            if "PatientName" in appointment:
                patient_names_found.append(appointment["PatientName"])

    # Print results
    print(f"\nFound {len(patient_names_found)} PatientName fields in document")

    # Redact PatientName for security (PHI/PII)
    for i, _name in enumerate(patient_names_found):
        print(f"PatientName {i+1}: [REDACTED]")

    # Check if PatientName is masked
    masked_count = patient_names_found.count("[MASKED NAME]") if patient_names_found else 0
    unmasked_count = len(patient_names_found) - masked_count

    print(f"\nMasked PatientNames: {masked_count}")
    print(f"Unmasked PatientNames: {unmasked_count}")

    # Write document to file for inspection
    with open("patient_name_document.json", "w") as f:
        json.dump(doc, f, indent=2, default=str)
    print("\nDocument written to patient_name_document.json for inspection")

    return 0


if __name__ == "__main__":
    sys.exit(main())
