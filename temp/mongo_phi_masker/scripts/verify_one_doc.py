#!/usr/bin/env python
import sys
from pymongo import MongoClient

print("--- Verification script started ---")

# MongoDB connection string with a longer timeout
mongo_uri = "mongodb+srv://dabebe:pdemes@Ubiquityproduction-pl-1.rgmqs.mongodb.net/test?authSource=admin&ssl=true"

try:
    print("Connecting to MongoDB...")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
    db = client["test"]
    collection = db["StaffAvailability"]
    print("Connection successful.")

    print("Executing find_one() query...")
    doc = collection.find_one({"Slots.Appointments.PatientName": {"$exists": True}})
    print("Query finished.")
    client.close()

    if not doc:
        print("VERIFICATION_RESULT::FAILED - Could not find a document with PatientName.")
        sys.exit(1)

    # Check the PatientName field
    for slot in doc.get("Slots", []):
        for appointment in slot.get("Appointments", []):
            if "PatientName" in appointment:
                patient_name = appointment["PatientName"]
                # Final definitive output
                print(f"VERIFICATION_RESULT::SUCCESS - PatientName is: {patient_name}")
                sys.exit(0) # Exit after finding the first one

    print("VERIFICATION_RESULT::FAILED - Found a document, but no PatientName field inside Slots.Appointments.")

except Exception as e:
    print(f"VERIFICATION_RESULT::ERROR - {e}")
    sys.exit(1)

