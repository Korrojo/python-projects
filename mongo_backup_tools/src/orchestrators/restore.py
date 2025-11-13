"""Orchestrator for mongorestore operations."""

from models.restore import MongoRestoreOptions
from orchestrators.base import BaseOrchestrator, MongoOperationResult


class MongoRestoreOrchestrator(BaseOrchestrator):
    """Orchestrator for mongorestore operations."""

    def __init__(self):
        super().__init__("mongorestore.sh")

    def restore(self, options: MongoRestoreOptions, timeout: int = 3600) -> MongoOperationResult:
        """
        Execute mongorestore operation.

        Args:
            options: Mongorestore configuration options
            timeout: Operation timeout in seconds (default: 1 hour)

        Returns:
            MongoOperationResult with execution details
        """
        # Validate prerequisites
        self.validate_prerequisites()

        # Validate namespace pair if specified
        options.validate_namespace_pair()

        # Execute operation
        return self.execute(options, timeout=timeout)
