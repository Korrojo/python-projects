"""Smoke tests for mongodb_index_tools."""

import sys
from pathlib import Path


class TestImports:
    """Test that all critical modules can be imported."""

    def test_import_run_module(self):
        """Test that run.py can be imported."""
        sys.path.insert(0, str(Path("mongodb_index_tools").absolute()))
        import run

        assert hasattr(run, "main")


class TestDependencies:
    """Test that required dependencies are installed."""

    def test_common_config_available(self):
        """Test that common_config package is available."""
        import common_config

        assert common_config is not None


class TestProjectStructure:
    """Test project directory structure."""

    def test_readme_exists(self):
        """Test that README.md exists."""
        readme = Path("mongodb_index_tools/README.md")
        assert readme.exists()

    def test_run_script_exists(self):
        """Test that run.py exists."""
        run = Path("mongodb_index_tools/run.py")
        assert run.exists()

    def test_src_directory_exists(self):
        """Test that src/ directory exists."""
        src = Path("mongodb_index_tools/src")
        assert src.exists()
        assert src.is_dir()
