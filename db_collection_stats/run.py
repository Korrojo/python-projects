"""Main entry point for db_collection_stats.

This project supports multiple commands:
  - coll-stats: Gather collection statistics
  - index-stats: Analyze index usage

Run with --help to see all available commands.
"""

import sys
from pathlib import Path

# Add src/ to path so we can import project modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from db_collection_stats.cli import app

if __name__ == "__main__":
    app()
