"""Test configuration and fixtures for MongoDB PHI Masker tests."""

import sys
from pathlib import Path
from typing import Any

import mongomock
import pytest

# Add src/ to path so tests can import project modules
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

# Add common_config to path (monorepo structure)
repo_root = project_root.parent
common_config_path = repo_root / "common_config" / "src"
if common_config_path.exists():
    sys.path.insert(0, str(common_config_path))


@pytest.fixture
def mock_mongo_client():
    """Provide a mock MongoDB client for testing."""
    client = mongomock.MongoClient()
    yield client
    client.close()


@pytest.fixture
def mock_database(mock_mongo_client):
    """Provide a mock MongoDB database for testing."""
    return mock_mongo_client["test_db"]


@pytest.fixture
def mock_collection(mock_database):
    """Provide a mock MongoDB collection for testing."""
    return mock_database["test_collection"]


@pytest.fixture
def sample_document():
    """Provide a sample document for testing."""
    return {
        "_id": "test_id_123",
        "PatientName": "John Doe",
        "DateOfBirth": "1990-01-15",
        "Email": "john.doe@example.com",
        "Phone": "555-1234",
        "Address": "123 Main St",
        "SSN": "123-45-6789",
        "Gender": "Male",
        "MedicalRecordNumber": "MRN123456",
    }


@pytest.fixture
def sample_masking_rules():
    """Provide sample masking rules for testing."""
    return {
        "PatientName": {"type": "replace_name", "preserve_format": True},
        "DateOfBirth": {"type": "replace_date", "preserve_format": True},
        "Email": {"type": "replace_email", "preserve_format": True},
        "Phone": {"type": "replace_phone", "preserve_format": True},
        "Address": {"type": "replace_string", "replacement": "XXXXXXXXXX"},
        "SSN": {"type": "replace_ssn", "preserve_format": True},
        "Gender": {"type": "replace_gender"},
        "MedicalRecordNumber": {"type": "replace_string", "replacement": "MRN_MASKED"},
    }


@pytest.fixture
def sample_config():
    """Provide a sample configuration for testing."""
    return {
        "source": {"database": "source_db", "collection": "source_coll"},
        "destination": {"database": "dest_db", "collection": "dest_coll"},
        "masking": {
            "batch_size": 100,
            "checkpoint_enabled": True,
            "in_situ": False,
        },
        "phi_collections": ["Patients", "Appointments"],
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Provide mock environment variables for testing."""
    env_vars = {
        "MONGO_SOURCE_HOST": "localhost",
        "MONGO_SOURCE_PORT": "27017",
        "MONGO_SOURCE_DB": "source_db",
        "MONGO_SOURCE_COLL": "source_coll",
        "MONGO_DEST_HOST": "localhost",
        "MONGO_DEST_PORT": "27017",
        "MONGO_DEST_DB": "dest_db",
        "MONGO_DEST_COLL": "dest_coll",
        "BATCH_SIZE": "100",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars
