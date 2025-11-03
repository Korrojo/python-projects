"""
Simple MongoDB Collection Comparison Script

This script compares two MongoDB collections (original and masked) using a specified
aggregation pipeline to select PHI fields, and reports on the differences.
"""

import os
import sys
from pymongo import MongoClient
import json
from dotenv import load_dotenv

# Aggregation pipeline to select PHI fields
phi_aggregation_pipeline = [
    {
        '$project': {
            'PatientRef': 1,
            'Dob': 1,
            'Email': 1,
            'FirstName': 1,
            'LastName': 1,
            'MiddleName': 1,
            'Address_City': '$Address.City',
            'Address_Street1': '$Address.Street1',
            'Address_Zip5': '$Address.Zip5',
            'Phones_PhoneNumber': '$Phones.PhoneNumber',
        }
    }
]

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
    print(f"Username provided: {'Yes' if username else 'No'}")
    print(f"Password provided: {'Yes' if password else 'No'}")
    
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
        
        # Define collection names
        original_col_name = 'AD_Patients_20250630_copy'
        masked_col_name = 'AD_Patients_20250630'
        
        # Check if collections exist
        collections = db.list_collection_names()
        if original_col_name not in collections:
            print(f"Error: Original collection '{original_col_name}' not found")
            return
        if masked_col_name not in collections:
            print(f"Error: Masked collection '{masked_col_name}' not found")
            return
        
        print(f"Both collections found. Starting comparison...")
        
        # Get collections
        original_col = db[original_col_name]
        masked_col = db[masked_col_name]
        
        # Count documents in each collection
        original_count = original_col.count_documents({})
        masked_count = masked_col.count_documents({})
        
        print(f"Original collection has {original_count} documents")
        print(f"Masked collection has {masked_count} documents")
        
        # Run aggregation on both collections
        print("Fetching data from original collection...")
        original_docs = list(original_col.aggregate(phi_aggregation_pipeline))
        print(f"Retrieved {len(original_docs)} documents from original collection")
        
        print("Fetching data from masked collection...")
        masked_docs = list(masked_col.aggregate(phi_aggregation_pipeline))
        print(f"Retrieved {len(masked_docs)} documents from masked collection")
        
        # Create a map of original documents by ID for faster lookup
        original_docs_map = {str(doc['_id']): doc for doc in original_docs}
        
        # Compare documents
        different_count = 0
        same_count = 0
        missing_count = 0
        
        print("\nComparing documents...")
        for masked_doc in masked_docs:
            masked_id = str(masked_doc['_id'])
            original_doc = original_docs_map.get(masked_id)
            
            if not original_doc:
                print(f"Document with ID {masked_id} not found in original collection")
                missing_count += 1
                continue
            
            # Compare fields
            differences = []
            for key in masked_doc:
                if key != '_id':  # Skip comparing _id field
                    masked_val = masked_doc[key]
                    original_val = original_doc.get(key)
                    
                    # Simple string comparison for demonstration
                    if str(masked_val) != str(original_val):
                        differences.append({
                            'field': key,
                            'original': original_val,
                            'masked': masked_val
                        })
            
            if differences:
                different_count += 1
                if different_count <= 5:  # Limit output to first 5 different documents
                    print(f"\nDocument with ID {masked_id} has differences:")
                    for diff in differences:
                        print(f"  Field: {diff['field']}")
                        print(f"    Original: {diff['original']}")
                        print(f"    Masked:   {diff['masked']}")
            else:
                same_count += 1
        
        # Print summary
        print("\n--- Comparison Summary ---")
        print(f"Total documents checked: {len(masked_docs)}")
        print(f"Documents with differences: {different_count}")
        print(f"Documents that are the same: {same_count}")
        print(f"Documents missing from original: {missing_count}")
        print("-------------------------")
        
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
