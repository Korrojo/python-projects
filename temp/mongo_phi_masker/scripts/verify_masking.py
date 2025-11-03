#!/usr/bin/env python
"""
Script to verify masking results for StaffAvailability collection.
"""

import sys
import os
from pymongo import MongoClient
from bson import ObjectId
import json
from datetime import datetime
import logging

# Configure logging to both console and file
log_file = "masking_verification_results.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, mode='w')
    ]
)
logger = logging.getLogger("verify_masking")

# Also write raw results to a separate file
results_file = "masking_verification_data.json"

def main():
    # MongoDB connection string
    mongo_uri = "mongodb+srv://dabebe:pdemes@Ubiquityproduction-pl-1.rgmqs.mongodb.net/test?authSource=admin&ssl=true"
    
    # Connect to MongoDB
    logger.info("Connecting to MongoDB...")
    client = MongoClient(mongo_uri)
    db = client["test"]
    collection = db["StaffAvailability"]
    
    # Verify connection
    try:
        # Check if collection exists
        if "StaffAvailability" not in db.list_collection_names():
            logger.error("StaffAvailability collection not found")
            return 1
        
        logger.info(f"Connected to MongoDB. Collection: {collection.name}")
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        return 1
    
    # Define aggregation pipeline to find documents with PatientName
    pipeline = [
        # Match documents with PatientName field
        {"$match": {
            "Slots.Appointments.PatientName": {"$exists": True}
        }},
        
        # Unwind arrays to access nested fields
        {"$unwind": "$Slots"},
        {"$unwind": "$Slots.Appointments"},
        
        # Additional filter to ensure PatientName is not null
        {"$match": {
            "Slots.Appointments.PatientName": {"$exists": True, "$ne": None}
        }},
        
        # Project PHI fields
        {"$project": {
            "_id": 0,
            "patientName": "$Slots.Appointments.PatientName",
            "city": "$Slots.Appointments.City",
            "visitNotes": "$Slots.Appointments.VisitNotes",
            "visitAddress": "$Slots.Appointments.VisitAddress",
            "comments": "$Slots.Appointments.Comments"
        }},
        
        # Limit results
        {"$limit": 10}
    ]
    
    # Execute the aggregation
    logger.info("Executing aggregation pipeline...")
    results = list(collection.aggregate(pipeline))
    
    if not results:
        logger.info("No documents found with PatientName field")
        return 0
    
    # Print the results
    logger.info(f"Found {len(results)} documents with PatientName field")
    logger.info("\n=== SAMPLE DOCUMENTS ===")
    for i, doc in enumerate(results):
        logger.info(f"Document {i+1}:")
        logger.info(f"  PatientName: {doc.get('patientName')}")
        logger.info(f"  City: {doc.get('city')}")
        logger.info(f"  VisitNotes: {doc.get('visitNotes')}")
        logger.info(f"  VisitAddress: {doc.get('visitAddress')}")
        logger.info(f"  Comments: {doc.get('comments')}")
    
    # Write raw results to JSON file
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Check if fields are masked
    patient_name_masked = all(doc.get('patientName') == "[MASKED NAME]" for doc in results if doc.get('patientName'))
    city_masked = all(doc.get('city') == "xxxxxxxxxx" for doc in results if doc.get('city'))
    visit_notes_masked = all(doc.get('visitNotes') == "xxxxxxxxxx" for doc in results if doc.get('visitNotes'))
    visit_address_masked = all(doc.get('visitAddress') == "xxxxxxxxxx" for doc in results if doc.get('visitAddress'))
    comments_masked = all(doc.get('comments') == "xxxxxxxxxx" for doc in results if doc.get('comments'))
    
    # Print masking verification summary
    logger.info("\n=== MASKING VERIFICATION SUMMARY ===")
    logger.info(f"PatientName masked: {'YES' if patient_name_masked else 'NO'}")
    logger.info(f"City masked: {'YES' if city_masked else 'NO'}")
    logger.info(f"VisitNotes masked: {'YES' if visit_notes_masked else 'NO'}")
    logger.info(f"VisitAddress masked: {'YES' if visit_address_masked else 'NO'}")
    logger.info(f"Comments masked: {'YES' if comments_masked else 'NO'}")
    
    # Count total documents with PatientName field
    total_with_patient_name = collection.count_documents({
        "Slots.Appointments.PatientName": {"$exists": True, "$ne": None}
    })
    logger.info(f"\nTotal documents with PatientName field: {total_with_patient_name}")
    
    # Count documents with unmasked PatientName
    unmasked_count = collection.count_documents({
        "Slots.Appointments.PatientName": {"$exists": True, "$ne": None, "$ne": "[MASKED NAME]"}
    })
    logger.info(f"Documents with unmasked PatientName: {unmasked_count}")
    
    # Count documents with masked PatientName
    masked_count = collection.count_documents({
        "Slots.Appointments.PatientName": "[MASKED NAME]"
    })
    logger.info(f"Documents with masked PatientName: {masked_count}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
