import json
import logging
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil


class PerformanceMonitor:
    """Utility for monitoring and reporting performance metrics with phase tracking."""

    def __init__(self, logger=None):
        """Initialize the performance monitor.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.metrics = {}
        self.phases = {}  # Track individual phases
        self.phase_order = []  # Track order of phases
        self.start_time = time.time()
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()
        self._current_phase = None  # Track currently active phase

    def start_monitoring(self, interval=5.0):
        """Start background monitoring thread.

        Args:
            interval: Monitoring interval in seconds
        """
        self._stop_monitoring.clear()
        self._monitoring_thread = threading.Thread(target=self._monitor_resources, args=(interval,), daemon=True)
        self._monitoring_thread.start()

    def stop_monitoring(self):
        """Stop background monitoring thread."""
        if self._monitoring_thread:
            self._stop_monitoring.set()
            self._monitoring_thread.join()
            self._monitoring_thread = None

    def _monitor_resources(self, interval):
        """Background thread for resource monitoring."""
        while not self._stop_monitoring.is_set():
            # Collect CPU, memory, and disk I/O metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()

            # Record metrics
            timestamp = time.time()
            self.metrics[timestamp] = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used": memory.used,
                "disk_read_bytes": disk_io.read_bytes,
                "disk_write_bytes": disk_io.write_bytes,
            }

            # Log if significant changes
            if cpu_percent > 90:
                self.logger.warning(f"High CPU usage: {cpu_percent}%")

            if memory.percent > 90:
                self.logger.warning(f"High memory usage: {memory.percent}%")

            # Sleep for the monitoring interval
            time.sleep(interval)

    @contextmanager
    def measure_time(self, operation_name):
        """Context manager for measuring operation time.

        Args:
            operation_name: Name of the operation being measured
        """
        start_time = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            self.logger.info(f"{operation_name} completed in {elapsed:.2f} seconds")

    def calculate_throughput(self, doc_count, elapsed=None):
        """Calculate and log processing throughput.

        Args:
            doc_count: Number of documents processed
            elapsed: Elapsed time (if None, uses time since initialization)
        """
        if elapsed is None:
            elapsed = time.time() - self.start_time

        throughput = doc_count / elapsed if elapsed > 0 else 0
        self.logger.info(f"Processed {doc_count} documents in {elapsed:.2f} seconds")
        self.logger.info(f"Throughput: {throughput:.2f} documents/second")

        return throughput

    def log_summary(self):
        """Log performance summary."""
        elapsed = time.time() - self.start_time

        # Calculate average metrics
        if self.metrics:
            avg_cpu = sum(m["cpu_percent"] for m in self.metrics.values()) / len(self.metrics)
            avg_memory = sum(m["memory_percent"] for m in self.metrics.values()) / len(self.metrics)

            self.logger.info("Performance Summary:")
            self.logger.info(f"  Total runtime: {elapsed:.2f} seconds")
            self.logger.info(f"  Average CPU usage: {avg_cpu:.2f}%")
            self.logger.info(f"  Average memory usage: {avg_memory:.2f}%")

    def start_phase(self, phase_name: str, metadata: dict[str, Any] | None = None):
        """Start tracking a performance phase.

        Args:
            phase_name: Name of the phase (e.g., "Database Connection", "Document Query")
            metadata: Optional metadata to associate with this phase
        """
        # End current phase if one is active
        if self._current_phase:
            self.logger.warning(f"Phase '{self._current_phase}' not ended before starting '{phase_name}'")
            self.end_phase(self._current_phase)

        self._current_phase = phase_name

        # Initialize phase tracking
        if phase_name not in self.phases:
            self.phases[phase_name] = []
            self.phase_order.append(phase_name)

        # Record phase start
        phase_data = {
            "start_time": time.time(),
            "start_timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        self.phases[phase_name].append(phase_data)
        self.logger.info(f"PHASE_START - {phase_name}")

    def end_phase(self, phase_name: str | None = None, result_metadata: dict[str, Any] | None = None):
        """End tracking a performance phase.

        Args:
            phase_name: Name of the phase to end (uses current phase if None)
            result_metadata: Optional metadata about the phase results
        """
        if phase_name is None:
            phase_name = self._current_phase

        if not phase_name:
            self.logger.warning("No active phase to end")
            return

        if phase_name not in self.phases or not self.phases[phase_name]:
            self.logger.warning(f"Phase '{phase_name}' not found or already ended")
            return

        # Get the most recent phase entry
        phase_data = self.phases[phase_name][-1]

        # Check if phase was already ended
        if "end_time" in phase_data:
            self.logger.warning(f"Phase '{phase_name}' already ended")
            return

        # Record phase end
        end_time = time.time()
        duration = end_time - phase_data["start_time"]

        phase_data["end_time"] = end_time
        phase_data["end_timestamp"] = datetime.now().isoformat()
        phase_data["duration_seconds"] = duration
        phase_data["result_metadata"] = result_metadata or {}

        # Clear current phase if this was it
        if self._current_phase == phase_name:
            self._current_phase = None

        self.logger.info(f"PHASE_END - {phase_name} - Duration: {duration:.2f}s")

    @contextmanager
    def phase(self, phase_name: str, metadata: dict[str, Any] | None = None):
        """Context manager for phase tracking.

        Args:
            phase_name: Name of the phase
            metadata: Optional metadata for the phase

        Example:
            with monitor.phase("Document Query", {"batch_size": 100}):
                # Perform query
                pass
        """
        self.start_phase(phase_name, metadata)
        try:
            yield
        finally:
            self.end_phase(phase_name)

    def get_phase_summary(self) -> dict[str, Any]:
        """Get summary of all tracked phases.

        Returns:
            Dictionary with phase statistics
        """
        summary = {}

        for phase_name in self.phase_order:
            phase_entries = self.phases[phase_name]

            # Calculate stats for this phase
            durations = [entry.get("duration_seconds", 0) for entry in phase_entries if "duration_seconds" in entry]

            if durations:
                summary[phase_name] = {
                    "count": len(durations),
                    "total_duration": sum(durations),
                    "average_duration": sum(durations) / len(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "entries": phase_entries,
                }
            else:
                summary[phase_name] = {
                    "count": 0,
                    "total_duration": 0,
                    "average_duration": 0,
                    "min_duration": 0,
                    "max_duration": 0,
                    "entries": [],
                }

        return summary

    def generate_performance_report(self, output_file: str | None = None) -> dict[str, Any]:
        """Generate comprehensive performance report.

        Args:
            output_file: Optional path to save report as JSON

        Returns:
            Performance report dictionary
        """
        elapsed = time.time() - self.start_time

        # Calculate resource metrics
        avg_cpu = 0
        avg_memory = 0
        peak_cpu = 0
        peak_memory = 0

        if self.metrics:
            cpu_values = [m["cpu_percent"] for m in self.metrics.values()]
            memory_values = [m["memory_percent"] for m in self.metrics.values()]

            avg_cpu = sum(cpu_values) / len(cpu_values)
            avg_memory = sum(memory_values) / len(memory_values)
            peak_cpu = max(cpu_values)
            peak_memory = max(memory_values)

        # Build comprehensive report
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "total_runtime_seconds": elapsed,
            "total_runtime_formatted": self._format_duration(elapsed),
            "resource_usage": {
                "average_cpu_percent": round(avg_cpu, 2),
                "average_memory_percent": round(avg_memory, 2),
                "peak_cpu_percent": round(peak_cpu, 2),
                "peak_memory_percent": round(peak_memory, 2),
                "samples_collected": len(self.metrics),
            },
            "phases": self.get_phase_summary(),
            "phase_order": self.phase_order,
        }

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with output_path.open("w") as f:
                json.dump(report, f, indent=2, default=str)

            self.logger.info(f"Performance report saved to {output_file}")

        return report

    def log_phase_summary(self):
        """Log a summary of all tracked phases."""
        elapsed = time.time() - self.start_time

        self.logger.info("=" * 70)
        self.logger.info("Performance Phase Summary")
        self.logger.info("=" * 70)
        self.logger.info(f"Total Runtime: {self._format_duration(elapsed)}")
        self.logger.info("")

        phase_summary = self.get_phase_summary()

        for phase_name in self.phase_order:
            stats = phase_summary.get(phase_name, {})

            if stats.get("count", 0) > 0:
                self.logger.info(f"Phase: {phase_name}")
                self.logger.info(f"  Count: {stats['count']}")
                self.logger.info(f"  Total Duration: {self._format_duration(stats['total_duration'])}")
                self.logger.info(f"  Average Duration: {self._format_duration(stats['average_duration'])}")
                self.logger.info(f"  Min Duration: {self._format_duration(stats['min_duration'])}")
                self.logger.info(f"  Max Duration: {self._format_duration(stats['max_duration'])}")
                self.logger.info("")

        self.logger.info("=" * 70)

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted string (e.g., "2h 15m 30s")
        """
        if seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.2f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs:.2f}s"
