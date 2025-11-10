"""Run script for patients HCMID validator.

Example usage:
    python run.py csv --input patients.csv --env prod
    python run.py excel --input patients.xlsx --env prod
"""

import sys
from pathlib import Path

# Add src to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and run the CLI app
from cli import app  # type: ignore[import-not-found]

if __name__ == "__main__":
    app()
