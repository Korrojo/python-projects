"""Test configuration for mongodb_index_tools."""

import sys
from pathlib import Path

# Add src/ to path so tests can import project modules
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
