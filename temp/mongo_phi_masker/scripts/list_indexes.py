#!/usr/bin/env python
import sys
from pymongo import MongoClient

print("--- List Indexes Script Started ---")

# MongoDB connection string
mongo_uri = "mongodb+srv://dabebe:pdemes@Ubiquityproduction-pl-1.rgmqs.mongodb.net/test?authSource=admin&ssl=true"

try:
    print("Connecting to MongoDB...")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)
    db = client["test"]
    collection = db["StaffAvailability"]
    print("Connection successful.")

    print("Fetching index information...")
    index_info = collection.index_information()
    print("SUCCESS: Retrieved index information.")
    
    print("\n--- Existing Indexes ---")
    for index_name, index_details in index_info.items():
        print(f"- {index_name}: {index_details}")
    print("------------------------")
    
    client.close()

except Exception as e:
    print(f"ERROR: An error occurred: {e}")
    sys.exit(1)
