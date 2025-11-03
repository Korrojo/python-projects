"""
Resource monitoring utility for MongoDB PHI masking pipeline.

This module provides system resource monitoring capabilities:
- CPU usage monitoring
- Memory usage monitoring
- Disk I/O monitoring
- Network I/O monitoring
"""

import os
import time
import logging
import threading
import psutil
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
from pathlib import Path


class ResourceMonitor:
    """Monitors system resources and collects metrics."""
    
    def __init__(self, config: Dict[str, Any], metrics_callback: Callable[[Dict[str, Any]], None] = None):
        """Initialize the resource monitor.
        
        Args:
            config: Resource monitoring configuration
            metrics_callback: Optional callback function for resource metrics
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.metrics_callback = metrics_callback
        self.enabled = config.get('enabled', True)
        
        # CPU thresholds
        self.cpu_high = config.get('cpu_threshold', {}).get('high', 80)
        self.cpu_low = config.get('cpu_threshold', {}).get('low', 20)
        
        # Memory thresholds
        self.memory_high = config.get('memory_threshold', {}).get('high', 85)
        self.memory_low = config.get('memory_threshold', {}).get('low', 15)
        
        # Monitoring intervals
        self.interval = config.get('intervals', {}).get('adjustment_interval', 60)
        self.history_length = config.get('intervals', {}).get('history_length', 6)
        
        # System stats
        self.process = psutil.Process(os.getpid())
        self.last_disk_io = psutil.disk_io_counters()
        self.last_net_io = psutil.net_io_counters()
        self.last_check_time = time.time()
        
        # Metrics history
        self.cpu_history: List[float] = []
        self.memory_history: List[float] = []
        self.disk_read_history: List[float] = []
        self.disk_write_history: List[float] = []
        self.net_sent_history: List[float] = []
        self.net_recv_history: List[float] = []
        
        # For adaptive batch sizing
        self.resource_state = "normal"  # normal, high, low
        
        # Monitoring thread
        self.monitor_thread = None
        self.stop_event = threading.Event()
    
    def start(self) -> None:
        """Start the resource monitoring thread."""
        if not self.enabled:
            self.logger.info("Resource monitoring is disabled")
            return
            
        self.logger.info("Starting resource monitoring")
        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop(self) -> None:
        """Stop the resource monitoring thread."""
        if not self.enabled or not self.monitor_thread:
            return
            
        self.logger.info("Stopping resource monitoring")
        self.stop_event.set()
        self.monitor_thread.join(timeout=5.0)
        self.monitor_thread = None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current system resource metrics.
        
        Returns:
            Dictionary of system resource metrics
        """
        current_time = time.time()
        elapsed = current_time - self.last_check_time
        
        # Get CPU usage
        cpu_percent = self.process.cpu_percent()
        system_cpu_percent = psutil.cpu_percent()
        
        # Get memory usage
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()
        
        # Get disk I/O
        current_disk_io = psutil.disk_io_counters()
        disk_read_bytes = current_disk_io.read_bytes - self.last_disk_io.read_bytes
        disk_write_bytes = current_disk_io.write_bytes - self.last_disk_io.write_bytes
        
        # Calculate disk I/O rates
        disk_read_rate = disk_read_bytes / elapsed if elapsed > 0 else 0
        disk_write_rate = disk_write_bytes / elapsed if elapsed > 0 else 0
        
        # Get network I/O
        current_net_io = psutil.net_io_counters()
        net_sent_bytes = current_net_io.bytes_sent - self.last_net_io.bytes_sent
        net_recv_bytes = current_net_io.bytes_recv - self.last_net_io.bytes_recv
        
        # Calculate network I/O rates
        net_sent_rate = net_sent_bytes / elapsed if elapsed > 0 else 0
        net_recv_rate = net_recv_bytes / elapsed if elapsed > 0 else 0
        
        # Update last values
        self.last_disk_io = current_disk_io
        self.last_net_io = current_net_io
        self.last_check_time = current_time
        
        # Return metrics
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'process_percent': cpu_percent,
                'system_percent': system_cpu_percent,
            },
            'memory': {
                'rss_bytes': memory_info.rss,
                'vms_bytes': memory_info.vms,
                'percent': memory_percent,
            },
            'disk_io': {
                'read_bytes': disk_read_bytes,
                'write_bytes': disk_write_bytes,
                'read_rate_bytes_per_sec': disk_read_rate,
                'write_rate_bytes_per_sec': disk_write_rate,
            },
            'network_io': {
                'sent_bytes': net_sent_bytes,
                'recv_bytes': net_recv_bytes,
                'sent_rate_bytes_per_sec': net_sent_rate,
                'recv_rate_bytes_per_sec': net_recv_rate,
            },
        }
    
    def get_resource_state(self) -> str:
        """Get the current resource state.
        
        Returns:
            Resource state: "normal", "high", or "low"
        """
        return self.resource_state
    
    def update_history(self, metrics: Dict[str, Any]) -> None:
        """Update the metrics history.
        
        Args:
            metrics: Current system resource metrics
        """
        # Extract values
        cpu_percent = metrics['cpu']['system_percent']
        memory_percent = metrics['memory']['percent']
        disk_read_rate = metrics['disk_io']['read_rate_bytes_per_sec']
        disk_write_rate = metrics['disk_io']['write_rate_bytes_per_sec']
        net_sent_rate = metrics['network_io']['sent_rate_bytes_per_sec']
        net_recv_rate = metrics['network_io']['recv_rate_bytes_per_sec']
        
        # Update histories
        self.cpu_history.append(cpu_percent)
        self.memory_history.append(memory_percent)
        self.disk_read_history.append(disk_read_rate)
        self.disk_write_history.append(disk_write_rate)
        self.net_sent_history.append(net_sent_rate)
        self.net_recv_history.append(net_recv_rate)
        
        # Trim histories
        if len(self.cpu_history) > self.history_length:
            self.cpu_history.pop(0)
        if len(self.memory_history) > self.history_length:
            self.memory_history.pop(0)
        if len(self.disk_read_history) > self.history_length:
            self.disk_read_history.pop(0)
        if len(self.disk_write_history) > self.history_length:
            self.disk_write_history.pop(0)
        if len(self.net_sent_history) > self.history_length:
            self.net_sent_history.pop(0)
        if len(self.net_recv_history) > self.history_length:
            self.net_recv_history.pop(0)
    
    def determine_resource_state(self) -> str:
        """Determine the current resource state based on metrics history.
        
        Returns:
            Resource state: "normal", "high", or "low"
        """
        if not self.cpu_history or not self.memory_history:
            return "normal"
            
        # Calculate averages
        avg_cpu = sum(self.cpu_history) / len(self.cpu_history)
        avg_memory = sum(self.memory_history) / len(self.memory_history)
        
        # Determine resource state
        if avg_cpu > self.cpu_high or avg_memory > self.memory_high:
            return "high"
        elif avg_cpu < self.cpu_low and avg_memory < self.memory_low:
            return "low"
        else:
            return "normal"
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while not self.stop_event.is_set():
            try:
                # Get current metrics
                metrics = self.get_metrics()
                
                # Update history
                self.update_history(metrics)
                
                # Determine resource state
                prev_state = self.resource_state
                self.resource_state = self.determine_resource_state()
                
                # Log state changes
                if prev_state != self.resource_state:
                    self.logger.info(
                        f"Resource state changed from {prev_state} to {self.resource_state}"
                    )
                
                # Call metrics callback if provided
                if self.metrics_callback:
                    self.metrics_callback(metrics)
                
                # Sleep for monitoring interval
                time.sleep(self.interval / self.history_length)
            except Exception as e:
                self.logger.error(f"Error in resource monitoring: {str(e)}")
                time.sleep(5)  # Sleep and retry


class ResourceMetricsWriter:
    """Writes resource metrics to disk."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the metrics writer.
        
        Args:
            config: Metrics configuration
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.enabled = config.get('enabled', True)
        
        if not self.enabled:
            self.logger.info("Metrics writer is disabled")
            return
            
        # System stats configuration
        system_config = config.get('system_stats', {})
        self.system_dir = system_config.get('directory', 'metrics/system_stats')
        self.system_filename_pattern = system_config.get(
            'filename', 'system_stats_%Y%m%d_%H%M%S.csv'
        )
        
        # Batch stats configuration
        batch_config = config.get('batch_stats', {})
        self.batch_dir = batch_config.get('directory', 'metrics/batch_stats')
        self.batch_filename_pattern = batch_config.get(
            'filename', 'batch_stats_%Y%m%d_%H%M%S.csv'
        )
        
        # Ensure directories exist
        os.makedirs(self.system_dir, exist_ok=True)
        os.makedirs(self.batch_dir, exist_ok=True)
        
        # Create files and write headers
        self.system_file = None
        self.batch_file = None
        self._create_system_file()
        self._create_batch_file()
    
    def _create_system_file(self) -> None:
        """Create the system metrics file and write header."""
        if not self.enabled:
            return
            
        try:
            filename = datetime.now().strftime(self.system_filename_pattern)
            filepath = os.path.join(self.system_dir, filename)
            
            self.system_file = open(filepath, 'w')
            self.system_file.write(
                "timestamp,cpu_process_percent,cpu_system_percent,"
                "memory_rss_bytes,memory_vms_bytes,memory_percent,"
                "disk_read_bytes,disk_write_bytes,disk_read_rate_bytes_per_sec,"
                "disk_write_rate_bytes_per_sec,net_sent_bytes,net_recv_bytes,"
                "net_sent_rate_bytes_per_sec,net_recv_rate_bytes_per_sec\n"
            )
            self.system_file.flush()
            
            self.logger.info(f"Created system metrics file: {filepath}")
        except Exception as e:
            self.logger.error(f"Error creating system metrics file: {str(e)}")
            self.enabled = False
    
    def _create_batch_file(self) -> None:
        """Create the batch metrics file and write header."""
        if not self.enabled:
            return
            
        try:
            filename = datetime.now().strftime(self.batch_filename_pattern)
            filepath = os.path.join(self.batch_dir, filename)
            
            self.batch_file = open(filepath, 'w')
            self.batch_file.write(
                "timestamp,batch_size,docs_processed,elapsed_seconds,"
                "throughput_docs_per_sec,cpu_percent,memory_percent\n"
            )
            self.batch_file.flush()
            
            self.logger.info(f"Created batch metrics file: {filepath}")
        except Exception as e:
            self.logger.error(f"Error creating batch metrics file: {str(e)}")
            self.enabled = False
    
    def write_system_metrics(self, metrics: Dict[str, Any]) -> None:
        """Write system metrics to file.
        
        Args:
            metrics: System resource metrics
        """
        if not self.enabled or not self.system_file:
            return
            
        try:
            # Extract values
            timestamp = metrics['timestamp']
            cpu_process = metrics['cpu']['process_percent']
            cpu_system = metrics['cpu']['system_percent']
            memory_rss = metrics['memory']['rss_bytes']
            memory_vms = metrics['memory']['vms_bytes']
            memory_percent = metrics['memory']['percent']
            disk_read_bytes = metrics['disk_io']['read_bytes']
            disk_write_bytes = metrics['disk_io']['write_bytes']
            disk_read_rate = metrics['disk_io']['read_rate_bytes_per_sec']
            disk_write_rate = metrics['disk_io']['write_rate_bytes_per_sec']
            net_sent_bytes = metrics['network_io']['sent_bytes']
            net_recv_bytes = metrics['network_io']['recv_bytes']
            net_sent_rate = metrics['network_io']['sent_rate_bytes_per_sec']
            net_recv_rate = metrics['network_io']['recv_rate_bytes_per_sec']
            
            # Write CSV line
            self.system_file.write(
                f"{timestamp},{cpu_process},{cpu_system},"
                f"{memory_rss},{memory_vms},{memory_percent},"
                f"{disk_read_bytes},{disk_write_bytes},{disk_read_rate},"
                f"{disk_write_rate},{net_sent_bytes},{net_recv_bytes},"
                f"{net_sent_rate},{net_recv_rate}\n"
            )
            self.system_file.flush()
        except Exception as e:
            self.logger.error(f"Error writing system metrics: {str(e)}")
    
    def write_batch_metrics(self, batch_metrics: Dict[str, Any]) -> None:
        """Write batch processing metrics to file.
        
        Args:
            batch_metrics: Batch processing metrics
        """
        if not self.enabled or not self.batch_file:
            return
            
        try:
            # Extract values
            timestamp = batch_metrics.get('timestamp', datetime.now().isoformat())
            batch_size = batch_metrics.get('batch_size', 0)
            docs_processed = batch_metrics.get('docs_processed', 0)
            elapsed_seconds = batch_metrics.get('elapsed_seconds', 0)
            throughput = batch_metrics.get('throughput', 0)
            cpu_percent = batch_metrics.get('cpu_percent', 0)
            memory_percent = batch_metrics.get('memory_percent', 0)
            
            # Write CSV line
            self.batch_file.write(
                f"{timestamp},{batch_size},{docs_processed},{elapsed_seconds},"
                f"{throughput},{cpu_percent},{memory_percent}\n"
            )
            self.batch_file.flush()
        except Exception as e:
            self.logger.error(f"Error writing batch metrics: {str(e)}")
    
    def close(self) -> None:
        """Close metrics files."""
        if self.system_file:
            self.system_file.close()
            self.system_file = None
            
        if self.batch_file:
            self.batch_file.close()
            self.batch_file = None 