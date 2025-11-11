import os

import pytest


@pytest.mark.unit
def test_import_and_settings_paths():
    # Import inside test to avoid hard dependency when running partial tests
    from common_config.config import get_settings

    # Ensure we can construct settings even if shared_config/.env is minimal
    s = get_settings()
    assert hasattr(s, "paths"), "settings should expose paths"
    # Check shared directories exist or can be created
    for p in (s.paths.data_input, s.paths.data_output, s.paths.logs, s.paths.temp, s.paths.archive):
        os.makedirs(p, exist_ok=True)
        assert os.path.isdir(p)


@pytest.mark.integration
def test_optional_mongo_attrs_present():
    from common_config.config import get_settings

    s = get_settings()
    # Unified config may not set these in CI; just assert attributes exist
    assert hasattr(s, "mongodb_uri")
    assert hasattr(s, "database_name")
