import time
import logging
from functools import wraps
from contextlib import contextmanager
import psutil
import threading
from typing import Dict, List, Any, Optional

class PerformanceMonitor:
    """Utility for monitoring and reporting performance metrics."""
    
    def __init__(self, logger=None):
        """Initialize the performance monitor.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.metrics = {}
        self.start_time = time.time()
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()
        
    def start_monitoring(self, interval=5.0):
        """Start background monitoring thread.
        
        Args:
            interval: Monitoring interval in seconds
        """
        self._stop_monitoring.clear()
        self._monitoring_thread = threading.Thread(
            target=self._monitor_resources,
            args=(interval,),
            daemon=True
        )
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
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used': memory.used,
                'disk_read_bytes': disk_io.read_bytes,
                'disk_write_bytes': disk_io.write_bytes
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
            avg_cpu = sum(m['cpu_percent'] for m in self.metrics.values()) / len(self.metrics)
            avg_memory = sum(m['memory_percent'] for m in self.metrics.values()) / len(self.metrics)
            
            self.logger.info(f"Performance Summary:")
            self.logger.info(f"  Total runtime: {elapsed:.2f} seconds")
            self.logger.info(f"  Average CPU usage: {avg_cpu:.2f}%")
            self.logger.info(f"  Average memory usage: {avg_memory:.2f}%")
