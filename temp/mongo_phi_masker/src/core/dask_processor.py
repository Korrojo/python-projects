import dask.bag as db
import dask.dataframe as dd
from dask.distributed import Client, progress
from typing import Dict, List, Any, Optional
import logging

from src.core.connector import MongoConnector
from src.core.masker import MaskingProcessor


class DaskProcessor:
    """Dask-based processor for high-throughput document masking."""

    def __init__(
        self,
        config: Dict[str, Any],
        logger: Optional[logging.Logger] = None,
        n_workers: Optional[int] = None,
        threads_per_worker: Optional[int] = None,
        mask_function=None,
    ):
        """Initialize the Dask processor.

        Args:
            config: Application configuration
            logger: Optional logger instance
            n_workers: Number of Dask workers (defaults to number of cores)
            threads_per_worker: Threads per worker (defaults to 1)
            mask_function: Function to use for masking documents (takes a document and returns a masked document)
        """
        self.logger = logger or logging.getLogger(__name__)
        self.config = config

        # Extract configuration values
        mongo_config = config.get("mongodb", {})
        self.source_config = mongo_config.get("source", {})
        self.dest_config = mongo_config.get("destination", {})

        processing_config = config.get("processing", {})
        batch_config = processing_config.get("batch_size", {})
        self.batch_size = batch_config.get("initial", 1000)

        # Initialize Dask client
        self.n_workers = n_workers
        self.threads_per_worker = threads_per_worker
        self.client = None

        # Store the masking function
        self.mask_function = mask_function

        # For backward compatibility
        if not self.mask_function:
            self.logger.warning(
                "No mask_function provided, using default implementation"
            )
            self.mask_function = lambda doc: doc  # Default implementation (no masking)

    def start_client(self):
        """Start the Dask distributed client."""
        self.client = Client(
            n_workers=self.n_workers, threads_per_worker=self.threads_per_worker
        )
        self.logger.info(f"Started Dask client: {self.client}")
        return self.client

    def stop_client(self):
        """Stop the Dask client."""
        if self.client:
            self.client.close()
            self.logger.info("Closed Dask client")

    def _mask_document_batch(self, documents):
        """Process a batch of documents.

        Args:
            documents: List of documents to process

        Returns:
            List of masked documents
        """
        return [self.mask_function(doc) for doc in documents]

    def process_collection(self, query=None, limit=None):
        """Process documents from source collection and write to destination.

        Args:
            query: Optional MongoDB query to filter documents
            limit: Optional limit on number of documents to process

        Returns:
            Number of documents processed
        """
        # Connect to MongoDB
        source_connector = MongoConnector(
            uri=self.source_config.get("uri"),
            database=self.source_config.get("database"),
            collection=self.source_config.get("collection"),
            auth_database=self.source_config.get("auth_database"),
        )
        source_connector.connect()

        dest_connector = MongoConnector(
            uri=self.dest_config.get("uri"),
            database=self.dest_config.get("database"),
            collection=self.dest_config.get("collection"),
            auth_database=self.dest_config.get("auth_database"),
        )
        dest_connector.connect()

        try:
            # Fetch documents (with batching handled by MongoDB cursor)
            cursor = source_connector.find(query)
            if limit:
                cursor = cursor.limit(limit)

            # Convert to Dask bag with optimal partition size
            docs_bag = db.from_sequence(cursor, partition_size=self.batch_size)

            # Process in parallel
            self.logger.info(f"Starting parallel processing with Dask")
            masked_bag = docs_bag.map_partitions(self._mask_document_batch)

            # Write results in batches
            results = []
            for batch in masked_bag.partitions:
                masked_docs = batch.compute()
                dest_connector.insert_many(masked_docs)
                results.append(len(masked_docs))

            total_processed = sum(results)
            self.logger.info(f"Processed {total_processed} documents")
            return total_processed

        finally:
            source_connector.disconnect()
            dest_connector.disconnect()

    def process_collection_as_dataframe(self, query=None, limit=None):
        """Alternative implementation using Dask DataFrame.

        This can be more efficient for certain operations.
        """
        # Implementation details would depend on specific requirements
        # This would use dask.dataframe for processing
        pass
