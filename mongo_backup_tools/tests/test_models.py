"""Unit tests for Pydantic models."""

import pytest
from pathlib import Path
from pydantic import ValidationError
from urllib.parse import parse_qs, urlparse

from mongo_backup_tools.models.base import MongoConnectionOptions
from mongo_backup_tools.models.dump import MongoDumpOptions
from mongo_backup_tools.models.restore import MongoRestoreOptions
from mongo_backup_tools.models.export import ExportFormat, MongoExportOptions
from mongo_backup_tools.models.import_opts import ImportMode, MongoImportOptions


@pytest.mark.unit
class TestMongoConnectionOptions:
    """Test MongoDB connection options."""

    def test_default_connection(self):
        """Test default connection options."""
        opts = MongoConnectionOptions()
        assert opts.host == "localhost"
        assert opts.port == 27017
        assert opts.uri is None

    def test_build_uri_from_components(self):
        """Test building URI from components."""
        opts = MongoConnectionOptions(host="example.com", port=27018)
        uri = opts.build_uri()
        # Parse URI properly instead of substring matching
        parsed = urlparse(uri)
        assert parsed.scheme == "mongodb"
        assert parsed.hostname == "example.com"
        assert parsed.port == 27018

    def test_build_uri_with_auth(self):
        """Test building URI with authentication."""
        opts = MongoConnectionOptions(
            host="example.com",
            username="user",
            password="pass",
            auth_database="admin",
        )
        uri = opts.build_uri()
        # Parse URI properly instead of substring matching
        parsed = urlparse(uri)
        assert parsed.scheme == "mongodb"
        assert parsed.hostname == "example.com"
        assert parsed.username == "user"
        assert parsed.password == "pass"
        # Check query parameters
        query_params = parse_qs(parsed.query)
        assert query_params.get("authSource") == ["admin"]

    def test_uri_validation(self):
        """Test URI validation."""
        # Valid MongoDB URI
        opts = MongoConnectionOptions(uri="mongodb://localhost:27017")
        assert opts.uri == "mongodb://localhost:27017"

        # Invalid URI should raise validation error
        with pytest.raises(ValidationError):
            MongoConnectionOptions(uri="http://invalid")


@pytest.mark.unit
class TestMongoDumpOptions:
    """Test mongodump options."""

    def test_minimal_dump_options(self):
        """Test minimal dump options."""
        opts = MongoDumpOptions(output_dir=Path("dump"))
        assert opts.output_dir == Path("dump")
        assert opts.archive_file is None
        assert opts.gzip is False

    def test_dump_with_query(self):
        """Test dump with query filter."""
        opts = MongoDumpOptions(
            output_dir=Path("dump"),
            database="testdb",
            query='{"status": "active"}',
        )
        assert opts.query == '{"status": "active"}'

    def test_dump_get_script_args(self):
        """Test generating script arguments."""
        opts = MongoDumpOptions(
            host="example.com",
            port=27018,
            database="testdb",
            output_dir=Path("dump"),
            gzip=True,
        )
        args = opts.get_script_args()
        assert "--host" in args
        assert "example.com" in args
        assert "--port" in args
        assert "27018" in args
        assert "--db" in args
        assert "testdb" in args
        assert "--gzip" in args


@pytest.mark.unit
class TestMongoRestoreOptions:
    """Test mongorestore options."""

    def test_minimal_restore_options(self):
        """Test minimal restore options."""
        opts = MongoRestoreOptions(input_dir=Path("dump"))
        assert opts.input_dir == Path("dump")
        assert opts.drop_existing is False

    def test_namespace_remapping(self):
        """Test namespace remapping."""
        opts = MongoRestoreOptions(
            input_dir=Path("dump"),
            ns_from="olddb.oldcoll",
            ns_to="newdb.newcoll",
        )
        assert opts.ns_from == "olddb.oldcoll"
        assert opts.ns_to == "newdb.newcoll"

    def test_namespace_validation(self):
        """Test namespace pair validation."""
        # Both or neither should be specified
        with pytest.raises(ValidationError):
            opts = MongoRestoreOptions(
                input_dir=Path("dump"),
                ns_from="olddb.oldcoll",
            )
            opts.validate_namespace_pair()


@pytest.mark.unit
class TestMongoExportOptions:
    """Test mongoexport options."""

    def test_minimal_export_options(self):
        """Test minimal export options."""
        opts = MongoExportOptions(
            database="testdb",
            collection="testcoll",
        )
        assert opts.database == "testdb"
        assert opts.collection == "testcoll"
        assert opts.export_format == ExportFormat.JSON

    def test_csv_export_validation(self):
        """Test CSV export requires fields."""
        opts = MongoExportOptions(
            database="testdb",
            collection="testcoll",
            export_format=ExportFormat.CSV,
        )
        # Should raise error if no fields specified
        with pytest.raises(ValueError, match="fields.*required"):
            opts.validate_csv_requirements()

    def test_export_with_query(self):
        """Test export with query and sort."""
        opts = MongoExportOptions(
            database="testdb",
            collection="testcoll",
            query='{"status": "active"}',
            sort='{"createdAt": -1}',
            limit=100,
        )
        assert opts.query == '{"status": "active"}'
        assert opts.sort == '{"createdAt": -1}'
        assert opts.limit == 100


@pytest.mark.unit
class TestMongoImportOptions:
    """Test mongoimport options."""

    def test_minimal_import_options(self):
        """Test minimal import options."""
        opts = MongoImportOptions(
            database="testdb",
            collection="testcoll",
            input_file=Path("data.json"),
        )
        assert opts.database == "testdb"
        assert opts.collection == "testcoll"
        assert opts.input_file == Path("data.json")
        assert opts.import_mode == ImportMode.INSERT

    def test_upsert_mode_validation(self):
        """Test upsert mode requires upsert_fields."""
        opts = MongoImportOptions(
            database="testdb",
            collection="testcoll",
            input_file=Path("data.json"),
            import_mode=ImportMode.UPSERT,
        )
        # Should raise error if no upsert_fields specified
        with pytest.raises(ValueError, match="upsert_fields.*required"):
            opts.validate_upsert_requirements()

    def test_csv_import_validation(self):
        """Test CSV import requires fields or headerline."""
        opts = MongoImportOptions(
            database="testdb",
            collection="testcoll",
            input_file=Path("data.csv"),
            import_format=ExportFormat.CSV,
        )
        # Should raise error if neither fields nor headerline specified
        with pytest.raises(ValueError, match="fields.*headerline"):
            opts.validate_csv_requirements()

    def test_import_modes(self):
        """Test different import modes."""
        # Insert mode
        opts = MongoImportOptions(
            database="testdb",
            collection="testcoll",
            input_file=Path("data.json"),
            import_mode=ImportMode.INSERT,
        )
        assert opts.import_mode == ImportMode.INSERT

        # Upsert mode
        opts = MongoImportOptions(
            database="testdb",
            collection="testcoll",
            input_file=Path("data.json"),
            import_mode=ImportMode.UPSERT,
            upsert_fields=["_id"],
        )
        assert opts.import_mode == ImportMode.UPSERT
        assert opts.upsert_fields == ["_id"]

        # Merge mode
        opts = MongoImportOptions(
            database="testdb",
            collection="testcoll",
            input_file=Path("data.json"),
            import_mode=ImportMode.MERGE,
            upsert_fields=["email"],
        )
        assert opts.import_mode == ImportMode.MERGE
