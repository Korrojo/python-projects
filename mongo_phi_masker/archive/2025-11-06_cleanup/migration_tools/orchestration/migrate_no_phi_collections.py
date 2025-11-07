#!/usr/bin/env python3
"""
Redirect script for backward compatibility.
This script now lives in nophi_migration/scripts/migrate_nophi_collections.py
"""

import os
import sys
from pathlib import Path

# Get the path to the new script location
PROJECT_ROOT = Path(__file__).parent.parent
NEW_SCRIPT_PATH = PROJECT_ROOT / "nophi_migration" / "scripts" / "migrate_nophi_collections.py"

if __name__ == "__main__":
    print("NOTE: This script has moved to nophi_migration/scripts/migrate_nophi_collections.py")
    print(f"Redirecting to {NEW_SCRIPT_PATH}...")

    # Execute the new script with the same arguments
    os.execv(sys.executable, [sys.executable, str(NEW_SCRIPT_PATH)] + sys.argv[1:])
