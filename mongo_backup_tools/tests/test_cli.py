"""Tests for CLI commands."""

import pytest
from typer.testing import CliRunner
from unittest.mock import patch

from mongo_backup_tools.cli import app
from mongo_backup_tools.orchestrators.base import MongoOperationResult


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.mark.unit
class TestCLICommands:
    """Test CLI command interface."""

    def test_version_command(self, runner):
        """Test version command."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "mongo-backup-tools version" in result.stdout

    def test_help_command(self, runner):
        """Test help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "mongo-backup-tools" in result.stdout
        assert "dump" in result.stdout
        assert "restore" in result.stdout
        assert "export" in result.stdout
        assert "import" in result.stdout

    def test_dump_help(self, runner):
        """Test dump command help."""
        result = runner.invoke(app, ["dump", "--help"])
        assert result.exit_code == 0
        assert "mongodump" in result.stdout.lower() or "dump" in result.stdout.lower()

    def test_restore_help(self, runner):
        """Test restore command help."""
        result = runner.invoke(app, ["restore", "--help"])
        assert result.exit_code == 0
        assert "restore" in result.stdout.lower()

    def test_export_help(self, runner):
        """Test export command help."""
        result = runner.invoke(app, ["export", "--help"])
        assert result.exit_code == 0
        assert "export" in result.stdout.lower()

    def test_import_help(self, runner):
        """Test import command help."""
        result = runner.invoke(app, ["import", "--help"])
        assert result.exit_code == 0
        assert "import" in result.stdout.lower()


@pytest.mark.integration
class TestDumpCommand:
    """Test dump command."""

    @patch("mongo_backup_tools.orchestrators.dump.MongoDumpOrchestrator.dump")
    @patch("mongo_backup_tools.orchestrators.dump.MongoDumpOrchestrator.validate_prerequisites")
    def test_dump_success(self, mock_validate, mock_dump, runner, tmp_path):
        """Test successful dump command."""
        mock_validate.return_value = None
        mock_dump.return_value = MongoOperationResult(
            success=True,
            exit_code=0,
            stdout="Dumped successfully",
            stderr="",
            duration=1.0,
        )

        result = runner.invoke(
            app,
            [
                "dump",
                "--database",
                "testdb",
                "--out",
                str(tmp_path / "dump"),
            ],
        )

        assert result.exit_code == 0
        assert "completed successfully" in result.stdout.lower()
        assert mock_dump.called

    @patch("mongo_backup_tools.orchestrators.dump.MongoDumpOrchestrator.dump")
    @patch("mongo_backup_tools.orchestrators.dump.MongoDumpOrchestrator.validate_prerequisites")
    def test_dump_failure(self, mock_validate, mock_dump, runner, tmp_path):
        """Test failed dump command."""
        mock_validate.return_value = None
        mock_dump.return_value = MongoOperationResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr="Connection error",
            duration=0.5,
        )

        result = runner.invoke(
            app,
            [
                "dump",
                "--database",
                "testdb",
                "--out",
                str(tmp_path / "dump"),
            ],
        )

        assert result.exit_code == 1
        assert "failed" in result.stdout.lower()


@pytest.mark.integration
class TestRestoreCommand:
    """Test restore command."""

    @patch("mongo_backup_tools.orchestrators.restore.MongoRestoreOrchestrator.restore")
    @patch("mongo_backup_tools.orchestrators.restore.MongoRestoreOrchestrator.validate_prerequisites")
    def test_restore_success(self, mock_validate, mock_restore, runner, tmp_path):
        """Test successful restore command."""
        mock_validate.return_value = None
        mock_restore.return_value = MongoOperationResult(
            success=True,
            exit_code=0,
            stdout="Restored successfully",
            stderr="",
            duration=1.0,
        )

        result = runner.invoke(
            app,
            [
                "restore",
                "--dir",
                str(tmp_path / "dump"),
            ],
        )

        assert result.exit_code == 0
        assert "completed successfully" in result.stdout.lower()
        assert mock_restore.called


@pytest.mark.integration
class TestExportCommand:
    """Test export command."""

    @patch("mongo_backup_tools.orchestrators.export.MongoExportOrchestrator.export")
    @patch("mongo_backup_tools.orchestrators.export.MongoExportOrchestrator.validate_prerequisites")
    def test_export_success(self, mock_validate, mock_export, runner, tmp_path):
        """Test successful export command."""
        mock_validate.return_value = None
        mock_export.return_value = MongoOperationResult(
            success=True,
            exit_code=0,
            stdout="Exported successfully",
            stderr="",
            duration=1.0,
        )

        result = runner.invoke(
            app,
            [
                "export",
                "--database",
                "testdb",
                "--collection",
                "testcoll",
            ],
        )

        assert result.exit_code == 0
        assert "completed successfully" in result.stdout.lower()
        assert mock_export.called

    @patch("mongo_backup_tools.orchestrators.export.MongoExportOrchestrator.export")
    @patch("mongo_backup_tools.orchestrators.export.MongoExportOrchestrator.validate_prerequisites")
    def test_csv_export(self, mock_validate, mock_export, runner):
        """Test CSV export."""
        mock_validate.return_value = None
        mock_export.return_value = MongoOperationResult(
            success=True,
            exit_code=0,
            stdout="Exported to CSV",
            stderr="",
            duration=1.0,
        )

        result = runner.invoke(
            app,
            [
                "export",
                "--database",
                "testdb",
                "--collection",
                "testcoll",
                "--type",
                "csv",
                "--field",
                "name",
                "--field",
                "email",
            ],
        )

        assert result.exit_code == 0
        assert mock_export.called


@pytest.mark.integration
class TestImportCommand:
    """Test import command."""

    @patch("mongo_backup_tools.orchestrators.import_orch.MongoImportOrchestrator.import_data")
    @patch("mongo_backup_tools.orchestrators.import_orch.MongoImportOrchestrator.validate_prerequisites")
    def test_import_success(self, mock_validate, mock_import, runner, tmp_path):
        """Test successful import command."""
        mock_validate.return_value = None
        mock_import.return_value = MongoOperationResult(
            success=True,
            exit_code=0,
            stdout="Imported successfully",
            stderr="",
            duration=1.0,
        )

        input_file = tmp_path / "data.json"
        input_file.write_text('{"name": "test"}')

        result = runner.invoke(
            app,
            [
                "import",
                "--database",
                "testdb",
                "--collection",
                "testcoll",
                "--file",
                str(input_file),
            ],
        )

        assert result.exit_code == 0
        assert "completed successfully" in result.stdout.lower()
        assert mock_import.called

    @patch("mongo_backup_tools.orchestrators.import_orch.MongoImportOrchestrator.import_data")
    @patch("mongo_backup_tools.orchestrators.import_orch.MongoImportOrchestrator.validate_prerequisites")
    def test_upsert_import(self, mock_validate, mock_import, runner, tmp_path):
        """Test upsert import mode."""
        mock_validate.return_value = None
        mock_import.return_value = MongoOperationResult(
            success=True,
            exit_code=0,
            stdout="Upserted successfully",
            stderr="",
            duration=1.0,
        )

        input_file = tmp_path / "data.json"
        input_file.write_text('{"_id": 1, "name": "test"}')

        result = runner.invoke(
            app,
            [
                "import",
                "--database",
                "testdb",
                "--collection",
                "testcoll",
                "--file",
                str(input_file),
                "--mode",
                "upsert",
                "--upsert-fields",
                "_id",
            ],
        )

        assert result.exit_code == 0
        assert mock_import.called
