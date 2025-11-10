"""Smoke tests for staff_appointment_visitStatus project.

Tests basic functionality:
- Module imports work correctly
- CLI shows help without errors
- Required dependencies are available
"""

import subprocess
import sys
from pathlib import Path


class TestImports:
    """Test that all critical modules can be imported."""

    def test_import_run_module(self):
        """Test that run.py can be imported."""
        sys.path.insert(0, str(Path("staff_appointment_visitStatus").absolute()))
        import run

        assert hasattr(run, "app")

    def test_import_visit_status_report(self):
        """Test that visit_status_report module can be imported."""
        sys.path.insert(0, str(Path("staff_appointment_visitStatus").absolute()))
        import visit_status_report

        assert hasattr(visit_status_report, "main")

    def test_import_agg_query_runner(self):
        """Test that agg_query_runner module can be imported."""
        sys.path.insert(0, str(Path("staff_appointment_visitStatus").absolute()))
        import agg_query_runner

        assert agg_query_runner is not None


class TestCLI:
    """Test CLI functionality."""

    def test_run_help(self):
        """Test that run.py --help works."""
        result = subprocess.run(
            [sys.executable, "staff_appointment_visitStatus/run.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "help" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_visit_status_report_help(self):
        """Test that visit_status_report.py --help works."""
        result = subprocess.run(
            [sys.executable, "staff_appointment_visitStatus/visit_status_report.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "help" in result.stdout.lower() or "usage" in result.stdout.lower()


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

    def test_typer_available(self):
        """Test that typer is available."""
        import typer

        assert typer is not None


class TestProjectStructure:
    """Test project directory structure."""

    def test_readme_exists(self):
        """Test that README.md exists."""
        readme = Path("staff_appointment_visitStatus/README.md")
        assert readme.exists()

    def test_requirements_exists(self):
        """Test that requirements.txt exists."""
        req = Path("staff_appointment_visitStatus/requirements.txt")
        assert req.exists()

    def test_run_script_exists(self):
        """Test that run.py exists."""
        run = Path("staff_appointment_visitStatus/run.py")
        assert run.exists()

    def test_visit_status_report_exists(self):
        """Test that visit_status_report.py exists."""
        script = Path("staff_appointment_visitStatus/visit_status_report.py")
        assert script.exists()

    def test_agg_query_runner_exists(self):
        """Test that agg_query_runner.py exists."""
        script = Path("staff_appointment_visitStatus/agg_query_runner.py")
        assert script.exists()
