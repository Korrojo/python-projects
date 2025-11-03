#!/usr/bin/env python
import sys
from pymongo import MongoClient
import json

print("--- Get Any Document Script Started ---")

# MongoDB connection string
mongo_uri = "mongodb+srv://dabebe:pdemes@Ubiquityproduction-pl-1.rgmqs.mongodb.net/test?authSource=admin&ssl=true"

try:
    print("Connecting to MongoDB...")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
    db = client["test"]
    collection = db["StaffAvailability"]
    print("Connection successful.")

    print("Fetching one document (no filter)...")
    doc = collection.find_one()
    print("Fetch complete.")
    client.close()

    if not doc:
        print("VERIFICATION_FAILED: The collection appears to be empty.")
        sys.exit(1)

    print("Document retrieved. Saving to 'inspected_any_document.json'...")
    with open("inspected_any_document.json", "w") as f:
        json.dump(doc, f, indent=2, default=str)
    print("Save complete.")

    # Check for PatientName in the retrieved document
    found_patient_name = False
    for slot in doc.get("Slots", []):
        for appointment in slot.get("Appointments", []):
            if "PatientName" in appointment:
                found_patient_name = True
                patient_name = appointment["PatientName"]
                print(f"VERIFICATION_RESULT::SUCCESS - Found PatientName: {patient_name}")
                sys.exit(0)
    
    if not found_patient_name:
        print("VERIFICATION_RESULT::NOTE - The retrieved document did not contain a PatientName field.")

except Exception as e:
    print(f"VERIFICATION_ERROR::{e}::")
    sys.exit(1)
