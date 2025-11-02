"""Main entry point for mongodb_index_tools.

This project provides multiple commands for MongoDB index management:
  - inventory: List all indexes with detailed information
  - utilization: Analyze index usage statistics
  - analyzer: Analyze query execution plans
  - advisor: Get index recommendations
  - create-index: Create new indexes
  - drop-index: Drop existing indexes

Run with --help to see all available commands.
"""

import sys
from pathlib import Path

# Add src/ to path so we can import project modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mongodb_index_tools.cli import app

if __name__ == "__main__":
    app()
