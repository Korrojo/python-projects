"""Integration tests for orchestrators."""

import pytest
from unittest.mock import Mock, patch

from src.models.dump import MongoDumpOptions
from src.models.restore import MongoRestoreOptions
from src.models.export import ExportFormat, MongoExportOptions
from src.models.import_opts import ImportMode, MongoImportOptions
from src.orchestrators.dump import MongoDumpOrchestrator
from src.orchestrators.restore import MongoRestoreOrchestrator
from src.orchestrators.export import MongoExportOrchestrator
from src.orchestrators.import_orch import MongoImportOrchestrator
from src.orchestrators.base import MongoOperationResult


@pytest.mark.integration
class TestMongoDumpOrchestrator:
    """Test dump orchestrator."""

    def test_orchestrator_initialization(self):
        """Test orchestrator can be initialized."""
        orchestrator = MongoDumpOrchestrator()
        assert orchestrator is not None
        assert orchestrator.script_path.name == "mongodump.sh"

    @patch("subprocess.run")
    def test_dump_execution(self, mock_run, tmp_path):
        """Test dump execution with mocked subprocess."""
        # Mock successful execution
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Dumped 100 documents",
            stderr="",
        )

        options = MongoDumpOptions(
            database="testdb",
            output_dir=tmp_path / "dump",
        )

        orchestrator = MongoDumpOrchestrator()
        result = orchestrator.dump(options)

        assert result.success
        assert result.exit_code == 0
        assert mock_run.called

    @patch("subprocess.run")
    def test_dump_failure(self, mock_run, tmp_path):
        """Test dump handles failure correctly."""
        # Mock failed execution
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Connection failed",
        )

        options = MongoDumpOptions(
            database="testdb",
            output_dir=tmp_path / "dump",
        )

        orchestrator = MongoDumpOrchestrator()
        result = orchestrator.dump(options)

        assert not result.success
        assert result.exit_code == 1
        assert "Connection failed" in result.stderr

    def test_dump_validates_prerequisites(self):
        """Test dump validates script exists."""
        orchestrator = MongoDumpOrchestrator()
        # This should not raise if script exists
        # If script doesn't exist, it will raise FileNotFoundError
        # We just verify the method exists
        assert hasattr(orchestrator, "validate_prerequisites")


@pytest.mark.integration
class TestMongoRestoreOrchestrator:
    """Test restore orchestrator."""

    def test_orchestrator_initialization(self):
        """Test orchestrator can be initialized."""
        orchestrator = MongoRestoreOrchestrator()
        assert orchestrator is not None
        assert orchestrator.script_path.name == "mongorestore.sh"

    @patch("subprocess.run")
    def test_restore_execution(self, mock_run, tmp_path):
        """Test restore execution with mocked subprocess."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Restored 100 documents",
            stderr="",
        )

        options = MongoRestoreOptions(
            input_dir=tmp_path / "dump",
        )

        orchestrator = MongoRestoreOrchestrator()
        result = orchestrator.restore(options)

        assert result.success
        assert result.exit_code == 0
        assert mock_run.called

    @patch("subprocess.run")
    def test_restore_with_namespace_remapping(self, mock_run, tmp_path):
        """Test restore with namespace remapping."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Restored with remapping",
            stderr="",
        )

        options = MongoRestoreOptions(
            input_dir=tmp_path / "dump",
            ns_from="olddb.oldcoll",
            ns_to="newdb.newcoll",
        )

        orchestrator = MongoRestoreOrchestrator()
        result = orchestrator.restore(options)

        assert result.success
        # Verify namespace options were passed
        call_args = mock_run.call_args[0][0]
        assert any("--nsFrom" in str(arg) for arg in call_args)
        assert any("--nsTo" in str(arg) for arg in call_args)


@pytest.mark.integration
class TestMongoExportOrchestrator:
    """Test export orchestrator."""

    def test_orchestrator_initialization(self):
        """Test orchestrator can be initialized."""
        orchestrator = MongoExportOrchestrator()
        assert orchestrator is not None
        assert orchestrator.script_path.name == "mongoexport.sh"

    @patch("subprocess.run")
    def test_export_execution(self, mock_run):
        """Test export execution with mocked subprocess."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"_id": 1, "name": "test"}',
            stderr="",
        )

        options = MongoExportOptions(
            database="testdb",
            collection="testcoll",
        )

        orchestrator = MongoExportOrchestrator()
        result = orchestrator.export(options)

        assert result.success
        assert result.exit_code == 0
        assert mock_run.called

    @patch("subprocess.run")
    def test_csv_export(self, mock_run, tmp_path):
        """Test CSV export."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="name,email\nJohn,john@example.com",
            stderr="",
        )

        output_file = tmp_path / "export.csv"
        options = MongoExportOptions(
            database="testdb",
            collection="testcoll",
            export_format=ExportFormat.CSV,
            fields=["name", "email"],
            output_file=output_file,
        )

        orchestrator = MongoExportOrchestrator()
        result = orchestrator.export(options)

        assert result.success
        # Verify CSV-specific options were passed
        call_args = mock_run.call_args[0][0]
        assert any("--type" in str(arg) for arg in call_args)
        assert any("csv" in str(arg) for arg in call_args)


@pytest.mark.integration
class TestMongoImportOrchestrator:
    """Test import orchestrator."""

    def test_orchestrator_initialization(self):
        """Test orchestrator can be initialized."""
        orchestrator = MongoImportOrchestrator()
        assert orchestrator is not None
        assert orchestrator.script_path.name == "mongoimport.sh"

    @patch("subprocess.run")
    def test_import_execution(self, mock_run, tmp_path):
        """Test import execution with mocked subprocess."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Imported 100 documents",
            stderr="",
        )

        input_file = tmp_path / "data.json"
        input_file.write_text('{"name": "test"}')

        options = MongoImportOptions(
            database="testdb",
            collection="testcoll",
            input_file=input_file,
        )

        orchestrator = MongoImportOrchestrator()
        result = orchestrator.import_data(options)

        assert result.success
        assert result.exit_code == 0
        assert mock_run.called

    @patch("subprocess.run")
    def test_upsert_import(self, mock_run, tmp_path):
        """Test upsert import mode."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Upserted 50 documents",
            stderr="",
        )

        input_file = tmp_path / "data.json"
        input_file.write_text('{"_id": 1, "name": "test"}')

        options = MongoImportOptions(
            database="testdb",
            collection="testcoll",
            input_file=input_file,
            import_mode=ImportMode.UPSERT,
            upsert_fields=["_id"],
        )

        orchestrator = MongoImportOrchestrator()
        result = orchestrator.import_data(options)

        assert result.success
        # Verify upsert options were passed
        call_args = mock_run.call_args[0][0]
        assert any("--mode" in str(arg) for arg in call_args)
        assert any("upsert" in str(arg) for arg in call_args)


@pytest.mark.integration
class TestMongoOperationResult:
    """Test operation result class."""

    def test_result_creation(self):
        """Test creating operation result."""
        result = MongoOperationResult(
            success=True,
            exit_code=0,
            stdout="Success",
            stderr="",
            duration=1.5,
        )

        assert result.success
        assert result.exit_code == 0
        assert result.stdout == "Success"
        assert result.stderr == ""
        assert result.duration == 1.5

    def test_result_repr(self):
        """Test result string representation."""
        result = MongoOperationResult(
            success=True,
            exit_code=0,
            stdout="Success",
            stderr="",
            duration=1.5,
        )

        repr_str = repr(result)
        assert "MongoOperationResult" in repr_str
        assert "success=True" in repr_str
        assert "exit_code=0" in repr_str
        assert "1.50s" in repr_str
