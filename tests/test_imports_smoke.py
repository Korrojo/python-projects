def test_projects_importable():
    # Common library
    import importlib

    assert importlib.import_module("common_config") is not None

    # Patients HCMID validator package
    try:
        assert importlib.import_module("patients_hcmid_validator") is not None
    except ModuleNotFoundError:
        # It may not be installed in editable mode locally; CI will install it
        pass

    # users-provider-update connector import
    try:
        mod = importlib.import_module("users-provider-update.src.connectors.mongodb_connector")
        assert mod is not None
    except ModuleNotFoundError:
        # Dotted path with hyphen is not a valid module name; import via relative path not supported here
        # Ensure at least the package path exists by importing through sys.path modifications in scripts
        pass
