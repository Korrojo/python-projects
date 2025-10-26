"""Pytest configuration to ensure repo root and common_config are importable.

Also provides shared fixtures for all projects:
- MongoDB connection mocking
- Configuration loading
- Temporary directories
- Sample test data
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def pytest_configure(config):
    """Add repo root and common_config/src to sys.path before test collection."""
    # tests/conftest.py is at repo_root/tests/, so parent is repo root
    repo_root = Path(__file__).parent.parent
    cc_src = repo_root / "common_config" / "src"

    # Add repo root so sample_project and other top-level modules are importable
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    # Add common_config/src so common_config can be imported without installing
    if str(cc_src) not in sys.path:
        sys.path.insert(0, str(cc_src))

    # Register custom markers
    config.addinivalue_line("markers", "integration: marks tests as integration tests (require real DB)")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "db: marks tests that require database connection")


@pytest.fixture
def mock_mongo_connection(monkeypatch):
    """Mock MongoDB connection for testing without real database."""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()

    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection

    # Mock common_config.database.mongodb.MongoDBConnection if used
    try:
        from common_config.database.mongodb import MongoDBConnection

        def mock_init(self, *args, **kwargs):
            self._client = mock_client
            self._database = mock_db

        monkeypatch.setattr(MongoDBConnection, "__init__", mock_init)
        monkeypatch.setattr(MongoDBConnection, "get_client", lambda self: mock_client)
        monkeypatch.setattr(MongoDBConnection, "get_database", lambda self: mock_db)
    except ImportError:
        pass  # common_config may not be installed yet

    return {"client": mock_client, "db": mock_db, "collection": mock_collection}


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock common_config settings for testing."""
    try:
        from common_config.config.settings import Settings

        test_settings = Settings(
            app_env="TEST",
            mongodb_uri="mongodb://localhost:27017",
            database_name="test_db",
            collection_name="test_collection",
            log_level="INFO",
        )

        monkeypatch.setattr("common_config.config.settings.get_settings", lambda: test_settings)
        return test_settings
    except ImportError:
        return None


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directories for testing."""
    data_dir = tmp_path / "data"
    input_dir = data_dir / "input"
    output_dir = data_dir / "output"

    input_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)

    return {"data": data_dir, "input": input_dir, "output": output_dir}


@pytest.fixture
def temp_log_dir(tmp_path):
    """Create temporary log directory for testing."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True)
    return log_dir


@pytest.fixture
def sample_csv_data():
    """Provide sample CSV data for testing."""
    return {
        "headers": ["HcmId", "FirstName", "LastName", "Dob", "Gender"],
        "rows": [
            ["12345", "John", "Doe", "1980-01-15", "M"],
            ["67890", "Jane", "Smith", "1990-05-20", "F"],
            ["11111", "Bob", "Johnson", "1975-12-10", "M"],
        ],
    }


@pytest.fixture
def sample_patient_data():
    """Provide sample patient data for testing."""
    return [
        {
            "_id": "507f1f77bcf86cd799439011",
            "HcmId": 12345,
            "FirstName": "John",
            "LastName": "Doe",
            "Dob": "1980-01-15",
            "Gender": "M",
        },
        {
            "_id": "507f1f77bcf86cd799439012",
            "HcmId": 67890,
            "FirstName": "Jane",
            "LastName": "Smith",
            "Dob": "1990-05-20",
            "Gender": "F",
        },
    ]


@pytest.fixture
def project_root():
    """Return the absolute path to the project root directory."""
    return Path(__file__).parent.parent.absolute()


@pytest.fixture
def shared_config_path(project_root):
    """Return the path to shared_config directory."""
    return project_root / "shared_config"


@pytest.fixture(autouse=True)
def reset_sys_path():
    """Reset sys.path after each test to avoid cross-contamination."""
    import sys

    original_path = sys.path.copy()
    yield
    sys.path = original_path
