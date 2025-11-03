"""
Main processor module for MongoDB PHI masking pipeline.

This module coordinates the overall masking workflow.
"""

import os
import logging
import time
import multiprocessing as mp
from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from datetime import datetime

from .connector import MongoConnector
from .masker import MaskingProcessor
from .validator import ValidationProcessor
from ..utils.checkpoint_manager import CheckpointManager, IncrementalSyncCheckpoint
from ..utils.resource_monitor import ResourceMonitor, ResourceMetricsWriter
from ..utils.error_handler import MaskerError, ConnectionError


class DataProcessor:
    """Coordinates the document processing workflow."""
    
    def __init__(
        self, 
        config: Dict[str, Any],
        logger: logging.Logger = None
    ):
        """Initialize the data processor.
        
        Args:
            config: Application configuration
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.config = config
        
        # Extract configuration values
        mongo_config = config.get("mongodb", {})
        source_config = mongo_config.get("source", {})
        dest_config = mongo_config.get("destination", {})
        
        processing_config = config.get("processing", {})
        self.masking_mode = processing_config.get("masking_mode", "separate")
        
        batch_config = processing_config.get("batch_size", {})
        self.initial_batch_size = batch_config.get("initial", 1000)
        self.min_batch_size = batch_config.get("min", 100)
        self.max_batch_size = batch_config.get("max", 10000)
        
        workers_config = processing_config.get("workers", {})
        self.min_workers = workers_config.get("min", 2)
        self.max_workers = workers_config.get("max", min(mp.cpu_count(), 64))
        
        # Masking configuration
        masking_config = config.get("masking", {})
        self.rules_path = masking_config.get("rules_path", "config/masking_rules/rules.json")
        self.default_rules_path = masking_config.get("default_rules", None)
        self.collection_rules = masking_config.get("collection_rules", {})
        
        # Set up connectors
        self.source_connector = MongoConnector(
            uri=source_config.get("uri"),
            database=source_config.get("database"),
            collection=source_config.get("collection")
        )
        
        if self.masking_mode == "separate" and dest_config:
            self.destination_connector = MongoConnector(
                uri=dest_config.get("uri"),
                database=dest_config.get("database"),
                collection=dest_config.get("collection")
            )
        else:
            self.destination_connector = self.source_connector
        
        # Set up processors
        self.masking_processor = MaskingProcessor(
            rules_path=self.rules_path,
            default_rules_path=self.default_rules_path,
            collection_rules=self.collection_rules,
            initial_batch_size=self.initial_batch_size,
            min_batch_size=self.min_batch_size,
            max_batch_size=self.max_batch_size,
            logger=self.logger
        )
        
        # Set up validation
        self.validator = ValidationProcessor(
            fields_to_validate=self._get_phi_field_names(),
            logger=self.logger
        )
        
        # Set up metrics writer
        metrics_config = config.get("metrics", {})
        self.metrics_writer = ResourceMetricsWriter(metrics_config)
        
        # Set up resource monitor
        resources_config = config.get("resources", {})
        self.resource_monitor = ResourceMonitor(
            config=resources_config,
            metrics_callback=self._handle_metrics_update
        )
        
        # Set up checkpointing
        progress_config = config.get("progress", {})
        checkpoint_config = progress_config.get("checkpoint", {})
        self.checkpoint_manager = CheckpointManager(checkpoint_config, "masking")
        
        # Set up incremental sync
        incremental_config = config.get("incremental", {})
        self.incremental_sync = IncrementalSyncCheckpoint(incremental_config)
        
        # Execution state
        self.is_running = False
        self.total_docs = 0
        self.processed_docs = 0
        self.current_batch_size = self.initial_batch_size
        self.worker_count = max(self.min_workers, min(self.max_workers, mp.cpu_count() // 2))
        
        self.logger.info(
            f"Initialized processor with batch size {self.initial_batch_size} "
            f"and {self.worker_count} workers"
        )
    
    def start(self) -> None:
        """Start the processing resources."""
        self.logger.info("Starting processor resources")
        
        # Start resource monitoring
        self.resource_monitor.start()
        
        # Start checkpoint autosave
        self.checkpoint_manager.start_autosave()
        
        # Connect to MongoDB
        self.source_connector.connect()
        
        if self.masking_mode == "separate":
            self.destination_connector.connect()
        
        self.is_running = True
        self.logger.info("Processor resources started")
    
    def stop(self) -> None:
        """Stop the processing resources."""
        self.logger.info("Stopping processor resources")
        
        # Stop resource monitoring
        self.resource_monitor.stop()
        
        # Stop checkpoint autosave
        self.checkpoint_manager.stop_autosave()
        
        # Disconnect from MongoDB
        self.source_connector.disconnect()
        
        if self.masking_mode == "separate":
            self.destination_connector.disconnect()
        
        # Close metrics writer
        self.metrics_writer.close()
        
        self.is_running = False
        self.logger.info("Processor resources stopped")
    
    def process_collection(
        self,
        query: Dict[str, Any] = None,
        incremental: bool = False
    ) -> Dict[str, Any]:
        """Process a collection with masking.
        
        Args:
            query: Optional query to filter documents
            incremental: Whether to use incremental processing
            
        Returns:
            Processing statistics
        """
        try:
            # Start resources if not already running
            if not self.is_running:
                self.start()
            
            # Get collection names
            src_db = self.source_connector.database_name
            src_coll = self.source_connector.collection_name
            
            # Determine query based on incremental mode
            if incremental:
                inc_query = self.incremental_sync.get_sync_query(src_coll)
                if query:
                    # Combine with user-provided query
                    query = {"$and": [query, inc_query]} if inc_query else query
                else:
                    query = inc_query
            
            # Count total documents
            self.total_docs = self.source_connector.count_documents(query)
            self.logger.info(f"Processing {self.total_docs} documents from {src_db}.{src_coll}")
            
            # Load checkpoint if resuming
            self.processed_docs = self.checkpoint_manager.get_docs_processed()
            last_id = self.checkpoint_manager.get_last_processed_id()
            
            if self.processed_docs > 0 and last_id:
                self.logger.info(f"Resuming from checkpoint: {self.processed_docs} docs processed")
                
                # Adjust query to start after last processed document
                if query:
                    query = {"$and": [query, {"_id": {"$gt": last_id}}]}
                else:
                    query = {"_id": {"$gt": last_id}}
            else:
                # Reset checkpoint if starting fresh
                self.checkpoint_manager.reset()
                self.processed_docs = 0
            
            # Start processing
            stats = self._process_documents(query)
            
            # Update incremental sync timestamp if in incremental mode
            if incremental:
                self.incremental_sync.update_last_sync_time(src_coll)
            
            return stats
        except Exception as e:
            self.logger.error(f"Error in process_collection: {str(e)}")
            raise
        finally:
            # Always stop resources
            self.stop()
    
    def _process_documents(self, query: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process documents from the source collection.
        
        Args:
            query: Optional query to filter documents
            
        Returns:
            Processing statistics
        """
        start_time = time.time()
        processed_count = 0
        error_count = 0
        last_id = None
        
        try:
            # Set up batch processing
            cursor = self.source_connector.find_documents(
                query=query,
                batch_size=self.current_batch_size
            )
            
            # Create a collection-specific masking processor
            collection_name = self.source_connector.collection_name
            self.logger.info(f"Creating collection-specific masking processor for {collection_name}")
            
            # Create a new masking processor with collection-specific rules
            from src.core.masker import create_masker_from_config
            masker = create_masker_from_config(self.config, collection_name, self.logger)
            collection_specific_processor = MaskingProcessor(
                document_masker=masker,
                initial_batch_size=self.initial_batch_size,
                min_batch_size=self.min_batch_size,
                max_batch_size=self.max_batch_size,
                logger=self.logger
            )
            
            # Process in batches
            current_batch = []
            
            for doc in cursor:
                current_batch.append(doc)
                last_id = doc.get("_id")
                
                # Process batch when it reaches current_batch_size
                if len(current_batch) >= self.current_batch_size:
                    batch_stats = self._process_batch(current_batch)
                    
                    # Update processing stats
                    processed_count += batch_stats.get("docs_processed", 0)
                    error_count += batch_stats.get("docs_with_errors", 0)
                    
                    # Update checkpoint
                    self.checkpoint_manager.update({
                        "docs_processed": self.processed_docs + processed_count,
                        "last_processed_id": last_id,
                        "last_updated": datetime.now().isoformat()
                    })
                    
                    # Clear batch
                    current_batch = []
                    
                    # Adjust batch size based on resource utilization
                    resource_state = self.resource_monitor.get_resource_state()
                    
                    # Use collection-specific processor if available
                    if hasattr(self, 'collection_specific_processor'):
                        self.collection_specific_processor.adjust_batch_size(resource_state)
                        self.current_batch_size = self.collection_specific_processor.current_batch_size
                    else:
                        # Fallback to global processor
                        self.masking_processor.adjust_batch_size(resource_state)
                        self.current_batch_size = self.masking_processor.current_batch_size
            
            # Process any remaining documents
            if current_batch:
                batch_stats = self._process_batch(current_batch)
                processed_count += batch_stats.get("docs_processed", 0)
                error_count += batch_stats.get("docs_with_errors", 0)
            
            # Final checkpoint update
            self.checkpoint_manager.update({
                "docs_processed": self.processed_docs + processed_count,
                "last_processed_id": last_id,
                "last_updated": datetime.now().isoformat(),
                "completed": True
            }, force_save=True)
            
            # Calculate final stats
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            stats = {
                "total_documents": self.total_docs,
                "processed_documents": processed_count,
                "documents_with_errors": error_count,
                "elapsed_time": elapsed_time,
                "throughput": processed_count / elapsed_time if elapsed_time > 0 else 0,
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
                "end_time": datetime.fromtimestamp(end_time).isoformat()
            }
            
            self.logger.info(
                f"Processing completed: {processed_count} documents processed in "
                f"{elapsed_time:.2f}s ({stats['throughput']:.2f} docs/sec)"
            )
            
            return stats
        except Exception as e:
            self.logger.error(f"Error in _process_documents: {str(e)}")
            # Save checkpoint even on error
            if last_id:
                self.checkpoint_manager.update({
                    "docs_processed": self.processed_docs + processed_count,
                    "last_processed_id": last_id,
                    "last_updated": datetime.now().isoformat(),
                    "error": str(e)
                }, force_save=True)
            
            raise
    
    def _process_batch(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a batch of documents.
        
        Args:
            batch: Batch of documents to process
            
        Returns:
            Batch processing statistics
        """
        # Get current resource metrics for batch stats
        resource_metrics = self.resource_monitor.get_metrics()
        
        # Mask documents with collection-specific processor
        start_time = time.time()
        # Use collection-specific processor if available, fall back to global one if not
        if hasattr(self, 'collection_specific_processor'):
            masked_docs, masking_metrics = self.collection_specific_processor.process_batch(batch)
        else:
            # Fallback to global processor
            masked_docs, masking_metrics = self.masking_processor.process_batch(batch)
        
        # Validate documents
        validation_results, validation_issues = self.validator.validate_batch(
            masked_docs, batch
        )
        
        # Calculate validation stats
        valid_count = sum(1 for result in validation_results if result)
        invalid_count = len(validation_results) - valid_count
        
        # Process documents based on masking mode
        if self.masking_mode == "separate":
            # Insert masked documents to destination
            self.destination_connector.bulk_insert(masked_docs)
        else:  # in-situ
            # Update documents in place
            for i, doc in enumerate(masked_docs):
                if "_id" in doc:
                    self.source_connector.update_document(
                        query={"_id": doc["_id"]},
                        update={"$set": doc}
                    )
        
        # Measure elapsed time
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Create batch metrics
        batch_metrics = {
            "timestamp": datetime.now().isoformat(),
            "batch_size": len(batch),
            "docs_processed": len(masked_docs),
            "docs_valid": valid_count,
            "docs_invalid": invalid_count,
            "elapsed_seconds": elapsed,
            "throughput": len(batch) / elapsed if elapsed > 0 else 0,
            "cpu_percent": resource_metrics["cpu"]["system_percent"],
            "memory_percent": resource_metrics["memory"]["percent"]
        }
        
        # Write batch metrics
        self.metrics_writer.write_batch_metrics(batch_metrics)
        
        self.logger.info(
            f"Batch processing: {len(batch)} docs in {elapsed:.2f}s "
            f"({batch_metrics['throughput']:.2f} docs/sec), "
            f"CPU: {batch_metrics['cpu_percent']:.1f}%, "
            f"Memory: {batch_metrics['memory_percent']:.1f}%"
        )
        
        return batch_metrics
    
    def _handle_metrics_update(self, metrics: Dict[str, Any]) -> None:
        """Handle system metrics update.
        
        Args:
            metrics: System resource metrics
        """
        # Write metrics to file
        self.metrics_writer.write_system_metrics(metrics)
    
    def _get_phi_field_names(self) -> List[str]:
        """Get list of PHI field names from rules.
        
        Returns:
            List of PHI field names
        """
        # Implementation depends on how rules are stored
        # This is a simplified example
        return self.masking_processor.get_phi_field_names()
        
    def process_in_situ(
        self,
        query: Dict[str, Any] = None,
        batch_size: int = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Process documents in-situ (modify documents in place).
        
        Args:
            query: Optional query to filter documents
            batch_size: Optional batch size override
            dry_run: Whether to perform a dry run (no modifications)
            
        Returns:
            Processing statistics
        """
        try:
            # Start resources if not already running
            if not self.is_running:
                self.start()
            
            # Get collection names
            src_db = self.source_connector.database_name
            src_coll = self.source_connector.collection_name
            
            # Count total documents
            self.total_docs = self.source_connector.count_documents(query)
            self.logger.info(f"Processing {self.total_docs} documents from {src_db}.{src_coll} in-situ")
            
            if dry_run:
                self.logger.info("Dry run mode - not making any changes")
                return {
                    "documents_found": self.total_docs,
                    "dry_run": True,
                    "elapsed_time": 0,
                }
            
            # Use provided batch size or default
            if batch_size is not None:
                self.current_batch_size = batch_size
            else:
                self.current_batch_size = self.initial_batch_size
                
            # Get ruleset for masking
            ruleset = self.masking_processor.get_ruleset()
            
            # Process in batches
            start_time = time.time()
            processed_count = 0
            updated_count = 0
            error_count = 0
            last_id = None
            
            while processed_count < self.total_docs:
                # Adjust query to use last_id for pagination
                current_query = query or {}
                if last_id:
                    # Clone the query and add _id filter
                    import copy
                    current_query = copy.deepcopy(current_query)
                    current_query["_id"] = {"$gt": last_id}
                
                # Get batch of documents
                batch_cursor = self.source_connector.find(
                    query=current_query,
                    limit=self.current_batch_size,
                )
                
                batch = list(batch_cursor)
                if not batch:
                    break  # No more documents to process
                
                # Track last ID for pagination
                last_id = batch[-1]["_id"]
                processed_count += len(batch)
                
                # Process batch
                batch_start_time = time.time()
                
                # Mask and update each document
                for doc in batch:
                    try:
                        # Create a copy of the original ID
                        doc_id = doc["_id"]
                        
                        # Mask the document
                        masked_doc = self.masking_processor.process_document(doc)
                        
                        # Update the document in place
                        self.source_connector.replace_one(
                            query={"_id": doc_id},
                            document=masked_doc,
                        )
                        
                        updated_count += 1
                    except Exception as e:
                        self.logger.error(f"Error masking document {doc.get('_id')}: {str(e)}")
                        error_count += 1
                
                # Calculate batch performance
                batch_end_time = time.time()
                batch_duration = batch_end_time - batch_start_time
                total_duration = batch_end_time - start_time
                docs_per_second = len(batch) / batch_duration if batch_duration > 0 else 0
                
                # Adjust batch size based on performance (optional)
                if self.masking_processor.should_adjust_batch_size():
                    new_batch_size = self.masking_processor.adjust_batch_size(
                        cpu_usage=self.resource_monitor.get_cpu_usage(),
                        memory_usage=self.resource_monitor.get_memory_usage(),
                    )
                    if new_batch_size != self.current_batch_size:
                        self.logger.info(f"Adjusted batch size from {self.current_batch_size} to {new_batch_size}")
                        self.current_batch_size = new_batch_size
                
                # Log progress
                progress = (processed_count / self.total_docs) * 100 if self.total_docs > 0 else 0
                self.logger.info(
                    f"Progress: {progress:.1f}% ({processed_count}/{self.total_docs}) - "
                    f"Speed: {docs_per_second:.1f} docs/sec"
                )
                
                # Write metrics
                self._handle_metrics_update({
                    "documents_processed": processed_count,
                    "documents_updated": updated_count,
                    "errors": error_count,
                    "batch_duration": batch_duration,
                    "total_duration": total_duration,
                    "docs_per_second": docs_per_second,
                    "progress": progress,
                })
            
            # Record end time and calculate elapsed time
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            # Prepare stats
            stats = {
                "documents_processed": processed_count,
                "documents_updated": updated_count,
                "error_count": error_count,
                "elapsed_time": elapsed_time,
                "performance": {
                    "docs_per_second": processed_count / elapsed_time if elapsed_time > 0 else 0,
                }
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error in process_in_situ: {str(e)}")
            raise
        
        finally:
            # Always stop resources
            self.stop() 