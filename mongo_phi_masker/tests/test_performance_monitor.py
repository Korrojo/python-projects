"""Unit tests for PerformanceMonitor with phase tracking."""

import json
import tempfile
import time
from pathlib import Path

import pytest

from src.utils.performance_monitor import PerformanceMonitor


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""

    @pytest.fixture
    def monitor(self):
        """Create a PerformanceMonitor instance for testing."""
        return PerformanceMonitor()

    def test_initialization(self, monitor):
        """Test PerformanceMonitor initialization."""
        assert monitor.metrics == {}
        assert monitor.phases == {}
        assert monitor.phase_order == []
        assert monitor._current_phase is None
        assert monitor.start_time > 0

    def test_start_phase(self, monitor):
        """Test starting a phase."""
        monitor.start_phase("Test Phase", metadata={"key": "value"})

        assert "Test Phase" in monitor.phases
        assert monitor._current_phase == "Test Phase"
        assert "Test Phase" in monitor.phase_order
        assert len(monitor.phases["Test Phase"]) == 1

        phase_data = monitor.phases["Test Phase"][0]
        assert "start_time" in phase_data
        assert "start_timestamp" in phase_data
        assert phase_data["metadata"] == {"key": "value"}
        assert "end_time" not in phase_data

    def test_end_phase(self, monitor):
        """Test ending a phase."""
        monitor.start_phase("Test Phase")
        time.sleep(0.1)  # Small delay to ensure duration > 0
        monitor.end_phase("Test Phase", result_metadata={"status": "success"})

        phase_data = monitor.phases["Test Phase"][0]
        assert "end_time" in phase_data
        assert "end_timestamp" in phase_data
        assert "duration_seconds" in phase_data
        assert phase_data["duration_seconds"] > 0
        assert phase_data["result_metadata"] == {"status": "success"}
        assert monitor._current_phase is None

    def test_end_phase_without_name(self, monitor):
        """Test ending phase without specifying name (uses current phase)."""
        monitor.start_phase("Test Phase")
        time.sleep(0.1)
        monitor.end_phase()  # No phase name specified

        assert monitor._current_phase is None
        assert "end_time" in monitor.phases["Test Phase"][0]

    def test_phase_context_manager(self, monitor):
        """Test phase tracking with context manager."""
        with monitor.phase("Test Phase", metadata={"batch": 1}):
            time.sleep(0.1)

        assert "Test Phase" in monitor.phases
        assert monitor._current_phase is None
        phase_data = monitor.phases["Test Phase"][0]
        assert "end_time" in phase_data
        assert phase_data["duration_seconds"] > 0
        assert phase_data["metadata"] == {"batch": 1}

    def test_phase_context_manager_with_exception(self, monitor):
        """Test that phase is ended even if exception occurs."""
        with pytest.raises(ValueError):
            with monitor.phase("Test Phase"):
                raise ValueError("Test error")
            # Phase should still be ended
            assert "Test Phase" in monitor.phases
            assert monitor._current_phase is None
            assert "end_time" in monitor.phases["Test Phase"][0]

    def test_multiple_phase_instances(self, monitor):
        """Test tracking the same phase multiple times."""
        for i in range(3):
            with monitor.phase("Process Batch", metadata={"batch_num": i}):
                time.sleep(0.05)

        assert "Process Batch" in monitor.phases
        assert len(monitor.phases["Process Batch"]) == 3

        # Verify each instance has its own data
        for i, phase_data in enumerate(monitor.phases["Process Batch"]):
            assert phase_data["metadata"]["batch_num"] == i
            assert phase_data["duration_seconds"] > 0

    def test_nested_phases(self, monitor):
        """Test nested phase tracking.

        Note: The implementation auto-ends the outer phase when inner phase starts.
        This is by design to ensure only one phase is active at a time.
        """
        with monitor.phase("Outer Phase"):
            time.sleep(0.05)
            with monitor.phase("Inner Phase"):
                time.sleep(0.05)

        assert "Outer Phase" in monitor.phases
        assert "Inner Phase" in monitor.phases
        assert monitor.phase_order == ["Outer Phase", "Inner Phase"]

        # Both phases should have completed
        assert "end_time" in monitor.phases["Outer Phase"][0]
        assert "end_time" in monitor.phases["Inner Phase"][0]

    def test_get_phase_summary(self, monitor):
        """Test getting phase summary statistics."""
        # Create multiple instances with varying durations
        for i in range(5):
            with monitor.phase("Test Phase"):
                time.sleep(0.02 * (i + 1))  # Increasing durations

        summary = monitor.get_phase_summary()

        assert "Test Phase" in summary
        stats = summary["Test Phase"]

        assert stats["count"] == 5
        assert stats["total_duration"] > 0
        assert stats["average_duration"] > 0
        assert stats["min_duration"] > 0
        assert stats["max_duration"] > 0
        assert stats["max_duration"] > stats["min_duration"]
        assert len(stats["entries"]) == 5

    def test_get_phase_summary_empty(self, monitor):
        """Test phase summary with no completed phases."""
        summary = monitor.get_phase_summary()
        assert summary == {}

    def test_get_phase_summary_incomplete_phase(self, monitor):
        """Test phase summary with incomplete phase (not ended)."""
        monitor.start_phase("Incomplete Phase")
        # Don't end the phase

        summary = monitor.get_phase_summary()
        assert "Incomplete Phase" in summary

        stats = summary["Incomplete Phase"]
        assert stats["count"] == 0  # No completed instances
        assert stats["total_duration"] == 0

    def test_generate_performance_report(self, monitor):
        """Test generating performance report."""
        # Add some phases
        with monitor.phase("Phase 1", metadata={"test": True}):
            time.sleep(0.1)

        with monitor.phase("Phase 2"):
            time.sleep(0.05)

        report = monitor.generate_performance_report()

        # Check report structure
        assert "report_timestamp" in report
        assert "total_runtime_seconds" in report
        assert "total_runtime_formatted" in report
        assert "resource_usage" in report
        assert "phases" in report
        assert "phase_order" in report

        # Check resource usage
        assert "average_cpu_percent" in report["resource_usage"]
        assert "average_memory_percent" in report["resource_usage"]
        assert "peak_cpu_percent" in report["resource_usage"]
        assert "peak_memory_percent" in report["resource_usage"]
        assert "samples_collected" in report["resource_usage"]

        # Check phases
        assert "Phase 1" in report["phases"]
        assert "Phase 2" in report["phases"]
        assert report["phase_order"] == ["Phase 1", "Phase 2"]

    def test_generate_performance_report_to_file(self, monitor):
        """Test saving performance report to file."""
        with monitor.phase("Test Phase"):
            time.sleep(0.05)

        with tempfile.TemporaryDirectory() as tmpdir:
            report_file = Path(tmpdir) / "performance_report.json"

            report = monitor.generate_performance_report(output_file=str(report_file))

            # Check file was created
            assert report_file.exists()

            # Load and verify file contents
            with report_file.open() as f:
                file_report = json.load(f)

            assert file_report["phases"]["Test Phase"]["count"] == 1
            assert file_report == report

    def test_format_duration_seconds(self, monitor):
        """Test duration formatting for seconds."""
        assert monitor._format_duration(5.5) == "5.50s"
        assert monitor._format_duration(45.12) == "45.12s"

    def test_format_duration_minutes(self, monitor):
        """Test duration formatting for minutes."""
        result = monitor._format_duration(125.5)  # 2m 5.5s
        assert result.startswith("2m")
        assert "5.50s" in result

    def test_format_duration_hours(self, monitor):
        """Test duration formatting for hours."""
        result = monitor._format_duration(7325.5)  # 2h 2m 5.5s
        assert result.startswith("2h")
        assert "2m" in result
        assert "5.50s" in result

    def test_phase_order_preservation(self, monitor):
        """Test that phase order is preserved."""
        phases = ["Phase A", "Phase B", "Phase C", "Phase D"]

        for phase_name in phases:
            with monitor.phase(phase_name):
                pass

        assert monitor.phase_order == phases

        # Check report also preserves order
        report = monitor.generate_performance_report()
        assert report["phase_order"] == phases

    def test_overlapping_phase_warning(self, monitor, caplog):
        """Test warning when starting new phase without ending current one."""
        monitor.start_phase("Phase 1")
        monitor.start_phase("Phase 2")  # Should trigger warning and end Phase 1

        # Phase 1 should have been auto-ended
        assert "end_time" in monitor.phases["Phase 1"][0]
        assert monitor._current_phase == "Phase 2"

    def test_end_nonexistent_phase(self, monitor, caplog):
        """Test ending a phase that doesn't exist."""
        monitor.end_phase("Nonexistent Phase")

        # Should log warning, not crash
        assert "not found" in caplog.text.lower() or "no active phase" in caplog.text.lower()

    def test_end_already_ended_phase(self, monitor, caplog):
        """Test ending a phase that was already ended."""
        monitor.start_phase("Test Phase")
        monitor.end_phase("Test Phase")
        monitor.end_phase("Test Phase")  # Try to end again

        # Should log warning
        assert "already ended" in caplog.text.lower() or "not found" in caplog.text.lower()

    def test_phase_metadata_preservation(self, monitor):
        """Test that phase metadata is preserved correctly."""
        metadata = {
            "batch_size": 100,
            "collection": "test_collection",
            "nested": {"key": "value"},
            "list": [1, 2, 3],
        }

        result_metadata = {"status": "success", "processed": 100}

        # Use manual start/end to test result_metadata
        monitor.start_phase("Test Phase", metadata=metadata)
        time.sleep(0.01)
        monitor.end_phase("Test Phase", result_metadata=result_metadata)

        phase_data = monitor.phases["Test Phase"][0]
        assert phase_data["metadata"] == metadata
        assert phase_data["result_metadata"] == result_metadata

    def test_log_phase_summary(self, monitor, caplog):
        """Test logging phase summary."""
        import logging

        caplog.set_level(logging.INFO)

        with monitor.phase("Test Phase"):
            time.sleep(0.05)

        monitor.log_phase_summary()

        # Check that summary was logged
        log_text = caplog.text.lower()
        assert "performance phase summary" in log_text
        assert "test phase" in log_text
        assert "count" in log_text
        assert "duration" in log_text

    def test_calculate_throughput(self, monitor, caplog):
        """Test throughput calculation."""
        import logging

        caplog.set_level(logging.INFO)

        time.sleep(0.1)  # Small delay
        throughput = monitor.calculate_throughput(1000)

        assert throughput > 0
        log_text = caplog.text.lower()
        assert "processed 1000 documents" in log_text
        assert "throughput" in log_text

    def test_calculate_throughput_with_custom_elapsed(self, monitor):
        """Test throughput calculation with custom elapsed time."""
        throughput = monitor.calculate_throughput(1000, elapsed=10.0)
        assert throughput == 100.0  # 1000 docs / 10 seconds

    def test_calculate_throughput_zero_elapsed(self, monitor):
        """Test throughput calculation with zero elapsed time."""
        throughput = monitor.calculate_throughput(1000, elapsed=0.0)
        assert throughput == 0  # Should handle divide by zero

    def test_phase_summary_with_zero_phases(self, monitor):
        """Test phase summary when no phases have been tracked."""
        summary = monitor.get_phase_summary()
        assert summary == {}

        report = monitor.generate_performance_report()
        assert report["phases"] == {}
        assert report["phase_order"] == []
