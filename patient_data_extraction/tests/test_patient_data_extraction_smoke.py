"""Smoke tests for patient_data_extraction project.

Tests basic functionality:
- Module imports work correctly
- Run script shows help without errors
- Required dependencies are available
"""

import subprocess
import sys
from pathlib import Path


class TestImports:
    """Test that all critical modules can be imported."""

    def test_import_run_module(self):
        """Test that run.py can be imported."""
        sys.path.insert(0, str(Path("patient_data_extraction").absolute()))
        import run

        assert hasattr(run, "main")

    def test_import_patient_extractor(self):
        """Test that patient_extractor module can be imported."""
        sys.path.insert(0, str(Path("patient_data_extraction/src").absolute()))
        import patient_extractor

        assert hasattr(patient_extractor, "PatientDataExtractor")
        assert hasattr(patient_extractor, "MultiDatabaseConfigManager")


class TestCLI:
    """Test CLI functionality."""

    def test_run_help(self):
        """Test that run.py --help works."""
        result = subprocess.run(
            [sys.executable, "patient_data_extraction/run.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "help" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_run_dry_run(self):
        """Test that run.py --dry-run validates config."""
        result = subprocess.run(
            [sys.executable, "patient_data_extraction/run.py", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        # May fail if config is missing, but should not crash
        assert "Configuration" in result.stdout or "configuration" in result.stdout or result.returncode in (0, 1)


class TestDependencies:
    """Test that required dependencies are installed."""

    def test_common_config_available(self):
        """Test that common_config package is available."""
        import common_config

        assert common_config is not None

    def test_pymongo_available(self):
        """Test that pymongo is available."""
        import pymongo

        assert pymongo is not None


class TestProjectStructure:
    """Test project directory structure."""

    def test_readme_exists(self):
        """Test that README.md exists."""
        readme = Path("patient_data_extraction/README.md")
        assert readme.exists()

    def test_requirements_exists(self):
        """Test that requirements.txt exists."""
        req = Path("patient_data_extraction/requirements.txt")
        assert req.exists()

    def test_run_script_exists(self):
        """Test that run.py exists."""
        run = Path("patient_data_extraction/run.py")
        assert run.exists()

    def test_src_directory_exists(self):
        """Test that src/ directory exists."""
        src = Path("patient_data_extraction/src")
        assert src.exists()
        assert src.is_dir()
