import os
import sys
from dotenv import load_dotenv

# Print Python version and path
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Construct the absolute path to the .env.prod file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env.prod')
print(f"Loading environment from: {os.path.abspath(env_path)}")

# Check if file exists
if os.path.exists(env_path):
    print(f".env.prod file exists at {env_path}")
else:
    print(f"ERROR: .env.prod file does not exist at {env_path}")
    sys.exit(1)

# Try to load environment variables
load_dotenv(dotenv_path=env_path)

# Print all environment variables
print("\nEnvironment Variables:")
for key, value in os.environ.items():
    if key.startswith('MONGO_'):
        # Mask sensitive information
        masked_value = value[:5] + '...' if len(value) > 5 else value
        print(f"{key}: {masked_value}")

# Specifically check for MongoDB connection variables
mongo_uri = os.getenv('MONGO_SOURCE_URI')
mongo_db = os.getenv('MONGO_SOURCE_DB')

print(f"\nMONGO_SOURCE_URI exists: {mongo_uri is not None}")
print(f"MONGO_SOURCE_DB exists: {mongo_db is not None}")

if mongo_uri and mongo_db:
    print("MongoDB connection variables found.")
else:
    print("ERROR: MongoDB connection variables not found in .env.prod file.")
    print("Please ensure your .env.prod file contains MONGO_SOURCE_URI and MONGO_SOURCE_DB variables.")
