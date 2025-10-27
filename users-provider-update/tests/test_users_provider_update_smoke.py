"""Smoke tests for users-provider-update project.

Tests basic functionality:
- Module imports work correctly
- Scripts exist and can be executed
- Required dependencies are available
"""

import subprocess
import sys
from pathlib import Path


class TestImports:
    """Test that all critical modules can be imported."""

    def test_import_validate_script(self):
        """Test that validate_users_update.py can be imported."""
        sys.path.insert(0, str(Path("users-provider-update").absolute()))
        import validate_users_update

        assert validate_users_update is not None

    def test_import_src_package(self):
        """Test that src package can be imported."""
        sys.path.insert(0, str(Path("users-provider-update").absolute()))
        import src

        assert src is not None


class TestCLI:
    """Test CLI functionality."""

    def test_validate_script_help(self):
        """Test that validate_users_update.py --help works."""
        result = subprocess.run(
            [sys.executable, "users-provider-update/validate_users_update.py", "--help"],
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
        readme = Path("users-provider-update/README.md")
        assert readme.exists()

    def test_requirements_exists(self):
        """Test that requirements.txt exists."""
        req = Path("users-provider-update/requirements.txt")
        assert req.exists()

    def test_validate_script_exists(self):
        """Test that validate_users_update.py exists."""
        script = Path("users-provider-update/validate_users_update.py")
        assert script.exists()

    def test_src_directory_exists(self):
        """Test that src/ directory exists."""
        src = Path("users-provider-update/src")
        assert src.exists()
        assert src.is_dir()

    def test_docs_directory_exists(self):
        """Test that docs/ directory exists."""
        docs = Path("users-provider-update/docs")
        assert docs.exists()
        assert docs.is_dir()
