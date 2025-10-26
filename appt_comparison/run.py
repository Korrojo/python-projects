"""Run script for appointment comparison validator.

Example usage:
    python run.py --input Daily_Appointment_Comparison_input1_20251023.csv --env PROD --limit 100
    python run.py --input Daily_Appointment_Comparison_input1_20251023.csv --env PROD
"""

import sys
from pathlib import Path

# Add src to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and run the CLI app
from cli_main import app  # type: ignore[import-not-found]

if __name__ == "__main__":
    app()
