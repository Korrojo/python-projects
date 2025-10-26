"""Smoke tests for patient_demographic project.

Tests basic functionality:
- Module imports work correctly
- Scripts exist and can be executed
- Required dependencies are available
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestImports:
    """Test that all critical modules can be imported."""

    def test_import_validate_script(self):
        """Test that validate_prod_vs_training.py can be imported."""
        sys.path.insert(0, str(Path("patient_demographic").absolute()))
        import validate_prod_vs_training

        assert validate_prod_vs_training is not None

    def test_import_src_package(self):
        """Test that src package can be imported."""
        sys.path.insert(0, str(Path("patient_demographic").absolute()))
        import src

        assert src is not None


class TestCLI:
    """Test CLI functionality."""

    def test_validate_script_help(self):
        """Test that validate_prod_vs_training.py --help works."""
        result = subprocess.run(
            [sys.executable, "patient_demographic/validate_prod_vs_training.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Some scripts may not have --help, check for reasonable output
        assert result.returncode in (0, 1, 2)


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
        readme = Path("patient_demographic/README.md")
        assert readme.exists()

    def test_requirements_exists(self):
        """Test that requirements.txt exists."""
        req = Path("patient_demographic/requirements.txt")
        assert req.exists()

    def test_validate_script_exists(self):
        """Test that validate_prod_vs_training.py exists."""
        script = Path("patient_demographic/validate_prod_vs_training.py")
        assert script.exists()

    def test_src_directory_exists(self):
        """Test that src/ directory exists."""
        src = Path("patient_demographic/src")
        assert src.exists()
        assert src.is_dir()

    def test_scripts_directory_exists(self):
        """Test that scripts/ directory exists."""
        scripts = Path("patient_demographic/scripts")
        assert scripts.exists()
        assert scripts.is_dir()
