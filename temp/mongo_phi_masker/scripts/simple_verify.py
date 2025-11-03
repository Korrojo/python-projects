#!/usr/bin/env python
"""
Simple script to verify masking results for StaffAvailability collection.
"""

import sys
import os
from pymongo import MongoClient
import json

def main():
    # MongoDB connection string
    mongo_uri = "mongodb+srv://dabebe:pdemes@Ubiquityproduction-pl-1.rgmqs.mongodb.net/test?authSource=admin&ssl=true"
    
    # Connect to MongoDB
    print("Connecting to MongoDB...")
    client = MongoClient(mongo_uri)
    db = client["test"]
    collection = db["StaffAvailability"]
    
    # Find a few documents with PatientName
    print("\nFinding documents with PatientName...")
    pipeline = [
        {"$match": {"Slots.Appointments.PatientName": {"$exists": True}}},
        {"$unwind": "$Slots"},
        {"$unwind": "$Slots.Appointments"},
        {"$match": {"Slots.Appointments.PatientName": {"$exists": True, "$ne": None}}},
        {"$project": {
            "_id": 0,
            "patientName": "$Slots.Appointments.PatientName",
            "city": "$Slots.Appointments.City",
            "visitNotes": "$Slots.Appointments.VisitNotes",
            "visitAddress": "$Slots.Appointments.VisitAddress",
            "comments": "$Slots.Appointments.Comments"
        }},
        {"$limit": 5}
    ]
    
    results = list(collection.aggregate(pipeline))
    
    # Write results to file
    with open("verification_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    # Print results to console
    print(f"Found {len(results)} documents with PatientName")
    print("\n=== SAMPLE DOCUMENTS ===")
    for i, doc in enumerate(results):
        print(f"Document {i+1}:")
        print(f"  PatientName: {doc.get('patientName')}")
        print(f"  City: {doc.get('city')}")
        print(f"  VisitNotes: {doc.get('visitNotes')}")
        print(f"  VisitAddress: {doc.get('visitAddress')}")
        print(f"  Comments: {doc.get('comments')}")
    
    # Check masking status
    patient_name_masked = all(doc.get('patientName') == "[MASKED NAME]" for doc in results if doc.get('patientName'))
    city_masked = all(doc.get('city') == "xxxxxxxxxx" for doc in results if doc.get('city'))
    visit_notes_masked = all(doc.get('visitNotes') == "xxxxxxxxxx" for doc in results if doc.get('visitNotes'))
    visit_address_masked = all(doc.get('visitAddress') == "xxxxxxxxxx" for doc in results if doc.get('visitAddress'))
    comments_masked = all(doc.get('comments') == "xxxxxxxxxx" for doc in results if doc.get('comments'))
    
    # Print masking verification summary
    print("\n=== MASKING VERIFICATION SUMMARY ===")
    print(f"PatientName masked: {'YES' if patient_name_masked else 'NO'}")
    print(f"City masked: {'YES' if city_masked else 'NO'}")
    print(f"VisitNotes masked: {'YES' if visit_notes_masked else 'NO'}")
    print(f"VisitAddress masked: {'YES' if visit_address_masked else 'NO'}")
    print(f"Comments masked: {'YES' if comments_masked else 'NO'}")
    
    # Count documents with PatientName
    total_with_patient_name = collection.count_documents({
        "Slots.Appointments.PatientName": {"$exists": True, "$ne": None}
    })
    print(f"\nTotal documents with PatientName field: {total_with_patient_name}")
    
    # Count documents with unmasked PatientName
    unmasked_count = collection.count_documents({
        "Slots.Appointments.PatientName": {"$exists": True, "$ne": None, "$ne": "[MASKED NAME]"}
    })
    print(f"Documents with unmasked PatientName: {unmasked_count}")
    
    # Count documents with masked PatientName
    masked_count = collection.count_documents({
        "Slots.Appointments.PatientName": "[MASKED NAME]"
    })
    print(f"Documents with masked PatientName: {masked_count}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
