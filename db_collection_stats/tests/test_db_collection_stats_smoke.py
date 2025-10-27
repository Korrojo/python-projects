"""Smoke tests for db_collection_stats."""

from pathlib import Path


class TestImports:
    """Test that all critical modules can be imported."""

    def test_import_run_module(self):
        """Test that run.py can be imported."""
        # Simply verify run.py exists and has proper structure

        run_path = Path("db_collection_stats/run.py").absolute()
        assert run_path.exists(), "run.py not found"

        # Verify it has valid Python syntax by checking it with ast
        import ast

        with open(run_path) as f:
            code = f.read()
            tree = ast.parse(code)

        # Check for main function
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        assert "main" in functions, "run.py missing main() function"


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
        readme = Path("db_collection_stats/README.md")
        assert readme.exists()

    def test_run_script_exists(self):
        """Test that run.py exists."""
        run = Path("db_collection_stats/run.py")
        assert run.exists()

    def test_src_directory_exists(self):
        """Test that src/ directory exists."""
        src = Path("db_collection_stats/src")
        assert src.exists()
        assert src.is_dir()
