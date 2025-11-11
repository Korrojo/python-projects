"""Test configuration and fixtures for mongo_backup_tools."""

import sys
from pathlib import Path

# Add src to Python path so modules can be imported
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
