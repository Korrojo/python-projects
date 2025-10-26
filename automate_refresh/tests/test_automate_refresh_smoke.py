"""Smoke tests for automate_refresh project.

Tests basic functionality:
- Module imports work correctly
- Run script shows help without errors
- Required dependencies are available
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestImports:
    """Test that all critical modules can be imported."""

    def test_import_run_module(self):
        """Test that run.py can be imported."""
        sys.path.insert(0, str(Path("automate_refresh").absolute()))
        import run

        assert hasattr(run, "main") or hasattr(run, "app")

    def test_import_init(self):
        """Test that package __init__ can be imported."""
        sys.path.insert(0, str(Path(".").absolute()))
        import automate_refresh

        assert automate_refresh is not None


class TestCLI:
    """Test CLI functionality."""

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific script")
    def test_run_help_win(self):
        """Test that run.py --help works on Windows."""
        result = subprocess.run(
            [sys.executable, "automate_refresh/run.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Should exit with 0 or show help message
        assert result.returncode in (0, 2) or "help" in result.stdout.lower() or "usage" in result.stdout.lower()

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix-specific script")
    def test_run_help_unix(self):
        """Test that run.py --help works on Unix systems."""
        result = subprocess.run(
            [sys.executable, "automate_refresh/run.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Should exit with 0 or show help message
        assert result.returncode in (0, 2) or "help" in result.stdout.lower() or "usage" in result.stdout.lower()


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
        readme = Path("automate_refresh/README.md")
        assert readme.exists()

    def test_requirements_exists(self):
        """Test that requirements.txt exists."""
        req = Path("automate_refresh/requirements.txt")
        assert req.exists()

    def test_run_script_exists(self):
        """Test that run.py exists."""
        run = Path("automate_refresh/run.py")
        assert run.exists()
