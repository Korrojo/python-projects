# Testing Guide

## Overview

This repository now has test coverage for all 9 projects:

- ✅ common_config (68.87% coverage)
- ✅ PatientOtherDetail_isActive_false
- ✅ automate_refresh (NEW)
- ✅ patient_data_extraction (NEW)
- ✅ patient_demographic (NEW)
- ✅ patients_hcmid_validator (NEW)
- ✅ staff_appointment_visitStatus (NEW)
- ✅ users-provider-update (NEW)
- ℹ️ appointment_comparison (archived)

## Running Tests

### All Tests

```bash
# From repository root
.venv311/Scripts/python.exe -m pytest tests/

# With coverage
.venv311/Scripts/python.exe -m pytest tests/ --cov
```

### Specific Project

```bash
# Single project
.venv311/Scripts/python.exe -m pytest automate_refresh/tests/ -v

# Multiple projects
.venv311/Scripts/python.exe -m pytest \
  patient_data_extraction/tests/ \
  patients_hcmid_validator/tests/ \
  -v
```

### By Test Type

```bash
# Only smoke tests (imports, dependencies, structure)
.venv311/Scripts/python.exe -m pytest -k "smoke" -v

# Skip integration tests (require database)
.venv311/Scripts/python.exe -m pytest -m "not integration" -v

# Skip slow tests
.venv311/Scripts/python.exe -m pytest -m "not slow" -v
```

## Test Structure

Each project follows this structure:

```
project_name/
├── tests/
│   ├── __init__.py
│   ├── test_<project>_smoke.py     # Smoke tests (imports, CLI, structure)
│   ├── test_<project>_unit.py      # Unit tests (functions, classes)
│   └── test_<project>_integration.py  # Integration tests (database, files)
├── src/                             # Source code
├── run.py                           # Entry point
└── README.md                        # Project documentation
```

## Smoke Tests

All projects include smoke tests that verify:

1. **Imports**: All modules can be imported without errors
1. **CLI**: Command-line interface responds to `--help`
1. **Dependencies**: Required packages are installed
1. **Structure**: Expected files and directories exist

## Shared Fixtures

Available in `tests/conftest.py`:

- `mock_mongo_connection`: Mock MongoDB client/database/collection
- `mock_settings`: Mock common_config settings
- `temp_data_dir`: Temporary data/input/output directories
- `temp_log_dir`: Temporary logs directory
- `sample_csv_data`: Sample CSV data for testing
- `sample_patient_data`: Sample patient records
- `project_root`: Repository root path
- `shared_config_path`: shared_config directory path

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.integration  # Requires real database
def test_mongo_query():
    pass


@pytest.mark.slow  # Takes > 5 seconds
def test_large_file_processing():
    pass


@pytest.mark.db  # Needs database connection
def test_collection_access():
    pass
```

Run tests by marker:

```bash
# Only integration tests
.venv311/Scripts/python.exe -m pytest -m integration

# Skip database tests
.venv311/Scripts/python.exe -m pytest -m "not db"
```

## Coverage Reports

Tests generate coverage reports in `artifacts/coverage/`:

```bash
# Run tests with coverage
.venv311/Scripts/python.exe -m pytest --cov

# View HTML report
start artifacts/coverage/htmlcov/index.html  # Windows
open artifacts/coverage/htmlcov/index.html   # macOS
```

## CI/CD Integration

GitHub Actions runs tests automatically on push/PR:

1. **Lint** job: Ruff linting and formatting
1. **Type-check** job: Pyright static analysis
1. **Tests** job: Full test suite with coverage
   - Uploads coverage reports (30-day retention)
   - Uploads test results (JUnit XML)
   - Codecov integration (optional)

## Writing New Tests

### 1. Create Test File

```python
# project/tests/test_feature.py
"""Tests for feature X."""

import pytest


class TestFeatureX:
    """Tests for feature X functionality."""

    def test_basic_usage(self):
        """Test basic feature X usage."""
        assert True  # Replace with actual test
```

### 2. Use Fixtures

```python
def test_with_mock_db(mock_mongo_connection):
    """Test using mocked MongoDB."""
    collection = mock_mongo_connection["collection"]
    collection.find_one.return_value = {"_id": "test"}

    # Your test code here
```

### 3. Run Tests

```bash
# Single file
.venv311/Scripts/python.exe -m pytest project/tests/test_feature.py -v

# Watch mode (requires pytest-watch)
.venv311/Scripts/python.exe -m pytest project/tests/test_feature.py --watch
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:

1. Check `tests/conftest.py` adds project paths to `sys.path`
1. Ensure `__init__.py` exists in test directories
1. Install project in editable mode: `pip install -e .`

### Pytest Not Found

```bash
# Install pytest
.venv311/Scripts/python.exe -m pip install pytest pytest-cov

# Verify installation
.venv311/Scripts/python.exe -m pytest --version
```

### Cache Issues

```bash
# Clear pytest cache
rm -rf artifacts/.pytest_cache

# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
```

## Next Steps

- [ ] Increase coverage to 30% minimum per project
- [ ] Add unit tests for core functions
- [ ] Add integration tests for database operations
- [ ] Set up pre-commit hooks for automatic testing
- [ ] Configure coverage thresholds in pyproject.toml
