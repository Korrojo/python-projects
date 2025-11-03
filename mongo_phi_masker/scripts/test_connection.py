#!/usr/bin/env python
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

print("Attempting to connect to MongoDB...")

# MongoDB connection string with a short timeout
mongo_uri = "mongodb+srv://dabebe:pdemes@Ubiquityproduction-pl-1.rgmqs.mongodb.net/test?authSource=admin&ssl=true"

try:
    # Initialize the client with a server selection timeout
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    
    # The ismaster command is cheap and does not require auth.
    client.admin.command('ismaster')
    
    print("SUCCESS: MongoDB connection was successful.")
    client.close()
    sys.exit(0)

except ConnectionFailure as e:
    print(f"ERROR: MongoDB connection failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: An unexpected error occurred: {e}")
    sys.exit(1)
