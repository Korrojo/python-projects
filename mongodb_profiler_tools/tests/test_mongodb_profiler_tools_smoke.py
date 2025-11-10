"""Smoke tests for mongodb_profiler_tools."""

import mongodb_profiler_tools
import mongodb_profiler_tools.cli as cli_module
import mongodb_profiler_tools.profiler_stats as profiler_stats_module
import mongodb_profiler_tools.slow_queries as slow_queries_module


def test_module_imports():
    """Test that all modules can be imported."""
    assert mongodb_profiler_tools is not None
    assert cli_module is not None
    assert profiler_stats_module is not None
    assert slow_queries_module is not None


def test_run_has_app():
    """Test that run.py defines the app."""
    import mongodb_profiler_tools.run as run

    assert hasattr(run, "app")


def test_cli_has_typer_app():
    """Test that cli module has a Typer app."""
    assert hasattr(cli_module, "app")
    assert cli_module.app is not None


def test_slow_queries_functions_exist():
    """Test that slow_queries module has required functions."""
    assert hasattr(slow_queries_module, "analyze_slow_queries")
    assert hasattr(slow_queries_module, "print_slow_queries")
    assert hasattr(slow_queries_module, "export_slow_queries_to_csv")


def test_profiler_stats_functions_exist():
    """Test that profiler_stats module has required functions."""
    assert hasattr(profiler_stats_module, "get_profiler_stats")
    assert hasattr(profiler_stats_module, "print_profiler_stats")
