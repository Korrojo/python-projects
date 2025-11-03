#!/usr/bin/env python3
"""
Results handling for MongoDB PHI Masking Tool.

This module provides functionality for handling and saving results from
the MongoDB PHI Masking Tool.
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Setup logger
logger = logging.getLogger(__name__)


class ResultsHandler:
    """Class for handling and saving results.

    This class is responsible for formatting and saving results from
    the MongoDB PHI Masking Tool.

    Attributes:
        environment: Environment name
        results_dir: Directory for saving results
    """

    def __init__(self, environment: Optional[str] = None):
        """Initialize the results handler.

        Args:
            environment: Environment name (e.g., DEV, TEST, PROD)
        """
        # Get environment name
        self.environment = environment.lower() if environment else "default"

        # Set results directory
        self.results_dir = f"results/{self.environment}"
        os.makedirs(self.results_dir, exist_ok=True)

        logger.debug(f"Results will be saved to {self.results_dir}")

    def save_results(
        self, results: Dict[str, Any], output_path: Optional[str] = None
    ) -> str:
        """Save results to a file.

        Args:
            results: Results dictionary
            output_path: Path to output file (optional)

        Returns:
            Path to the saved results file
        """
        # Add timestamp to results
        results["timestamp"] = datetime.now().isoformat()

        # Create default output path if not provided
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"{self.results_dir}/masking_results_{timestamp}.json"

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save results to file
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Results saved to {output_path}")

        # Create symlink to latest results if on Linux/Mac
        if sys.platform != "win32":
            latest_link = f"{self.results_dir}/masking_results_latest.json"
            if os.path.exists(latest_link):
                try:
                    os.remove(latest_link)
                except Exception as e:
                    logger.warning(f"Could not remove old results symlink: {str(e)}")

            try:
                os.symlink(os.path.basename(output_path), latest_link)
                logger.info(f"Latest results symlink created: {latest_link}")
            except Exception as e:
                logger.warning(f"Could not create symlink to latest results: {str(e)}")

        return output_path

    def format_results_summary(
        self, results: Dict[str, Any], verify_only: bool = False
    ) -> str:
        """Format results summary for display.

        Args:
            results: Results dictionary
            verify_only: Whether this is a verification-only run

        Returns:
            Formatted results summary
        """
        summary = "\nResults Summary:\n"

        if not verify_only:
            summary += (
                f"  Documents Processed: {results.get('documents_processed', 0)}\n"
            )
            summary += (
                f"  Documents with Errors: {results.get('documents_with_errors', 0)}\n"
            )
            summary += f"  Elapsed Time: {results.get('elapsed_time', 0):.2f} seconds\n"

        summary += f"  Source Count: {results.get('source_count', 0)}\n"
        summary += f"  Masked Count: {results.get('masked_count', 0)}\n"
        summary += f"  Count Match: {results.get('count_match', False)}\n"
        summary += f"  PHI Fields Masked: {results.get('phi_fields_masked', False)}\n"
        summary += f"  Non-PHI Fields Preserved: {results.get('non_phi_fields_preserved', False)}\n"

        # Add masked fields information
        masked_fields = results.get("masked_fields", [])
        if masked_fields:
            summary += f"  Successfully Masked Fields: {', '.join(masked_fields)}\n"

        # Add unmasked fields information
        unmasked_fields = results.get("unmasked_fields", [])
        if unmasked_fields:
            summary += f"  Fields Not Properly Masked: {', '.join(unmasked_fields)}\n"

        return summary

    def log_results_summary(
        self, results: Dict[str, Any], verify_only: bool = False
    ) -> None:
        """Log results summary.

        Args:
            results: Results dictionary
            verify_only: Whether this is a verification-only run
        """
        summary = self.format_results_summary(results, verify_only)
        logger.info(summary)
