import os
import sys
import traceback

from dotenv import load_dotenv
from pymongo import MongoClient


# Print to stderr to ensure output is visible
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    sys.stderr.flush()


eprint("Script started")

try:
    # Load environment variables
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, "..", ".env.prod")
    eprint(f"Loading environment from: {os.path.abspath(env_path)}")

    load_dotenv(dotenv_path=env_path)

    # Get individual MongoDB connection variables
    username = os.getenv("MONGO_SOURCE_USERNAME")
    password = os.getenv("MONGO_SOURCE_PASSWORD")
    host = os.getenv("MONGO_SOURCE_HOST")
    auth_db = os.getenv("MONGO_SOURCE_AUTH_DB")
    use_ssl = os.getenv("MONGO_SOURCE_USE_SSL", "false").lower() == "true"
    use_srv = os.getenv("MONGO_SOURCE_USE_SRV", "false").lower() == "true"
    db_name = os.getenv("MONGO_SOURCE_DB")

    eprint(f"Host: {host}")
    eprint(f"Database: {db_name}")
    eprint(f"Username exists: {'Yes' if username else 'No'}")
    eprint(f"Password exists: {'Yes' if password else 'No'}")
    eprint(f"Auth DB: {auth_db}")
    eprint(f"Use SSL: {use_ssl}")
    eprint(f"Use SRV: {use_srv}")

    # Construct the MongoDB URI
    protocol = "mongodb+srv" if use_srv else "mongodb"
    auth_part = f"{username}:{password}@" if username and password else ""
    auth_db_part = f"/?authSource={auth_db}" if auth_db else "/"
    ssl_part = "&ssl=true" if use_ssl else ""

    uri = f"{protocol}://{auth_part}{host}{auth_db_part}{ssl_part}"

    eprint(f"Constructed MongoDB URI: {protocol}://{auth_part}[HOST]{auth_db_part}{ssl_part}")

    # Try to connect to MongoDB
    eprint("Connecting to MongoDB...")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)

    # Force a connection to verify it works
    server_info = client.server_info()
    eprint("Connection successful!")
    eprint(f"MongoDB version: {server_info.get('version', 'unknown')}")

    # List collections in the database
    db = client[db_name]
    collections = db.list_collection_names()
    eprint(f"Collections in {db_name}: {collections}")

    # Check if our target collections exist
    original_coll = "AD_Patients_20250630_copy"
    masked_coll = "AD_Patients_20250630"

    eprint(f"Original collection '{original_coll}' exists: {original_coll in collections}")
    eprint(f"Masked collection '{masked_coll}' exists: {masked_coll in collections}")

    # Close the connection
    client.close()
    eprint("Connection closed.")

except Exception as e:
    eprint(f"Error: {e}")
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

eprint("Script completed successfully")
