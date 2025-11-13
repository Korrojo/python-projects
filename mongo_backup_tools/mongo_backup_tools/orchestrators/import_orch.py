"""Orchestrator for mongoimport operations."""

from ..models.import_opts import MongoImportOptions
from .base import BaseOrchestrator, MongoOperationResult


class MongoImportOrchestrator(BaseOrchestrator):
    """Orchestrator for mongoimport operations."""

    def __init__(self):
        super().__init__("mongoimport.sh")

    def import_data(self, options: MongoImportOptions, timeout: int = 1800) -> MongoOperationResult:
        """
        Execute mongoimport operation.

        Args:
            options: Mongoimport configuration options
            timeout: Operation timeout in seconds (default: 30 minutes)

        Returns:
            MongoOperationResult with execution details
        """
        # Validate prerequisites
        self.validate_prerequisites()

        # Validate CSV requirements
        options.validate_csv_requirements()

        # Validate upsert requirements
        options.validate_upsert_requirements()

        # Execute operation
        return self.execute(options, timeout=timeout)
