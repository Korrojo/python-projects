"""
Check Masking Progress Script

This script connects to MongoDB and samples documents from the StaffAvailability collection
to check how many have been masked so far.
"""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
import time
import random

def main():
    # Load environment variables from .env.prod
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env.prod')
    print(f"Loading environment from: {env_path}")
    load_dotenv(dotenv_path=env_path)
    
    # Get MongoDB connection details
    host = os.getenv('MONGO_SOURCE_HOST', 'localhost')
    port = int(os.getenv('MONGO_SOURCE_PORT', '27017'))
    username = os.getenv('MONGO_SOURCE_USERNAME')
    password = os.getenv('MONGO_SOURCE_PASSWORD')
    db_name = os.getenv('MONGO_SOURCE_DB', 'admin')
    
    # Print connection details (without sensitive info)
    print(f"Connecting to MongoDB at {host}:{port}")
    print(f"Using database: {db_name}")
    
    # Construct MongoDB URI
    if username and password:
        uri = f"mongodb://{username}:{password}@{host}:{port}/{db_name}"
    else:
        uri = f"mongodb://{host}:{port}/{db_name}"
    
    try:
        # Connect to MongoDB
        print("Connecting to MongoDB...")
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print("MongoDB connection successful!")
        
        # Get database
        db = client[db_name]
        
        # Define collection name
        collection_name = 'StaffAvailability'
        
        # Check if collection exists
        collections = db.list_collection_names()
        if collection_name not in collections:
            print(f"Error: Collection '{collection_name}' not found")
            return
        
        # Get collection
        collection = db[collection_name]
        
        # Count total documents
        total_count = collection.count_documents({})
        print(f"Total documents in {collection_name}: {total_count}")
        
        # Sample documents to check masking progress
        sample_size = 100
        print(f"Sampling {sample_size} documents to check masking progress...")
        
        # Get random sample of documents
        pipeline = [{"$sample": {"size": sample_size}}]
        sample_docs = list(collection.aggregate(pipeline))
        
        # Check for masked fields in the sample
        masked_count = 0
        masked_fields = {
            'PatientName': 0,
            'City': 0,
            'VisitNotes': 0,
            'VisitAddress': 0,
            'Comments': 0
        }
        
        for doc in sample_docs:
            # Check if document has Slots.Appointments
            if 'Slots' in doc and isinstance(doc['Slots'], list):
                for slot in doc['Slots']:
                    if 'Appointments' in slot and isinstance(slot['Appointments'], list):
                        for appt in slot['Appointments']:
                            # Check for masked fields
                            if 'PatientName' in appt and isinstance(appt['PatientName'], str):
                                if appt['PatientName'].isupper() and len(appt['PatientName']) > 0:
                                    masked_fields['PatientName'] += 1
                            
                            if 'City' in appt and appt['City'] == 'xxxxxxxxxx':
                                masked_fields['City'] += 1
                            
                            if 'VisitNotes' in appt and appt['VisitNotes'] == 'xxxxxxxxxx':
                                masked_fields['VisitNotes'] += 1
                            
                            if 'VisitAddress' in appt and appt['VisitAddress'] == 'xxxxxxxxxx':
                                masked_fields['VisitAddress'] += 1
                            
                            if 'Comments' in appt and appt['Comments'] == 'xxxxxxxxxx':
                                masked_fields['Comments'] += 1
        
        # Calculate percentage of documents with masked fields
        print("\nMasking Progress (based on sample):")
        for field, count in masked_fields.items():
            percentage = (count / sample_size) * 100
            print(f"  {field}: {count}/{sample_size} ({percentage:.2f}%)")
        
        # Overall progress estimate
        total_masked = sum(masked_fields.values())
        total_possible = sample_size * len(masked_fields)
        overall_percentage = (total_masked / total_possible) * 100 if total_possible > 0 else 0
        print(f"\nOverall masking progress estimate: {overall_percentage:.2f}%")
        
        # Check if masking is still in progress
        print("\nChecking if masking is still in progress...")
        # Wait a few seconds and check if more documents get masked
        time.sleep(5)
        
        # Sample again
        new_sample_docs = list(collection.aggregate(pipeline))
        new_masked_count = 0
        
        for doc in new_sample_docs:
            # Check if document has Slots.Appointments
            if 'Slots' in doc and isinstance(doc['Slots'], list):
                for slot in doc['Slots']:
                    if 'Appointments' in slot and isinstance(slot['Appointments'], list):
                        for appt in slot['Appointments']:
                            # Check for masked fields
                            if ('PatientName' in appt and isinstance(appt['PatientName'], str) and appt['PatientName'].isupper()) or \
                               ('City' in appt and appt['City'] == 'xxxxxxxxxx') or \
                               ('VisitNotes' in appt and appt['VisitNotes'] == 'xxxxxxxxxx') or \
                               ('VisitAddress' in appt and appt['VisitAddress'] == 'xxxxxxxxxx') or \
                               ('Comments' in appt and appt['Comments'] == 'xxxxxxxxxx'):
                                new_masked_count += 1
                                break
        
        if new_masked_count > masked_count:
            print("Masking appears to be still in progress (more documents masked since last check)")
        else:
            print("No change in masked documents detected in the last few seconds")
            print("This could mean masking is complete or proceeding slowly")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'client' in locals():
            client.close()
            print("MongoDB connection closed")

if __name__ == "__main__":
    main()
