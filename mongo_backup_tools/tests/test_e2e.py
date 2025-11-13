"""End-to-end tests for mongo-backup-tools with real MongoDB.

These tests use actual MongoDB connections (LOCL and DEV) to verify
the complete workflow of dump, restore, export, and import operations.

Run with: pytest tests/test_e2e.py -v -m e2e
Run only local: pytest tests/test_e2e.py -v -m "e2e and locl"
Run only remote: pytest tests/test_e2e.py -v -m "e2e and dev"
"""

import json
import os

import pytest
from pymongo import MongoClient

from src.models.dump import MongoDumpOptions
from src.models.export import MongoExportOptions
from src.models.import_opts import MongoImportOptions
from src.models.restore import MongoRestoreOptions
from src.orchestrators.dump import MongoDumpOrchestrator
from src.orchestrators.export import MongoExportOrchestrator
from src.orchestrators.import_orch import MongoImportOrchestrator
from src.orchestrators.restore import MongoRestoreOrchestrator

# Environment configurations
LOCL_CONFIG = {
    "uri": "mongodb://localhost:27017",
    "database": "test_mongo_backup_tools",  # Use test database
}

DEV_CONFIG = {
    "uri": os.getenv(
        "MONGODB_URI_DEV",
        "mongodb+srv://dabebe:jBmuad12m34mxbjY@cluster0.7hyef.mongodb.net/?retryWrites=true&w=majority",
    ),
    "database": "test_mongo_backup_tools",  # Use test database on Atlas too
}


@pytest.fixture
def locl_client():
    """MongoDB client for local database."""
    client = MongoClient(LOCL_CONFIG["uri"], serverSelectionTimeoutMS=5000)
    try:
        # Test connection
        client.admin.command("ping")
        yield client
    except Exception as e:
        pytest.skip(f"Local MongoDB not available: {e}")
    finally:
        client.close()


@pytest.fixture
def dev_client():
    """MongoDB client for DEV (Atlas) database."""
    client = MongoClient(DEV_CONFIG["uri"], serverSelectionTimeoutMS=10000)
    try:
        # Test connection
        client.admin.command("ping")
        yield client
    except Exception as e:
        pytest.skip(f"DEV MongoDB not available: {e}")
    finally:
        client.close()


@pytest.fixture
def test_data():
    """Sample test data for E2E tests."""
    return [
        {"_id": 1, "name": "Alice", "email": "alice@example.com", "age": 30, "city": "NYC"},
        {"_id": 2, "name": "Bob", "email": "bob@example.com", "age": 25, "city": "LA"},
        {"_id": 3, "name": "Charlie", "email": "charlie@example.com", "age": 35, "city": "Chicago"},
        {"_id": 4, "name": "Diana", "email": "diana@example.com", "age": 28, "city": "Boston"},
        {"_id": 5, "name": "Eve", "email": "eve@example.com", "age": 32, "city": "Seattle"},
    ]


@pytest.fixture
def locl_test_collection(locl_client, test_data):
    """Set up test collection with sample data on local MongoDB."""
    database_name = LOCL_CONFIG["database"]
    collection_name = "test_users"

    # Create test database and collection
    db = locl_client[database_name]
    collection = db[collection_name]

    # Clear any existing data
    collection.delete_many({})

    # Insert test data
    collection.insert_many(test_data)

    yield {
        "client": locl_client,
        "database": database_name,
        "collection": collection_name,
        "config": LOCL_CONFIG,
    }

    # Cleanup
    try:
        collection.delete_many({})
    except Exception:
        pass


@pytest.fixture
def dev_test_collection(dev_client, test_data):
    """Set up test collection with sample data on DEV (Atlas) MongoDB."""
    database_name = DEV_CONFIG["database"]
    collection_name = "test_users"

    # Create test database and collection
    db = dev_client[database_name]
    collection = db[collection_name]

    # Clear any existing data
    collection.delete_many({})

    # Insert test data
    collection.insert_many(test_data)

    yield {
        "client": dev_client,
        "database": database_name,
        "collection": collection_name,
        "config": DEV_CONFIG,
    }

    # Cleanup
    try:
        collection.delete_many({})
    except Exception:
        pass


# =============================================================================
# LOCL (Local MongoDB) Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.locl
def test_locl_dump_and_restore(locl_test_collection, tmp_path):
    """Test dump and restore operations on local MongoDB."""
    config = locl_test_collection["config"]
    database = locl_test_collection["database"]
    collection = locl_test_collection["collection"]

    # Step 1: Dump the database
    dump_dir = tmp_path / "dump"
    dump_options = MongoDumpOptions(
        uri=config["uri"],
        database=database,
        output_dir=dump_dir,
        collections=[collection],
    )

    dump_orchestrator = MongoDumpOrchestrator()
    dump_result = dump_orchestrator.dump(dump_options)

    assert dump_result.success, f"Dump failed: {dump_result.stderr}"
    assert dump_result.exit_code == 0
    assert dump_dir.exists()

    # Verify dump files were created
    dump_collection_file = dump_dir / database / f"{collection}.bson"
    assert dump_collection_file.exists(), f"Dump file not found: {dump_collection_file}"

    # Step 2: Drop the collection
    client = locl_test_collection["client"]
    client[database][collection].drop()

    # Verify collection is empty
    count_after_drop = client[database][collection].count_documents({})
    assert count_after_drop == 0, "Collection should be empty after drop"

    # Step 3: Restore the database
    # Note: Don't specify database when restoring from directory-based dump
    # MongoDB will restore to the original database name from the directory structure
    restore_options = MongoRestoreOptions(
        uri=config["uri"],
        input_dir=dump_dir,
    )

    restore_orchestrator = MongoRestoreOrchestrator()
    restore_result = restore_orchestrator.restore(restore_options)

    assert restore_result.success, f"Restore failed: {restore_result.stderr}"
    assert restore_result.exit_code == 0

    # Step 4: Verify data was restored
    count_after_restore = client[database][collection].count_documents({})
    assert count_after_restore == 5, f"Expected 5 documents, got {count_after_restore}"

    # Verify specific document
    doc = client[database][collection].find_one({"_id": 1})
    assert doc is not None
    assert doc["name"] == "Alice"
    assert doc["email"] == "alice@example.com"


@pytest.mark.e2e
@pytest.mark.locl
def test_locl_export_and_import_json(locl_test_collection, tmp_path):
    """Test export and import operations with JSON on local MongoDB."""
    config = locl_test_collection["config"]
    database = locl_test_collection["database"]
    collection = locl_test_collection["collection"]
    client = locl_test_collection["client"]

    # Step 1: Export to JSON
    export_file = tmp_path / "users.json"
    export_options = MongoExportOptions(
        uri=config["uri"],
        database=database,
        collection=collection,
        output_file=export_file,
        export_format="json",
    )

    export_orchestrator = MongoExportOrchestrator()
    export_result = export_orchestrator.export(export_options)

    assert export_result.success, f"Export failed: {export_result.stderr}"
    assert export_result.exit_code == 0
    assert export_file.exists()

    # Verify export file has data
    with open(export_file) as f:
        lines = f.readlines()
        assert len(lines) == 5, f"Expected 5 JSON lines, got {len(lines)}"

    # Step 2: Drop the collection
    client[database][collection].drop()
    assert client[database][collection].count_documents({}) == 0

    # Step 3: Import from JSON
    import_options = MongoImportOptions(
        uri=config["uri"],
        database=database,
        collection=collection,
        input_file=export_file,
        import_format="json",
    )

    import_orchestrator = MongoImportOrchestrator()
    import_result = import_orchestrator.import_data(import_options)

    assert import_result.success, f"Import failed: {import_result.stderr}"
    assert import_result.exit_code == 0

    # Step 4: Verify data was imported
    count = client[database][collection].count_documents({})
    assert count == 5, f"Expected 5 documents, got {count}"

    # Verify specific document
    doc = client[database][collection].find_one({"_id": 2})
    assert doc is not None
    assert doc["name"] == "Bob"


@pytest.mark.e2e
@pytest.mark.locl
def test_locl_export_and_import_csv(locl_test_collection, tmp_path):
    """Test export and import operations with CSV on local MongoDB."""
    config = locl_test_collection["config"]
    database = locl_test_collection["database"]
    collection = locl_test_collection["collection"]
    client = locl_test_collection["client"]

    # Step 1: Export to CSV
    export_file = tmp_path / "users.csv"
    export_options = MongoExportOptions(
        uri=config["uri"],
        database=database,
        collection=collection,
        output_file=export_file,
        export_format="csv",
        fields=["_id", "name", "email", "age", "city"],
    )

    export_orchestrator = MongoExportOrchestrator()
    export_result = export_orchestrator.export(export_options)

    assert export_result.success, f"Export failed: {export_result.stderr}"
    assert export_result.exit_code == 0
    assert export_file.exists()

    # Verify CSV file has data (header + 5 rows)
    with open(export_file) as f:
        lines = f.readlines()
        assert len(lines) == 6, f"Expected 6 lines (header + 5 rows), got {len(lines)}"
        assert lines[0].strip() == "_id,name,email,age,city"

    # Step 2: Drop the collection
    client[database][collection].drop()
    assert client[database][collection].count_documents({}) == 0

    # Step 3: Import from CSV
    import_options = MongoImportOptions(
        uri=config["uri"],
        database=database,
        collection=collection,
        input_file=export_file,
        import_format="csv",
        headerline=True,
    )

    import_orchestrator = MongoImportOrchestrator()
    import_result = import_orchestrator.import_data(import_options)

    assert import_result.success, f"Import failed: {import_result.stderr}"
    assert import_result.exit_code == 0

    # Step 4: Verify data was imported
    count = client[database][collection].count_documents({})
    assert count == 5, f"Expected 5 documents, got {count}"

    # Verify specific document (CSV imports numeric _id as integer)
    doc = client[database][collection].find_one({"_id": 3})
    assert doc is not None
    assert doc["name"] == "Charlie"
    assert doc["city"] == "Chicago"


@pytest.mark.e2e
@pytest.mark.locl
def test_locl_import_with_upsert(locl_test_collection, tmp_path):
    """Test import with upsert mode on local MongoDB."""
    config = locl_test_collection["config"]
    database = locl_test_collection["database"]
    collection = locl_test_collection["collection"]
    client = locl_test_collection["client"]

    # Create JSON file with updated data (some existing, some new)
    updated_data = [
        {"_id": 1, "name": "Alice Updated", "email": "alice.new@example.com", "age": 31, "city": "NYC"},
        {"_id": 2, "name": "Bob Updated", "email": "bob.new@example.com", "age": 26, "city": "LA"},
        {"_id": 6, "name": "Frank", "email": "frank@example.com", "age": 29, "city": "Miami"},
    ]

    import_file = tmp_path / "updated_users.json"
    with open(import_file, "w") as f:
        for doc in updated_data:
            f.write(json.dumps(doc) + "\n")

    # Import with upsert mode
    import_options = MongoImportOptions(
        uri=config["uri"],
        database=database,
        collection=collection,
        input_file=import_file,
        import_format="json",
        import_mode="upsert",
        upsert_fields=["_id"],
    )

    import_orchestrator = MongoImportOrchestrator()
    import_result = import_orchestrator.import_data(import_options)

    assert import_result.success, f"Import failed: {import_result.stderr}"
    assert import_result.exit_code == 0

    # Verify: Should have 6 documents total (5 original, 1 new, 2 updated)
    count = client[database][collection].count_documents({})
    assert count == 6, f"Expected 6 documents, got {count}"

    # Verify updates
    alice = client[database][collection].find_one({"_id": 1})
    assert alice["name"] == "Alice Updated"
    assert alice["age"] == 31

    bob = client[database][collection].find_one({"_id": 2})
    assert bob["name"] == "Bob Updated"

    # Verify new document
    frank = client[database][collection].find_one({"_id": 6})
    assert frank is not None
    assert frank["name"] == "Frank"

    # Verify unchanged document
    charlie = client[database][collection].find_one({"_id": 3})
    assert charlie["name"] == "Charlie"  # Should not be changed


# =============================================================================
# DEV (Atlas) Tests - Optional, can be skipped if connection fails
# =============================================================================


@pytest.mark.e2e
@pytest.mark.dev
def test_dev_dump_and_restore(dev_test_collection, tmp_path):
    """Test dump and restore operations on DEV (Atlas) MongoDB."""
    # Same logic as test_locl_dump_and_restore but with DEV connection
    config = dev_test_collection["config"]
    database = dev_test_collection["database"]
    collection = dev_test_collection["collection"]

    # Dump
    dump_dir = tmp_path / "dump"
    dump_options = MongoDumpOptions(
        uri=config["uri"],
        database=database,
        output_dir=dump_dir,
        collections=[collection],
    )

    dump_orchestrator = MongoDumpOrchestrator()
    dump_result = dump_orchestrator.dump(dump_options)

    assert dump_result.success, f"Dump failed: {dump_result.stderr}"
    assert dump_result.exit_code == 0

    # Drop
    client = dev_test_collection["client"]
    client[database][collection].drop()

    # Restore
    # Don't specify database - let mongorestore use the original database name
    restore_options = MongoRestoreOptions(
        uri=config["uri"],
        input_dir=dump_dir,
    )

    restore_orchestrator = MongoRestoreOrchestrator()
    restore_result = restore_orchestrator.restore(restore_options)

    assert restore_result.success, f"Restore failed: {restore_result.stderr}"
    assert restore_result.exit_code == 0

    # Verify
    count = client[database][collection].count_documents({})
    assert count == 5, f"Expected 5 documents, got {count}"


@pytest.mark.e2e
@pytest.mark.dev
def test_dev_export_and_import(dev_test_collection, tmp_path):
    """Test export and import operations on DEV (Atlas) MongoDB."""
    config = dev_test_collection["config"]
    database = dev_test_collection["database"]
    collection = dev_test_collection["collection"]
    client = dev_test_collection["client"]

    # Export
    export_file = tmp_path / "users.json"
    export_options = MongoExportOptions(
        uri=config["uri"],
        database=database,
        collection=collection,
        output_file=export_file,
        export_format="json",
    )

    export_orchestrator = MongoExportOrchestrator()
    export_result = export_orchestrator.export(export_options)

    assert export_result.success, f"Export failed: {export_result.stderr}"
    assert export_file.exists()

    # Drop and Import
    client[database][collection].drop()

    import_options = MongoImportOptions(
        uri=config["uri"],
        database=database,
        collection=collection,
        input_file=export_file,
        import_format="json",
    )

    import_orchestrator = MongoImportOrchestrator()
    import_result = import_orchestrator.import_data(import_options)

    assert import_result.success, f"Import failed: {import_result.stderr}"

    # Verify
    count = client[database][collection].count_documents({})
    assert count == 5, f"Expected 5 documents, got {count}"
