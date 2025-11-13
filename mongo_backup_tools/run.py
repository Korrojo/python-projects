"""Entry point for mongo_backup_tools CLI."""

import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cli import app  # noqa: E402

if __name__ == "__main__":
    app()
