"""Orchestrator for mongoexport operations."""

from models.export import MongoExportOptions
from orchestrators.base import BaseOrchestrator, MongoOperationResult


class MongoExportOrchestrator(BaseOrchestrator):
    """Orchestrator for mongoexport operations."""

    def __init__(self):
        super().__init__("mongoexport.sh")

    def export(self, options: MongoExportOptions, timeout: int = 1800) -> MongoOperationResult:
        """
        Execute mongoexport operation.

        Args:
            options: Mongoexport configuration options
            timeout: Operation timeout in seconds (default: 30 minutes)

        Returns:
            MongoOperationResult with execution details
        """
        # Validate prerequisites
        self.validate_prerequisites()

        # Validate CSV requirements
        options.validate_csv_requirements()

        # Ensure output directory exists if file specified
        if options.output_file:
            options.output_file.parent.mkdir(parents=True, exist_ok=True)

        # Execute operation
        return self.execute(options, timeout=timeout)
