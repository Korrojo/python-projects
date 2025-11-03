#!/usr/bin/env python3
"""
Simple utility to check environment variables for MongoDB connection.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Path to the project root
PROJECT_ROOT = Path(__file__).parent.parent

def main():
    # Load environment variables
    env_file = '.env.prod'
    if len(sys.argv) > 1:
        env_file = sys.argv[1]
    
    print(f"Checking environment variables from {env_file}")
    
    # Try both locations
    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)
        print(f"Loaded from current directory: {env_file}")
    elif os.path.exists(os.path.join(PROJECT_ROOT, env_file)):
        load_dotenv(os.path.join(PROJECT_ROOT, env_file), override=True)
        print(f"Loaded from project root: {os.path.join(PROJECT_ROOT, env_file)}")
    else:
        print(f"Warning: Environment file {env_file} not found")
        return
    
    # Check MongoDB source connection variables
    mongo_vars = [
        "MONGO_SOURCE_USERNAME",
        "MONGO_SOURCE_PASSWORD",
        "MONGO_SOURCE_HOST",
        "MONGO_SOURCE_PORT",
        "MONGO_SOURCE_AUTH_DB",
        "MONGO_SOURCE_USE_SSL",
        "MONGO_SOURCE_USE_SRV"
    ]
    
    print("\nMongoDB Source Connection Variables:")
    for var in mongo_vars:
        value = os.environ.get(var)
        if var.endswith("PASSWORD") and value:
            # Mask password
            print(f"  {var}: ****")
        else:
            print(f"  {var}: {value}")
    
    # Also check any variables with different naming patterns
    print("\nAdditional MongoDB Variables (if any):")
    for key, value in os.environ.items():
        if "MONGO" in key and key not in mongo_vars:
            if "PASSWORD" in key and value:
                # Mask password
                print(f"  {key}: ****")
            else:
                print(f"  {key}: {value}")

if __name__ == "__main__":
    main()
