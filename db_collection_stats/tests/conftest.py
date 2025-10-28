"""Test configuration for db_collection_stats tests."""

import sys
from pathlib import Path

# Add src/ to path so tests can import project modules
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Add common_config to path (monorepo structure)
repo_root = project_root.parent
common_config_path = repo_root / "common_config" / "src"
if common_config_path.exists():
    sys.path.insert(0, str(common_config_path))
