"""Orchestrator for mongodump operations."""

from ..models.dump import MongoDumpOptions
from .base import BaseOrchestrator, MongoOperationResult


class MongoDumpOrchestrator(BaseOrchestrator):
    """Orchestrator for mongodump operations."""

    def __init__(self):
        super().__init__("mongodump.sh")

    def dump(self, options: MongoDumpOptions, timeout: int = 3600) -> MongoOperationResult:
        """
        Execute mongodump operation.

        Args:
            options: Mongodump configuration options
            timeout: Operation timeout in seconds (default: 1 hour)

        Returns:
            MongoOperationResult with execution details
        """
        # Validate prerequisites
        self.validate_prerequisites()

        # Ensure output directory exists
        if not options.archive_file:
            options.output_dir.mkdir(parents=True, exist_ok=True)

        # Execute operation
        return self.execute(options, timeout=timeout)
